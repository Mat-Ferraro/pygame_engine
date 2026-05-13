"""
pygame_engine.atlas

Sprite atlas packing for efficient rendering of many small sprites.

Public API::

    from pygame_engine.atlas import AtlasPacker, SpriteAtlas

    # Build at startup
    packer = AtlasPacker(max_size=2048)
    packer.add("player", player_surf).add("coin", coin_surf)
    atlas = packer.build()

    # Blit in render loop (fast — one surface)
    atlas.blit(screen, "player", dest=(x, y))

    # Save/load for offline build step
    packer.save(Path("assets/ui.atlas.png"), Path("assets/ui.atlas.json"))
    atlas = SpriteAtlas.load(Path("assets/ui.atlas.png"),
                             Path("assets/ui.atlas.json"))
"""

from pygame_engine.atlas.atlas import AtlasPacker, SpriteAtlas

__all__ = ["AtlasPacker", "SpriteAtlas"]
