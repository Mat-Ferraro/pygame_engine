"""
utils/rects.py

pygame.Rect helpers for pygame_engine.

Utility functions for common rect operations that pygame does not
provide directly or that are awkward to express with the standard API.
"""

from __future__ import annotations

import pygame


# ── Construction helpers ──────────────────────────────────────────────────────

def rect_from_center(
    center: tuple[int, int],
    size: tuple[int, int],
) -> pygame.Rect:
    """
    Create a rect centred at a given point.

    Args:
        center: (x, y) centre position.
        size:   (width, height).

    Returns:
        A new ``pygame.Rect``.
    """
    r = pygame.Rect(0, 0, *size)
    r.center = center
    return r


def rect_from_corners(
    top_left: tuple[int, int],
    bottom_right: tuple[int, int],
) -> pygame.Rect:
    """
    Create a rect from two corner points.

    Args:
        top_left:     (x, y) of the top-left corner.
        bottom_right: (x, y) of the bottom-right corner.

    Returns:
        A new ``pygame.Rect``.
    """
    x1, y1 = top_left
    x2, y2 = bottom_right
    return pygame.Rect(x1, y1, x2 - x1, y2 - y1)


# ── Inset / padding ───────────────────────────────────────────────────────────

def inset(rect: pygame.Rect, amount: int) -> pygame.Rect:
    """
    Return a new rect shrunk on all sides by ``amount`` pixels.

    Equivalent to ``rect.inflate(-amount * 2, -amount * 2)`` but reads
    more clearly at call sites.

    Args:
        rect:   Source rect.
        amount: Pixels to remove from each edge.

    Returns:
        A new shrunk ``pygame.Rect``.
    """
    return rect.inflate(-amount * 2, -amount * 2)


def inset_xy(rect: pygame.Rect, x: int, y: int) -> pygame.Rect:
    """
    Return a new rect shrunk by ``x`` pixels on left/right and ``y``
    pixels on top/bottom.

    Args:
        rect: Source rect.
        x:    Horizontal inset on each side.
        y:    Vertical inset on each side.

    Returns:
        A new shrunk ``pygame.Rect``.
    """
    return rect.inflate(-x * 2, -y * 2)


# ── Snapping / alignment ──────────────────────────────────────────────────────

def snap_to_grid(rect: pygame.Rect, cell: int) -> pygame.Rect:
    """
    Snap a rect's top-left corner to the nearest grid cell.

    Args:
        rect: Source rect.
        cell: Grid cell size in pixels.

    Returns:
        A new ``pygame.Rect`` with its position snapped.
    """
    x = round(rect.x / cell) * cell
    y = round(rect.y / cell) * cell
    return pygame.Rect(x, y, rect.width, rect.height)


# ── Containment / clipping ────────────────────────────────────────────────────

def clamp_inside(inner: pygame.Rect, outer: pygame.Rect) -> pygame.Rect:
    """
    Move ``inner`` so it fits entirely within ``outer``, preserving size.

    If ``inner`` is larger than ``outer`` along any axis it is left
    aligned to the ``outer`` edge on that axis.

    Args:
        inner: The rect to move.
        outer: The bounding rect.

    Returns:
        A new ``pygame.Rect`` clamped inside ``outer``.
    """
    x = max(outer.left, min(inner.x, outer.right  - inner.width))
    y = max(outer.top,  min(inner.y, outer.bottom - inner.height))
    return pygame.Rect(x, y, inner.width, inner.height)


# ── Splitting ─────────────────────────────────────────────────────────────────

def split_horizontal(
    rect: pygame.Rect,
    ratio: float,
) -> tuple[pygame.Rect, pygame.Rect]:
    """
    Split a rect into left and right portions by a ratio.

    Args:
        rect:  Source rect.
        ratio: Width fraction for the left portion (0.0–1.0).

    Returns:
        (left_rect, right_rect)
    """
    split_x = rect.x + int(rect.width * max(0.0, min(1.0, ratio)))
    left  = pygame.Rect(rect.x, rect.y, split_x - rect.x, rect.height)
    right = pygame.Rect(split_x, rect.y, rect.right - split_x, rect.height)
    return left, right


def split_vertical(
    rect: pygame.Rect,
    ratio: float,
) -> tuple[pygame.Rect, pygame.Rect]:
    """
    Split a rect into top and bottom portions by a ratio.

    Args:
        rect:  Source rect.
        ratio: Height fraction for the top portion (0.0–1.0).

    Returns:
        (top_rect, bottom_rect)
    """
    split_y = rect.y + int(rect.height * max(0.0, min(1.0, ratio)))
    top    = pygame.Rect(rect.x, rect.y, rect.width, split_y - rect.y)
    bottom = pygame.Rect(rect.x, split_y, rect.width, rect.bottom - split_y)
    return top, bottom
