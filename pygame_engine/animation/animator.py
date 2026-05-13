"""
animation/animator.py

Sprite animation data and playback for pygame_engine.

Two classes:

``SpriteAnimation`` — immutable data: a named list of frames and timing.
``AnimationPlayer`` — mutable playback state: current frame, elapsed time.

Typical usage::

    from pygame_engine.animation.animator import SpriteAnimation, AnimationPlayer

    # Load frames from a spritesheet (via AssetLoader)
    frames = app.assets.spritesheet("player.png", 48, 48)

    # Define named animations from frame slices
    idle_anim = SpriteAnimation("idle", frames[0:4],  frame_duration=0.15)
    run_anim  = SpriteAnimation("run",  frames[4:12], frame_duration=0.08)
    jump_anim = SpriteAnimation("jump", frames[12:16],frame_duration=0.1,
                                loop=False)

    # Create a player and register animations
    player = AnimationPlayer()
    player.add("idle", idle_anim)
    player.add("run",  run_anim)
    player.add("jump", jump_anim)
    player.play("idle")

    # Each frame:
    player.update(dt)
    current_surface = player.current_frame

    # Transitions:
    player.play("run")    # switch immediately
    player.play("jump")   # plays once then returns to "idle" if configured
"""

from __future__ import annotations

import pygame


class SpriteAnimation:
    """
    Immutable animation data — a named sequence of frames with timing.

    Shared across multiple ``AnimationPlayer`` instances.
    Frame duration can be uniform (one float) or per-frame (list of floats).
    """

    def __init__(
        self,
        name:           str,
        frames:         list[pygame.Surface],
        frame_duration: float | list[float] = 0.1,
        loop:           bool  = True,
        ping_pong:      bool  = False,
    ) -> None:
        """
        Args:
            name:           Identifier for this animation (e.g. ``"idle"``).
            frames:         List of surfaces. Must not be empty.
            frame_duration: Seconds per frame. A single float applies to all
                            frames. A list must match ``len(frames)``.
            loop:           If True, restarts from frame 0 when done.
            ping_pong:      If True, reverses direction each cycle instead
                            of jumping back to frame 0. Implies looping.
        """
        if not frames:
            raise ValueError(f"SpriteAnimation '{name}': frames must not be empty.")

        self._name      = name
        self._frames    = frames
        self._loop      = loop
        self._ping_pong = ping_pong

        # Normalise frame_duration to a list
        if isinstance(frame_duration, (int, float)):
            self._durations: list[float] = [float(frame_duration)] * len(frames)
        else:
            if len(frame_duration) != len(frames):
                raise ValueError(
                    f"SpriteAnimation '{name}': frame_duration list length "
                    f"({len(frame_duration)}) must match frames ({len(frames)})."
                )
            self._durations = [float(d) for d in frame_duration]

    @property
    def name(self) -> str:
        return self._name

    @property
    def frames(self) -> list[pygame.Surface]:
        return self._frames

    @property
    def frame_count(self) -> int:
        return len(self._frames)

    @property
    def durations(self) -> list[float]:
        return self._durations

    @property
    def total_duration(self) -> float:
        return sum(self._durations)

    @property
    def loop(self) -> bool:
        return self._loop

    @property
    def ping_pong(self) -> bool:
        return self._ping_pong

    def __repr__(self) -> str:
        return (f"SpriteAnimation(name={self._name!r}, "
                f"frames={len(self._frames)}, loop={self._loop})")


class AnimationPlayer:
    """
    Mutable playback state for sprite animations.

    Owns a registry of named ``SpriteAnimation`` instances. Call
    ``play(name)`` to switch animations. ``update(dt)`` advances the
    frame timer. ``current_frame`` gives the surface to render.

    On-finish callback
    ------------------
    Register ``on_finish`` to be notified when a non-looping animation
    completes. The callback receives the animation name::

        player.on_finish = lambda name: player.play("idle")

    This is the recommended way to chain animations (jump → idle, etc.).
    """

    def __init__(self) -> None:
        self._animations: dict[str, SpriteAnimation] = {}
        self._current:    SpriteAnimation | None      = None
        self._frame_idx:  int                         = 0
        self._elapsed:    float                       = 0.0
        self._forward:    bool                        = True   # for ping-pong
        self._finished:   bool                        = False

        self.on_finish: "Callable[[str], None] | None" = None  # type: ignore[type-arg]

    # ── Animation registry ────────────────────────────────────────────────────

    def add(self, name: str, animation: SpriteAnimation) -> None:
        """
        Register a named animation.

        Args:
            name:      Key used to play this animation via ``play()``.
            animation: The ``SpriteAnimation`` data object.
        """
        self._animations[name] = animation

    def add_many(self, animations: dict[str, SpriteAnimation]) -> None:
        """Register multiple animations at once from a name→animation dict."""
        self._animations.update(animations)

    # ── Playback control ──────────────────────────────────────────────────────

    def play(self, name: str, restart: bool = False) -> None:
        """
        Switch to a named animation.

        If the animation is already playing and ``restart`` is False,
        this is a no-op (avoids restarting from frame 0 on every update).

        Args:
            name:    Animation name registered via ``add()``.
            restart: If True, restart from frame 0 even if already playing.

        Raises:
            KeyError: If ``name`` is not registered.
        """
        if name not in self._animations:
            raise KeyError(
                f"Animation '{name}' not registered. "
                f"Available: {sorted(self._animations)}"
            )

        if self._current is not None and self._current.name == name and not restart:
            return

        self._current   = self._animations[name]
        self._frame_idx = 0
        self._elapsed   = 0.0
        self._forward   = True
        self._finished  = False

    def stop(self) -> None:
        """Stop playback and hold on the current frame."""
        self._current = None

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Advance the animation by one frame tick.

        Args:
            dt: Delta time in seconds.
        """
        if self._current is None or self._finished:
            return

        anim = self._current
        self._elapsed += dt

        # Advance frames while elapsed exceeds current frame duration
        while self._elapsed >= anim.durations[self._frame_idx]:
            self._elapsed -= anim.durations[self._frame_idx]
            self._advance_frame(anim)
            if self._finished:
                break

    def _advance_frame(self, anim: SpriteAnimation) -> None:
        """Move to the next frame, handling loop and ping-pong."""
        last = anim.frame_count - 1

        if anim.ping_pong:
            if self._forward:
                if self._frame_idx >= last:
                    self._forward = False
                    self._frame_idx = max(0, last - 1)
                else:
                    self._frame_idx += 1
            else:
                if self._frame_idx <= 0:
                    self._forward = True
                    self._frame_idx = min(1, last)
                else:
                    self._frame_idx -= 1

        elif anim.loop:
            self._frame_idx = (self._frame_idx + 1) % anim.frame_count

        else:
            if self._frame_idx < last:
                self._frame_idx += 1
            else:
                self._finished = True
                if self.on_finish is not None:
                    self.on_finish(anim.name)

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def current_frame(self) -> pygame.Surface | None:
        """The surface for the current animation frame, or None if stopped."""
        if self._current is None:
            return None
        return self._current.frames[self._frame_idx]

    @property
    def current_animation(self) -> str | None:
        """Name of the currently playing animation, or None."""
        return self._current.name if self._current else None

    @property
    def frame_index(self) -> int:
        """Current frame index within the active animation."""
        return self._frame_idx

    @property
    def is_finished(self) -> bool:
        """True when a non-looping animation has played its last frame."""
        return self._finished

    @property
    def is_playing(self) -> bool:
        """True if an animation is active and not finished."""
        return self._current is not None and not self._finished
