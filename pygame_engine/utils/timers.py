"""
Timer utilities for pygame_engine.

Provides lightweight time-tracking helpers used by animations, cooldowns,
timed feedback widgets, and any system that needs to measure elapsed time
or fire after a delay.

All timers are driven by delta-time passed from the frame loop — they do
not call pygame.time.get_ticks() internally, which keeps them testable
and predictable.
"""

from __future__ import annotations


class Timer:
    """
    Counts down from a duration and signals when it has elapsed.

    Usage::

        timer = Timer(2.0)          # 2-second timer
        timer.start()

        # Each frame:
        timer.update(dt)
        if timer.is_done:
            self._on_expired()

        # Reset and reuse:
        timer.restart()
    """

    def __init__(self, duration: float, auto_start: bool = False) -> None:
        """
        Args:
            duration:   How long the timer runs, in seconds.
            auto_start: If True, the timer starts immediately.
        """
        self._duration: float  = duration
        self._elapsed:  float  = 0.0
        self._running:  bool   = auto_start

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the timer from zero. Has no effect if already running."""
        if not self._running:
            self._elapsed = 0.0
            self._running = True

    def restart(self) -> None:
        """Reset elapsed time to zero and start running."""
        self._elapsed = 0.0
        self._running = True

    def stop(self) -> None:
        """Stop the timer without resetting elapsed time."""
        self._running = False

    def reset(self) -> None:
        """Stop the timer and reset elapsed time to zero."""
        self._running = False
        self._elapsed = 0.0

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Advance the timer by one frame.

        Does nothing if the timer is not running or is already done.

        Args:
            dt: Delta time in seconds.
        """
        if self._running and not self.is_done:
            self._elapsed += dt

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        """True if the timer is running (even if elapsed)."""
        return self._running

    @property
    def is_done(self) -> bool:
        """True if the timer has reached or exceeded its duration."""
        return self._elapsed >= self._duration

    @property
    def elapsed(self) -> float:
        """Elapsed time in seconds (clamped to duration)."""
        return min(self._elapsed, self._duration)

    @property
    def remaining(self) -> float:
        """Remaining time in seconds. Zero when done."""
        return max(0.0, self._duration - self._elapsed)

    @property
    def progress(self) -> float:
        """
        Normalised progress from 0.0 (start) to 1.0 (done).

        Useful for driving animations and interpolation.
        """
        if self._duration <= 0:
            return 1.0
        return min(self._elapsed / self._duration, 1.0)

    @property
    def duration(self) -> float:
        """The total duration of this timer in seconds."""
        return self._duration

    @duration.setter
    def duration(self, value: float) -> None:
        """Return the total duration of this timer in seconds."""
        self._duration = value


class Cooldown(Timer):
    """
    A timer that automatically restarts when done.

    Useful for repeating events: shooting intervals, footstep sounds,
    periodic spawns.

    Usage::

        cooldown = Cooldown(0.5, auto_start=True)  # fires every 0.5s

        # Each frame:
        cooldown.update(dt)
        if cooldown.fired:
            self._spawn_particle()
    """

    def __init__(self, interval: float, auto_start: bool = False) -> None:
        """
        Args:
            interval:   Time between firings in seconds.
            auto_start: If True, starts immediately.
        """
        super().__init__(interval, auto_start)
        self._fired: bool = False

    def update(self, dt: float) -> None:
        """Advance the cooldown. Auto-resets when interval elapses."""
        self._fired = False
        if not self._running:
            return
        self._elapsed += dt
        if self._elapsed >= self._duration:
            self._elapsed -= self._duration   # carry over remainder
            self._fired = True

    @property
    def fired(self) -> bool:
        """
        True for exactly one frame when the interval has elapsed.

        Check this each frame immediately after ``update(dt)``.
        """
        return self._fired