"""
editor/editor_settings.py

Load and save the editor's own durable settings between sessions.

This is deliberately separate from scene layout persistence:

- A *scene layout* (``*.layout.json``) is authored content that belongs in
  version control next to the scene it describes.
- *Editor settings* (this file) are per-developer preferences — grid size,
  overlay toggles, the last scene that was open. They do not belong in a
  scene file and are typically git-ignored.

The actual bytes are read and written through
``pygame_engine.persistence.storage``, which already gives us atomic writes
(write to ``.tmp``, rename) and a ``.bak`` of the previous file. There is no
reason to reimplement that here.

The settings file lives at ``editor/editor_settings.json`` by default.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pygame_engine.persistence import storage

if False:  # TYPE_CHECKING without importing at runtime
    from editor.editor_state import EditorState


#: Default location of the settings file, resolved relative to this module
#: so it does not depend on the process working directory.
DEFAULT_SETTINGS_PATH: Path = Path(__file__).resolve().parent / "editor_settings.json"

#: Schema version of the settings envelope. Bump on incompatible changes.
SETTINGS_VERSION = 1


def load_settings(
    state: "EditorState",
    path: Path | None = None,
) -> bool:
    """
    Load editor settings from disk and apply them to ``state``.

    A missing file is not an error — it just means this is a first run, and
    ``state`` keeps its dataclass defaults. A corrupt file is also tolerated:
    it is ignored and ``False`` is returned so the caller can log it.

    Args:
        state: The ``EditorState`` to populate. Modified in place.
        path:  Override the settings file location (mainly for tests).

    Returns:
        True if a settings file was found and applied; False if there was no
        file or it could not be read.
    """
    path = Path(path) if path is not None else DEFAULT_SETTINGS_PATH

    try:
        envelope = storage.read(path)
    except storage.SaveNotFoundError:
        return False          # first run — nothing to load
    except storage.StorageError:
        return False          # corrupt or unreadable — fall back to defaults

    if not isinstance(envelope, dict):
        return False

    payload = envelope.get("settings", {})
    state.apply_settings(payload)
    return True


def save_settings(
    state: "EditorState",
    path: Path | None = None,
) -> None:
    """
    Write the durable fields of ``state`` to the settings file.

    Wraps ``EditorState.to_settings()`` in a small versioned envelope so the
    file can be migrated later if its shape ever changes. Uses the engine's
    atomic storage writer, so an interrupted write cannot corrupt the
    existing file.

    Args:
        state: The ``EditorState`` to persist.
        path:  Override the settings file location (mainly for tests).

    Raises:
        StorageError: If the file cannot be written.
    """
    path = Path(path) if path is not None else DEFAULT_SETTINGS_PATH

    envelope: dict[str, Any] = {
        "settings_version": SETTINGS_VERSION,
        "settings":         state.to_settings(),
    }
    storage.write(path, envelope)
