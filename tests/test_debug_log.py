"""
tests/test_debug_log.py

Tests for pygame_engine.devtools.debug_log.

Covers: log/warn/error, filtering by level and tag, limit, clear.
"""

import pytest

from pygame_engine.devtools.debug_log import (
    LogLevel,
    clear,
    error,
    get_entries,
    log,
    warn,
)


def setup_function():
    """Clear the log before each test."""
    clear()


def test_log_adds_info_entry() -> None:
    log("hello", tag="test")
    entries = get_entries()
    assert entries[0].message == "hello"
    assert entries[0].level   == LogLevel.INFO
    assert entries[0].tag     == "test"


def test_warn_adds_warn_entry() -> None:
    warn("careful", tag="test")
    entries = get_entries(level=LogLevel.WARN)
    assert entries[0].message == "careful"
    assert entries[0].level   == LogLevel.WARN


def test_error_adds_error_entry() -> None:
    error("broken", tag="test")
    entries = get_entries(level=LogLevel.ERROR)
    assert entries[0].level == LogLevel.ERROR


def test_get_entries_newest_first() -> None:
    log("first",  tag="test")
    log("second", tag="test")
    log("third",  tag="test")
    entries = get_entries()
    assert entries[0].message == "third"
    assert entries[1].message == "second"
    assert entries[2].message == "first"


def test_get_entries_filter_by_level() -> None:
    log("info msg",  tag="test")
    warn("warn msg", tag="test")
    error("err msg", tag="test")
    entries = get_entries(level=LogLevel.WARN)
    assert len(entries) == 1
    assert entries[0].message == "warn msg"


def test_get_entries_filter_by_tag() -> None:
    log("scene msg", tag="scene")
    log("input msg", tag="input")
    entries = get_entries(tag="scene")
    assert len(entries) == 1
    assert entries[0].message == "scene msg"


def test_get_entries_limit() -> None:
    for i in range(20):
        log(f"msg {i}", tag="test")
    entries = get_entries(limit=5)
    assert len(entries) == 5


def test_clear_removes_all_entries() -> None:
    log("something", tag="test")
    clear()
    assert get_entries() == []


def test_entries_have_timestamp() -> None:
    log("timed", tag="test")
    entry = get_entries()[0]
    assert entry.timestamp > 0


def test_default_tag_is_engine() -> None:
    log("no tag given")
    entry = get_entries()[0]
    assert entry.tag == "engine"