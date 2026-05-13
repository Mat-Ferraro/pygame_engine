"""
Tileset — slices a spritesheet into individual tile surfaces.

A Tileset is immutable once created. Load it once and share it across
as many Tilemaps as needed.

Usage::

    from pygame_engine.tilemap import Tileset

    tileset = Tileset.from_surface(sheet_surface, tile_w=16, tile_h=16)
    # or load directly:
    tileset = Tileset.from_file(Path("assets/images/tiles.png"), 16, 16)
"""

from __future__ import annotations

from pathlib import Path

import pygame


class Tileset:
    """
    A sliced spritesheet of tile images.

    Tiles are indexed left-to-right, top-to-bottom starting at 0.
    Index 0 is conventionally the first tile in the top-left corner.
    Tile index -1 (or any negative) is treated as "empty" — transparent.

    Args:
        surfaces: Ordered list of tile surfaces (index 0 = first tile).
        tile_w:   Width of each tile in pixels.
        tile_h:   Height of each tile in pixels.
    """

    def __init__(
        self,
        surfaces: list[pygame.Surface],
        tile_w:   int,
        tile_h:   int,
    ) -> None:
        if not surfaces:
            raise ValueError("Tileset requires at least one tile surface.")
        self._surfaces = list(surfaces)
        self._tile_w   = tile_w
        self._tile_h   = tile_h

    # ── Factory methods ───────────────────────────────────────────────────────

    @classmethod
    def from_surface(
        cls,
        sheet:  pygame.Surface,
        tile_w: int,
        tile_h: int,
        margin: int = 0,
        spacing: int = 0,
    ) -> "Tileset":
        """
        Slice a pygame Surface into tile surfaces.

        Args:
            sheet:   The full spritesheet surface.
            tile_w:  Width of each tile in pixels.
            tile_h:  Height of each tile in pixels.
            margin:  Pixels of empty border around the whole sheet.
            spacing: Pixels of gap between adjacent tiles.

        Returns:
            A new Tileset.
        """
        surfaces: list[pygame.Surface] = []
        cols = (sheet.get_width()  - margin * 2 + spacing) // (tile_w + spacing)
        rows = (sheet.get_height() - margin * 2 + spacing) // (tile_h + spacing)

        for row in range(rows):
            for col in range(cols):
                x = margin + col * (tile_w + spacing)
                y = margin + row * (tile_h + spacing)
                surf = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
                surf.blit(sheet, (0, 0), pygame.Rect(x, y, tile_w, tile_h))
                surfaces.append(surf)

        if not surfaces:
            raise ValueError(
                f"No tiles extracted — sheet {sheet.get_size()} is too small "
                f"for tile size ({tile_w}×{tile_h})."
            )
        return cls(surfaces, tile_w, tile_h)

    @classmethod
    def from_file(
        cls,
        path:    Path,
        tile_w:  int,
        tile_h:  int,
        margin:  int = 0,
        spacing: int = 0,
    ) -> "Tileset":
        """
        Load a tileset image from disk and slice it.

        Args:
            path:    Path to the image file.
            tile_w:  Width of each tile in pixels.
            tile_h:  Height of each tile in pixels.
            margin:  Pixels of empty border around the whole sheet.
            spacing: Pixels of gap between adjacent tiles.
        """
        sheet = pygame.image.load(str(path)).convert_alpha()
        return cls.from_surface(sheet, tile_w, tile_h, margin, spacing)

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def tile_w(self) -> int:
        return self._tile_w

    @property
    def tile_h(self) -> int:
        return self._tile_h

    @property
    def count(self) -> int:
        """Total number of tiles in this tileset."""
        return len(self._surfaces)

    def get(self, index: int) -> pygame.Surface | None:
        """
        Return the surface for tile ``index``, or None if index < 0.

        Args:
            index: Tile index. Negative values mean "empty/transparent".

        Raises:
            IndexError: If index >= count.
        """
        if index < 0:
            return None
        if index >= len(self._surfaces):
            raise IndexError(
                f"Tile index {index} out of range (tileset has {len(self._surfaces)} tiles)."
            )
        return self._surfaces[index]

    def __len__(self) -> int:
        return self._tile_w

    def __repr__(self) -> str:
        return (f"Tileset({len(self._surfaces)} tiles, "
                f"{self._tile_w}×{self._tile_h}px)")
