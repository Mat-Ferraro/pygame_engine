"""
2D lighting system for pygame_engine.

Simulates 2D lighting by rendering a dark overlay with alpha cutouts for
light sources. Not physically accurate — a visually convincing technique
used by countless indie games.

Each frame:
1. The game renders the world normally.
2. Call ``LightingSystem.render(surface, camera)`` to draw the darkness
   overlay on top, with light circles cut out.

Usage::

    from pygame_engine.lighting import LightingSystem, Light

    lights = LightingSystem(ambient=(20, 20, 35))

    # Add lights
    torch  = lights.add(Light(world_x=200, world_y=300,
                               radius=180, colour=(255, 200, 100),
                               intensity=0.95))
    player_light = lights.add(Light(world_x=0, world_y=0,
                                     radius=120, colour=(200, 220, 255),
                                     intensity=0.7))

    # Each frame — update positions and render
    player_light.world_x = player.rect.centerx
    player_light.world_y = player.rect.centery
    lights.render(surface, camera)   # call after world render, before UI
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from pygame_engine.utils.mathx import clamp

if TYPE_CHECKING:
    from pygame_engine.camera import Camera


class Light:
    """
    A single 2D light source.

    Args:
        world_x:    X position in world space.
        world_y:    Y position in world space.
        radius:     Radius of the light circle in world pixels.
        colour:     RGB colour of the light. Default warm white.
        intensity:  How much darkness the light removes [0, 1].
                    1.0 = fully lit at centre, 0.0 = invisible.
        flicker:    Flicker amplitude [0, 1]. 0 = steady.
        enabled:    Whether this light is active.
    """

    def __init__(
        self,
        world_x:   float = 0.0,
        world_y:   float = 0.0,
        radius:    float = 150.0,
        colour:    tuple[int, int, int] = (255, 220, 160),
        intensity: float = 0.9,
        flicker:   float = 0.0,
        enabled:   bool  = True,
    ) -> None:
        self.world_x   = world_x
        self.world_y   = world_y
        self.radius    = radius
        self.colour    = colour
        self.intensity = clamp(intensity, 0.0, 1.0)
        self.flicker   = clamp(flicker,   0.0, 1.0)
        self.enabled   = enabled

        self._flicker_offset = 0.0
        self._flicker_time   = 0.0

    def update(self, dt: float) -> None:
        """Update flicker animation. Call each frame if flicker > 0."""
        if self.flicker > 0:
            import random
            self._flicker_time   += dt * 8.0
            self._flicker_offset  = (
                math.sin(self._flicker_time * 3.7) * 0.3
                + math.sin(self._flicker_time * 7.1) * 0.15
                + random.uniform(-0.1, 0.1) * 0.5
            ) * self.flicker

    @property
    def effective_intensity(self) -> float:
        return clamp(self.intensity + self._flicker_offset, 0.0, 1.0)

    @property
    def effective_radius(self) -> float:
        return max(1.0, self.radius * (1.0 + self._flicker_offset * 0.15))


class LightingSystem:
    """
    Renders a 2D lighting overlay over the game world.

    Creates a dark alpha surface covering the viewport and punches
    radial gradient "holes" for each enabled light source.

    Args:
        ambient: RGB colour of the darkness. ``(0, 0, 0)`` = pitch black.
                 Use a dark colour like ``(15, 20, 35)`` for moonlight.
        darkness: Global darkness opacity [0, 1]. 1.0 = fully dark without
                  lights. 0.0 = no darkness at all.
    """

    def __init__(
        self,
        ambient:  tuple[int, int, int] = (10, 10, 20),
        darkness: float = 1.0,
    ) -> None:
        self._ambient  = ambient
        self._darkness = clamp(darkness, 0.0, 1.0)
        self._lights:  list[Light] = []

    # ── Light management ──────────────────────────────────────────────────────

    def add(self, light: Light) -> Light:
        """Register a light source. Returns the light for convenience."""
        self._lights.append(light)
        return light

    def remove(self, light: Light) -> bool:
        """Remove a light source. Returns True if found."""
        try:
            self._lights.remove(light)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Remove all light sources."""
        self._lights.clear()

    @property
    def lights(self) -> list[Light]:
        return list(self._lights)

    @property
    def darkness(self) -> float:
        return self._darkness

    @darkness.setter
    def darkness(self, value: float) -> None:
        self._darkness = clamp(value, 0.0, 1.0)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Update all flickering lights. Call each frame."""
        for light in self._lights:
            if light.enabled and light.flicker > 0:
                light.update(dt)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(
        self,
        surface: pygame.Surface,
        camera:  "Camera | None" = None,
    ) -> None:
        """
        Draw the lighting overlay onto ``surface``.

        Call this after rendering the world but before rendering UI.

        Args:
            surface: The surface to draw the overlay onto.
            camera:  Optional Camera for world-to-screen conversion.
                     If None, light positions are treated as screen coords.
        """
        if self._darkness <= 0.0:
            return

        vp_w, vp_h = surface.get_size()
        overlay     = pygame.Surface((vp_w, vp_h), pygame.SRCALPHA)
        alpha       = int(self._darkness * 255)
        overlay.fill((*self._ambient, alpha))

        # Draw each light as a radial gradient cut-out
        for light in self._lights:
            if not light.enabled:
                continue

            # Convert world position to screen position
            if camera is not None:
                sx, sy = camera.world_to_screen((light.world_x, light.world_y))
                zoom   = camera.zoom
                screen_radius = int(light.effective_radius * zoom)
            else:
                sx, sy        = int(light.world_x), int(light.world_y)
                screen_radius = int(light.effective_radius)

            if screen_radius <= 0:
                continue

            # Cull lights fully outside viewport
            if (sx + screen_radius < 0 or sx - screen_radius > vp_w or
                    sy + screen_radius < 0 or sy - screen_radius > vp_h):
                continue

            self._draw_light(overlay, sx, sy, screen_radius,
                             light.colour, light.effective_intensity)

        surface.blit(overlay, (0, 0))

    def _draw_light(
        self,
        overlay:   pygame.Surface,
        cx:        int,
        cy:        int,
        radius:    int,
        colour:    tuple[int, int, int],
        intensity: float,
    ) -> None:
        """Draw a single radial gradient light onto the overlay."""
        # Create a temporary surface for the gradient
        diam   = radius * 2
        light_surf = pygame.Surface((diam, diam), pygame.SRCALPHA)

        # Radial gradient: solid at centre, transparent at edge
        # Draw concentric circles from outside in
        steps = min(radius, 48)
        for i in range(steps, 0, -1):
            t     = i / steps                    # 1.0 at edge, 0.0 at centre
            alpha = int((1.0 - t) * intensity * 255)
            r     = int(radius * t / steps * steps)
            if alpha <= 0 or r <= 0:
                continue
            # We use BLEND_RGBA_MAX so each ring only adds transparency
            pygame.draw.circle(
                light_surf,
                (*colour, alpha),
                (radius, radius),
                r,
            )

        # Blit the light with subtract blend — removes darkness
        overlay.blit(
            light_surf,
            (cx - radius, cy - radius),
            special_flags=pygame.BLEND_RGBA_SUB,
        )

    def __repr__(self) -> str:
        return (f"LightingSystem({len(self._lights)} lights, "
                f"darkness={self._darkness:.1f})")
