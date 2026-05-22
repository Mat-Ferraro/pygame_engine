"""
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

    # Subscribe — callback receives (old_value, new_value)
    def on_volume_change(old_val, new_val):
        audio.set_master_volume(new_val)

    volume.subscribe(on_volume_change)

    # Change value — listener fires automatically
    volume.value = 0.5   # on_volume_change(1.0, 0.5) called

    # Batch multiple changes — listeners fire once on exit
    with volume.transaction():
        volume.value = 0.3
        volume.value = 0.2
        volume.value = 0.1
    # on_volume_change(0.5, 0.1) called once

    # Unsubscribe
    volume.unsubscribe(on_volume_change)

Weak references
---------------
Subscriptions to *bound methods* are held via weak references. When the
owning object is deleted, the subscription is silently removed on the next
notification. This prevents scenes and widgets from being kept alive by
observables after they have been discarded.

Subscriptions to plain functions and lambdas are held via strong references
and must be explicitly unsubscribed, or the owning object must call
``self.subscriptions.dispose()`` (via ``SubscriptionGroup``).

Subscriber signature
--------------------
Listeners receive ``(old_value, new_value)`` — old first, new second.
This order matches the mental model of undo/redo commands:
``undo = lambda old, new: state.set(old)``
"""

from __future__ import annotations

import inspect
import weakref
from contextlib import contextmanager
from typing import Callable, Generator, Generic, TypeVar

T = TypeVar("T")

# Listener signature: (old_value, new_value) -> None
Listener = Callable[[T, T], None]


# ── Weak reference helpers ────────────────────────────────────────────────────

def _make_ref(fn: Listener) -> tuple[str, object]:
    """
    Return a (kind, ref) pair for ``fn``.

    Bound methods use ``WeakMethod`` so that deleting the owning object
    silently removes the subscription. Everything else (plain functions,
    lambdas, callable objects) uses a strong reference — the caller is
    responsible for managing the lifecycle.
    """
    if inspect.ismethod(fn):
        return ("weak", weakref.WeakMethod(fn))
    return ("strong", fn)


def _deref(entry: tuple[str, object]) -> Listener | None:
    """Return the live callable from a ref entry, or ``None`` if dead."""
    kind, ref = entry
    if kind == "weak":
        return ref()  # type: ignore[return-value]
    return ref  # type: ignore[return-value]


def _ref_matches(entry: tuple[str, object], fn: Listener) -> bool:
    """Return True if the ref entry refers to the same callable as ``fn``."""
    live = _deref(entry)
    if live is None:
        return False
    return live == fn


# ── Observable ────────────────────────────────────────────────────────────────

class Observable(Generic[T]):
    """
    A value wrapper that notifies subscribers when its value changes.

    Type parameter ``T`` is the type of the wrapped value.

    Thread safety: not thread-safe. Intended for single-threaded
    game loops only.

    Subscriber signature: ``callback(old_value: T, new_value: T) -> None``
    """

    def __init__(self, initial: T) -> None:
        """
        Args:
            initial: The starting value.
        """
        self._value:           T                           = initial
        self._listeners:       list[tuple[str, object]]   = []
        self._in_transaction:  bool                        = False
        self._pending_old:     T | None                    = None

    # ── Value access ──────────────────────────────────────────────────────────

    @property
    def value(self) -> T:
        """The current wrapped value."""
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        """
        Set a new value and notify listeners if it changed.

        Listeners are called with ``(old_value, new_value)``.
        Setting the same value does not notify listeners.

        Inside a ``transaction()`` block, the notification is deferred
        until the block exits and fires only once.
        """
        if new_value == self._value:
            return
        old_value   = self._value
        self._value = new_value
        if not self._in_transaction:
            self._notify(old_value, new_value)

    def set_silent(self, new_value: T) -> None:
        """
        Set a new value WITHOUT notifying listeners.

        Use sparingly — bypasses the reactive contract.

        Args:
            new_value: The value to store silently.
        """
        self._value = new_value

    # ── Transactions ──────────────────────────────────────────────────────────

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """
        Context manager that batches multiple changes into one notification.

        All ``value`` assignments inside the block are applied immediately
        but listeners are not called until the block exits. They receive
        ``(old_value, new_value)`` where ``old_value`` is the value at the
        start of the transaction and ``new_value`` is the final value.

        If the value is unchanged at block exit, no notification is sent.

        Nested transactions are transparent — the innermost block does not
        fire a separate event; the outermost block fires once.

        Usage::

            with observable.transaction():
                observable.value = 1
                observable.value = 2
                observable.value = 3
            # listeners called once: (old, 3)
        """
        if self._in_transaction:
            # Already inside a transaction — inner block is transparent
            yield
            return

        self._in_transaction = True
        self._pending_old    = self._value
        try:
            yield
        finally:
            self._in_transaction = False
            final_value = self._value
            old_value   = self._pending_old
            self._pending_old = None
            if final_value != old_value:
                self._notify(old_value, final_value)

    # ── Subscription ──────────────────────────────────────────────────────────

    def subscribe(self, listener: Listener[T]) -> Listener[T]:
        """
        Register a listener to be called on value change.

        The listener receives ``(old_value, new_value)`` on each change.

        Bound methods are held via weak reference — when the owning object
        is deleted the subscription is silently removed.

        Plain functions and lambdas are held via strong reference — call
        ``unsubscribe()`` explicitly or use a ``SubscriptionGroup``.

        Adding the same listener twice is a no-op.

        Args:
            listener: Callable taking ``(old_value: T, new_value: T)``.

        Returns:
            The listener itself (used as an unsubscription token).
        """
        if not any(_ref_matches(e, listener) for e in self._listeners):
            self._listeners.append(_make_ref(listener))
        return listener

    def unsubscribe(self, listener: Listener[T]) -> None:
        """
        Remove a previously registered listener.

        Removing a listener that was never registered is a no-op.

        Args:
            listener: The listener to remove (the same object passed to
                      ``subscribe()``).
        """
        self._listeners = [
            e for e in self._listeners if not _ref_matches(e, listener)
        ]

    def clear_listeners(self) -> None:
        """Remove all registered listeners."""
        self._listeners.clear()

    @property
    def listener_count(self) -> int:
        """Number of currently live registered listeners."""
        return sum(1 for e in self._listeners if _deref(e) is not None)

    # ── Representation ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Observable({self._value!r})"

    # ── Internal ──────────────────────────────────────────────────────────────

    def _notify(self, old_value: T, new_value: T) -> None:
        """
        Call all live listeners with ``(old_value, new_value)``.

        Dead weak references are pruned from the list during iteration.
        """
        live: list[tuple[str, object]] = []
        for entry in self._listeners:
            fn = _deref(entry)
            if fn is not None:
                live.append(entry)
                fn(old_value, new_value)
        self._listeners = live
