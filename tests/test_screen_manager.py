"""
tests/test_screen_manager.py

Tests for the screen manager additions:
- Scene.on_resize() hook
- SceneManager.notify_resize()
- Application._on_resize() wiring (scene notification + bus event)
- app.screen_rect reflects post-resize dimensions
"""

from unittest.mock import patch

import pygame
import pytest

from pygame_engine.app import Application, AppConfig
from pygame_engine.scene import Scene, SceneManager


# ── Scene.on_resize ───────────────────────────────────────────────────────────

def test_scene_on_resize_default_is_noop() -> None:
    """Base Scene.on_resize must not raise."""
    scene = Scene()
    scene.on_resize(1920, 1080)   # should not raise


def test_scene_on_resize_called_with_correct_dimensions() -> None:
    sizes: list[tuple] = []

    class ResizeScene(Scene):
        def on_resize(self, width, height):
            sizes.append((width, height))

    scene = ResizeScene()
    scene.on_resize(800, 600)
    assert sizes == [(800, 600)]


def test_scene_on_resize_is_overridable() -> None:
    rebuilt: list[bool] = []

    class LayoutScene(Scene):
        def on_resize(self, width, height):
            rebuilt.append(True)

    scene = LayoutScene()
    scene.on_resize(1280, 720)
    assert rebuilt == [True]


# ── SceneManager.notify_resize ────────────────────────────────────────────────

def test_notify_resize_calls_current_scene() -> None:
    sizes: list[tuple] = []

    class ResizeScene(Scene):
        def on_resize(self, w, h):
            sizes.append((w, h))

    manager = SceneManager()
    manager.push(ResizeScene())
    manager.notify_resize(1024, 768)
    assert sizes == [(1024, 768)]


def test_notify_resize_noop_when_no_scene() -> None:
    manager = SceneManager()
    manager.notify_resize(800, 600)   # should not raise


def test_notify_resize_only_calls_top_scene() -> None:
    bottom_calls: list[tuple] = []
    top_calls:    list[tuple] = []

    class BottomScene(Scene):
        def on_resize(self, w, h):
            bottom_calls.append((w, h))

    class TopScene(Scene):
        def on_resize(self, w, h):
            top_calls.append((w, h))

    manager = SceneManager()
    manager.push(BottomScene())
    manager.push(TopScene())
    manager.notify_resize(640, 480)

    assert top_calls    == [(640, 480)]
    assert bottom_calls == []            # not notified while covered


def test_notify_resize_reaches_new_top_after_pop() -> None:
    calls: list[str] = []

    class SceneA(Scene):
        def on_resize(self, w, h):
            calls.append("A")

    class SceneB(Scene):
        def on_resize(self, w, h):
            calls.append("B")

    manager = SceneManager()
    manager.push(SceneA())
    manager.push(SceneB())
    manager.notify_resize(800, 600)
    assert calls == ["B"]

    manager.pop()
    calls.clear()
    manager.notify_resize(800, 600)
    assert calls == ["A"]


# ── Application._on_resize wiring ────────────────────────────────────────────

def test_on_resize_fires_bus_event() -> None:
    from pygame_engine.events import bus

    received: list[dict] = []
    bus.on("window.resized", lambda **kw: received.append(kw))

    app = Application(AppConfig(resizable=True))
    fake = pygame.Surface((400, 300))

    with patch("pygame.display.set_mode", return_value=fake):
        app._on_resize(400, 300)

    bus.off("window.resized", lambda **kw: None)
    bus.clear("window.resized")

    assert len(received) == 1
    assert received[0]["width"]  == 400
    assert received[0]["height"] == 300


def test_on_resize_notifies_scene_manager() -> None:
    sizes: list[tuple] = []

    class ResizeScene(Scene):
        def on_resize(self, w, h):
            sizes.append((w, h))

    app = Application(AppConfig(resizable=True))
    app._scene_manager = SceneManager()
    app._scene_manager.push(ResizeScene())
    fake = pygame.Surface((640, 480))

    with patch("pygame.display.set_mode", return_value=fake):
        app._on_resize(640, 480)

    assert sizes == [(640, 480)]


def test_on_resize_updates_display_surface() -> None:
    app  = Application(AppConfig(resizable=True))
    fake = pygame.Surface((320, 240))

    with patch("pygame.display.set_mode", return_value=fake):
        app._on_resize(320, 240)

    assert app._display_surface is fake


# ── app.screen_rect ───────────────────────────────────────────────────────────

def test_screen_rect_before_run_uses_config() -> None:
    app = Application(AppConfig(width=1280, height=720))
    r   = app.screen_rect
    assert r.width  == 1280
    assert r.height == 720
    assert r.x == 0
    assert r.y == 0


def test_screen_rect_after_resize_reflects_new_size() -> None:
    app  = Application(AppConfig(resizable=True))
    fake = pygame.Surface((640, 480))

    with patch("pygame.display.set_mode", return_value=fake):
        app._on_resize(640, 480)

    r = app.screen_rect
    assert r.width  == 640
    assert r.height == 480


def test_screen_rect_is_at_origin() -> None:
    app = Application(AppConfig(width=800, height=600))
    r   = app.screen_rect
    assert r.topleft == (0, 0)
