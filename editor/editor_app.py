"""
EditorApplication — the scene editor entry point.

Wraps a pygame_engine Application in an ImGui docking layout. The game
scene renders into a pygame subsurface which is then displayed as an
ImGui image widget. All editor panels (hierarchy, inspector, scene)
surround the viewport.

Architecture
------------
- pygame owns the OpenGL/SDL window and the game rendering surface
- imgui-bundle provides the editor UI panels via the pygame backend
- The game scene runs with time_scale=0 in edit mode (nothing moves)
- The game scene is completely unaware of the editor's existence

Persistence
-----------
Three independent things persist between sessions:

1. **ImGui panel/dock geometry** — handled entirely by ImGui itself. We
   point ``io.ini_filename`` at a fixed absolute path (``editor/imgui.ini``)
   *before the first frame* so ImGui both loads and auto-saves it.

2. **Editor settings** — grid size, overlay toggles, last scene — live in
   ``editor/editor_settings.json`` via ``editor.editor_settings``.

3. **Scene layout** — the widget rects/props of the scene being edited —
   live in a ``*.layout.json`` next to the scene module.

The default dock layout
-----------------------
``DEFAULT_LAYOUT_INI`` below is a hardcoded ImGui settings string — a
hand-tuned panel layout captured from a real ``imgui.ini``. It is used as a
fallback in exactly two cases:

* **First run** — there is no ``editor/imgui.ini`` on disk yet.
* **Reset Layout** — the user picks View → Reset Layout.

In both cases we feed the string straight to
``imgui.load_ini_settings_from_memory()``. ImGui parses it with the same
code path it uses for a real ini file, so the editor is restored to that
exact layout — Scene wide on the left, Hierarchy and Inspector as two
side-by-side columns on the right. No fraction math, no dock-builder; the
hand-tuned file IS the default.

To change the default: lay panels out the way you like, quit (which writes
``editor/imgui.ini``), then paste that file's contents into
``DEFAULT_LAYOUT_INI``.

The captured layout is sized for a 1600x900 window. ImGui automatically
rescales dock nodes to the actual dockspace, so other window sizes still
get a sensible layout.

Caveat: the descriptor is currently a parallel model. Loading a layout
updates the descriptor, but unless the scene rebuilds its real widgets
from the descriptor, the viewport will keep showing the code-built layout.
The inspector and hierarchy reflect the loaded data correctly either way.

Usage::

    python -m editor
    python editor/editor_app.py
    python -m editor --scene mygame.scenes.main_menu.MainMenuScene
"""

from __future__ import annotations

import argparse
import importlib
import pathlib
import sys
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
from editor.editor_settings import load_settings, save_settings
from editor.panels.toolbar import render_toolbar
from editor.panels.hierarchy import render_hierarchy
from editor.panels.inspector import render_inspector


# ── Constants ─────────────────────────────────────────────────────────────────

EDITOR_WIDTH  = 1600
EDITOR_HEIGHT = 900
PANEL_WIDTH   = 280     # nominal hierarchy + inspector side panel width
TOOLBAR_H     = 56      # menu bar (~20px) + controls bar (32px) + padding (4px)
VIEWPORT_W    = EDITOR_WIDTH - PANEL_WIDTH
VIEWPORT_H    = EDITOR_HEIGHT - TOOLBAR_H
EDITOR_TITLE  = "pygame_engine — Scene Editor"

#: Absolute path to the ImGui layout file. Resolved relative to this module
#: so it is stable regardless of the process working directory.
IMGUI_INI_PATH = pathlib.Path(__file__).resolve().parent / "imgui.ini"

#: Window titles. Used by begin(); MUST match the [Window][...] sections in
#: DEFAULT_LAYOUT_INI exactly, or ImGui cannot place the window.
WIN_HIERARCHY = "Hierarchy"
WIN_INSPECTOR = "Inspector"
WIN_SCENE     = "Scene"

# ── Hardcoded default panel layout ───────────────────────────────────────────
# A hand-tuned ImGui settings string. Used verbatim as the fallback layout
# when editor/imgui.ini is missing (first run) or the user resets the layout.
# This is the exact format ImGui itself writes — to update the default,
# arrange the panels, quit, and paste the new editor/imgui.ini contents here.
DEFAULT_LAYOUT_INI = """\
[Window][WindowOverViewport_11111111]
Pos=0,75
Size=1600,825
Collapsed=0

[Window][Debug##Default]
Pos=60,60
Size=400,400
Collapsed=0

[Window][Hierarchy]
Pos=1206,75
Size=183,825
Collapsed=0
DockId=0x00000001,0

[Window][Inspector]
Pos=1391,75
Size=209,825
Collapsed=0
DockId=0x00000002,0

[Window][Scene]
Pos=0,75
Size=1204,825
Collapsed=0
DockId=0x00000003,0

[Docking][Data]
DockSpace     ID=0x08BD597D Window=0x1BBC0F80 Pos=0,75 Size=1600,825 Split=X
  DockNode    ID=0x00000003 Parent=0x08BD597D SizeRef=1204,825 CentralNode=1 Selected=0xE601B12F
  DockNode    ID=0x00000004 Parent=0x08BD597D SizeRef=394,825 Split=X Selected=0xBABDAE5E
    DockNode  ID=0x00000001 Parent=0x00000004 SizeRef=183,825 Selected=0xBABDAE5E
    DockNode  ID=0x00000002 Parent=0x00000004 SizeRef=209,825 Selected=0x36DC96AB
"""


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

        # These are created in run()
        self._display:        pygame.Surface | None = None
        self._viewport:       pygame.Surface | None = None   # pygame subsurface
        self._imgui_renderer: PygameRenderer | None = None
        self._app:            Application | None = None
        self._scene:          Scene | None = None
        self._tex_id:          int  = 0      # OpenGL texture id for viewport image

        # True = apply the hardcoded default layout this frame. Set on the
        # first run (no ini) and whenever the user picks "Reset Layout".
        self._reset_layout_flag: bool = True

        # Where this scene's layout is saved. None = persistence unavailable.
        self._layout_path: Path | None = None

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self) -> None:
        """Initialise everything and enter the editor frame loop."""
        pygame.init()

        if load_settings(self._state):
            print("[editor] loaded editor settings")
        else:
            print("[editor] no editor settings file — using defaults")

        self._display = pygame.display.set_mode(
            (EDITOR_WIDTH, EDITOR_HEIGHT),
            pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE,
        )
        pygame.display.set_caption(EDITOR_TITLE)

        # ── imgui initialisation ──────────────────────────────────────────────
        imgui.create_context()
        io = imgui.get_io()
        io.config_flags |= imgui.ConfigFlags_.docking_enable
        io.config_flags |= imgui.ConfigFlags_.nav_enable_keyboard

        self._bind_imgui_ini(io)

        self._imgui_renderer = PygameRenderer()

        io.display_size = imgui.ImVec2(float(EDITOR_WIDTH), float(EDITOR_HEIGHT))
        io.display_framebuffer_scale = imgui.ImVec2(1.0, 1.0)

        imgui.style_colors_dark()
        self._apply_editor_style()

        # Decide whether to apply the hardcoded default layout. If a saved
        # editor/imgui.ini exists, ImGui has already restored it during
        # _bind_imgui_ini() and we leave it alone. If not, flag the default
        # layout to be applied on the first frame.
        if IMGUI_INI_PATH.exists():
            self._reset_layout_flag = False
            print("[editor] imgui.ini found — restoring saved panel layout")
        else:
            self._reset_layout_flag = True
            print("[editor] no imgui.ini — applying hardcoded default layout")

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

    # ── ImGui ini binding ─────────────────────────────────────────────────────

    def _bind_imgui_ini(self, io: "imgui.IO") -> None:
        """
        Point ImGui's settings system at ``IMGUI_INI_PATH``.

        Binding this BEFORE the first frame is what makes ImGui both load the
        saved dock layout on startup and auto-save it on its own timer.
        Different imgui-bundle versions expose this via a setter method or a
        writable property; we try both, then fall back to a manual load.
        """
        ini = str(IMGUI_INI_PATH)
        IMGUI_INI_PATH.parent.mkdir(parents=True, exist_ok=True)

        bound = False
        setter = getattr(io, "set_ini_filename", None)
        if callable(setter):
            try:
                setter(ini)
                bound = True
            except Exception:
                bound = False

        if not bound:
            try:
                io.ini_filename = ini  # type: ignore[attr-defined]
                bound = True
            except Exception:
                bound = False

        if bound:
            print(f"[editor] imgui.ini bound to {ini}")
            return

        print("[editor] could not bind io.ini_filename — loading ini manually")
        if IMGUI_INI_PATH.exists():
            try:
                imgui.load_ini_settings_from_disk(ini)  # type: ignore[attr-defined]
            except Exception as exc:
                print(f"[editor] manual ini load failed: {exc}")

    def _apply_default_layout(self) -> None:
        """
        Apply the hardcoded ``DEFAULT_LAYOUT_INI`` to ImGui.

        Feeds the string straight into ImGui's settings parser, the same
        code path used for a real ini file. Called on the first frame when
        there is no saved layout, and again whenever the user resets the
        layout. ImGui rescales the dock nodes to the live dockspace, so the
        captured 1600x900 layout still works at other window sizes.
        """
        try:
            imgui.load_ini_settings_from_memory(DEFAULT_LAYOUT_INI)  # type: ignore[attr-defined]
            print("[editor] applied hardcoded default layout")
        except Exception as exc:
            print(f"[editor] could not apply default layout: {exc}",
                  file=sys.stderr)

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
                    if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
                        self._state.request(self._state.ACTION_SAVE_LAYOUT)

            self._handle_pending_action()
            self._update_scene(dt)
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

    # ── Actions ───────────────────────────────────────────────────────────────

    def _handle_pending_action(self) -> None:
        """Consume and act on a one-shot action from the toolbar or a hotkey."""
        action = self._state.take_pending_action()
        if action is None:
            return
        if action == self._state.ACTION_SAVE_LAYOUT:
            self._save_layout()

    def _save_layout(self) -> None:
        """Save the current scene descriptor to its layout file."""
        descriptor = self._get_descriptor()
        if descriptor is None:
            self._state.set_status("Save Layout: no descriptor to save")
            return
        if self._layout_path is None:
            self._state.set_status("Save Layout: no layout path for this scene")
            return

        try:
            descriptor.save(self._layout_path)
            self._state.set_status(f"Layout saved → {self._layout_path.name}")
            print(f"[editor] saved layout to {self._layout_path}")
        except OSError as exc:
            self._state.set_status(f"Save Layout failed: {exc}")
            print(f"[editor] save layout FAILED: {exc}", file=sys.stderr)

    def _update_scene(self, dt: float) -> None:
        """Advance the scene (dt is 0 in edit mode)."""
        if self._scene is None:
            return
        effective_dt = dt if self._state.mode == EditorMode.PLAY else 0.0
        try:
            self._scene.update(effective_dt)
        except Exception as exc:
            self._state.set_status(f"Error in update(): {exc}")

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

        if self._state.show_grid and self._state.is_editing:
            self._draw_grid()

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

    # ── ImGui layout ──────────────────────────────────────────────────────────

    def _render_imgui(self) -> None:
        """Render all ImGui panels for this frame."""
        descriptor = self._get_descriptor()

        # A reset is requested either by the first-run flag or by the toolbar's
        # "Reset Layout" menu item. Consume both — they are one-shot.
        was_reset = self._reset_layout_flag or getattr(self._state, "reset_layout", False)
        self._reset_layout_flag = False
        if hasattr(self._state, "reset_layout"):
            self._state.reset_layout = False

        # Apply the hardcoded default layout BEFORE any window is begun this
        # frame, so ImGui places the panels using the freshly loaded settings.
        if was_reset:
            self._apply_default_layout()

        render_toolbar(self._state)
        self._render_panels(descriptor)

    def _render_panels(self, descriptor) -> None:
        """
        Render all editor panels inside a shared DockSpace.

        Panel geometry is never forced here. On a normal frame ImGui's saved
        ini owns it; on a reset frame the hardcoded default layout was just
        loaded into ImGui by ``_apply_default_layout()`` and ImGui places the
        panels from that. Only size constraints (min/max) are applied, which
        never fight the loaded layout.
        """
        # ── DockSpace below the toolbar ──────────────────────────────────────
        try:
            vp = imgui.get_main_viewport()
            orig_pos  = vp.work_pos
            orig_size = vp.work_size
            vp.work_pos  = imgui.ImVec2(orig_pos.x,  orig_pos.y  + TOOLBAR_H)  # type: ignore[attr-defined]
            vp.work_size = imgui.ImVec2(orig_size.x, orig_size.y - TOOLBAR_H)  # type: ignore[attr-defined]
            imgui.dock_space_over_viewport(0, vp, 0)
            vp.work_pos  = orig_pos   # type: ignore[attr-defined]
            vp.work_size = orig_size  # type: ignore[attr-defined]
        except Exception:
            try:
                imgui.dock_space_over_viewport(0, imgui.get_main_viewport(), 0)
            except Exception:
                pass

        # ── Panel windows ────────────────────────────────────────────────────
        imgui.set_next_window_size_constraints(
            imgui.ImVec2(120, 100), imgui.ImVec2(EDITOR_WIDTH * 0.5, EDITOR_HEIGHT),
        )
        render_hierarchy(self._state, descriptor)

        imgui.set_next_window_size_constraints(
            imgui.ImVec2(120, 100), imgui.ImVec2(EDITOR_WIDTH * 0.5, EDITOR_HEIGHT),
        )
        render_inspector(self._state, descriptor)

        # Scene — a normal, named, dockable window. NO no_saved_settings flag,
        # so ImGui persists its dock state like every other panel.
        imgui.set_next_window_size_constraints(
            imgui.ImVec2(200, 200), imgui.ImVec2(EDITOR_WIDTH, EDITOR_HEIGHT),
        )
        scene_flags = (
            getattr(imgui.WindowFlags_, "no_scrollbar",          0)
            | getattr(imgui.WindowFlags_, "no_scroll_with_mouse", 0)
        )
        imgui.begin(WIN_SCENE, None, scene_flags)
        if self._tex_id:
            size = imgui.get_content_region_avail()
            w, h = max(1.0, size.x), max(1.0, size.y)
            try:
                tex_ref = imgui.ImTextureRef(self._tex_id)  # type: ignore[arg-type]
                imgui.image(
                    tex_ref,
                    imgui.ImVec2(w, h),
                    imgui.ImVec2(0, 1),
                    imgui.ImVec2(1, 0),
                )
            except (AttributeError, TypeError):
                try:
                    imgui.image(self._tex_id, (w, h))  # type: ignore[arg-type]
                except Exception:
                    pass
        else:
            imgui.text_colored((0.4, 0.4, 0.4, 1.0), "Viewport loading...")
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
        self._scene, status, layout_path = load_scene_for_editor(
            self._scene_class,
            width=VIEWPORT_W,
            height=VIEWPORT_H,
        )
        self._state.set_status(status)
        self._layout_path = layout_path

        if self._scene is not None:
            self._state.scene_path = self._scene_class.__name__
        self._state.layout_path = str(layout_path) if layout_path else None

    # ── OpenGL texture upload ─────────────────────────────────────────────────

    def _surface_to_texture(self, surface: pygame.Surface) -> int:
        """Upload a pygame Surface to an OpenGL texture and return its id."""
        try:
            from OpenGL import GL as gl

            if self._tex_id:
                gl.glDeleteTextures([self._tex_id])

            texture_data = pygame.image.tobytes(surface, "RGBA", False)
            w, h = surface.get_size()

            tex_id = int(gl.glGenTextures(1))
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D,
                               gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0,
                gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, texture_data,
            )
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            return tex_id
        except Exception:
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
        """Clean up scene, persist state, and tear down imgui and pygame."""
        if self._state.is_editing:
            descriptor = self._get_descriptor()
            if descriptor is not None and self._layout_path is not None:
                try:
                    descriptor.save(self._layout_path)
                    print(f"[editor] layout saved on exit → {self._layout_path}")
                except OSError as exc:
                    print(f"[editor] layout save on exit FAILED: {exc}",
                          file=sys.stderr)

        try:
            save_settings(self._state)
            print("[editor] editor settings saved")
        except Exception as exc:
            print(f"[editor] settings save FAILED: {exc}", file=sys.stderr)

        try:
            imgui.save_ini_settings_to_disk(str(IMGUI_INI_PATH))  # type: ignore[attr-defined]
            print(f"[editor] imgui.ini saved → {IMGUI_INI_PATH}")
        except Exception as exc:
            print(f"[editor] imgui.ini save FAILED: {exc}", file=sys.stderr)

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
