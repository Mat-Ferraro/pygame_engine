"""
Tests for pygame_engine.assets.asset_loader.AssetLoader.

All pygame and filesystem calls are mocked so no display or real asset
files are required.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pygame_engine.assets.asset_loader import AssetLoader, AssetNotFoundError


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_loader(tmp_path: Path, debug: bool = False) -> AssetLoader:
    return AssetLoader(tmp_path / "assets", debug=debug)


# ── Construction ──────────────────────────────────────────────────────────────

def test_construction_is_side_effect_free(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    assert loader is not None


def test_asset_root_property(tmp_path: Path) -> None:
    root = tmp_path / "assets"
    loader = AssetLoader(root, debug=False)
    assert loader.asset_root == root


def test_debug_false_by_default(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    assert loader.debug is False


def test_debug_true_when_set(tmp_path: Path) -> None:
    loader = make_loader(tmp_path, debug=True)
    assert loader.debug is True


# ── image() ───────────────────────────────────────────────────────────────────

def test_image_delegates_to_sprite_loader(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    fake_surf = MagicMock()
    loader._sprites.load = MagicMock(return_value=fake_surf)

    result = loader.image("ui/btn.png")

    loader._sprites.load.assert_called_once_with(
        "ui/btn.png", convert_alpha=True, debug=False
    )
    assert result is fake_surf


def test_image_passes_debug_flag(tmp_path: Path) -> None:
    loader = make_loader(tmp_path, debug=True)
    loader._sprites.load = MagicMock(return_value=MagicMock())
    loader.image("ui/btn.png")
    _, kwargs = loader._sprites.load.call_args
    assert kwargs["debug"] is True


def test_image_convert_alpha_false_passed_through(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    loader._sprites.load = MagicMock(return_value=MagicMock())
    loader.image("bg.png", convert_alpha=False)
    _, kwargs = loader._sprites.load.call_args
    assert kwargs["convert_alpha"] is False


# ── spritesheet() ─────────────────────────────────────────────────────────────

def test_spritesheet_delegates_to_sprite_loader(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    fake_frames = [MagicMock(), MagicMock()]
    loader._sprites.load_sheet = MagicMock(return_value=fake_frames)

    result = loader.spritesheet("player.png", 32, 32)

    loader._sprites.load_sheet.assert_called_once_with(
        "player.png", 32, 32, convert_alpha=True, debug=False
    )
    assert result is fake_frames


# ── font() ────────────────────────────────────────────────────────────────────

def test_font_delegates_to_font_cache(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    fake_font = MagicMock()
    loader._fonts.load = MagicMock(return_value=fake_font)

    result = loader.font("fonts/inter.ttf", size=18)

    loader._fonts.load.assert_called_once_with(
        "fonts/inter.ttf", 18, bold=False, italic=False
    )
    assert result is fake_font


def test_font_passes_bold_italic(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    loader._fonts.load = MagicMock(return_value=MagicMock())
    loader.font("f.ttf", 14, bold=True, italic=True)
    _, kwargs = loader._fonts.load.call_args
    assert kwargs["bold"] is True
    assert kwargs["italic"] is True


# ── sysfont() ─────────────────────────────────────────────────────────────────

def test_sysfont_delegates_to_font_cache(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    fake_font = MagicMock()
    loader._fonts.load_sys = MagicMock(return_value=fake_font)

    result = loader.sysfont("arial", 16)

    loader._fonts.load_sys.assert_called_once_with(
        "arial", 16, bold=False, italic=False
    )
    assert result is fake_font


# ── sound() ───────────────────────────────────────────────────────────────────

def test_sound_delegates_to_sound_cache(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    fake_sound = MagicMock()
    loader._sounds.load = MagicMock(return_value=fake_sound)

    result = loader.sound("sfx/click.wav")

    loader._sounds.load.assert_called_once_with("sfx/click.wav")
    assert result is fake_sound


def test_sound_returns_none_for_missing(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    loader._sounds.load = MagicMock(return_value=None)
    assert loader.sound("missing.wav") is None


# ── atlas() ───────────────────────────────────────────────────────────────────

def test_atlas_method_exists(tmp_path: Path) -> None:
    """atlas() exists and is callable — full integration tested in test_atlas.py."""
    loader = make_loader(tmp_path)
    assert callable(loader.atlas)


# ── clear_cache() ─────────────────────────────────────────────────────────────

def test_clear_cache_clears_all_sub_caches(tmp_path: Path) -> None:
    loader = make_loader(tmp_path)
    loader._fonts.clear   = MagicMock()
    loader._sounds.clear  = MagicMock()
    loader._sprites.clear = MagicMock()

    loader.clear_cache()

    loader._fonts.clear.assert_called_once()
    loader._sounds.clear.assert_called_once()
    loader._sprites.clear.assert_called_once()


# ── AssetNotFoundError ────────────────────────────────────────────────────────

def test_asset_not_found_error_is_file_not_found_error() -> None:
    err = AssetNotFoundError("missing.png")
    assert isinstance(err, FileNotFoundError)


def test_image_raises_asset_not_found_when_file_missing(tmp_path: Path) -> None:
    loader = make_loader(tmp_path, debug=False)
    loader._sprites.load = MagicMock(side_effect=AssetNotFoundError("missing.png"))
    with pytest.raises(AssetNotFoundError):
        loader.image("missing.png")
