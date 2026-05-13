## Purpose

2D tile map rendering and collision for grid-based worlds — platformers,
RPGs, top-down adventures, puzzle games.

Three classes work together:

- **`Tileset`** — slices a spritesheet into individual tile surfaces
- **`TileLayer`** — a named 2D grid of tile indices
- **`Tilemap`** — owns a Tileset and layers; handles rendering and collision

---

## Quick start

```python
from pathlib import Path
from pygame_engine.tilemap import Tilemap, Tileset, TileLayer
from pygame_engine.camera import Camera

tileset = Tileset.from_file(Path("assets/images/tiles.png"), tile_w=16, tile_h=16)

ground = TileLayer("ground", [
    [0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1],
])
walls = TileLayer("collision", [
    [-1, -1, 3, -1, -1],
    [ 3,  3, 3,  3,  3],
])

tmap = Tilemap(tileset, tile_w=16, tile_h=16, layers=[ground, walls])
tmap.set_collision_layer("collision")

camera = Camera(1280, 720)
tmap.render(surface, camera)

if tmap.collides_rect(player.rect):
    resolve_collision(player, tmap.get_colliding_tiles(player.rect))
```

---

## Tileset

```python
tileset = Tileset.from_file(Path("assets/tiles.png"), tile_w=16, tile_h=16)
tileset = Tileset.from_surface(sheet_surface, tile_w=16, tile_h=16)
tileset = Tileset.from_file(path, 16, 16, margin=1, spacing=1)

surf  = tileset.get(5)    # tile index 5 — None if negative
count = tileset.count     # total tiles
```

Tiles are indexed left-to-right, top-to-bottom from 0. Index -1 means empty.

---

## TileLayer

```python
layer = TileLayer("ground", [[0, 1, 0], [2, -1, 2]])

layer.get(col=1, row=0)   # → 1  (safe — returns -1 if out of bounds)
layer.set(0, 0, 5)
layer.fill(-1)            # clear entire layer

layer.name     # "ground"
layer.cols     # 3
layer.rows     # 2
layer.visible  # True/False
```

---

## Tilemap

```python
tmap = Tilemap(tileset, tile_w=16, tile_h=16,
               layers=[ground, walls], world_offset=(0, 0))
```

### Layer management

```python
tmap.add_layer(new_layer)
layer = tmap.get_layer("ground")
tmap.layer_names   # ["ground", "collision"]
```

### Coordinate conversion

```python
x, y     = tmap.tile_to_world(col=3, row=2)
col, row = tmap.world_to_tile(world_x=48.5, world_y=32.0)
rect     = tmap.tile_rect(col=3, row=2)
index    = tmap.get_tile_at_world(world_x, world_y, "ground")
```

### Collision

```python
tmap.set_collision_layer("collision")

if tmap.collides_rect(player.rect):
    for tile_rect in tmap.get_colliding_tiles(player.rect):
        resolve_overlap(player, tile_rect)
```

A tile is solid if its index is >= 0 in the collision layer.

### Rendering

```python
tmap.render(surface, camera)          # camera-culled
tmap.render(surface)                  # all tiles (small maps)
tmap.render_layer(surface, "deco", camera)
```

### Dimensions

```python
tmap.cols, tmap.rows       # tile dimensions
tmap.pixel_width, tmap.pixel_height
tmap.world_rect            # full map in world space
```

---

## Platformer pattern

```python
def on_enter(self):
    self._camera = Camera(app.screen_rect.width, app.screen_rect.height)
    self._camera.set_world_bounds(self._tmap.world_rect)
    self._camera.move_to(self._player.rect.center)

def update(self, dt):
    self._player.update(dt, self._tmap)
    self._camera.follow(self._player.rect.center, speed=6, dt=dt)
    self._camera.update(dt)

def render(self, surface):
    surface.fill((30, 30, 46))
    self._tmap.render(surface, self._camera)
    # render entities...
    super().render(surface)
```

## Simple collision resolution

```python
def update(self, dt, tmap):
    self.rect.x += int(self.vx * dt)
    for tile in tmap.get_colliding_tiles(self.rect):
        if self.vx > 0: self.rect.right = tile.left
        elif self.vx < 0: self.rect.left = tile.right
        self.vx = 0
    self.rect.y += int(self.vy * dt)
    for tile in tmap.get_colliding_tiles(self.rect):
        if self.vy > 0: self.rect.bottom = tile.top; self.on_ground = True
        elif self.vy < 0: self.rect.top = tile.bottom
        self.vy = 0
```