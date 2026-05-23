"""
Tests for pygame_engine.events.signals.Signal.
"""

from __future__ import annotations

import pytest

from pygame_engine.events.event_bus import EventBus
from pygame_engine.events.signals import Signal


def make_bus() -> EventBus:
    return EventBus()


# ── Construction ──────────────────────────────────────────────────────────────

def test_event_property_returns_name() -> None:
    bus = make_bus()
    sig = Signal("player.died", bus)
    assert sig.event == "player.died"


def test_repr_contains_event_name() -> None:
    bus = make_bus()
    sig = Signal("ui.clicked", bus)
    assert "ui.clicked" in repr(sig)


# ── connect / emit ────────────────────────────────────────────────────────────

def test_connect_handler_receives_emit() -> None:
    bus = make_bus()
    sig = Signal("test.event", bus)
    calls: list = []
    sig.connect(lambda **kw: calls.append(kw))
    sig.emit(value=42)
    assert calls == [{"value": 42}]


def test_emit_returns_handler_count() -> None:
    bus = make_bus()
    sig = Signal("test.event", bus)
    sig.connect(lambda **kw: None)
    sig.connect(lambda **kw: None)
    count = sig.emit()
    assert count == 2


def test_emit_returns_zero_with_no_handlers() -> None:
    bus = make_bus()
    sig = Signal("test.event", bus)
    assert sig.emit() == 0


def test_emit_kwargs_forwarded() -> None:
    bus = make_bus()
    sig = Signal("test.event", bus)
    received: list = []
    sig.connect(lambda x=None, y=None, **kw: received.append((x, y)))
    sig.emit(x=10, y=20)
    assert received == [(10, 20)]


# ── connect_once ──────────────────────────────────────────────────────────────

def test_connect_once_fires_once() -> None:
    bus = make_bus()
    sig = Signal("once.event", bus)
    calls: list = []
    sig.connect_once(lambda **kw: calls.append(1))
    sig.emit()
    sig.emit()
    assert calls == [1]


def test_connect_once_and_connect_coexist() -> None:
    bus = make_bus()
    sig = Signal("mixed.event", bus)
    permanent: list = []
    once_calls: list = []
    sig.connect(lambda **kw: permanent.append(1))
    sig.connect_once(lambda **kw: once_calls.append(1))
    sig.emit()
    sig.emit()
    assert permanent == [1, 1]
    assert once_calls == [1]


# ── disconnect ────────────────────────────────────────────────────────────────

def test_disconnect_returns_true_when_found() -> None:
    bus = make_bus()
    sig = Signal("test.event", bus)
    handler = lambda **kw: None
    sig.connect(handler)
    assert sig.disconnect(handler) is True


def test_disconnect_returns_false_when_not_registered() -> None:
    bus = make_bus()
    sig = Signal("test.event", bus)
    assert sig.disconnect(lambda **kw: None) is False


def test_disconnect_stops_handler_from_firing() -> None:
    bus = make_bus()
    sig = Signal("test.event", bus)
    calls: list = []
    handler = lambda **kw: calls.append(1)
    sig.connect(handler)
    sig.disconnect(handler)
    sig.emit()
    assert calls == []


# ── clear ────────────────────────────────────────────────────────────────────

def test_clear_removes_all_handlers() -> None:
    bus = make_bus()
    sig = Signal("clear.event", bus)
    calls: list = []
    sig.connect(lambda **kw: calls.append(1))
    sig.connect(lambda **kw: calls.append(2))
    sig.clear()
    sig.emit()
    assert calls == []


# ── multiple signals on same bus ──────────────────────────────────────────────

def test_two_signals_independent() -> None:
    bus = make_bus()
    a = Signal("event.a", bus)
    b = Signal("event.b", bus)
    a_calls: list = []
    b_calls: list = []
    a.connect(lambda **kw: a_calls.append(1))
    b.connect(lambda **kw: b_calls.append(1))
    a.emit()
    assert a_calls == [1]
    assert b_calls == []


def test_signal_uses_provided_bus() -> None:
    bus1 = make_bus()
    bus2 = make_bus()
    sig_on_1 = Signal("shared.event", bus1)
    calls: list = []
    bus2.on("shared.event", lambda **kw: calls.append(1))
    sig_on_1.emit()
    assert calls == []   # bus2 not affected
