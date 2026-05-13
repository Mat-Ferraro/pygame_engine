"""
pygame_engine.tilemap

2D tile map system with layered rendering, camera culling, and collision.

Public API::

    from pygame_engine.tilemap import Tilemap, Tileset
    from pygame_engine.tilemap.layer import TileLayer

    tileset = Tileset.from_file(Path("assets/tiles.png"), tile_w=16, tile_h=16)
    ground  = TileLayer("ground",    [[0, 1, 0], [2, 0, 2]])
    walls   = TileLayer("collision", [[-1, 3, -1], [3, 3, 3]])
    tmap    = Tilemap(tileset, tile_w=16, tile_h=16, layers=[ground, walls])

    tmap.set_collision_layer("collision")
    tmap.render(surface, camera)

    if tmap.collides_rect(player.rect):
        resolve_collision()
"""

from pygame_engine.tilemap.layer import TileLayer
from pygame_engine.tilemap.tilemap import Tilemap
from pygame_engine.tilemap.tileset import Tileset

__all__ = ["Tilemap", "Tileset", "TileLayer"]
