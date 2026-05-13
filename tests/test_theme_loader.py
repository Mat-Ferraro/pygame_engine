"""tests/test_theme_loader.py — Theme file loading and serialisation."""

import json
import pytest

from pygame_engine.theme.defaults import DEFAULT_THEME, Theme
from pygame_engine.theme.loader import (
    reload_theme_file,
    theme_from_file,
    theme_to_dict,
)
from pygame_engine.theme.runtime import get_theme, reset_theme, set_theme


# ── theme_from_file ───────────────────────────────────────────────────────────

def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        theme_from_file(tmp_path / "nope.json")


def test_load_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        theme_from_file(p)


def test_load_empty_object_returns_default_theme(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text("{}", encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.colours.bg_base == DEFAULT_THEME.colours.bg_base


def test_load_colour_override(tmp_path):
    data = {"colours": {"bg_base": [10, 20, 30]}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.colours.bg_base == (10, 20, 30)


def test_load_does_not_mutate_default_theme(tmp_path):
    original = DEFAULT_THEME.colours.bg_base
    data = {"colours": {"bg_base": [1, 2, 3]}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme_from_file(p)
    assert DEFAULT_THEME.colours.bg_base == original


def test_load_typography_family(tmp_path):
    data = {"typography": {"family": "consolas,monospace"}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.typography.family == "consolas,monospace"


def test_load_typography_size(tmp_path):
    data = {"typography": {"md": 22}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.typography.md == 22


def test_load_spacing(tmp_path):
    data = {"spacing": {"xl": 32}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.spacing.xl == 32


def test_load_button_normal_bg(tmp_path):
    data = {"button": {"normal": {"bg": [60, 90, 180]}}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.button.normal.bg == (60, 90, 180)


def test_load_button_radius(tmp_path):
    data = {"button": {"normal": {"radius": 10}}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.button.normal.radius == 10


def test_load_button_padding(tmp_path):
    data = {"button": {"padding": 14}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.button.padding == 14


def test_load_panel_surface(tmp_path):
    data = {"panel": {"surface": {"bg": [30, 34, 50]}}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    assert theme.panel.surface.bg == (30, 34, 50)


def test_load_partial_override_preserves_other_keys(tmp_path):
    data = {"colours": {"bg_base": [1, 2, 3]}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    theme = theme_from_file(p)
    # text colour should be unchanged
    assert theme.colours.text == DEFAULT_THEME.colours.text


def test_load_returns_theme_instance(tmp_path):
    p = tmp_path / "t.json"
    p.write_text("{}", encoding="utf-8")
    assert isinstance(theme_from_file(p), Theme)


# ── reload_theme_file ─────────────────────────────────────────────────────────

def test_reload_activates_theme(tmp_path):
    data = {"colours": {"bg_base": [99, 88, 77]}}
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    try:
        reload_theme_file(p)
        assert get_theme().colours.bg_base == (99, 88, 77)
    finally:
        reset_theme()


def test_reload_returns_theme(tmp_path):
    p = tmp_path / "t.json"
    p.write_text("{}", encoding="utf-8")
    try:
        result = reload_theme_file(p)
        assert isinstance(result, Theme)
    finally:
        reset_theme()


# ── theme_to_dict ─────────────────────────────────────────────────────────────

def test_to_dict_contains_top_level_keys():
    d = theme_to_dict(DEFAULT_THEME)
    for key in ("colours", "typography", "spacing", "button", "label", "panel"):
        assert key in d


def test_to_dict_colours_are_lists():
    d = theme_to_dict(DEFAULT_THEME)
    for val in d["colours"].values():
        assert isinstance(val, list)
        assert len(val) == 3


def test_to_dict_roundtrip(tmp_path):
    """Save default theme, load it back, values should match."""
    d  = theme_to_dict(DEFAULT_THEME)
    p  = tmp_path / "rt.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    t2 = theme_from_file(p)
    assert t2.colours.bg_base   == DEFAULT_THEME.colours.bg_base
    assert t2.typography.md     == DEFAULT_THEME.typography.md
    assert t2.button.normal.bg  == DEFAULT_THEME.button.normal.bg
    assert t2.spacing.xl        == DEFAULT_THEME.spacing.xl
