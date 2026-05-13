"""
events/signals.py

Typed signal helpers for pygame_engine.

A ``Signal`` wraps a specific event name on an ``EventBus`` and provides
a cleaner, typed interface for the most common patterns. Instead of
using raw string event names everywhere, game systems can expose named
Signal attributes that callers subscribe to directly.

Usage::

    from pygame_engine.events.signals import Signal
    from pygame_engine.events import bus

    class Player:
        damaged    = Signal("player.damaged",    bus)
        died       = Signal("player.died",       bus)
        levelled_up = Signal("player.levelled_up", bus)

        def take_damage(self, amount: int) -> None:
            self.hp -= amount
            Player.damaged.emit(amount=amount, hp=self.hp)
            if self.hp <= 0:
                Player.died.emit()

    # Elsewhere:
    Player.damaged.connect(hud.show_damage)
    Player.died.connect(game_scene.on_player_died)

This is purely a convenience layer over EventBus — no new mechanism.
"""

from __future__ import annotations

from typing import Callable

from pygame_engine.events.event_bus import EventBus, Handler


class Signal:
    """
    A named, typed wrapper around a specific EventBus event.

    Signals give game systems a clean, discoverable API surface compared
    to raw string event names. They are optional — the bus works fine
    without them.
    """

    def __init__(self, event: str, bus: EventBus) -> None:
        """
        Args:
            event: The event name this signal maps to.
            bus:   The EventBus this signal publishes/subscribes on.
        """
        self._event = event
        self._bus   = bus

    @property
    def event(self) -> str:
        """The event name this signal is bound to."""
        return self._event

    def connect(self, handler: Handler) -> None:
        """
        Subscribe ``handler`` to this signal.

        Equivalent to ``bus.on(event, handler)``.
        """
        self._bus.on(self._event, handler)

    def connect_once(self, handler: Handler) -> None:
        """
        Subscribe ``handler`` for a single emission only.

        Equivalent to ``bus.once(event, handler)``.
        """
        self._bus.once(self._event, handler)

    def disconnect(self, handler: Handler) -> bool:
        """
        Remove ``handler`` from this signal.

        Equivalent to ``bus.off(event, handler)``.

        Returns:
            True if the handler was found and removed.
        """
        return self._bus.off(self._event, handler)

    def emit(self, **kwargs) -> int:
        """
        Emit this signal with the given keyword arguments.

        Equivalent to ``bus.emit(event, **kwargs)``.

        Returns:
            Number of handlers called.
        """
        return self._bus.emit(self._event, **kwargs)

    def clear(self) -> None:
        """Remove all handlers for this signal."""
        self._bus.clear(self._event)

    def __repr__(self) -> str:
        return f"Signal({self._event!r})"
