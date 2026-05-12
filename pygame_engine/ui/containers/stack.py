"""
ui/containers/stack.py

Transparent stack container for pygame_engine.

Stack is the lightweight grouping container:
- no background
- no border
- owns child widgets
- supports z-ordered event routing
- optional clipping

Use Panel when you want a surfaced container.
Use Stack when you only want grouping/layering behavior.
"""

from __future__ import annotations

import pygame

from pygame_engine.ui.base.widget import Widget


class Stack(Widget):
    """
    Transparent grouping container.

    Children render in add order and receive events in reverse add order
    so later-added children behave as visually topmost.
    """

    def __init__(self, rect: pygame.Rect, *, clip: bool = False) -> None:
        super().__init__(rect)
        self.clip: bool = clip
        self._children: list[Widget] = []

    def add(self, widget: Widget) -> Widget:
        self._children.append(widget)
        return widget

    def remove(self, widget: Widget) -> bool:
        try:
            self._children.remove(widget)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        self._children.clear()

    @property
    def children(self) -> tuple[Widget, ...]:
        return tuple(self._children)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False

        for child in reversed(self._children):
            if child.handle_event(event):
                return True
        return False

    def update(self, dt: float) -> None:
        if not self.visible:
            return

        for child in self._children:
            child.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        old_clip = None
        if self.clip:
            old_clip = surface.get_clip()
            surface.set_clip(self.rect)

        try:
            for child in self._children:
                child.render(surface)
        finally:
            if self.clip and old_clip is not None:
                surface.set_clip(old_clip)
