"""
Tests for CHANGE-08: Extension hooks on Application.

Hooks are tested without running the full pygame loop — we call
_startup/_loop/_shutdown surrogates or invoke _fire_hook directly.
Application construction is always side-effect-free so hook registration
can be tested without pygame init.
"""

from __future__ import annotations

import pytest

from pygame_engine.app import Application, AppConfig


# ── add_hook — validation ─────────────────────────────────────────────────────

def test_add_hook_invalid_name_raises() -> None:
    """Registering on an unknown hook name raises ValueError."""
    app = Application()
    with pytest.raises(ValueError, match="Unknown hook"):
        app.add_hook("nonexistent_hook", lambda: None)


def test_add_hook_valid_names_do_not_raise() -> None:
    """All six valid hook names are accepted."""
    app = Application()
    noop = lambda: None
    for name in ("startup", "shutdown", "pre_update", "post_update",
                 "pre_render", "post_render"):
        app.add_hook(name, noop)   # should not raise


# ── remove_hook ───────────────────────────────────────────────────────────────

def test_remove_hook_returns_true_when_found() -> None:
    app = Application()
    cb = lambda: None
    app.add_hook("startup", cb)
    assert app.remove_hook("startup", cb) is True


def test_remove_hook_returns_false_when_not_registered() -> None:
    app = Application()
    assert app.remove_hook("startup", lambda: None) is False


def test_remove_hook_invalid_name_raises() -> None:
    app = Application()
    with pytest.raises(ValueError, match="Unknown hook"):
        app.remove_hook("bad_name", lambda: None)


def test_remove_hook_stops_callback_from_firing() -> None:
    """Callback must not fire after removal."""
    calls: list[str] = []
    app = Application()
    cb = lambda: calls.append("x")
    app.add_hook("startup", cb)
    app.remove_hook("startup", cb)
    app._fire_hook("startup")
    assert calls == []


# ── firing order — priority ───────────────────────────────────────────────────

def test_hooks_fire_in_registration_order_at_equal_priority() -> None:
    """Equal-priority hooks fire in the order they were registered."""
    order: list[int] = []
    app = Application()
    app.add_hook("startup", lambda: order.append(1))
    app.add_hook("startup", lambda: order.append(2))
    app.add_hook("startup", lambda: order.append(3))
    app._fire_hook("startup")
    assert order == [1, 2, 3]


def test_higher_priority_fires_later() -> None:
    """Higher priority number means the hook runs after lower-priority hooks."""
    order: list[int] = []
    app = Application()
    app.add_hook("startup", lambda: order.append(10), priority=10)
    app.add_hook("startup", lambda: order.append(0),  priority=0)
    app.add_hook("startup", lambda: order.append(5),  priority=5)
    app._fire_hook("startup")
    assert order == [0, 5, 10]


def test_negative_priority_fires_first() -> None:
    order: list[int] = []
    app = Application()
    app.add_hook("startup", lambda: order.append(0),   priority=0)
    app.add_hook("startup", lambda: order.append(-10), priority=-10)
    app._fire_hook("startup")
    assert order == [-10, 0]


def test_mixed_priority_with_equal_groups() -> None:
    """Within equal-priority groups, registration order is preserved."""
    order: list[str] = []
    app = Application()
    app.add_hook("startup", lambda: order.append("a1"), priority=0)
    app.add_hook("startup", lambda: order.append("a2"), priority=0)
    app.add_hook("startup", lambda: order.append("b"),  priority=1)
    app._fire_hook("startup")
    assert order == ["a1", "a2", "b"]


# ── hook arguments ────────────────────────────────────────────────────────────

def test_pre_update_receives_dt() -> None:
    """pre_update callbacks receive the dt float argument."""
    received: list[float] = []
    app = Application()
    app.add_hook("pre_update", lambda dt: received.append(dt))
    app._fire_hook("pre_update", 0.016)
    assert len(received) == 1
    assert abs(received[0] - 0.016) < 1e-9


def test_post_update_receives_dt() -> None:
    received: list[float] = []
    app = Application()
    app.add_hook("post_update", lambda dt: received.append(dt))
    app._fire_hook("post_update", 0.033)
    assert abs(received[0] - 0.033) < 1e-9


def test_pre_render_receives_surface() -> None:
    """pre_render callbacks receive the display surface."""
    import pygame
    surfaces: list = []
    app = Application()
    app.add_hook("pre_render", lambda s: surfaces.append(s))
    fake = pygame.Surface((10, 10))
    app._fire_hook("pre_render", fake)
    assert surfaces == [fake]


def test_post_render_receives_surface() -> None:
    import pygame
    surfaces: list = []
    app = Application()
    app.add_hook("post_render", lambda s: surfaces.append(s))
    fake = pygame.Surface((10, 10))
    app._fire_hook("post_render", fake)
    assert surfaces == [fake]


def test_startup_callback_takes_no_args() -> None:
    called: list[bool] = []
    app = Application()
    app.add_hook("startup", lambda: called.append(True))
    app._fire_hook("startup")
    assert called == [True]


def test_shutdown_callback_takes_no_args() -> None:
    called: list[bool] = []
    app = Application()
    app.add_hook("shutdown", lambda: called.append(True))
    app._fire_hook("shutdown")
    assert called == [True]


# ── multiple hooks fire independently ─────────────────────────────────────────

def test_multiple_hooks_registered_on_same_name_all_fire() -> None:
    calls: list[int] = []
    app = Application()
    for i in range(5):
        app.add_hook("pre_update", lambda dt, i=i: calls.append(i))
    app._fire_hook("pre_update", 0.016)
    assert len(calls) == 5


def test_hooks_on_different_names_do_not_cross_fire() -> None:
    """Firing pre_update must not invoke post_update callbacks."""
    pre_calls: list[int] = []
    post_calls: list[int] = []
    app = Application()
    app.add_hook("pre_update",  lambda dt: pre_calls.append(1))
    app.add_hook("post_update", lambda dt: post_calls.append(1))
    app._fire_hook("pre_update", 0.016)
    assert pre_calls == [1]
    assert post_calls == []


# ── hook state at construction ────────────────────────────────────────────────

def test_hooks_dict_initialised_at_construction() -> None:
    """All hook buckets exist immediately after construction."""
    app = Application()
    for name in ("startup", "shutdown", "pre_update", "post_update",
                 "pre_render", "post_render"):
        assert name in app._hooks
        assert app._hooks[name] == []


def test_fire_empty_hook_does_not_raise() -> None:
    """Firing a hook with no registered callbacks is a no-op."""
    app = Application()
    app._fire_hook("startup")         # no callbacks — should not raise
    app._fire_hook("pre_update", 0.0)
