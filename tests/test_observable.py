"""
Dedicated tests for pygame_engine.state.observable.Observable.

test_state.py covers the Observable API via the state module. This file
focuses on internal machinery and edge cases not covered there.
"""

from __future__ import annotations

import gc

import pytest

from pygame_engine.state.observable import Observable, _make_ref, _deref, _ref_matches


# ── Internal helpers ──────────────────────────────────────────────────────────

def test_make_ref_lambda_is_strong() -> None:
    fn = lambda old, new: None
    kind, _ = _make_ref(fn)
    assert kind == "strong"


def test_make_ref_plain_function_is_strong() -> None:
    def fn(old, new): pass
    kind, _ = _make_ref(fn)
    assert kind == "strong"


def test_make_ref_bound_method_is_weak() -> None:
    class Owner:
        def handler(self, old, new): pass
    o = Owner()
    kind, _ = _make_ref(o.handler)
    assert kind == "weak"


def test_deref_strong_returns_callable() -> None:
    fn = lambda old, new: None
    entry = _make_ref(fn)
    assert _deref(entry) is fn


def test_deref_weak_live_returns_callable() -> None:
    class Owner:
        def handler(self, old, new): pass
    o = Owner()
    entry = _make_ref(o.handler)
    assert _deref(entry) is not None


def test_deref_weak_dead_returns_none() -> None:
    class Owner:
        def handler(self, old, new): pass
    o = Owner()
    entry = _make_ref(o.handler)
    del o
    gc.collect()
    assert _deref(entry) is None


def test_ref_matches_strong_true() -> None:
    fn = lambda old, new: None
    entry = _make_ref(fn)
    assert _ref_matches(entry, fn) is True


def test_ref_matches_different_callable_false() -> None:
    fn1 = lambda old, new: None
    fn2 = lambda old, new: None
    entry = _make_ref(fn1)
    assert _ref_matches(entry, fn2) is False


def test_ref_matches_dead_weak_false() -> None:
    class Owner:
        def handler(self, old, new): pass
    o = Owner()
    entry = _make_ref(o.handler)
    del o
    gc.collect()
    assert _ref_matches(entry, lambda: None) is False


# ── subscribe() return value ──────────────────────────────────────────────────

def test_subscribe_returns_listener_as_token() -> None:
    obs = Observable(0)
    fn = lambda old, new: None
    token = obs.subscribe(fn)
    assert token is fn


def test_subscribe_token_can_be_used_to_unsubscribe() -> None:
    obs = Observable(0)
    calls: list = []
    token = obs.subscribe(lambda old, new: calls.append(new))
    obs.unsubscribe(token)
    obs.value = 1
    assert calls == []


# ── Notification ordering ─────────────────────────────────────────────────────

def test_listeners_fire_in_registration_order() -> None:
    obs = Observable(0)
    order: list[int] = []
    obs.subscribe(lambda old, new: order.append(1))
    obs.subscribe(lambda old, new: order.append(2))
    obs.subscribe(lambda old, new: order.append(3))
    obs.value = 1
    assert order == [1, 2, 3]


def test_second_listener_sees_already_updated_value() -> None:
    obs = Observable(0)
    seen: list[int] = []
    obs.subscribe(lambda old, new: None)
    obs.subscribe(lambda old, new: seen.append(obs.value))
    obs.value = 42
    assert seen == [42]


# ── Exception propagation behaviour ──────────────────────────────────────────

def test_broken_listener_raises_and_stops_later_listeners() -> None:
    """
    Observable._notify() does NOT isolate exceptions. If a listener raises,
    the exception propagates immediately and later listeners do not fire.
    This is the documented behaviour — callers must not raise in listeners.
    """
    obs = Observable(0)
    later_called: list[bool] = []

    def bad(old, new):
        raise RuntimeError("deliberate error")

    obs.subscribe(bad)
    obs.subscribe(lambda old, new: later_called.append(True))

    with pytest.raises(RuntimeError, match="deliberate error"):
        obs.value = 5

    # Later listener was NOT called — exception stopped iteration
    assert later_called == []


# ── Dead-ref pruning during _notify ──────────────────────────────────────────

def test_dead_weak_ref_pruned_during_notify() -> None:
    obs = Observable(0)

    class Owner:
        def handler(self, old, new): pass

    o = Owner()
    obs.subscribe(o.handler)
    assert obs.listener_count == 1

    del o
    gc.collect()

    obs.value = 1
    assert obs.listener_count == 0


def test_live_listeners_still_fire_after_dead_ref_pruned() -> None:
    obs = Observable(0)
    calls: list[int] = []

    class Owner:
        def handler(self, old, new): pass

    o = Owner()
    obs.subscribe(o.handler)
    obs.subscribe(lambda old, new: calls.append(new))

    del o
    gc.collect()

    obs.value = 99
    assert calls == [99]


# ── set_silent edge cases ─────────────────────────────────────────────────────

def test_set_silent_updates_value_without_notify() -> None:
    obs = Observable(0)
    calls: list = []
    obs.subscribe(lambda old, new: calls.append(new))
    obs.set_silent(42)
    assert obs.value == 42
    assert calls == []


def test_set_silent_same_value_no_notify() -> None:
    obs = Observable(10)
    calls: list = []
    obs.subscribe(lambda old, new: calls.append(new))
    obs.set_silent(10)
    assert calls == []


def test_set_silent_inside_transaction_fires_on_exit() -> None:
    obs = Observable(0)
    calls: list = []
    obs.subscribe(lambda old, new: calls.append((old, new)))
    with obs.transaction():
        obs.set_silent(5)
        obs.value = 10
    assert calls == [(0, 10)]


# ── transaction() cleanup on exception ───────────────────────────────────────

def test_transaction_cleans_up_on_exception() -> None:
    obs = Observable(0)
    try:
        with obs.transaction():
            obs.value = 5
            raise ValueError("mid-transaction error")
    except ValueError:
        pass
    assert obs._in_transaction is False
    assert obs.value == 5


def test_transaction_usable_again_after_exception() -> None:
    obs = Observable(0)
    try:
        with obs.transaction():
            raise ValueError("error")
    except ValueError:
        pass
    calls: list = []
    obs.subscribe(lambda old, new: calls.append(new))
    with obs.transaction():
        obs.value = 7
    assert calls == [7]


# ── Type variants ─────────────────────────────────────────────────────────────

def test_observable_with_list_value() -> None:
    obs = Observable([1, 2, 3])
    calls: list = []
    obs.subscribe(lambda old, new: calls.append(new))
    obs.value = [4, 5, 6]
    assert calls == [[4, 5, 6]]


def test_observable_with_none_initial() -> None:
    obs: Observable[str | None] = Observable(None)
    assert obs.value is None
    calls: list = []
    obs.subscribe(lambda old, new: calls.append(new))
    obs.value = "hello"
    assert calls == ["hello"]


def test_observable_with_float() -> None:
    obs = Observable(0.0)
    calls: list = []
    obs.subscribe(lambda old, new: calls.append(new))
    obs.value = 0.5
    assert abs(calls[0] - 0.5) < 1e-9


def test_observable_with_tuple() -> None:
    obs = Observable((0, 0))
    calls: list = []
    obs.subscribe(lambda old, new: calls.append(new))
    obs.value = (1, 2)
    assert calls == [(1, 2)]


# ── listener_count with mixed refs ────────────────────────────────────────────

def test_listener_count_mixed_live_and_dead() -> None:
    obs = Observable(0)

    class Owner:
        def handler(self, old, new): pass

    o = Owner()
    obs.subscribe(o.handler)
    obs.subscribe(lambda old, new: None)

    assert obs.listener_count == 2
    del o
    gc.collect()
    assert obs.listener_count == 1


def test_listener_count_zero_after_clear() -> None:
    obs = Observable(0)
    obs.subscribe(lambda old, new: None)
    obs.subscribe(lambda old, new: None)
    obs.clear_listeners()
    assert obs.listener_count == 0


# ── repr ──────────────────────────────────────────────────────────────────────

def test_repr_int() -> None:
    assert repr(Observable(42)) == "Observable(42)"


def test_repr_string() -> None:
    assert repr(Observable("hello")) == "Observable('hello')"


def test_repr_updates_with_value() -> None:
    obs = Observable(0)
    obs.value = 99
    assert "99" in repr(obs)
