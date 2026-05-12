"""
ui/containers/panel.py

Panel container widget for pygame_engine.

Panel is the standard surfaced container:
- draws a themed background and border
- owns a flat list of child widgets
- delegates event, update, and render work to children
- optionally clips child rendering to its own rect

Panel does NOT own a layout helper. Child rects are assigned externally
using the layout helpers in ``pygame_engine.layout``.
"""

from __future__ import annotations

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class Panel(Widget):
    """
    Container widget that groups child widgets behind a themed surface.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        clip: bool = False,
        *,
        draw_background: bool = True,
        draw_border: bool = True,
    ) -> None:
        super().__init__(rect)
        self.clip: bool = clip
        self.draw_background: bool = draw_background
        self.draw_border: bool = draw_border
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

        self._draw_background(surface)

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

    def _draw_background(self, surface: pygame.Surface) -> None:
        """
        Draw the panel background and border from the active theme.

        ``theme.panel`` is a PanelTheme wrapper. The actual drawable surface
        values live under ``theme.panel.surface``.
        """
        theme = get_theme()
        panel_theme = theme.panel
        surface_style = panel_theme.surface

        if self.draw_background:
            pygame.draw.rect(
                surface,
                surface_style.bg,
                self.rect,
                border_radius=surface_style.radius,
            )

        if self.draw_border and surface_style.border_width > 0:
            pygame.draw.rect(
                surface,
                surface_style.border,
                self.rect,
                width=surface_style.border_width,
                border_radius=surface_style.radius,
            )
