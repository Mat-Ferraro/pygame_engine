"""
graphics/sprite_renderer.py

Sprite rendering helpers for pygame_engine.

Provides ``draw_sprite`` — a single function that draws a pygame.Surface
(sprite frame) onto a destination surface with optional transform support:
flip, scale, alpha, and rotation.

Also provides ``draw_animation_frame`` as a convenience wrapper for
rendering an ``AnimationPlayer``'s current frame.

Usage::

    from pygame_engine.graphics.sprite_renderer import draw_sprite

    # Basic — draw frame at rect position
    draw_sprite(surface, frame, rect)

    # With transforms
    draw_sprite(surface, frame, rect, flip_x=True, alpha=180)

    # From an AnimationPlayer
    from pygame_engine.graphics.sprite_renderer import draw_animation_frame
    draw_animation_frame(surface, player, rect)
"""

from __future__ import annotations

import pygame


def draw_sprite(
    dest:     pygame.Surface,
    frame:    pygame.Surface,
    rect:     pygame.Rect,
    flip_x:   bool  = False,
    flip_y:   bool  = False,
    alpha:    int   = 255,
    rotation: float = 0.0,
    scale:    float = 1.0,
) -> None:
    """
    Draw a sprite frame onto ``dest`` at ``rect``.

    The frame is scaled to fit ``rect`` before any other transforms are
    applied, unless ``scale`` overrides this.

    Args:
        dest:     Destination surface.
        frame:    The sprite surface to draw.
        rect:     Destination position and size. The frame is scaled to
                  match ``rect.size`` before drawing.
        flip_x:   Mirror horizontally.
        flip_y:   Mirror vertically.
        alpha:    Overall opacity 0–255.
        rotation: Clockwise rotation in degrees. 0 = no rotation.
        scale:    Additional scale multiplier applied after rect sizing.
                  1.0 = no additional scale.
    """
    if frame is None or alpha <= 0:
        return

    # Scale to rect size
    w, h = rect.size
    if scale != 1.0:
        w = int(w * scale)
        h = int(h * scale)

    if (w, h) != frame.get_size():
        frame = pygame.transform.scale(frame, (w, h))

    # Flip
    if flip_x or flip_y:
        frame = pygame.transform.flip(frame, flip_x, flip_y)

    # Rotate
    if rotation != 0.0:
        frame = pygame.transform.rotate(frame, -rotation)  # pygame is CCW

    # Alpha
    if alpha < 255:
        frame = frame.copy()
        frame.set_alpha(alpha)

    # Blit — centre on rect if rotation changed the size
    if rotation != 0.0:
        fr = frame.get_rect(center=rect.center)
        dest.blit(frame, fr.topleft)
    else:
        dest.blit(frame, rect.topleft)


def draw_animation_frame(
    dest:     pygame.Surface,
    player:   object,
    rect:     pygame.Rect,
    flip_x:   bool  = False,
    flip_y:   bool  = False,
    alpha:    int   = 255,
    rotation: float = 0.0,
    scale:    float = 1.0,
) -> None:
    """
    Draw the current frame of an ``AnimationPlayer`` onto ``dest``.

    A no-op if the player has no current frame (stopped or unstarted).

    Args:
        dest:   Destination surface.
        player: An ``AnimationPlayer`` instance.
        rect:   Destination position and size.
        flip_x: Mirror horizontally.
        flip_y: Mirror vertically.
        alpha:  Overall opacity 0–255.
        rotation: Clockwise rotation in degrees.
        scale:  Additional scale multiplier.
    """
    frame = getattr(player, "current_frame", None)
    if frame is None:
        return
    draw_sprite(dest, frame, rect,
                flip_x=flip_x, flip_y=flip_y,
                alpha=alpha, rotation=rotation, scale=scale)
