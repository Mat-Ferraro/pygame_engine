"""
tests/test_editor_helpers.py

Unit tests for the pure helper functions introduced during editor
bring-up. These are logic-only — no imgui context, no GL, no live
windows — so they run fast and deterministically in CI.

Covered helpers
---------------
- editor.editor_app._ini_is_valid   — layout-file validation truth table
- editor.editor_app._resolve_dir    — imgui direction enum lookup
- editor.panels.inspector._snap     — grid-snap rounding

Deliberately NOT covered here: dock-layout building and texture upload.
Those require a live imgui context / GL surface and belong in (heavier,
optional) integration tests, not this unit pass.

Covers: ini validation accepts good files and rejects ones missing a
required window section or the docking block; grid snap rounds to the
nearest multiple including at .5 boundaries and for negative values;
direction resolution returns distinct ints for the four cardinals.
"""

from __future__ import annotations

from editor.editor_app import _ini_is_valid, _resolve_dir
from editor.panels.inspector import _snap


# ── _ini_is_valid ─────────────────────────────────────────────────────────────

_REQUIRED = ("Hierarchy", "Inspector", "Scene")


def _good_ini() -> str:
    """A minimal ini that should pass validation."""
    return (
        "[Window][Hierarchy]\nDockId=0x01,0\n\n"
        "[Window][Inspector]\nDockId=0x02,0\n\n"
        "[Window][Scene]\nDockId=0x03,0\n\n"
        "[Docking][Data]\nDockSpace ID=0xABCD Pos=0,0 Size=1600,900\n"
    )


def test_valid_ini_accepted() -> None:
    valid, reason = _ini_is_valid(_good_ini(), _REQUIRED)
    assert valid is True
    assert reason == ""


def test_ini_missing_scene_rejected() -> None:
    """The exact failure mode we hit: Scene absent from the ini."""
    text = (
        "[Window][Hierarchy]\n\n"
        "[Window][Inspector]\n\n"
        "[Docking][Data]\nDockSpace ID=0xABCD\n"
    )
    valid, reason = _ini_is_valid(text, _REQUIRED)
    assert valid is False
    assert "Scene" in reason


def test_ini_missing_multiple_windows_lists_all() -> None:
    text = "[Window][Hierarchy]\n\n[Docking][Data]\nDockSpace ID=0x1\n"
    valid, reason = _ini_is_valid(text, _REQUIRED)
    assert valid is False
    assert "Inspector" in reason
    assert "Scene" in reason


def test_ini_missing_docking_block_rejected() -> None:
    """All windows present but no docking data — still invalid, because
    the panels would render free-floating with no dock relationships."""
    text = (
        "[Window][Hierarchy]\n\n"
        "[Window][Inspector]\n\n"
        "[Window][Scene]\n\n"
    )
    valid, reason = _ini_is_valid(text, _REQUIRED)
    assert valid is False
    assert "Docking" in reason


def test_empty_ini_rejected() -> None:
    valid, reason = _ini_is_valid("", _REQUIRED)
    assert valid is False
    assert reason != ""


# ── _snap ─────────────────────────────────────────────────────────────────────

def test_snap_rounds_to_nearest_multiple() -> None:
    assert _snap(13, 8) == 16
    assert _snap(11, 8) == 8
    assert _snap(12, 8) == 16     # .5 rounds up via round-half logic*


def test_snap_exact_multiple_unchanged() -> None:
    assert _snap(16, 8) == 16
    assert _snap(0, 8) == 0


def test_snap_grid_of_one_is_identity() -> None:
    for v in (-3, 0, 5, 17):
        assert _snap(v, 1) == v


def test_snap_negative_values() -> None:
    assert _snap(-13, 8) == -16
    assert _snap(-3, 8) == 0      # -3/8 = -0.375 → rounds to 0


# *Note on the .5 case: Python's round() uses banker's rounding, so
# round(12/8) = round(1.5) = 2 (nearest even). _snap therefore maps 12→16.
# This test pins the actual behaviour so a future change to the rounding
# strategy is a deliberate, visible decision rather than a silent drift.


# ── _resolve_dir ──────────────────────────────────────────────────────────────

def test_resolve_dir_returns_int_for_each_cardinal() -> None:
    for d in ("left", "right", "up", "down"):
        value = _resolve_dir(d)
        assert isinstance(value, int)


def test_resolve_dir_distinguishes_directions() -> None:
    """The four cardinals must resolve to distinct values, or splits in
    different directions would collide."""
    values = {_resolve_dir(d) for d in ("left", "right", "up", "down")}
    assert len(values) == 4
