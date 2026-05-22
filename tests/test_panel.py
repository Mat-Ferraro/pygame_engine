"""
Tests for pygame_engine.ui.containers.Panel.

Covers: child management, event routing, focus management opt-in,
update/render delegation, clip mode, set_rect propagation.
"""

import pygame
import pytest

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.containers.panel import Panel



# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    """Return a default RenderContext for render() calls in tests."""
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

RECT = pygame.Rect(0, 0, 400, 300)


class TrackingWidget(Widget):
    """Records events received."""
    def __init__(self, rect=None):
        super().__init__(rect or pygame.Rect(0, 0, 100, 40))
        self.received: list[pygame.event.Event] = []
        self.update_dt: list[float] = []

    def _handle_event_widget(self, event):
        self.received.append(event)
        return True

    def update(self, dt):
        self.update_dt.append(dt)


# ── Child management ──────────────────────────────────────────────────────────

def test_panel_starts_empty() -> None:
    p = Panel(RECT)
    assert len(p.children) == 0


def test_add_returns_widget() -> None:
    p = Panel(RECT)
    w = Widget(pygame.Rect(0, 0, 10, 10))
    assert p.add(w) is w


def test_add_increases_child_count() -> None:
    p = Panel(RECT)
    p.add(Widget(pygame.Rect(0, 0, 10, 10)))
    p.add(Widget(pygame.Rect(0, 0, 10, 10)))
    assert len(p.children) == 2


def test_remove_existing_returns_true() -> None:
    p = Panel(RECT)
    w = Widget(pygame.Rect(0, 0, 10, 10))
    p.add(w)
    assert p.remove(w) is True
    assert len(p.children) == 0


def test_remove_absent_returns_false() -> None:
    p = Panel(RECT)
    w = Widget(pygame.Rect(0, 0, 10, 10))
    assert p.remove(w) is False


def test_clear_removes_all() -> None:
    p = Panel(RECT)
    p.add(Widget(pygame.Rect(0, 0, 10, 10)))
    p.add(Widget(pygame.Rect(0, 0, 10, 10)))
    p.clear()
    assert len(p.children) == 0


# ── Event routing ─────────────────────────────────────────────────────────────

def test_events_routed_to_children_reverse_order() -> None:
    order: list[int] = []
    p = Panel(RECT)

    class OrderWidget(Widget):
        def __init__(self, n):
            super().__init__(pygame.Rect(0, 0, 400, 300))
            self.n = n
        def _handle_event_widget(self, event):
            order.append(self.n)
            return False

    p.add(OrderWidget(1))
    p.add(OrderWidget(2))
    p.add(OrderWidget(3))

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (10, 10), "button": 1})
    p.handle_event(click)
    assert order == [3, 2, 1]


def test_event_stops_at_first_consumer() -> None:
    p  = Panel(RECT)
    w1 = TrackingWidget()
    w2 = TrackingWidget()
    p.add(w1)
    p.add(w2)  # topmost

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (10, 10), "button": 1})
    p.handle_event(click)
    assert len(w2.received) == 1
    assert len(w1.received) == 0   # w2 consumed it


def test_invisible_panel_ignores_events() -> None:
    p = Panel(RECT)
    w = TrackingWidget()
    p.add(w)
    p.visible = False

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (10, 10), "button": 1})
    consumed = p.handle_event(click)
    assert consumed is False
    assert len(w.received) == 0


def test_disabled_panel_does_not_route_events() -> None:
    p = Panel(RECT)
    w = TrackingWidget()
    p.add(w)
    p.enabled = False

    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                               {"pos": (10, 10), "button": 1})
    consumed = p.handle_event(click)
    assert consumed is False
    assert len(w.received) == 0


def test_hover_updated_when_disabled() -> None:
    p = Panel(RECT)
    p.enabled = False
    motion = pygame.event.Event(pygame.MOUSEMOTION,
                                {"pos": (10, 10), "rel": (0, 0),
                                 "buttons": (0, 0, 0)})
    p.handle_event(motion)
    assert p.hovered is True


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_delegated_to_children() -> None:
    p = Panel(RECT)
    w = TrackingWidget()
    p.add(w)
    p.update(0.016)
    assert w.update_dt == [0.016]


def test_update_skipped_when_invisible() -> None:
    p = Panel(RECT)
    w = TrackingWidget()
    p.add(w)
    p.visible = False
    p.update(0.016)
    assert w.update_dt == []


# ── Render ────────────────────────────────────────────────────────────────────

def test_render_does_not_raise(display_surface) -> None:
    p = Panel(RECT)
    p.add(Widget(pygame.Rect(0, 0, 50, 30)))
    p.render(display_surface, _ctx())


def test_invisible_panel_skips_render(display_surface) -> None:
    p = Panel(RECT)
    p.visible = False
    p.render(display_surface, _ctx())  # should not raise


# ── set_rect ──────────────────────────────────────────────────────────────────

def test_set_rect_updates_panel_rect() -> None:
    p = Panel(RECT)
    new_rect = pygame.Rect(50, 50, 200, 150)
    p.set_rect(new_rect)
    assert p.rect == new_rect


# ── Focus management ──────────────────────────────────────────────────────────

def test_manage_focus_false_by_default() -> None:
    p = Panel(RECT)
    assert p._manage_focus is False


def test_manage_focus_true_when_opted_in() -> None:
    p = Panel(RECT, manage_focus=True)
    assert p._manage_focus is True


def test_tab_not_consumed_without_manage_focus() -> None:
    p = Panel(RECT, manage_focus=False)
    w = Widget(pygame.Rect(0, 0, 100, 40))
    w.focusable = True
    p.add(w)

    tab = pygame.event.Event(pygame.KEYDOWN,
                             {"key": pygame.K_TAB, "mod": 0,
                              "unicode": "\t", "scancode": 0})
    consumed = p.handle_event(tab)
    assert consumed is False


def test_tab_consumed_with_manage_focus() -> None:
    p = Panel(RECT, manage_focus=True)
    w1 = Widget(pygame.Rect(0, 0, 100, 40))
    w2 = Widget(pygame.Rect(0, 0, 100, 40))
    w1.focusable = True
    w2.focusable = True
    p.add(w1)
    p.add(w2)
    p.focus_first(p._children)

    tab = pygame.event.Event(pygame.KEYDOWN,
                             {"key": pygame.K_TAB, "mod": 0,
                              "unicode": "\t", "scancode": 0})
    consumed = p.handle_event(tab)
    assert consumed is True