"""
Layout DSL — ``SceneDescriptor.builder()`` context manager.

Adds a fluent ``L.panel()``, ``L.stack()``, ``L.button()``, ``L.label()``,
``L.dynamic()`` interface for populating a ``SceneDescriptor``
declaratively inside ``DescribedScene._build_layout()``.

This module monkey-patches ``builder()`` onto ``SceneDescriptor`` when
imported. Import it at the top of any ``DescribedScene`` subclass file::

    from pygame_engine.scene import layout_builder  # noqa: F401

Or it is imported automatically when you use ``DescribedScene``.

Usage::

    def _build_layout(self) -> None:
        with self.layout.builder() as L:
            L.stack("root", x=0, y=0, w=1280, h=720)
            L.panel("sidebar", x=0, y=0, w=240, h=720, parent="root")
            L.button("start_btn", x=8, y=8, w=224, h=44,
                     parent="sidebar", label="Start Game")
            L.dynamic("hero_rows", parent="sidebar",
                      placeholder_count=4, placeholder_height=80)

All keyword arguments beyond ``x, y, w, h, parent`` are stored as
``Observable`` props on the ``WidgetNode``.

The named methods (``panel``, ``stack``, ``button`` …) cover the engine's
built-in widget types. For a custom widget type registered with the widget
registry, use ``L.node("MyType", ...)``.

``L.dynamic()`` marks the node as a runtime-filled region. The editor
renders placeholder rows for it; the scene fills it with real widgets.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode
from pygame_engine.state.observable import Observable
from pygame_engine.state.observable_rect import ObservableRect


class LayoutBuilder:
    """
    Fluent builder for ``SceneDescriptor``.

    Created by ``SceneDescriptor.builder()`` and used as a context manager.
    All methods return ``self`` for optional chaining, but the typical
    pattern is one call per line inside a ``with`` block.
    """

    def __init__(self, descriptor: SceneDescriptor) -> None:
        self._d = descriptor

    def _add(
        self,
        widget_type: str,
        widget_id:   str,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        parent: str | None = None,
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """Common node creation logic shared by all builder methods."""
        props: dict[str, Observable] = {
            k: Observable(v) for k, v in kwargs.items()
        }
        node = WidgetNode(
            widget_id = widget_id,
            type      = widget_type,
            rect      = ObservableRect(x, y, w, h),
            props     = props,
        )
        self._d.add(node, parent_id=parent)
        return self

    # ── Containers ────────────────────────────────────────────────────────────

    def panel(
        self,
        widget_id: str,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        parent: str | None = None,
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """
        Add a Panel node — a container with a styled background and border.

        Args:
            widget_id: Unique identifier.
            x, y, w, h: Geometry in pixels.
            parent: Parent node ID, or None for a root node.
            **kwargs: Additional props stored as Observable values.
        """
        return self._add("Panel", widget_id, x, y, w, h, parent, **kwargs)

    def stack(
        self,
        widget_id: str,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        parent: str | None = None,
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """
        Add a Stack node — a transparent grouping/layering container.

        Use a Stack when you want grouping without a visible background —
        root widget trees, HUD layers, overlays. Use ``panel()`` when you
        want a surfaced background and border.

        Args:
            widget_id: Unique identifier.
            x, y, w, h: Geometry in pixels.
            parent: Parent node ID, or None for a root node.
            **kwargs: Additional props stored as Observable values.
        """
        return self._add("Stack", widget_id, x, y, w, h, parent, **kwargs)

    # ── Controls ──────────────────────────────────────────────────────────────

    def button(
        self,
        widget_id: str,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        parent: str | None = None,
        label: str = "",
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """
        Add a Button node.

        Args:
            widget_id: Unique identifier.
            x, y, w, h: Geometry in pixels.
            parent: Parent node ID.
            label: Button label text (stored as a prop).
            **kwargs: Additional props.
        """
        return self._add("Button", widget_id, x, y, w, h, parent,
                         label=label, **kwargs)

    def label(
        self,
        widget_id: str,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        parent: str | None = None,
        text: str = "",
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """
        Add a Label node.

        Args:
            widget_id: Unique identifier.
            x, y, w, h: Geometry in pixels.
            parent: Parent node ID.
            text: Label text (stored as a prop).
            **kwargs: Additional props.
        """
        return self._add("Label", widget_id, x, y, w, h, parent,
                         text=text, **kwargs)

    def input_field(
        self,
        widget_id: str,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        parent: str | None = None,
        placeholder: str = "",
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """Add an InputField node."""
        return self._add("InputField", widget_id, x, y, w, h, parent,
                         placeholder=placeholder, **kwargs)

    def image(
        self,
        widget_id: str,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        parent: str | None = None,
        src: str = "",
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """Add an Image node."""
        return self._add("Image", widget_id, x, y, w, h, parent,
                         src=src, **kwargs)

    def dynamic(
        self,
        widget_id: str,
        parent: str | None = None,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        placeholder_count: int = 1,
        placeholder_height: int = 48,
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """
        Add a Dynamic region — a runtime-filled area.

        The editor renders placeholder rows to visualise the region.
        At runtime, scene code fills this area with real widgets.

        Args:
            widget_id:          Unique identifier.
            parent:             Parent node ID.
            x, y, w, h:        Geometry in pixels.
            placeholder_count:  How many placeholder rows to show in the editor.
            placeholder_height: Height of each placeholder row in pixels.
            **kwargs:           Additional props.
        """
        return self._add(
            "Dynamic", widget_id, x, y, w, h, parent,
            placeholder_count=placeholder_count,
            placeholder_height=placeholder_height,
            **kwargs,
        )

    def node(
        self,
        widget_type: str,
        widget_id:   str,
        x: int = 0, y: int = 0, w: int = 0, h: int = 0,
        parent: str | None = None,
        **kwargs: Any,
    ) -> "LayoutBuilder":
        """
        Add an arbitrary node type not covered by the named helpers.

        Use this for custom widget types defined in your game project and
        registered with the widget registry.

        Args:
            widget_type: The widget class name (e.g. ``"HeroCard"``).
            widget_id:   Unique identifier.
            x, y, w, h: Geometry in pixels.
            parent:      Parent node ID.
            **kwargs:    Additional props.
        """
        return self._add(widget_type, widget_id, x, y, w, h, parent, **kwargs)


# ── Patch builder() onto SceneDescriptor ─────────────────────────────────────

@contextmanager
def _builder(self: SceneDescriptor) -> Generator[LayoutBuilder, None, None]:
    """
    Context manager that yields a ``LayoutBuilder`` for this descriptor.

    Usage::

        with descriptor.builder() as L:
            L.stack("root", x=0, y=0, w=1280, h=720)
    """
    yield LayoutBuilder(self)


# Attach as a method on SceneDescriptor
SceneDescriptor.builder = _builder  # type: ignore[attr-defined]
