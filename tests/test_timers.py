"""
tests/test_timers.py

Tests for pygame_engine.utils.timers — Timer and Cooldown.

Covers: start/stop/reset/restart, progress, elapsed/remaining,
is_done, Cooldown.fired and carry-over remainder.
"""

from pygame_engine.utils.timers import Cooldown, Timer


# ── Timer — initial state ─────────────────────────────────────────────────────

def test_timer_not_running_by_default() -> None:
    t = Timer(1.0)
    assert t.is_running is False
    assert t.is_done    is False


def test_timer_auto_start() -> None:
    t = Timer(1.0, auto_start=True)
    assert t.is_running is True


def test_timer_progress_before_start_is_zero() -> None:
    t = Timer(2.0)
    assert t.progress == 0.0


def test_timer_elapsed_before_start_is_zero() -> None:
    t = Timer(1.0)
    assert t.elapsed == 0.0


def test_timer_remaining_before_start_equals_duration() -> None:
    t = Timer(2.0)
    assert t.remaining == 2.0


# ── Timer — update behaviour ──────────────────────────────────────────────────

def test_timer_counts_up_correctly() -> None:
    t = Timer(2.0, auto_start=True)
    t.update(1.0)
    assert t.elapsed   == 1.0
    assert t.remaining == 1.0
    assert t.progress  == 0.5
    assert t.is_done   is False


def test_timer_done_when_elapsed_equals_duration() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(1.0)
    assert t.is_done   is True
    assert t.progress  == 1.0
    assert t.remaining == 0.0


def test_timer_does_not_exceed_duration() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(5.0)
    assert t.elapsed  == 1.0
    assert t.progress == 1.0


def test_timer_does_not_update_when_stopped() -> None:
    t = Timer(1.0)
    t.update(0.5)
    assert t.elapsed == 0.0


def test_timer_does_not_update_when_done() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(1.0)
    assert t.is_done is True
    t.update(5.0)
    assert t.elapsed == 1.0   # clamped — not advancing past done


# ── Timer — control methods ───────────────────────────────────────────────────

def test_timer_stop_halts_progress() -> None:
    t = Timer(2.0, auto_start=True)
    t.update(0.5)
    t.stop()
    t.update(0.5)
    assert t.elapsed == 0.5


def test_timer_stop_does_not_reset_elapsed() -> None:
    t = Timer(2.0, auto_start=True)
    t.update(0.8)
    t.stop()
    assert t.elapsed == 0.8


def test_timer_restart_resets_and_runs() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(1.0)
    assert t.is_done is True
    t.restart()
    assert t.is_done    is False
    assert t.elapsed    == 0.0
    assert t.is_running is True


def test_timer_reset_stops_and_clears() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(0.5)
    t.reset()
    assert t.is_running is False
    assert t.elapsed    == 0.0
    assert t.is_done    is False


def test_timer_start_from_idle() -> None:
    t = Timer(1.0)
    t.start()
    t.update(0.3)
    assert t.elapsed == 0.3


def test_timer_start_while_running_has_no_effect() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(0.4)
    t.start()   # already running
    t.update(0.3)
    assert abs(t.elapsed - 0.7) < 1e-6


# ── Timer — edge cases ────────────────────────────────────────────────────────

def test_timer_zero_duration_is_immediately_done() -> None:
    t = Timer(0.0, auto_start=True)
    assert t.is_done  is True
    assert t.progress == 1.0


def test_timer_duration_property() -> None:
    t = Timer(3.5)
    assert t.duration == 3.5


def test_timer_duration_setter() -> None:
    t = Timer(1.0)
    t.duration = 2.0
    assert t.duration == 2.0


def test_timer_progress_at_quarter() -> None:
    t = Timer(4.0, auto_start=True)
    t.update(1.0)
    assert abs(t.progress - 0.25) < 1e-6


# ── Cooldown ──────────────────────────────────────────────────────────────────

def test_cooldown_does_not_fire_before_interval() -> None:
    c = Cooldown(1.0, auto_start=True)
    c.update(0.5)
    assert c.fired is False


def test_cooldown_fires_when_interval_elapses() -> None:
    c = Cooldown(1.0, auto_start=True)
    c.update(1.0)
    assert c.fired is True


def test_cooldown_fired_is_false_next_frame() -> None:
    c = Cooldown(1.0, auto_start=True)
    c.update(1.0)
    assert c.fired is True
    c.update(0.0)
    assert c.fired is False


def test_cooldown_carries_over_remainder() -> None:
    c = Cooldown(1.0, auto_start=True)
    c.update(1.5)
    assert c.fired is True
    c.update(0.4)
    assert c.fired is False
    c.update(0.1)
    assert c.fired is True


def test_cooldown_does_not_fire_when_not_started() -> None:
    c = Cooldown(1.0)
    c.update(2.0)
    assert c.fired is False


def test_cooldown_stop_prevents_firing() -> None:
    c = Cooldown(0.5, auto_start=True)
    c.stop()
    c.update(1.0)
    assert c.fired is False


def test_cooldown_restart_resets_and_fires_again() -> None:
    c = Cooldown(0.5, auto_start=True)
    c.update(0.5)
    assert c.fired is True
    c.restart()
    c.update(0.3)
    assert c.fired is False
    c.update(0.2)
    assert c.fired is True
