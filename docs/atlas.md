## Purpose

Pack many small surfaces into one large surface to reduce blit overhead.
Useful for UI icon sets, tile variants, and particle frames rendered
many times per frame.

---

## Quick start

```python
from pygame_engine.atlas import AtlasPacker, SpriteAtlas

packer = AtlasPacker(max_size=2048)
packer.add("player", player_surf).add("coin", coin_surf)
atlas  = packer.build()

atlas.blit(screen, "player", dest=(x, y))
atlas.blit(screen, "coin",   dest=(cx, cy))

# Save/load
packer.save(Path("assets/ui.atlas.png"), Path("assets/ui.atlas.json"))
atlas = SpriteAtlas.load(Path("assets/ui.atlas.png"),
                         Path("assets/ui.atlas.json"))

# Via AssetLoader
atlas = app.assets.atlas("ui.atlas.png", "ui.atlas.json")
```

---

## AtlasPacker

```python
packer = AtlasPacker(max_size=2048, padding=1)
packer.add("name", surface)   # chainable; raises ValueError if too large
atlas  = packer.build()
packer.save(img_path, meta_path)   # build + save PNG + JSON metadata
packer.count   # registered surface count
packer.clear()
```

Raises `ValueError` if surfaces won't fit within `max_size`.

---

## SpriteAtlas

```python
atlas.blit(surface, "name", dest=(x, y))   # fast path
atlas.get_rect("name")                      # pygame.Rect (copy)
atlas.get_surface("name")                   # new Surface (allocates)
atlas.has("name")
atlas.names    # sorted list
atlas.count
atlas.size     # (width, height)
```

## When to use

Useful when rendering many small sprites each frame (icon grids, tile
sets, particle systems). For large or infrequently blitted images,
direct asset loading is simpler and sufficient.