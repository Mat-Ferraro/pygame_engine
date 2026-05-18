"""
A Tilemap holds one or more TileLayers rendered in order (bottom to top).
Each layer is a 2D grid of integers where:
  -1 (or any negative) = empty cell (transparent, nothing drawn)
   0+ = tile index into the associated Tileset

Usage::

    from pygame_engine.tilemap.layer import TileLayer

    layer = TileLayer("ground", grid=[[0, 1, 2], [3, -1, 3]])
"""

from __future__ import annotations


class TileLayer:
    """
    A named 2D grid of tile indices.

    Args:
        name:    Layer name (e.g. "ground", "decoration", "collision").
        grid:    2D list of tile indices. grid[row][col]. All rows must be
                 the same length. Negative values mean empty.
        visible: Whether this layer is rendered. Default True.
    """

    def __init__(
        self,
        name:    str,
        grid:    list[list[int]],
        visible: bool = True,
    ) -> None:
        if not grid or not grid[0]:
            raise ValueError("TileLayer grid must not be empty.")
        row_len = len(grid[0])
        for i, row in enumerate(grid):
            if len(row) != row_len:
                raise ValueError(
                    f"TileLayer row {i} has {len(row)} columns, expected {row_len}."
                )
        self._name    = name
        self._grid    = [list(row) for row in grid]   # defensive copy
        self._rows    = len(grid)
        self._cols    = row_len
        self.visible  = visible

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Return the name of this tile layer."""
        return self._name

    @property
    def rows(self) -> int:
        """Return the number of tile rows in this layer."""
        return self._rows

    @property
    def cols(self) -> int:
        """Return the number of tile columns in this layer."""
        return self._cols

    # ── Tile access ───────────────────────────────────────────────────────────

    def get(self, col: int, row: int) -> int:
        """
        Return the tile index at (col, row). Returns -1 if out of bounds.

        Args:
            col: Column (x tile coordinate).
            row: Row (y tile coordinate).
        """
        if row < 0 or row >= self._rows or col < 0 or col >= self._cols:
            return -1
        return self._grid[row][col]

    def set(self, col: int, row: int, index: int) -> None:
        """
        Set the tile index at (col, row).

        Args:
            col:   Column (x tile coordinate).
            row:   Row (y tile coordinate).
            index: New tile index. Use -1 for empty.

        Raises:
            IndexError: If (col, row) is out of bounds.
        """
        if row < 0 or row >= self._rows or col < 0 or col >= self._cols:
            raise IndexError(f"Tile position ({col}, {row}) out of bounds.")
        self._grid[row][col] = index

    def fill(self, index: int) -> None:
        """Fill the entire layer with one tile index."""
        for row in self._grid:
            for c in range(len(row)):
                row[c] = index

    def __repr__(self) -> str:
        return f"TileLayer({self._name!r}, {self._cols}×{self._rows})"