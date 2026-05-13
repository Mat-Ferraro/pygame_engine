"""tests/test_checkbox.py — Checkbox widget tests."""

import pygame

from pygame_engine.ui.controls.checkbox import Checkbox

RECT = pygame.Rect(100, 100, 200, 32)


def test_default_unchecked() -> None:
    assert Checkbox(RECT).checked is False


def test_initial_checked() -> None:
    assert Checkbox(RECT, checked=True).checked is True


def test_toggle_flips_state() -> None:
    c = Checkbox(RECT, checked=False)
    c.toggle()
    assert c.checked is True
    c.toggle()
    assert c.checked is False


def test_on_change_fires_on_toggle() -> None:
    vals: list[bool] = []
    c = Checkbox(RECT, on_change=lambda v: vals.append(v))
    c.toggle()
    assert vals == [True]


def test_on_change_fires_via_setter() -> None:
    vals: list[bool] = []
    c = Checkbox(RECT, on_change=lambda v: vals.append(v))
    c.checked = True
    assert vals == [True]


def test_setter_no_fire_when_same() -> None:
    vals: list[bool] = []
    c = Checkbox(RECT, checked=True, on_change=lambda v: vals.append(v))
    c.checked = True
    assert vals == []


def test_click_inside_toggles() -> None:
    c = Checkbox(RECT, checked=False)
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": RECT.center, "button": 1})
    c.handle_event(click)
    assert c.checked is True


def test_click_outside_no_toggle() -> None:
    c = Checkbox(RECT, checked=False)
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (0, 0), "button": 1})
    c.handle_event(click)
    assert c.checked is False


def test_space_toggles_when_focused() -> None:
    c = Checkbox(RECT, checked=False)
    c.focused = True
    c.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                      {"key": pygame.K_SPACE, "mod": 0,
                                       "unicode": " ", "scancode": 0}))
    assert c.checked is True


def test_space_no_toggle_when_unfocused() -> None:
    c = Checkbox(RECT, checked=False)
    c.focused = False
    c.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                      {"key": pygame.K_SPACE, "mod": 0,
                                       "unicode": " ", "scancode": 0}))
    assert c.checked is False


def test_focusable_by_default() -> None:
    assert Checkbox(RECT).focusable is True


def test_render_does_not_raise(display_surface) -> None:
    Checkbox(RECT, label="Enable VSync", checked=True).render(display_surface)


def test_render_unchecked_does_not_raise(display_surface) -> None:
    Checkbox(RECT, label="Fullscreen", checked=False).render(display_surface)


def test_invisible_skips_render(display_surface) -> None:
    c = Checkbox(RECT)
    c.visible = False
    c.render(display_surface)
