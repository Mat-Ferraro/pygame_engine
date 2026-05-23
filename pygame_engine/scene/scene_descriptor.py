"""
WidgetNode and SceneDescriptor — the live observable model of a scene's
widget tree.

``SceneDescriptor`` is the data model that bridges scene code and the scene
editor. A ``DescribedScene`` owns one ``SceneDescriptor``; the editor reads
and writes to that descriptor, and the scene reacts to changes via
subscriptions.

Architecture
------------
The descriptor holds a tree of ``WidgetNode`` objects. Each node describes
one widget: its type, rect, properties, and children. Changes to any node
fire ``on_any_change``; structural changes (add/remove) additionally fire
``on_structure_change``.

The editor binds its inspector to ``node.rect`` (an ``ObservableRect``) and
its hierarchy panel to the node tree via ``on_structure_change``. This gives
live two-way binding without any special editor-scene coupling.

Usage::

    from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode
    from pygame_engine.state.observable_rect import ObservableRect

    descriptor = SceneDescriptor()

    # Add nodes
    panel = WidgetNode(widget_id="main_panel", type="Panel",
                       rect=ObservableRect(0, 0, 400, 300))
    btn   = WidgetNode(widget_id="ok_btn", type="Button",
                       rect=ObservableRect(10, 10, 80, 32))
    descriptor.add(panel)
    descriptor.add(btn, parent_id="main_panel")

    # Save / load
    descriptor.save(Path("scenes/main_menu.layout.json"))
    descriptor.load(Path("scenes/main_menu.layout.json"))

Persistence notes
-----------------
``save()`` writes atomically: it serialises to a ``.tmp`` sibling file and
renames it over the destination. A failed write therefore never corrupts an
existing layout file. ``load()`` validates the envelope ``version`` and
raises ``ValueError`` on anything it does not recognise.

Property values are stored with their JSON-native type. Tuples are written
as lists (JSON has no tuple); on load they come back as lists. If a widget
needs a tuple (e.g. an RGBA colour) it should coerce the prop itself — the
descriptor does not guess.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pygame

from pygame_engine.state.observable import Observable
from pygame_engine.state.observable_list import ObservableList
from pygame_engine.state.observable_rect import ObservableRect


# ── Constants ─────────────────────────────────────────────────────────────────

#: Current layout-file schema version. Bump this whenever the on-disk shape
#: of a layout file changes in a way older loaders cannot read.
LAYOUT_FILE_VERSION = 1


# ── WidgetNode ────────────────────────────────────────────────────────────────

@dataclass
class WidgetNode:
    """
    A single node in the scene descriptor tree.

    Represents one widget: its identity, geometry, properties, and
    relationships to other nodes. All fields that the editor modifies are
    observable so the scene can react in real time.

    Fields reserved for future implementation are present but ignored by
    all current engine code.

    Args:
        widget_id:        Stable string identifier. Must be unique within
                          the scene. Used by the editor to identify widgets
                          across reloads and by code to look up nodes.
        type:             Widget class name (e.g. ``"Panel"``, ``"Button"``).
                          Used by the editor and the ``LayoutLoader`` to
                          instantiate the correct widget class.
        rect:             Observable geometry. The editor writes to this;
                          the scene reads from it.
        props:            Observable per-widget properties (label text,
                          colour overrides, etc.). Keys and value types are
                          widget-type-specific.
        children:         Observable ordered list of child ``WidgetNode``
                          objects. Structural changes fire
                          ``SceneDescriptor.on_structure_change``.
        parent:           Reference to the parent node, or ``None`` for
                          top-level nodes.
        anchor:           Reserved for future anchor system. Always ``None``
                          in v1.
        prefab_source:    Reserved. Path to a prefab layout file. ``None``
                          means this is not an instanced prefab.
        prefab_overrides: Reserved. Per-instance property overrides for a
                          prefab instance.
        editor_only:      When True this node is not instantiated at runtime.
                          Used for organisational folders in the hierarchy.
        editor_tags:      Arbitrary tags for hierarchy panel filtering.
        editor_visible:   When False the node is hidden in the hierarchy.
        editor_locked:    When True the node cannot be selected or moved in
                          the editor viewport.
    """

    widget_id:        str
    type:             str
    rect:             ObservableRect = field(default_factory=ObservableRect)

    # Observable properties — each value is an Observable wrapping the raw value
    props: dict[str, Observable] = field(default_factory=dict)

    # Tree structure
    children: ObservableList[WidgetNode] = field(
        default_factory=ObservableList
    )
    parent: WidgetNode | None = field(default=None, repr=False)

    # Reserved — not yet implemented
    anchor:           Any         = field(default=None, repr=False)
    prefab_source:    str | None  = field(default=None, repr=False)
    prefab_overrides: dict        = field(default_factory=dict, repr=False)

    # Editor metadata
    editor_only:    bool      = False
    editor_tags:    list[str] = field(default_factory=list)
    editor_visible: bool      = True
    editor_locked:  bool      = False

    def __repr__(self) -> str:
        child_count = len(self.children)
        return (
            f"WidgetNode(id={self.widget_id!r}, type={self.type!r}, "
            f"rect={self.rect!r}, children={child_count})"
        )


# ── SceneDescriptor ───────────────────────────────────────────────────────────

class SceneDescriptor:
    """
    The live observable model of a scene's widget tree.

    Owned by a ``DescribedScene``. The editor reads and writes to this;
    the scene reacts to changes via ``on_any_change`` and
    ``on_structure_change``.

    Change signals
    --------------
    ``on_any_change`` fires when any rect or property in the tree changes.
    ``on_structure_change`` fires when nodes are added, removed, or reordered.
    Both are ``Observable[int]`` — the value is a monotonically increasing
    change counter, useful as a cache-invalidation signal.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, WidgetNode] = {}
        self._roots: list[WidgetNode]      = []

        # Change signals — value is a monotonically increasing counter
        self.on_any_change:       Observable[int] = Observable(0)
        self.on_structure_change: Observable[int] = Observable(0)

        self._change_counter: int = 0

    # ── Node management ───────────────────────────────────────────────────────

    def add(
        self,
        node: WidgetNode,
        parent_id: str | None = None,
    ) -> None:
        """
        Add a node to the descriptor tree.

        Args:
            node:      The node to add. Its ``widget_id`` must be unique.
            parent_id: ID of the parent node. If ``None``, the node is added
                       as a top-level root node.

        Raises:
            ValueError: If ``node.widget_id`` already exists in the tree.
            KeyError:   If ``parent_id`` is given but not found.
        """
        if node.widget_id in self._nodes:
            raise ValueError(
                f"WidgetNode id {node.widget_id!r} already exists in descriptor."
            )
        if parent_id is not None:
            parent = self._nodes[parent_id]
            node.parent = parent
            parent.children.append(node)
            # Wire child-list changes to structure_change
            parent.children.subscribe(lambda ev: self._on_structure_change())
        else:
            node.parent = None
            self._roots.append(node)

        self._nodes[node.widget_id] = node

        # Wire change signals for this node. Factored into a helper so that a
        # node which is removed and later re-added (e.g. via undo) is fully
        # re-wired rather than left with stale, cleared listeners.
        self._wire_node(node)

        self._on_structure_change()

    def remove(self, widget_id: str) -> None:
        """
        Remove a node and all its descendants from the tree.

        Args:
            widget_id: ID of the node to remove.

        Raises:
            KeyError: If the node is not found.
        """
        node = self._nodes[widget_id]
        # Remove descendants first
        for child in list(node.children):
            self.remove(child.widget_id)

        # Detach from parent or roots
        if node.parent is not None:
            try:
                node.parent.children.remove(node)
            except ValueError:
                pass
        else:
            try:
                self._roots.remove(node)
            except ValueError:
                pass

        del self._nodes[widget_id]
        node.rect.clear_listeners()
        self._on_structure_change()

    def get(self, widget_id: str) -> WidgetNode:
        """
        Return the node with the given ``widget_id``.

        Raises:
            KeyError: If not found.
        """
        return self._nodes[widget_id]

    def has(self, widget_id: str) -> bool:
        """Return True if a node with ``widget_id`` exists."""
        return widget_id in self._nodes

    def clear(self) -> None:
        """Remove all nodes from the descriptor."""
        for node in list(self._nodes.values()):
            node.rect.clear_listeners()
        self._nodes.clear()
        self._roots.clear()
        self._on_structure_change()

    # ── Tree traversal ────────────────────────────────────────────────────────

    @property
    def roots(self) -> list[WidgetNode]:
        """Top-level nodes (those with no parent)."""
        return list(self._roots)

    @property
    def all_nodes(self) -> list[WidgetNode]:
        """All nodes in the tree, in insertion order."""
        return list(self._nodes.values())

    @property
    def node_count(self) -> int:
        """Total number of nodes in the descriptor."""
        return len(self._nodes)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: Path) -> None:
        """
        Serialise the descriptor tree to a JSON layout file, atomically.

        The data is written to a sibling ``.tmp`` file first, then renamed
        over the destination. A crash or exception mid-write therefore
        leaves any existing layout file intact.

        Args:
            path: Destination path. Parent directories are created if needed.

        Raises:
            OSError: If the file cannot be written or renamed.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": LAYOUT_FILE_VERSION,
            "nodes":   [self._serialise_node(n) for n in self._roots],
        }
        text = json.dumps(data, indent=2, ensure_ascii=False)

        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)   # atomic on the same filesystem

    def load(self, path: Path) -> None:
        """
        Load a JSON layout file and replace the current tree.

        Args:
            path: Source path.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError:        If the file is malformed or an unsupported
                               version.
        """
        path = Path(path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Layout file is not valid JSON: {path}\n  {exc}"
            ) from exc

        if not isinstance(raw, dict):
            raise ValueError(f"Layout file root must be an object: {path}")

        version = raw.get("version", 0)
        if version != LAYOUT_FILE_VERSION:
            raise ValueError(
                f"Unsupported layout file version: {version!r} "
                f"(expected {LAYOUT_FILE_VERSION}) in {path}"
            )

        self.clear()
        for node_data in raw.get("nodes", []):
            self._deserialise_node(node_data, parent_id=None)

    def load_or_default(self, path: Path, build_fn: Any) -> None:
        """
        Load from ``path`` if it exists; otherwise call ``build_fn()`` to
        populate the descriptor programmatically.

        If the file exists but fails to load (corrupt JSON, bad version),
        ``build_fn()`` is used as a fallback so the scene still opens.

        Typical usage in ``DescribedScene._build_layout()``::

            def _build_layout(self) -> None:
                self.layout.load_or_default(
                    Path("scenes/main_menu.layout.json"),
                    self._default_layout,
                )

        Args:
            path:     Layout file path.
            build_fn: Zero-argument callable that populates the descriptor.
                      Called when the file does not exist or cannot be read.
        """
        path = Path(path)
        if path.exists():
            try:
                self.load(path)
                return
            except (ValueError, OSError):
                # Corrupt or unreadable — fall through to the code default.
                self.clear()
        build_fn()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _wire_node(self, node: WidgetNode) -> None:
        """Subscribe a node's rect and props to the change signals."""
        node.rect.subscribe(lambda old, new: self._on_any_change())
        for obs in node.props.values():
            obs.subscribe(lambda old, new: self._on_any_change())

    def _on_any_change(self) -> None:
        self._change_counter += 1
        self.on_any_change.value = self._change_counter

    def _on_structure_change(self) -> None:
        self._change_counter += 1
        self.on_structure_change.value = self._change_counter
        self.on_any_change.value       = self._change_counter

    def _serialise_node(self, node: WidgetNode) -> dict:
        """Convert a WidgetNode to a JSON-serialisable dict."""
        props_out: dict[str, Any] = {}
        for key, obs in node.props.items():
            props_out[key] = _serialise_prop(obs.value)

        return {
            "widget_id":      node.widget_id,
            "type":           node.type,
            "rect":           [node.rect.x, node.rect.y,
                               node.rect.w, node.rect.h],
            "props":          props_out,
            "editor_only":    node.editor_only,
            "editor_tags":    list(node.editor_tags),
            "editor_visible": node.editor_visible,
            "editor_locked":  node.editor_locked,
            "children":       [self._serialise_node(c)
                               for c in node.children],
        }

    def _deserialise_node(
        self, data: dict, parent_id: str | None
    ) -> WidgetNode:
        """Reconstruct a WidgetNode from a dict and add it to the tree."""
        if "widget_id" not in data or "type" not in data:
            raise ValueError(
                f"Layout node missing required 'widget_id'/'type': {data!r}"
            )

        rect_raw = data.get("rect", [0, 0, 0, 0])
        if not (isinstance(rect_raw, (list, tuple)) and len(rect_raw) == 4):
            raise ValueError(
                f"Layout node {data['widget_id']!r} has a malformed rect: "
                f"{rect_raw!r}"
            )
        rx, ry, rw, rh = rect_raw
        rect = ObservableRect(rx, ry, rw, rh)

        props: dict[str, Observable] = {}
        for key, val in data.get("props", {}).items():
            props[key] = Observable(val)

        node = WidgetNode(
            widget_id      = data["widget_id"],
            type           = data["type"],
            rect           = rect,
            props          = props,
            editor_only    = data.get("editor_only",    False),
            editor_tags    = list(data.get("editor_tags", [])),
            editor_visible = data.get("editor_visible", True),
            editor_locked  = data.get("editor_locked",  False),
        )
        self.add(node, parent_id=parent_id)

        for child_data in data.get("children", []):
            self._deserialise_node(child_data, parent_id=node.widget_id)

        return node

    def __repr__(self) -> str:
        return f"SceneDescriptor(nodes={self.node_count}, roots={len(self._roots)})"


# ── Module helpers ────────────────────────────────────────────────────────────

def _serialise_prop(value: Any) -> Any:
    """
    Convert a single prop value into a JSON-native form.

    Tuples become lists (JSON has no tuple type). ``pygame.Color`` becomes a
    4-element RGBA list. Nested lists/tuples are converted recursively.
    Everything else is returned unchanged and assumed JSON-serialisable.
    """
    if isinstance(value, pygame.Color):
        return [value.r, value.g, value.b, value.a]
    if isinstance(value, (list, tuple)):
        return [_serialise_prop(item) for item in value]
    return value
