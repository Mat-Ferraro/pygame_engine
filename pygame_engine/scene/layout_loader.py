"""
pygame_engine.scene.layout_loader

``LayoutLoader`` — turns a ``SceneDescriptor`` into a live tree of real
widgets, and keeps the two in sync.

This module is the other half of "the descriptor is the source of truth".
The descriptor describes the UI; the loader *realises* it:

1. Walk the descriptor's node tree.
2. For each node, ask the widget registry to build the matching widget.
3. Add child widgets into their container parents.
4. Subscribe every widget's geometry to its node's ``rect`` so a change in
   the descriptor moves the live widget — the live binding the editor
   needs.

Type knowledge lives entirely in ``widget_registry``. This loader never
mentions a concrete widget type; it asks the registry to build nodes and to
say which types are containers.

Live binding
------------
For each built widget the loader calls ``node.rect.subscribe(...)`` with a
listener that pushes the new geometry into the widget via ``set_rect``. The
editor edits ``node.rect``; the listener fires; the widget moves. No polling,
no per-frame diffing.

The subscriptions are kept on the returned ``LoadedLayout`` so the scene can
release them in ``on_exit`` — see ``LoadedLayout.dispose()``.

Layout vs behaviour
-------------------
The loader builds *structure and geometry only*. Behaviour — a Button's
``on_click``, navigation — is not in the descriptor and is not wired here.
The owning scene attaches behaviour after loading by looking widgets up via
``widget_id`` (see ``LoadedLayout.by_id``).

Usage (from DescribedScene.on_enter)::

    from pygame_engine.scene.layout_loader import LayoutLoader

    loaded = LayoutLoader().load(self.layout)
    self.root_widget = loaded.root
    # ... later, scene binds behaviour:
    loaded.by_id("play_btn").on_click = self._on_play
    # ... in on_exit:
    loaded.dispose()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from pygame_engine.ui import Stack
from pygame_engine.ui.widget_registry import build_widget, is_container_type

if TYPE_CHECKING:
    from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode
    from pygame_engine.ui.base.widget import Widget


# ── Errors ────────────────────────────────────────────────────────────────────

class LayoutLoadError(Exception):
    """Raised when a descriptor cannot be realised into a widget tree."""


# ── LoadedLayout ──────────────────────────────────────────────────────────────

class LoadedLayout:
    """
    The result of loading a descriptor: the root widget plus the bookkeeping
    needed to look widgets up and to tear the binding down.

    Attributes
    ----------
    root:
        The single root ``Widget``. When the descriptor has multiple root
        nodes they are wrapped in a transparent ``Stack`` so the scene always
        has exactly one root widget to render.
    widgets:
        Mapping of ``widget_id`` -> built ``Widget`` for every node that had
        a non-empty id. Nodes without an id are still built and parented;
        they just are not looked-up-able.
    """

    def __init__(self, root: "Widget", widgets: dict[str, "Widget"]) -> None:
        self.root:    "Widget"               = root
        self.widgets: dict[str, "Widget"]    = widgets
        # Live rect subscriptions, kept so they can be released on dispose().
        self._unsubscribes: list[tuple] = []

    # ── Lookup ────────────────────────────────────────────────────────────────

    def by_id(self, widget_id: str) -> "Widget":
        """
        Return the widget built from the node with ``widget_id``.

        Raises:
            KeyError: If no widget has that id. This is deliberately loud —
                      a scene binding behaviour to a missing id is a bug
                      (a typo, or a renamed node), not something to paper
                      over with a silent no-op.
        """
        try:
            return self.widgets[widget_id]
        except KeyError:
            raise KeyError(
                f"No widget with widget_id {widget_id!r} in the loaded "
                f"layout. Known ids: {sorted(self.widgets)}"
            ) from None

    def find(self, widget_id: str) -> "Widget | None":
        """Return the widget for ``widget_id``, or ``None`` if absent."""
        return self.widgets.get(widget_id)

    # ── Teardown ──────────────────────────────────────────────────────────────

    def dispose(self) -> None:
        """
        Release every live rect subscription created for this layout.

        Call from the scene's ``on_exit``. After this the descriptor and the
        (now discarded) widgets no longer hold references to each other, so
        both can be garbage-collected cleanly.
        """
        for node_rect, listener in self._unsubscribes:
            try:
                node_rect.unsubscribe(listener)
            except (AttributeError, ValueError):
                # Older ObservableRect without unsubscribe, or already gone.
                # Falling back to clear_listeners would nuke unrelated
                # subscribers, so we simply drop our reference instead.
                pass
        self._unsubscribes.clear()

    # ── Internal — used by LayoutLoader ───────────────────────────────────────

    def _track_subscription(self, node_rect, listener) -> None:
        """Record a (rect, listener) pair so dispose() can release it."""
        self._unsubscribes.append((node_rect, listener))


# ── LayoutLoader ──────────────────────────────────────────────────────────────

class LayoutLoader:
    """
    Builds a live widget tree from a ``SceneDescriptor``.

    Stateless and reusable — one loader can load any number of descriptors.
    """

    def load(self, descriptor: "SceneDescriptor") -> LoadedLayout:
        """
        Realise ``descriptor`` into a live widget tree.

        Args:
            descriptor: The populated scene descriptor to build from.

        Returns:
            A ``LoadedLayout`` holding the root widget, the id lookup table,
            and the live rect subscriptions.

        Raises:
            LayoutLoadError:        If the descriptor has no nodes.
            UnknownWidgetTypeError: If a node's type has no registered
                                    builder (propagated from the registry).
        """
        roots = descriptor.roots
        if not roots:
            raise LayoutLoadError(
                "Cannot load an empty descriptor — it has no root nodes. "
                "Populate the descriptor in _build_layout() first."
            )

        widgets: dict[str, "Widget"] = {}
        loaded = LoadedLayout(root=_PLACEHOLDER, widgets=widgets)

        built_roots = [
            self._build_subtree(node, widgets, loaded) for node in roots
        ]

        # One descriptor root → that widget is the root. Several → wrap them
        # in a transparent Stack so the scene always has a single root.
        if len(built_roots) == 1:
            loaded.root = built_roots[0]
        else:
            bounds = _union_rect(built_roots)
            stack  = Stack(bounds)
            for w in built_roots:
                stack.add(w)
            loaded.root = stack

        return loaded

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_subtree(
        self,
        node:    "WidgetNode",
        widgets: dict[str, "Widget"],
        loaded:  LoadedLayout,
    ) -> "Widget":
        """
        Recursively build ``node`` and all its descendants.

        Returns the widget for ``node``, with all child widgets already
        added into it.
        """
        # Build this node's widget via the registry (raises on unknown type).
        widget = build_widget(node)

        # Register it for id lookup, if it has an id.
        if node.widget_id:
            if node.widget_id in widgets:
                raise LayoutLoadError(
                    f"Duplicate widget_id {node.widget_id!r} in descriptor. "
                    f"Widget ids must be unique within a scene."
                )
            widgets[node.widget_id] = widget

        # Wire the live binding: descriptor rect change -> widget.set_rect.
        self._bind_rect(node, widget, loaded)

        # Recurse into children.
        children = list(node.children)
        if children:
            if not is_container_type(node.type):
                # A node has children but its widget cannot hold them. This
                # is a descriptor authoring error — fail loudly rather than
                # silently dropping the children.
                raise LayoutLoadError(
                    f"Node {node.widget_id or node.type!r} of type "
                    f"{node.type!r} has {len(children)} child node(s), but "
                    f"{node.type!r} is not a container type. Only container "
                    f"widgets (e.g. Panel, Stack) may have children."
                )
            for child_node in children:
                child_widget = self._build_subtree(child_node, widgets, loaded)
                widget.add(child_widget)  # type: ignore[attr-defined]

        return widget

    @staticmethod
    def _bind_rect(
        node:   "WidgetNode",
        widget: "Widget",
        loaded: LoadedLayout,
    ) -> None:
        """
        Subscribe ``widget``'s geometry to ``node.rect``.

        After this, any change to the descriptor's rect — from the editor's
        inspector, a drag gizmo, or a loaded ``.layout.json`` — pushes the
        new geometry into the live widget via ``set_rect``.
        """
        def _on_rect_changed(_old: pygame.Rect, new: pygame.Rect) -> None:
            # set_rect is part of the baseline Widget contract.
            widget.set_rect(pygame.Rect(new))

        node.rect.subscribe(_on_rect_changed)
        loaded._track_subscription(node.rect, _on_rect_changed)


# ── Module helpers ────────────────────────────────────────────────────────────

#: Sentinel root used while a LoadedLayout is being constructed, before the
#: real root is known. Never escapes load().
_PLACEHOLDER: "Widget" = None  # type: ignore[assignment]


def _union_rect(widgets: list["Widget"]) -> pygame.Rect:
    """
    Return the bounding rect that encloses every widget in ``widgets``.

    Used to size the wrapper Stack when a descriptor has multiple roots.
    """
    rect = pygame.Rect(widgets[0].rect)
    for w in widgets[1:]:
        rect.union_ip(w.rect)
    return rect
