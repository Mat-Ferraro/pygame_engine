"""
Tests for pygame_engine.app.time_manager.TimeManager (CHANGE-05).

All tests are pure-Python — no pygame display required. TimeManager
itself has no pygame dependency.
"""

from __future__ import annotations

import pytest

from pygame_engine.app.time_manager import TimeManager


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_time_scale_is_one() -> None:
    tm = TimeManager()
    assert tm.time_scale.value == 1.0


def test_default_delta_time_is_zero() -> None:
    tm = TimeManager()
    assert tm.delta_time == 0.0


def test_default_unscaled_delta_time_is_zero() -> None:
    tm = TimeManager()
    assert tm.unscaled_delta_time == 0.0


def test_default_time_is_zero() -> None:
    tm = TimeManager()
    assert tm.time == 0.0


def test_default_unscaled_time_is_zero() -> None:
    tm = TimeManager()
    assert tm.unscaled_time == 0.0


def test_default_frame_count_is_zero() -> None:
    tm = TimeManager()
    assert tm.frame_count == 0


def test_default_max_delta_time() -> None:
    tm = TimeManager()
    assert tm.max_delta_time == 0.1


def test_custom_max_delta_time() -> None:
    tm = TimeManager(max_delta_time=0.05)
    assert tm.max_delta_time == 0.05


# ── advance() — basic behaviour ───────────────────────────────────────────────

def test_advance_increments_frame_count() -> None:
    tm = TimeManager()
    tm.advance(0.016)
    assert tm.frame_count == 1
    tm.advance(0.016)
    assert tm.frame_count == 2


def test_advance_sets_unscaled_delta_time() -> None:
    tm = TimeManager()
    tm.advance(0.016)
    assert abs(tm.unscaled_delta_time - 0.016) < 1e-9


def test_advance_sets_delta_time_at_scale_one() -> None:
    """With time_scale=1, delta_time == unscaled_delta_time."""
    tm = TimeManager()
    tm.advance(0.016)
    assert abs(tm.delta_time - 0.016) < 1e-9


def test_advance_accumulates_unscaled_time() -> None:
    tm = TimeManager()
    tm.advance(0.016)
    tm.advance(0.016)
    assert abs(tm.unscaled_time - 0.032) < 1e-9


def test_advance_accumulates_scaled_time() -> None:
    tm = TimeManager()
    tm.advance(0.016)
    tm.advance(0.016)
    assert abs(tm.time - 0.032) < 1e-9


# ── time_scale ────────────────────────────────────────────────────────────────

def test_time_scale_zero_gives_zero_delta() -> None:
    """time_scale=0 pauses game time; delta_time == 0."""
    tm = TimeManager()
    tm.time_scale.value = 0.0
    tm.advance(0.016)
    assert tm.delta_time == 0.0


def test_time_scale_zero_unscaled_still_advances() -> None:
    """Unscaled values are never affected by time_scale."""
    tm = TimeManager()
    tm.time_scale.value = 0.0
    tm.advance(0.016)
    assert abs(tm.unscaled_delta_time - 0.016) < 1e-9
    assert abs(tm.unscaled_time - 0.016) < 1e-9


def test_time_scale_half_speed() -> None:
    """time_scale=0.5 → delta_time is half the raw delta."""
    tm = TimeManager()
    tm.time_scale.value = 0.5
    tm.advance(0.016)
    assert abs(tm.delta_time - 0.008) < 1e-9


def test_time_scale_double_speed() -> None:
    """time_scale=2 → delta_time is double the raw delta."""
    tm = TimeManager()
    tm.time_scale.value = 2.0
    tm.advance(0.016)
    assert abs(tm.delta_time - 0.032) < 1e-9


def test_scaled_time_diverges_from_unscaled_at_half_speed() -> None:
    """After N frames at 0.5x, time == unscaled_time * 0.5."""
    tm = TimeManager()
    tm.time_scale.value = 0.5
    for _ in range(10):
        tm.advance(0.016)
    assert abs(tm.time - tm.unscaled_time * 0.5) < 1e-9


def test_time_scale_is_observable() -> None:
    """time_scale is an Observable; subscribers are notified on change."""
    changes: list[tuple[float, float]] = []
    tm = TimeManager()
    tm.time_scale.subscribe(lambda old, new: changes.append((old, new)))
    tm.time_scale.value = 0.0
    assert changes == [(1.0, 0.0)]


# ── max_delta_time clamping ───────────────────────────────────────────────────

def test_max_delta_time_clamps_large_hitch() -> None:
    """A 500 ms hitch is clamped to max_delta_time=0.1."""
    tm = TimeManager(max_delta_time=0.1)
    tm.advance(0.5)
    assert abs(tm.unscaled_delta_time - 0.1) < 1e-9


def test_max_delta_time_zero_disables_clamping() -> None:
    """max_delta_time=0 means no clamping."""
    tm = TimeManager(max_delta_time=0.0)
    tm.advance(0.5)
    assert abs(tm.unscaled_delta_time - 0.5) < 1e-9


def test_normal_frame_not_clamped() -> None:
    """A 16 ms frame is well under the 100 ms cap."""
    tm = TimeManager(max_delta_time=0.1)
    tm.advance(0.016)
    assert abs(tm.unscaled_delta_time - 0.016) < 1e-9


# ── register_fixed_step ───────────────────────────────────────────────────────

def test_fixed_step_fires_at_correct_rate() -> None:
    """A 60 Hz fixed step fires once per ~16.67 ms frame."""
    calls: list[int] = []
    tm = TimeManager()
    tm.register_fixed_step(lambda: calls.append(1), rate=60)

    # Advance exactly one 60 Hz interval
    tm.advance(1.0 / 60.0)
    assert len(calls) == 1


def test_fixed_step_fires_multiple_times_on_slow_frame() -> None:
    """A slow frame causes catch-up — 2 steps for a 2x interval."""
    calls: list[int] = []
    tm = TimeManager()
    tm.register_fixed_step(lambda: calls.append(1), rate=60)

    tm.advance(2.0 / 60.0)
    assert len(calls) == 2


def test_fixed_step_does_not_fire_on_short_frame() -> None:
    """A very short frame doesn't accumulate enough to fire."""
    calls: list[int] = []
    tm = TimeManager()
    tm.register_fixed_step(lambda: calls.append(1), rate=60)

    tm.advance(0.001)   # 1 ms — far short of 16.67 ms
    assert len(calls) == 0


def test_fixed_step_paused_when_time_scale_zero() -> None:
    """Fixed step uses scaled time — paused when time_scale == 0."""
    calls: list[int] = []
    tm = TimeManager()
    tm.time_scale.value = 0.0
    tm.register_fixed_step(lambda: calls.append(1), rate=60)

    tm.advance(1.0 / 60.0)   # raw delta would fire, but scale=0
    assert len(calls) == 0


def test_fixed_step_invalid_rate_raises() -> None:
    tm = TimeManager()
    with pytest.raises(ValueError):
        tm.register_fixed_step(lambda: None, rate=0)
    with pytest.raises(ValueError):
        tm.register_fixed_step(lambda: None, rate=-1)


# ── reset() ───────────────────────────────────────────────────────────────────

def test_reset_clears_accumulators() -> None:
    tm = TimeManager()
    tm.advance(0.016)
    tm.advance(0.016)
    tm.reset()
    assert tm.time == 0.0
    assert tm.unscaled_time == 0.0
    assert tm.delta_time == 0.0
    assert tm.unscaled_delta_time == 0.0
    assert tm.frame_count == 0


def test_reset_preserves_time_scale() -> None:
    """reset() does not touch time_scale."""
    tm = TimeManager()
    tm.time_scale.value = 0.5
    tm.reset()
    assert tm.time_scale.value == 0.5


def test_reset_preserves_max_delta_time() -> None:
    tm = TimeManager(max_delta_time=0.05)
    tm.reset()
    assert tm.max_delta_time == 0.05


def test_reset_preserves_fixed_step_registrations() -> None:
    """reset() resets fixed-step accumulators but keeps the callbacks."""
    calls: list[int] = []
    tm = TimeManager()
    tm.register_fixed_step(lambda: calls.append(1), rate=60)
    tm.advance(1.0 / 60.0)   # fires once
    tm.reset()
    tm.advance(1.0 / 60.0)   # should fire again after reset
    assert len(calls) == 2


# ── repr ──────────────────────────────────────────────────────────────────────

def test_repr_contains_key_fields() -> None:
    tm = TimeManager()
    r = repr(tm)
    assert "TimeManager" in r
    assert "time_scale" in r
    assert "frame_count" in r
