"""tests/test_radio_group.py — RadioGroup widget tests."""

import pygame
import pytest

from pygame_engine.ui.controls.radio_group import RadioGroup

RECT    = pygame.Rect(100, 100, 200, 120)
OPTIONS = ["Low", "Medium", "High"]


def test_empty_options_raises() -> None:
    with pytest.raises(ValueError):
        RadioGroup(RECT, options=[])


def test_default_selected_index() -> None:
    rg = RadioGroup(RECT, OPTIONS)
    assert rg.selected_index == 0


def test_custom_selected_index() -> None:
    rg = RadioGroup(RECT, OPTIONS, selected_index=2)
    assert rg.selected_index == 2


def test_selected_value_matches_label() -> None:
    rg = RadioGroup(RECT, OPTIONS, selected_index=1)
    assert rg.selected_value == "Medium"


def test_select_changes_index() -> None:
    rg = RadioGroup(RECT, OPTIONS)
    rg.select(2)
    assert rg.selected_index == 2


def test_select_fires_on_change() -> None:
    received: list = []
    rg = RadioGroup(RECT, OPTIONS, on_change=lambda i, v: received.append((i, v)))
    rg.select(1)
    assert received == [(1, "Medium")]


def test_select_same_index_does_not_fire() -> None:
    received: list = []
    rg = RadioGroup(RECT, OPTIONS, selected_index=0,
                    on_change=lambda i, v: received.append((i, v)))
    rg.select(0)
    assert received == []


def test_options_returns_copy() -> None:
    rg = RadioGroup(RECT, OPTIONS)
    opts = rg.options
    opts.append("Ultra")
    assert len(rg.options) == 3


def test_keyboard_down_moves_focus() -> None:
    rg = RadioGroup(RECT, OPTIONS, selected_index=0)
    rg.focused = True
    down = pygame.event.Event(pygame.KEYDOWN,
                              {"key": pygame.K_DOWN, "mod": 0,
                               "unicode": "", "scancode": 0})
    rg.handle_event(down)
    assert rg._focused_index == 1


def test_keyboard_up_moves_focus() -> None:
    rg = RadioGroup(RECT, OPTIONS, selected_index=2)
    rg.focused = True
    rg._focused_index = 2
    up = pygame.event.Event(pygame.KEYDOWN,
                            {"key": pygame.K_UP, "mod": 0,
                             "unicode": "", "scancode": 0})
    rg.handle_event(up)
    assert rg._focused_index == 1


def test_keyboard_down_clamped_at_last() -> None:
    rg = RadioGroup(RECT, OPTIONS, selected_index=2)
    rg.focused = True
    rg._focused_index = 2
    down = pygame.event.Event(pygame.KEYDOWN,
                              {"key": pygame.K_DOWN, "mod": 0,
                               "unicode": "", "scancode": 0})
    rg.handle_event(down)
    assert rg._focused_index == 2


def test_keyboard_space_selects_focused() -> None:
    received: list = []
    rg = RadioGroup(RECT, OPTIONS, selected_index=0,
                    on_change=lambda i, v: received.append((i, v)))
    rg.focused = True
    rg._focused_index = 2
    rg.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                       {"key": pygame.K_SPACE, "mod": 0,
                                        "unicode": " ", "scancode": 0}))
    assert rg.selected_index == 2
    assert received == [(2, "High")]


def test_focusable_by_default() -> None:
    assert RadioGroup(RECT, OPTIONS).focusable is True


def test_render_does_not_raise(display_surface) -> None:
    RadioGroup(RECT, OPTIONS, selected_index=1).render(display_surface)


def test_invisible_skips_render(display_surface) -> None:
    rg = RadioGroup(RECT, OPTIONS)
    rg.visible = False
    rg.render(display_surface)
