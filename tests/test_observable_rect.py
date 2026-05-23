"""Tests for pygame_engine.state.observable_rect.ObservableRect."""

from __future__ import annotations
import pytest
import pygame
from pygame_engine.state.observable_rect import ObservableRect


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_construction() -> None:
    r = ObservableRect()
    assert (r.x, r.y, r.w, r.h) == (0, 0, 0, 0)

def test_construction_with_values() -> None:
    r = ObservableRect(10, 20, 300, 400)
    assert (r.x, r.y, r.w, r.h) == (10, 20, 300, 400)

def test_from_pygame_rect() -> None:
    pr = pygame.Rect(5, 15, 100, 50)
    r  = ObservableRect.from_pygame_rect(pr)
    assert (r.x, r.y, r.w, r.h) == (5, 15, 100, 50)

def test_to_pygame_rect() -> None:
    r  = ObservableRect(1, 2, 3, 4)
    pr = r.to_pygame_rect()
    assert isinstance(pr, pygame.Rect)
    assert (pr.x, pr.y, pr.width, pr.height) == (1, 2, 3, 4)

def test_to_pygame_rect_is_copy() -> None:
    r  = ObservableRect(0, 0, 100, 100)
    pr = r.to_pygame_rect()
    pr.x = 999
    assert r.x == 0   # original unchanged


# ── Property setters fire events ──────────────────────────────────────────────

def test_x_setter_fires_event() -> None:
    r = ObservableRect(0, 0, 100, 100)
    events = []
    r.subscribe(lambda old, new: events.append((old.x, new.x)))
    r.x = 50
    assert events == [(0, 50)]

def test_y_setter_fires_event() -> None:
    r = ObservableRect(0, 0, 100, 100)
    events = []
    r.subscribe(lambda old, new: events.append((old.y, new.y)))
    r.y = 30
    assert events == [(0, 30)]

def test_w_setter_fires_event() -> None:
    r = ObservableRect(0, 0, 100, 100)
    events = []
    r.subscribe(lambda old, new: events.append(new.width))
    r.w = 200
    assert events == [200]

def test_h_setter_fires_event() -> None:
    r = ObservableRect(0, 0, 100, 100)
    events = []
    r.subscribe(lambda old, new: events.append(new.height))
    r.h = 50
    assert events == [50]

def test_same_value_no_event() -> None:
    r = ObservableRect(10, 20, 30, 40)
    events = []
    r.subscribe(lambda old, new: events.append(1))
    r.x = 10   # same value
    assert events == []


# ── set() fires one event ─────────────────────────────────────────────────────

def test_set_fires_once() -> None:
    r = ObservableRect(0, 0, 0, 0)
    count = []
    r.subscribe(lambda old, new: count.append(1))
    r.set(10, 20, 300, 400)
    assert len(count) == 1

def test_set_no_change_no_event() -> None:
    r = ObservableRect(1, 2, 3, 4)
    count = []
    r.subscribe(lambda old, new: count.append(1))
    r.set(1, 2, 3, 4)
    assert count == []

def test_set_old_rect_correct() -> None:
    r = ObservableRect(0, 0, 100, 100)
    olds = []
    r.subscribe(lambda old, new: olds.append((old.x, old.y, old.width, old.height)))
    r.set(50, 60, 200, 300)
    assert olds == [(0, 0, 100, 100)]

def test_set_new_rect_correct() -> None:
    r = ObservableRect(0, 0, 0, 0)
    news = []
    r.subscribe(lambda old, new: news.append((new.x, new.y, new.width, new.height)))
    r.set(10, 20, 300, 400)
    assert news == [(10, 20, 300, 400)]


# ── move_to and resize ────────────────────────────────────────────────────────

def test_move_to_changes_position_only() -> None:
    r = ObservableRect(0, 0, 100, 50)
    r.move_to(200, 300)
    assert (r.x, r.y, r.w, r.h) == (200, 300, 100, 50)

def test_move_to_fires_one_event() -> None:
    r = ObservableRect(0, 0, 100, 50)
    count = []
    r.subscribe(lambda old, new: count.append(1))
    r.move_to(10, 20)
    assert len(count) == 1

def test_resize_changes_size_only() -> None:
    r = ObservableRect(10, 20, 100, 50)
    r.resize(400, 300)
    assert (r.x, r.y, r.w, r.h) == (10, 20, 400, 300)

def test_resize_fires_one_event() -> None:
    r = ObservableRect(0, 0, 100, 50)
    count = []
    r.subscribe(lambda old, new: count.append(1))
    r.resize(200, 200)
    assert len(count) == 1


# ── transaction() ─────────────────────────────────────────────────────────────

def test_transaction_fires_once() -> None:
    r = ObservableRect(0, 0, 0, 0)
    count = []
    r.subscribe(lambda old, new: count.append(1))
    with r.transaction():
        r.x = 10
        r.y = 20
        r.w = 300
        r.h = 400
    assert len(count) == 1

def test_transaction_no_change_no_event() -> None:
    r = ObservableRect(1, 2, 3, 4)
    count = []
    r.subscribe(lambda old, new: count.append(1))
    with r.transaction():
        r.x = 1   # same
    assert count == []

def test_transaction_old_value_is_start() -> None:
    r = ObservableRect(10, 20, 0, 0)
    olds = []
    r.subscribe(lambda old, new: olds.append((old.x, old.y)))
    with r.transaction():
        r.x = 99
        r.y = 88
    assert olds == [(10, 20)]

def test_transaction_new_value_is_final() -> None:
    r = ObservableRect(0, 0, 0, 0)
    news = []
    r.subscribe(lambda old, new: news.append((new.x, new.y)))
    with r.transaction():
        r.x = 1
        r.x = 2
        r.x = 99
        r.y = 77
    assert news == [(99, 77)]

def test_nested_transaction_transparent() -> None:
    r = ObservableRect(0, 0, 0, 0)
    count = []
    r.subscribe(lambda old, new: count.append(1))
    with r.transaction():
        r.x = 10
        with r.transaction():   # inner — transparent
            r.y = 20
    assert len(count) == 1

def test_transaction_cleans_up_on_exception() -> None:
    r = ObservableRect(0, 0, 0, 0)
    try:
        with r.transaction():
            r.x = 5
            raise ValueError("mid-transaction")
    except ValueError:
        pass
    assert r._in_transaction is False


# ── Subscription management ───────────────────────────────────────────────────

def test_subscribe_returns_listener() -> None:
    r  = ObservableRect()
    fn = lambda old, new: None
    assert r.subscribe(fn) is fn

def test_subscribe_twice_is_noop() -> None:
    r  = ObservableRect()
    fn = lambda old, new: None
    r.subscribe(fn)
    r.subscribe(fn)
    assert r.listener_count == 1

def test_unsubscribe_stops_events() -> None:
    r = ObservableRect()
    calls = []
    fn = lambda old, new: calls.append(1)
    r.subscribe(fn)
    r.unsubscribe(fn)
    r.x = 10
    assert calls == []

def test_unsubscribe_unknown_is_noop() -> None:
    r  = ObservableRect()
    fn = lambda old, new: None
    r.unsubscribe(fn)   # should not raise

def test_clear_listeners() -> None:
    r = ObservableRect()
    r.subscribe(lambda old, new: None)
    r.subscribe(lambda old, new: None)
    r.clear_listeners()
    assert r.listener_count == 0


# ── Equality ──────────────────────────────────────────────────────────────────

def test_eq_same_values() -> None:
    assert ObservableRect(1, 2, 3, 4) == ObservableRect(1, 2, 3, 4)

def test_eq_different_values() -> None:
    assert ObservableRect(1, 2, 3, 4) != ObservableRect(1, 2, 3, 5)

def test_eq_pygame_rect() -> None:
    assert ObservableRect(10, 20, 30, 40) == pygame.Rect(10, 20, 30, 40)


# ── Repr ──────────────────────────────────────────────────────────────────────

def test_repr() -> None:
    r = ObservableRect(1, 2, 3, 4)
    assert "1" in repr(r) and "2" in repr(r)
