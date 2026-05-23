"""
Runtime audio management for pygame_engine.

``AudioManager`` handles all playback policy: volume, muting, music
streaming, and sound effect playback via an AudioBus topology.

Owned by ``Application``, accessible via ``app.audio``.

Bus topology
------------
Four built-in buses form a two-level hierarchy::

    master
    ├── music   (respects_time_scale=True  — pauses when game pauses)
    ├── sfx     (respects_time_scale=True  — pauses when game pauses)
    └── ui      (respects_time_scale=False — plays during game pause)

Effective volume for any bus = product of its own volume and all parent
volumes, zeroed if any bus in the chain is muted or paused by time_scale.

Observable properties
---------------------
``bus.volume`` and ``bus.muted`` are ``Observable`` — settings UI can
subscribe directly::

    app.audio.music.volume.subscribe(lambda old, new: slider.set_value(new))
    app.audio.sfx.muted.subscribe(lambda old, new: btn.update(new))

Backward compatibility
----------------------
The flat API (``master_volume``, ``music_volume``, ``sfx_volume``,
``muted``, ``toggle_mute``) is fully preserved as property shims that
delegate to the bus topology. Existing code requires no changes.

Usage::

    # Bus API (preferred for new code)
    app.audio.music.set_volume(0.7)
    app.audio.sfx.muted.value = True
    app.audio.ui.set_volume(0.9)

    # Legacy flat API (still works)
    app.audio.master_volume = 0.8
    app.audio.muted = True

    # Playback
    app.audio.play_music("music/theme.ogg")
    app.audio.play_sfx(app.assets.sound("click.wav"))
    app.audio.play_sfx(app.assets.sound("ui_click.wav"), bus="ui")
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pygame

from pygame_engine.audio.audio_bus import AudioBus


class AudioManager:
    """
    Runtime audio controller with bus topology.

    Built-in buses: ``master``, ``music``, ``sfx``, ``ui``.
    Use ``create_bus(name, parent)`` for additional buses.

    The flat volume/mute API from the previous version is preserved as
    property shims for backward compatibility.
    """

    def __init__(self) -> None:
        # ── Bus topology ──────────────────────────────────────────────────────
        self.master = AudioBus("master", respects_time_scale=False)
        """
        Root bus. Volume and mute here affect ALL other buses.

        ``respects_time_scale=False`` — the master itself is never silenced
        by time_scale; individual child buses apply that policy.
        """

        self.music = AudioBus("music", respects_time_scale=True)
        """Music bus. Pauses when ``time_scale`` is 0."""

        self.sfx = AudioBus("sfx", respects_time_scale=True)
        """Sound effects bus. Pauses when ``time_scale`` is 0."""

        self.ui = AudioBus("ui", respects_time_scale=False)
        """
        UI sounds bus. Never pauses — menu sounds work during game pause.
        """

        # Wire parent chain
        self.music._parent = self.master
        self.sfx._parent   = self.master
        self.ui._parent    = self.master

        # Named registry (includes built-ins)
        self._buses: dict[str, AudioBus] = {
            "master": self.master,
            "music":  self.music,
            "sfx":    self.sfx,
            "ui":     self.ui,
        }

        # ── Music state ───────────────────────────────────────────────────────
        self._music_path:   str | None = None
        self._music_paused: bool       = False

    # ── Bus management ────────────────────────────────────────────────────────

    def create_bus(
        self,
        name:   str,
        parent: AudioBus | None = None,
    ) -> AudioBus:
        """
        Create and register a custom audio bus.

        Args:
            name:   Unique identifier for the bus.
            parent: Parent bus. Defaults to ``master`` if None.

        Returns:
            The newly created ``AudioBus``.

        Raises:
            ValueError: If a bus with ``name`` already exists.
        """
        if name in self._buses:
            raise ValueError(
                f"AudioBus {name!r} already exists. "
                f"Use get_bus({name!r}) to retrieve it."
            )
        bus = AudioBus(name)
        bus._parent = parent if parent is not None else self.master
        self._buses[name] = bus
        return bus

    def get_bus(self, name: str) -> AudioBus:
        """
        Return a registered bus by name.

        Args:
            name: The bus identifier.

        Raises:
            KeyError: If no bus with ``name`` is registered.
        """
        try:
            return self._buses[name]
        except KeyError:
            raise KeyError(
                f"No AudioBus named {name!r}. "
                f"Available: {sorted(self._buses)}"
            )

    # ── Time-scale integration ────────────────────────────────────────────────

    def update(self, time_scale: float) -> None:
        """
        Apply time-scale policy to all buses.

        Call once per frame from ``Application._loop()`` with the current
        ``time_scale`` value. Buses with ``respects_time_scale=True`` are
        silenced when ``time_scale`` is 0.

        Args:
            time_scale: Current time scale (0.0 = paused, 1.0 = normal).
        """
        paused = time_scale == 0.0
        for bus in self._buses.values():
            bus._apply_time_scale(time_scale)

        # Reflect time-scale pause in pygame mixer music
        if self.music.respects_time_scale:
            if paused and self._music_paused is False:
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
                    # Track that WE paused it (not the user)
                    self._time_paused_music = True
            elif not paused and getattr(self, "_time_paused_music", False):
                if pygame.mixer.get_init():
                    pygame.mixer.music.unpause()
                self._time_paused_music = False

    # ── Music ─────────────────────────────────────────────────────────────────

    def play_music(
        self,
        path:       str | Path,
        loops:      int = -1,
        fade_in_ms: int = 0,
    ) -> None:
        """
        Load and play a music track on the music bus.

        Stops any currently playing music before starting the new track.
        Music is streamed from disk — it is not loaded into memory.

        Args:
            path:       Path to the music file.
            loops:      Additional loops after first play. -1 = loop forever.
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
            pygame.mixer.music.set_volume(self.music.effective_volume)
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
        sound:  pygame.mixer.Sound | None,
        volume: float = 1.0,
        loops:  int   = 0,
        bus:    str   = "sfx",
    ) -> pygame.mixer.Channel | None:
        """
        Play a sound effect through the named bus.

        Args:
            sound:  A ``pygame.mixer.Sound`` from ``app.assets.sound()``.
                    If None (missing asset), this is a safe no-op.
            volume: Per-call volume multiplier in [0.0, 1.0].
            loops:  Additional loops after first play. 0 = play once.
            bus:    Bus name to route through. Default ``"sfx"``.
                    Use ``"ui"`` for interface sounds that must play
                    during game pause.

        Returns:
            The mixer channel, or None if the sound could not be played.
        """
        if sound is None:
            return None
        if not pygame.mixer.get_init():
            return None

        audio_bus  = self._buses.get(bus, self.sfx)
        effective  = audio_bus.effective_volume * max(0.0, min(1.0, volume))
        sound.set_volume(effective)
        return sound.play(loops=loops)

    # ── Backward-compatible flat API ──────────────────────────────────────────

    @property
    def master_volume(self) -> float:
        """Master volume in [0.0, 1.0]. Delegates to ``master`` bus."""
        return self.master.volume.value

    @master_volume.setter
    def master_volume(self, value: float) -> None:
        self.master.set_volume(value)
        self._apply_music_volume()

    @property
    def music_volume(self) -> float:
        """Music volume in [0.0, 1.0]. Delegates to ``music`` bus."""
        return self.music.volume.value

    @music_volume.setter
    def music_volume(self, value: float) -> None:
        self.music.set_volume(value)
        self._apply_music_volume()

    @property
    def sfx_volume(self) -> float:
        """SFX volume in [0.0, 1.0]. Delegates to ``sfx`` bus."""
        return self.sfx.volume.value

    @sfx_volume.setter
    def sfx_volume(self, value: float) -> None:
        self.sfx.set_volume(value)

    @property
    def muted(self) -> bool:
        """Global mute. Delegates to ``master`` bus muted flag."""
        return self.master.muted.value

    @muted.setter
    def muted(self, value: bool) -> None:
        self.master.muted.value = value
        self._apply_music_volume()

    def toggle_mute(self) -> bool:
        """Toggle master mute and return the new state."""
        new_state = self.master.toggle_mute()
        self._apply_music_volume()
        return new_state

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
        """Backward-compat: effective volume via bus chain."""
        return self.music.effective_volume

    @property
    def _effective_sfx_volume(self) -> float:
        """Backward-compat: effective volume via bus chain."""
        return self.sfx.effective_volume

    def _apply_music_volume(self) -> None:
        """Apply current effective music volume to pygame mixer."""
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.music.effective_volume)
