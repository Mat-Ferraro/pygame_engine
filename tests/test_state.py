"""
tests/test_state.py

Tests for pygame_engine.state — Observable and RuntimeFlags.
"""

import pytest

from pygame_engine.state.observable import Observable
from pygame_engine.state.runtime_flags import RuntimeFlags


# ── Observable ────────────────────────────────────────────────────────────────

def test_observable_initial_value() -> None:
    o = Observable(42)
    assert o.value == 42


def test_observable_set_value_notifies_listener() -> None:
    received: list[tuple] = []
    o = Observable(0)
    o.subscribe(lambda new, old: received.append((new, old)))
    o.value = 10
    assert received == [(10, 0)]


def test_observable_same_value_does_not_notify() -> None:
    calls: list[int] = []
    o = Observable(5)
    o.subscribe(lambda n, _: calls.append(n))
    o.value = 5
    assert calls == []


def test_observable_multiple_listeners() -> None:
    results: list[int] = []
    o = Observable(0)
    o.subscribe(lambda n, _: results.append(n * 1))
    o.subscribe(lambda n, _: results.append(n * 2))
    o.value = 3
    assert sorted(results) == [3, 6]


def test_observable_unsubscribe_stops_notifications() -> None:
    calls: list[int] = []
    o = Observable(0)

    def listener(new, old):
        calls.append(new)

    o.subscribe(listener)
    o.value = 1
    o.unsubscribe(listener)
    o.value = 2
    assert calls == [1]


def test_observable_unsubscribe_unknown_listener_is_noop() -> None:
    o = Observable(0)
    o.unsubscribe(lambda n, _: None)   # should not raise


def test_observable_subscribe_same_listener_twice_is_noop() -> None:
    calls: list[int] = []
    o = Observable(0)

    def listener(new, old):
        calls.append(new)

    o.subscribe(listener)
    o.subscribe(listener)
    o.value = 1
    assert calls == [1]   # only one call, not two


def test_observable_clear_listeners() -> None:
    calls: list[int] = []
    o = Observable(0)
    o.subscribe(lambda n, _: calls.append(n))
    o.clear_listeners()
    o.value = 99
    assert calls == []


def test_observable_set_silent_does_not_notify() -> None:
    calls: list[int] = []
    o = Observable(0)
    o.subscribe(lambda n, _: calls.append(n))
    o.set_silent(42)
    assert calls == []
    assert o.value == 42


def test_observable_listener_count() -> None:
    o = Observable(0)
    assert o.listener_count == 0
    o.subscribe(lambda n, _: None)
    o.subscribe(lambda n, _: None)
    assert o.listener_count == 2


def test_observable_repr() -> None:
    o = Observable(7)
    assert "7" in repr(o)


def test_observable_works_with_string_type() -> None:
    o: Observable[str] = Observable("hello")
    results: list[str] = []
    o.subscribe(lambda n, _: results.append(n))
    o.value = "world"
    assert results == ["world"]


def test_observable_works_with_bool_type() -> None:
    o: Observable[bool] = Observable(False)
    results: list[bool] = []
    o.subscribe(lambda n, _: results.append(n))
    o.value = True
    assert results == [True]


# ── RuntimeFlags ──────────────────────────────────────────────────────────────

def test_flags_all_false_by_default() -> None:
    f = RuntimeFlags()
    assert f.debug        is False
    assert f.show_fps     is False
    assert f.show_rects   is False
    assert f.show_overlay is False


def test_flags_can_be_set() -> None:
    f = RuntimeFlags()
    f.debug = True
    assert f.debug is True


def test_flags_toggle_flips_value() -> None:
    f = RuntimeFlags()
    result = f.toggle("debug")
    assert result is True
    assert f.debug is True
    result = f.toggle("debug")
    assert result is False


def test_flags_toggle_unknown_raises() -> None:
    f = RuntimeFlags()
    with pytest.raises(AttributeError):
        f.toggle("nonexistent_flag")


def test_flags_reset_clears_all() -> None:
    f = RuntimeFlags()
    f.debug = True
    f.show_fps = True
    f.reset()
    assert f.debug    is False
    assert f.show_fps is False


def test_flags_enable_debug_all() -> None:
    f = RuntimeFlags()
    f.enable_debug_all()
    assert f.debug        is True
    assert f.show_fps     is True
    assert f.show_rects   is True
    assert f.show_overlay is True


def test_flags_as_dict_returns_all_flags() -> None:
    f = RuntimeFlags()
    d = f.as_dict()
    assert "debug"        in d
    assert "show_fps"     in d
    assert "show_rects"   in d
    assert "show_overlay" in d


def test_flags_repr_shows_active_flags() -> None:
    f = RuntimeFlags()
    f.debug = True
    r = repr(f)
    assert "debug=True" in r


def test_flags_repr_shows_all_false_when_none_active() -> None:
    f = RuntimeFlags()
    assert "all False" in repr(f)
