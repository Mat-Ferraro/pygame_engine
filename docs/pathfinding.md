## Purpose

Grid-based A* pathfinding for top-down games, strategy games, and any
game with navigable tile worlds.

---

## Quick start

```python
from pygame_engine.pathfinding import ObstacleGrid, Pathfinder

grid   = ObstacleGrid.from_tilemap(tmap, collision_layer="walls")
finder = Pathfinder(grid, diagonal=True)
path   = finder.find((2, 3), (15, 10))
# → [(2,3), (3,4), ..., (15,10)]  or [] if no path

waypoints = [tmap.tile_to_world(c, r) for c, r in path]
```

---

## ObstacleGrid

```python
grid = ObstacleGrid(cols=40, rows=20)
grid.set_obstacle(5, 3, True)
grid.is_blocked(5, 3)   # True; also True for out-of-bounds
grid.fill(False)

grid = ObstacleGrid.from_tilemap(tmap, collision_layer="collision")
# Any tile with index >= 0 in the named layer is blocked
```

---

## Pathfinder

```python
finder = Pathfinder(grid, diagonal=False)   # 4-directional (default)
finder = Pathfinder(grid, diagonal=True)    # 8-directional, no corner-cutting

path = finder.find(start=(0,0), goal=(19,14))
# [] if start/goal is blocked or no path exists

finder.diagonal = True
finder.set_grid(new_grid)
```

---

## Movement pattern

```python
class Enemy:
    def set_target(self, finder, tmap, goal_tile):
        start      = tmap.world_to_tile(*self.rect.center)
        self._path = finder.find(start, goal_tile)

    def update(self, dt, tmap):
        if self._path:
            col, row = self._path[0]
            wx, wy   = tmap.tile_to_world(col, row)
            tx = wx + tmap.tile_w // 2
            ty = wy + tmap.tile_h // 2
            dx, dy = tx - self.rect.centerx, ty - self.rect.centery
            dist   = math.sqrt(dx*dx + dy*dy)
            if dist < 4:
                self._path.pop(0)
            else:
                speed = 120 * dt
                self.rect.x += int(dx / dist * speed)
                self.rect.y += int(dy / dist * speed)
```

---

## Notes

- Works in tile coordinates — convert with `tmap.tile_to_world()`.
- Out-of-bounds cells are always blocked.
- Diagonal mode prevents cutting through corner gaps.
- For large maps with many enemies, cache paths and recalculate only when the target moves significantly.