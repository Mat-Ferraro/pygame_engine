"""
pygame_engine.camera

2D camera for world-space / screen-space coordinate conversion.

Public API::

    from pygame_engine.camera import Camera

    camera = Camera(viewport_width=1280, viewport_height=720)
    camera.follow(player.rect.center, speed=6.0, dt=dt)
    screen_rect = camera.world_rect_to_screen(enemy.rect)
    camera.add_trauma(0.5)
    camera.update(dt)
"""

from pygame_engine.camera.camera import Camera

__all__ = ["Camera"]
