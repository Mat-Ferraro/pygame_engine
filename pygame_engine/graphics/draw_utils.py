"""
graphics/draw_utils.py

Low-level drawing helpers for pygame_engine.

These functions consolidate repeated drawing patterns from across the
widget system into one place. They are thin wrappers over pygame.draw
that accept the same arguments widgets already work with — SurfaceStyle
dataclasses, theme colours, and pygame.Rect.

All functions draw directly onto the provided surface and return None.

Usage::

    from pygame_engine.graphics.draw_utils import draw_surface_style, draw_rect_bordered

    # Draw a themed widget background + border in one call
    draw_surface_style(surface, rect, theme.button.normal)

    # Draw a filled rect with a separate border
    draw_rect_bordered(
        surface,
        rect=my_rect,
        fill=(40, 44, 60),
        border=(80, 90, 120),
        border_width=1,
        radius=6,
    )
"""

from __future__ import annotations

import pygame


# ── Styled rect (primary widget drawing primitive) ────────────────────────────

def draw_surface_style(
    surface: pygame.Surface,
    rect: pygame.Rect,
    style: object,
) -> None:
    """
    Draw a filled rect with a border using a ``SurfaceStyle`` dataclass.

    This is the primary drawing call for all themed widgets. It reads
    ``style.bg``, ``style.border``, ``style.border_width``, and
    ``style.radius`` from the provided style object.

    Args:
        surface: Destination surface.
        rect:    Position and size to draw.
        style:   A ``SurfaceStyle`` instance (from ``theme.defaults``).
    """
    pygame.draw.rect(
        surface,
        style.bg,           # type: ignore[attr-defined]
        rect,
        border_radius=style.radius,     # type: ignore[attr-defined]
    )
    bw: int = style.border_width        # type: ignore[attr-defined]
    if bw > 0:
        pygame.draw.rect(
            surface,
            style.border,               # type: ignore[attr-defined]
            rect,
            width=bw,
            border_radius=style.radius, # type: ignore[attr-defined]
        )


def draw_rect_bordered(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill: tuple[int, int, int],
    border: tuple[int, int, int] | None = None,
    border_width: int = 1,
    radius: int = 0,
) -> None:
    """
    Draw a filled rect with an optional border.

    Args:
        surface:      Destination surface.
        rect:         Position and size.
        fill:         Background RGB colour.
        border:       Border RGB colour. Pass None to skip border.
        border_width: Border thickness in pixels.
        radius:       Corner radius in pixels.
    """
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if border is not None and border_width > 0:
        pygame.draw.rect(surface, border, rect,
                         width=border_width, border_radius=radius)


# ── Lines and shapes ──────────────────────────────────────────────────────────

def draw_horizontal_line(
    surface: pygame.Surface,
    y: int,
    x_start: int,
    x_end: int,
    colour: tuple[int, int, int],
    width: int = 1,
) -> None:
    """
    Draw a horizontal line.

    Args:
        surface:  Destination surface.
        y:        Y coordinate.
        x_start:  Left X coordinate.
        x_end:    Right X coordinate.
        colour:   RGB colour.
        width:    Line thickness in pixels.
    """
    pygame.draw.line(surface, colour, (x_start, y), (x_end, y), width)


def draw_vertical_line(
    surface: pygame.Surface,
    x: int,
    y_start: int,
    y_end: int,
    colour: tuple[int, int, int],
    width: int = 1,
) -> None:
    """
    Draw a vertical line.

    Args:
        surface:  Destination surface.
        x:        X coordinate.
        y_start:  Top Y coordinate.
        y_end:    Bottom Y coordinate.
        colour:   RGB colour.
        width:    Line thickness in pixels.
    """
    pygame.draw.line(surface, colour, (x, y_start), (x, y_end), width)


def draw_cross(
    surface: pygame.Surface,
    center: tuple[int, int],
    size: int,
    colour: tuple[int, int, int],
    width: int = 1,
) -> None:
    """
    Draw a cross (×) centred at ``center``.

    Useful for close buttons and debug markers.

    Args:
        surface: Destination surface.
        center:  (x, y) centre point.
        size:    Half-length of each arm in pixels.
        colour:  RGB colour.
        width:   Line thickness.
    """
    cx, cy = center
    pygame.draw.line(surface, colour, (cx - size, cy - size),
                     (cx + size, cy + size), width)
    pygame.draw.line(surface, colour, (cx + size, cy - size),
                     (cx - size, cy + size), width)


def draw_chevron(
    surface: pygame.Surface,
    center: tuple[int, int],
    size: int,
    colour: tuple[int, int, int],
    direction: str = "down",
    width: int = 2,
) -> None:
    """
    Draw a chevron arrow (›, ‹, ∧, ∨) centred at ``center``.

    Useful for dropdown indicators, scroll arrows, and nav controls.

    Args:
        surface:   Destination surface.
        center:    (x, y) centre point.
        size:      Half-size of the chevron in pixels.
        colour:    RGB colour.
        direction: ``"up"``, ``"down"``, ``"left"``, or ``"right"``.
        width:     Line thickness.
    """
    cx, cy = center
    s = size

    points: dict[str, list[tuple[int, int]]] = {
        "down":  [(cx - s, cy - s // 2), (cx,     cy + s // 2), (cx + s, cy - s // 2)],
        "up":    [(cx - s, cy + s // 2), (cx,     cy - s // 2), (cx + s, cy + s // 2)],
        "right": [(cx - s // 2, cy - s), (cx + s // 2, cy    ), (cx - s // 2, cy + s)],
        "left":  [(cx + s // 2, cy - s), (cx - s // 2, cy    ), (cx + s // 2, cy + s)],
    }

    pts = points.get(direction, points["down"])
    pygame.draw.lines(surface, colour, False, pts, width)
