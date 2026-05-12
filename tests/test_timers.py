"""
tests/test_timers.py

Tests for pygame_engine.utils.timers — Timer and Cooldown.

Covers: start/stop/reset, progress, elapsed/remaining, Cooldown.fired
"""

from pygame_engine.utils.timers import Cooldown, Timer


# ── Timer ─────────────────────────────────────────────────────────────────────

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
    assert t.is_done  is True
    assert t.progress == 1.0
    assert t.remaining == 0.0


def test_timer_does_not_exceed_duration() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(5.0)
    assert t.elapsed  == 1.0
    assert t.progress == 1.0


def test_timer_stop_halts_progress() -> None:
    t = Timer(2.0, auto_start=True)
    t.update(0.5)
    t.stop()
    t.update(0.5)
    assert t.elapsed == 0.5


def test_timer_restart_resets_and_runs() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(1.0)
    assert t.is_done is True
    t.restart()
    assert t.is_done   is False
    assert t.elapsed   == 0.0
    assert t.is_running is True


def test_timer_reset_stops_and_clears() -> None:
    t = Timer(1.0, auto_start=True)
    t.update(0.5)
    t.reset()
    assert t.is_running is False
    assert t.elapsed    == 0.0


def test_timer_does_not_update_when_stopped() -> None:
    t = Timer(1.0)
    t.update(0.5)
    assert t.elapsed == 0.0


def test_timer_zero_duration_is_immediately_done() -> None:
    t = Timer(0.0, auto_start=True)
    assert t.is_done  is True
    assert t.progress == 1.0


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
    # Remainder 0.5 should be carried over — won't fire again until another 0.5s
    c.update(0.4)
    assert c.fired is False
    c.update(0.1)
    assert c.fired is True


def test_cooldown_does_not_fire_when_not_started() -> None:
    c = Cooldown(1.0)
    c.update(2.0)
    assert c.fired is False
