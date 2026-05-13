"""
DialogueRunner — executes a DialogueScript.

The runner is a pure state machine with no rendering. It tracks the current
node, manages choices, and fires callbacks on actions and completion.
Games drive it by calling ``advance()`` or ``select_choice()``.

Usage::

    from pygame_engine.dialogue import DialogueRunner, DialogueScript

    script = DialogueScript({
        "start": {"speaker": "NPC", "text": "Hello!", "next": "end"},
        "end":   {"text": ""},
    })
    runner = DialogueRunner(script)
    runner.on_action  = lambda tag, node: print(f"action: {tag}")
    runner.on_complete = lambda: print("dialogue done")

    runner.start()
    print(runner.current_node.text)   # "Hello!"
    runner.advance()                  # moves to "end"
    print(runner.is_complete)         # True
"""

from __future__ import annotations

from typing import Callable

from pygame_engine.dialogue.script import DialogueNode, DialogueScript


class DialogueRunner:
    """
    State machine that executes a DialogueScript.

    States
    ------
    - Not started: ``current_node`` is None, ``is_complete`` is False.
    - Running, no choices: call ``advance()`` to move to the next node.
    - Running, awaiting choice: call ``select_choice(index)`` to branch.
    - Complete: ``is_complete`` is True; ``current_node`` is the last node.

    Callbacks
    ---------
    ``on_action(tag, node)``  — fired when a node with a non-empty ``action``
                                is entered, and when a choice with an action
                                is selected.
    ``on_complete()``         — fired when the dialogue reaches its end
                                (a node with no ``next`` and no choices).
    ``on_node_enter(node)``   — fired every time a new node is entered.
                                Useful for playing voices, updating portraits, etc.

    Args:
        script: The validated DialogueScript to execute.
    """

    def __init__(self, script: DialogueScript) -> None:
        self._script:   DialogueScript     = script
        self._current:  DialogueNode | None = None
        self._complete: bool               = False

        self.on_action:    Callable[[str, DialogueNode], None] | None = None
        self.on_complete:  Callable[[], None] | None                  = None
        self.on_node_enter: Callable[[DialogueNode], None] | None     = None

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def current_node(self) -> DialogueNode | None:
        """The currently active dialogue node, or None if not started."""
        return self._current

    @property
    def is_complete(self) -> bool:
        """True when the dialogue has reached its end."""
        return self._complete

    @property
    def is_started(self) -> bool:
        """True after ``start()`` has been called."""
        return self._current is not None or self._complete

    @property
    def has_choices(self) -> bool:
        """True if the current node requires a player choice to advance."""
        return (
            self._current is not None
            and len(self._current.choices) > 0
        )

    @property
    def choices(self) -> list:
        """The Choice objects for the current node, or empty list."""
        if self._current is None:
            return []
        return list(self._current.choices)

    def start(self, node_id: str | None = None) -> None:
        """
        Begin the dialogue at the start node (or a specific node).

        Args:
            node_id: Override the start node. Defaults to
                     ``script.start_node``.
        """
        self._complete = False
        target = node_id or self._script.start_node
        self._enter_node(target)

    def advance(self) -> None:
        """
        Advance to the next node.

        No-op if the dialogue is complete, not started, or awaiting a choice.
        If the current node has no ``next``, marks the dialogue complete.
        """
        if self._complete or self._current is None:
            return
        if self.has_choices:
            return   # must use select_choice() instead

        next_id = self._current.next
        if next_id is None:
            self._finish()
        else:
            self._enter_node(next_id)

    def select_choice(self, index: int) -> None:
        """
        Select a choice by index and advance to the target node.

        Args:
            index: Index into ``current_node.choices``.

        Raises:
            ValueError: If the current node has no choices or index is
                        out of range.
        """
        if self._current is None or not self.has_choices:
            raise ValueError("No choices available on the current node.")
        if index < 0 or index >= len(self._current.choices):
            raise ValueError(
                f"Choice index {index} out of range "
                f"(node has {len(self._current.choices)} choices)."
            )
        choice = self._current.choices[index]

        # Fire choice action before navigating
        if choice.action and self.on_action:
            self.on_action(choice.action, self._current)

        self._enter_node(choice.next)

    def jump(self, node_id: str) -> None:
        """
        Jump directly to a named node.

        Useful for skipping ahead, replaying a section, or implementing
        conditional branches from game code.

        Args:
            node_id: ID of the node to jump to.
        """
        self._complete = False
        self._enter_node(node_id)

    def reset(self) -> None:
        """Reset to the not-started state."""
        self._current  = None
        self._complete = False

    # ── Internal ──────────────────────────────────────────────────────────────

    def _enter_node(self, node_id: str) -> None:
        node = self._script.get(node_id)
        self._current = node

        if self.on_node_enter:
            self.on_node_enter(node)

        if node.action and self.on_action:
            self.on_action(node.action, node)

        # Auto-finish on empty end nodes (text == "" and no next and no choices)
        if not node.text and not node.next and not node.choices:
            self._finish()

    def _finish(self) -> None:
        self._complete = True
        if self.on_complete:
            self.on_complete()

    def __repr__(self) -> str:
        node_id = self._current.node_id if self._current else "None"
        return f"DialogueRunner(node={node_id!r}, complete={self._complete})"
