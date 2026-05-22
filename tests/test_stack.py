"""
Tests for pygame_engine.ui.containers.Stack.
"""

import pygame
import pytest

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.containers.stack import Stack



# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    """Return a default RenderContext for render() calls in tests."""
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

class TrackingWidget(Widget):
    """Records received events."""
    def __init__(self, rect):
        super().__init__(rect)
        self.received: list[pygame.event.Event] = []

    def _handle_event_widget(self, event):
        self.received.append(event)
        return True


RECT = pygame.Rect(0, 0, 400, 300)


# ── Construction ──────────────────────────────────────────────────────────────

def test_stack_starts_empty() -> None:
    s = Stack(RECT)
    assert len(s.children) == 0


def test_clip_defaults_false() -> None:
    s = Stack(RECT)
    assert s.clip is False


# ── Child management ──────────────────────────────────────────────────────────

def test_add_returns_widget() -> None:
    s = Stack(RECT)
    w = Widget(pygame.Rect(0, 0, 10, 10))
    result = s.add(w)
    assert result is w


def test_add_increases_child_count() -> None:
    s = Stack(RECT)
    s.add(Widget(pygame.Rect(0, 0, 10, 10)))
    s.add(Widget(pygame.Rect(0, 0, 10, 10)))
    assert len(s.children) == 2


def test_remove_existing_child_returns_true() -> None:
    s = Stack(RECT)
    w = Widget(pygame.Rect(0, 0, 10, 10))
    s.add(w)
    assert s.remove(w) is True
    assert len(s.children) == 0


def test_remove_absent_child_returns_false() -> None:
    s = Stack(RECT)
    w = Widget(pygame.Rect(0, 0, 10, 10))
    assert s.remove(w) is False


def test_clear_removes_all_children() -> None:
    s = Stack(RECT)
    s.add(Widget(pygame.Rect(0, 0, 10, 10)))
    s.add(Widget(pygame.Rect(0, 0, 10, 10)))
    s.clear()
    assert len(s.children) == 0


def test_children_is_snapshot() -> None:
    s = Stack(RECT)
    w = Widget(pygame.Rect(0, 0, 10, 10))
    s.add(w)
    snapshot = s.children
    s.clear()
    assert len(snapshot) == 1   # snapshot not affected by clear


# ── Event routing ─────────────────────────────────────────────────────────────

def test_event_routes_to_children_reverse_order() -> None:
    """Last added child should receive event first."""
    order: list[int] = []
    s = Stack(RECT)

    class OrderWidget(Widget):
        def __init__(self, n, rect):
            super().__init__(rect)
            self.n = n
        def _handle_event_widget(self, event):
            order.append(self.n)
            return False   # don't consume — let routing continue

    s.add(OrderWidget(1, RECT))
    s.add(OrderWidget(2, RECT))
    s.add(OrderWidget(3, RECT))

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (10, 10), "button": 1})
    s.handle_event(click)
    assert order == [3, 2, 1]


def test_event_stops_at_first_consuming_child() -> None:
    s = Stack(RECT)
    w1 = TrackingWidget(RECT)
    w2 = TrackingWidget(RECT)
    s.add(w1)
    s.add(w2)   # w2 is topmost

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (10, 10), "button": 1})
    consumed = s.handle_event(click)
    assert consumed is True
    assert len(w2.received) == 1
    assert len(w1.received) == 0   # w2 consumed it


def test_invisible_stack_ignores_events() -> None:
    s = Stack(RECT)
    w = TrackingWidget(RECT)
    s.add(w)
    s.visible = False

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (10, 10), "button": 1})
    consumed = s.handle_event(click)
    assert consumed is False
    assert len(w.received) == 0


def test_disabled_stack_does_not_route_events() -> None:
    s = Stack(RECT)
    w = TrackingWidget(RECT)
    s.add(w)
    s.enabled = False

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (10, 10), "button": 1})
    consumed = s.handle_event(click)
    assert consumed is False
    assert len(w.received) == 0


def test_mousemotion_updates_hovered_regardless_of_enabled() -> None:
    s = Stack(RECT)
    s.enabled = False
    motion = pygame.event.Event(pygame.MOUSEMOTION,
                                {"pos": (10, 10), "rel": (0, 0),
                                 "buttons": (0, 0, 0)})
    s.handle_event(motion)
    assert s.hovered is True


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_called_on_all_children() -> None:
    updated: list[float] = []

    class DtWidget(Widget):
        def update(self, dt):
            updated.append(dt)

    s = Stack(RECT)
    s.add(DtWidget(RECT))
    s.add(DtWidget(RECT))
    s.update(0.016)
    assert updated == [0.016, 0.016]


def test_invisible_stack_skips_update() -> None:
    updated: list[float] = []

    class DtWidget(Widget):
        def update(self, dt):
            updated.append(dt)

    s = Stack(RECT)
    s.add(DtWidget(RECT))
    s.visible = False
    s.update(0.016)
    assert updated == []


# ── Render ────────────────────────────────────────────────────────────────────

def test_invisible_stack_skips_render(display_surface) -> None:
    s = Stack(RECT)
    s.add(Widget(RECT))
    s.visible = False
    s.render(display_surface, _ctx())   # should not raise


def test_render_does_not_raise(display_surface) -> None:
    s = Stack(RECT)
    s.add(Widget(RECT))
    s.render(display_surface, _ctx())