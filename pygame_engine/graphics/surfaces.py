"""
graphics/surfaces.py

Surface creation and alpha-blitting helpers for pygame_engine.

These helpers consolidate the SRCALPHA surface creation, alpha fade, and
blit patterns used by Toast, Tooltip, and other widgets that need
partially-transparent drawing.

Usage::

    from pygame_engine.graphics.surfaces import (
        make_alpha_surface,
        blit_alpha,
        blit_alpha_surface,
    )

    # Create a 200x80 SRCALPHA surface
    surf = make_alpha_surface(200, 80)

    # Blit a surface at a given alpha (0–255) without mutating it
    blit_alpha(dest, source, (x, y), alpha=180)
"""

from __future__ import annotations

import pygame


# ── Surface creation ──────────────────────────────────────────────────────────

def make_alpha_surface(width: int, height: int) -> pygame.Surface:
    """
    Create a transparent (SRCALPHA) surface of the given size.

    Args:
        width:  Surface width in pixels.
        height: Surface height in pixels.

    Returns:
        A new ``pygame.Surface`` with per-pixel alpha, cleared to
        fully transparent.
    """
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    return surf


def make_solid_surface(
    width: int,
    height: int,
    colour: tuple[int, int, int],
) -> pygame.Surface:
    """
    Create a solid-colour surface with no alpha channel.

    Args:
        width:  Surface width in pixels.
        height: Surface height in pixels.
        colour: RGB fill colour.

    Returns:
        A new filled ``pygame.Surface``.
    """
    surf = pygame.Surface((width, height))
    surf.fill(colour)
    return surf


# ── Alpha blitting ────────────────────────────────────────────────────────────

def blit_alpha(
    dest: pygame.Surface,
    source: pygame.Surface,
    pos: tuple[int, int],
    alpha: int,
) -> None:
    """
    Blit ``source`` onto ``dest`` at ``pos`` with an overall alpha value.

    Copies the source surface before applying alpha so the original is
    not mutated. Useful for fade-in/out effects on cached surfaces.

    Args:
        dest:   Destination surface.
        source: Source surface to blit.
        pos:    (x, y) destination position.
        alpha:  Overall alpha 0 (transparent) – 255 (opaque).
    """
    if alpha <= 0:
        return
    if alpha >= 255:
        dest.blit(source, pos)
        return
    temp = source.copy()
    temp.set_alpha(alpha)
    dest.blit(temp, pos)


def blit_alpha_surface(
    dest: pygame.Surface,
    source: pygame.Surface,
    pos: tuple[int, int],
    alpha: float,
) -> None:
    """
    Blit ``source`` at a normalised alpha (0.0 – 1.0).

    Convenience wrapper over ``blit_alpha`` for callers working with
    0.0–1.0 floats (e.g. Tween or Timer progress values).

    Args:
        dest:   Destination surface.
        source: Source surface to blit.
        pos:    (x, y) destination position.
        alpha:  Normalised alpha 0.0 (transparent) – 1.0 (opaque).
    """
    blit_alpha(dest, source, pos, int(max(0.0, min(1.0, alpha)) * 255))


# ── Surface sampling ──────────────────────────────────────────────────────────

def scale_surface(
    surface: pygame.Surface,
    width: int,
    height: int,
    smooth: bool = True,
) -> pygame.Surface:
    """
    Scale a surface to the given dimensions.

    Args:
        surface: Source surface.
        width:   Target width.
        height:  Target height.
        smooth:  Use ``smoothscale`` (better quality) if True,
                 ``scale`` (faster) if False.

    Returns:
        A new scaled surface.
    """
    if smooth:
        return pygame.transform.smoothscale(surface, (width, height))
    return pygame.transform.scale(surface, (width, height))


def crop_surface(
    surface: pygame.Surface,
    rect: pygame.Rect,
) -> pygame.Surface:
    """
    Return a new surface containing only the region defined by ``rect``.

    Args:
        surface: Source surface.
        rect:    Region to crop.

    Returns:
        A new surface with the cropped content.
    """
    cropped = pygame.Surface((rect.width, rect.height), surface.get_flags())
    cropped.blit(surface, (0, 0), rect)
    return cropped
