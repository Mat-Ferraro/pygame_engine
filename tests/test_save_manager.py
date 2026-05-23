"""
Dedicated tests for pygame_engine.persistence.save_manager.SaveManager.

test_persistence.py already covers the full integration round-trip.
This file covers SaveManager-specific internals and edge cases:
  - Envelope field names and structure
  - game_id mismatch raises ValueError
  - load_payload() convenience wrapper
  - list_slots() ordering (most-recent first) and payload exclusion
  - Corrupt slot files skipped gracefully in list_slots()
  - save_dir property
  - Overwriting a slot preserves created_at
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pygame_engine.persistence.save_manager import SaveManager


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_manager(tmp_path: Path, game_id: str = "test_game",
                 version: int = 1) -> SaveManager:
    return SaveManager(
        save_dir=tmp_path / "saves",
        game_id=game_id,
        current_version=version,
    )


# ── Envelope structure ────────────────────────────────────────────────────────

def test_envelope_contains_required_fields(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {"gold": 100})
    env = sm.load("s1")
    for field in ("save_version", "game_id", "slot_id", "created_at",
                  "updated_at", "payload"):
        assert field in env, f"Missing envelope field: {field}"


def test_envelope_game_id_matches(tmp_path: Path) -> None:
    sm = make_manager(tmp_path, game_id="mygame")
    sm.save("s1", {})
    env = sm.load("s1")
    assert env["game_id"] == "mygame"


def test_envelope_slot_id_matches(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("hero_save", {"x": 10})
    env = sm.load("hero_save")
    assert env["slot_id"] == "hero_save"


def test_envelope_save_version_matches_current(tmp_path: Path) -> None:
    sm = make_manager(tmp_path, version=3)
    sm.save("s1", {})
    env = sm.load("s1")
    assert env["save_version"] == 3


def test_envelope_payload_matches(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {"level": 5, "hp": 80})
    env = sm.load("s1")
    assert env["payload"] == {"level": 5, "hp": 80}


def test_envelope_created_at_is_string(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {})
    env = sm.load("s1")
    assert isinstance(env["created_at"], str)
    assert len(env["created_at"]) > 0


def test_envelope_updated_at_is_string(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {})
    env = sm.load("s1")
    assert isinstance(env["updated_at"], str)


# ── Overwrite preserves created_at ────────────────────────────────────────────

def test_overwrite_preserves_created_at(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {"x": 1})
    first_env = sm.load("s1")
    created = first_env["created_at"]

    sm.save("s1", {"x": 2})
    second_env = sm.load("s1")
    assert second_env["created_at"] == created


def test_overwrite_updates_payload(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {"x": 1})
    sm.save("s1", {"x": 99})
    assert sm.load("s1")["payload"] == {"x": 99}


# ── game_id validation ────────────────────────────────────────────────────────

def test_load_wrong_game_id_raises(tmp_path: Path) -> None:
    """Loading a save from a different game raises ValueError."""
    sm_a = make_manager(tmp_path, game_id="game_a")
    sm_b = make_manager(tmp_path, game_id="game_b")

    sm_a.save("s1", {"x": 1})

    with pytest.raises(ValueError, match="game_a"):
        sm_b.load("s1")


def test_load_empty_game_id_in_file_does_not_raise(tmp_path: Path) -> None:
    """Old saves without game_id are loaded without validation."""
    sm = make_manager(tmp_path, game_id="mygame")
    # Write a save file with no game_id field
    slot_path = tmp_path / "saves" / "s1.json"
    slot_path.parent.mkdir(parents=True, exist_ok=True)
    slot_path.write_text(
        json.dumps({
            "save_version": 1,
            "slot_id": "s1",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "payload": {"legacy": True},
        }),
        encoding="utf-8",
    )
    env = sm.load("s1")   # should not raise
    assert env["payload"]["legacy"] is True


# ── load_payload() ────────────────────────────────────────────────────────────

def test_load_payload_returns_only_payload(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {"score": 42})
    payload = sm.load_payload("s1")
    assert payload == {"score": 42}
    # Should NOT contain envelope keys
    assert "save_version" not in payload
    assert "game_id" not in payload


def test_load_payload_missing_slot_raises(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    from pygame_engine.persistence.storage import SaveNotFoundError
    with pytest.raises(SaveNotFoundError):
        sm.load_payload("nonexistent")


# ── list_slots() ─────────────────────────────────────────────────────────────

def test_list_slots_most_recent_first(tmp_path: Path) -> None:
    """list_slots() returns slots sorted by updated_at descending.

    Timestamps use isoformat with second precision, so we patch _timestamp
    to return distinct values instead of relying on time.sleep().
    """
    from unittest.mock import patch
    sm = make_manager(tmp_path)

    timestamps = iter(["2025-01-01T10:00:00", "2025-01-01T10:00:01"])
    with patch.object(sm, "_timestamp", side_effect=lambda: next(timestamps)):
        sm.save("slot_a", {"n": 1})   # gets 10:00:00
        sm.save("slot_b", {"n": 2})   # gets 10:00:01

    slots = sm.list_slots()
    ids = [s["slot_id"] for s in slots]
    # slot_b has later timestamp — should appear first
    assert ids.index("slot_b") < ids.index("slot_a")


def test_list_slots_does_not_include_payload(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {"secret": "data"})
    slots = sm.list_slots()
    assert len(slots) == 1
    assert "payload" not in slots[0]
    assert "secret" not in slots[0]


def test_list_slots_includes_metadata_fields(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {})
    slot = sm.list_slots()[0]
    for field in ("slot_id", "save_version", "game_id", "created_at", "updated_at"):
        assert field in slot


def test_list_slots_empty_when_no_saves(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    assert sm.list_slots() == []


def test_list_slots_skips_corrupt_files(tmp_path: Path) -> None:
    """Corrupt save files are skipped silently in list_slots()."""
    sm = make_manager(tmp_path)
    sm.save("good", {"x": 1})

    # Write a corrupt file directly
    corrupt = tmp_path / "saves" / "corrupt.json"
    corrupt.write_text("{this is not json", encoding="utf-8")

    slots = sm.list_slots()
    ids = [s["slot_id"] for s in slots]
    assert "good" in ids
    assert "corrupt" not in ids


# ── exists() and delete() ─────────────────────────────────────────────────────

def test_exists_false_before_save(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    assert sm.exists("new_slot") is False


def test_exists_true_after_save(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {})
    assert sm.exists("s1") is True


def test_delete_returns_true_when_slot_existed(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {})
    assert sm.delete("s1") is True


def test_delete_returns_false_when_slot_missing(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    assert sm.delete("nonexistent") is False


def test_delete_removes_slot(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    sm.save("s1", {})
    sm.delete("s1")
    assert sm.exists("s1") is False


# ── save_dir property ─────────────────────────────────────────────────────────

def test_save_dir_property_returns_configured_path(tmp_path: Path) -> None:
    expected = tmp_path / "my_saves"
    sm = SaveManager(save_dir=expected, game_id="g", current_version=1)
    assert sm.save_dir == expected


def test_save_dir_created_on_first_save(tmp_path: Path) -> None:
    sm = make_manager(tmp_path)
    assert not (tmp_path / "saves").exists()
    sm.save("s1", {})
    assert (tmp_path / "saves").exists()
