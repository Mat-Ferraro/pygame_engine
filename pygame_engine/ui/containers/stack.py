"""
Stack is the lightweight grouping container:
- no background
- no border
- owns child widgets
- supports z-ordered event routing
- optional clipping

Use Panel when you want a surfaced background and border.
Use Stack when you only want grouping and layering behaviour —
overlays, HUD layers, root widget trees, transparent composites.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.focus import FocusManager


class Stack(Widget, FocusManager):
    """
    Transparent grouping container.

    Children render in add-order (first added = bottom).
    Events route in reverse add-order (last added = topmost = first to receive).

    Follows the full base Widget contract:
    - invisible Stack returns False from handle_event immediately
    - disabled Stack skips event routing but still renders and updates
    - MOUSEMOTION updates the Stack's own hovered state
    """

    def __init__(self, rect: pygame.Rect, *, clip: bool = False, manage_focus: bool = False) -> None:
        """
        Args:
            rect: Position and size of this stack.
            clip: If True, child rendering is clipped to this rect.
        """
        Widget.__init__(self, rect)
        FocusManager.__init__(self)
        self.clip: bool = clip
        self._manage_focus: bool = manage_focus
        self._children: list[Widget] = []

    # ── Child management ──────────────────────────────────────────────────────

    def add(self, widget: Widget) -> Widget:
        """
        Add a child widget. Returns the widget for chaining.

        Children are rendered bottom-up in add-order.
        Events route top-down in reverse add-order.
        """
        self._children.append(widget)
        return widget

    def remove(self, widget: Widget) -> bool:
        """Remove a child. Returns True if found and removed."""
        try:
            self._children.remove(widget)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Remove all children."""
        self._children.clear()

    @property
    def children(self) -> tuple[Widget, ...]:
        """Read-only snapshot of children in add-order."""
        return tuple(self._children)

    # ── Frame methods ─────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Route event through children in reverse add-order.

        Follows the full base Widget guard contract:
        - returns False immediately if not visible
        - updates hovered state from MOUSEMOTION regardless of enabled
        - skips child routing if not enabled
        - stops at first child that consumes the event
        """
        if not self.visible:
            return False

        # Update own hover state (base class contract)
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if not self.enabled:
            return False

        # Focus traversal intercept
        if self._focus_handle_event(event, self._children):
            return True

        # Give open Dropdowns priority — their floating list renders
        # outside their own rect so normal Z-order routing misses it.
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                          pygame.MOUSEMOTION):
            from pygame_engine.ui.controls.dropdown import Dropdown
            for child in self._children:
                if (isinstance(child, Dropdown)
                        and child.visible
                        and child.enabled
                        and child.is_open):
                    if child.handle_event(event):
                        return True

        for child in reversed(self._children):
            if child.handle_event(event):
                return True
        return False

    def update(self, dt: float) -> None:
        """Update all children. Skipped when not visible."""
        if not self.visible:
            return
        for child in self._children:
            child.update(dt)

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """
        Render all children in add-order.

        If ``clip`` is True, rendering is scissored to this Stack's rect.
        Skipped when not visible.
        """
        if not self.visible:
            return

        if self.clip:
            old_clip = surface.get_clip()
            surface.set_clip(self.rect)
            try:
                for child in self._children:
                    child.render(surface, ctx)
            finally:
                surface.set_clip(old_clip)
        else:
            for child in self._children:
                child.render(surface, ctx)