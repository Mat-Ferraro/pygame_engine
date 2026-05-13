"""
animation/tween.py

Tween — single-value animator for pygame_engine.

A Tween moves a float from ``start`` to ``end`` over ``duration`` seconds
using a chosen easing function. It is driven by ``update(dt)`` each frame
and exposes a ``value`` property that callers read and apply to whatever
they are animating.

Design rules
------------
- No magic property binding. Callers read ``value`` and use it explicitly.
  This keeps Tweens predictable and easy to debug.
- A Tween does not know what it is animating. It animates a number.
- Looping and ping-pong are opt-in.

Usage::

    from pygame_engine.animation.tween import Tween
    from pygame_engine.animation.easing import ease_out_cubic

    # Fade in over 0.3 seconds
    fade = Tween(start=0.0, end=1.0, duration=0.3,
                 easing=ease_out_cubic, auto_start=True)

    # Each frame:
    fade.update(dt)
    my_surface.set_alpha(int(fade.value * 255))

    # Slide a rect from x=−200 to x=0
    slide = Tween(start=-200, end=0, duration=0.4,
                  easing=ease_out_back, auto_start=True)
    slide.update(dt)
    rect.x = int(slide.value)
"""

from __future__ import annotations

from typing import Callable

from pygame_engine.animation.easing import linear


class Tween:
    """
    Animates a single float value from ``start`` to ``end`` over time.

    State machine
    -------------
    idle → running → done  (no loop)
    idle → running → done → running → ...  (loop=True)
    idle → running → done → running (reversed) → ...  (ping_pong=True)

    ``is_done`` becomes True when the tween reaches the end value.
    With looping enabled it resets automatically.
    """

    def __init__(
        self,
        start:      float,
        end:        float,
        duration:   float,
        easing:     Callable[[float], float] = linear,
        auto_start: bool  = False,
        loop:       bool  = False,
        ping_pong:  bool  = False,
    ) -> None:
        """
        Args:
            start:      Initial value.
            end:        Target value.
            duration:   Duration in seconds. Must be > 0.
            easing:     Easing function (t: float) -> float.
                        Defaults to ``linear``.
            auto_start: If True, starts immediately on construction.
            loop:       If True, restarts from ``start`` when done.
            ping_pong:  If True, reverses direction each cycle instead
                        of jumping back to start. Implies loop behaviour.
        """
        if duration <= 0:
            raise ValueError(f"Tween duration must be > 0, got {duration}")

        self._start:     float                    = start
        self._end:       float                    = end
        self._duration:  float                    = duration
        self._easing:    Callable[[float], float] = easing
        self._loop:      bool                     = loop
        self._ping_pong: bool                     = ping_pong

        self._elapsed:   float = 0.0
        self._running:   bool  = False
        self._done:      bool  = False
        self._forward:   bool  = True   # direction for ping-pong

        if auto_start:
            self.start()

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the tween from the beginning. No-op if already running."""
        if not self._running:
            self._elapsed = 0.0
            self._running = True
            self._done    = False
            self._forward = True

    def restart(self) -> None:
        """Reset and start the tween regardless of current state."""
        self._elapsed = 0.0
        self._running = True
        self._done    = False
        self._forward = True

    def stop(self) -> None:
        """Stop the tween at its current value."""
        self._running = False

    def complete(self) -> None:
        """Jump immediately to the end value and mark as done."""
        self._elapsed = self._duration
        self._running = False
        self._done    = True

    def reverse(self) -> None:
        """
        Swap start and end values and restart.

        Useful for animating out after animating in.
        """
        self._start, self._end = self._end, self._start
        self.restart()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Advance the tween by one frame.

        Args:
            dt: Delta time in seconds.
        """
        if not self._running or self._done:
            return

        self._elapsed += dt

        if self._elapsed >= self._duration:
            if self._ping_pong:
                self._elapsed -= self._duration
                # Swap direction
                self._start, self._end = self._end, self._start
                self._forward = not self._forward
            elif self._loop:
                self._elapsed -= self._duration
            else:
                self._elapsed = self._duration
                self._running = False
                self._done    = True

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def value(self) -> float:
        """
        The current animated value.

        Computed from the easing function applied to normalised progress.
        Returns ``start`` before the tween begins and ``end`` when done.
        """
        if self._duration <= 0:
            return self._end
        t = min(self._elapsed / self._duration, 1.0)
        eased = self._easing(t)
        return self._start + (self._end - self._start) * eased

    @property
    def progress(self) -> float:
        """Normalised elapsed time, 0.0 → 1.0. Not eased."""
        if self._duration <= 0:
            return 1.0
        return min(self._elapsed / self._duration, 1.0)

    @property
    def is_running(self) -> bool:
        """True while the tween is actively animating."""
        return self._running

    @property
    def is_done(self) -> bool:
        """True when the tween has reached its end value (no looping)."""
        return self._done

    # ── Configuration ─────────────────────────────────────────────────────────

    @property
    def start_value(self) -> float:
        return self._start

    @property
    def end_value(self) -> float:
        return self._end

    @property
    def duration(self) -> float:
        return self._duration
