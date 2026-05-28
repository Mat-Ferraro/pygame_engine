"""
EditorApplication — the scene editor entry point.

Wraps a pygame_engine Application in an ImGui docking layout. The game
scene renders into a pygame subsurface which is then displayed as an
ImGui image widget. All editor panels (hierarchy, inspector, toolbar)
surround the viewport.

Architecture
------------
- pygame owns the OpenGL/SDL window and the game rendering surface
- imgui-bundle provides the editor UI panels via the pygame backend
- The game scene runs with time_scale=0 in edit mode (nothing moves)
- The game scene is completely unaware of the editor's existence

Window behaviour
----------------
- Panels auto-dock into a default layout on first launch and after
  ``View → Reset Layout``: Hierarchy top-left, Inspector bottom-left,
  Scene viewport filling the rest. Subsequent launches restore the
  user's last layout from ``editor/imgui.ini``.
- The persisted layout is validated before being trusted — if any
  expected window is missing from the ini, we rebuild defaults
  instead of restoring a half-broken layout.
- Windows can only be moved by dragging their title bar / tab, not
  by dragging anywhere in the body. This matches Unity / Blender /
  Visual Studio conventions and prevents accidental panel drags while
  clicking widgets inside a panel.

Selection gizmos
----------------
When ``EditorState.show_gizmos`` is True and the editor is in EDIT
mode, the viewport overlays a selection outline + corner handles on
``selected_node_id`` and a faint hover outline on ``hovered_node_id``
(when distinct from the selection). Both are pure cosmetic overlays
drawn after the scene render — the game scene itself never sees them.

Usage::

    # From repo root:
    python -m editor

    # Or directly:
    python editor/editor_app.py

    # With a specific scene:
    python -m editor --scene mygame.scenes.main_menu.MainMenuScene
"""

from __future__ import annotations

import argparse
import pathlib
import importlib
import sys
import traceback
from pathlib import Path
from typing import Type

import pygame
from imgui_bundle import imgui
from imgui_bundle.python_backends.pygame_backend import PygameRenderer

from pygame_engine.app.application import Application
from pygame_engine.app.config import AppConfig
from pygame_engine.app.render_context import RenderContext
from pygame_engine.scene.scene import Scene
from pygame_engine.scene.described_scene import DescribedScene
from pygame_engine.theme.runtime import get_theme

from editor.editor_state import EditorState, EditorMode
from editor.panels.toolbar import render_toolbar
from editor.panels.hierarchy import render_hierarchy
from editor.panels.inspector import render_inspector


# ── Constants ─────────────────────────────────────────────────────────────────

EDITOR_WIDTH  = 1600
EDITOR_HEIGHT = 900
PANEL_WIDTH   = 280
TOOLBAR_H     = 56
VIEWPORT_W    = EDITOR_WIDTH - PANEL_WIDTH
VIEWPORT_H    = EDITOR_HEIGHT - TOOLBAR_H
EDITOR_TITLE  = "pygame_engine — Scene Editor"

WIN_HIERARCHY = "Hierarchy"
WIN_INSPECTOR = "Inspector"
WIN_SCENE     = "Scene"

EXPECTED_WINDOWS: tuple[str, ...] = (WIN_HIERARCHY, WIN_INSPECTOR, WIN_SCENE)

# ── Gizmo styling ─────────────────────────────────────────────────────────────
# These mirror the accent blue used by the toolbar so selection in the
# viewport visually rhymes with selection elsewhere in the editor.
GIZMO_SELECTED_RGB:  tuple[int, int, int] = (51, 128, 230)
GIZMO_HOVER_RGB:     tuple[int, int, int] = (51, 128, 230)
GIZMO_HANDLE_INNER:  tuple[int, int, int] = (255, 255, 255)
GIZMO_OUTLINE_PX:    int = 2     # selection outline thickness
GIZMO_HOVER_PX:      int = 1     # hover outline thickness
GIZMO_HANDLE_PX:     int = 6     # corner handle side length
GIZMO_HOVER_ALPHA:   int = 140   # 0–255; hover is intentionally faint


# ── ImGui binding compatibility helpers ──────────────────────────────────────

def _resolve_dir(direction: str) -> int:
    """
    Resolve an ImGui cardinal direction to its integer value.

    Tries every plausible enum spelling — ``Dir_.left``, ``Dir_.Left``,
    ``Dir.left``, ``Dir.Left`` — and returns the integer value.
    """
    candidates = (
        ("Dir_", direction.lower()),
        ("Dir_", direction.capitalize()),
        ("Dir",  direction.lower()),
        ("Dir",  direction.capitalize()),
    )
    for enum_name, member in candidates:
        enum = getattr(imgui, enum_name, None)
        if enum is None:
            continue
        value = getattr(enum, member, None)
        if value is None:
            continue
        return int(getattr(value, "value", value))
    raise RuntimeError(
        f"Could not find imgui direction enum for {direction!r}. "
        "Checked imgui.Dir_ and imgui.Dir, snake_case and PascalCase."
    )


_SPLIT_ATTR_DIR: str | None      = None
_SPLIT_ATTR_OPPOSITE: str | None = None


def _split_node(di, node_id: int, direction: int, ratio: float) -> tuple[int, int]:
    """
    Call ``dock_builder_split_node`` and return ``(id_at_dir, id_at_opposite)``.

    Handles both tuple-returning (older bindings) and struct-returning
    (current bindings) variants. On first call with a struct, discovers
    the attribute names and caches them for subsequent calls.
    """
    global _SPLIT_ATTR_DIR, _SPLIT_ATTR_OPPOSITE

    result = di.dock_builder_split_node(node_id, direction, ratio)

    if isinstance(result, (tuple, list)) and len(result) == 2:
        return int(result[0]), int(result[1])

    if _SPLIT_ATTR_DIR is not None and _SPLIT_ATTR_OPPOSITE is not None:
        return (
            int(getattr(result, _SPLIT_ATTR_DIR)),
            int(getattr(result, _SPLIT_ATTR_OPPOSITE)),
        )

    known_pairs = (
        ("id_at_dir",         "id_at_opposite_dir"),
        ("id_at_dir",         "id_at_opposite"),
        ("at_dir",            "at_opposite_dir"),
        ("at_dir",            "at_opposite"),
        ("id_dir",            "id_opposite"),
    )
    for a, b in known_pairs:
        if hasattr(result, a) and hasattr(result, b):
            _SPLIT_ATTR_DIR, _SPLIT_ATTR_OPPOSITE = a, b
            print(f"[editor] dock split result attrs: {a!r}, {b!r}")
            return int(getattr(result, a)), int(getattr(result, b))

    int_attrs = [
        name for name in dir(result)
        if not name.startswith("_") and isinstance(getattr(result, name, None), int)
    ]
    if len(int_attrs) >= 2:
        a, b = int_attrs[0], int_attrs[1]
        _SPLIT_ATTR_DIR, _SPLIT_ATTR_OPPOSITE = a, b
        print(
            f"[editor] dock split result: introspected attrs {a!r}, {b!r} "
            f"from {type(result).__name__}; full attr list: {int_attrs}"
        )
        return int(getattr(result, a)), int(getattr(result, b))

    raise RuntimeError(
        f"dock_builder_split_node returned {type(result).__name__!r}; "
        f"could not identify ID attributes. dir(result)={dir(result)}"
    )


# ── Ini validation ────────────────────────────────────────────────────────────

def _ini_is_valid(ini_text: str, required: tuple[str, ...]) -> tuple[bool, str]:
    """Check whether a persisted ImGui ini file is usable."""
    missing = [name for name in required
               if f"[Window][{name}]" not in ini_text]
    if missing:
        return False, f"missing window section(s): {', '.join(missing)}"
    if "[Docking][Data]" not in ini_text:
        return False, "missing [Docking][Data] block"
    return True, ""


# ── EditorApplication ─────────────────────────────────────────────────────────

def _save_imgui_ini() -> None:
    """Save ImGui layout to editor/imgui.ini."""
    try:
        import pathlib
        from imgui_bundle import imgui as _imgui
        ini_data = _imgui.save_ini_settings_to_memory()  # type: ignore[attr-defined]
        pathlib.Path("editor").mkdir(exist_ok=True)
        dest = pathlib.Path("editor/imgui.ini")
        dest.write_text(ini_data, encoding="utf-8")
        print(f"[editor] _save_imgui_ini: wrote {len(ini_data)} chars to {dest.absolute()}")
    except Exception as e:
        print(f"[editor] _save_imgui_ini FAILED: {e}")


def _render_texture(tex_id: int, w: float, h: float) -> None:
    """Render an OpenGL texture into the current ImGui window."""
    from imgui_bundle import imgui
    try:
        ref = imgui.ImTextureRef(tex_id)  # type: ignore[attr-defined]
        imgui.image(ref, imgui.ImVec2(w, h), imgui.ImVec2(0, 1), imgui.ImVec2(1, 0))
        return
    except Exception:
        pass
    try:
        from imgui_bundle import imgui_tex_id  # type: ignore[import]
        imgui.image(imgui_tex_id(tex_id), imgui.ImVec2(w, h),
                    imgui.ImVec2(0, 1), imgui.ImVec2(1, 0))
        return
    except Exception:
        pass
    try:
        imgui.image(tex_id, imgui.ImVec2(w, h),  # type: ignore[arg-type]
                    imgui.ImVec2(0, 1), imgui.ImVec2(1, 0))
        return
    except Exception:
        pass
    try:
        imgui.image(tex_id, (w, h), (0, 1), (1, 0))  # type: ignore[arg-type]
    except Exception:
        pass


class EditorApplication:
    """
    The scene editor — an ImGui shell around a pygame_engine Application.

    Args:
        scene_class: The DescribedScene subclass to open. If None, an
                     empty descriptor is shown.
    """

    def __init__(self, scene_class: Type[Scene] | None = None) -> None:
        self._scene_class = scene_class
        self._state       = EditorState()

        self._display:    pygame.Surface | None = None
        self._viewport:   pygame.Surface | None = None
        self._imgui_renderer: PygameRenderer | None = None
        self._app:        Application | None = None
        self._scene:      Scene | None = None
        self._tex_id:          int  = 0
        self._reset_layout_flag: bool = True
        self._scene_dock_id: int = 0

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self) -> None:
        """Initialise everything and enter the editor frame loop."""
        pygame.init()

        self._display = pygame.display.set_mode(
            (EDITOR_WIDTH, EDITOR_HEIGHT),
            pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE,
        )
        pygame.display.set_caption(EDITOR_TITLE)

        imgui.create_context()
        io = imgui.get_io()
        io.config_flags |= imgui.ConfigFlags_.docking_enable
        io.config_flags |= imgui.ConfigFlags_.nav_enable_keyboard

        try:
            io.config_windows_move_from_title_bar_only = True  # type: ignore[attr-defined]
        except AttributeError:
            try:
                io.ConfigWindowsMoveFromTitleBarOnly = True   # type: ignore[attr-defined]
            except AttributeError:
                pass

        try:
            io.ini_saving_rate = 0.0  # type: ignore[attr-defined]
        except AttributeError:
            pass
        try:
            io.ini_file_name = ""  # type: ignore[attr-defined]
        except AttributeError:
            pass

        self._imgui_renderer = PygameRenderer()

        ini_path = pathlib.Path("editor/imgui.ini")
        if ini_path.exists():
            try:
                ini_text = ini_path.read_text(encoding="utf-8")
                valid, reason = _ini_is_valid(ini_text, EXPECTED_WINDOWS)
                if valid:
                    imgui.load_ini_settings_from_memory(ini_text)
                    self._reset_layout_flag = False
                    print(f"[editor] loaded layout from {ini_path}")
                else:
                    print(
                        f"[editor] ini at {ini_path} is invalid ({reason}); "
                        "rebuilding default layout"
                    )
                    self._reset_layout_flag = True
            except Exception as exc:
                print(f"[editor] failed to load {ini_path}: {exc} — using defaults")
                self._reset_layout_flag = True
        else:
            print("[editor] no imgui.ini found — building default dock layout")
            self._reset_layout_flag = True

        self._ini_loaded  = False
        self._frame_count = 0

        io.display_size = imgui.ImVec2(float(EDITOR_WIDTH), float(EDITOR_HEIGHT))
        io.display_framebuffer_scale = imgui.ImVec2(1.0, 1.0)

        imgui.style_colors_dark()
        self._apply_editor_style()

        self._viewport = pygame.Surface((VIEWPORT_W, VIEWPORT_H))

        config = AppConfig(
            mode="development",
            width=VIEWPORT_W,
            height=VIEWPORT_H,
        )
        self._app = Application(config)

        self._load_scene()

        if self._app._time_manager is not None:
            self._app._time_manager.time_scale.value = 0.0

        self._loop()
        self._shutdown()

    # ── Frame loop ────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        clock   = pygame.time.Clock()
        running = True

        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                self._imgui_renderer.process_event(event)  # type: ignore[union-attr]

                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self._on_resize(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F5:
                        self._state.enter_play() if self._state.is_editing else self._state.enter_edit()
                    if event.key == pygame.K_ESCAPE and self._state.is_playing:
                        self._state.enter_edit()

            self._update_scene(dt)
            self._handle_pending_actions()
            self._render_scene()

            if self._viewport is not None:
                self._tex_id = self._surface_to_texture(self._viewport)

            try:
                from OpenGL import GL as gl
                gl.glClearColor(0.08, 0.08, 0.10, 1.0)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            except Exception:
                pass
            self._imgui_renderer.process_inputs()  # type: ignore[union-attr]
            imgui.new_frame()

            self._render_imgui()

            imgui.end_frame()
            imgui.render()
            self._imgui_renderer.render(imgui.get_draw_data())  # type: ignore[union-attr]

            pygame.display.flip()

    def _update_scene(self, dt: float) -> None:
        """Advance the scene (dt is 0 in edit mode)."""
        if self._scene is None:
            return
        effective_dt = dt if self._state.mode == EditorMode.PLAY else 0.0
        try:
            self._scene.update(effective_dt)
        except Exception as exc:
            self._state.set_status(f"Error in update(): {exc}")

    def _handle_pending_actions(self) -> None:
        """
        Consume and act on any one-shot action a panel requested.

        Panels (e.g. the toolbar's "Save Layout") don't touch the
        descriptor directly — they raise a ``pending_action`` on the
        state, and the application performs the real work here, where it
        owns the scene and descriptor.
        """
        action = self._state.take_pending_action()
        if action is None:
            return

        if action == self._state.ACTION_SAVE_LAYOUT:
            self._save_layout()

    def _save_layout(self) -> None:
        """
        Write the current descriptor to the scene's layout file.

        The descriptor is the source of truth for geometry, so saving it
        persists every edit made via the inspector or gizmos. Errors are
        surfaced in the status bar rather than crashing the editor.
        """
        descriptor = self._get_descriptor()
        if descriptor is None:
            self._state.set_status("Save Layout: no descriptor to save.")
            return
        if not self._state.layout_path:
            self._state.set_status("Save Layout: no layout path set.")
            return

        from pathlib import Path
        try:
            descriptor.save(Path(self._state.layout_path))
            self._state.set_status(f"Layout saved: {self._state.layout_path}")
            print(f"[editor] layout saved to {self._state.layout_path}")
        except OSError as exc:
            self._state.set_status(f"Save Layout failed: {exc}")
            print(f"[editor] save layout failed: {exc}")

    def _render_scene(self) -> None:
        """Render the game scene into the viewport subsurface."""
        if self._viewport is None:
            return

        self._viewport.fill((30, 30, 35))

        if self._scene is not None:
            ctx = RenderContext(theme=get_theme())
            try:
                self._scene.render(self._viewport, ctx)
            except Exception as exc:
                self._state.set_status(f"Error in render(): {exc}")

        if self._state.mode in (EditorMode.PLAY, EditorMode.PAUSED):
            r, g, b, a = self._state.viewport_tint
            if a > 0:
                tint = pygame.Surface(self._viewport.get_size(), pygame.SRCALPHA)
                tint.fill((r, g, b, a))
                self._viewport.blit(tint, (0, 0))

        # Grid and selection overlays are EDIT-mode only — play mode
        # should look exactly like the game runs in production.
        if self._state.is_editing:
            if self._state.show_grid:
                self._draw_grid()
            if self._state.show_gizmos:
                # Hover first, selection on top, so selecting the hovered
                # node looks correct (no faint hover bleeding through).
                self._draw_hover_gizmo()
                self._draw_selection_gizmo()

    def _draw_grid(self) -> None:
        """Draw the snap grid onto the viewport."""
        if self._viewport is None:
            return
        size  = self._state.grid_size
        w, h  = self._viewport.get_size()
        color = (50, 55, 60)
        for x in range(0, w, size):
            pygame.draw.line(self._viewport, color, (x, 0), (x, h))
        for y in range(0, h, size):
            pygame.draw.line(self._viewport, color, (0, y), (w, y))

    # ── Selection gizmo ───────────────────────────────────────────────────────

    def _get_node_rect(self, node_id: str) -> pygame.Rect | None:
        """
        Resolve a node id to its current pygame rect, or ``None``.

        Returns None for any failure — descriptor missing, node missing,
        rect conversion missing. Callers treat None as "nothing to draw"
        and move on without raising.
        """
        if self._scene is None or not isinstance(self._scene, DescribedScene):
            return None
        descriptor = getattr(self._scene, "layout", None)
        if descriptor is None:
            return None
        try:
            node = descriptor.get(node_id)
        except Exception:
            return None
        if node is None:
            return None
        try:
            return node.rect.to_pygame_rect()
        except Exception:
            return None

    def _draw_selection_gizmo(self) -> None:
        """
        Outline the selected node and draw four corner handles.

        Handles are filled accent squares with a 1-pixel white inner
        border, which keeps them readable against both dark and bright
        scene backgrounds. F5 will hit-test against these handles for
        resize; for now they're purely visual.
        """
        if self._viewport is None:
            return
        node_id = self._state.selected_node_id
        if not node_id:
            return
        rect = self._get_node_rect(node_id)
        if rect is None or rect.width <= 0 or rect.height <= 0:
            return

        # Outline. pygame.draw.rect with width>0 draws an outlined rect.
        pygame.draw.rect(
            self._viewport, GIZMO_SELECTED_RGB, rect,
            width=GIZMO_OUTLINE_PX,
        )

        # Four corner handles. Each handle is centred on the corner so
        # half overlaps the rect, half outside — the visual centre is
        # exactly the corner, which is what feels right for F5's resize.
        half = GIZMO_HANDLE_PX // 2
        for corner_x, corner_y in (
            (rect.left,  rect.top),
            (rect.right, rect.top),
            (rect.left,  rect.bottom),
            (rect.right, rect.bottom),
        ):
            handle = pygame.Rect(
                corner_x - half, corner_y - half,
                GIZMO_HANDLE_PX, GIZMO_HANDLE_PX,
            )
            pygame.draw.rect(self._viewport, GIZMO_SELECTED_RGB, handle)
            pygame.draw.rect(self._viewport, GIZMO_HANDLE_INNER, handle, width=1)

    def _draw_hover_gizmo(self) -> None:
        """
        Faint outline on the hovered node, when it's not the selected one.

        Drawing the hover overlay on the same node we're about to outline
        as "selected" just doubles the line weight, so we skip it.
        """
        if self._viewport is None:
            return
        node_id = self._state.hovered_node_id
        if not node_id or node_id == self._state.selected_node_id:
            return
        rect = self._get_node_rect(node_id)
        if rect is None or rect.width <= 0 or rect.height <= 0:
            return

        # Alpha lines aren't directly supported by pygame.draw.rect on
        # an opaque surface, so we composite onto a temp SRCALPHA layer
        # then blit. Cheap at viewport sizes; happens at most once per
        # frame.
        layer = pygame.Surface(self._viewport.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(
            layer, (*GIZMO_HOVER_RGB, GIZMO_HOVER_ALPHA), rect,
            width=GIZMO_HOVER_PX,
        )
        self._viewport.blit(layer, (0, 0))

    # ── ImGui layout ──────────────────────────────────────────────────────────

    def _render_imgui(self) -> None:
        """Render all ImGui panels for this frame."""
        descriptor = self._get_descriptor()

        was_reset = self._reset_layout_flag or getattr(self._state, 'reset_layout', False)
        self._reset_layout_flag = False
        if hasattr(self._state, 'reset_layout'):
            self._state.reset_layout = False
        reset = was_reset

        render_toolbar(self._state)
        self._render_panels(descriptor, reset)

        if was_reset:
            _save_imgui_ini()

    def _build_default_dock_layout(self, dockspace_id: int) -> None:
        """Construct the default docked layout via the dock-builder API."""
        dir_left = _resolve_dir("left")
        dir_up   = _resolve_dir("up")

        try:
            di = imgui.internal  # type: ignore[attr-defined]
        except AttributeError:
            di = imgui

        try:
            di.dock_builder_remove_node(dockspace_id)
        except Exception:
            pass

        try:
            flag_none = imgui.DockNodeFlags_.none.value  # type: ignore[attr-defined]
        except Exception:
            flag_none = 0
        di.dock_builder_add_node(dockspace_id, flag_none)

        ds_size = imgui.ImVec2(
            float(EDITOR_WIDTH),
            float(max(1, EDITOR_HEIGHT - TOOLBAR_H)),
        )
        di.dock_builder_set_node_size(dockspace_id, ds_size)

        left_ratio = max(0.05, min(0.5, PANEL_WIDTH / float(EDITOR_WIDTH)))

        left_id, center_id = _split_node(di, dockspace_id, dir_left, left_ratio)
        hier_id, insp_id   = _split_node(di, left_id,      dir_up,   0.55)

        print(
            f"[editor] dock layout built: "
            f"dockspace={dockspace_id:#x} "
            f"hier={hier_id:#x} insp={insp_id:#x} center={center_id:#x}"
        )

        di.dock_builder_dock_window(WIN_HIERARCHY, hier_id)
        di.dock_builder_dock_window(WIN_INSPECTOR, insp_id)
        di.dock_builder_dock_window(WIN_SCENE,     center_id)

        di.dock_builder_finish(dockspace_id)

        self._scene_dock_id = center_id

    def _render_panels(self, descriptor, reset: bool) -> None:
        """Render all editor panels inside a shared DockSpace."""
        if reset:
            try:
                imgui.load_ini_settings_from_memory("")  # type: ignore[attr-defined]
            except Exception:
                pass

        dockspace_id = 0
        try:
            vp = imgui.get_main_viewport()
            orig_pos  = vp.work_pos
            orig_size = vp.work_size
            vp.work_pos  = imgui.ImVec2(orig_pos.x,  orig_pos.y  + TOOLBAR_H)  # type: ignore[attr-defined]
            vp.work_size = imgui.ImVec2(orig_size.x, orig_size.y - TOOLBAR_H)  # type: ignore[attr-defined]
            dockspace_id = imgui.dock_space_over_viewport(0, vp, 0)
            vp.work_pos  = orig_pos   # type: ignore[attr-defined]
            vp.work_size = orig_size  # type: ignore[attr-defined]
        except Exception:
            try:
                dockspace_id = imgui.dock_space_over_viewport(0, imgui.get_main_viewport(), 0)
            except Exception:
                dockspace_id = 0

        if reset and dockspace_id:
            try:
                self._build_default_dock_layout(dockspace_id)
            except Exception as exc:
                print(f"[editor] dock layout build FAILED: {exc}")
                traceback.print_exc()

        render_hierarchy(self._state, descriptor)
        render_inspector(self._state, descriptor)

        if reset and self._scene_dock_id:
            try:
                imgui.set_next_window_dock_id(self._scene_dock_id, imgui.Cond_.always)
            except Exception:
                pass
        scene_flags = (
            getattr(imgui.WindowFlags_, "no_scrollbar",           0)
            | getattr(imgui.WindowFlags_, "no_scroll_with_mouse",  0)
            | getattr(imgui.WindowFlags_, "no_saved_settings",     0)
        )
        imgui.begin(WIN_SCENE, None, scene_flags)
        if self._tex_id:
            size = imgui.get_content_region_avail()
            w, h = max(1.0, size.x), max(1.0, size.y)
            _render_texture(self._tex_id, w, h)
        else:
            imgui.text_colored((0.4, 0.4, 0.4, 1.0), "Scene loading...")
        imgui.end()

    def _get_descriptor(self):
        """Return the SceneDescriptor if the scene is a DescribedScene."""
        if isinstance(self._scene, DescribedScene):
            return self._scene.layout
        return None

    def _load_scene(self) -> None:
        """Instantiate and enter the target scene via EditorAppStub."""
        if self._scene_class is None:
            self._state.set_status("No scene loaded. Use --scene to open one.")
            return

        from editor.scene_loader import load_scene_for_editor
        result = load_scene_for_editor(
            self._scene_class,
            width=VIEWPORT_W,
            height=VIEWPORT_H,
        )
        layout_path = None
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            self._scene = result[0]
            status      = str(result[1])
            # Third element is the layout path (where Save Layout writes).
            if len(result) >= 3:
                layout_path = result[2]
        else:
            self._scene = None
            status      = f"Unexpected return from loader: {result!r}"
        self._state.set_status(status)
        print(f"[editor] _load_scene: {status}")
        if self._scene is not None:
            self._state.scene_path = self._scene_class.__name__
            # Storing the layout path enables the "Save Layout" action —
            # the toolbar greys it out while this is None.
            if layout_path is not None:
                self._state.layout_path = str(layout_path)
                print(f"[editor] layout path: {layout_path}")

    # ── OpenGL texture upload ─────────────────────────────────────────────────

    def _surface_to_texture(self, surface: pygame.Surface) -> int:
        """
        Upload a pygame Surface to an OpenGL texture.

        pygame surfaces are top-down; OpenGL samples bottom-up. We flip
        the surface before upload, and ImGui's image() uses UVs (0,1)–(1,0)
        to flip back. Both together give a right-side-up image.
        """
        flipped = pygame.transform.flip(surface, False, True)
        texture_data = pygame.image.tobytes(flipped, "RGBA", False)
        w, h = surface.get_size()

        try:
            from imgui_bundle.python_backends import gl as igl  # type: ignore[import]
            if self._tex_id:
                igl.glDeleteTextures([self._tex_id])
            tex_id = int(igl.glGenTextures(1))
            igl.glBindTexture(igl.GL_TEXTURE_2D, tex_id)
            igl.glTexParameteri(igl.GL_TEXTURE_2D, igl.GL_TEXTURE_MIN_FILTER, igl.GL_LINEAR)
            igl.glTexParameteri(igl.GL_TEXTURE_2D, igl.GL_TEXTURE_MAG_FILTER, igl.GL_LINEAR)
            igl.glTexParameteri(igl.GL_TEXTURE_2D, igl.GL_TEXTURE_WRAP_S, igl.GL_CLAMP_TO_EDGE)
            igl.glTexParameteri(igl.GL_TEXTURE_2D, igl.GL_TEXTURE_WRAP_T, igl.GL_CLAMP_TO_EDGE)
            igl.glTexImage2D(
                igl.GL_TEXTURE_2D, 0, igl.GL_RGBA, w, h, 0,
                igl.GL_RGBA, igl.GL_UNSIGNED_BYTE, texture_data,
            )
            igl.glBindTexture(igl.GL_TEXTURE_2D, 0)
            return tex_id
        except Exception:
            pass

        try:
            from OpenGL import GL as gl
            if self._tex_id:
                gl.glDeleteTextures([self._tex_id])
            tex_id = int(gl.glGenTextures(1))
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0,
                gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, texture_data,
            )
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            return tex_id
        except Exception as e:
            if not hasattr(self, "_tex_error_logged"):
                self._tex_error_logged = True
                print(f"[editor] Texture upload failed: {e}")
            return 0

    # ── Resize ────────────────────────────────────────────────────────────────

    def _on_resize(self, w: int, h: int) -> None:
        """Handle window resize."""
        global EDITOR_WIDTH, EDITOR_HEIGHT, VIEWPORT_W, VIEWPORT_H
        EDITOR_WIDTH  = w
        EDITOR_HEIGHT = h
        VIEWPORT_W    = max(100, w - PANEL_WIDTH)
        VIEWPORT_H    = max(100, h - TOOLBAR_H)
        self._viewport = pygame.Surface((VIEWPORT_W, VIEWPORT_H))

    # ── Style ─────────────────────────────────────────────────────────────────

    def _apply_editor_style(self) -> None:
        """Apply a clean dark style to ImGui."""
        style = imgui.get_style()
        style.window_rounding    = 4.0
        style.frame_rounding     = 3.0
        style.grab_rounding      = 3.0
        style.window_border_size = 1.0
        style.frame_border_size  = 0.0
        style.item_spacing       = imgui.ImVec2(6, 4)
        style.frame_padding      = imgui.ImVec2(6, 3)

        dark_bg   = (0.10, 0.10, 0.12, 1.00)
        panel_bg  = (0.13, 0.13, 0.16, 1.00)
        accent    = (0.20, 0.50, 0.90, 1.00)
        accent_hv = (0.30, 0.60, 1.00, 1.00)

        def sc(col, rgba):
            try:
                style.set_color(col, rgba)  # type: ignore[attr-defined]
            except AttributeError:
                try:
                    style.colors[col] = rgba  # type: ignore[attr-defined]
                except (AttributeError, TypeError):
                    pass

        sc(imgui.Col_.window_bg,        dark_bg)
        sc(imgui.Col_.child_bg,         panel_bg)
        sc(imgui.Col_.frame_bg,         (0.16, 0.16, 0.20, 1.00))
        sc(imgui.Col_.frame_bg_hovered, (0.20, 0.20, 0.26, 1.00))
        sc(imgui.Col_.title_bg,         dark_bg)
        sc(imgui.Col_.title_bg_active,  (0.14, 0.14, 0.18, 1.00))
        sc(imgui.Col_.button,           accent)
        sc(imgui.Col_.button_hovered,   accent_hv)
        sc(imgui.Col_.button_active,    (0.10, 0.40, 0.80, 1.00))
        sc(imgui.Col_.header,           (0.18, 0.35, 0.60, 1.00))
        sc(imgui.Col_.header_hovered,   (0.22, 0.42, 0.72, 1.00))
        sc(imgui.Col_.header_active,    accent)
        sc(imgui.Col_.separator,        (0.25, 0.25, 0.30, 1.00))
        sc(imgui.Col_.tab,              (0.14, 0.14, 0.18, 1.00))
        sc(imgui.Col_.tab_hovered,      accent_hv)
        for tab_sel in ("tab_selected", "tab_active"):
            try:
                sc(getattr(imgui.Col_, tab_sel), accent)
                break
            except AttributeError:
                continue
        for dock_col, val in [
            ("docking_preview",  (*accent[:3], 0.70)),
            ("docking_empty_bg", (0.08, 0.08, 0.10, 1.00)),
        ]:
            try:
                sc(getattr(imgui.Col_, dock_col), val)
            except AttributeError:
                pass

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def _shutdown(self) -> None:
        """Clean up scene, imgui, and pygame."""
        _save_imgui_ini()

        if self._scene is not None:
            try:
                self._scene.on_exit()
            except Exception:
                pass

        if self._imgui_renderer is not None:
            self._imgui_renderer.shutdown()

        imgui.destroy_context()
        pygame.quit()


# ── CLI entry point ───────────────────────────────────────────────────────────

def _load_scene_class(scene_path: str) -> Type[Scene] | None:
    """Import a scene class from a dotted module path."""
    try:
        module_path, class_name = scene_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except Exception as exc:
        print(f"[editor] Could not load scene {scene_path!r}: {exc}", file=sys.stderr)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="pygame_engine Scene Editor")
    parser.add_argument(
        "--scene", "-s",
        default=None,
        help="Dotted path to a Scene class, e.g. mygame.scenes.main_menu.MainMenuScene",
    )
    args = parser.parse_args()

    scene_class = None
    if args.scene:
        scene_class = _load_scene_class(args.scene)
        if scene_class is None:
            sys.exit(1)

    EditorApplication(scene_class=scene_class).run()


if __name__ == "__main__":
    main()
