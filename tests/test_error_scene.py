"""Tests for ErrorScene and Application error tier integration."""

from __future__ import annotations
import pytest
import pygame
from pygame_engine.scene.error_scene import ErrorScene
from pygame_engine.scene.scene import Scene


def make_error_scene(mode="development"):
    exc = ValueError("test error")
    return ErrorScene(exc, mode=mode)


# ── Construction ──────────────────────────────────────────────────────────────

def test_construction_does_not_raise() -> None:
    scene = make_error_scene()
    assert scene is not None

def test_stores_exception() -> None:
    exc = RuntimeError("oops")
    s = ErrorScene(exc, mode="development")
    assert s._exc is exc

def test_stores_mode() -> None:
    s = ErrorScene(ValueError(), mode="production")
    assert s._mode == "production"

def test_blocks_update_below() -> None:
    assert ErrorScene.blocks_update_below is True

def test_does_not_block_render_below() -> None:
    """ErrorScene shows the broken scene behind it as context."""
    assert ErrorScene.blocks_render_below is False


# ── on_enter populates lines ──────────────────────────────────────────────────

def test_development_mode_shows_traceback() -> None:
    try:
        raise ValueError("traceback test")
    except ValueError as exc:
        s = ErrorScene(exc, mode="development")
    s.on_enter()
    assert any("traceback test" in line.lower() or
               "valueerror" in line.lower()
               for line in s._lines)

def test_production_mode_shows_friendly_message() -> None:
    s = make_error_scene(mode="production")
    s.on_enter()
    assert any("unexpected error" in line.lower() or
               "restart" in line.lower()
               for line in s._lines)

def test_production_mode_no_traceback() -> None:
    s = make_error_scene(mode="production")
    s.on_enter()
    # Should not contain Python file paths
    assert not any("File " in line for line in s._lines)


# ── render does not raise ─────────────────────────────────────────────────────

def test_render_development_does_not_raise() -> None:
    s = make_error_scene(mode="development")
    s.on_enter()
    surface = pygame.Surface((800, 600))
    s.render(surface)

def test_render_production_does_not_raise() -> None:
    s = make_error_scene(mode="production")
    s.on_enter()
    surface = pygame.Surface((800, 600))
    s.render(surface)


# ── Application error tier — testing mode re-raises ──────────────────────────

def test_application_reraises_in_testing_mode() -> None:
    """In testing mode, runtime errors should propagate, not be swallowed."""
    from unittest.mock import patch, MagicMock
    from pygame_engine.app import Application, AppConfig

    class BrokenScene(Scene):
        def on_enter(self): pass
        def update(self, dt):
            raise RuntimeError("scene broke in testing")

    app = Application(AppConfig(mode="testing"))

    with pytest.raises(RuntimeError, match="scene broke in testing"):
        app._handle_runtime_error(
            RuntimeError("scene broke in testing"),
            phase="update",
        )


# ── repr ──────────────────────────────────────────────────────────────────────

def test_repr() -> None:
    s = make_error_scene()
    r = repr(s)
    assert "ErrorScene" in r
    assert "development" in r
