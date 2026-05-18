"""
Usage::

    from pygame_engine.tilemap import Tilemap, Tileset
    from pygame_engine.tilemap.layer import TileLayer
    from pygame_engine.camera import Camera

    tileset = Tileset.from_file(Path("assets/tiles.png"), 16, 16)
    ground  = TileLayer("ground",    [[0,1,0],[2,0,2]])
    walls   = TileLayer("collision", [[-1,3,-1],[3,3,3]])
    tmap    = Tilemap(tileset, tile_w=16, tile_h=16, layers=[ground, walls])

    # Render with camera culling:
    tmap.render(surface, camera)

    # Collision:
    tmap.set_collision_layer("collision")
    if tmap.collides_rect(player.rect):
        ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from pygame_engine.tilemap.layer import TileLayer
from pygame_engine.tilemap.tileset import Tileset

if TYPE_CHECKING:
    from pygame_engine.camera import Camera


class Tilemap:
    """
    A 2D tile map with layered rendering and collision support.

    Coordinate conventions
    ----------------------
    - Tile coordinates: (col, row) integers
    - World coordinates: pixels, origin at top-left of the map
    - The map's world origin can be offset with ``world_offset``

    Collision model
    ---------------
    One layer is designated the collision layer. Any tile with index >= 0
    (non-empty) in that layer is treated as solid. Use ``collides_rect()``
    for AABB collision against the tile grid.

    Camera culling
    --------------
    ``render()`` accepts an optional Camera. When provided, only tiles
    that overlap the visible viewport are drawn — critical for large maps.

    Args:
        tileset:      The Tileset used for all layers.
        tile_w:       Tile width in pixels.
        tile_h:       Tile height in pixels.
        layers:       Ordered list of TileLayers (bottom rendered first).
        world_offset: Top-left world position of the map. Default (0, 0).
    """

    def __init__(
        self,
        tileset:      Tileset,
        tile_w:       int,
        tile_h:       int,
        layers:       list[TileLayer] | None = None,
        world_offset: tuple[int, int] = (0, 0),
    ) -> None:
        self._tileset      = tileset
        self._tile_w       = tile_w
        self._tile_h       = tile_h
        self._layers:      list[TileLayer] = list(layers) if layers else []
        self._world_offset = world_offset
        self._collision_layer: str | None = None

        # Validate all layers have consistent size
        if self._layers:
            rows = self._layers[0].rows
            cols = self._layers[0].cols
            for layer in self._layers[1:]:
                if layer.rows != rows or layer.cols != cols:
                    raise ValueError(
                        f"Layer '{layer.name}' size ({layer.cols}×{layer.rows}) "
                        f"does not match first layer ({cols}×{rows})."
                    )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def tile_w(self) -> int:
        """Return the width of a single tile in pixels."""
        return self._tile_w

    @property
    def tile_h(self) -> int:
        """Return the height of a single tile in pixels."""
        return self._tile_h

    @property
    def cols(self) -> int:
        """Width of the map in tiles."""
        return self._layers[0].cols if self._layers else 0

    @property
    def rows(self) -> int:
        """Height of the map in tiles."""
        return self._layers[0].rows if self._layers else 0

    @property
    def pixel_width(self) -> int:
        """Total map width in pixels."""
        return self.cols * self._tile_w

    @property
    def pixel_height(self) -> int:
        """Total map height in pixels."""
        return self.rows * self._tile_h

    @property
    def world_rect(self) -> pygame.Rect:
        """Bounding rect of the full map in world space."""
        ox, oy = self._world_offset
        return pygame.Rect(ox, oy, self.pixel_width, self.pixel_height)

    @property
    def world_offset(self) -> tuple[int, int]:
        """Return the world-space offset of the tilemap origin."""
        return self._world_offset

    @world_offset.setter
    def world_offset(self, offset: tuple[int, int]) -> None:
        """Return the world-space offset of the tilemap origin."""
        self._world_offset = offset

    @property
    def tileset(self) -> Tileset:
        """Return the Tileset used by this tilemap."""
        return self._tileset

    # ── Layer management ──────────────────────────────────────────────────────

    def add_layer(self, layer: TileLayer) -> None:
        """Append a layer on top of the existing stack."""
        if self._layers:
            if layer.rows != self.rows or layer.cols != self.cols:
                raise ValueError(
                    f"Layer '{layer.name}' size ({layer.cols}×{layer.rows}) "
                    f"does not match map size ({self.cols}×{self.rows})."
                )
        self._layers.append(layer)

    def get_layer(self, name: str) -> TileLayer:
        """
        Return the layer with the given name.

        Raises:
            KeyError: If no layer with that name exists.
        """
        for layer in self._layers:
            if layer.name == name:
                return layer
        raise KeyError(f"No layer named {name!r}.")

    @property
    def layer_names(self) -> list[str]:
        """Return a list of all layer names in draw order."""
        return [layer.name for layer in self._layers]

    def set_collision_layer(self, name: str) -> None:
        """
        Designate a layer as the collision layer.

        Any non-empty tile (index >= 0) in this layer is treated as solid.

        Args:
            name: Name of the layer to use for collision.

        Raises:
            KeyError: If no layer with that name exists.
        """
        self.get_layer(name)   # validates existence
        self._collision_layer = name

    # ── Coordinate helpers ────────────────────────────────────────────────────

    def world_to_tile(self, world_x: float, world_y: float) -> tuple[int, int]:
        """
        Convert a world position to tile coordinates (col, row).

        Args:
            world_x: X position in world pixels.
            world_y: Y position in world pixels.

        Returns:
            (col, row) tile coordinate. May be outside map bounds.
        """
        ox, oy = self._world_offset
        col = int((world_x - ox) // self._tile_w)
        row = int((world_y - oy) // self._tile_h)
        return (col, row)

    def tile_to_world(self, col: int, row: int) -> tuple[int, int]:
        """
        Convert tile coordinates to the top-left world position of that tile.

        Args:
            col: Tile column.
            row: Tile row.

        Returns:
            (x, y) world pixel position of the tile's top-left corner.
        """
        ox, oy = self._world_offset
        return (ox + col * self._tile_w, oy + row * self._tile_h)

    def tile_rect(self, col: int, row: int) -> pygame.Rect:
        """Return the world-space rect for a tile at (col, row)."""
        x, y = self.tile_to_world(col, row)
        return pygame.Rect(x, y, self._tile_w, self._tile_h)

    def get_tile_at_world(
        self, world_x: float, world_y: float, layer_name: str
    ) -> int:
        """
        Return the tile index at a world position on a named layer.

        Returns -1 if the position is outside the map or the cell is empty.

        Args:
            world_x:    X position in world pixels.
            world_y:    Y position in world pixels.
            layer_name: Which layer to query.
        """
        col, row = self.world_to_tile(world_x, world_y)
        return self.get_layer(layer_name).get(col, row)

    # ── Collision ─────────────────────────────────────────────────────────────

    def collides_rect(self, rect: pygame.Rect) -> bool:
        """
        Return True if ``rect`` overlaps any solid tile in the collision layer.

        A tile is solid if its index is >= 0 (non-empty).
        Returns False if no collision layer has been set.

        Args:
            rect: World-space rect to test (e.g. player.rect).
        """
        if self._collision_layer is None:
            return False
        layer = self.get_layer(self._collision_layer)
        ox, oy = self._world_offset

        # Tile range that could overlap rect
        col_min = max(0, int((rect.left   - ox) // self._tile_w))
        col_max = min(self.cols - 1, int((rect.right  - ox - 1) // self._tile_w))
        row_min = max(0, int((rect.top    - oy) // self._tile_h))
        row_max = min(self.rows - 1, int((rect.bottom - oy - 1) // self._tile_h))

        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):
                if layer.get(col, row) >= 0:
                    if rect.colliderect(self.tile_rect(col, row)):
                        return True
        return False

    def get_colliding_tiles(self, rect: pygame.Rect) -> list[pygame.Rect]:
        """
        Return world-space rects of all solid tiles overlapping ``rect``.

        Useful for resolving collision responses.

        Args:
            rect: World-space rect to test.
        """
        if self._collision_layer is None:
            return []
        layer = self.get_layer(self._collision_layer)
        ox, oy = self._world_offset
        result: list[pygame.Rect] = []

        col_min = max(0, int((rect.left   - ox) // self._tile_w))
        col_max = min(self.cols - 1, int((rect.right  - ox - 1) // self._tile_w))
        row_min = max(0, int((rect.top    - oy) // self._tile_h))
        row_max = min(self.rows - 1, int((rect.bottom - oy - 1) // self._tile_h))

        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):
                if layer.get(col, row) >= 0:
                    tr = self.tile_rect(col, row)
                    if rect.colliderect(tr):
                        result.append(tr)
        return result

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(
        self,
        surface: pygame.Surface,
        camera:  "Camera | None" = None,
    ) -> None:
        """
        Render all visible layers to ``surface``.

        With a Camera, only tiles in the visible viewport are drawn.
        Without a Camera, all tiles are drawn (fine for small maps).

        Args:
            surface: Target surface to draw onto.
            camera:  Optional Camera for coordinate conversion and culling.
        """
        for layer in self._layers:
            if layer.visible:
                self._render_layer(surface, layer, camera)

    def render_layer(
        self,
        surface:    pygame.Surface,
        layer_name: str,
        camera:     "Camera | None" = None,
    ) -> None:
        """
        Render a single named layer.

        Args:
            surface:    Target surface.
            layer_name: Which layer to render.
            camera:     Optional Camera.
        """
        self._render_layer(surface, self.get_layer(layer_name), camera)

    def _render_layer(
        self,
        surface: pygame.Surface,
        layer:   TileLayer,
        camera:  "Camera | None",
    ) -> None:
        ox, oy = self._world_offset

        if camera is not None:
            # Compute visible tile range from camera viewport
            vp_w, vp_h = camera.viewport_size
            top_left     = camera.screen_to_world((0, 0))
            bottom_right = camera.screen_to_world((vp_w, vp_h))

            col_min = max(0, int((top_left[0]     - ox) // self._tile_w))
            col_max = min(layer.cols - 1, int((bottom_right[0] - ox) // self._tile_w) + 1)
            row_min = max(0, int((top_left[1]     - oy) // self._tile_h))
            row_max = min(layer.rows - 1, int((bottom_right[1] - oy) // self._tile_h) + 1)
        else:
            col_min, col_max = 0, layer.cols - 1
            row_min, row_max = 0, layer.rows - 1

        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):
                tile_idx = layer.get(col, row)
                surf = self._tileset.get(tile_idx)
                if surf is None:
                    continue   # empty tile

                world_x = ox + col * self._tile_w
                world_y = oy + row * self._tile_h

                if camera is not None:
                    sx, sy = camera.world_to_screen((world_x, world_y))
                    # Apply zoom to tile size
                    z = camera.zoom
                    if z != 1.0:
                        tw = max(1, int(self._tile_w * z))
                        th = max(1, int(self._tile_h * z))
                        surf = pygame.transform.scale(surf, (tw, th))
                else:
                    sx, sy = world_x, world_y

                surface.blit(surf, (sx, sy))

    # ── Repr ──────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (f"Tilemap({self.cols}×{self.rows} tiles, "
                f"{self._tile_w}×{self._tile_h}px, "
                f"{len(self._layers)} layers)")