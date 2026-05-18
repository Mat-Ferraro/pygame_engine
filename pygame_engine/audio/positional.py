"""
Simulates distance-based volume falloff and stereo panning by wrapping
pygame's mixer channel API. Not true 3D audio — a convincing 2D
approximation using left/right channel volume.

Usage::

    from pygame_engine.audio.positional import PositionalAudio

    # Create once, update listener position each frame
    pos_audio = PositionalAudio(max_distance=600.0)
    pos_audio.set_listener(player.rect.centerx, player.rect.centery)

    # Play a sound at a world position
    pos_audio.play(sound, world_x=enemy.rect.centerx,
                   world_y=enemy.rect.centery)

    # For looping ambient sounds, create a source and update its position
    source = pos_audio.create_source(footstep_sound, loop=True)
    source.world_x = npc.rect.centerx
    source.world_y = npc.rect.centery
    source.update(pos_audio)
"""

from __future__ import annotations

import math

import pygame

from pygame_engine.utils.mathx import clamp


class PositionalSource:
    """
    A looping or one-shot positional sound source.

    Args:
        sound:     The pygame Sound to play.
        world_x:   Initial X position in world space.
        world_y:   Initial Y position in world space.
        loop:      True for looping sounds (ambient, engine rumble, etc.).
        volume:    Base volume multiplier [0, 1]. Default 1.0.
    """

    def __init__(
        self,
        sound:   pygame.mixer.Sound,
        world_x: float = 0.0,
        world_y: float = 0.0,
        loop:    bool  = False,
        volume:  float = 1.0,
    ) -> None:
        self.world_x  = world_x
        self.world_y  = world_y
        self.volume   = volume
        self._sound   = sound
        self._loop    = loop
        self._channel: pygame.mixer.Channel | None = None

    def start(self, pos_audio: "PositionalAudio") -> None:
        """Begin playing this source. Call once."""
        loops = -1 if self._loop else 0
        self._channel = self._sound.play(loops=loops)
        self.update(pos_audio)

    def stop(self) -> None:
        """Stop this source."""
        if self._channel is not None:
            self._channel.stop()
            self._channel = None

    def update(self, pos_audio: "PositionalAudio") -> None:
        """
        Recompute and apply volume/panning based on current listener position.

        Call each frame for moving sources.
        """
        if self._channel is None:
            return
        left, right = pos_audio._compute_volumes(
            self.world_x, self.world_y, self.volume
        )
        self._channel.set_volume(left, right)

    @property
    def is_playing(self) -> bool:
        """Return True if this source is currently playing."""
        return self._channel is not None and self._channel.get_busy()


class PositionalAudio:
    """
    2D positional audio system.

    Wraps pygame's mixer to provide distance-based volume falloff and
    stereo panning. All coordinates are in world space.

    Args:
        max_distance: Distance beyond which sounds are completely silent.
        rolloff:      Volume falloff exponent. 1.0 = linear, 2.0 = quadratic.
    """

    def __init__(
        self,
        max_distance: float = 500.0,
        rolloff:      float = 1.0,
    ) -> None:
        self._listener_x   = 0.0
        self._listener_y   = 0.0
        self._max_distance = max(1.0, max_distance)
        self._rolloff      = max(0.1, rolloff)

    # ── Listener ──────────────────────────────────────────────────────────────

    def set_listener(self, world_x: float, world_y: float) -> None:
        """
        Update the listener (player/camera) position.

        Call once per frame before any ``update()`` calls on sources.

        Args:
            world_x: Listener X in world space.
            world_y: Listener Y in world space.
        """
        self._listener_x = world_x
        self._listener_y = world_y

    # ── One-shot sounds ───────────────────────────────────────────────────────

    def play(
        self,
        sound:   pygame.mixer.Sound,
        world_x: float,
        world_y: float,
        volume:  float = 1.0,
    ) -> None:
        """
        Play a one-shot sound at a world position.

        Args:
            sound:   The pygame Sound to play.
            world_x: X position in world space.
            world_y: Y position in world space.
            volume:  Base volume multiplier [0, 1].
        """
        left, right = self._compute_volumes(world_x, world_y, volume)
        if left <= 0.0 and right <= 0.0:
            return   # too far away — skip entirely
        channel = sound.play()
        if channel is not None:
            channel.set_volume(left, right)

    # ── Looping sources ───────────────────────────────────────────────────────

    def create_source(
        self,
        sound:   pygame.mixer.Sound,
        world_x: float = 0.0,
        world_y: float = 0.0,
        loop:    bool  = True,
        volume:  float = 1.0,
    ) -> PositionalSource:
        """
        Create a managed looping sound source.

        Call ``source.start(pos_audio)`` to begin and
        ``source.update(pos_audio)`` each frame to keep it positioned.

        Returns:
            A ``PositionalSource`` ready to start.
        """
        return PositionalSource(sound, world_x, world_y, loop, volume)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def max_distance(self) -> float:
        """Return the maximum audible distance in world units."""
        return self._max_distance

    @max_distance.setter
    def max_distance(self, value: float) -> None:
        """Return the maximum audible distance in world units."""
        self._max_distance = max(1.0, value)

    @property
    def listener_position(self) -> tuple[float, float]:
        """Return the current listener position as (x, y)."""
        return (self._listener_x, self._listener_y)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _compute_volumes(
        self,
        world_x: float,
        world_y: float,
        base_volume: float,
    ) -> tuple[float, float]:
        """
        Compute (left, right) channel volumes for a world position.

        Returns (0, 0) when the source is beyond max_distance.
        """
        dx       = world_x - self._listener_x
        dy       = world_y - self._listener_y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance >= self._max_distance:
            return (0.0, 0.0)

        # Distance falloff
        t      = clamp(distance / self._max_distance, 0.0, 1.0)
        volume = base_volume * (1.0 - t ** self._rolloff)

        # Stereo panning: dx normalised to [-1, 1] within max_distance
        pan   = clamp(dx / self._max_distance, -1.0, 1.0)
        left  = volume * clamp(1.0 - pan, 0.0, 1.0)
        right = volume * clamp(1.0 + pan, 0.0, 1.0)

        return (left, right)

    def __repr__(self) -> str:
        return (f"PositionalAudio(listener=({self._listener_x:.0f},"
                f"{self._listener_y:.0f}), max_dist={self._max_distance})")