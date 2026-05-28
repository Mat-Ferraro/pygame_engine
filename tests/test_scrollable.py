"""
tests/test_scrollable.py

Tests for pygame_engine.ui.containers.Scrollable.

Covers: scroll clamping, max_scroll calculation, wheel event handling,
event position offsetting, child routing.
"""

import pygame
import pytest

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.containers.scrollable import Scrollable


# ── Helpers ───────────────────────────────────────────────────────────────────

class TrackingWidget(Widget):
    """Widget that records which events it received."""
    def __init__(self, rect):
        super().__init__(rect)
        self.received: list[pygame.event.Event] = []

    def _handle_event_widget(self, event):
        self.received.append(event)
        return True


VIEWPORT = pygame.Rect(0, 0, 300, 200)   # visible area
CONTENT  = pygame.Rect(0, 0, 300, 600)   # larger content


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_scroll_is_zero() -> None:
    s = Scrollable(VIEWPORT)
    assert s.scroll_y == 0.0


def test_no_child_max_scroll_is_zero() -> None:
    s = Scrollable(VIEWPORT)
    assert s._max_scroll() == 0.0


def test_max_scroll_equals_content_minus_viewport() -> None:
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)
    assert s._max_scroll() == 400.0   # 600 - 200


def test_content_fits_viewport_max_scroll_is_zero() -> None:
    child = Widget(pygame.Rect(0, 0, 300, 150))
    s = Scrollable(VIEWPORT, child=child)
    assert s._max_scroll() == 0.0


# ── Scroll control ────────────────────────────────────────────────────────────

def test_scroll_by_positive_moves_down() -> None:
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)
    s.scroll_by(50)
    assert s.scroll_y == 50.0


def test_scroll_by_clamped_at_max() -> None:
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)
    s.scroll_by(9999)
    assert s.scroll_y == s._max_scroll()


def test_scroll_by_clamped_at_zero() -> None:
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)
    s.scroll_by(-100)
    assert s.scroll_y == 0.0


def test_scroll_to_bottom() -> None:
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)
    s.scroll_to_bottom()
    assert s.scroll_y == s._max_scroll()


def test_scroll_to_top_resets_to_zero() -> None:
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)
    s.scroll_by(200)
    s.scroll_to_top()
    assert s.scroll_y == 0.0


def test_setting_child_resets_scroll() -> None:
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)
    s.scroll_by(200)
    s.child = Widget(CONTENT)
    assert s.scroll_y == 0.0


# ── Event handling ────────────────────────────────────────────────────────────

def test_wheel_event_inside_viewport_scrolls(monkeypatch) -> None:
    """
    A wheel event scrolls when the cursor is over the viewport.

    MOUSEWHEEL events carry no position, so Scrollable reads the cursor
    via ``pygame.mouse.get_pos()``. We monkeypatch that to a fixed point
    inside the viewport rather than calling ``pygame.mouse.set_pos()`` —
    the latter writes the real OS cursor, which doesn't reliably stick in
    headless / CI / out-of-focus runs and makes this test order-dependent.
    Patching ``get_pos`` makes the test deterministic in any environment.
    """
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)

    # Cursor inside the viewport — deterministic, no real OS mouse involved.
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (100, 100))

    wheel = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": -1, "flipped": False})
    consumed = s.handle_event(wheel)

    assert consumed is True
    assert s.scroll_y == s._scroll_speed


def test_wheel_event_outside_viewport_ignored(monkeypatch) -> None:
    """
    A wheel event does nothing when the cursor is outside the viewport.

    The complement of the test above — guards the collidepoint branch in
    Scrollable's wheel handling. Also deterministic via monkeypatch.
    """
    child = Widget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)

    # Cursor well outside the 300x200 viewport.
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (5000, 5000))

    wheel = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": -1, "flipped": False})
    consumed = s.handle_event(wheel)

    assert consumed is False
    assert s.scroll_y == 0.0


def test_mouse_event_routed_to_child_with_offset() -> None:
    child = TrackingWidget(CONTENT)
    s = Scrollable(pygame.Rect(50, 50, 300, 200), child=child)
    s.scroll_by(100)

    # Click at screen pos (100, 100) — inside viewport
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        "pos": (100, 100), "button": 1
    })
    s.handle_event(click)

    assert len(child.received) == 1
    # Adjusted pos: (100-50, 100-50+100) = (50, 150)
    adjusted_pos = child.received[0].pos
    assert adjusted_pos[0] == 50
    assert adjusted_pos[1] == 150


def test_mouse_event_outside_viewport_not_routed() -> None:
    child = TrackingWidget(CONTENT)
    s = Scrollable(pygame.Rect(50, 50, 300, 200), child=child)

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        "pos": (10, 10), "button": 1   # outside viewport
    })
    s.handle_event(click)
    assert len(child.received) == 0


def test_invisible_scrollable_ignores_events() -> None:
    child = TrackingWidget(CONTENT)
    s = Scrollable(VIEWPORT, child=child)
    s.visible = False

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
        "pos": (100, 100), "button": 1
    })
    consumed = s.handle_event(click)
    assert consumed is False
