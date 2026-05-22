"""
Nine-slice (9-patch) scaling for pygame_engine.

Nine-slice divides a source surface into a 3×3 grid:

    ┌─────┬───────────┬─────┐
    │ TL  │  Top      │ TR  │  ← corners: never scaled
    ├─────┼───────────┼─────┤
    │Left │  Centre   │Right│  ← edges: scaled in one axis
    ├─────┼───────────┼─────┤
    │ BL  │  Bottom   │ BR  │  ← centre: scaled in both axes
    └─────┴───────────┴─────┘

This allows a small source texture to scale to any destination size
without distorting the corners — essential for dialog boxes, panels,
speech bubbles, and buttons with rounded corners or decorative borders.

Usage::

    from pygame_engine.graphics.nine_slice import draw_nine_slice, NineSlicePanel

    # Draw a scaled panel using a source texture
    source = app.assets.image("ui/panel.png")
    draw_nine_slice(surface, source, dest_rect, border=12)

    # Or use a widget that handles it automatically
    panel = NineSlicePanel(rect, source_surface, border=12)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame


# ── Core drawing function ─────────────────────────────────────────────────────

def draw_nine_slice(
    dest:    pygame.Surface,
    source:  pygame.Surface,
    rect:    pygame.Rect,
    border:  int | tuple[int, int, int, int],
) -> None:
    """
    Draw ``source`` scaled into ``rect`` using nine-slice scaling.

    The corner regions of ``source`` are copied without scaling.
    Edge regions are scaled in one axis. The centre is scaled in both.

    Args:
        dest:   Destination surface to draw onto.
        source: Source surface containing the nine-slice artwork.
                Should be at least (2*border+1) × (2*border+1) pixels.
        rect:   Destination rect. Corners are never distorted regardless
                of how large or small ``rect`` is.
        border: Corner/edge size in pixels. Either a single int (same on
                all sides) or a (top, right, bottom, left) tuple.

    Raises:
        ValueError: If the destination rect is smaller than the combined
                    border sizes in either dimension.
    """
    top, right, bottom, left = _normalise_border(border)
    sw, sh = source.get_size()
    dx, dy, dw, dh = rect.x, rect.y, rect.width, rect.height

    # Validate destination is large enough
    if dw < left + right or dh < top + bottom:
        raise ValueError(
            f"Destination rect ({dw}×{dh}) is smaller than the combined "
            f"border sizes (h:{left+right}, v:{top+bottom})."
        )

    # Source slice coordinates
    sl = left
    sr = sw - right
    st = top
    sb = sh - bottom

    # Destination slice coordinates
    dl = left
    dr = dw - right
    dt = top
    db = dh - bottom

    # Build the 9 (src_rect, dst_rect) pairs
    slices = [
        # Corners
        (pygame.Rect(0,  0,  sl,    st),    pygame.Rect(dx,       dy,       dl,       dt)),
        (pygame.Rect(sr, 0,  right, st),    pygame.Rect(dx+dr,    dy,       right,    dt)),
        (pygame.Rect(0,  sb, sl,    bottom),pygame.Rect(dx,       dy+db,    dl,       bottom)),
        (pygame.Rect(sr, sb, right, bottom),pygame.Rect(dx+dr,    dy+db,    right,    bottom)),
        # Edges
        (pygame.Rect(sl, 0,  sr-sl, st),    pygame.Rect(dx+dl,    dy,       dr-dl,    dt)),
        (pygame.Rect(sl, sb, sr-sl, bottom),pygame.Rect(dx+dl,    dy+db,    dr-dl,    bottom)),
        (pygame.Rect(0,  st, sl,    sb-st), pygame.Rect(dx,       dy+dt,    dl,       db-dt)),
        (pygame.Rect(sr, st, right, sb-st), pygame.Rect(dx+dr,    dy+dt,    right,    db-dt)),
        # Centre
        (pygame.Rect(sl, st, sr-sl, sb-st), pygame.Rect(dx+dl,    dy+dt,    dr-dl,    db-dt)),
    ]

    for src_rect, dst_rect in slices:
        if dst_rect.width <= 0 or dst_rect.height <= 0:
            continue
        if src_rect.width <= 0 or src_rect.height <= 0:
            continue
        piece = source.subsurface(src_rect)
        if dst_rect.size != src_rect.size:
            piece = pygame.transform.scale(piece, dst_rect.size)
        dest.blit(piece, dst_rect.topleft)


def make_nine_slice_surface(
    source:  pygame.Surface,
    size:    tuple[int, int],
    border:  int | tuple[int, int, int, int],
) -> pygame.Surface:
    """
    Return a new surface of ``size`` containing a nine-slice-scaled
    copy of ``source``.

    Useful for pre-rendering a scaled panel to avoid scaling every frame.

    Args:
        source: Source nine-slice artwork.
        size:   (width, height) of the output surface.
        border: Corner/edge size — int or (top, right, bottom, left).

    Returns:
        A new ``pygame.Surface`` at the requested size.
    """
    flags = source.get_flags()
    out   = pygame.Surface(size, flags)
    if flags & pygame.SRCALPHA:
        out.fill((0, 0, 0, 0))
    draw_nine_slice(out, source, pygame.Rect(0, 0, *size), border)
    return out


# ── NineSlicePanel widget ─────────────────────────────────────────────────────

class NineSlicePanel:
    """
    A simple container that draws a nine-slice background.

    Not a full Widget subclass — this is intentionally lightweight.
    Compose it with a Stack or Panel for child management.

    Usage::

        source = app.assets.image("ui/dialog.png")
        panel  = NineSlicePanel(rect, source, border=16)

        # In render():
        panel.render(surface)
        # Then render children on top
    """

    def __init__(
        self,
        rect:   pygame.Rect,
        source: pygame.Surface,
        border: int | tuple[int, int, int, int],
    ) -> None:
        """
        Args:
            rect:   Position and size to draw at.
            source: Nine-slice source texture.
            border: Corner/edge size in pixels.
        """
        self.rect    = rect
        self.source  = source
        self.border  = border
        self.visible = True

        self._cached: pygame.Surface | None = None
        self._cached_size: tuple[int, int]  = (0, 0)

    def set_rect(self, rect: pygame.Rect) -> None:
        """Update the panel rect. Invalidates the cached surface."""
        self.rect = rect
        self._cached = None

    def render(self, surface: pygame.Surface, ctx: "RenderContext" = None) -> None:
        """Draw the nine-slice background."""
        if not self.visible:
            return

        size = (self.rect.width, self.rect.height)

        # Rebuild cache only when size changes
        if self._cached is None or self._cached_size != size:
            self._cached      = make_nine_slice_surface(self.source, size,
                                                        self.border)
            self._cached_size = size

        surface.blit(self._cached, self.rect.topleft)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _normalise_border(
    border: int | tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    """
    Return a (top, right, bottom, left) tuple from a border value.

    Args:
        border: Single int (same on all sides) or
                (top, right, bottom, left) tuple.

    Returns:
        (top, right, bottom, left) tuple of ints.
    """
    if isinstance(border, int):
        return (border, border, border, border)
    if len(border) == 4:
        return tuple(border)  # type: ignore[return-value]
    raise ValueError(
        f"border must be an int or a 4-tuple, got {border!r}"
    )