"""
layout/anchor.py

Anchor placement helper for pygame_engine.

Places a rect of a given size relative to a reference rect (or screen
area) using named anchor points. Useful for HUD elements, overlays,
centred dialogs, and corner-pinned UI.

Usage::

    from pygame_engine.layout.anchor import anchor

    # Centre a 200x80 rect on the screen
    dialog_rect = anchor(screen_rect, (200, 80), "center")

    # Pin a 120x40 button to the bottom-right with 16px margin
    btn_rect = anchor(screen_rect, (120, 40), "bottom_right", margin=16)
"""

from __future__ import annotations

import pygame

# Accepted anchor point names
AnchorPoint = str

ANCHOR_POINTS: frozenset[str] = frozenset({
    "top_left",    "top",    "top_right",
    "left",        "center", "right",
    "bottom_left", "bottom", "bottom_right",
})


def anchor(
    bounds: pygame.Rect,
    size: tuple[int, int],
    point: AnchorPoint = "center",
    margin: int = 0,
    offset: tuple[int, int] = (0, 0),
) -> pygame.Rect:
    """
    Return a rect of ``size`` placed at ``point`` within ``bounds``.

    Args:
        bounds:  The reference rect to anchor within.
        size:    (width, height) of the rect to place.
        point:   One of the nine named anchor points:
                 ``"top_left"``, ``"top"``, ``"top_right"``,
                 ``"left"``,    ``"center"``, ``"right"``,
                 ``"bottom_left"``, ``"bottom"``, ``"bottom_right"``.
        margin:  Inward margin from the edge of ``bounds`` in pixels.
                 Applies to the nearest edges for the chosen anchor point.
                 Has no effect for ``"center"``.
        offset:  Additional (dx, dy) nudge applied after placement.

    Returns:
        A new ``pygame.Rect`` positioned at the requested anchor point.

    Raises:
        ValueError: If ``point`` is not a recognised anchor point name.
    """
    if point not in ANCHOR_POINTS:
        raise ValueError(
            f"Unknown anchor point {point!r}. "
            f"Valid points: {sorted(ANCHOR_POINTS)}"
        )

    w, h = size
    bx, by, bw, bh = bounds.x, bounds.y, bounds.width, bounds.height
    dx, dy = offset

    # Horizontal position
    if point in ("top_left", "left", "bottom_left"):
        x = bx + margin
    elif point in ("top_right", "right", "bottom_right"):
        x = bx + bw - w - margin
    else:  # top, center, bottom
        x = bx + (bw - w) // 2

    # Vertical position
    if point in ("top_left", "top", "top_right"):
        y = by + margin
    elif point in ("bottom_left", "bottom", "bottom_right"):
        y = by + bh - h - margin
    else:  # left, center, right
        y = by + (bh - h) // 2

    return pygame.Rect(x + dx, y + dy, w, h)
