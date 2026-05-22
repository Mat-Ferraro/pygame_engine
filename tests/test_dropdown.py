# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

"""
Tests for pygame_engine.ui.controls.Dropdown.

Covers: construction, selection, on_change callback, keyboard navigation,
open/close, item_at hit-testing, overlay_render safety.
"""

import pygame
import pytest

from pygame_engine.ui.controls.dropdown import Dropdown

RECT = pygame.Rect(100, 100, 200, 42)
OPTS = ["Alpha", "Beta", "Gamma", "Delta"]


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_selected_index() -> None:
    d = Dropdown(RECT, OPTS, selected_index=0)
    assert d.selected_index == 0


def test_selected_label_matches_option() -> None:
    d = Dropdown(RECT, OPTS, selected_index=1)
    assert d.selected_label == "Beta"


def test_selected_value_defaults_to_label() -> None:
    d = Dropdown(RECT, OPTS, selected_index=2)
    assert d.selected_value == "Gamma"


def test_custom_values_used() -> None:
    d = Dropdown(RECT, ["Low", "High"], values=[0, 1], selected_index=1)
    assert d.selected_value == 1


def test_empty_options_raises() -> None:
    with pytest.raises(ValueError):
        Dropdown(RECT, [])


def test_mismatched_values_raises() -> None:
    with pytest.raises(ValueError):
        Dropdown(RECT, ["A", "B"], values=[1])


def test_placeholder_when_no_selection() -> None:
    d = Dropdown(RECT, OPTS, selected_index=-1, placeholder="Pick one")
    assert d.selected_label == "Pick one"


# ── Selection ─────────────────────────────────────────────────────────────────

def test_select_changes_index() -> None:
    d = Dropdown(RECT, OPTS, selected_index=0)
    d.select(2)
    assert d.selected_index == 2
    assert d.selected_label == "Gamma"


def test_select_fires_on_change() -> None:
    changes: list[tuple] = []
    d = Dropdown(RECT, OPTS, selected_index=0,
                 on_change=lambda v, i: changes.append((v, i)))
    d.select(1)
    assert changes == [("Beta", 1)]


def test_select_same_index_does_not_fire() -> None:
    changes: list[tuple] = []
    d = Dropdown(RECT, OPTS, selected_index=1,
                 on_change=lambda v, i: changes.append((v, i)))
    d.select(1)
    assert changes == []


def test_select_out_of_range_raises() -> None:
    d = Dropdown(RECT, OPTS)
    with pytest.raises(IndexError):
        d.select(99)


# ── Open / close ──────────────────────────────────────────────────────────────

def test_starts_closed() -> None:
    d = Dropdown(RECT, OPTS)
    assert d.is_open is False


def test_close_closes_dropdown() -> None:
    d = Dropdown(RECT, OPTS)
    d._open = True
    d.close()
    assert d.is_open is False


def test_click_on_button_opens_dropdown() -> None:
    d = Dropdown(RECT, OPTS)
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (150, 121), "button": 1})
    d.handle_event(click)
    assert d.is_open is True


def test_escape_closes_dropdown() -> None:
    d = Dropdown(RECT, OPTS)
    d._open_list()
    esc = pygame.event.Event(pygame.KEYDOWN,
                             {"key": pygame.K_ESCAPE, "mod": 0,
                              "unicode": "", "scancode": 0})
    d.handle_event(esc)
    assert d.is_open is False


# ── Keyboard navigation ───────────────────────────────────────────────────────

def test_down_arrow_moves_highlight_down() -> None:
    d = Dropdown(RECT, OPTS, selected_index=0)
    d._open_list()
    d._hovered_item = 0
    down = pygame.event.Event(pygame.KEYDOWN,
                              {"key": pygame.K_DOWN, "mod": 0,
                               "unicode": "", "scancode": 0})
    d.handle_event(down)
    assert d._hovered_item == 1


def test_up_arrow_moves_highlight_up() -> None:
    d = Dropdown(RECT, OPTS, selected_index=0)
    d._open_list()
    d._hovered_item = 2
    up = pygame.event.Event(pygame.KEYDOWN,
                            {"key": pygame.K_UP, "mod": 0,
                             "unicode": "", "scancode": 0})
    d.handle_event(up)
    assert d._hovered_item == 1


def test_up_arrow_clamped_at_zero() -> None:
    d = Dropdown(RECT, OPTS)
    d._open_list()
    d._hovered_item = 0
    up = pygame.event.Event(pygame.KEYDOWN,
                            {"key": pygame.K_UP, "mod": 0,
                             "unicode": "", "scancode": 0})
    d.handle_event(up)
    assert d._hovered_item == 0


def test_enter_selects_highlighted_item() -> None:
    changes: list[int] = []
    d = Dropdown(RECT, OPTS, selected_index=0,
                 on_change=lambda v, i: changes.append(i))
    d._open_list()
    d._hovered_item = 2
    enter = pygame.event.Event(pygame.KEYDOWN,
                               {"key": pygame.K_RETURN, "mod": 0,
                                "unicode": "", "scancode": 0})
    d.handle_event(enter)
    assert d.is_open is False
    assert d.selected_index == 2
    assert changes == [2]


# ── Hit testing ───────────────────────────────────────────────────────────────

def test_item_at_returns_minus_one_outside_list() -> None:
    d = Dropdown(RECT, OPTS)
    d._open_list()
    assert d._item_at((0, 0)) == -1


def test_item_at_returns_correct_index() -> None:
    d = Dropdown(RECT, OPTS)
    d._open_list()
    r = d._list_rect
    # Click centre of first item
    pos = (r.centerx, r.y + d._item_height // 2)
    assert d._item_at(pos) == 0


# ── Rendering ─────────────────────────────────────────────────────────────────

def test_render_does_not_raise(display_surface) -> None:
    d = Dropdown(RECT, OPTS)
    d.render(display_surface, _ctx())


def test_overlay_render_noop_when_closed(display_surface) -> None:
    d = Dropdown(RECT, OPTS)
    d.overlay_render(display_surface, _ctx())   # should not raise


def test_render_invisible_does_not_raise(display_surface) -> None:
    d = Dropdown(RECT, OPTS)
    d.visible = False
    d.render(display_surface, _ctx())
    d.overlay_render(display_surface, _ctx())