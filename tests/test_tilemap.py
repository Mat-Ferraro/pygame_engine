"""
tests/test_tilemap.py

Tests for pygame_engine.tilemap: Tileset, TileLayer, Tilemap.
"""

import pygame
import pytest

from pygame_engine.camera import Camera
from pygame_engine.tilemap import TileLayer, Tilemap, Tileset


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_tileset(tile_w=16, tile_h=16, count=8) -> Tileset:
    """Create a Tileset from plain colour surfaces."""
    surfaces = []
    for i in range(count):
        s = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
        s.fill((i * 30 % 256, 100, 150))
        surfaces.append(s)
    return Tileset(surfaces, tile_w, tile_h)


GRID_3x2 = [[0, 1, 2], [3, -1, 3]]   # 3 cols, 2 rows
GRID_SOLID = [[1, 1, 1], [1, 1, 1]]


# ══════════════════════════════════════════════════════════════════════════════
# Tileset
# ══════════════════════════════════════════════════════════════════════════════

def test_tileset_count() -> None:
    ts = make_tileset(count=8)
    assert ts.count == 8


def test_tileset_tile_dimensions() -> None:
    ts = make_tileset(tile_w=32, tile_h=16)
    assert ts.tile_w == 32
    assert ts.tile_h == 16


def test_tileset_get_valid_index() -> None:
    ts = make_tileset(count=4)
    surf = ts.get(0)
    assert isinstance(surf, pygame.Surface)


def test_tileset_get_negative_returns_none() -> None:
    ts = make_tileset()
    assert ts.get(-1) is None


def test_tileset_get_out_of_range_raises() -> None:
    ts = make_tileset(count=4)
    with pytest.raises(IndexError):
        ts.get(4)


def test_tileset_empty_raises() -> None:
    with pytest.raises(ValueError):
        Tileset([], 16, 16)


def test_tileset_from_surface() -> None:
    sheet = pygame.Surface((64, 32), pygame.SRCALPHA)
    ts = Tileset.from_surface(sheet, tile_w=16, tile_h=16)
    assert ts.count == 8   # 4 cols × 2 rows


def test_tileset_from_surface_with_spacing() -> None:
    # 2 tiles wide with 2px spacing: 16 + 2 + 16 = 34px wide, plus margin
    sheet = pygame.Surface((34, 16), pygame.SRCALPHA)
    ts = Tileset.from_surface(sheet, tile_w=16, tile_h=16, spacing=2)
    assert ts.count == 2


def test_tileset_from_surface_too_small_raises() -> None:
    sheet = pygame.Surface((4, 4), pygame.SRCALPHA)
    with pytest.raises(ValueError):
        Tileset.from_surface(sheet, tile_w=16, tile_h=16)


def test_tileset_repr() -> None:
    ts = make_tileset(count=4)
    assert "Tileset" in repr(ts)
    assert "4" in repr(ts)


# ══════════════════════════════════════════════════════════════════════════════
# TileLayer
# ══════════════════════════════════════════════════════════════════════════════

def test_layer_dimensions() -> None:
    layer = TileLayer("ground", GRID_3x2)
    assert layer.cols == 3
    assert layer.rows == 2


def test_layer_name() -> None:
    assert TileLayer("bg", GRID_3x2).name == "bg"


def test_layer_get_valid() -> None:
    layer = TileLayer("g", GRID_3x2)
    assert layer.get(0, 0) == 0
    assert layer.get(1, 0) == 1
    assert layer.get(1, 1) == -1   # empty cell


def test_layer_get_out_of_bounds_returns_minus_one() -> None:
    layer = TileLayer("g", GRID_3x2)
    assert layer.get(-1, 0)  == -1
    assert layer.get(99, 0)  == -1
    assert layer.get(0, -1)  == -1
    assert layer.get(0, 99)  == -1


def test_layer_set_updates_value() -> None:
    layer = TileLayer("g", [[0, 1], [2, 3]])
    layer.set(0, 0, 99)
    assert layer.get(0, 0) == 99


def test_layer_set_out_of_bounds_raises() -> None:
    layer = TileLayer("g", GRID_3x2)
    with pytest.raises(IndexError):
        layer.set(99, 0, 0)


def test_layer_fill() -> None:
    layer = TileLayer("g", GRID_3x2)
    layer.fill(7)
    for row in range(layer.rows):
        for col in range(layer.cols):
            assert layer.get(col, row) == 7


def test_layer_empty_grid_raises() -> None:
    with pytest.raises(ValueError):
        TileLayer("g", [])


def test_layer_ragged_grid_raises() -> None:
    with pytest.raises(ValueError):
        TileLayer("g", [[0, 1], [0]])


def test_layer_grid_is_copied() -> None:
    original = [[0, 1], [2, 3]]
    layer = TileLayer("g", original)
    original[0][0] = 99
    assert layer.get(0, 0) == 0   # original mutation doesn't affect layer


def test_layer_visible_default_true() -> None:
    assert TileLayer("g", GRID_3x2).visible is True


def test_layer_repr() -> None:
    assert "TileLayer" in repr(TileLayer("ground", GRID_3x2))


# ══════════════════════════════════════════════════════════════════════════════
# Tilemap
# ══════════════════════════════════════════════════════════════════════════════

def make_map(rows=4, cols=6, tile_size=16) -> Tilemap:
    ts    = make_tileset(tile_w=tile_size, tile_h=tile_size)
    grid  = [[0] * cols for _ in range(rows)]
    layer = TileLayer("ground", grid)
    return Tilemap(ts, tile_w=tile_size, tile_h=tile_size, layers=[layer])


# ── Construction ──────────────────────────────────────────────────────────────

def test_tilemap_dimensions() -> None:
    tmap = make_map(rows=4, cols=6)
    assert tmap.rows == 4
    assert tmap.cols == 6


def test_tilemap_pixel_size() -> None:
    tmap = make_map(rows=4, cols=6, tile_size=16)
    assert tmap.pixel_width  == 96
    assert tmap.pixel_height == 64


def test_tilemap_world_rect() -> None:
    tmap = make_map(rows=2, cols=3, tile_size=16)
    r = tmap.world_rect
    assert r.width  == 48
    assert r.height == 32


def test_tilemap_mismatched_layer_sizes_raises() -> None:
    ts = make_tileset()
    l1 = TileLayer("a", [[0, 1]])
    l2 = TileLayer("b", [[0, 1, 2]])
    with pytest.raises(ValueError):
        Tilemap(ts, 16, 16, layers=[l1, l2])


# ── Layer management ──────────────────────────────────────────────────────────

def test_add_layer() -> None:
    tmap = make_map()
    deco = TileLayer("deco", [[0]*6]*4)
    tmap.add_layer(deco)
    assert "deco" in tmap.layer_names


def test_get_layer_by_name() -> None:
    tmap = make_map()
    layer = tmap.get_layer("ground")
    assert layer.name == "ground"


def test_get_layer_missing_raises() -> None:
    tmap = make_map()
    with pytest.raises(KeyError):
        tmap.get_layer("nonexistent")


def test_add_wrong_size_layer_raises() -> None:
    tmap = make_map(rows=4, cols=6)
    bad  = TileLayer("bad", [[0]*3]*4)   # wrong col count
    with pytest.raises(ValueError):
        tmap.add_layer(bad)


# ── Coordinate conversion ─────────────────────────────────────────────────────

def test_world_to_tile() -> None:
    tmap = make_map(tile_size=16)
    assert tmap.world_to_tile(0,  0 ) == (0, 0)
    assert tmap.world_to_tile(16, 0 ) == (1, 0)
    assert tmap.world_to_tile(0,  16) == (0, 1)
    assert tmap.world_to_tile(31, 31) == (1, 1)


def test_tile_to_world() -> None:
    tmap = make_map(tile_size=16)
    assert tmap.tile_to_world(0, 0) == (0,  0 )
    assert tmap.tile_to_world(1, 0) == (16, 0 )
    assert tmap.tile_to_world(0, 2) == (0,  32)


def test_world_offset_shifts_coordinates() -> None:
    ts    = make_tileset()
    layer = TileLayer("g", [[0]*4]*4)
    tmap  = Tilemap(ts, 16, 16, layers=[layer], world_offset=(100, 50))
    col, row = tmap.world_to_tile(100, 50)
    assert col == 0
    assert row == 0


def test_tile_rect_correct_position() -> None:
    tmap = make_map(tile_size=16)
    r = tmap.tile_rect(2, 1)
    assert r.x == 32
    assert r.y == 16
    assert r.width  == 16
    assert r.height == 16


def test_get_tile_at_world() -> None:
    ts    = make_tileset()
    layer = TileLayer("g", [[5, 3], [1, 2]])
    tmap  = Tilemap(ts, 16, 16, layers=[layer])
    assert tmap.get_tile_at_world(0,  0,  "g") == 5
    assert tmap.get_tile_at_world(16, 0,  "g") == 3
    assert tmap.get_tile_at_world(0,  16, "g") == 1


# ── Collision ─────────────────────────────────────────────────────────────────

def test_no_collision_without_collision_layer() -> None:
    tmap = make_map()
    rect = pygame.Rect(0, 0, 16, 16)
    assert tmap.collides_rect(rect) is False


def test_collision_with_solid_tile() -> None:
    ts     = make_tileset()
    solid  = TileLayer("walls", [[1, 1], [1, 1]])
    tmap   = Tilemap(ts, 16, 16, layers=[solid])
    tmap.set_collision_layer("walls")
    rect   = pygame.Rect(0, 0, 16, 16)
    assert tmap.collides_rect(rect) is True


def test_no_collision_with_empty_tile() -> None:
    ts     = make_tileset()
    layer  = TileLayer("walls", [[-1, -1], [-1, -1]])
    tmap   = Tilemap(ts, 16, 16, layers=[layer])
    tmap.set_collision_layer("walls")
    rect   = pygame.Rect(0, 0, 16, 16)
    assert tmap.collides_rect(rect) is False


def test_no_collision_outside_map() -> None:
    ts    = make_tileset()
    layer = TileLayer("walls", [[1, 1], [1, 1]])
    tmap  = Tilemap(ts, 16, 16, layers=[layer])
    tmap.set_collision_layer("walls")
    rect  = pygame.Rect(500, 500, 16, 16)
    assert tmap.collides_rect(rect) is False


def test_get_colliding_tiles_returns_rects() -> None:
    ts    = make_tileset()
    layer = TileLayer("walls", [[1, -1], [-1, -1]])
    tmap  = Tilemap(ts, 16, 16, layers=[layer])
    tmap.set_collision_layer("walls")
    rect  = pygame.Rect(0, 0, 32, 32)
    tiles = tmap.get_colliding_tiles(rect)
    assert len(tiles) == 1
    assert tiles[0] == pygame.Rect(0, 0, 16, 16)


def test_get_colliding_tiles_empty_without_collision_layer() -> None:
    tmap = make_map()
    assert tmap.get_colliding_tiles(pygame.Rect(0, 0, 100, 100)) == []


def test_set_collision_layer_missing_raises() -> None:
    tmap = make_map()
    with pytest.raises(KeyError):
        tmap.set_collision_layer("nonexistent")


# ── Rendering ─────────────────────────────────────────────────────────────────

def test_render_without_camera_does_not_raise(display_surface) -> None:
    make_map().render(display_surface)


def test_render_with_camera_does_not_raise(display_surface) -> None:
    cam  = Camera(800, 600)
    cam.move_to((0, 0))
    make_map(rows=10, cols=10).render(display_surface, cam)


def test_render_invisible_layer_skipped(display_surface) -> None:
    ts    = make_tileset()
    layer = TileLayer("g", [[0]*4]*4)
    layer.visible = False
    tmap  = Tilemap(ts, 16, 16, layers=[layer])
    tmap.render(display_surface)   # should not raise


def test_render_named_layer(display_surface) -> None:
    ts   = make_tileset()
    l1   = TileLayer("ground", [[0]*4]*4)
    l2   = TileLayer("deco",   [[1]*4]*4)
    tmap = Tilemap(ts, 16, 16, layers=[l1, l2])
    tmap.render_layer(display_surface, "deco")   # single layer


# ── Repr ──────────────────────────────────────────────────────────────────────

def test_tilemap_repr() -> None:
    tmap = make_map(rows=4, cols=6)
    r    = repr(tmap)
    assert "Tilemap" in r
    assert "6" in r
    assert "4" in r
