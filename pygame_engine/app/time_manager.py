"""
TimeManager centralises all time-related values for a running application.

Every frame the Application calls ``advance(raw_dt)`` with the raw delta
from the system clock. TimeManager applies ``time_scale`` and makes the
scaled and unscaled values available for that frame.

Scenes receive ``delta_time`` (scaled) so pausing the game simply means
setting ``time_scale = 0``. UI widgets, audio buses, and other systems
that must not pause should read ``unscaled_delta_time`` instead.

Usage::

    # In Application._loop():
    time_manager.advance(raw_ms / 1000.0)
    scene_manager.update(time_manager.delta_time)

    # Pause all game logic:
    app.time.time_scale.value = 0.0

    # Slow motion at half speed:
    app.time.time_scale.value = 0.5

    # Subscribe to time-scale changes (e.g. audio bus):
    app.time.time_scale.subscribe(lambda old, new: audio.set_pitch(new))

    # Fixed-rate physics callback:
    app.time.register_fixed_step(physics.step, rate=60)
"""

from __future__ import annotations

from typing import Callable

from pygame_engine.state.observable import Observable


class TimeManager:
    """
    Manages scaled and unscaled time for one application instance.

    Attributes
    ----------
    time_scale:
        ``Observable[float]``. Multiplier applied to raw delta time.
        ``1.0`` = normal speed, ``0.0`` = paused, ``0.5`` = half speed.
        Subscribers are notified when this value changes.
    delta_time:
        Scaled delta time for the most recent frame (seconds).
        Equal to ``unscaled_delta_time * time_scale``.
        Pass this to ``scene.update(dt)``.
    unscaled_delta_time:
        Raw delta time for the most recent frame (seconds), ignoring
        ``time_scale``. Use for UI animations, menus, and audio UI.
    time:
        Total scaled time elapsed since startup (seconds).
    unscaled_time:
        Total unscaled (wall-clock) time elapsed since startup (seconds).
    frame_count:
        Total number of frames advanced since startup or last reset.
    max_delta_time:
        Upper bound on raw_dt passed to ``advance()``.  Prevents the
        "spiral of death" after a long hitch (e.g. OS suspend).
        Set to ``0.0`` to disable clamping. Defaults to ``0.1`` (100 ms).
    """

    def __init__(self, max_delta_time: float = 0.1) -> None:
        """
        Args:
            max_delta_time: Maximum raw dt in seconds. ``0.0`` = no clamp.
        """
        self.time_scale: Observable[float] = Observable(1.0)
        """
        Multiplier applied to raw delta time each frame.

        Subscribe to react to pause/resume events::

            app.time.time_scale.subscribe(lambda old, new: ...)
        """

        self.delta_time:          float = 0.0
        self.unscaled_delta_time: float = 0.0
        self.time:                float = 0.0
        self.unscaled_time:       float = 0.0
        self.frame_count:         int   = 0
        self.max_delta_time:      float = max_delta_time

        # Fixed-step registry: list of (callback, interval_seconds, accumulator)
        self._fixed_steps: list[tuple[Callable[[], None], float, float]] = []

    # ── Core API ──────────────────────────────────────────────────────────────

    def advance(self, raw_dt: float) -> None:
        """
        Advance time by one frame.

        Clamps ``raw_dt`` to ``max_delta_time`` (when > 0), applies
        ``time_scale``, updates all accumulators, fires fixed-step
        callbacks, and increments ``frame_count``.

        Called once per frame by ``Application._loop()`` before
        ``scene_manager.update()``.

        Args:
            raw_dt: Elapsed seconds since the previous frame, as reported
                    by the system clock. Must be >= 0.
        """
        # Clamp raw delta to prevent spiral-of-death after hitches
        if self.max_delta_time > 0.0:
            raw_dt = min(raw_dt, self.max_delta_time)

        scale = self.time_scale.value
        scaled_dt = raw_dt * scale

        self.unscaled_delta_time = raw_dt
        self.delta_time          = scaled_dt
        self.unscaled_time      += raw_dt
        self.time               += scaled_dt
        self.frame_count        += 1

        # Fire fixed-step callbacks using scaled time
        for i, (cb, interval, accum) in enumerate(self._fixed_steps):
            accum += scaled_dt
            while accum >= interval:
                cb()
                accum -= interval
            self._fixed_steps[i] = (cb, interval, accum)

    def register_fixed_step(
        self,
        callback: Callable[[], None],
        rate: int = 60,
    ) -> None:
        """
        Register a callback that fires at a fixed rate each frame.

        The callback is driven by *scaled* time so it naturally pauses
        when ``time_scale`` is ``0.0``.

        Args:
            callback: Zero-argument callable to invoke at ``rate`` Hz.
            rate:     Target invocations per second. Defaults to 60.

        Raises:
            ValueError: If ``rate`` is not a positive integer.
        """
        if rate <= 0:
            raise ValueError(f"rate must be > 0, got {rate!r}")
        interval = 1.0 / rate
        self._fixed_steps.append((callback, interval, 0.0))

    def reset(self) -> None:
        """
        Reset all accumulators to zero.

        Does NOT change ``time_scale`` or ``max_delta_time``, and does NOT
        clear fixed-step registrations.  Useful for tests or editor
        play/stop cycles.
        """
        self.delta_time          = 0.0
        self.unscaled_delta_time = 0.0
        self.time                = 0.0
        self.unscaled_time       = 0.0
        self.frame_count         = 0
        # Reset fixed-step accumulators without removing registrations
        self._fixed_steps = [
            (cb, interval, 0.0) for cb, interval, _ in self._fixed_steps
        ]

    # ── Representation ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"TimeManager("
            f"time_scale={self.time_scale.value!r}, "
            f"time={self.time:.3f}, "
            f"frame_count={self.frame_count})"
        )
