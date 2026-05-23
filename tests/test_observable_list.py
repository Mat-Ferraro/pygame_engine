"""Tests for pygame_engine.state.observable_list.ObservableList."""

from __future__ import annotations
import pytest
from pygame_engine.state.observable_list import ObservableList, ListEvent


# ── Construction ──────────────────────────────────────────────────────────────

def test_empty_by_default() -> None:
    lst = ObservableList()
    assert len(lst) == 0

def test_initial_contents_copied() -> None:
    src = [1, 2, 3]
    lst = ObservableList(src)
    src.append(99)
    assert list(lst) == [1, 2, 3]

def test_len() -> None:
    lst = ObservableList([10, 20, 30])
    assert len(lst) == 3

def test_iter() -> None:
    lst = ObservableList([1, 2, 3])
    assert list(lst) == [1, 2, 3]

def test_contains() -> None:
    lst = ObservableList(["a", "b"])
    assert "a" in lst
    assert "c" not in lst

def test_getitem() -> None:
    lst = ObservableList([10, 20, 30])
    assert lst[0] == 10
    assert lst[-1] == 30

def test_index() -> None:
    lst = ObservableList(["x", "y", "z"])
    assert lst.index("y") == 1

def test_copy_returns_plain_list() -> None:
    lst = ObservableList([1, 2, 3])
    c   = lst.copy()
    assert isinstance(c, list)
    assert c == [1, 2, 3]


# ── append ────────────────────────────────────────────────────────────────────

def test_append_adds_item() -> None:
    lst = ObservableList()
    lst.append("a")
    assert list(lst) == ["a"]

def test_append_event_kind() -> None:
    lst = ObservableList()
    events = []
    lst.subscribe(events.append)
    lst.append("x")
    assert events[0].kind == "add"

def test_append_event_index() -> None:
    lst = ObservableList(["a", "b"])
    events = []
    lst.subscribe(events.append)
    lst.append("c")
    assert events[0].index == 2

def test_append_event_item() -> None:
    lst = ObservableList()
    events = []
    lst.subscribe(events.append)
    lst.append(42)
    assert events[0].item == 42


# ── insert ────────────────────────────────────────────────────────────────────

def test_insert_at_start() -> None:
    lst = ObservableList([2, 3])
    lst.insert(0, 1)
    assert list(lst) == [1, 2, 3]

def test_insert_event_kind_and_index() -> None:
    lst = ObservableList([10, 20])
    events = []
    lst.subscribe(events.append)
    lst.insert(1, 15)
    assert events[0].kind == "add"
    assert events[0].index == 1


# ── remove ────────────────────────────────────────────────────────────────────

def test_remove_item() -> None:
    lst = ObservableList([1, 2, 3])
    lst.remove(2)
    assert list(lst) == [1, 3]

def test_remove_event() -> None:
    lst = ObservableList(["a", "b", "c"])
    events = []
    lst.subscribe(events.append)
    lst.remove("b")
    assert events[0].kind == "remove"
    assert events[0].index == 1
    assert events[0].item == "b"

def test_remove_not_found_raises() -> None:
    lst = ObservableList([1, 2])
    with pytest.raises(ValueError):
        lst.remove(99)


# ── pop ───────────────────────────────────────────────────────────────────────

def test_pop_returns_item() -> None:
    lst = ObservableList([1, 2, 3])
    assert lst.pop() == 3

def test_pop_removes_item() -> None:
    lst = ObservableList([1, 2, 3])
    lst.pop()
    assert list(lst) == [1, 2]

def test_pop_event() -> None:
    lst = ObservableList([10, 20, 30])
    events = []
    lst.subscribe(events.append)
    lst.pop(1)
    assert events[0].kind == "remove"
    assert events[0].item == 20


# ── __setitem__ ───────────────────────────────────────────────────────────────

def test_setitem_replaces() -> None:
    lst = ObservableList([1, 2, 3])
    lst[1] = 99
    assert list(lst) == [1, 99, 3]

def test_setitem_event() -> None:
    lst = ObservableList([1, 2, 3])
    events = []
    lst.subscribe(events.append)
    lst[0] = 100
    assert events[0].kind == "replace"
    assert events[0].index == 0
    assert events[0].item == 100


# ── move ──────────────────────────────────────────────────────────────────────

def test_move_reorders() -> None:
    lst = ObservableList(["a", "b", "c"])
    lst.move(0, 2)
    assert list(lst) == ["b", "c", "a"]

def test_move_same_index_no_event() -> None:
    lst = ObservableList([1, 2, 3])
    events = []
    lst.subscribe(events.append)
    lst.move(1, 1)
    assert events == []

def test_move_event() -> None:
    lst = ObservableList(["x", "y", "z"])
    events = []
    lst.subscribe(events.append)
    lst.move(2, 0)
    assert events[0].kind == "move"
    assert events[0].old_index == 2
    assert events[0].index == 0


# ── clear ─────────────────────────────────────────────────────────────────────

def test_clear_removes_all() -> None:
    lst = ObservableList([1, 2, 3])
    lst.clear()
    assert len(lst) == 0

def test_clear_fires_one_event() -> None:
    lst = ObservableList([1, 2, 3])
    events = []
    lst.subscribe(events.append)
    lst.clear()
    assert len(events) == 1
    assert events[0].kind == "clear"


# ── Subscription ──────────────────────────────────────────────────────────────

def test_subscribe_returns_listener() -> None:
    lst = ObservableList()
    fn  = lambda e: None
    assert lst.subscribe(fn) is fn

def test_subscribe_twice_is_noop() -> None:
    lst = ObservableList()
    fn  = lambda e: None
    lst.subscribe(fn)
    lst.subscribe(fn)
    assert lst.listener_count == 1

def test_unsubscribe_stops_events() -> None:
    lst   = ObservableList()
    calls = []
    fn    = lambda e: calls.append(1)
    lst.subscribe(fn)
    lst.unsubscribe(fn)
    lst.append(1)
    assert calls == []

def test_unsubscribe_unknown_is_noop() -> None:
    lst = ObservableList()
    lst.unsubscribe(lambda e: None)   # must not raise

def test_clear_listeners() -> None:
    lst = ObservableList()
    lst.subscribe(lambda e: None)
    lst.subscribe(lambda e: None)
    lst.clear_listeners()
    assert lst.listener_count == 0


# ── Repr ──────────────────────────────────────────────────────────────────────

def test_repr() -> None:
    lst = ObservableList([1, 2, 3])
    assert "1" in repr(lst)
