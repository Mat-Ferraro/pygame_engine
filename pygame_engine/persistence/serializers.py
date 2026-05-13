"""
persistence/serializers.py

Generic serialisation helpers for pygame_engine persistence.

These helpers convert Python objects to and from JSON-safe plain dicts.
They work with simple types and dataclasses. They do not know about
game-specific schemas — that belongs in the game project.

Usage::

    from pygame_engine.persistence.serializers import to_dict, from_dict
    from dataclasses import dataclass

    @dataclass
    class Settings:
        volume: float = 1.0
        fullscreen: bool = False

    data   = to_dict(Settings(volume=0.8))
    # {"volume": 0.8, "fullscreen": False}

    result = from_dict(Settings, data)
    # Settings(volume=0.8, fullscreen=False)
"""

from __future__ import annotations

import dataclasses
from typing import Any, Type, TypeVar

T = TypeVar("T")


# ── Dataclass helpers ─────────────────────────────────────────────────────────

def to_dict(obj: Any) -> dict[str, Any]:
    """
    Convert a dataclass instance to a plain JSON-safe dict.

    Nested dataclasses are converted recursively. Lists and dicts are
    passed through. Other types are included as-is and must be
    JSON-serialisable.

    Args:
        obj: A dataclass instance.

    Returns:
        A plain dict representation.

    Raises:
        TypeError: If ``obj`` is not a dataclass instance.
    """
    if not dataclasses.is_dataclass(obj) or isinstance(obj, type):
        raise TypeError(f"to_dict expects a dataclass instance, got {type(obj)}")

    result: dict[str, Any] = {}
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        result[field.name] = _serialise_value(value)
    return result


def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
    """
    Reconstruct a dataclass instance from a plain dict.

    Only fields present in the dataclass are read from ``data``.
    Extra keys in ``data`` are silently ignored (forwards compatibility).
    Missing keys use the dataclass field default (if one exists) or
    raise ``TypeError`` if the field is required.

    Args:
        cls:  A dataclass class.
        data: A dict previously produced by ``to_dict`` (or equivalent).

    Returns:
        An instance of ``cls``.

    Raises:
        TypeError: If ``cls`` is not a dataclass.
    """
    if not dataclasses.is_dataclass(cls) or not isinstance(cls, type):
        raise TypeError(f"from_dict expects a dataclass class, got {cls}")

    field_names = {f.name for f in dataclasses.fields(cls)}
    kwargs = {k: v for k, v in data.items() if k in field_names}
    return cls(**kwargs)  # type: ignore[call-arg]


# ── Primitive helpers ─────────────────────────────────────────────────────────

def ensure_str_keys(data: dict[Any, Any]) -> dict[str, Any]:
    """
    Return a copy of ``data`` with all keys converted to strings.

    JSON requires string keys. Use this when building a payload that
    contains non-string keys (e.g. integer slot IDs).

    Args:
        data: Source dict.

    Returns:
        New dict with string keys.
    """
    return {str(k): v for k, v in data.items()}


def safe_int(value: Any, default: int = 0) -> int:
    """
    Coerce ``value`` to int, returning ``default`` on failure.

    Useful when loading save data that may contain the wrong type
    due to schema drift.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Coerce ``value`` to float, returning ``default`` on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Coerce ``value`` to bool, returning ``default`` on failure."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return default


# ── Internal ──────────────────────────────────────────────────────────────────

def _serialise_value(value: Any) -> Any:
    """Recursively serialise a value for JSON storage."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return to_dict(value)
    if isinstance(value, list):
        return [_serialise_value(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _serialise_value(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_serialise_value(item) for item in value]
    return value
