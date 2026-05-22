"""
Tests for pygame_engine.state — Observable and RuntimeFlags.
"""

import gc
import weakref

import pytest

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

from pygame_engine.state.observable import Observable
from pygame_engine.state.runtime_flags import RuntimeFlags


# ── Observable — basic contract ───────────────────────────────────────────────

def test_observable_initial_value() -> None:
    o = Observable(42)
    assert o.value == 42


def test_observable_set_value_notifies_listener() -> None:
    received: list[tuple] = []
    o = Observable(0)
    o.subscribe(lambda old, new: received.append((old, new)))
    o.value = 10
    assert received == [(0, 10)]


def test_observable_same_value_does_not_notify() -> None:
    calls: list[int] = [0]
    o = Observable(5)
    o.subscribe(lambda old, new: calls.__setitem__(0, calls[0] + 1))
    o.value = 5
    assert calls[0] == 0


def test_observable_multiple_listeners() -> None:
    results: list[int] = []
    o = Observable(0)
    o.subscribe(lambda old, new: results.append(new * 1))
    o.subscribe(lambda old, new: results.append(new * 2))
    o.value = 3
    assert sorted(results) == [3, 6]


def test_observable_unsubscribe_stops_notifications() -> None:
    calls: list[int] = []
    o = Observable(0)

    def listener(old, new):
        calls.append(new)

    o.subscribe(listener)
    o.value = 1
    o.unsubscribe(listener)
    o.value = 2
    assert calls == [1]


def test_observable_unsubscribe_unknown_listener_is_noop() -> None:
    o = Observable(0)
    o.unsubscribe(lambda old, new: None)   # should not raise


def test_observable_subscribe_same_listener_twice_is_noop() -> None:
    calls: list[int] = []
    o = Observable(0)

    def listener(old, new):
        calls.append(new)

    o.subscribe(listener)
    o.subscribe(listener)
    o.value = 1
    assert calls == [1]   # only one call, not two


def test_observable_clear_listeners() -> None:
    calls: list[int] = []
    o = Observable(0)
    o.subscribe(lambda old, new: calls.append(new))
    o.clear_listeners()
    o.value = 99
    assert calls == []


def test_observable_set_silent_does_not_notify() -> None:
    calls: list[int] = []
    o = Observable(0)
    o.subscribe(lambda old, new: calls.append(new))
    o.set_silent(42)
    assert calls == []
    assert o.value == 42


def test_observable_listener_count() -> None:
    o = Observable(0)
    assert o.listener_count == 0
    o.subscribe(lambda old, new: None)
    o.subscribe(lambda old, new: None)
    assert o.listener_count == 2


def test_observable_repr() -> None:
    o = Observable(7)
    assert "7" in repr(o)


def test_observable_works_with_string_type() -> None:
    o: Observable[str] = Observable("hello")
    results: list[str] = []
    o.subscribe(lambda old, new: results.append(new))
    o.value = "world"
    assert results == ["world"]


def test_observable_works_with_bool_type() -> None:
    o: Observable[bool] = Observable(False)
    results: list[bool] = []
    o.subscribe(lambda old, new: results.append(new))
    o.value = True
    assert results == [True]


# ── Observable — subscriber signature ────────────────────────────────────────

def test_subscriber_receives_old_then_new() -> None:
    """Callback signature is (old_value, new_value)."""
    pairs: list[tuple] = []
    o = Observable(10)
    o.subscribe(lambda old, new: pairs.append((old, new)))
    o.value = 20
    assert pairs == [(10, 20)]


def test_subscriber_old_value_is_previous_value() -> None:
    """After multiple changes, each callback sees the value before that change."""
    history: list[tuple] = []
    o = Observable(0)
    o.subscribe(lambda old, new: history.append((old, new)))
    o.value = 1
    o.value = 2
    o.value = 3
    assert history == [(0, 1), (1, 2), (2, 3)]


# ── Observable — weak references ─────────────────────────────────────────────

def test_weak_ref_bound_method_auto_removed_on_gc() -> None:
    """Bound method subscription is dropped when owning object is deleted."""
    calls: list[int] = []
    o = Observable(0)

    class Owner:
        def handler(self, old, new):
            calls.append(new)

    owner = Owner()
    o.subscribe(owner.handler)
    assert o.listener_count == 1

    o.value = 1
    assert calls == [1]

    del owner
    gc.collect()

    o.value = 2
    assert calls == [1]          # no second call — owner gone
    assert o.listener_count == 0  # dead ref cleaned up


def test_weak_ref_multiple_owners_partial_gc() -> None:
    """Only deleted owners are removed; surviving owners still receive events."""
    calls_a: list[int] = []
    calls_b: list[int] = []
    o = Observable(0)

    class Owner:
        def __init__(self, log):
            self.log = log

        def handler(self, old, new):
            self.log.append(new)

    owner_a = Owner(calls_a)
    owner_b = Owner(calls_b)
    o.subscribe(owner_a.handler)
    o.subscribe(owner_b.handler)

    del owner_a
    gc.collect()

    o.value = 99
    assert calls_a == []     # owner_a gone
    assert calls_b == [99]   # owner_b still alive


def test_lambda_strong_ref_survives() -> None:
    """Lambdas and plain functions use strong refs and stay alive."""
    calls: list[int] = []
    o = Observable(0)

    fn = lambda old, new: calls.append(new)  # noqa: E731
    o.subscribe(fn)
    # fn held locally — strong ref keeps it alive
    o.value = 5
    assert calls == [5]


def test_listener_count_excludes_dead_refs() -> None:
    """listener_count reflects only live subscribers."""
    o = Observable(0)

    class Owner:
        def handler(self, old, new): pass

    owner = Owner()
    o.subscribe(owner.handler)
    assert o.listener_count == 1

    del owner
    gc.collect()

    assert o.listener_count == 0


# ── Observable — transaction batching ────────────────────────────────────────

def test_transaction_fires_once_on_exit() -> None:
    """Multiple changes inside a transaction fire a single notification."""
    events: list[tuple] = []
    o = Observable(0)
    o.subscribe(lambda old, new: events.append((old, new)))

    with o.transaction():
        o.value = 1
        o.value = 2
        o.value = 3

    assert len(events) == 1
    assert events[0] == (0, 3)


def test_transaction_no_event_if_value_unchanged() -> None:
    """Transaction with net-zero change fires no event."""
    events: list[tuple] = []
    o = Observable(5)
    o.subscribe(lambda old, new: events.append((old, new)))

    with o.transaction():
        o.value = 10
        o.value = 5   # back to start

    assert events == []


def test_transaction_reports_original_old_value() -> None:
    """Old value in event is the value before the transaction started."""
    events: list[tuple] = []
    o = Observable(100)
    o.subscribe(lambda old, new: events.append((old, new)))

    with o.transaction():
        o.value = 200
        o.value = 300

    assert events == [(100, 300)]


def test_nested_transaction_transparent() -> None:
    """Inner transaction does not fire; only outermost fires on exit."""
    events: list[tuple] = []
    o = Observable(0)
    o.subscribe(lambda old, new: events.append((old, new)))

    with o.transaction():
        o.value = 1
        with o.transaction():   # inner — transparent
            o.value = 2
        o.value = 3

    assert len(events) == 1
    assert events[0] == (0, 3)


def test_transaction_fires_after_normal_change() -> None:
    """Changes outside a transaction still fire immediately."""
    events: list[tuple] = []
    o = Observable(0)
    o.subscribe(lambda old, new: events.append((old, new)))

    o.value = 1           # immediate
    with o.transaction():
        o.value = 2
        o.value = 3       # deferred
    o.value = 4           # immediate

    assert events == [(0, 1), (1, 3), (3, 4)]


def test_transaction_single_change_fires() -> None:
    """A single change inside a transaction still fires on exit."""
    events: list[tuple] = []
    o = Observable(0)
    o.subscribe(lambda old, new: events.append((old, new)))

    with o.transaction():
        o.value = 42

    assert events == [(0, 42)]


def test_set_silent_inside_transaction_fires_on_exit() -> None:
    """
    set_silent inside a transaction suppresses the immediate notification
    but the transaction still fires on exit if the value changed.

    set_silent means "don't notify right now" — it does not mean "pretend
    this change never happened." The transaction compares the value at entry
    (0) with the value at exit (99) and fires once, which is correct.
    """
    events: list[tuple] = []
    o = Observable(0)
    o.subscribe(lambda old, new: events.append((old, new)))

    with o.transaction():
        o.set_silent(99)

    # Transaction fires once: (old=0, new=99)
    assert events == [(0, 99)]
    assert o.value == 99


# ── Observable — Hypothesis property-based tests ──────────────────────────────

if HAS_HYPOTHESIS:
    @given(values=st.lists(st.integers(), min_size=1, max_size=20))
    @settings(max_examples=200)
    def test_listener_count_never_negative(values) -> None:
        """listener_count is always >= 0."""
        o = Observable(0)
        for v in values:
            fn = lambda old, new: None  # noqa: E731
            o.subscribe(fn)
            o.unsubscribe(fn)
        assert o.listener_count >= 0

    @given(values=st.lists(st.integers(min_value=-1000, max_value=1000),
                           min_size=1, max_size=50))
    @settings(max_examples=200)
    def test_transaction_fires_at_most_once(values) -> None:
        """A single transaction block fires 0 or 1 events, never more."""
        events: list[int] = []
        o = Observable(values[0])
        o.subscribe(lambda old, new: events.append(1))

        with o.transaction():
            for v in values:
                o.value = v

        assert len(events) <= 1

    @given(
        start=st.integers(),
        changes=st.lists(st.integers(), min_size=0, max_size=30),
    )
    @settings(max_examples=200)
    def test_final_value_always_reachable(start, changes) -> None:
        """After any sequence of assignments, o.value == last assigned."""
        o = Observable(start)
        expected = start
        for v in changes:
            o.value = v
            expected = v
        assert o.value == expected

    @given(values=st.lists(st.integers(min_value=0, max_value=100),
                           min_size=2, max_size=30))
    @settings(max_examples=100)
    def test_subscriber_old_new_always_consistent(values) -> None:
        """Each callback's old == previously observed new."""
        history: list[tuple] = []
        o = Observable(values[0])
        o.subscribe(lambda old, new: history.append((old, new)))

        for v in values[1:]:
            o.value = v

        for i, (old, new) in enumerate(history):
            if i > 0:
                _, prev_new = history[i - 1]
                assert old == prev_new


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
