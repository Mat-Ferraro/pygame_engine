import pygame
import pytest

from pygame_engine.ui.controls.slider import Slider


# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    """Return a default RenderContext for render() calls in tests."""
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

RECT = pygame.Rect(100, 100, 200, 24)


def test_default_value() -> None:
    s = Slider(RECT)
    assert s.value == 0.5


def test_custom_value_clamped() -> None:
    s = Slider(RECT, value=1.5, max_value=1.0)
    assert s.value == 1.0


def test_value_below_min_clamped() -> None:
    s = Slider(RECT, value=-1.0, min_value=0.0)
    assert s.value == 0.0


def test_normalised_at_min() -> None:
    s = Slider(RECT, value=0.0)
    assert s.normalised == pytest.approx(0.0)


def test_normalised_at_max() -> None:
    s = Slider(RECT, value=1.0)
    assert s.normalised == pytest.approx(1.0)


def test_normalised_midpoint() -> None:
    s = Slider(RECT, value=0.5)
    assert s.normalised == pytest.approx(0.5)


def test_on_change_fires_on_value_set() -> None:
    received: list[float] = []
    s = Slider(RECT, value=0.0, on_change=lambda v: received.append(v))
    s.value = 0.5
    assert received == [pytest.approx(0.5)]


def test_on_change_not_fired_when_same_value() -> None:
    received: list[float] = []
    s = Slider(RECT, value=0.5, on_change=lambda v: received.append(v))
    s.value = 0.5
    assert received == []


def test_keyboard_right_increases_value() -> None:
    s = Slider(RECT, value=0.5, step=0.1)
    s.focused = True
    key = pygame.event.Event(pygame.KEYDOWN,
                             {"key": pygame.K_RIGHT, "mod": 0,
                              "unicode": "", "scancode": 0})
    s.handle_event(key)
    assert s.value == pytest.approx(0.6)


def test_keyboard_left_decreases_value() -> None:
    s = Slider(RECT, value=0.5, step=0.1)
    s.focused = True
    key = pygame.event.Event(pygame.KEYDOWN,
                             {"key": pygame.K_LEFT, "mod": 0,
                              "unicode": "", "scancode": 0})
    s.handle_event(key)
    assert s.value == pytest.approx(0.4)


def test_keyboard_home_goes_to_min() -> None:
    s = Slider(RECT, value=0.8)
    s.focused = True
    s.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                      {"key": pygame.K_HOME, "mod": 0,
                                       "unicode": "", "scancode": 0}))
    assert s.value == pytest.approx(0.0)


def test_keyboard_end_goes_to_max() -> None:
    s = Slider(RECT, value=0.2)
    s.focused = True
    s.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                      {"key": pygame.K_END, "mod": 0,
                                       "unicode": "", "scancode": 0}))
    assert s.value == pytest.approx(1.0)


def test_keyboard_not_active_when_unfocused() -> None:
    s = Slider(RECT, value=0.5, step=0.1)
    s.focused = False
    s.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                      {"key": pygame.K_RIGHT, "mod": 0,
                                       "unicode": "", "scancode": 0}))
    assert s.value == pytest.approx(0.5)


def test_focusable_by_default() -> None:
    assert Slider(RECT).focusable is True


def test_click_sets_value() -> None:
    s = Slider(RECT, value=0.0)
    # Click at the rightmost part of the track
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (RECT.right - 10, RECT.centery), "button": 1})
    s.handle_event(click)
    assert s.value > 0.8


def test_render_does_not_raise(display_surface) -> None:
    Slider(RECT, value=0.5).render(display_surface, _ctx())


def test_invisible_slider_skips_render(display_surface) -> None:
    s = Slider(RECT)
    s.visible = False
    s.render(display_surface, _ctx())


def test_custom_range() -> None:
    s = Slider(RECT, value=50.0, min_value=0.0, max_value=100.0)
    assert s.value == pytest.approx(50.0)
    assert s.normalised == pytest.approx(0.5)