"""
persistence/save_manager.py

High-level save/load orchestration for pygame_engine.

``SaveManager`` is the top-level entry point for persistence. It owns:
- save slot organisation under a configured save directory
- the save envelope (metadata wrapper around the game payload)
- optional migration pipeline integration
- delegation to ``storage`` for safe file I/O

Game projects interact with ``SaveManager``, not with ``storage`` directly.

Usage::

    from pygame_engine.persistence.save_manager import SaveManager
    from pathlib import Path

    saves = SaveManager(
        save_dir=Path("saves"),
        game_id="my_game",
        current_version=1,
    )

    # Save
    saves.save(slot="slot_1", payload={"level": 3, "gold": 120})

    # Load
    envelope = saves.load("slot_1")
    payload  = envelope["payload"]

    # List all slots
    for info in saves.list_slots():
        print(info["slot_id"], info["updated_at"])

    # Delete
    saves.delete("slot_1")
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from pygame_engine.persistence import storage
from pygame_engine.persistence.migrations import MigrationRunner
from pygame_engine.persistence.storage import SaveNotFoundError


class SaveManager:
    """
    Manages save slots for a game project.

    Each slot is a single JSON file: ``{save_dir}/{slot_id}.json``.

    The save envelope structure::

        {
            "save_version": 1,
            "game_id":      "my_game",
            "slot_id":      "slot_1",
            "created_at":   "2025-01-01T12:00:00",
            "updated_at":   "2025-01-01T12:05:00",
            "payload":      { ... game data ... }
        }

    ``payload`` is entirely owned by the game project. The engine only
    reads and writes the envelope fields listed above.
    """

    def __init__(
        self,
        save_dir: Path,
        game_id: str,
        current_version: int = 1,
        migrations: MigrationRunner | None = None,
    ) -> None:
        """
        Args:
            save_dir:        Directory where save files are stored.
                             Created automatically on first save.
            game_id:         Identifier for this game. Written into every
                             save envelope as a sanity check.
            current_version: Current save schema version. Used to detect
                             when a save needs migration.
            migrations:      Optional ``MigrationRunner`` for upgrading
                             old saves. If None, loading an old-version
                             save raises ``ValueError``.
        """
        self._save_dir        = Path(save_dir)
        self._game_id         = game_id
        self._current_version = current_version
        self._migrations      = migrations

    # ── Save / load ───────────────────────────────────────────────────────────

    def save(self, slot: str, payload: dict[str, Any]) -> None:
        """
        Save ``payload`` to the given slot.

        Creates the slot if it does not exist. Updates ``updated_at`` on
        every save. Preserves the original ``created_at`` on overwrites.

        Args:
            slot:    Slot identifier (used as the filename stem).
                     Must be a valid filename component (no slashes).
            payload: Game-specific save data. Must be JSON-serialisable.
        """
        path     = self._slot_path(slot)
        now      = self._timestamp()
        existing = None

        if path.exists():
            try:
                existing = storage.read(path)
            except Exception:
                pass  # overwrite corrupt saves cleanly

        created_at = existing["created_at"] if existing else now

        envelope: dict[str, Any] = {
            "save_version": self._current_version,
            "game_id":      self._game_id,
            "slot_id":      slot,
            "created_at":   created_at,
            "updated_at":   now,
            "payload":      payload,
        }
        storage.write(path, envelope)

    def load(self, slot: str) -> dict[str, Any]:
        """
        Load and return the save envelope for ``slot``.

        If the save is an older version and a ``MigrationRunner`` was
        provided, migrations are applied automatically before returning.

        Args:
            slot: Slot identifier.

        Returns:
            The full save envelope dict (including ``payload``).

        Raises:
            SaveNotFoundError: If the slot does not exist.
            ValueError:        If the save version is outdated and no
                               migration runner was configured.
            MigrationError:    If migration fails.
            CorruptSaveError:  If the file cannot be parsed.
        """
        path = self._slot_path(slot)
        data = storage.read(path)

        self._validate_game_id(data, slot)

        if data.get("save_version", 1) < self._current_version:
            if self._migrations is None:
                raise ValueError(
                    f"Save '{slot}' is version {data.get('save_version')} "
                    f"but current version is {self._current_version}. "
                    f"Provide a MigrationRunner to upgrade it."
                )
            data = self._migrations.run(data)

        return data

    def load_payload(self, slot: str) -> dict[str, Any]:
        """
        Load and return only the game payload for ``slot``.

        Convenience wrapper over ``load()`` — skips the envelope fields.

        Args:
            slot: Slot identifier.

        Returns:
            The ``payload`` dict from the save envelope.
        """
        return self.load(slot)["payload"]

    # ── Slot management ───────────────────────────────────────────────────────

    def exists(self, slot: str) -> bool:
        """Return True if a save file exists for ``slot``."""
        return self._slot_path(slot).exists()

    def delete(self, slot: str) -> bool:
        """
        Delete the save file for ``slot`` (and its .bak if present).

        Returns:
            True if deleted, False if the slot did not exist.
        """
        return storage.delete(self._slot_path(slot))

    def list_slots(self) -> list[dict[str, Any]]:
        """
        Return metadata for all existing save slots.

        Each entry contains: ``slot_id``, ``save_version``, ``game_id``,
        ``created_at``, ``updated_at``. The ``payload`` is NOT included.

        Returns:
            List of slot metadata dicts, sorted by ``updated_at``
            descending (most recent first).
        """
        slots: list[dict[str, Any]] = []

        for path in storage.list_saves(self._save_dir):
            try:
                data = storage.read(path)
                slots.append({
                    "slot_id":      data.get("slot_id", path.stem),
                    "save_version": data.get("save_version", 0),
                    "game_id":      data.get("game_id", ""),
                    "created_at":   data.get("created_at", ""),
                    "updated_at":   data.get("updated_at", ""),
                })
            except Exception:
                pass  # skip corrupt slot files in listing

        return sorted(slots, key=lambda s: s["updated_at"], reverse=True)

    @property
    def save_dir(self) -> Path:
        """The directory where save files are stored."""
        return self._save_dir

    # ── Internal ──────────────────────────────────────────────────────────────

    def _slot_path(self, slot: str) -> Path:
        return self._save_dir / f"{slot}.json"

    @staticmethod
    def _timestamp() -> str:
        return datetime.datetime.now().isoformat(timespec="seconds")

    def _validate_game_id(self, data: dict[str, Any], slot: str) -> None:
        saved_id = data.get("game_id", "")
        if saved_id and saved_id != self._game_id:
            raise ValueError(
                f"Save slot '{slot}' belongs to game '{saved_id}', "
                f"not '{self._game_id}'. Wrong save directory?"
            )
