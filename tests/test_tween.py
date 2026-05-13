"""
tests/test_tween.py

Tests for pygame_engine.animation.Tween.

Covers: start/stop/restart/complete/reverse, value interpolation,
easing application, loop and ping-pong modes, is_done flag.
"""

import pytest

from pygame_engine.animation.easing import ease_out_cubic, linear
from pygame_engine.animation.tween import Tween


# ── Construction ──────────────────────────────────────────────────────────────

def test_tween_not_running_by_default() -> None:
    t = Tween(0.0, 1.0, 1.0)
    assert t.is_running is False
    assert t.is_done    is False


def test_tween_auto_start() -> None:
    t = Tween(0.0, 1.0, 1.0, auto_start=True)
    assert t.is_running is True


def test_tween_zero_duration_raises() -> None:
    with pytest.raises(ValueError):
        Tween(0.0, 1.0, 0.0)


def test_tween_negative_duration_raises() -> None:
    with pytest.raises(ValueError):
        Tween(0.0, 1.0, -1.0)


# ── Value before start ────────────────────────────────────────────────────────

def test_value_at_start_before_running() -> None:
    t = Tween(5.0, 10.0, 1.0)
    assert t.value == 5.0


# ── Linear interpolation ──────────────────────────────────────────────────────

def test_linear_tween_midpoint() -> None:
    t = Tween(0.0, 100.0, 1.0, easing=linear, auto_start=True)
    t.update(0.5)
    assert abs(t.value - 50.0) < 1e-6


def test_linear_tween_at_end() -> None:
    t = Tween(0.0, 100.0, 1.0, easing=linear, auto_start=True)
    t.update(1.0)
    assert abs(t.value - 100.0) < 1e-6
    assert t.is_done    is True
    assert t.is_running is False


def test_tween_does_not_exceed_end_value() -> None:
    t = Tween(0.0, 1.0, 1.0, easing=linear, auto_start=True)
    t.update(5.0)
    assert t.value == 1.0


# ── Negative range ────────────────────────────────────────────────────────────

def test_tween_negative_range() -> None:
    t = Tween(100.0, 0.0, 1.0, easing=linear, auto_start=True)
    t.update(0.5)
    assert abs(t.value - 50.0) < 1e-6


# ── Easing applied ────────────────────────────────────────────────────────────

def test_ease_out_cubic_midpoint_above_linear() -> None:
    """ease_out_cubic at t=0.5 should be above the linear midpoint."""
    t = Tween(0.0, 1.0, 1.0, easing=ease_out_cubic, auto_start=True)
    t.update(0.5)
    assert t.value > 0.5


# ── Control methods ───────────────────────────────────────────────────────────

def test_stop_halts_value() -> None:
    t = Tween(0.0, 1.0, 1.0, easing=linear, auto_start=True)
    t.update(0.3)
    val = t.value
    t.stop()
    t.update(0.3)
    assert t.value == val


def test_restart_resets_to_start() -> None:
    t = Tween(0.0, 1.0, 1.0, easing=linear, auto_start=True)
    t.update(1.0)
    assert t.is_done is True
    t.restart()
    assert t.is_done    is False
    assert t.is_running is True
    assert t.value      == 0.0


def test_complete_jumps_to_end() -> None:
    t = Tween(0.0, 1.0, 1.0, easing=linear, auto_start=True)
    t.update(0.1)
    t.complete()
    assert t.value   == 1.0
    assert t.is_done is True


def test_reverse_swaps_start_and_end() -> None:
    t = Tween(0.0, 100.0, 1.0, easing=linear, auto_start=True)
    t.update(1.0)
    t.reverse()
    t.update(0.5)
    assert abs(t.value - 50.0) < 1e-6


# ── Progress ──────────────────────────────────────────────────────────────────

def test_progress_is_normalised() -> None:
    t = Tween(0.0, 1.0, 2.0, easing=linear, auto_start=True)
    t.update(1.0)
    assert abs(t.progress - 0.5) < 1e-6


# ── Loop ──────────────────────────────────────────────────────────────────────

def test_loop_restarts_after_done() -> None:
    t = Tween(0.0, 1.0, 1.0, easing=linear, auto_start=True, loop=True)
    t.update(1.5)
    assert t.is_done    is False
    assert t.is_running is True
    assert abs(t.progress - 0.5) < 1e-6


def test_loop_value_wraps_correctly() -> None:
    t = Tween(0.0, 100.0, 1.0, easing=linear, auto_start=True, loop=True)
    t.update(1.25)
    assert abs(t.value - 25.0) < 1e-6


# ── Ping-pong ─────────────────────────────────────────────────────────────────

def test_ping_pong_reverses_direction() -> None:
    t = Tween(0.0, 1.0, 1.0, easing=linear, auto_start=True, ping_pong=True)
    t.update(1.5)   # past the end, now going backward
    assert abs(t.value - 0.5) < 1e-6
