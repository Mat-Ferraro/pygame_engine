"""
tests/test_event_bus.py

Tests for pygame_engine.events.EventBus.

Covers: subscribe, emit, unsubscribe, once, wildcards, clear,
duplicate subscription prevention, broken handler isolation,
handler_count, subscribed_events.
"""

import pytest

from pygame_engine.events.event_bus import EventBus


def fresh() -> EventBus:
    """Return a clean EventBus for each test."""
    return EventBus()


# ── Basic subscribe / emit ────────────────────────────────────────────────────

def test_handler_called_on_matching_emit() -> None:
    bus   = fresh()
    calls: list[dict] = []
    bus.on("player.damaged", lambda **kw: calls.append(kw))
    bus.emit("player.damaged", amount=10)
    assert calls == [{"amount": 10}]


def test_handler_not_called_on_different_event() -> None:
    bus   = fresh()
    calls: list = []
    bus.on("player.damaged", lambda **kw: calls.append(kw))
    bus.emit("player.died")
    assert calls == []


def test_multiple_handlers_all_called() -> None:
    bus    = fresh()
    calls: list[int] = []
    bus.on("game.tick", lambda **kw: calls.append(1))
    bus.on("game.tick", lambda **kw: calls.append(2))
    bus.emit("game.tick")
    assert sorted(calls) == [1, 2]


def test_emit_returns_handler_count() -> None:
    bus = fresh()
    bus.on("ev", lambda **kw: None)
    bus.on("ev", lambda **kw: None)
    assert bus.emit("ev") == 2


def test_emit_returns_zero_when_no_handlers() -> None:
    bus = fresh()
    assert bus.emit("ev") == 0


def test_kwargs_forwarded_correctly() -> None:
    bus       = fresh()
    received: list = []
    bus.on("hit", lambda source, amount, **kw: received.append((source, amount)))
    bus.emit("hit", source="spike", amount=25)
    assert received == [("spike", 25)]


# ── Unsubscribe ───────────────────────────────────────────────────────────────

def test_off_removes_handler() -> None:
    bus   = fresh()
    calls: list = []

    def handler(**kw):
        calls.append(1)

    bus.on("ev", handler)
    bus.off("ev", handler)
    bus.emit("ev")
    assert calls == []


def test_off_returns_true_when_found() -> None:
    bus = fresh()
    def h(**kw): pass
    bus.on("ev", h)
    assert bus.off("ev", h) is True


def test_off_returns_false_when_not_found() -> None:
    bus = fresh()
    def h(**kw): pass
    assert bus.off("ev", h) is False


def test_off_unknown_event_returns_false() -> None:
    bus = fresh()
    assert bus.off("nonexistent", lambda **kw: None) is False


def test_off_only_removes_specified_handler() -> None:
    bus    = fresh()
    calls: list[int] = []

    def h1(**kw): calls.append(1)
    def h2(**kw): calls.append(2)

    bus.on("ev", h1)
    bus.on("ev", h2)
    bus.off("ev", h1)
    bus.emit("ev")
    assert calls == [2]


# ── Duplicate subscription prevention ────────────────────────────────────────

def test_subscribing_same_handler_twice_is_noop() -> None:
    bus   = fresh()
    calls: list = []

    def h(**kw): calls.append(1)

    bus.on("ev", h)
    bus.on("ev", h)   # duplicate
    bus.emit("ev")
    assert calls == [1]   # called only once


# ── Once ──────────────────────────────────────────────────────────────────────

def test_once_fires_on_first_emit() -> None:
    bus   = fresh()
    calls: list = []
    bus.once("ev", lambda **kw: calls.append(1))
    bus.emit("ev")
    assert calls == [1]


def test_once_does_not_fire_on_second_emit() -> None:
    bus   = fresh()
    calls: list = []
    bus.once("ev", lambda **kw: calls.append(1))
    bus.emit("ev")
    bus.emit("ev")
    assert calls == [1]


def test_once_handler_removed_after_firing() -> None:
    bus = fresh()
    bus.once("ev", lambda **kw: None)
    bus.emit("ev")
    assert bus.handler_count("ev") == 0


def test_once_and_permanent_can_coexist() -> None:
    bus       = fresh()
    once_calls: list = []
    perm_calls: list = []
    bus.once("ev", lambda **kw: once_calls.append(1))
    bus.on("ev",   lambda **kw: perm_calls.append(1))
    bus.emit("ev")
    bus.emit("ev")
    assert once_calls == [1]
    assert perm_calls == [1, 1]


# ── Wildcards ─────────────────────────────────────────────────────────────────

def test_wildcard_matches_all_subevents() -> None:
    bus   = fresh()
    calls: list[str] = []
    bus.on("player.*", lambda event_name="", **kw: calls.append(event_name))
    bus.emit("player.damaged", event_name="player.damaged")
    bus.emit("player.died",    event_name="player.died")
    bus.emit("enemy.spawned",  event_name="enemy.spawned")
    assert "player.damaged" in calls
    assert "player.died"    in calls
    assert "enemy.spawned"  not in calls


def test_wildcard_does_not_match_parent() -> None:
    bus   = fresh()
    calls: list = []
    bus.on("player.*", lambda **kw: calls.append(1))
    bus.emit("player")   # no dot — should not match player.*
    assert calls == []


def test_exact_and_wildcard_both_fire() -> None:
    bus   = fresh()
    calls: list[str] = []
    bus.on("player.damaged", lambda **kw: calls.append("exact"))
    bus.on("player.*",       lambda **kw: calls.append("wild"))
    bus.emit("player.damaged")
    assert "exact" in calls
    assert "wild"  in calls


# ── Clear ─────────────────────────────────────────────────────────────────────

def test_clear_removes_all_handlers_for_event() -> None:
    bus   = fresh()
    calls: list = []
    bus.on("ev", lambda **kw: calls.append(1))
    bus.on("ev", lambda **kw: calls.append(2))
    bus.clear("ev")
    bus.emit("ev")
    assert calls == []


def test_clear_all_removes_everything() -> None:
    bus = fresh()
    bus.on("a", lambda **kw: None)
    bus.on("b", lambda **kw: None)
    bus.on("c", lambda **kw: None)
    bus.clear_all()
    assert bus.handler_count() == 0


def test_clear_unknown_event_is_noop() -> None:
    bus = fresh()
    bus.clear("nonexistent")   # should not raise


# ── Broken handler isolation ──────────────────────────────────────────────────

def test_broken_handler_does_not_prevent_other_handlers() -> None:
    bus   = fresh()
    calls: list = []

    def broken(**kw): raise RuntimeError("oops")
    def good(**kw):   calls.append(1)

    bus.on("ev", broken)
    bus.on("ev", good)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bus.emit("ev")

    assert calls == [1]


# ── Handler count / subscribed events ────────────────────────────────────────

def test_handler_count_specific_event() -> None:
    bus = fresh()
    bus.on("ev", lambda **kw: None)
    bus.on("ev", lambda **kw: None)
    assert bus.handler_count("ev") == 2


def test_handler_count_all() -> None:
    bus = fresh()
    bus.on("a", lambda **kw: None)
    bus.on("b", lambda **kw: None)
    bus.on("b", lambda **kw: None)
    assert bus.handler_count() == 3


def test_handler_count_zero_for_unknown_event() -> None:
    bus = fresh()
    assert bus.handler_count("nonexistent") == 0


def test_subscribed_events_returns_sorted_list() -> None:
    bus = fresh()
    bus.on("c", lambda **kw: None)
    bus.on("a", lambda **kw: None)
    bus.on("b", lambda **kw: None)
    assert bus.subscribed_events() == ["a", "b", "c"]


def test_subscribed_events_empty_when_no_handlers() -> None:
    bus = fresh()
    assert bus.subscribed_events() == []


# ── Module-level singleton ────────────────────────────────────────────────────

def test_module_level_bus_is_eventbus_instance() -> None:
    from pygame_engine.events import bus
    from pygame_engine.events.event_bus import EventBus
    assert isinstance(bus, EventBus)


def test_module_level_bus_can_emit_and_receive() -> None:
    from pygame_engine.events import bus
    calls: list = []
    bus.on("test.singleton", lambda **kw: calls.append(1))
    bus.emit("test.singleton")
    bus.off("test.singleton", calls.append)   # attempt cleanup
    bus.clear("test.singleton")
    assert calls == [1]
