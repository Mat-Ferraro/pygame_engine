"""
Dialogue script format for pygame_engine.

A dialogue script is a plain Python dict (JSON-compatible). This module
provides the data structures and a validator so games can define scripts
clearly and catch errors early.

Script format
-------------
A script is a dict mapping node IDs to node dicts::

    {
        "start": {
            "speaker": "Guard",
            "text": "Halt! Who goes there?",
            "choices": [
                {"label": "A friend.", "next": "friendly"},
                {"label": "None of your business.", "next": "hostile"},
            ]
        },
        "friendly": {
            "speaker": "Guard",
            "text": "Very well. Pass.",
            "next": "end"
        },
        "hostile": {
            "speaker": "Guard",
            "text": "Then you shall not pass!",
            "next": "end"
        },
        "end": {
            "text": "",
        }
    }

Node fields
-----------
``speaker``  (str, optional)  — Who is speaking. Empty string or absent = narration.
``text``     (str, required)  — The dialogue text to display.
``next``     (str, optional)  — ID of the next node. Absent or None = dialogue ends.
``choices``  (list, optional) — List of choice dicts (see below). Overrides ``next``.
``action``   (str, optional)  — Arbitrary string tag; ``DialogueRunner`` fires a
                                callback when this node is reached.

Choice fields
-------------
``label``  (str, required) — Text shown on the choice button.
``next``   (str, required) — Node ID to jump to on selection.
``action`` (str, optional) — Action tag fired when this choice is selected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Choice:
    """A single selectable option in a branching dialogue node."""
    label:  str
    next:   str
    action: str = ""


@dataclass(frozen=True)
class DialogueNode:
    """
    One node in a dialogue script.

    Attrs:
        node_id: The unique identifier of this node within its script.
        text:    Dialogue text to display (may be empty for end nodes).
        speaker: Who is speaking. Empty string = narration.
        next:    ID of the node to advance to. None = end of dialogue.
        choices: If non-empty, player must choose instead of auto-advancing.
        action:  Optional event tag fired when this node is entered.
    """
    node_id: str
    text:    str
    speaker: str           = ""
    next:    str | None    = None
    choices: list[Choice]  = field(default_factory=list)
    action:  str           = ""


class DialogueScript:
    """
    A validated dialogue script.

    Wraps a raw dict and exposes nodes by ID. Validates on construction
    so errors are caught before the game runs.

    Args:
        raw:        The script dict (see module docstring for format).
        start_node: ID of the first node. Defaults to ``"start"``.

    Raises:
        ValueError: If the script is invalid (missing start node,
                    broken ``next`` references, etc.).
    """

    def __init__(
        self,
        raw:        dict,
        start_node: str = "start",
    ) -> None:
        self._start  = start_node
        self._nodes: dict[str, DialogueNode] = {}
        self._parse(raw)
        self._validate()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def start_node(self) -> str:
        return self._start

    def get(self, node_id: str) -> DialogueNode:
        """
        Return the node with the given ID.

        Raises:
            KeyError: If no node with that ID exists.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Dialogue node {node_id!r} not found in script.")
        return self._nodes[node_id]

    def has(self, node_id: str) -> bool:
        return node_id in self._nodes

    @property
    def node_ids(self) -> list[str]:
        return list(self._nodes.keys())

    # ── Internal ──────────────────────────────────────────────────────────────

    def _parse(self, raw: dict) -> None:
        for node_id, data in raw.items():
            if not isinstance(data, dict):
                raise ValueError(f"Node {node_id!r} must be a dict.")
            if "text" not in data:
                raise ValueError(f"Node {node_id!r} is missing required 'text' field.")

            raw_choices = data.get("choices", [])
            choices = [
                Choice(
                    label  = c["label"],
                    next   = c["next"],
                    action = c.get("action", ""),
                )
                for c in raw_choices
            ]

            self._nodes[node_id] = DialogueNode(
                node_id = node_id,
                text    = data["text"],
                speaker = data.get("speaker", ""),
                next    = data.get("next", None),
                choices = choices,
                action  = data.get("action", ""),
            )

    def _validate(self) -> None:
        if self._start not in self._nodes:
            raise ValueError(
                f"Start node {self._start!r} not found in script. "
                f"Available nodes: {sorted(self._nodes.keys())}"
            )

        for node in self._nodes.values():
            if node.next and node.next not in self._nodes:
                raise ValueError(
                    f"Node {node.node_id!r} references unknown next node {node.next!r}."
                )
            for choice in node.choices:
                if choice.next not in self._nodes:
                    raise ValueError(
                        f"Choice {choice.label!r} in node {node.node_id!r} "
                        f"references unknown node {choice.next!r}."
                    )

    def __repr__(self) -> str:
        return f"DialogueScript({len(self._nodes)} nodes, start={self._start!r})"
