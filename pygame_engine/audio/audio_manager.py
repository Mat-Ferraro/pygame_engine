"""
Runtime audio management for pygame_engine.

``AudioManager`` handles all playback policy: volume, muting, music
streaming, and sound effect playback. It does not load assets itself —
sounds are loaded through ``app.assets`` and passed in as
``pygame.mixer.Sound`` objects.

Owned by ``Application``, accessible via ``app.audio``.

Architecture
------------
- Music (``pygame.mixer.music``) — one streamed track at a time.
  Typically background music. Supports play, stop, pause, resume,
  fade-out, and looping.

- Sound effects (``pygame.mixer.Sound``) — short clips played on
  mixer channels. Multiple effects can play simultaneously.

Volume model
------------
Three independent volume levels, all in [0.0, 1.0]:

    effective_music_sfx_volume = master * music/sfx * (0 if muted)

``muted`` silences everything without destroying volume settings.

Usage::

    # Via Application (preferred)
    app.audio.play_music("music/theme.ogg")        # path via app.assets
    app.audio.play_sfx(app.assets.sound("click.wav"))
    app.audio.master_volume = 0.8
    app.audio.muted = True
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pygame


class AudioManager:
    """
    Runtime audio controller for pygame_engine.

    Handles music streaming and sound effect playback with independent
    volume controls and a global mute flag.
    """

    def __init__(self) -> None:
        self._master_volume: float = 1.0
        self._music_volume:  float = 1.0
        self._sfx_volume:    float = 1.0
        self._muted:         bool  = False

        self._music_path:    str | None = None   # currently loaded track
        self._music_paused:  bool       = False

    # ── Music ─────────────────────────────────────────────────────────────────

    def play_music(
        self,
        path: str | Path,
        loops: int = -1,
        fade_in_ms: int = 0,
    ) -> None:
        """
        Load and play a music track.

        Stops any currently playing music before starting the new track.
        Music is streamed from disk — it is not loaded into memory.

        Args:
            path:       Absolute or relative path to the music file.
                        Pass the result of ``app.assets.asset_root / ...``
                        or resolve it through ``PathResolver``.
            loops:      Number of additional loops after the first play.
                        -1 = loop forever (default).
            fade_in_ms: Fade-in duration in milliseconds. 0 = instant.
        """
        if not pygame.mixer.get_init():
            warnings.warn("AudioManager: mixer not initialised — music will not play.")
            return

        path_str = str(path)
        try:
            pygame.mixer.music.load(path_str)
            self._music_path   = path_str
            self._music_paused = False
            pygame.mixer.music.set_volume(self._effective_music_volume)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_in_ms)
        except pygame.error as exc:
            warnings.warn(f"AudioManager: failed to load music '{path}': {exc}")

    def stop_music(self, fade_out_ms: int = 0) -> None:
        """
        Stop the currently playing music.

        Args:
            fade_out_ms: Fade-out duration in milliseconds. 0 = instant.
        """
        if fade_out_ms > 0:
            pygame.mixer.music.fadeout(fade_out_ms)
        else:
            pygame.mixer.music.stop()
        self._music_paused = False

    def pause_music(self) -> None:
        """Pause the currently playing music."""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self._music_paused = True

    def resume_music(self) -> None:
        """Resume a paused music track."""
        if self._music_paused:
            pygame.mixer.music.unpause()
            self._music_paused = False

    @property
    def music_playing(self) -> bool:
        """True if music is currently playing (not paused)."""
        return pygame.mixer.music.get_busy() and not self._music_paused

    @property
    def music_paused(self) -> bool:
        """True if music is loaded and paused."""
        return self._music_paused

    # ── Sound effects ─────────────────────────────────────────────────────────

    def play_sfx(
        self,
        sound: pygame.mixer.Sound | None,
        volume: float = 1.0,
        loops: int = 0,
    ) -> pygame.mixer.Channel | None:
        """
        Play a sound effect on an available mixer channel.

        Args:
            sound:  A ``pygame.mixer.Sound`` from ``app.assets.sound()``.
                    If None (missing asset), this is a safe no-op.
            volume: Per-call volume multiplier in [0.0, 1.0]. Combined
                    with the global SFX and master volumes.
            loops:  Additional loops after first play. 0 = play once.

        Returns:
            The ``pygame.mixer.Channel`` the sound is playing on,
            or None if the sound could not be played.
        """
        if sound is None:
            return None
        if not pygame.mixer.get_init():
            return None

        effective = self._effective_sfx_volume * max(0.0, min(1.0, volume))
        sound.set_volume(effective)
        channel = sound.play(loops=loops)
        return channel

    # ── Volume ────────────────────────────────────────────────────────────────

    @property
    def master_volume(self) -> float:
        """Master volume in [0.0, 1.0]. Scales all audio."""
        return self._master_volume

    @master_volume.setter
    def master_volume(self, value: float) -> None:
        """Return the current master volume in the range 0.0–1.0."""
        self._master_volume = max(0.0, min(1.0, value))
        self._apply_music_volume()

    @property
    def music_volume(self) -> float:
        """Music volume in [0.0, 1.0]."""
        return self._music_volume

    @music_volume.setter
    def music_volume(self, value: float) -> None:
        """Return the current music volume in the range 0.0–1.0."""
        self._music_volume = max(0.0, min(1.0, value))
        self._apply_music_volume()

    @property
    def sfx_volume(self) -> float:
        """Sound effect volume in [0.0, 1.0]."""
        return self._sfx_volume

    @sfx_volume.setter
    def sfx_volume(self, value: float) -> None:
        """Return the current SFX volume in the range 0.0–1.0."""
        self._sfx_volume = max(0.0, min(1.0, value))

    # ── Mute ──────────────────────────────────────────────────────────────────

    @property
    def muted(self) -> bool:
        """When True, all audio is silenced without losing volume settings."""
        return self._muted

    @muted.setter
    def muted(self, value: bool) -> None:
        """Return True if the audio manager is currently muted."""
        self._muted = value
        self._apply_music_volume()

    def toggle_mute(self) -> bool:
        """Toggle mute state and return the new state."""
        self.muted = not self._muted
        return self._muted

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """
        Stop all audio cleanly.

        Called by ``Application._shutdown()`` before ``pygame.quit()``.
        """
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.stop()

    # ── Internal ──────────────────────────────────────────────────────────────

    @property
    def _effective_music_volume(self) -> float:
        if self._muted:
            return 0.0
        return self._master_volume * self._music_volume

    @property
    def _effective_sfx_volume(self) -> float:
        if self._muted:
            return 0.0
        return self._master_volume * self._sfx_volume

    def _apply_music_volume(self) -> None:
        """Apply the current effective music volume to the mixer."""
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self._effective_music_volume)