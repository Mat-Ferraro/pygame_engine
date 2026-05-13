"""
pygame_engine.persistence

Save/load infrastructure for pygame_engine projects.

Public API::

    from pygame_engine.persistence import SaveManager
    from pygame_engine.persistence.migrations import MigrationRunner
    from pygame_engine.persistence.serializers import to_dict, from_dict
    from pygame_engine.persistence.storage import (
        SaveNotFoundError,
        CorruptSaveError,
        StorageError,
    )

Typical usage::

    from pygame_engine.persistence import SaveManager
    from pathlib import Path

    saves = SaveManager(
        save_dir=Path("saves"),
        game_id="my_game",
        current_version=1,
    )
    saves.save("slot_1", {"level": 1, "gold": 0})
    payload = saves.load_payload("slot_1")
"""

from pygame_engine.persistence.save_manager import SaveManager
from pygame_engine.persistence.storage import (
    CorruptSaveError,
    SaveNotFoundError,
    StorageError,
)

__all__ = [
    "SaveManager",
    "StorageError",
    "SaveNotFoundError",
    "CorruptSaveError",
]
