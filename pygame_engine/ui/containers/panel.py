"""
ui/containers/panel.py

Panel container widget for pygame_engine.

Panel is the standard building block for grouping widgets. It draws a
styled background and border from the active theme, owns a flat list of
child widgets, and delegates the three frame methods to them.

Panel does NOT own a layout helper — callers assign child rects
externally using the layout helpers in ``pygame_engine.layout``. This
keeps Panel focused on containment and delegation, not positioning.

Usage::

    from pygame_engine.ui.containers.panel import Panel
    from pygame_engine.layout import column

    panel = Panel(pygame.Rect(100, 100, 300, 400))

    btn_rects = column(panel.rect, count=3, item_size=(220, 48), spacing=12)
    panel.add(Button(btn_rects[0], "New Game"))
    panel.add(Button(btn_rects[1], "Options"))
    panel.add(Button(btn_rects[2], "Quit"))

    scene.root_widget = panel
"""

from __future__ import annotations

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class Panel(Widget):
    """
    Container widget that groups child widgets behind a styled surface.

    Responsibilities
    ----------------
    - Draw a themed background and border
    - Own and delegate to a flat list of child widgets
    - Route events top-down through children (first consumer wins)
    - Update and render children in add-order
    - Optionally clip child rendering to the panel rect

    Non-responsibilities
    --------------------
    - Layout (callers assign child rects via layout helpers)
    - Focus traversal (future addition)
    - Scrolling (future addition)
    """

    def __init__(
        self,
        rect: pygame.Rect,
        clip: bool = False,
    ) -> None:
        """
        Args:
            rect: Position and size of this panel.
            clip: If True, child rendering is clipped to this panel's rect.
                  Children that draw outside the rect will be cut off.
        """
        super().__init__(rect)

        self.clip: bool = clip
        self._children: list[Widget] = []

    # ── Child management ──────────────────────────────────────────────────────

    def add(self, widget: Widget) -> Widget:
        """
        Add a child widget to this panel.

        Children are stored in add-order. Rendering and updates happen
        in add-order; event routing happens in reverse add-order (last
        added = topmost = first to receive events).

        Args:
            widget: The widget to add.

        Returns:
            The added widget (for chaining convenience).
        """
        self._children.append(widget)
        return widget

    def remove(self, widget: Widget) -> bool:
        """
        Remove a child widget from this panel.

        Args:
            widget: The widget to remove.

        Returns:
            True if the widget was found and removed; False otherwise.
        """
        try:
            self._children.remove(widget)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Remove all child widgets from this panel."""
        self._children.clear()

    @property
    def children(self) -> list[Widget]:
        """Read-only view of the child list in add-order."""
        return list(self._children)

    # ── Layout passthrough ────────────────────────────────────────────────────

    def set_rect(self, rect: pygame.Rect) -> None:
        """
        Assign a new rect to this panel.

        Does NOT reposition children — callers are responsible for
        reassigning child rects after a panel resize.
        """
        self.rect = rect

    # ── Frame methods ─────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        """
        Route event to children in reverse add-order (topmost first).

        Stops as soon as a child consumes the event.
        """
        for child in reversed(self._children):
            if child.handle_event(event):
                return True
        return False

    def update(self, dt: float) -> None:
        """Update all visible children in add-order."""
        for child in self._children:
            if child.visible:
                child.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Draw the panel background and border, then render all children.

        If ``clip`` is True, child rendering is scissored to this panel's
        rect using pygame's clip stack.
        """
        if not self.visible:
            return

        self._draw_background(surface)

        if self.clip:
            old_clip = surface.get_clip()
            surface.set_clip(self.rect)
            self._render_children(surface)
            surface.set_clip(old_clip)
        else:
            self._render_children(surface)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _draw_background(self, surface: pygame.Surface) -> None:
        """Draw the panel surface (background + border) from theme."""
        theme = get_theme()
        style = theme.panel.surface

        pygame.draw.rect(
            surface, style.bg, self.rect,
            border_radius=style.radius,
        )
        if style.border_width > 0:
            pygame.draw.rect(
                surface, style.border, self.rect,
                width=style.border_width,
                border_radius=style.radius,
            )

    def _render_children(self, surface: pygame.Surface) -> None:
        """Render all visible children in add-order (bottom to top)."""
        for child in self._children:
            if child.visible:
                child.render(surface)
