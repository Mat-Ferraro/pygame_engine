"""
pygame_engine.lighting

2D lighting overlay system.

Simulates 2D lighting using a dark overlay with radial gradient
cut-outs for each light source. Supports flicker, colour, and
camera-aware world-space positioning.

Public API::

    from pygame_engine.lighting import Light, LightingSystem

    lights = LightingSystem(ambient=(15, 20, 35), darkness=0.92)
    torch  = lights.add(Light(world_x=400, world_y=300,
                               radius=180, colour=(255, 190, 80),
                               intensity=0.95, flicker=0.2))

    # Each frame:
    lights.update(dt)
    lights.render(surface, camera)   # after world, before UI
"""

from pygame_engine.lighting.lighting import Light, LightingSystem

__all__ = ["Light", "LightingSystem"]
