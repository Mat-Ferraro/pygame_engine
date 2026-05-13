# Sprite Atlas

## Purpose

Pack many small surfaces into one large surface to reduce blit overhead
when rendering large numbers of sprites.

- **`AtlasPacker`** — builds an atlas from named surfaces using shelf packing
- **`SpriteAtlas`** — the built atlas; blit named sprites from it

---

## Quick start

```python
from pygame_engine.atlas import AtlasPacker, SpriteAtlas

# Build at startup
packer = AtlasPacker(max_size=2048)
packer.add("player_idle", idle_surf)
packer.add("player_run",  run_surf)
packer.add("coin",        coin_surf)
atlas = packer.build()

# In render loop
atlas.blit(screen, "player_idle", dest=(100, 200))

# Save/load (offline build step)
packer.save(Path("assets/images/ui.atlas.png"),
            Path("assets/images/ui.atlas.json"))
atlas = SpriteAtlas.load(Path("assets/images/ui.atlas.png"),
                         Path("assets/images/ui.atlas.json"))

# Via AssetLoader
atlas = app.assets.atlas("ui.atlas.png", "ui.atlas.json")
```

---

## AtlasPacker

```python
packer = AtlasPacker(max_size=2048, padding=1)
packer.add("name", surface)   # chainable
atlas = packer.build()        # pack and return SpriteAtlas
packer.save(img_path, meta_path)   # build + save PNG + JSON
packer.clear()
packer.count    # number of registered surfaces
```

Raises `ValueError` if a surface exceeds `max_size` or all surfaces
don't fit in the atlas.

---

## SpriteAtlas

```python
atlas.blit(surface, "name", dest=(x, y))     # fast — direct blit
atlas.get_rect("name")                        # pygame.Rect within atlas
atlas.get_surface("name")                     # new Surface (allocates)
atlas.has("name")                             # bool
atlas.names                                   # sorted list
atlas.count                                   # number of sprites
atlas.size                                    # (width, height) of atlas
```

## When to use

Use an atlas when you have many small sprites (UI icons, tile variants,
particle frames) that are rendered frequently each frame. For large sprites
or infrequently used images, direct loading is fine.

Build atlases offline as part of a build step; load them at game startup.
