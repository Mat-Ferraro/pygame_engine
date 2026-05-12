"""
layout/row.py

Row layout helper for pygame_engine.

Distributes a number of equally-sized slots horizontally within a bounds
rect. Returns one rect per slot, left to right.

All layout helpers in this package are stateless functions:
input bounds in, list of rects out. No state, no instances.

Usage::

    from pygame_engine.layout.row import row

    # Three 120x40 buttons, 8px apart, centred vertically in a 600x80 area
    rects = row(bounds, count=3, item_size=(120, 40), spacing=8)
    for rect, btn in zip(rects, buttons):
        btn.set_rect(rect)
"""

from __future__ import annotations

import pygame

from pygame_engine.layout._shared import Align, _resolve_align


def row(
    bounds: pygame.Rect,
    count: int,
    item_size: tuple[int, int],
    spacing: int = 0,
    padding: int = 0,
    align: Align = "center",
) -> list[pygame.Rect]:
    """
    Distribute ``count`` items horizontally within ``bounds``.

    Items are equally sized at ``item_size``. The group is positioned
    within the padded bounds according to ``align``.

    Args:
        bounds:    The available area to lay out within.
        count:     Number of items (slots) to generate.
        item_size: (width, height) of each item.
        spacing:   Pixels between adjacent items.
        padding:   Inward margin on all four sides of ``bounds``.
        align:     Vertical alignment of items within the padded bounds.
                   One of ``"start"``, ``"center"``, ``"end"``.

    Returns:
        List of ``pygame.Rect`` objects, one per item, left to right.
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

    total_width = iw * count + spacing * (count - 1)
    start_x = inner.x + (inner.width - total_width) // 2

    y = _resolve_align(align, inner.y, inner.height, ih)

    rects: list[pygame.Rect] = []
    for i in range(count):
        x = start_x + i * (iw + spacing)
        rects.append(pygame.Rect(x, y, iw, ih))

    return rects
