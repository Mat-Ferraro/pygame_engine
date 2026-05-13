"""
state/observable.py

Observable value wrapper for pygame_engine.

An ``Observable`` wraps a single value and notifies registered listeners
whenever that value changes. Use it when multiple consumers need to react
to a changing value without being directly coupled to its owner.

Use observables intentionally — not for everything. A plain attribute is
fine when only one thing reads a value. Use Observable when:
- multiple consumers care about a changing value
- UI should react automatically to a state change
- loose coupling between producer and consumers is genuinely helpful

Usage::

    from pygame_engine.state.observable import Observable

    volume = Observable(1.0)

    # Subscribe
    def on_volume_change(new_val, old_val):
        audio.set_master_volume(new_val)

    volume.subscribe(on_volume_change)

    # Change value — listener fires automatically
    volume.value = 0.5

    # Read
    print(volume.value)   # 0.5

    # Unsubscribe
    volume.unsubscribe(on_volume_change)
"""

from __future__ import annotations

from typing import Callable, Generic, TypeVar

T = TypeVar("T")

# Listener signature: (new_value, old_value) -> None
Listener = Callable[[T, T], None]


class Observable(Generic[T]):
    """
    A value wrapper that notifies subscribers on change.

    Type parameter ``T`` is the type of the wrapped value.

    Thread safety: not thread-safe. Intended for single-threaded
    game loops only.
    """

    def __init__(self, initial: T) -> None:
        """
        Args:
            initial: The starting value.
        """
        self._value:     T               = initial
        self._listeners: list[Listener[T]] = []

    # ── Value access ──────────────────────────────────────────────────────────

    @property
    def value(self) -> T:
        """The current wrapped value."""
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        """
        Set a new value and notify all listeners if it changed.

        Listeners are called with ``(new_value, old_value)``.
        Equality is checked with ``==`` before firing listeners —
        setting the same value twice does not notify listeners.
        """
        if new_value == self._value:
            return
        old_value   = self._value
        self._value = new_value
        self._notify(new_value, old_value)

    def set_silent(self, new_value: T) -> None:
        """
        Set a new value WITHOUT notifying listeners.

        Use sparingly — bypasses the reactive contract.
        """
        self._value = new_value

    # ── Subscription ──────────────────────────────────────────────────────────

    def subscribe(self, listener: Listener[T]) -> None:
        """
        Register a listener to be called on value change.

        Adding the same listener twice is a no-op.

        Args:
            listener: Callable taking ``(new_value, old_value)``.
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Listener[T]) -> None:
        """
        Remove a previously registered listener.

        Removing a listener that was never registered is a no-op.

        Args:
            listener: The listener to remove.
        """
        try:
            self._listeners.remove(listener)
        except ValueError:
            pass

    def clear_listeners(self) -> None:
        """Remove all registered listeners."""
        self._listeners.clear()

    @property
    def listener_count(self) -> int:
        """Number of currently registered listeners."""
        return len(self._listeners)

    # ── Representation ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Observable({self._value!r})"

    # ── Internal ──────────────────────────────────────────────────────────────

    def _notify(self, new_value: T, old_value: T) -> None:
        for listener in list(self._listeners):
            listener(new_value, old_value)
