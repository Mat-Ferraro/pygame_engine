"""
Tests for pygame_engine.state.subscription_group — SubscriptionGroup.
"""

import pytest

from pygame_engine.state.observable import Observable
from pygame_engine.state.subscription_group import SubscriptionGroup


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_subscription_count_is_zero() -> None:
    g = SubscriptionGroup()
    assert g.subscription_count == 0


def test_repr_contains_count() -> None:
    g = SubscriptionGroup()
    assert "0" in repr(g)


# ── on() ─────────────────────────────────────────────────────────────────────

def test_on_subscribes_and_receives_events() -> None:
    calls: list[int] = []
    o = Observable(0)
    g = SubscriptionGroup()
    g.on(o, lambda old, new: calls.append(new))
    o.value = 42
    assert calls == [42]


def test_on_increments_count() -> None:
    o1 = Observable(0)
    o2 = Observable(0)
    g  = SubscriptionGroup()
    g.on(o1, lambda old, new: None)
    g.on(o2, lambda old, new: None)
    assert g.subscription_count == 2


def test_on_multiple_observables() -> None:
    a_calls: list[int] = []
    b_calls: list[int] = []
    oa = Observable(0)
    ob = Observable(0)
    g  = SubscriptionGroup()
    g.on(oa, lambda old, new: a_calls.append(new))
    g.on(ob, lambda old, new: b_calls.append(new))
    oa.value = 1
    ob.value = 2
    assert a_calls == [1]
    assert b_calls == [2]


# ── add() ─────────────────────────────────────────────────────────────────────

def test_add_tracks_existing_token() -> None:
    calls: list[int] = []
    o = Observable(0)
    g = SubscriptionGroup()

    fn = lambda old, new: calls.append(new)  # noqa: E731
    token = o.subscribe(fn)
    g.add(o, token)

    assert g.subscription_count == 1
    o.value = 7
    assert calls == [7]


def test_add_then_dispose_unsubscribes() -> None:
    calls: list[int] = []
    o = Observable(0)
    g = SubscriptionGroup()

    fn = lambda old, new: calls.append(new)  # noqa: E731
    token = o.subscribe(fn)
    g.add(o, token)
    g.dispose()

    o.value = 99
    assert calls == []


# ── dispose() ─────────────────────────────────────────────────────────────────

def test_dispose_unsubscribes_all() -> None:
    calls: list[int] = []
    o = Observable(0)
    g = SubscriptionGroup()
    g.on(o, lambda old, new: calls.append(new))
    g.on(o, lambda old, new: calls.append(new * 2))

    g.dispose()
    o.value = 5
    assert calls == []


def test_dispose_resets_count_to_zero() -> None:
    o = Observable(0)
    g = SubscriptionGroup()
    g.on(o, lambda old, new: None)
    g.on(o, lambda old, new: None)
    g.dispose()
    assert g.subscription_count == 0


def test_dispose_is_idempotent() -> None:
    """Calling dispose twice does not raise."""
    o = Observable(0)
    g = SubscriptionGroup()
    g.on(o, lambda old, new: None)
    g.dispose()
    g.dispose()   # should not raise


def test_dispose_allows_reuse() -> None:
    """After dispose, the group can track new subscriptions."""
    calls: list[int] = []
    o = Observable(0)
    g = SubscriptionGroup()

    g.on(o, lambda old, new: None)
    g.dispose()

    g.on(o, lambda old, new: calls.append(new))
    o.value = 10
    assert calls == [10]


# ── Scene integration ─────────────────────────────────────────────────────────

def test_scene_has_subscriptions_attribute() -> None:
    """Scene base class provides self.subscriptions: SubscriptionGroup."""
    from pygame_engine.scene import Scene
    scene = Scene()
    assert isinstance(scene.subscriptions, SubscriptionGroup)


def test_scene_on_exit_disposes_subscriptions() -> None:
    """Scene.on_exit() cancels all subscriptions in self.subscriptions."""
    from pygame_engine.scene import Scene

    calls: list[int] = []
    o = Observable(0)

    class TestScene(Scene):
        def on_enter(self) -> None:
            self.subscriptions.on(o, lambda old, new: calls.append(new))

    scene = TestScene()
    scene.on_enter()
    o.value = 1
    assert calls == [1]

    scene.on_exit()
    o.value = 2
    assert calls == [1]   # no call after exit


def test_scene_subclass_on_exit_with_super() -> None:
    """Subclass on_exit calling super() still disposes subscriptions."""
    from pygame_engine.scene import Scene

    calls: list[int] = []
    cleanup: list[str] = []
    o = Observable(0)

    class MyScene(Scene):
        def on_enter(self) -> None:
            self.subscriptions.on(o, lambda old, new: calls.append(new))

        def on_exit(self) -> None:
            super().on_exit()
            cleanup.append("cleaned")

    scene = MyScene()
    scene.on_enter()
    o.value = 5
    scene.on_exit()
    o.value = 6

    assert calls == [5]
    assert cleanup == ["cleaned"]


def test_scene_init_creates_fresh_group_per_instance() -> None:
    """Each Scene instance has its own independent SubscriptionGroup."""
    from pygame_engine.scene import Scene

    s1, s2 = Scene(), Scene()
    assert s1.subscriptions is not s2.subscriptions


# ── Mixing on() and add() ─────────────────────────────────────────────────────

def test_mix_on_and_add() -> None:
    calls: list[int] = []
    o1 = Observable(0)
    o2 = Observable(0)
    g  = SubscriptionGroup()

    g.on(o1, lambda old, new: calls.append(new))

    fn = lambda old, new: calls.append(new * 10)  # noqa: E731
    token = o2.subscribe(fn)
    g.add(o2, token)

    o1.value = 1
    o2.value = 2
    assert sorted(calls) == [1, 20]

    g.dispose()
    o1.value = 9
    o2.value = 9
    assert sorted(calls) == [1, 20]   # no new calls after dispose
