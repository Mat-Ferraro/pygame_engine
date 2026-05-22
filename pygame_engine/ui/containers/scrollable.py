"""
Clips a child widget to a visible viewport and allows vertical scrolling
via the mouse wheel. A simple non-interactive scrollbar is drawn on the
right edge when the content overflows.

The child widget renders at full size onto an off-screen surface. Only the
visible portion is blitted to the screen. Mouse event positions are offset
so the child's hit-testing remains correct regardless of scroll position.

Vertical scrolling only in v1. Horizontal scrolling is a future addition.

Usage::

    from pygame_engine.ui.containers.scrollable import Scrollable
    from pygame_engine.ui.containers.panel import Panel

    # A 300x400 viewport scrolling over a 300x900 content panel
    content = Panel(pygame.Rect(0, 0, 300, 900))
    content.add(...)   # add lots of widgets

    scroll = Scrollable(
        pygame.Rect(100, 50, 300, 400),
        child=content,
    )

    # Frame loop — route events and render
    scroll.handle_event(event)
    scroll.update(dt)
    scroll.render(surface)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame

from pygame_engine.ui.base.widget import Widget


class Scrollable(Widget):
    """
    Clipping viewport with vertical scroll for a single child widget.

    The child widget should have its rect positioned at (0, 0) — the
    Scrollable treats the child's coordinate space as starting at the
    top-left of the content area, independent of the Scrollable's own
    screen position.

    Scrollbar
    ---------
    A simple visual scrollbar track and thumb are drawn on the right edge
    when content overflows. The scrollbar is display-only in v1 — drag
    interaction is a future addition.

    Scroll speed
    ------------
    Each wheel tick scrolls by ``scroll_speed`` pixels (default 30).
    """

    SCROLLBAR_WIDTH = 8
    SCROLLBAR_TRACK_COLOUR  = (40,  44,  60)
    SCROLLBAR_THUMB_COLOUR  = (90,  100, 130)
    SCROLLBAR_THUMB_HOVER   = (120, 135, 170)

    def __init__(
        self,
        rect:         pygame.Rect,
        child:        Widget | None = None,
        scroll_speed: int = 30,
    ) -> None:
        """
        Args:
            rect:         The visible viewport rect (screen coordinates).
            child:        The widget to scroll. Its rect defines the content
                          size. Position the child at (0, 0) — the Scrollable
                          handles screen offset internally.
            scroll_speed: Pixels scrolled per mouse wheel tick.
        """
        super().__init__(rect)

        self._child:        Widget | None = child
        self._scroll_speed: int           = scroll_speed
        self._scroll_y:     float         = 0.0   # current scroll in pixels

        # Cached off-screen surface for child rendering
        self._content_surf: pygame.Surface | None = None
        self._content_size: tuple[int, int]        = (rect.width, rect.height)

        if child is not None:
            self._sync_content_surface()

    # ── Child management ──────────────────────────────────────────────────────

    @property
    def child(self) -> Widget | None:
        """Return the current child widget, or None if unset."""
        return self._child

    @child.setter
    def child(self, widget: Widget | None) -> None:
        """Return the current child widget, or None if unset."""
        self._child = widget
        self._scroll_y = 0.0
        self._sync_content_surface()

    # ── Scroll control ────────────────────────────────────────────────────────

    @property
    def scroll_y(self) -> float:
        """Current vertical scroll offset in pixels."""
        return self._scroll_y

    def scroll_to_top(self) -> None:
        """Jump to the top of the content."""
        self._scroll_y = 0.0

    def scroll_to_bottom(self) -> None:
        """Jump to the bottom of the content."""
        self._scroll_y = float(self._max_scroll())

    def scroll_by(self, pixels: float) -> None:
        """Scroll by a given number of pixels (positive = down)."""
        self._scroll_y = max(0.0, min(
            self._scroll_y + pixels, self._max_scroll()
        ))

    # ── Frame methods ─────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        """
        Handle mouse wheel for scrolling, then route other events to child
        with adjusted positions so hit-testing stays correct.
        """
        # Mouse wheel scrolling
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_by(-event.y * self._scroll_speed)
                return True

        # Route events to child with offset-adjusted positions
        if self._child is not None:
            adjusted = self._offset_event(event)
            if adjusted is not None:
                return self._child.handle_event(adjusted)

        return False

    def update(self, dt: float) -> None:
        """Update child state and handle scroll input."""
        if self._child is not None and self._child.visible:
            self._child.update(dt)

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """Draw the scrollable container and its child onto surface."""
        if not self.visible:
            return

        self._sync_content_surface()

        viewport_w = self.rect.width - self.SCROLLBAR_WIDTH
        viewport_h = self.rect.height

        # Draw child onto content surface
        if self._content_surf is not None and self._child is not None:
            self._content_surf.fill((0, 0, 0, 0))
            self._child.render(self._content_surf, ctx)

            # Blit the visible slice onto the screen
            src_rect = pygame.Rect(0, int(self._scroll_y),
                                   viewport_w, viewport_h)
            surface.blit(self._content_surf, self.rect.topleft, src_rect)

        # Clip border
        theme = ctx.theme
        bw    = theme.panel.surface.border_width
        if bw > 0:
            pygame.draw.rect(surface, theme.panel.surface.border,
                             pygame.Rect(self.rect.x, self.rect.y,
                                         viewport_w, viewport_h),
                             width=bw)

        # Scrollbar
        if self._max_scroll() > 0:
            self._draw_scrollbar(surface)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _max_scroll(self) -> float:
        """Maximum scroll offset in pixels."""
        if self._child is None:
            return 0.0
        content_h = self._child.rect.height
        return max(0.0, float(content_h - self.rect.height))

    def _sync_content_surface(self) -> None:
        """Recreate the off-screen content surface if the child size changed."""
        if self._child is None:
            self._content_surf = None
            return

        w = max(self.rect.width - self.SCROLLBAR_WIDTH, 1)
        h = max(self._child.rect.height, self.rect.height)
        size = (w, h)

        if self._content_surf is None or self._content_size != size:
            self._content_surf = pygame.Surface(size, pygame.SRCALPHA)
            self._content_size = size

    def _offset_event(
        self,
        event: pygame.event.Event,
    ) -> pygame.event.Event | None:
        """
        Return a copy of ``event`` with mouse positions adjusted by the
        scroll offset and viewport position, or None if no adjustment needed.

        This ensures the child's hit-testing works correctly even when
        its content is scrolled.
        """
        pos_attrs = {
            pygame.MOUSEBUTTONDOWN: "pos",
            pygame.MOUSEBUTTONUP:   "pos",
            pygame.MOUSEMOTION:     "pos",
        }
        attr = pos_attrs.get(event.type)
        if attr is None:
            return event

        ox = self.rect.x
        oy = self.rect.y - int(self._scroll_y)
        original_pos = getattr(event, attr)
        adjusted_pos = (original_pos[0] - ox, original_pos[1] - oy)

        # Only route to child if the original position is inside the viewport
        if not self.rect.collidepoint(original_pos):
            return None

        new_attrs = dict(event.__dict__)
        new_attrs[attr] = adjusted_pos
        return pygame.event.Event(event.type, new_attrs)

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        """Draw the scrollbar track and thumb."""
        bar_x  = self.rect.right - self.SCROLLBAR_WIDTH
        bar_y  = self.rect.y
        bar_h  = self.rect.height

        # Track
        track = pygame.Rect(bar_x, bar_y, self.SCROLLBAR_WIDTH, bar_h)
        pygame.draw.rect(surface, self.SCROLLBAR_TRACK_COLOUR, track,
                         border_radius=4)

        # Thumb — proportional to viewport/content ratio
        content_h  = self._child.rect.height if self._child else bar_h
        ratio      = min(1.0, bar_h / max(content_h, 1))
        thumb_h    = max(20, int(bar_h * ratio))
        max_scroll = self._max_scroll()
        scroll_pct = self._scroll_y / max_scroll if max_scroll > 0 else 0.0
        thumb_y    = bar_y + int((bar_h - thumb_h) * scroll_pct)

        thumb = pygame.Rect(bar_x + 1, thumb_y,
                            self.SCROLLBAR_WIDTH - 2, thumb_h)

        colour = (self.SCROLLBAR_THUMB_HOVER
                  if self.hovered
                  else self.SCROLLBAR_THUMB_COLOUR)
        pygame.draw.rect(surface, colour, thumb, border_radius=4)