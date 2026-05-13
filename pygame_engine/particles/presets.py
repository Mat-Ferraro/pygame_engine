"""
particles/presets.py

Common particle effect presets for pygame_engine.

Each function returns a configured ``Emitter`` ready to use. Call
``emitter.start()`` for continuous effects or ``emitter.burst(n)``
for one-shot effects.

Usage::

    from pygame_engine.particles.presets import explosion, sparkle, smoke, trail

    # One-shot explosion at (400, 300)
    fx = explosion(400, 300)
    fx.burst(60)

    # Continuous fire at (320, 450)
    fire = fire_emitter(320, 450)
    fire.start()

    # Each frame:
    fx.update(dt)
    fx.render(surface)
"""

from __future__ import annotations

from pygame_engine.particles.emitter import Emitter


def explosion(
    x: float,
    y: float,
    colour: tuple = ((255, 180, 0), (255, 80, 0)),
    speed: tuple  = (80, 280),
    count: int    = 60,
) -> Emitter:
    """
    One-shot explosion burst.

    Call ``emitter.burst(count)`` immediately after creation.
    Particles fly outward in all directions with gravity and drag.

    Args:
        x, y:   Centre of the explosion.
        colour: Colour range (default orange/red fire).
        speed:  Particle speed range (pixels/second).
        count:  Suggested burst count (pass to ``burst()``).

    Returns:
        Configured ``Emitter``. Call ``.burst(count)`` to fire.

    Example::

        fx = explosion(400, 300)
        fx.burst(60)
    """
    return Emitter(
        x=x, y=y,
        rate=0,
        lifetime=(0.4, 1.0),
        speed=speed,
        angle=(0.0, 360.0),
        colour=colour,    # type: ignore[arg-type]
        size=(2.0, 5.0),
        size_end=0.0,
        gravity=80.0,
        drag=0.92,
        spread=4.0,
    )


def sparkle(
    x: float,
    y: float,
    colour: tuple = ((255, 255, 120), (200, 220, 255)),
    count: int    = 20,
) -> Emitter:
    """
    Glittery sparkle burst — short-lived, slow-moving bright particles.

    Good for pickups, stars, and magic effects.

    Args:
        x, y:   Spawn position.
        colour: Colour range (default gold/white).
        count:  Suggested burst count.

    Returns:
        Configured ``Emitter``. Call ``.burst(count)`` to fire.
    """
    return Emitter(
        x=x, y=y,
        rate=0,
        lifetime=(0.3, 0.8),
        speed=(20.0, 80.0),
        angle=(0.0, 360.0),
        colour=colour,    # type: ignore[arg-type]
        size=(1.5, 3.5),
        size_end=0.0,
        gravity=-20.0,    # slight upward drift
        drag=0.85,
        spread=6.0,
    )


def smoke(
    x: float,
    y: float,
    rate: float   = 8.0,
    colour: tuple = ((80, 80, 80), (140, 140, 140)),
) -> Emitter:
    """
    Continuous smoke plume drifting upward.

    Call ``emitter.start()`` to begin and ``emitter.stop()`` to end.

    Args:
        x, y:   Base position of the smoke source.
        rate:   Particles per second.
        colour: Grey range (default dark/light grey).

    Returns:
        Configured ``Emitter``. Call ``.start()`` to begin emitting.
    """
    return Emitter(
        x=x, y=y,
        rate=rate,
        lifetime=(1.5, 3.0),
        speed=(15.0, 40.0),
        angle=(-100.0, -80.0),   # mostly upward
        colour=colour,            # type: ignore[arg-type]
        size=(4.0, 8.0),
        size_end=12.0,            # grows as it rises
        gravity=-15.0,
        drag=0.97,
        spread=8.0,
        alpha_start=(180.0, 220.0),
    )


def fire_emitter(
    x: float,
    y: float,
    rate: float = 35.0,
    intensity: float = 1.0,
) -> Emitter:
    """
    Continuous fire emitter.

    Call ``emitter.start()`` to begin and ``emitter.stop()`` to end.
    Scale ``rate`` and ``intensity`` for larger/smaller flames.

    Args:
        x, y:      Base position (bottom of flame).
        rate:      Particles per second.
        intensity: Multiplier on speed and size (1.0 = normal).

    Returns:
        Configured ``Emitter``. Call ``.start()`` to begin emitting.
    """
    spd = (60 * intensity, 130 * intensity)
    sz  = (2.0 * intensity, 5.0 * intensity)
    return Emitter(
        x=x, y=y,
        rate=rate,
        lifetime=(0.4, 0.9),
        speed=spd,
        angle=(-110.0, -70.0),   # upward fan
        colour=((255, 60, 0), (255, 200, 0)),   # type: ignore[arg-type]
        size=sz,
        size_end=0.0,
        gravity=-20.0,
        drag=0.94,
        spread=6.0 * intensity,
    )


def trail(
    x: float,
    y: float,
    colour: tuple = (180, 180, 255),
    rate: float   = 30.0,
) -> Emitter:
    """
    Short-lived motion trail — attach to a moving object and update
    ``emitter.x``, ``emitter.y`` each frame.

    Args:
        x, y:   Starting position (update each frame).
        colour: Trail colour (default light blue).
        rate:   Particles per second.

    Returns:
        Configured ``Emitter``. Call ``.start()`` to begin emitting.

    Example::

        trail_fx = trail(player.x, player.y)
        trail_fx.start()

        # Each frame:
        trail_fx.x = player.x
        trail_fx.y = player.y
        trail_fx.update(dt)
        trail_fx.render(surface)
    """
    return Emitter(
        x=x, y=y,
        rate=rate,
        lifetime=(0.15, 0.35),
        speed=(5.0, 20.0),
        angle=(0.0, 360.0),
        colour=colour,            # type: ignore[arg-type]
        size=(2.0, 4.0),
        size_end=0.0,
        gravity=0.0,
        drag=0.80,
        spread=2.0,
        alpha_start=(160.0, 220.0),
    )


def hit_effect(
    x: float,
    y: float,
    colour: tuple = (255, 60, 60),
    count: int    = 12,
) -> Emitter:
    """
    Small impact burst — for hits, collisions, and damage feedback.

    Args:
        x, y:   Impact position.
        colour: Particle colour (default red).
        count:  Suggested burst count.

    Returns:
        Configured ``Emitter``. Call ``.burst(count)`` to fire.
    """
    return Emitter(
        x=x, y=y,
        rate=0,
        lifetime=(0.2, 0.5),
        speed=(40.0, 120.0),
        angle=(0.0, 360.0),
        colour=colour,            # type: ignore[arg-type]
        size=(1.5, 3.5),
        size_end=0.0,
        gravity=60.0,
        drag=0.88,
        spread=3.0,
    )
