# Tilemap System

## Purpose

Provides 2D tile map rendering and collision for games with grid-based
worlds — platformers, RPGs, top-down adventures, puzzle games.

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

# 1. Load tileset from a spritesheet
tileset = Tileset.from_file(Path("assets/images/tiles.png"), tile_w=16, tile_h=16)

# 2. Define layers as 2D grids of tile indices (-1 = empty)
ground = TileLayer("ground", [
    [0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1],
])
walls = TileLayer("collision", [
    [-1, -1, 3, -1, -1],
    [ 3,  3, 3,  3,  3],
])

# 3. Create the map
tmap = Tilemap(tileset, tile_w=16, tile_h=16, layers=[ground, walls])
tmap.set_collision_layer("collision")

# 4. Render each frame (camera-culled)
camera = Camera(1280, 720)
tmap.render(surface, camera)

# 5. Collision check
if tmap.collides_rect(player.rect):
    resolve_collision(player, tmap.get_colliding_tiles(player.rect))
```

---

## Tileset

Immutable. Load once, share across maps.

```python
# From file (most common)
tileset = Tileset.from_file(Path("assets/tiles.png"), tile_w=16, tile_h=16)

# From an already-loaded surface
tileset = Tileset.from_surface(sheet_surface, tile_w=16, tile_h=16)

# With margin and spacing (e.g. Tiled-exported sheets)
tileset = Tileset.from_file(path, 16, 16, margin=1, spacing=1)

# Access tiles directly
surf = tileset.get(5)   # tile index 5
print(tileset.count)    # total tiles
```

Tiles are indexed left-to-right, top-to-bottom from 0. Index -1 (or
any negative value) means "empty" — `get()` returns `None`.

---

## TileLayer

A named 2D grid. `grid[row][col]`.

```python
layer = TileLayer("ground", [
    [0, 1, 0, 1],
    [2, 0, 2, 0],
])

# Access
layer.get(col=1, row=0)   # → 1
layer.get(99, 0)          # out of bounds → -1 (safe)

# Modify
layer.set(0, 0, 5)
layer.fill(-1)            # clear entire layer

# Properties
layer.name     # "ground"
layer.cols     # 4
layer.rows     # 2
layer.visible  # True/False — controls rendering
```

---

## Tilemap

```python
tmap = Tilemap(
    tileset,
    tile_w=16,
    tile_h=16,
    layers=[ground, walls, decoration],
    world_offset=(0, 0),   # top-left world position of the map
)
```

### Layer management

```python
tmap.add_layer(new_layer)
layer = tmap.get_layer("ground")
print(tmap.layer_names)   # ["ground", "collision", "decoration"]
```

### Coordinate conversion

```python
# Tile → world pixel (top-left of tile)
x, y = tmap.tile_to_world(col=3, row=2)

# World pixel → tile
col, row = tmap.world_to_tile(world_x=48.5, world_y=32.0)

# World-space rect for a specific tile
rect = tmap.tile_rect(col=3, row=2)

# Tile index at a world position on a named layer
index = tmap.get_tile_at_world(world_x, world_y, "ground")
```

### Collision

```python
tmap.set_collision_layer("collision")

# Boolean test — any solid tile overlaps rect?
if tmap.collides_rect(player.rect):
    ...

# Get all colliding tile rects for response
tiles = tmap.get_colliding_tiles(player.rect)
for tile_rect in tiles:
    resolve_overlap(player, tile_rect)
```

A tile is **solid** if its index is >= 0 (non-empty) in the collision layer.

### Rendering

```python
# Render all visible layers (camera-culled)
tmap.render(surface, camera)

# Render without camera (all tiles, fine for small maps)
tmap.render(surface)

# Render a single named layer
tmap.render_layer(surface, "decoration", camera)
```

### Map dimensions

```python
tmap.cols          # width in tiles
tmap.rows          # height in tiles
tmap.pixel_width   # width in pixels
tmap.pixel_height  # height in pixels
tmap.world_rect    # pygame.Rect covering the full map in world space
```

---

## Patterns

### Platformer scene setup

```python
def on_enter(self):
    screen = self._app.screen_rect
    self._camera = Camera(screen.width, screen.height)
    self._camera.set_world_bounds(self._tmap.world_rect)
    self._camera.move_to(self._player.rect.center)

def update(self, dt):
    self._player.update(dt, self._tmap)
    self._camera.follow(self._player.rect.center, speed=6, dt=dt)
    self._camera.update(dt)

def render(self, surface):
    surface.fill((30, 30, 46))
    self._tmap.render(surface, self._camera)
    # render entities using camera.world_rect_to_screen(...)
    super().render(surface)
```

### Simple collision resolution

```python
def update(self, dt, tmap):
    self.rect.x += int(self.velocity_x * dt)
    for tile in tmap.get_colliding_tiles(self.rect):
        if self.velocity_x > 0:
            self.rect.right = tile.left
        elif self.velocity_x < 0:
            self.rect.left = tile.right
        self.velocity_x = 0

    self.rect.y += int(self.velocity_y * dt)
    for tile in tmap.get_colliding_tiles(self.rect):
        if self.velocity_y > 0:
            self.rect.bottom = tile.top
            self.on_ground = True
        elif self.velocity_y < 0:
            self.rect.top = tile.bottom
        self.velocity_y = 0
```

### Building a map from code

```python
import random

cols, rows = 30, 20
ground_grid = [[-1] * cols for _ in range(rows)]

# Solid floor on bottom two rows
for row in range(rows - 2, rows):
    for col in range(cols):
        ground_grid[row][col] = 1

# Random platforms
for _ in range(10):
    c = random.randint(1, cols - 4)
    r = random.randint(rows // 2, rows - 4)
    for dc in range(3):
        ground_grid[r][c + dc] = 1

layer = TileLayer("ground", ground_grid)
```

---

## Accepted decisions

### Negative tile index means empty
Any negative index (conventionally -1) means "no tile here". `Tileset.get()`
returns `None` for negative indices, and the renderer skips them. This
matches the Tiled editor convention.

### Collision layer is opt-in
No layer is a collision layer by default. Games call `set_collision_layer()`
with the name of whichever layer holds solid tiles. Decouples visual layers
from collision data — games often use a separate invisible collision layer.

### Camera culling uses screen_to_world
The renderer computes the visible tile range by converting the viewport
corners to world space using `camera.screen_to_world()`. This correctly
accounts for zoom and shake offset.

### No built-in Tiled .tmx loader
The core tilemap system has no external dependencies. `.tmx` loading via
`pytmx` is deferred until a real game needs it. The `TileLayer` grid format
is compatible with how Tiled exports data — adding a loader later is
straightforward.
