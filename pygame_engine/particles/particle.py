"""
particles/particle.py

Single particle data for pygame_engine.

A ``Particle`` is a plain data object. It holds position, velocity,
acceleration, colour, size, alpha, and lifetime. The ``Emitter`` owns
and updates a list of these each frame.

Particles live in world/surface space, not UI space. They are not
Widgets — they are rendered directly by the Emitter onto a surface.
"""

from __future__ import annotations

import random


class Particle:
    """
    Single particle — a lightweight data container.

    All fields are public and mutated directly by ``Emitter.update()``.
    No methods beyond ``__init__`` — keep it fast.
    """

    __slots__ = (
        "x", "y",           # position (float)
        "vx", "vy",         # velocity (pixels/second)
        "ax", "ay",         # acceleration (pixels/second²) — for gravity
        "r", "g", "b",      # base colour channels (0–255)
        "alpha",            # current alpha (0.0–255.0)
        "size",             # current radius in pixels (float)
        "size_end",         # radius at end of life (shrinks toward this)
        "lifetime",         # total lifetime in seconds
        "age",              # elapsed time in seconds
        "drag",             # velocity multiplier per second (0.95 = 5% drag)
    )

    def __init__(
        self,
        x: float, y: float,
        vx: float, vy: float,
        r: int, g: int, b: int,
        lifetime: float,
        size: float       = 4.0,
        size_end: float   = 0.0,
        ax: float         = 0.0,
        ay: float         = 0.0,
        drag: float       = 1.0,
        alpha_start: float = 255.0,
    ) -> None:
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.ax, self.ay = ax, ay
        self.r, self.g, self.b = r, g, b
        self.alpha    = alpha_start
        self.size     = size
        self.size_end = size_end
        self.lifetime = lifetime
        self.age      = 0.0
        self.drag     = drag

    @property
    def progress(self) -> float:
        """Normalised age from 0.0 (just spawned) to 1.0 (expired)."""
        if self.lifetime <= 0:
            return 1.0
        return min(self.age / self.lifetime, 1.0)

    @property
    def is_dead(self) -> bool:
        """True when the particle has exceeded its lifetime."""
        return self.age >= self.lifetime
