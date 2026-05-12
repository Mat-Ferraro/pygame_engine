import pygame

from pygame_engine.ui.base import Widget


class ProbeWidget(Widget):
    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self.event_calls = 0
        self.update_calls = 0
        self.render_calls = 0
        self.consume = False

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
    widget = ProbeWidget(pygame.Rect(10, 10, 100, 40))

    inside = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (20, 20), "rel": (0, 0), "buttons": (0, 0, 0)})
    outside = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (500, 500), "rel": (0, 0), "buttons": (0, 0, 0)})

    widget.handle_event(inside)
    assert widget.hovered is True

    widget.handle_event(outside)
    assert widget.hovered is False


def test_contains_point_and_set_rect_work() -> None:
    widget = ProbeWidget(pygame.Rect(10, 10, 100, 40))

    assert widget.contains_point((20, 20)) is True
    assert widget.contains_point((500, 500)) is False

    new_rect = pygame.Rect(100, 200, 50, 60)
    widget.set_rect(new_rect)

    assert widget.rect == new_rect
    assert widget.contains_point((110, 210)) is True


def test_invisible_widget_skips_update_and_render(display_surface: pygame.Surface) -> None:
    widget = ProbeWidget(pygame.Rect(10, 10, 100, 40))
    widget.visible = False

    widget.update(0.1)
    widget.render(display_surface)

    assert widget.update_calls == 0
    assert widget.render_calls == 0
