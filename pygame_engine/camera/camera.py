"""
A 2D camera that converts between world-space and screen-space coordinates.
Supports smooth target following, zoom, and trauma-based screen shake.

Usage::

    from pygame_engine.camera import Camera

    camera = Camera(viewport_width=1280, viewport_height=720)

    # Follow the player each frame
    camera.follow(player.rect.center, speed=5.0, dt=dt)

    # Convert world positions to screen positions for rendering
    screen_pos = camera.world_to_screen(enemy.rect.topleft)

    # Apply to a rect
    screen_rect = camera.world_rect_to_screen(enemy.rect)

    # Add trauma on hit (screen shake)
    camera.add_trauma(0.6)
"""

from __future__ import annotations

import math
import random

import pygame

from pygame_engine.utils.mathx import clamp, lerp


class Camera:
    """
    2D camera with smooth follow, zoom, and screen shake.

    Coordinate model
    ----------------
    The camera has a ``position`` in world space — the world point that
    maps to the centre of the viewport. Everything is expressed relative
    to this point.

    Screen shake
    ------------
    Uses a trauma model: ``add_trauma(amount)`` adds to a [0, 1] trauma
    value that decays over time. Shake offset = trauma² × max_shake_offset.
    This produces natural-feeling shake that diminishes smoothly.

    Zoom
    ----
    A zoom of 1.0 is no zoom. 2.0 means world units appear twice as large
    on screen. 0.5 means the viewport shows twice the world area.
    """

    def __init__(
        self,
        viewport_width:  int,
        viewport_height: int,
        zoom:            float = 1.0,
    ) -> None:
        """
        Args:
            viewport_width:  Width of the screen/viewport in pixels.
            viewport_height: Height of the screen/viewport in pixels.
            zoom:            Initial zoom level. 1.0 = no zoom.
        """
        self._vp_w    = viewport_width
        self._vp_h    = viewport_height
        self._zoom    = max(0.01, zoom)
        self._pos_x   = float(viewport_width  / 2)
        self._pos_y   = float(viewport_height / 2)

        # Screen shake
        self._trauma:          float = 0.0   # [0, 1]
        self._trauma_decay:    float = 1.2   # trauma units lost per second
        self._max_shake_px:    int   = 20    # max pixel offset at full trauma
        self._max_shake_angle: float = 5.0   # max rotation degrees at full trauma
        self._shake_offset_x:  float = 0.0
        self._shake_offset_y:  float = 0.0

        # World bounds clamping (optional)
        self._world_bounds: pygame.Rect | None = None

    # ── Public API — configuration ────────────────────────────────────────────

    @property
    def position(self) -> tuple[float, float]:
        """World-space position the camera is centred on."""
        return (self._pos_x, self._pos_y)

    @position.setter
    def position(self, pos: tuple[float, float]) -> None:
        """Return the current camera position in world space."""
        self._pos_x, self._pos_y = float(pos[0]), float(pos[1])
        self._clamp_to_bounds()

    @property
    def zoom(self) -> float:
        """Return the current zoom level."""
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        """Return the current zoom level."""
        self._zoom = max(0.01, value)

    @property
    def viewport_size(self) -> tuple[int, int]:
        """Return the viewport size as (width, height)."""
        return (self._vp_w, self._vp_h)

    @viewport_size.setter
    def viewport_size(self, size: tuple[int, int]) -> None:
        """Return the viewport size as (width, height)."""
        self._vp_w, self._vp_h = size

    @property
    def trauma(self) -> float:
        """Return the current trauma level (0.0–1.0)."""
        return self._trauma

    def set_world_bounds(self, bounds: pygame.Rect | None) -> None:
        """
        Clamp the camera so the viewport never shows outside this rect.

        Pass ``None`` to remove bounds. Bounds should be at least as large
        as the viewport; smaller bounds are clamped silently.

        Args:
            bounds: World-space rect the camera cannot pan beyond.
        """
        self._world_bounds = pygame.Rect(bounds) if bounds else None
        self._clamp_to_bounds()

    # ── Public API — movement ─────────────────────────────────────────────────

    def move_to(self, world_pos: tuple[float, float]) -> None:
        """Instantly centre the camera on a world position."""
        self.position = world_pos

    def follow(
        self,
        target:    tuple[float, float],
        speed:     float = 5.0,
        dt:        float = 0.016,
        threshold: float = 1.0,
    ) -> None:
        """
        Smoothly move the camera towards ``target``.

        Uses exponential decay so the camera always approaches the target
        asymptotically, feeling natural without overshooting.

        Args:
            target:    World-space position to follow.
            speed:     Approach speed in camera-position units per second.
                       Higher = snappier. Recommended: 3–10.
            dt:        Delta-time from the frame loop.
            threshold: Stop moving when distance < threshold (avoids jitter).
        """
        tx, ty = float(target[0]), float(target[1])
        dx = tx - self._pos_x
        dy = ty - self._pos_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < threshold:
            return
        t = clamp(speed * dt, 0.0, 1.0)
        self._pos_x = lerp(self._pos_x, tx, t)
        self._pos_y = lerp(self._pos_y, ty, t)
        self._clamp_to_bounds()

    # ── Public API — screen shake ─────────────────────────────────────────────

    def add_trauma(self, amount: float) -> None:
        """
        Add screen-shake trauma in [0, 1].

        Trauma accumulates (clamped to 1.0) and decays over time via
        ``update()``. Typical values: 0.3 = light, 0.6 = medium, 1.0 = heavy.

        Args:
            amount: Trauma to add. Clamped to keep total in [0, 1].
        """
        self._trauma = clamp(self._trauma + amount, 0.0, 1.0)

    def update(self, dt: float) -> None:
        """
        Decay trauma and recompute shake offset.

        Call once per frame before any coordinate conversion.

        Args:
            dt: Delta-time from the frame loop.
        """
        self._trauma = max(0.0, self._trauma - self._trauma_decay * dt)
        shake = self._trauma * self._trauma
        self._shake_offset_x = random.uniform(-1, 1) * self._max_shake_px * shake
        self._shake_offset_y = random.uniform(-1, 1) * self._max_shake_px * shake

    # ── Public API — coordinate conversion ───────────────────────────────────

    def world_to_screen(self, world_pos: tuple[float, float]) -> tuple[int, int]:
        """
        Convert a world-space position to a screen-space pixel position.

        Args:
            world_pos: (x, y) in world space.

        Returns:
            (x, y) in screen pixels.
        """
        wx, wy = world_pos
        sx = (wx - self._pos_x) * self._zoom + self._vp_w / 2 + self._shake_offset_x
        sy = (wy - self._pos_y) * self._zoom + self._vp_h / 2 + self._shake_offset_y
        return (int(sx), int(sy))

    def screen_to_world(self, screen_pos: tuple[int, int]) -> tuple[float, float]:
        """
        Convert a screen-space pixel position to a world-space position.

        Useful for mouse picking and click-to-move.

        Args:
            screen_pos: (x, y) in screen pixels.

        Returns:
            (x, y) in world space.
        """
        px, py = screen_pos
        wx = (px - self._vp_w / 2 - self._shake_offset_x) / self._zoom + self._pos_x
        wy = (py - self._vp_h / 2 - self._shake_offset_y) / self._zoom + self._pos_y
        return (wx, wy)

    def world_rect_to_screen(self, world_rect: pygame.Rect) -> pygame.Rect:
        """
        Convert a world-space rect to a screen-space rect.

        Args:
            world_rect: Rect in world coordinates.

        Returns:
            Rect in screen coordinates with zoom applied to size.
        """
        sx, sy = self.world_to_screen(world_rect.topleft)
        sw = int(world_rect.width  * self._zoom)
        sh = int(world_rect.height * self._zoom)
        return pygame.Rect(sx, sy, sw, sh)

    def is_visible(self, world_rect: pygame.Rect, margin: int = 0) -> bool:
        """
        Return True if a world-space rect is at least partially on screen.

        Use this to cull entities before drawing.

        Args:
            world_rect: Rect in world coordinates.
            margin:     Extra pixels of margin around the viewport to keep
                        off-screen objects alive slightly longer.
        """
        sr = self.world_rect_to_screen(world_rect)
        vp = pygame.Rect(-margin, -margin,
                         self._vp_w + margin * 2,
                         self._vp_h + margin * 2)
        return sr.colliderect(vp)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _clamp_to_bounds(self) -> None:
        if self._world_bounds is None:
            return
        half_w = (self._vp_w / 2) / self._zoom
        half_h = (self._vp_h / 2) / self._zoom
        b = self._world_bounds
        self._pos_x = clamp(self._pos_x,
                            b.left  + half_w,
                            b.right - half_w)
        self._pos_y = clamp(self._pos_y,
                            b.top    + half_h,
                            b.bottom - half_h)

    def __repr__(self) -> str:
        return (f"Camera(pos=({self._pos_x:.1f}, {self._pos_y:.1f}), "
                f"zoom={self._zoom:.2f}, trauma={self._trauma:.2f})")