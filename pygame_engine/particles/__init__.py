"""
pygame_engine.particles

Particle system for visual effects.

Public API::

    from pygame_engine.particles import Emitter
    from pygame_engine.particles.particle import Particle
    from pygame_engine.particles.presets import (
        explosion, sparkle, smoke, fire_emitter, trail, hit_effect
    )

Quick start::

    from pygame_engine.particles.presets import explosion

    fx = explosion(400, 300)
    fx.burst(60)

    # Each frame:
    fx.update(dt)
    fx.render(surface)
"""

from pygame_engine.particles.emitter import Emitter
from pygame_engine.particles.particle import Particle

__all__ = ["Emitter", "Particle"]
