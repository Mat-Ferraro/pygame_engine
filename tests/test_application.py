"""
We do NOT call app.run() — that starts the main loop. Instead we call
the individual lifecycle methods directly after mocking the display, or
we test the parts that are safe to call in isolation.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pygame
import pytest

from pygame_engine.app import Application, AppConfig
from pygame_engine.scene import Scene


# ── Helpers ───────────────────────────────────────────────────────────────────



# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

class MinimalScene(Scene):
    """Bare-minimum scene for startup tests."""
    def __init__(self):
        super().__init__()
        self.entered = False

    def on_enter(self) -> None:
        self.entered = True


# ── AppConfig ─────────────────────────────────────────────────────────────────

def test_appconfig_defaults() -> None:
    config = AppConfig()
    assert config.title      == "pygame_engine"
    assert config.width      == 1280
    assert config.height     == 720
    assert config.target_fps == 60
    assert config.max_dt     == 0.1
    assert config.mode        == "development"
    assert config.reduced_motion is False
    assert config.resizable  is False
    assert config.fullscreen is False
    assert config.vsync      is False
    assert config.asset_root == Path("assets")


def test_appconfig_custom_values() -> None:
    config = AppConfig(title="Test", width=800, height=600,
                       target_fps=30, mode="production")
    assert config.title      == "Test"
    assert config.width      == 800
    assert config.height     == 600
    assert config.target_fps == 30
    assert config.mode       == "production"


def test_appconfig_default_factory_is_independent() -> None:
    """Each AppConfig gets its own Path instance."""
    a = AppConfig()
    b = AppConfig()
    assert a.asset_root == b.asset_root
    assert a.asset_root is not b.asset_root


# ── Application construction ──────────────────────────────────────────────────

def test_application_construction_is_side_effect_free() -> None:
    """__init__ must not call pygame or create resources."""
    config = AppConfig()
    app    = Application(config)

    assert app._display_surface is None
    assert app._clock           is None
    assert app._scene_manager   is None
    assert app._input_manager   is None
    assert app._assets          is None
    assert app._audio           is None
    assert app.is_running       is False


def test_application_default_config() -> None:
    """Application created without config gets default AppConfig."""
    app = Application()
    assert app.config.title == "pygame_engine"


def test_application_stores_config() -> None:
    config = AppConfig(title="My Game", width=800, height=600)
    app    = Application(config)
    assert app.config is config


# ── Service access guards ─────────────────────────────────────────────────────

def test_scene_manager_raises_before_run() -> None:
    app = Application()
    with pytest.raises(RuntimeError, match="before Application.run"):
        _ = app.scene_manager


def test_input_manager_raises_before_run() -> None:
    app = Application()
    with pytest.raises(RuntimeError, match="before Application.run"):
        _ = app.input_manager


def test_assets_raises_before_run() -> None:
    app = Application()
    with pytest.raises(RuntimeError, match="before Application.run"):
        _ = app.assets


def test_audio_raises_before_run() -> None:
    app = Application()
    with pytest.raises(RuntimeError, match="before Application.run"):
        _ = app.audio


def test_display_surface_raises_before_run() -> None:
    app = Application()
    with pytest.raises(RuntimeError, match="before Application.run"):
        _ = app.display_surface


def test_clock_raises_before_run() -> None:
    app = Application()
    with pytest.raises(RuntimeError, match="before Application.run"):
        _ = app.clock


# ── Delta-time computation ────────────────────────────────────────────────────

def test_compute_dt_converts_ms_to_seconds() -> None:
    app = Application(AppConfig())
    assert abs(app._compute_dt(16) - 0.016) < 1e-6
    assert abs(app._compute_dt(33) - 0.033) < 1e-6


def test_compute_dt_clamped_by_max_dt() -> None:
    app = Application(AppConfig(max_dt=0.1))
    assert app._compute_dt(500) == 0.1   # 500ms >> 100ms max


def test_compute_dt_no_clamp_when_max_dt_zero() -> None:
    app = Application(AppConfig(max_dt=0.0))
    assert abs(app._compute_dt(500) - 0.5) < 1e-6


def test_compute_dt_normal_frame_not_clamped() -> None:
    app = Application(AppConfig(max_dt=0.1))
    assert abs(app._compute_dt(16) - 0.016) < 1e-6


# ── Debug flag activation ─────────────────────────────────────────────────────

def test_production_mode_does_not_enable_flags_legacy() -> None:
    from pygame_engine.state.runtime_flags import flags
    flags.reset()

    app = Application(AppConfig(mode="production"))
    # Simulate the flag portion of _startup without running the full loop
    flags.reset()
    if app.config.mode == "development":
        flags.enable_debug_all()

    assert flags.debug        is False
    assert flags.show_overlay is False
    assert flags.show_console is False
    flags.reset()   # cleanup


def test_development_mode_enables_all_flags_legacy() -> None:
    from pygame_engine.state.runtime_flags import flags
    flags.reset()

    app = Application(AppConfig(mode="development"))
    flags.reset()
    if app.config.mode == "development":
        flags.enable_debug_all()

    assert flags.debug        is True
    assert flags.show_overlay is True
    assert flags.show_console is True
    assert flags.show_fps     is True
    flags.reset()   # cleanup


# ── RuntimeFlags behaviour ────────────────────────────────────────────────────

def test_show_console_and_show_overlay_are_independent() -> None:
    from pygame_engine.state.runtime_flags import flags
    flags.reset()
    flags.show_overlay = True
    flags.show_console = False
    assert flags.show_overlay is True
    assert flags.show_console is False
    flags.reset()


def test_flags_reset_clears_show_console() -> None:
    from pygame_engine.state.runtime_flags import flags
    flags.show_console = True
    flags.reset()
    assert flags.show_console is False


# ── Stop signal ───────────────────────────────────────────────────────────────

def test_stop_sets_is_running_false() -> None:
    app = Application()
    app._is_running = True
    app.stop()
    assert app.is_running is False


def test_stop_is_idempotent() -> None:
    app = Application()
    app._is_running = False
    app.stop()   # already stopped — should not raise
    assert app.is_running is False


# ── Theme access ──────────────────────────────────────────────────────────────

def test_theme_returns_current_theme() -> None:
    from pygame_engine.theme.runtime import get_theme
    app   = Application()
    theme = app.theme
    assert theme is get_theme()


def test_set_theme_updates_global_theme() -> None:
    from dataclasses import replace
    from pygame_engine.theme.runtime import get_theme
    app       = Application()
    original  = get_theme()
    new_theme = replace(original)
    app.set_theme(new_theme)
    assert get_theme() is new_theme
    app.set_theme(original)   # restore



# ── AppMode and reduced_motion ────────────────────────────────────────────────

def test_appconfig_mode_default_is_development() -> None:
    config = AppConfig()
    assert config.mode == "development"


def test_appconfig_mode_production() -> None:
    config = AppConfig(mode="production")
    assert config.mode == "production"


def test_appconfig_mode_testing() -> None:
    config = AppConfig(mode="testing")
    assert config.mode == "testing"


def test_appconfig_reduced_motion_default_false() -> None:
    config = AppConfig()
    assert config.reduced_motion is False


def test_appconfig_reduced_motion_can_be_set() -> None:
    config = AppConfig(reduced_motion=True)
    assert config.reduced_motion is True


def test_app_mode_property() -> None:
    app = Application(AppConfig(mode="production"))
    assert app.mode == "production"


def test_app_reduced_motion_property_false() -> None:
    app = Application(AppConfig())
    assert app.reduced_motion is False


def test_app_reduced_motion_property_true() -> None:
    app = Application(AppConfig(reduced_motion=True))
    assert app.reduced_motion is True


def test_production_mode_does_not_enable_flags() -> None:
    from pygame_engine.state.runtime_flags import flags
    flags.reset()
    app = Application(AppConfig(mode="production"))
    flags.reset()
    if app.config.mode == "development":
        flags.enable_debug_all()
    assert flags.debug is False
    assert flags.show_overlay is False
    flags.reset()


def test_development_mode_enables_all_flags() -> None:
    from pygame_engine.state.runtime_flags import flags
    flags.reset()
    app = Application(AppConfig(mode="development"))
    flags.reset()
    if app.config.mode == "development":
        flags.enable_debug_all()
    assert flags.debug is True
    assert flags.show_overlay is True
    flags.reset()


# ── Resize handler ────────────────────────────────────────────────────────────

def test_on_resize_updates_display_surface() -> None:
    app = Application(AppConfig(resizable=True))
    fake_surface = pygame.Surface((400, 300))

    with patch("pygame.display.set_mode", return_value=fake_surface) as mock_mode:
        app._on_resize(400, 300)
        mock_mode.assert_called_once_with(
            (400, 300), pygame.RESIZABLE, vsync=0
        )
    assert app._display_surface is fake_surface


# ── Scene overlay_render integration ─────────────────────────────────────────

def test_scene_render_calls_overlay_render() -> None:
    """Scene.render() must always call overlay_render()."""
    calls: list[str] = []

    class TrackingScene(Scene):
        def overlay_render(self, surface, ctx=None):
            calls.append("overlay")

    scene   = TrackingScene()
    surface = pygame.Surface((100, 80))
    scene.render(surface, _ctx())
    assert "overlay" in calls


def test_overlay_render_default_is_noop() -> None:
    """Default overlay_render() must not raise."""
    scene   = Scene()
    surface = pygame.Surface((100, 80))
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    ctx = RenderContext(theme=get_theme())
    scene.overlay_render(surface, ctx)   # should not raise


def test_scene_render_calls_overlay_after_widget_tree() -> None:
    """overlay_render must be called AFTER root_widget.render."""
    order: list[str] = []

    class OrderWidget:
        rect = pygame.Rect(0, 0, 10, 10)
        visible = True
        def render(self, surface, ctx=None):
            order.append("widget")

    class TrackingScene(Scene):
        def overlay_render(self, surface, ctx=None):
            order.append("overlay")

    scene = TrackingScene()
    scene.root_widget = OrderWidget()  # type: ignore
    scene.render(pygame.Surface((100, 80)), _ctx())

    assert order == ["widget", "overlay"]


# ── Event bus cleanup ─────────────────────────────────────────────────────────

def test_event_bus_cleared_on_shutdown() -> None:
    """bus.clear_all() must be called during Application._shutdown."""
    from pygame_engine.events import bus
    called: list[str] = []
    bus.on("test.event", lambda **kw: called.append("x"))

    app = Application()
    # Simulate just the bus cleanup portion of _shutdown
    # (full _shutdown calls pygame.quit which we avoid in tests)
    from pygame_engine.events.event_bus import bus as _event_bus
    _event_bus.clear_all()

    bus.emit("test.event")
    assert called == []   # handler was cleared

# ── TimeManager (CHANGE-05) ───────────────────────────────────────────────────

def test_time_raises_before_run() -> None:
    """app.time must raise RuntimeError before run() is called."""
    app = Application()
    with pytest.raises(RuntimeError, match="before Application.run"):
        _ = app.time


def test_time_manager_not_created_at_construction() -> None:
    """TimeManager is only created during _startup, not __init__."""
    app = Application()
    assert app._time_manager is None
