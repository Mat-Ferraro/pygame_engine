# Pathfinding

## Purpose

Grid-based A* pathfinding for any game with navigable tile worlds —
top-down RPGs, strategy games, tower defence, puzzle games.

Two classes:

- **`ObstacleGrid`** — 2D boolean grid of walkable/blocked cells
- **`Pathfinder`** — A* search on an ObstacleGrid

---

## Quick start

```python
from pygame_engine.pathfinding import ObstacleGrid, Pathfinder

# Build from a Tilemap collision layer
grid   = ObstacleGrid.from_tilemap(tmap, collision_layer="walls")
finder = Pathfinder(grid, diagonal=True)

# Find a path (returns list of (col, row) tuples)
path = finder.find(start=(2, 3), goal=(15, 10))
# → [(2,3), (3,4), (4,5), ..., (15,10)]  or [] if no path

# Convert to world positions for entity movement
waypoints = [tmap.tile_to_world(col, row) for col, row in path]
```

---

## ObstacleGrid

```python
# Build manually
grid = ObstacleGrid(cols=40, rows=20)
grid.set_obstacle(5, 3, True)    # block a cell
grid.set_obstacle(5, 3, False)   # unblock a cell
grid.fill(True)                  # fill entire grid
grid.is_blocked(5, 3)            # True/False (also True if out of bounds)

# Build from Tilemap
grid = ObstacleGrid.from_tilemap(tmap, collision_layer="collision")
# Any tile with index >= 0 in the named layer is treated as blocked
```

---

## Pathfinder

```python
finder = Pathfinder(grid, diagonal=False)   # 4-directional (default)
finder = Pathfinder(grid, diagonal=True)    # 8-directional with corner prevention

path = finder.find((0, 0), (19, 14))
# Returns [] if: start/goal is blocked, or no path exists

finder.diagonal = True   # change mode at runtime
finder.set_grid(new_grid)
```

### Return value

`find()` returns a `list[tuple[int, int]]` — tile coordinates from start
to goal **inclusive**. Returns `[]` if no path found.

---

## Movement pattern

```python
class Enemy:
    def __init__(self):
        self._path:     list[tuple[int,int]] = []
        self._waypoint: tuple[int,int] | None = None

    def set_target(self, finder, tmap, goal_tile):
        start = tmap.world_to_tile(*self.rect.center)
        self._path = finder.find(start, goal_tile)
        self._next_waypoint(tmap)

    def _next_waypoint(self, tmap):
        if self._path:
            col, row = self._path.pop(0)
            wx, wy   = tmap.tile_to_world(col, row)
            self._waypoint = (wx + tmap.tile_w//2, wy + tmap.tile_h//2)

    def update(self, dt, tmap):
        if self._waypoint:
            dx = self._waypoint[0] - self.rect.centerx
            dy = self._waypoint[1] - self.rect.centery
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 4:
                self._next_waypoint(tmap)
            else:
                speed = 120 * dt
                self.rect.x += int(dx / dist * speed)
                self.rect.y += int(dy / dist * speed)
```

---

## Performance notes

A* performance scales with grid size and path length. For large maps
(100×100+) with many enemies, consider:

- Caching paths and only recalculating when the target moves significantly
- Running pathfinding every N frames rather than every frame
- Using a smaller grid (one cell per 2 tiles) for coarser navigation

For small maps (40×30 typical tilemap), live recalculation per enemy per
second is fine.

---

## Accepted decisions

### Tile coordinates, not pixel coordinates
`find()` works in tile space, not world pixels. Convert with
`tmap.tile_to_world()` and `tmap.world_to_tile()`.

### Out-of-bounds cells are blocked
`is_blocked(col, row)` returns True for any position outside the grid.
This means the pathfinder naturally can't route through the edges.

### Corner cutting is prevented in diagonal mode
When diagonal movement is enabled, a diagonal step is only allowed if
both adjacent cardinal cells are walkable. This prevents moving through
the gap between two diagonal walls.
