"""
events/event_bus.py

Pub/sub event bus for pygame_engine.

``EventBus`` allows game systems to communicate without direct coupling.
A combat system can emit ``"player.damaged"`` without knowing that the
HUD, the audio manager, and the screen-shake system all want to react.

Design
------
- Events are named strings with dot-separated namespaces: ``"player.damaged"``,
  ``"scene.entered"``, ``"item.collected"``.
- Handlers receive keyword arguments from ``emit()``.
- Wildcard subscriptions use ``*``: ``"player.*"`` matches all player events.
- One-shot subscriptions auto-unsubscribe after first call.
- All calls are synchronous — no queuing, no threading.
- A module-level ``bus`` singleton is provided for convenience. Game code
  can use it directly or inject a fresh ``EventBus()`` for testing.

Naming conventions (recommended)
----------------------------------
Use dot-namespaced event names::

    "player.damaged"        # player took damage
    "player.died"           # player died
    "player.levelled_up"    # player gained a level
    "enemy.spawned"         # enemy was created
    "enemy.died"            # enemy was destroyed
    "item.collected"        # player picked up an item
    "scene.entered"         # scene became active
    "scene.exited"          # scene was removed
    "audio.muted"           # audio muted/unmuted
    "save.completed"        # save finished successfully

Usage::

    from pygame_engine.events import bus

    # Subscribe
    def on_damaged(amount: int, source: str = "unknown") -> None:
        hud.show_damage(amount)
        audio.play_sfx(hurt_sound)

    bus.on("player.damaged", on_damaged)

    # Emit (keyword arguments only)
    bus.emit("player.damaged", amount=30, source="spike_trap")

    # One-shot
    bus.once("tutorial.first_kill", lambda **kw: show_tutorial_tip())

    # Wildcard
    bus.on("player.*", lambda **kw: analytics.record(**kw))

    # Unsubscribe
    bus.off("player.damaged", on_damaged)

    # Clear all handlers for an event (useful between scenes)
    bus.clear("player.damaged")

    # Clear everything (call between major game resets)
    bus.clear_all()
"""

from __future__ import annotations

import fnmatch
from typing import Callable


Handler = Callable[..., None]


class EventBus:
    """
    Synchronous pub/sub event bus.

    Thread safety: not thread-safe. Intended for single-threaded game loops.
    """

    def __init__(self) -> None:
        # Maps event name → list of (handler, one_shot) tuples
        self._handlers: dict[str, list[tuple[Handler, bool]]] = {}

    # ── Subscription ──────────────────────────────────────────────────────────

    def on(self, event: str, handler: Handler) -> None:
        """
        Subscribe ``handler`` to ``event``.

        Subscribing the same handler twice to the same event is a no-op.

        Args:
            event:   Event name or wildcard pattern (e.g. ``"player.*"``).
            handler: Callable that accepts keyword arguments from ``emit()``.
        """
        if event not in self._handlers:
            self._handlers[event] = []

        # Avoid duplicate subscriptions
        for h, _ in self._handlers[event]:
            if h is handler:
                return

        self._handlers[event].append((handler, False))

    def once(self, event: str, handler: Handler) -> None:
        """
        Subscribe ``handler`` to ``event`` for a single call only.

        The handler is automatically removed after the first time it fires.

        Args:
            event:   Event name or wildcard pattern.
            handler: Callable that accepts keyword arguments from ``emit()``.
        """
        if event not in self._handlers:
            self._handlers[event] = []

        for h, _ in self._handlers[event]:
            if h is handler:
                return

        self._handlers[event].append((handler, True))

    def off(self, event: str, handler: Handler) -> bool:
        """
        Remove a subscription.

        Args:
            event:   The event name the handler was subscribed to.
            handler: The handler to remove.

        Returns:
            True if the handler was found and removed, False otherwise.
        """
        if event not in self._handlers:
            return False

        before = len(self._handlers[event])
        self._handlers[event] = [
            (h, once) for h, once in self._handlers[event]
            if h is not handler
        ]
        return len(self._handlers[event]) < before

    # ── Emission ──────────────────────────────────────────────────────────────

    def emit(self, event: str, **kwargs) -> int:
        """
        Emit ``event`` with the given keyword arguments.

        All matching subscribers are called synchronously in subscription
        order. Wildcard subscribers (e.g. ``"player.*"``) are matched
        against the emitted event name using ``fnmatch``.

        One-shot subscribers are removed after being called.

        Args:
            event:   The event name to emit.
            **kwargs: Payload passed to every matching handler.

        Returns:
            Number of handlers called.
        """
        called    = 0
        to_remove: list[tuple[str, Handler]] = []

        for pattern, entries in list(self._handlers.items()):
            if not self._matches(pattern, event):
                continue

            # Snapshot entries so handlers can subscribe/unsubscribe safely
            for handler, one_shot in list(entries):
                try:
                    handler(**kwargs)
                except Exception as exc:
                    # Don't let one broken handler kill the entire emit
                    import warnings
                    warnings.warn(
                        f"EventBus: handler {handler!r} raised an exception "
                        f"for event '{event}': {exc}",
                        stacklevel=2,
                    )
                called += 1
                if one_shot:
                    to_remove.append((pattern, handler))

        # Remove one-shot handlers after iteration
        for pattern, handler in to_remove:
            self.off(pattern, handler)

        return called

    # ── Management ────────────────────────────────────────────────────────────

    def clear(self, event: str) -> None:
        """
        Remove all handlers for ``event``.

        Args:
            event: The exact event name (not a wildcard) to clear.
        """
        self._handlers.pop(event, None)

    def clear_all(self) -> None:
        """
        Remove all handlers for all events.

        Call between major game resets (e.g. returning to main menu from
        deep inside gameplay) to avoid stale references.
        """
        self._handlers.clear()

    def handler_count(self, event: str | None = None) -> int:
        """
        Return the number of registered handlers.

        Args:
            event: If given, count handlers for this specific event only.
                   If None, count all handlers across all events.

        Returns:
            Total handler count.
        """
        if event is not None:
            return len(self._handlers.get(event, []))
        return sum(len(entries) for entries in self._handlers.values())

    def subscribed_events(self) -> list[str]:
        """Return a sorted list of all event patterns that have handlers."""
        return sorted(self._handlers.keys())

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _matches(pattern: str, event: str) -> bool:
        """
        Return True if ``event`` matches ``pattern``.

        Exact match always works. Wildcards use ``fnmatch`` rules:
        ``*`` matches any sequence of characters within a segment,
        ``player.*`` matches ``player.damaged``, ``player.died``, etc.
        """
        if pattern == event:
            return True
        return fnmatch.fnmatch(event, pattern)


# ── Module-level singleton ────────────────────────────────────────────────────

#: The shared game event bus.
#:
#: Import and use directly in game code::
#:
#:     from pygame_engine.events import bus
#:     bus.on("player.damaged", my_handler)
#:     bus.emit("player.damaged", amount=10)
#:
#: For testing, create a fresh ``EventBus()`` instance instead.
bus: EventBus = EventBus()
