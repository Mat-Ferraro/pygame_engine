"""
editor/scene_loader.py

Loads a scene class for the editor without requiring a full Application.

The challenge: most scenes take an ``Application`` as their first constructor
argument. The editor doesn't run a full Application, so we need a lightweight
stub that satisfies the scene's needs for config, screen rect, and assets.

Strategy
--------
1. If the scene is a ``DescribedScene`` with no constructor args beyond self,
   instantiate it directly.
2. If the scene takes an ``Application`` argument, build a minimal
   ``EditorAppStub`` that satisfies the most common attribute accesses
   (config, screen_rect, input_manager, assets, audio, clock).
3. If the scene is a ``DescribedScene``, hand it the editor viewport size
   via ``set_screen_rect()`` BEFORE ``on_enter()`` — its ``_build_layout()``
   computes layout against that rect.
4. Call ``on_enter()`` to build the descriptor and realise the widget tree.
5. If a saved ``*.layout.json`` exists for this scene, load it over the
   freshly built descriptor.

The stub is intentionally dumb — it returns safe defaults for everything.
Scenes that crash during on_enter() in stub mode will show an error in
the status bar and open with an empty descriptor.

Layout file location
--------------------
The layout file sits next to the scene module's source file and is named
after it: a scene defined in ``game/scenes/main_menu.py`` gets the layout
``game/scenes/main_menu.layout.json``. ``layout_path_for_scene()`` derives
this. A scene may pin an explicit path via the ``layout_path`` class
attribute; that always wins.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Type

import pygame

from pygame_engine.app.config import AppConfig
from pygame_engine.scene.described_scene import DescribedScene
from pygame_engine.scene.scene import Scene


# ── EditorAppStub ─────────────────────────────────────────────────────────────

class _StubClock:
    def get_fps(self) -> float: return 0.0
    def tick(self, fps: int = 60) -> int: return 16


class _StubInputManager:
    def was_action_pressed(self, *a, **kw) -> bool: return False
    def is_action_down(self, *a, **kw) -> bool: return False
    def was_action_released(self, *a, **kw) -> bool: return False


class _StubAudio:
    class _Bus:
        class _Vol:
            value = 1.0
        volume = _Vol()
        muted  = _Vol()
    master = _Bus()
    music  = _Bus()
    sfx    = _Bus()
    ui     = _Bus()
    def play_sfx(self, *a, **kw): pass
    def play_music(self, *a, **kw): pass
    def stop_music(self, *a, **kw): pass


class _StubAssets:
    def image(self, *a, **kw): return None
    def font(self, *a, **kw): return None
    def sound(self, *a, **kw): return None
    def sysfont(self, *a, **kw): return None


class EditorAppStub:
    """
    Minimal Application-like object for use during editor scene loading.

    Satisfies the most common ``app.xxx`` accesses without requiring
    pygame display, mixer, or a full engine runtime.
    """

    def __init__(self, width: int = 1280, height: int = 720) -> None:
        self.config        = AppConfig(width=width, height=height,
                                       mode="development")
        self.input_manager = _StubInputManager()
        self.audio         = _StubAudio()
        self.assets        = _StubAssets()
        self.clock         = _StubClock()
        self._width        = width
        self._height       = height

    @property
    def screen_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self._width, self._height)

    def stop(self) -> None:
        pass

    @property
    def gizmos(self): return None

    @property
    def focus(self):
        from pygame_engine.ui.global_focus import GlobalFocusManager
        return GlobalFocusManager()

    @property
    def time(self):
        from pygame_engine.app.time_manager import TimeManager
        return TimeManager()


# ── Layout path resolution ────────────────────────────────────────────────────

def layout_path_for_scene(scene_class: Type[Scene]) -> Path | None:
    """
    Work out where this scene's ``*.layout.json`` lives.

    Resolution order:

    1. A non-``None`` ``layout_path`` class attribute is used verbatim.
    2. Otherwise the path is derived from the module's source file:
       ``<scene_source>.py`` -> ``<scene_source>.layout.json``.
    3. If neither is available, returns ``None`` (persistence disabled).

    Args:
        scene_class: The scene class being opened.

    Returns:
        An absolute ``Path`` to the layout file, or ``None``.
    """
    explicit = getattr(scene_class, "layout_path", None)
    if explicit is not None:
        return Path(explicit).resolve()

    try:
        source = inspect.getsourcefile(scene_class)
    except (TypeError, OSError):
        source = None

    if not source:
        return None

    return Path(source).resolve().with_suffix(".layout.json")


# ── Scene loading ─────────────────────────────────────────────────────────────

def load_scene_for_editor(
    scene_class: Type[Scene],
    width:  int = 1280,
    height: int = 720,
) -> tuple[Scene | None, str, Path | None]:
    """
    Instantiate a scene for editor preview.

    Builds a stub Application if the scene needs one, hands a
    ``DescribedScene`` the editor viewport size, calls ``on_enter()`` to
    realise the widget tree, then loads a saved layout file over it if one
    exists.

    Args:
        scene_class: The scene class to instantiate.
        width:       Viewport width in pixels.
        height:      Viewport height in pixels.

    Returns:
        A tuple ``(scene, status_message, layout_path)``:

        - ``scene``          — the scene instance, or ``None`` on failure.
        - ``status_message`` — a one-line summary for the status bar.
        - ``layout_path``    — where this scene's layout should be saved,
          or ``None`` if persistence is unavailable. Returned even when
          loading fails, so the caller can still wire up "Save Layout".
    """
    layout_path = layout_path_for_scene(scene_class)

    # Inspect constructor signature
    try:
        sig    = inspect.signature(scene_class.__init__)
        params = [p for p in sig.parameters.keys() if p != "self"]
    except (ValueError, TypeError):
        params = []

    try:
        stub = EditorAppStub(width=width, height=height)

        # Instantiate — pass stub as first arg if constructor expects it.
        scene = scene_class(stub) if params else scene_class()

        # A DescribedScene computes its layout against a screen rect. The
        # editor viewport is that rect — hand it over BEFORE on_enter() so
        # _build_layout() sees the right size on its first run.
        if isinstance(scene, DescribedScene):
            scene.set_screen_rect(pygame.Rect(0, 0, width, height))

        # Enter the scene — builds the descriptor and realises the widgets.
        scene.on_enter()

    except Exception as exc:
        return (
            None,
            f"Failed to load {scene_class.__name__}: {exc}",
            layout_path,
        )

    name = scene_class.__name__
    desc = getattr(scene, "layout", None)

    # Not a DescribedScene, or it never built a descriptor.
    if desc is None:
        return scene, f"Loaded: {name}  (no descriptor)", None

    # Load a saved layout over the code-built defaults, if one exists.
    layout_status = ""
    if layout_path is not None and layout_path.exists():
        try:
            desc.load(layout_path)
            layout_status = "  [layout restored]"
        except (ValueError, OSError) as exc:
            layout_status = f"  [layout file ignored: {exc}]"

    return (
        scene,
        f"Loaded: {name}  ({desc.node_count} nodes){layout_status}",
        layout_path,
    )
