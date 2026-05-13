"""
particles/emitter.py

Particle emitter for pygame_engine.

``Emitter`` spawns, updates, and renders particles. It handles:
- Continuous emission at a given rate (particles/second)
- One-shot bursts
- Per-particle physics: gravity, drag, fade, shrink
- Rendering as filled circles with alpha blending

Emitters are not Widgets. They live in world/surface space and are
updated and rendered directly by scenes or game objects.

Usage::

    from pygame_engine.particles.emitter import Emitter

    # Create a fire emitter at position (320, 400)
    fire = Emitter(
        x=320, y=400,
        rate=40,                       # 40 particles/second
        lifetime=(0.5, 1.2),           # random lifetime between 0.5–1.2s
        speed=(60, 120),               # random speed between 60–120 px/s
        angle=(-110, -70),             # upward spread (degrees)
        colour=((255, 100, 0), (255, 200, 0)),  # orange to yellow
        size=(3, 6),
        size_end=0,
        gravity=30,
    )
    fire.start()

    # Each frame:
    fire.update(dt)
    fire.render(surface)

    # One-shot burst:
    explosion = Emitter(x=400, y=300, ...)
    explosion.burst(50)
"""

from __future__ import annotations

import math
import random
from typing import Union

import pygame

from pygame_engine.particles.particle import Particle


# Type aliases for parameter ranges
_Range = Union[float, tuple[float, float]]
_ColourRange = Union[
    tuple[int, int, int],
    tuple[tuple[int, int, int], tuple[int, int, int]],
]


def _rand(r: _Range) -> float:
    """Return a random float within a range, or the value itself."""
    if isinstance(r, (int, float)):
        return float(r)
    return random.uniform(r[0], r[1])


def _rand_colour(c: _ColourRange) -> tuple[int, int, int]:
    """Return a colour, interpolating between two if a pair is given."""
    if isinstance(c[0], int):
        return c  # type: ignore[return-value]
    a, b = c  # type: ignore[misc]
    t = random.random()
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


class Emitter:
    """
    Spawns, updates, and renders a stream of particles.

    Parameters
    ----------
    Most parameters accept either a fixed value or a ``(min, max)`` tuple
    for randomised per-particle values.

    Position
    --------
    ``(x, y)`` is the world-space emission point. Update ``emitter.x``
    and ``emitter.y`` each frame to follow a moving object.

    Spread
    ------
    ``spread`` — emission radius. Particles spawn within a circle of this
    radius around ``(x, y)``. 0 = all from the same point.

    Angle
    -----
    Direction in degrees (0 = right, 90 = down). Use a tuple for a spread
    range, e.g. ``(-110, -70)`` for an upward fan.
    """

    def __init__(
        self,
        x:         float,
        y:         float,
        rate:      float        = 20.0,
        lifetime:  _Range       = (0.5, 1.5),
        speed:     _Range       = (50.0, 150.0),
        angle:     _Range       = (0.0, 360.0),
        colour:    _ColourRange = (255, 255, 255),  # type: ignore[assignment]
        size:      _Range       = (3.0, 6.0),
        size_end:  _Range       = 0.0,
        gravity:   float        = 0.0,
        drag:      _Range       = 1.0,
        spread:    float        = 0.0,
        alpha_start: _Range     = 255.0,
        max_particles: int      = 500,
    ) -> None:
        """
        Args:
            x, y:          Emission position in surface coordinates.
            rate:          Particles emitted per second (continuous mode).
            lifetime:      Particle lifetime in seconds. Range or fixed.
            speed:         Initial speed in pixels/second. Range or fixed.
            angle:         Emission angle in degrees. Range or fixed.
                           0=right, 90=down, 180=left, 270=up.
            colour:        RGB colour or (colour_a, colour_b) for random
                           interpolation between two colours.
            size:          Initial particle radius. Range or fixed.
            size_end:      Radius at end of life (shrinks to this).
            gravity:       Downward acceleration in pixels/second².
            drag:          Velocity multiplier per second. 1.0 = no drag,
                           0.9 = 10% drag per second.
            spread:        Spawn radius around (x, y).
            alpha_start:   Starting alpha (0–255). Range or fixed.
            max_particles: Hard cap on simultaneous particles.
        """
        self.x = x
        self.y = y

        self._rate         = rate
        self._lifetime     = lifetime
        self._speed        = speed
        self._angle        = angle
        self._colour       = colour
        self._size         = size
        self._size_end     = size_end
        self._gravity      = gravity
        self._drag         = drag
        self._spread       = spread
        self._alpha_start  = alpha_start
        self._max_particles = max_particles

        self._particles:   list[Particle] = []
        self._accumulator: float          = 0.0
        self._running:     bool           = False
        self._one_shot:    bool           = False

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Begin continuous emission."""
        self._running  = True
        self._one_shot = False

    def stop(self) -> None:
        """Stop emitting new particles (existing particles continue)."""
        self._running = False

    def burst(self, count: int) -> None:
        """
        Emit ``count`` particles immediately (one-shot mode).

        Does not require ``start()`` — just call ``burst()`` and update.
        """
        for _ in range(min(count,
                           self._max_particles - len(self._particles))):
            self._spawn_one()

    def clear(self) -> None:
        """Remove all active particles immediately."""
        self._particles.clear()

    @property
    def is_running(self) -> bool:
        """True while continuous emission is active."""
        return self._running

    @property
    def particle_count(self) -> int:
        """Number of currently active particles."""
        return len(self._particles)

    @property
    def is_empty(self) -> bool:
        """True when there are no active particles."""
        return len(self._particles) == 0

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Advance all particles by one frame and spawn new ones.

        Args:
            dt: Delta time in seconds.
        """
        # Spawn new particles (continuous mode)
        if self._running and self._rate > 0:
            self._accumulator += self._rate * dt
            while (self._accumulator >= 1.0
                   and len(self._particles) < self._max_particles):
                self._spawn_one()
                self._accumulator -= 1.0

        # Update existing particles
        alive: list[Particle] = []
        for p in self._particles:
            p.age += dt

            if p.is_dead:
                continue

            # Physics
            p.vx = (p.vx + p.ax * dt) * (p.drag ** dt)
            p.vy = (p.vy + (p.ay + self._gravity) * dt) * (p.drag ** dt)
            p.x += p.vx * dt
            p.y += p.vy * dt

            # Fade and shrink
            t        = p.progress
            p.alpha  = 255.0 * (1.0 - t)
            p.size   = p.size + (p.size_end - p.size) * dt / max(p.lifetime - p.age + dt, 0.001)

            alive.append(p)

        self._particles = alive

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """
        Draw all active particles onto ``surface``.

        Uses ``pygame.draw.circle`` with alpha blending via a temporary
        SRCALPHA surface per particle. For large particle counts consider
        using ``render_fast()`` which skips alpha.

        Args:
            surface: The surface to render onto (world/display surface).
        """
        for p in self._particles:
            alpha = int(max(0.0, min(255.0, p.alpha)))
            size  = max(1, int(p.size))
            if alpha <= 0:
                continue

            # Draw with alpha using a small temp surface
            diameter = size * 2
            tmp = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (p.r, p.g, p.b, alpha),
                               (size, size), size)
            surface.blit(tmp, (int(p.x) - size, int(p.y) - size))

    def render_fast(self, surface: pygame.Surface) -> None:
        """
        Draw particles without alpha blending.

        Much faster for high particle counts. Particles appear solid
        (no fade). Good for effects where overdraw is acceptable.

        Args:
            surface: The surface to render onto.
        """
        for p in self._particles:
            size = max(1, int(p.size))
            pygame.draw.circle(surface, (p.r, p.g, p.b),
                               (int(p.x), int(p.y)), size)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _spawn_one(self) -> None:
        """Spawn a single particle at the emission point."""
        # Position with spread
        if self._spread > 0:
            angle_r = random.uniform(0, math.tau)
            dist    = random.uniform(0, self._spread)
            ox      = math.cos(angle_r) * dist
            oy      = math.sin(angle_r) * dist
        else:
            ox, oy = 0.0, 0.0

        # Velocity from angle + speed
        angle_deg = _rand(self._angle)
        angle_rad = math.radians(angle_deg)
        speed     = _rand(self._speed)
        vx        = math.cos(angle_rad) * speed
        vy        = math.sin(angle_rad) * speed

        r, g, b = _rand_colour(self._colour)  # type: ignore[arg-type]

        self._particles.append(Particle(
            x=self.x + ox,
            y=self.y + oy,
            vx=vx,
            vy=vy,
            r=r, g=g, b=b,
            lifetime=_rand(self._lifetime),
            size=_rand(self._size),
            size_end=_rand(self._size_end),
            drag=_rand(self._drag),
            alpha_start=_rand(self._alpha_start),
        ))
