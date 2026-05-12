"""
layout/column.py

Column layout helper for pygame_engine.

Distributes a number of equally-sized slots vertically within a bounds
rect. Returns one rect per slot, top to bottom.

Usage::

    from pygame_engine.layout.column import column

    # Four 200x48 menu items, 12px apart, centred horizontally
    rects = column(bounds, count=4, item_size=(200, 48), spacing=12)
    for rect, item in zip(rects, menu_items):
        item.set_rect(rect)
"""

from __future__ import annotations

import pygame

from pygame_engine.layout._shared import Align, _resolve_align


def column(
    bounds: pygame.Rect,
    count: int,
    item_size: tuple[int, int],
    spacing: int = 0,
    padding: int = 0,
    align: Align = "center",
) -> list[pygame.Rect]:
    """
    Distribute ``count`` items vertically within ``bounds``.

    Items are equally sized at ``item_size``. The group is positioned
    within the padded bounds according to ``align``.

    Args:
        bounds:    The available area to lay out within.
        count:     Number of items (slots) to generate.
        item_size: (width, height) of each item.
        spacing:   Pixels between adjacent items.
        padding:   Inward margin on all four sides of ``bounds``.
        align:     Horizontal alignment of items within the padded bounds.
                   One of ``"start"``, ``"center"``, ``"end"``.

    Returns:
        List of ``pygame.Rect`` objects, one per item, top to bottom.
        Returns an empty list when ``count`` is zero.

    Raises:
        ValueError: If ``count`` is negative.
    """
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")
    if count == 0:
        return []

    iw, ih = item_size
    inner = bounds.inflate(-padding * 2, -padding * 2)

    total_height = ih * count + spacing * (count - 1)
    start_y = inner.y + (inner.height - total_height) // 2

    x = _resolve_align(align, inner.x, inner.width, iw)

    rects: list[pygame.Rect] = []
    for i in range(count):
        y = start_y + i * (ih + spacing)
        rects.append(pygame.Rect(x, y, iw, ih))

    return rects
