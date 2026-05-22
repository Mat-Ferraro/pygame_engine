"""
Tests for pygame_engine.ui.base.Widget.

Covers: visibility/enabled guards, hovered updates, contains_point,
set_rect, focusable attribute, is_interactive, focused default.
"""

import pygame

from pygame_engine.ui.base.widget import Widget


class ProbeWidget(Widget):
    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self.event_calls  = 0
        self.update_calls = 0
        self.render_calls = 0
        self.consume      = False

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        self.event_calls += 1
        return self.consume

    def update(self, dt: float) -> None:
        if not self.visible:
            return
        self.update_calls += 1

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        self.render_calls += 1


# ── Original tests ────────────────────────────────────────────────────────────

def test_invisible_widget_ignores_events() -> None:
    widget = ProbeWidget(pygame.Rect(10, 10, 100, 40))
    widget.visible = False

    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (20, 20), "button": 1})
    consumed = widget.handle_event(event)

    assert consumed is False
    assert widget.event_calls == 0


def test_disabled_widget_ignores_events() -> None:
    widget = ProbeWidget(pygame.Rect(10, 10, 100, 40))
    widget.enabled = False

    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (20, 20), "button": 1})
    consumed = widget.handle_event(event)

    assert consumed is False
    assert widget.event_calls == 0


def test_hovered_updates_from_mouse_motion_inside_and_outside() -> None:
    widget  = ProbeWidget(pygame.Rect(10, 10, 100, 40))
    inside  = pygame.event.Event(pygame.MOUSEMOTION,
                                 {"pos": (20, 20),   "rel": (0, 0), "buttons": (0, 0, 0)})
    outside = pygame.event.Event(pygame.MOUSEMOTION,
                                 {"pos": (500, 500), "rel": (0, 0), "buttons": (0, 0, 0)})

    widget.handle_event(inside)
    assert widget.hovered is True

    widget.handle_event(outside)
    assert widget.hovered is False


def test_contains_point_and_set_rect_work() -> None:
    widget = ProbeWidget(pygame.Rect(10, 10, 100, 40))

    assert widget.contains_point((20, 20))   is True
    assert widget.contains_point((500, 500)) is False

    new_rect = pygame.Rect(100, 200, 50, 60)
    widget.set_rect(new_rect)

    assert widget.rect == new_rect
    assert widget.contains_point((110, 210)) is True


def test_invisible_widget_skips_update_and_render(display_surface) -> None:
    widget = ProbeWidget(pygame.Rect(10, 10, 100, 40))
    widget.visible = False

    widget.update(0.1)
    widget.render(display_surface)

    assert widget.update_calls == 0
    assert widget.render_calls == 0


# ── Additional coverage ───────────────────────────────────────────────────────

def test_focusable_defaults_false() -> None:
    w = Widget(pygame.Rect(0, 0, 100, 40))
    assert w.focusable is False


def test_focusable_can_be_set() -> None:
    w = Widget(pygame.Rect(0, 0, 100, 40))
    w.focusable = True
    assert w.focusable is True


def test_is_interactive_true_when_visible_and_enabled() -> None:
    w = Widget(pygame.Rect(0, 0, 100, 40))
    assert w.is_interactive is True


def test_is_interactive_false_when_invisible() -> None:
    w = Widget(pygame.Rect(0, 0, 100, 40))
    w.visible = False
    assert w.is_interactive is False


def test_is_interactive_false_when_disabled() -> None:
    w = Widget(pygame.Rect(0, 0, 100, 40))
    w.enabled = False
    assert w.is_interactive is False


def test_set_rect_replaces_rect() -> None:
    w   = Widget(pygame.Rect(0, 0, 100, 40))
    new = pygame.Rect(10, 20, 200, 80)
    w.set_rect(new)
    assert w.rect == new


def test_contains_point_true_inside() -> None:
    w = Widget(pygame.Rect(10, 10, 100, 50))
    assert w.contains_point((50, 30)) is True


def test_contains_point_false_outside() -> None:
    w = Widget(pygame.Rect(10, 10, 100, 50))
    assert w.contains_point((200, 200)) is False


def test_focused_defaults_false() -> None:
    w = Widget(pygame.Rect(0, 0, 100, 40))
    assert w.focused is False