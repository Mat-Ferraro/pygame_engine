"""
Grid-based A* pathfinding for pygame_engine.

Finds the shortest walkable path between two tile positions on a grid.
Supports 4-directional and 8-directional (diagonal) movement.
Integrates naturally with the Tilemap system.

Usage::

    from pygame_engine.pathfinding import Pathfinder, ObstacleGrid

    # Build from a Tilemap collision layer
    grid = ObstacleGrid.from_tilemap(tmap, collision_layer="walls")

    # Or build manually
    grid = ObstacleGrid(cols=40, rows=20)
    grid.set_obstacle(5, 3, True)

    finder = Pathfinder(grid)
    path = finder.find((0, 0), (10, 8))   # list of (col, row) tuples, or []
"""

from __future__ import annotations

import heapq
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.tilemap import Tilemap


class ObstacleGrid:
    """
    A 2D boolean grid of walkable/blocked cells.

    Cells are addressed as (col, row). ``True`` = blocked, ``False`` = walkable.

    Args:
        cols: Width of the grid in cells.
        rows: Height of the grid in cells.
    """

    def __init__(self, cols: int, rows: int) -> None:
        if cols <= 0 or rows <= 0:
            raise ValueError("Grid dimensions must be positive.")
        self._cols    = cols
        self._rows    = rows
        self._blocked = [[False] * cols for _ in range(rows)]

    # ── Factory methods ───────────────────────────────────────────────────────

    @classmethod
    def from_tilemap(
        cls,
        tilemap:         "Tilemap",
        collision_layer: str,
    ) -> "ObstacleGrid":
        """
        Build an ObstacleGrid from a Tilemap's collision layer.

        Any non-empty tile (index >= 0) in ``collision_layer`` is treated
        as blocked.

        Args:
            tilemap:         The Tilemap to read from.
            collision_layer: Name of the layer to use for obstacle data.

        Raises:
            KeyError: If the layer does not exist.
        """
        layer = tilemap.get_layer(collision_layer)
        grid  = cls(layer.cols, layer.rows)
        for row in range(layer.rows):
            for col in range(layer.cols):
                if layer.get(col, row) >= 0:
                    grid._blocked[row][col] = True
        return grid

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def rows(self) -> int:
        return self._rows

    def is_blocked(self, col: int, row: int) -> bool:
        """Return True if (col, row) is blocked or out of bounds."""
        if col < 0 or col >= self._cols or row < 0 or row >= self._rows:
            return True
        return self._blocked[row][col]

    def set_obstacle(self, col: int, row: int, blocked: bool) -> None:
        """
        Set the blocked state of a cell.

        Args:
            col:     Column index.
            row:     Row index.
            blocked: True = impassable, False = walkable.

        Raises:
            IndexError: If (col, row) is out of bounds.
        """
        if col < 0 or col >= self._cols or row < 0 or row >= self._rows:
            raise IndexError(f"Cell ({col}, {row}) out of bounds.")
        self._blocked[row][col] = blocked

    def fill(self, blocked: bool) -> None:
        """Set all cells to the same blocked state."""
        for row in range(self._rows):
            for col in range(self._cols):
                self._blocked[row][col] = blocked

    def __repr__(self) -> str:
        return f"ObstacleGrid({self._cols}×{self._rows})"


class Pathfinder:
    """
    A* pathfinder for an ObstacleGrid.

    Finds the shortest walkable path between two tile positions.

    Args:
        grid:      The obstacle grid to search.
        diagonal:  If True, allows 8-directional movement (includes diagonals).
                   Default False (4-directional only).
    """

    def __init__(self, grid: ObstacleGrid, diagonal: bool = False) -> None:
        self._grid     = grid
        self._diagonal = diagonal

    # ── Public API ────────────────────────────────────────────────────────────

    def find(
        self,
        start: tuple[int, int],
        goal:  tuple[int, int],
    ) -> list[tuple[int, int]]:
        """
        Find the shortest path from ``start`` to ``goal``.

        Args:
            start: (col, row) starting tile.
            goal:  (col, row) destination tile.

        Returns:
            List of (col, row) tuples from start to goal **inclusive**,
            or an empty list if no path exists or start/goal are blocked.
        """
        if self._grid.is_blocked(*start) or self._grid.is_blocked(*goal):
            return []
        if start == goal:
            return [start]

        open_heap: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_heap, (0.0, start))

        came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        g_score:   dict[tuple[int, int], float]                  = {start: 0.0}

        while open_heap:
            _, current = heapq.heappop(open_heap)

            if current == goal:
                return self._reconstruct(came_from, goal)

            for neighbour in self._neighbours(current):
                cost   = math.sqrt(2) if (
                    neighbour[0] != current[0] and neighbour[1] != current[1]
                ) else 1.0
                new_g  = g_score[current] + cost

                if neighbour not in g_score or new_g < g_score[neighbour]:
                    g_score[neighbour]  = new_g
                    f_score             = new_g + self._heuristic(neighbour, goal)
                    came_from[neighbour] = current
                    heapq.heappush(open_heap, (f_score, neighbour))

        return []   # no path found

    def set_grid(self, grid: ObstacleGrid) -> None:
        """Replace the obstacle grid."""
        self._grid = grid

    @property
    def diagonal(self) -> bool:
        return self._diagonal

    @diagonal.setter
    def diagonal(self, value: bool) -> None:
        self._diagonal = value

    # ── Internal ──────────────────────────────────────────────────────────────

    def _heuristic(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> float:
        """Octile distance heuristic (works for both 4-dir and 8-dir)."""
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        if self._diagonal:
            return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        return dx + dy

    def _neighbours(
        self, pos: tuple[int, int]
    ) -> list[tuple[int, int]]:
        col, row = pos
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        if self._diagonal:
            directions += [(-1, -1), (1, -1), (-1, 1), (1, 1)]

        result = []
        for dc, dr in directions:
            nc, nr = col + dc, row + dr
            if not self._grid.is_blocked(nc, nr):
                # For diagonals, check that both cardinal neighbours are clear
                # to prevent cutting corners
                if dc != 0 and dr != 0:
                    if self._grid.is_blocked(col + dc, row) or \
                       self._grid.is_blocked(col, row + dr):
                        continue
                result.append((nc, nr))
        return result

    def _reconstruct(
        self,
        came_from: dict[tuple[int, int], tuple[int, int] | None],
        current:   tuple[int, int],
    ) -> list[tuple[int, int]]:
        path = []
        node: tuple[int, int] | None = current
        while node is not None:
            path.append(node)
            node = came_from[node]
        path.reverse()
        return path

    def __repr__(self) -> str:
        return (f"Pathfinder(grid={self._grid}, "
                f"diagonal={self._diagonal})")
