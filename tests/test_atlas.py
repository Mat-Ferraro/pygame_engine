"""
tests/test_atlas.py — SpriteAtlas and AtlasPacker tests.
"""

import json
import tempfile
from pathlib import Path

import pygame
import pytest

from pygame_engine.atlas import AtlasPacker, SpriteAtlas


def make_surf(w=32, h=32, colour=(255, 0, 0, 255)) -> pygame.Surface:
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(colour)
    return s


# ── AtlasPacker ───────────────────────────────────────────────────────────────

def test_packer_empty_build_returns_atlas() -> None:
    packer = AtlasPacker()
    atlas  = packer.build()
    assert isinstance(atlas, SpriteAtlas)
    assert atlas.count == 0


def test_packer_single_sprite() -> None:
    packer = AtlasPacker()
    packer.add("hero", make_surf(32, 32))
    atlas = packer.build()
    assert atlas.count == 1
    assert atlas.has("hero")


def test_packer_multiple_sprites() -> None:
    packer = AtlasPacker()
    packer.add("a", make_surf(16, 16))
    packer.add("b", make_surf(32, 32))
    packer.add("c", make_surf(24, 24))
    atlas = packer.build()
    assert atlas.count == 3


def test_packer_regions_within_atlas_bounds() -> None:
    packer = AtlasPacker(max_size=256)
    packer.add("a", make_surf(32, 32))
    packer.add("b", make_surf(64, 16))
    atlas = packer.build()
    w, h  = atlas.size
    for name in atlas.names:
        r = atlas.get_rect(name)
        assert r.x >= 0 and r.y >= 0
        assert r.right  <= w
        assert r.bottom <= h


def test_packer_oversized_sprite_raises() -> None:
    packer = AtlasPacker(max_size=64)
    with pytest.raises(ValueError, match="exceeds atlas max_size"):
        packer.add("big", make_surf(128, 128))


def test_packer_too_many_sprites_raises() -> None:
    packer = AtlasPacker(max_size=32, padding=0)
    # Fill with sprites that definitely won't fit
    for i in range(200):
        packer.add(f"s{i}", make_surf(16, 16))
    with pytest.raises(ValueError, match="do not fit"):
        packer.build()


def test_packer_chaining() -> None:
    packer = AtlasPacker()
    result = packer.add("a", make_surf()).add("b", make_surf())
    assert result is packer
    assert packer.count == 2


def test_packer_clear() -> None:
    packer = AtlasPacker()
    packer.add("a", make_surf())
    packer.clear()
    assert packer.count == 0


def test_packer_save_and_load(tmp_path) -> None:
    packer = AtlasPacker()
    packer.add("hero", make_surf(32, 32, (200, 100, 50, 255)))
    packer.add("coin", make_surf(16, 16, (255, 215, 0, 255)))

    img  = tmp_path / "test.atlas.png"
    meta = tmp_path / "test.atlas.json"
    packer.save(img, meta)

    assert img.exists()
    assert meta.exists()

    loaded = SpriteAtlas.load(img, meta)
    assert loaded.count == 2
    assert loaded.has("hero")
    assert loaded.has("coin")


def test_packer_save_metadata_format(tmp_path) -> None:
    packer = AtlasPacker()
    packer.add("tile", make_surf(16, 16))
    img  = tmp_path / "t.png"
    meta = tmp_path / "t.json"
    packer.save(img, meta)

    data = json.loads(meta.read_text())
    assert "size" in data
    assert "regions" in data
    assert "tile" in data["regions"]
    r = data["regions"]["tile"]
    assert all(k in r for k in ("x", "y", "w", "h"))


# ── SpriteAtlas ───────────────────────────────────────────────────────────────

def make_atlas(*names) -> SpriteAtlas:
    packer = AtlasPacker()
    for name in names:
        packer.add(name, make_surf(32, 32))
    return packer.build()


def test_atlas_has_returns_true_for_known() -> None:
    atlas = make_atlas("hero", "coin")
    assert atlas.has("hero") is True
    assert atlas.has("coin") is True


def test_atlas_has_returns_false_for_unknown() -> None:
    atlas = make_atlas("hero")
    assert atlas.has("ghost") is False


def test_atlas_get_rect_returns_rect() -> None:
    atlas = make_atlas("hero")
    r = atlas.get_rect("hero")
    assert isinstance(r, pygame.Rect)
    assert r.width == 32
    assert r.height == 32


def test_atlas_get_rect_unknown_raises() -> None:
    atlas = make_atlas("hero")
    with pytest.raises(KeyError):
        atlas.get_rect("ghost")


def test_atlas_get_surface_correct_size() -> None:
    atlas = make_atlas("hero")
    surf  = atlas.get_surface("hero")
    assert surf.get_width()  == 32
    assert surf.get_height() == 32


def test_atlas_blit_does_not_raise(display_surface) -> None:
    atlas = make_atlas("hero")
    atlas.blit(display_surface, "hero", (10, 10))


def test_atlas_blit_unknown_raises(display_surface) -> None:
    atlas = make_atlas("hero")
    with pytest.raises(KeyError):
        atlas.blit(display_surface, "ghost", (0, 0))


def test_atlas_names_sorted() -> None:
    atlas = make_atlas("zebra", "apple", "mango")
    assert atlas.names == ["apple", "mango", "zebra"]


def test_atlas_count() -> None:
    assert make_atlas("a", "b", "c").count == 3


def test_atlas_size_within_max() -> None:
    packer = AtlasPacker(max_size=512)
    for i in range(10):
        packer.add(f"s{i}", make_surf(32, 32))
    atlas = packer.build()
    w, h  = atlas.size
    assert w <= 512
    assert h <= 512


def test_atlas_from_surfaces() -> None:
    surfs = {
        "hero": make_surf(32, 32),
        "coin": make_surf(16, 16),
    }
    atlas = SpriteAtlas.from_surfaces(surfs)
    assert atlas.count == 2
    assert atlas.has("hero")
    assert atlas.has("coin")


def test_atlas_load_missing_file_raises(tmp_path) -> None:
    with pytest.raises(Exception):
        SpriteAtlas.load(tmp_path / "nope.png", tmp_path / "nope.json")


def test_atlas_repr() -> None:
    atlas = make_atlas("hero")
    assert "SpriteAtlas" in repr(atlas)
    assert "1" in repr(atlas)


def test_atlas_get_rect_returns_copy() -> None:
    """Modifying the returned rect must not affect the atlas."""
    atlas = make_atlas("hero")
    r1 = atlas.get_rect("hero")
    r1.x = 9999
    r2 = atlas.get_rect("hero")
    assert r2.x != 9999
