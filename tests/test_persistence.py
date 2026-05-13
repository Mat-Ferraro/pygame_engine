"""
tests/test_persistence.py

Tests for pygame_engine.persistence.

Covers: storage read/write/delete/list, serializers, migrations,
and SaveManager slot operations.

All file I/O uses pytest's tmp_path fixture — no real disk writes.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from pygame_engine.persistence.migrations import MigrationError, MigrationRunner
from pygame_engine.persistence.save_manager import SaveManager
from pygame_engine.persistence.serializers import (
    from_dict,
    safe_bool,
    safe_float,
    safe_int,
    to_dict,
)
from pygame_engine.persistence.storage import (
    CorruptSaveError,
    SaveNotFoundError,
    delete,
    exists,
    list_saves,
    read,
    write,
)


# ── storage ───────────────────────────────────────────────────────────────────

def test_write_and_read_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    data = {"save_version": 1, "payload": {"gold": 99}}
    write(path, data)
    result = read(path)
    assert result["payload"]["gold"] == 99


def test_read_raises_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SaveNotFoundError):
        read(tmp_path / "nonexistent.json")


def test_read_raises_on_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.json"
    path.write_text("this is not json", encoding="utf-8")
    with pytest.raises(CorruptSaveError):
        read(path)


def test_write_creates_backup(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    write(path, {"save_version": 1, "payload": {"v": 1}})
    write(path, {"save_version": 1, "payload": {"v": 2}})
    bak = path.with_suffix(".bak")
    assert bak.exists()
    bak_data = read(bak)
    assert bak_data["payload"]["v"] == 1


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "deep" / "save.json"
    write(path, {"save_version": 1})
    assert path.exists()


def test_exists_true_when_file_present(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    write(path, {"save_version": 1})
    assert exists(path) is True


def test_exists_false_when_file_missing(tmp_path: Path) -> None:
    assert exists(tmp_path / "missing.json") is False


def test_delete_removes_file(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    write(path, {"save_version": 1})
    result = delete(path)
    assert result is True
    assert not path.exists()


def test_delete_returns_false_when_missing(tmp_path: Path) -> None:
    assert delete(tmp_path / "missing.json") is False


def test_list_saves_returns_sorted_paths(tmp_path: Path) -> None:
    for name in ("c.json", "a.json", "b.json"):
        (tmp_path / name).write_text("{}", encoding="utf-8")
    result = list_saves(tmp_path)
    names = [p.name for p in result]
    assert names == ["a.json", "b.json", "c.json"]


def test_list_saves_empty_when_no_directory(tmp_path: Path) -> None:
    assert list_saves(tmp_path / "nonexistent") == []


# ── serializers ───────────────────────────────────────────────────────────────

@dataclasses.dataclass
class Settings:
    volume: float = 1.0
    fullscreen: bool = False
    name: str = "player"


def test_to_dict_produces_correct_keys() -> None:
    s = Settings(volume=0.8, fullscreen=True, name="hero")
    d = to_dict(s)
    assert d == {"volume": 0.8, "fullscreen": True, "name": "hero"}


def test_from_dict_reconstructs_dataclass() -> None:
    d = {"volume": 0.5, "fullscreen": False, "name": "test"}
    s = from_dict(Settings, d)
    assert s.volume == 0.5
    assert s.name == "test"


def test_from_dict_ignores_extra_keys() -> None:
    d = {"volume": 0.5, "fullscreen": False, "name": "x", "unknown": 99}
    s = from_dict(Settings, d)
    assert s.volume == 0.5


def test_to_dict_raises_on_non_dataclass() -> None:
    with pytest.raises(TypeError):
        to_dict({"not": "a dataclass"})


def test_to_dict_nested_dataclass() -> None:
    @dataclasses.dataclass
    class Outer:
        inner: Settings = dataclasses.field(
            default_factory=Settings)

    o = Outer(inner=Settings(volume=0.3))
    d = to_dict(o)
    assert isinstance(d["inner"], dict)
    assert d["inner"]["volume"] == 0.3


def test_safe_int_coerces_string() -> None:
    assert safe_int("42") == 42


def test_safe_int_returns_default_on_failure() -> None:
    assert safe_int("nope", default=7) == 7


def test_safe_float_coerces_string() -> None:
    assert abs(safe_float("3.14") - 3.14) < 1e-6


def test_safe_bool_handles_string_true() -> None:
    assert safe_bool("true") is True
    assert safe_bool("yes")  is True
    assert safe_bool("1")    is True


def test_safe_bool_handles_false() -> None:
    assert safe_bool("false") is False
    assert safe_bool(0)       is False


# ── migrations ────────────────────────────────────────────────────────────────

def test_migration_runner_applies_single_step() -> None:
    runner = MigrationRunner(current_version=2)

    @runner.register(from_version=1)
    def v1_to_v2(data):
        data["payload"]["new_field"] = "added"
        data["save_version"] = 2
        return data

    data = {"save_version": 1, "payload": {}}
    result = runner.run(data)
    assert result["save_version"] == 2
    assert result["payload"]["new_field"] == "added"


def test_migration_runner_chains_multiple_steps() -> None:
    runner = MigrationRunner(current_version=3)

    @runner.register(from_version=1)
    def v1_to_v2(data):
        data["payload"]["a"] = 1
        data["save_version"] = 2
        return data

    @runner.register(from_version=2)
    def v2_to_v3(data):
        data["payload"]["b"] = 2
        data["save_version"] = 3
        return data

    data   = {"save_version": 1, "payload": {}}
    result = runner.run(data)
    assert result["payload"]["a"] == 1
    assert result["payload"]["b"] == 2


def test_migration_runner_skips_if_current() -> None:
    runner = MigrationRunner(current_version=2)
    data   = {"save_version": 2, "payload": {"x": 1}}
    result = runner.run(data)
    assert result["payload"]["x"] == 1


def test_migration_runner_raises_on_missing_handler() -> None:
    runner = MigrationRunner(current_version=3)
    data   = {"save_version": 1, "payload": {}}
    with pytest.raises(MigrationError):
        runner.run(data)


def test_migration_needs_migration_true_for_old_save() -> None:
    runner = MigrationRunner(current_version=2)
    assert runner.needs_migration({"save_version": 1}) is True


def test_migration_needs_migration_false_for_current() -> None:
    runner = MigrationRunner(current_version=2)
    assert runner.needs_migration({"save_version": 2}) is False


# ── SaveManager ───────────────────────────────────────────────────────────────

def test_save_and_load_payload(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game", current_version=1)
    sm.save("slot_1", {"level": 5, "gold": 200})
    payload = sm.load_payload("slot_1")
    assert payload["level"] == 5
    assert payload["gold"]  == 200


def test_save_creates_file(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game")
    sm.save("slot_1", {})
    assert (tmp_path / "slot_1.json").exists()


def test_load_raises_on_missing_slot(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game")
    with pytest.raises(SaveNotFoundError):
        sm.load("nonexistent")


def test_exists_true_after_save(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game")
    sm.save("slot_1", {})
    assert sm.exists("slot_1") is True


def test_exists_false_before_save(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game")
    assert sm.exists("slot_1") is False


def test_delete_removes_slot(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game")
    sm.save("slot_1", {})
    sm.delete("slot_1")
    assert sm.exists("slot_1") is False


def test_list_slots_returns_saved_slots(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game")
    sm.save("slot_a", {"x": 1})
    sm.save("slot_b", {"x": 2})
    slots = sm.list_slots()
    ids = [s["slot_id"] for s in slots]
    assert "slot_a" in ids
    assert "slot_b" in ids


def test_list_slots_does_not_include_payload(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game")
    sm.save("slot_1", {"secret": "data"})
    slots = sm.list_slots()
    assert "payload" not in slots[0]


def test_save_preserves_created_at_on_overwrite(tmp_path: Path) -> None:
    sm = SaveManager(tmp_path, game_id="test_game")
    sm.save("slot_1", {"v": 1})
    first = sm.load("slot_1")["created_at"]
    sm.save("slot_1", {"v": 2})
    second = sm.load("slot_1")["created_at"]
    assert first == second


def test_load_applies_migration_automatically(tmp_path: Path) -> None:
    runner = MigrationRunner(current_version=2)

    @runner.register(from_version=1)
    def v1_to_v2(data):
        data["payload"]["migrated"] = True
        data["save_version"] = 2
        return data

    # Write a v1 save manually
    path = tmp_path / "slot_1.json"
    write(path, {
        "save_version": 1,
        "game_id": "test_game",
        "slot_id": "slot_1",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
        "payload": {},
    })

    sm = SaveManager(tmp_path, game_id="test_game",
                     current_version=2, migrations=runner)
    payload = sm.load_payload("slot_1")
    assert payload["migrated"] is True


def test_load_raises_without_migration_runner_for_old_save(tmp_path: Path) -> None:
    path = tmp_path / "slot_1.json"
    write(path, {
        "save_version": 1,
        "game_id": "test_game",
        "slot_id": "slot_1",
        "created_at": "",
        "updated_at": "",
        "payload": {},
    })
    sm = SaveManager(tmp_path, game_id="test_game", current_version=2)
    with pytest.raises(ValueError):
        sm.load("slot_1")
