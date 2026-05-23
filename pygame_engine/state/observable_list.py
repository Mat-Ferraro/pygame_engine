"""
ObservableList[T] — a list that notifies subscribers when items are
added, removed, or reordered.

Unlike wrapping a plain list in a single ``Observable``, ``ObservableList``
carries structured change information so subscribers can react efficiently —
a hierarchy panel only needs to re-render the affected row, not the whole
tree.

Usage::

    from pygame_engine.state.observable_list import ObservableList

    nodes: ObservableList[str] = ObservableList()

    def on_change(event):
        print(event.kind, event.index, event.item)

    nodes.subscribe(on_change)

    nodes.append("alpha")       # ListEvent(kind="add",    index=0, item="alpha")
    nodes.insert(0, "beta")     # ListEvent(kind="add",    index=0, item="beta")
    nodes.remove("alpha")       # ListEvent(kind="remove", index=1, item="alpha")
    nodes[0] = "gamma"          # ListEvent(kind="replace",index=0, item="gamma")
    nodes.move(0, 1)            # ListEvent(kind="move",   index=0, item="gamma")

Change event
------------
Listeners receive a ``ListEvent`` dataclass::

    @dataclass
    class ListEvent:
        kind:      str   # "add" | "remove" | "replace" | "move" | "clear"
        index:     int   # position of the change (-1 for "clear")
        item:      T     # the item involved (None for "clear")
        old_index: int   # source index for "move", -1 otherwise
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Iterator, TypeVar, overload

T = TypeVar("T")

# ── Change event ──────────────────────────────────────────────────────────────

@dataclass
class ListEvent(Generic[T]):
    """
    Describes a single structural change to an ``ObservableList``.

    Attributes:
        kind:      The type of change — one of ``"add"``, ``"remove"``,
                   ``"replace"``, ``"move"``, or ``"clear"``.
        index:     The position where the change occurred.
                   For ``"clear"`` this is ``-1``.
        item:      The item that was added, removed, replaced, or moved.
                   For ``"clear"`` this is ``None``.
        old_index: The original position for ``"move"`` events.
                   ``-1`` for all other event kinds.
    """
    kind:      str
    index:     int
    item:      object   # T, but dataclass + Generic needs object here
    old_index: int = -1


# Listener signature: (event: ListEvent[T]) -> None
Listener = Callable[[ListEvent], None]


# ── ObservableList ────────────────────────────────────────────────────────────

class ObservableList(Generic[T]):
    """
    A list that fires a ``ListEvent`` whenever its contents change.

    Supports all standard list operations. Subscribers receive a
    ``ListEvent`` describing the change — they do not receive the full
    list before and after, keeping notification cost O(1).

    Thread safety: not thread-safe. Intended for single-threaded game loops.
    """

    def __init__(self, initial: list[T] | None = None) -> None:
        """
        Args:
            initial: Optional initial contents. Copied — not stored by reference.
                     No notification is fired during construction.
        """
        self._items:     list[T]      = list(initial) if initial else []
        self._listeners: list[Listener] = []

    # ── List read interface ───────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __contains__(self, item: object) -> bool:
        return item in self._items

    def __getitem__(self, index: int) -> T:
        return self._items[index]

    def index(self, item: T) -> int:
        """Return the index of ``item``. Raises ``ValueError`` if not found."""
        return self._items.index(item)

    def copy(self) -> list[T]:
        """Return a plain list copy of the current contents."""
        return list(self._items)

    # ── List write interface ──────────────────────────────────────────────────

    def __setitem__(self, index: int, item: T) -> None:
        """Replace the item at ``index``. Fires a ``"replace"`` event."""
        self._items[index] = item
        self._notify(ListEvent(kind="replace", index=index, item=item))

    def append(self, item: T) -> None:
        """
        Add ``item`` to the end of the list.

        Fires an ``"add"`` event with the new item's index.

        Args:
            item: The item to append.
        """
        self._items.append(item)
        self._notify(ListEvent(kind="add", index=len(self._items) - 1, item=item))

    def insert(self, index: int, item: T) -> None:
        """
        Insert ``item`` before ``index``.

        Fires an ``"add"`` event.

        Args:
            index: Position to insert at.
            item:  The item to insert.
        """
        self._items.insert(index, item)
        self._notify(ListEvent(kind="add", index=index, item=item))

    def remove(self, item: T) -> None:
        """
        Remove the first occurrence of ``item``.

        Fires a ``"remove"`` event. Raises ``ValueError`` if not found.

        Args:
            item: The item to remove.
        """
        idx = self._items.index(item)
        self._items.remove(item)
        self._notify(ListEvent(kind="remove", index=idx, item=item))

    def pop(self, index: int = -1) -> T:
        """
        Remove and return the item at ``index`` (default: last item).

        Fires a ``"remove"`` event.

        Args:
            index: Position to remove from. Negative indices are supported.

        Returns:
            The removed item.
        """
        resolved = index if index >= 0 else len(self._items) + index
        item = self._items.pop(index)
        self._notify(ListEvent(kind="remove", index=resolved, item=item))
        return item

    def move(self, from_index: int, to_index: int) -> None:
        """
        Move the item at ``from_index`` to ``to_index``.

        Fires a ``"move"`` event. Both indices must be valid.

        Args:
            from_index: Current position of the item.
            to_index:   Destination position.
        """
        if from_index == to_index:
            return
        item = self._items.pop(from_index)
        self._items.insert(to_index, item)
        self._notify(ListEvent(
            kind="move", index=to_index, item=item, old_index=from_index
        ))

    def clear(self) -> None:
        """
        Remove all items.

        Fires a single ``"clear"`` event regardless of how many items existed.
        """
        self._items.clear()
        self._notify(ListEvent(kind="clear", index=-1, item=None))

    # ── Subscription ──────────────────────────────────────────────────────────

    def subscribe(self, listener: Listener) -> Listener:
        """
        Register a listener to be called on any structural change.

        The listener receives a ``ListEvent`` describing the change.
        Adding the same listener twice is a no-op.

        Args:
            listener: Callable taking ``(event: ListEvent[T])``.

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

    # ── Repr ─────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"ObservableList({self._items!r})"

    # ── Internal ──────────────────────────────────────────────────────────────

    def _notify(self, event: ListEvent) -> None:
        """Call all listeners with the change event."""
        for listener in list(self._listeners):
            listener(event)
