"""
persistence/storage.py

Low-level safe file storage for pygame_engine.

Handles reading and writing JSON files with:
- atomic writes (write to .tmp, rename to final)
- automatic .bak backup of the previous save
- clear errors on missing or corrupt files

Nothing in here knows about save slots, game payloads, or versions.
It only knows about files and JSON.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class StorageError(OSError):
    """Raised when a storage operation fails unrecoverably."""


class CorruptSaveError(StorageError):
    """Raised when a save file exists but cannot be parsed as valid JSON."""


class SaveNotFoundError(StorageError):
    """Raised when a requested save file does not exist."""


def write(path: Path, data: dict[str, Any]) -> None:
    """
    Write ``data`` to ``path`` as JSON, atomically.

    Process:
    1. Serialise to JSON string.
    2. Write to ``path.with_suffix('.tmp')``.
    3. If ``path`` already exists, copy it to ``path.with_suffix('.bak')``.
    4. Rename the .tmp file to the final path.

    Args:
        path: Destination file path. Parent directory is created if needed.
        data: A JSON-serialisable dict.

    Raises:
        StorageError: If the write or rename fails.
    """
    path = Path(path)
    tmp  = path.with_suffix(".tmp")
    bak  = path.with_suffix(".bak")

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        text = json.dumps(data, indent=2, ensure_ascii=False)
        tmp.write_text(text, encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        raise StorageError(f"Failed to write save to {path}: {exc}") from exc

    # Backup previous save before replacing it
    if path.exists():
        try:
            path.replace(bak)
        except OSError:
            pass  # best-effort backup; don't fail the whole save

    try:
        tmp.rename(path)
    except OSError as exc:
        raise StorageError(f"Failed to finalise save at {path}: {exc}") from exc


def read(path: Path) -> dict[str, Any]:
    """
    Read and parse a JSON save file.

    Args:
        path: File to read.

    Returns:
        Parsed dict.

    Raises:
        SaveNotFoundError: If the file does not exist.
        CorruptSaveError:  If the file exists but is not valid JSON.
        StorageError:      If the file cannot be read for another reason.
    """
    path = Path(path)

    if not path.exists():
        raise SaveNotFoundError(f"Save not found: {path}")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"Cannot read save file {path}: {exc}") from exc

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CorruptSaveError(
            f"Save file is corrupt (invalid JSON): {path}\n  {exc}"
        ) from exc


def exists(path: Path) -> bool:
    """Return True if a save file exists at ``path``."""
    return Path(path).exists()


def delete(path: Path) -> bool:
    """
    Delete a save file and its .bak if present.

    Args:
        path: File to delete.

    Returns:
        True if the file was deleted, False if it did not exist.
    """
    path = Path(path)
    bak  = path.with_suffix(".bak")
    deleted = False

    if path.exists():
        path.unlink()
        deleted = True
    if bak.exists():
        bak.unlink()

    return deleted


def list_saves(directory: Path, suffix: str = ".json") -> list[Path]:
    """
    Return all save files in ``directory`` matching ``suffix``.

    Args:
        directory: Directory to scan.
        suffix:    File extension to match (default ``.json``).

    Returns:
        Sorted list of matching ``Path`` objects.
        Returns an empty list if the directory does not exist.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return sorted(directory.glob(f"*{suffix}"))
