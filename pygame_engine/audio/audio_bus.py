"""
audio/audio_bus.py

AudioBus — an independent volume/mute channel for the AudioManager.

Each bus has its own ``Observable[float]`` volume and ``Observable[bool]``
muted flag, so settings UI can subscribe directly::

    app.audio.music.volume.subscribe(lambda old, new: slider.set_value(new))
    app.audio.sfx.muted.subscribe(lambda old, new: mute_btn.update_icon(new))

Buses are combined with the master bus when computing effective volume::

    effective = master.volume * bus.volume  (0.0 if either is muted)

``respects_time_scale``
-----------------------
When True (default), the bus is paused when ``time_scale`` is 0. The
``ui`` bus sets this to False so menu sounds work during game pause.
``AudioManager.update(scaled_dt, unscaled_dt)`` applies this policy.

``pitch_follows_time_scale``
----------------------------
When True, the bus pitch is multiplied by ``time_scale`` each frame.
Useful for slow-motion effects. Default False.

Creating custom buses
---------------------
Use ``AudioManager.create_bus()`` rather than instantiating directly::

    cutscene_bus = app.audio.create_bus("cutscene", parent=app.audio.master)
"""

from __future__ import annotations

from pygame_engine.state.observable import Observable


class AudioBus:
    """
    An independent audio channel with Observable volume and mute state.

    Attributes
    ----------
    name : str
        Human-readable identifier (e.g. ``"music"``, ``"sfx"``, ``"ui"``).
    volume : Observable[float]
        Volume multiplier in [0.0, 1.0]. Subscribers receive
        ``(old_value, new_value)`` on change.
    muted : Observable[bool]
        When True the bus is silenced without losing its volume setting.
        Subscribers receive ``(old_value, new_value)`` on change.
    pitch : float
        Pitch multiplier. 1.0 = normal. Not yet wired to pygame (reserved
        for future implementation). Default 1.0.
    respects_time_scale : bool
        When True (default), this bus pauses when ``time_scale`` is 0.
        Set to False for UI buses that must keep playing during game pause.
    pitch_follows_time_scale : bool
        When True, pitch is multiplied by ``time_scale`` each frame.
        Default False.
    """

    def __init__(
        self,
        name:                   str,
        volume:                 float = 1.0,
        muted:                  bool  = False,
        respects_time_scale:    bool  = True,
        pitch_follows_time_scale: bool = False,
    ) -> None:
        """
        Args:
            name:                     Human-readable bus identifier.
            volume:                   Initial volume in [0.0, 1.0].
            muted:                    Initial mute state.
            respects_time_scale:      Pause when time_scale == 0.
            pitch_follows_time_scale: Scale pitch with time_scale.
        """
        self.name: str = name

        self.volume: Observable[float] = Observable(
            max(0.0, min(1.0, volume))
        )
        """Observable volume in [0.0, 1.0]."""

        self.muted: Observable[bool] = Observable(muted)
        """Observable mute flag."""

        self.pitch:                   float = 1.0
        self.respects_time_scale:     bool  = respects_time_scale
        self.pitch_follows_time_scale: bool  = pitch_follows_time_scale

        # Optional parent bus — effective volume walks up the chain
        self._parent: AudioBus | None = None

        # Whether this bus is currently paused by time_scale == 0
        self._paused_by_time: bool = False

    # ── Parent chain ──────────────────────────────────────────────────────────

    @property
    def parent(self) -> AudioBus | None:
        """The parent bus, or None for root buses."""
        return self._parent

    # ── Effective volume ──────────────────────────────────────────────────────

    @property
    def effective_volume(self) -> float:
        """
        Compute the final volume for this bus.

        Walks up the parent chain, multiplying volumes, zeroing if any
        bus (including parents) is muted or paused by time_scale.

        Returns:
            A float in [0.0, 1.0].
        """
        vol: float = self.volume.value
        if self.muted.value or self._paused_by_time:
            return 0.0

        bus: AudioBus | None = self._parent
        while bus is not None:
            if bus.muted.value or bus._paused_by_time:
                return 0.0
            vol *= bus.volume.value
            bus  = bus._parent

        return max(0.0, min(1.0, vol))

    # ── Volume helpers ────────────────────────────────────────────────────────

    def set_volume(self, value: float) -> None:
        """
        Set bus volume, clamped to [0.0, 1.0].

        Equivalent to ``bus.volume.value = value`` but with clamping.

        Args:
            value: New volume in [0.0, 1.0].
        """
        self.volume.value = max(0.0, min(1.0, value))

    def toggle_mute(self) -> bool:
        """
        Toggle the mute state and return the new value.

        Returns:
            True if now muted, False if now unmuted.
        """
        self.muted.value = not self.muted.value
        return self.muted.value

    # ── Time-scale pause ──────────────────────────────────────────────────────

    def _apply_time_scale(self, time_scale: float) -> None:
        """
        Called by AudioManager.update() to pause/resume this bus.

        Only acts when ``respects_time_scale`` is True.

        Args:
            time_scale: Current time scale from TimeManager.
        """
        if self.respects_time_scale:
            self._paused_by_time = time_scale == 0.0

    # ── Representation ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        muted_str = " [muted]" if self.muted.value else ""
        paused_str = " [time-paused]" if self._paused_by_time else ""
        return (
            f"AudioBus({self.name!r}, "
            f"vol={self.volume.value:.2f}{muted_str}{paused_str})"
        )
