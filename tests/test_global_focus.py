"""
Tests for pygame_engine.ui.global_focus.GlobalFocusManager (CHANGE-06).

No pygame display required — GlobalFocusManager has no display dependency.
Widget objects are used directly (no subclassing needed for basic tests).
"""

from __future__ import annotations

import pygame
import pytest

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.global_focus import GlobalFocusManager


# ── Helpers ───────────────────────────────────────────────────────────────────

RECT = pygame.Rect(0, 0, 100, 40)


def make_focusable(tab_index=None) -> Widget:
    w = Widget(RECT)
    w.focusable = True
    w.tab_index = tab_index
    return w


def make_display() -> Widget:
    w = Widget(RECT)
    w.focusable = False
    return w


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_focused_is_none() -> None:
    fm = GlobalFocusManager()
    assert fm.focused is None


def test_initial_candidates_empty() -> None:
    fm = GlobalFocusManager()
    fm.next_focus()   # should not raise with no candidates
    assert fm.focused is None


def test_default_focus_ring_colour() -> None:
    fm = GlobalFocusManager()
    assert fm.focus_ring_colour == (100, 180, 255)


def test_default_focus_ring_width() -> None:
    fm = GlobalFocusManager()
    assert fm.focus_ring_width == 2


# ── set_focus ─────────────────────────────────────────────────────────────────

def test_set_focus_marks_widget_focused() -> None:
    fm = GlobalFocusManager()
    w = make_focusable()
    fm.set_focus(w)
    assert w.focused is True
    assert fm.focused is w


def test_set_focus_clears_previous_widget() -> None:
    fm = GlobalFocusManager()
    w1 = make_focusable()
    w2 = make_focusable()
    fm.set_focus(w1)
    fm.set_focus(w2)
    assert w1.focused is False
    assert w2.focused is True


def test_set_focus_same_widget_is_noop() -> None:
    """Setting focus to the already-focused widget emits no event."""
    events: list = []
    from pygame_engine.events.event_bus import bus
    bus.on("ui.focus.changed", lambda widget=None: events.append(widget))

    fm = GlobalFocusManager()
    w = make_focusable()
    fm.set_focus(w)
    initial_count = len(events)
    fm.set_focus(w)   # same widget — no-op
    assert len(events) == initial_count

    bus.clear("ui.focus.changed")


# ── clear_focus ───────────────────────────────────────────────────────────────

def test_clear_focus_unfocuses_widget() -> None:
    fm = GlobalFocusManager()
    w = make_focusable()
    fm.set_focus(w)
    fm.clear_focus()
    assert w.focused is False
    assert fm.focused is None


def test_clear_focus_when_nothing_focused_does_not_raise() -> None:
    fm = GlobalFocusManager()
    fm.clear_focus()   # should not raise


# ── ui.focus.changed bus event ────────────────────────────────────────────────

def test_set_focus_emits_bus_event() -> None:
    from pygame_engine.events.event_bus import bus
    events: list = []
    bus.on("ui.focus.changed", lambda widget=None: events.append(widget))

    fm = GlobalFocusManager()
    w = make_focusable()
    fm.set_focus(w)
    assert events == [w]

    bus.clear("ui.focus.changed")


def test_clear_focus_emits_bus_event_with_none() -> None:
    from pygame_engine.events.event_bus import bus
    events: list = []
    bus.on("ui.focus.changed", lambda widget=None: events.append(widget))

    fm = GlobalFocusManager()
    w = make_focusable()
    fm.set_focus(w)
    events.clear()
    fm.clear_focus()
    assert events == [None]

    bus.clear("ui.focus.changed")


# ── set_candidates ────────────────────────────────────────────────────────────

def test_set_candidates_filters_non_focusable() -> None:
    fm = GlobalFocusManager()
    w1 = make_focusable()
    w2 = make_display()
    fm.set_candidates([w1, w2])
    assert w2 not in fm._candidates
    assert w1 in fm._candidates


def test_set_candidates_filters_invisible() -> None:
    fm = GlobalFocusManager()
    w = make_focusable()
    w.visible = False
    fm.set_candidates([w])
    assert fm._candidates == []


def test_set_candidates_filters_disabled() -> None:
    fm = GlobalFocusManager()
    w = make_focusable()
    w.enabled = False
    fm.set_candidates([w])
    assert fm._candidates == []


def test_set_candidates_tab_index_sorted_first() -> None:
    """tab_index widgets come before None-index widgets, sorted ascending."""
    fm = GlobalFocusManager()
    w_none = make_focusable(tab_index=None)
    w_5    = make_focusable(tab_index=5)
    w_1    = make_focusable(tab_index=1)
    fm.set_candidates([w_none, w_5, w_1])
    assert fm._candidates == [w_1, w_5, w_none]


def test_set_candidates_unindexed_preserve_order() -> None:
    """Unindexed widgets maintain the order they were supplied."""
    fm = GlobalFocusManager()
    a = make_focusable()
    b = make_focusable()
    c = make_focusable()
    fm.set_candidates([a, b, c])
    assert fm._candidates == [a, b, c]


# ── next_focus / prev_focus ───────────────────────────────────────────────────

def test_next_focus_moves_to_first_when_nothing_focused() -> None:
    fm = GlobalFocusManager()
    w1 = make_focusable()
    w2 = make_focusable()
    fm.set_candidates([w1, w2])
    fm.next_focus()
    assert fm.focused is w1


def test_next_focus_advances_to_next() -> None:
    fm = GlobalFocusManager()
    w1 = make_focusable()
    w2 = make_focusable()
    fm.set_candidates([w1, w2])
    fm.set_focus(w1)
    fm.next_focus()
    assert fm.focused is w2


def test_next_focus_wraps_around() -> None:
    fm = GlobalFocusManager()
    w1 = make_focusable()
    w2 = make_focusable()
    fm.set_candidates([w1, w2])
    fm.set_focus(w2)
    fm.next_focus()
    assert fm.focused is w1


def test_prev_focus_moves_to_last_when_nothing_focused() -> None:
    fm = GlobalFocusManager()
    w1 = make_focusable()
    w2 = make_focusable()
    fm.set_candidates([w1, w2])
    fm.prev_focus()
    assert fm.focused is w2


def test_prev_focus_goes_back() -> None:
    fm = GlobalFocusManager()
    w1 = make_focusable()
    w2 = make_focusable()
    fm.set_candidates([w1, w2])
    fm.set_focus(w2)
    fm.prev_focus()
    assert fm.focused is w1


def test_next_focus_no_candidates_does_not_raise() -> None:
    fm = GlobalFocusManager()
    fm.next_focus()
    assert fm.focused is None


# ── render_focus_ring ─────────────────────────────────────────────────────────

def test_render_focus_ring_no_focused_does_not_raise() -> None:
    fm = GlobalFocusManager()
    surf = pygame.Surface((200, 200))
    fm.render_focus_ring(surf)   # should not raise


def test_render_focus_ring_draws_on_surface() -> None:
    """After rendering, pixels near the widget edge should be the ring colour."""
    fm = GlobalFocusManager()
    fm.focus_ring_colour = (255, 0, 0)
    w = make_focusable()
    w.rect = pygame.Rect(10, 10, 80, 30)
    fm.set_focus(w)

    surf = pygame.Surface((200, 200))
    surf.fill((0, 0, 0))
    fm.render_focus_ring(surf)

    # The ring inflates by 1 px each side — check a corner pixel
    colour = surf.get_at((9, 9))[:3]   # top-left of inflated rect
    assert colour == (255, 0, 0)


def test_render_focus_ring_zero_size_rect_does_not_raise() -> None:
    fm = GlobalFocusManager()
    w = make_focusable()
    w.rect = pygame.Rect(0, 0, 0, 0)
    fm.set_focus(w)
    surf = pygame.Surface((200, 200))
    fm.render_focus_ring(surf)   # should not raise


# ── app.focus property ────────────────────────────────────────────────────────

def test_app_focus_available_before_run() -> None:
    """app.focus is available immediately — no pygame init required."""
    from pygame_engine.app import Application
    app = Application()
    assert isinstance(app.focus, GlobalFocusManager)


def test_app_focus_returns_same_instance() -> None:
    from pygame_engine.app import Application
    app = Application()
    assert app.focus is app.focus


# ── Widget.tab_index and focus_trap (CHANGE-06 fields) ───────────────────────

def test_widget_tab_index_default_none() -> None:
    w = Widget(RECT)
    assert w.tab_index is None


def test_widget_tab_index_can_be_set() -> None:
    w = Widget(RECT)
    w.tab_index = 3
    assert w.tab_index == 3


def test_widget_focus_trap_default_false() -> None:
    w = Widget(RECT)
    assert w.focus_trap is False


def test_widget_focus_trap_can_be_set() -> None:
    w = Widget(RECT)
    w.focus_trap = True
    assert w.focus_trap is True


# ── repr ──────────────────────────────────────────────────────────────────────

def test_repr_contains_key_info() -> None:
    fm = GlobalFocusManager()
    r = repr(fm)
    assert "GlobalFocusManager" in r
    assert "focused" in r
    assert "candidates" in r
