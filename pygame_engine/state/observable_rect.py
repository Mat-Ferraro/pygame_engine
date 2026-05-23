"""
ObservableRect — a pygame.Rect whose coordinate changes fire a single
batched notification.

Unlike wrapping four separate ``Observable[int]`` values, ``ObservableRect``
treats a coordinate change as an atomic operation. Moving a widget from
(0, 0) to (100, 200) fires one event — ``(old_rect, new_rect)`` — not four.
This is essential for the editor: every drag gesture is one undo step, not
four.

Usage::

    from pygame_engine.state.observable_rect import ObservableRect

    rect = ObservableRect(10, 20, 200, 100)

    def on_moved(old, new):
        print(f"moved from {old} to {new}")

    rect.subscribe(on_moved)

    rect.x = 50          # fires once: old=(10,20,200,100), new=(50,20,200,100)
    rect.set(50, 20, 300, 100)  # fires once regardless of how many coords changed

    with rect.transaction():
        rect.x = 0
        rect.y = 0
        rect.w = 640
        rect.h = 480
    # fires once on exit

    pygame_rect = rect.to_pygame_rect()

Subscriber signature
--------------------
Listeners receive ``(old_rect, new_rect)`` where each value is a
``pygame.Rect`` snapshot (a copy, not the live rect).

``old_rect`` is the state at the moment the change began.
``new_rect`` is the state after the change completed.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Generator

import pygame

# Listener: (old_rect: pygame.Rect, new_rect: pygame.Rect) -> None
Listener = Callable[[pygame.Rect, pygame.Rect], None]


class ObservableRect:
    """
    A rectangle whose coordinate changes fire a single batched notification.

    Coordinates (x, y, w, h) are plain ints — no clamping, no validation.
    Negative width or height is allowed (consistent with pygame.Rect).

    Subscriber signature: ``callback(old_rect: pygame.Rect, new_rect: pygame.Rect)``
    where both arguments are ``pygame.Rect`` copies (not live references).
    """

    def __init__(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0) -> None:
        """
        Args:
            x: Left edge in pixels.
            y: Top edge in pixels.
            w: Width in pixels.
            h: Height in pixels.
        """
        self._x: int = int(x)
        self._y: int = int(y)
        self._w: int = int(w)
        self._h: int = int(h)

        self._listeners:      list[Listener] = []
        self._in_transaction: bool           = False
        self._pending_old:    pygame.Rect | None = None

    # ── Coordinate properties ─────────────────────────────────────────────────

    @property
    def x(self) -> int:
        """Left edge in pixels."""
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        if int(value) != self._x:
            old = self._snapshot()
            self._x = int(value)
            self._notify_if_not_in_transaction(old)

    @property
    def y(self) -> int:
        """Top edge in pixels."""
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        if int(value) != self._y:
            old = self._snapshot()
            self._y = int(value)
            self._notify_if_not_in_transaction(old)

    @property
    def w(self) -> int:
        """Width in pixels."""
        return self._w

    @w.setter
    def w(self, value: int) -> None:
        if int(value) != self._w:
            old = self._snapshot()
            self._w = int(value)
            self._notify_if_not_in_transaction(old)

    @property
    def h(self) -> int:
        """Height in pixels."""
        return self._h

    @h.setter
    def h(self, value: int) -> None:
        if int(value) != self._h:
            old = self._snapshot()
            self._h = int(value)
            self._notify_if_not_in_transaction(old)

    # ── Atomic multi-coordinate update ────────────────────────────────────────

    def set(self, x: int, y: int, w: int, h: int) -> None:
        """
        Set all four coordinates atomically, firing at most one notification.

        If no coordinate changes, no notification is sent.

        Args:
            x: New left edge.
            y: New top edge.
            w: New width.
            h: New height.
        """
        nx, ny, nw, nh = int(x), int(y), int(w), int(h)
        if (nx, ny, nw, nh) == (self._x, self._y, self._w, self._h):
            return
        old = self._snapshot()
        self._x, self._y, self._w, self._h = nx, ny, nw, nh
        self._notify_if_not_in_transaction(old)

    def move_to(self, x: int, y: int) -> None:
        """
        Move the rect to a new position without changing its size.

        Fires at most one notification.

        Args:
            x: New left edge.
            y: New top edge.
        """
        self.set(x, y, self._w, self._h)

    def resize(self, w: int, h: int) -> None:
        """
        Resize the rect without changing its position.

        Fires at most one notification.

        Args:
            w: New width.
            h: New height.
        """
        self.set(self._x, self._y, w, h)

    # ── Transaction ───────────────────────────────────────────────────────────

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """
        Batch multiple coordinate changes into one notification.

        All changes inside the block are applied immediately but subscribers
        are not called until the block exits. If the rect is unchanged at
        block exit, no notification is sent.

        Nested transactions are transparent — only the outermost fires.

        Usage::

            with rect.transaction():
                rect.x = 0
                rect.y = 0
                rect.w = 640
                rect.h = 480
            # one notification fired here
        """
        if self._in_transaction:
            yield
            return

        self._in_transaction = True
        self._pending_old    = self._snapshot()
        try:
            yield
        finally:
            self._in_transaction = False
            old      = self._pending_old
            self._pending_old = None
            new_snap = self._snapshot()
            if old != new_snap:
                self._notify(old, new_snap)

    # ── Conversion ────────────────────────────────────────────────────────────

    def to_pygame_rect(self) -> pygame.Rect:
        """
        Return a ``pygame.Rect`` copy of the current coordinates.

        The returned rect is a snapshot — it does not update when the
        ``ObservableRect`` changes.
        """
        return pygame.Rect(self._x, self._y, self._w, self._h)

    @classmethod
    def from_pygame_rect(cls, rect: pygame.Rect) -> "ObservableRect":
        """
        Create an ``ObservableRect`` from an existing ``pygame.Rect``.

        Args:
            rect: Source rect. Values are copied — the ObservableRect is
                  independent of the source after construction.
        """
        return cls(rect.x, rect.y, rect.width, rect.height)

    # ── Subscription ──────────────────────────────────────────────────────────

    def subscribe(self, listener: Listener) -> Listener:
        """
        Register a listener to be called when any coordinate changes.

        The listener receives ``(old_rect, new_rect)`` as ``pygame.Rect``
        copies. Adding the same listener twice is a no-op.

        Args:
            listener: Callable taking ``(old_rect, new_rect)``.

        Returns:
            The listener itself, usable as an unsubscription token.
        """
        if listener not in self._listeners:
            self._listeners.append(listener)
        return listener

    def unsubscribe(self, listener: Listener) -> None:
        """
        Remove a previously registered listener. No-op if not registered.

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
        """Number of registered listeners."""
        return len(self._listeners)

    # ── Equality and repr ─────────────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ObservableRect):
            return (self._x, self._y, self._w, self._h) == (
                other._x, other._y, other._w, other._h
            )
        if isinstance(other, pygame.Rect):
            return (self._x, self._y, self._w, self._h) == (
                other.x, other.y, other.width, other.height
            )
        return NotImplemented

    def __repr__(self) -> str:
        return (
            f"ObservableRect(x={self._x}, y={self._y}, "
            f"w={self._w}, h={self._h})"
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _snapshot(self) -> pygame.Rect:
        """Return a pygame.Rect copy of the current state."""
        return pygame.Rect(self._x, self._y, self._w, self._h)

    def _notify(self, old: pygame.Rect, new: pygame.Rect) -> None:
        """Call all listeners with old and new rect snapshots."""
        for listener in list(self._listeners):
            listener(old, new)

    def _notify_if_not_in_transaction(self, old: pygame.Rect) -> None:
        """Fire notification only when not inside a transaction block."""
        if not self._in_transaction:
            self._notify(old, self._snapshot())
        # If inside transaction, the outermost transaction block will notify.
