"""
Provides a simple, tag-aware log with level filtering and capped history.
The overlay and console read from this log. Game code writes to it.

Usage::

    from pygame_engine.devtools.debug_log import log, warn, error, get_entries

    log("Scene entered", tag="scene")
    warn("Asset not cached", tag="assets")
    error("Save failed", tag="persistence")

    entries = get_entries()   # list of LogEntry namedtuples
"""

from __future__ import annotations

import time
from collections import deque
from typing import NamedTuple


class LogLevel:
    """Enumeration of available log severity levels."""
    INFO  = "INFO"
    WARN  = "WARN"
    ERROR = "ERROR"


class LogEntry(NamedTuple):
    """A single entry in the debug log with level, tag, message, and timestamp."""
    timestamp: float   # time.monotonic()
    level:     str     # LogLevel constant
    tag:       str     # subsystem tag e.g. "scene", "input"
    message:   str


# ── Module-level log store ────────────────────────────────────────────────────

_MAX_ENTRIES = 200
_entries: deque[LogEntry] = deque(maxlen=_MAX_ENTRIES)
_min_level: str = LogLevel.INFO


# ── Public API ────────────────────────────────────────────────────────────────

def log(message: str, tag: str = "engine") -> None:
    """Log an INFO-level message."""
    _append(LogLevel.INFO, tag, message)


def warn(message: str, tag: str = "engine") -> None:
    """Log a WARN-level message."""
    _append(LogLevel.WARN, tag, message)


def error(message: str, tag: str = "engine") -> None:
    """Log an ERROR-level message."""
    _append(LogLevel.ERROR, tag, message)


def get_entries(
    level: str | None = None,
    tag:   str | None = None,
    limit: int        = 50,
) -> list[LogEntry]:
    """
    Return recent log entries, optionally filtered.

    Args:
        level: If given, only return entries at this level.
        tag:   If given, only return entries with this tag.
        limit: Maximum number of entries to return (most recent first).

    Returns:
        List of ``LogEntry`` namedtuples, newest first.
    """
    results = list(_entries)

    if level is not None:
        results = [e for e in results if e.level == level]
    if tag is not None:
        results = [e for e in results if e.tag == tag]

    return list(reversed(results))[:limit]


def clear() -> None:
    """Clear all log entries."""
    _entries.clear()


def set_max_entries(n: int) -> None:
    """Change the maximum number of stored entries."""
    global _entries
    _entries = deque(_entries, maxlen=n)


# ── Internal ──────────────────────────────────────────────────────────────────

def _append(level: str, tag: str, message: str) -> None:
    _entries.append(LogEntry(
        timestamp=time.monotonic(),
        level=level,
        tag=tag,
        message=message,
    ))