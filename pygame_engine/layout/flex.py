"""
Distribute a list of widgets horizontally or vertically within a bounds
rect using fixed sizes, proportional weights, or a mix of both. Recompute
on resize by calling ``layout(new_bounds)`` again.

Usage::

    from pygame_engine.layout.flex import FlexRow, FlexColumn

    # Three buttons sharing available width equally
    row = FlexRow(spacing=8)
    row.add(btn_back,    weight=1)
    row.add(btn_confirm, weight=2)   # twice as wide as btn_back
    row.add(btn_cancel,  weight=1)
    row.layout(pygame.Rect(20, 500, 760, 48))

    # Fixed + proportional mix
    col = FlexColumn(spacing=4)
    col.add(header,  fixed=60)        # always 60px tall
    col.add(content, weight=1)        # fills remaining space
    col.add(footer,  fixed=40)        # always 40px tall
    col.layout(screen_rect)

    # In on_resize:
    def on_resize(self, width, height):
        self._row.layout(pygame.Rect(20, height - 68, width - 40, 48))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import pygame


class _HasSetRect(Protocol):
    def set_rect(self, rect: pygame.Rect) -> None: ...


@dataclass
class _FlexItem:
    widget: _HasSetRect
    weight: float       # proportional share of free space (0 = use fixed)
    fixed:  int         # fixed size in pixels (0 = use weight)
    min_size: int       # minimum size in pixels
    max_size: int       # maximum size in pixels (0 = unlimited)


class FlexRow:
    """
    Distribute widgets horizontally within a bounds rect.

    Each item is either:
    - **fixed** — always exactly ``fixed`` pixels wide
    - **weighted** — gets a proportional share of the remaining space

    Heights fill the full bounds height unless overridden by ``item_height``.

    Args:
        spacing:     Gap between items in pixels.
        padding:     Inset on all sides of the bounds rect.
        item_height: Override height for all items. 0 = fill bounds height.
    """

    def __init__(
        self,
        spacing:     int = 0,
        padding:     int = 0,
        item_height: int = 0,
    ) -> None:
        self._items:       list[_FlexItem] = []
        self._spacing      = spacing
        self._padding      = padding
        self._item_height  = item_height
        self._last_bounds: pygame.Rect | None = None

    def add(
        self,
        widget:   _HasSetRect,
        weight:   float = 1.0,
        fixed:    int   = 0,
        min_size: int   = 0,
        max_size: int   = 0,
    ) -> "FlexRow":
        """
        Register a widget for layout.

        Args:
            widget:   Any object with a ``set_rect(rect)`` method.
            weight:   Proportional share of remaining space. Ignored if
                      ``fixed > 0``.
            fixed:    Fixed pixel width. Overrides ``weight``.
            min_size: Minimum width in pixels (applied after weight calc).
            max_size: Maximum width in pixels. 0 = no limit.

        Returns:
            self — for chaining.
        """
        self._items.append(_FlexItem(widget, weight, fixed, min_size, max_size))
        return self

    def layout(self, bounds: pygame.Rect) -> list[pygame.Rect]:
        """
        Compute and apply rects for all registered widgets.

        Call this in ``on_enter`` and again in ``on_resize``.

        Args:
            bounds: The rect to distribute items within.

        Returns:
            List of computed rects in registration order.
        """
        self._last_bounds = pygame.Rect(bounds)
        pad  = self._padding
        inner = pygame.Rect(
            bounds.x + pad, bounds.y + pad,
            bounds.width - pad * 2, bounds.height - pad * 2,
        )

        # Split items into fixed and weighted
        total_fixed    = sum(item.fixed for item in self._items if item.fixed > 0)
        total_gaps     = self._spacing * max(0, len(self._items) - 1)
        free_space     = max(0, inner.width - total_fixed - total_gaps)
        total_weight   = sum(item.weight for item in self._items if item.fixed == 0)

        rects: list[pygame.Rect] = []
        x = inner.x
        h = self._item_height if self._item_height > 0 else inner.height
        y = inner.y + (inner.height - h) // 2

        for item in self._items:
            if item.fixed > 0:
                w = item.fixed
            elif total_weight > 0:
                w = int(free_space * item.weight / total_weight)
            else:
                w = 0

            # Apply min/max
            if item.min_size > 0:
                w = max(w, item.min_size)
            if item.max_size > 0:
                w = min(w, item.max_size)

            rect = pygame.Rect(x, y, w, h)
            item.widget.set_rect(rect)
            rects.append(rect)
            x += w + self._spacing

        return rects

    def relayout(self) -> list[pygame.Rect]:
        """Re-run layout with the last bounds. No-op if never laid out."""
        if self._last_bounds is not None:
            return self.layout(self._last_bounds)
        return []

    @property
    def item_count(self) -> int:
        """Return the number of items in this flex layout."""
        return len(self._items)

    def clear(self) -> None:
        """Remove all registered items."""
        self._items.clear()


class FlexColumn:
    """
    Distribute widgets vertically within a bounds rect.

    Each item is either fixed height or proportionally weighted.
    Widths fill the full bounds width unless overridden by ``item_width``.

    Args:
        spacing:    Gap between items in pixels.
        padding:    Inset on all sides of the bounds rect.
        item_width: Override width for all items. 0 = fill bounds width.
    """

    def __init__(
        self,
        spacing:    int = 0,
        padding:    int = 0,
        item_width: int = 0,
    ) -> None:
        self._items:      list[_FlexItem] = []
        self._spacing     = spacing
        self._padding     = padding
        self._item_width  = item_width
        self._last_bounds: pygame.Rect | None = None

    def add(
        self,
        widget:   _HasSetRect,
        weight:   float = 1.0,
        fixed:    int   = 0,
        min_size: int   = 0,
        max_size: int   = 0,
    ) -> "FlexColumn":
        """
        Register a widget for layout.

        Args:
            widget:   Any object with a ``set_rect(rect)`` method.
            weight:   Proportional share of remaining space. Ignored if
                      ``fixed > 0``.
            fixed:    Fixed pixel height. Overrides ``weight``.
            min_size: Minimum height in pixels.
            max_size: Maximum height in pixels. 0 = no limit.

        Returns:
            self — for chaining.
        """
        self._items.append(_FlexItem(widget, weight, fixed, min_size, max_size))
        return self

    def layout(self, bounds: pygame.Rect) -> list[pygame.Rect]:
        """
        Compute and apply rects for all registered widgets.

        Args:
            bounds: The rect to distribute items within.

        Returns:
            List of computed rects in registration order.
        """
        self._last_bounds = pygame.Rect(bounds)
        pad   = self._padding
        inner = pygame.Rect(
            bounds.x + pad, bounds.y + pad,
            bounds.width - pad * 2, bounds.height - pad * 2,
        )

        total_fixed  = sum(item.fixed for item in self._items if item.fixed > 0)
        total_gaps   = self._spacing * max(0, len(self._items) - 1)
        free_space   = max(0, inner.height - total_fixed - total_gaps)
        total_weight = sum(item.weight for item in self._items if item.fixed == 0)

        rects: list[pygame.Rect] = []
        y = inner.y
        w = self._item_width if self._item_width > 0 else inner.width
        x = inner.x + (inner.width - w) // 2

        for item in self._items:
            if item.fixed > 0:
                h = item.fixed
            elif total_weight > 0:
                h = int(free_space * item.weight / total_weight)
            else:
                h = 0

            if item.min_size > 0:
                h = max(h, item.min_size)
            if item.max_size > 0:
                h = min(h, item.max_size)

            rect = pygame.Rect(x, y, w, h)
            item.widget.set_rect(rect)
            rects.append(rect)
            y += h + self._spacing

        return rects

    def relayout(self) -> list[pygame.Rect]:
        """Re-run layout with the last bounds. No-op if never laid out."""
        if self._last_bounds is not None:
            return self.layout(self._last_bounds)
        return []

    @property
    def item_count(self) -> int:
        """Return the number of items in this flex layout."""
        return len(self._items)

    def clear(self) -> None:
        """Remove all registered items."""
        self._items.clear()