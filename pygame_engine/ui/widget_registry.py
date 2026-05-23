"""
pygame_engine.ui.widget_registry

The single source of truth for which widget *types* exist and how each one
is constructed from a ``WidgetNode``.

Why a registry
--------------
A ``SceneDescriptor`` describes a UI as a tree of ``WidgetNode``s. Each node
carries a ``type`` string (``"Panel"``, ``"Button"``, …), a ``rect``, and a
bag of ``props``. To turn that tree into real widgets, something must map
each type string to a concrete widget class and know how to call its
constructor.

That knowledge does **not** belong scattered through the layout loader as
``if node.type == "Button": ...`` branches. It lives here, in one place, as
a table of *builder functions* — one per type. The loader stays completely
type-agnostic: it asks the registry to build a node and recurses into
children.

Builder functions, not ``cls(rect, **props)``
----------------------------------------------
Widget constructors are deliberately not uniform — ``Button(rect, label,
on_click)`` differs from ``Label(rect, text, font_size, colour, …)``. A
blanket ``cls(rect, **props)`` would break the moment a prop name does not
match a constructor parameter. So each type registers a small builder that
knows its own constructor and picks only the props it understands.

Layout vs behaviour
-------------------
The descriptor stores layout data only — it must stay JSON-serialisable.
Behaviour (a Button's ``on_click``, navigation callbacks) is **not** stored
and **not** built here. Builders construct the widget's structure and
geometry; the owning scene attaches behaviour afterward by looking the
widget up via ``widget_id``. Builders therefore ignore any callable-valued
or unrecognised prop rather than failing on it.

Registering custom types
-------------------------
Games define their own widget types. They register a builder with::

    from pygame_engine.ui.widget_registry import register

    @register("HeroCard")
    def _build_hero_card(spec):
        return HeroCard(spec.rect, title=spec.prop("title", ""))

Engine built-in types are registered at import time at the bottom of this
module.

Usage (from the layout loader)::

    from pygame_engine.ui.widget_registry import build_widget

    widget = build_widget(node)        # node is a WidgetNode
    for child_node in node.children:
        widget.add(build_widget(child_node))
"""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from pygame_engine.scene.scene_descriptor import WidgetNode
    from pygame_engine.ui.base.widget import Widget


# ── Errors ────────────────────────────────────────────────────────────────────

class UnknownWidgetTypeError(KeyError):
    """
    Raised when a ``WidgetNode.type`` has no registered builder.

    Carries the offending type string and the list of types that *are*
    registered, so the message points straight at the fix (a typo in a
    layout file, or a custom type that was never registered).
    """

    def __init__(self, widget_type: str, known: list[str]) -> None:
        self.widget_type = widget_type
        self.known       = known
        known_str = ", ".join(known) if known else "(none registered)"
        super().__init__(
            f"No widget builder registered for type {widget_type!r}. "
            f"Registered types: {known_str}. "
            f"Register a builder with widget_registry.register(), or check "
            f"the type string in the layout/descriptor."
        )


# ── Build spec ────────────────────────────────────────────────────────────────

class WidgetBuildSpec:
    """
    The read-only view of a ``WidgetNode`` handed to a builder function.

    A thin wrapper rather than the raw node, so builders depend on a small,
    stable surface (``rect``, ``widget_id``, ``prop()``) and never reach into
    descriptor internals or the observable machinery.

    ``prop()`` unwraps a node's ``Observable`` props to plain values and
    applies a default for anything absent.
    """

    __slots__ = ("widget_id", "type", "rect", "_props")

    def __init__(self, node: "WidgetNode") -> None:
        r = node.rect
        self.widget_id: str | None = node.widget_id
        self.type:      str        = node.type
        self.rect:      pygame.Rect = pygame.Rect(
            int(r.x), int(r.y), int(r.w), int(r.h),
        )
        # Snapshot prop values, unwrapping Observables to plain values.
        self._props: dict[str, Any] = {
            key: getattr(obs, "value", obs)
            for key, obs in node.props.items()
        }

    def prop(self, key: str, default: Any = None) -> Any:
        """
        Return the plain value of prop ``key``, or ``default`` if absent.

        Builders use this to pull the props they understand. Props a builder
        does not ask for are simply ignored — that is how an unknown or
        behaviour-only prop never breaks a build.
        """
        return self._props.get(key, default)

    def has_prop(self, key: str) -> bool:
        """Return True if prop ``key`` is present on the node."""
        return key in self._props


# ── Registry ──────────────────────────────────────────────────────────────────

#: A builder takes a WidgetBuildSpec and returns a constructed Widget.
#: It must NOT add children — the layout loader owns tree assembly.
WidgetBuilder = Callable[[WidgetBuildSpec], "Widget"]

#: type string -> builder function
_REGISTRY: dict[str, WidgetBuilder] = {}

#: type strings whose widgets are containers (support ``.add(child)``).
#: The layout loader consults this to know whether to recurse children into
#: the widget or treat it as a leaf.
_CONTAINER_TYPES: set[str] = set()


def register(
    widget_type: str,
    *,
    container: bool = False,
) -> Callable[[WidgetBuilder], WidgetBuilder]:
    """
    Decorator — register a builder function for a widget type.

    Args:
        widget_type: The ``WidgetNode.type`` string this builder handles.
        container:   True if the produced widget is a container that
                     supports ``.add(child)``. The layout loader uses this
                     to decide whether to recurse the node's children into
                     it.

    Raises:
        ValueError: If ``widget_type`` already has a registered builder.
                    Re-registration is rejected rather than silently
                    overwritten — a duplicate is almost always a bug.

    Example::

        @register("Panel", container=True)
        def _build_panel(spec):
            return Panel(spec.rect, clip=bool(spec.prop("clip", False)))
    """
    def decorator(builder: WidgetBuilder) -> WidgetBuilder:
        if widget_type in _REGISTRY:
            raise ValueError(
                f"Widget type {widget_type!r} is already registered. "
                f"Each type may be registered only once."
            )
        _REGISTRY[widget_type] = builder
        if container:
            _CONTAINER_TYPES.add(widget_type)
        return builder
    return decorator


def is_registered(widget_type: str) -> bool:
    """Return True if ``widget_type`` has a registered builder."""
    return widget_type in _REGISTRY


def is_container_type(widget_type: str) -> bool:
    """
    Return True if ``widget_type`` produces a container widget.

    Unknown types return False; callers should validate the type
    separately (``build_widget`` raises on unknown types).
    """
    return widget_type in _CONTAINER_TYPES


def registered_types() -> list[str]:
    """Return a sorted list of all registered widget type strings."""
    return sorted(_REGISTRY)


def build_widget(node: "WidgetNode") -> "Widget":
    """
    Construct a single widget from a ``WidgetNode``.

    Builds only this node — its children are the layout loader's concern.
    The constructed widget has its ``widget_id`` set from the node.

    Args:
        node: The descriptor node to build.

    Returns:
        A constructed ``Widget`` (no children attached).

    Raises:
        UnknownWidgetTypeError: If ``node.type`` has no registered builder.
    """
    builder = _REGISTRY.get(node.type)
    if builder is None:
        raise UnknownWidgetTypeError(node.type, registered_types())

    spec   = WidgetBuildSpec(node)
    widget = builder(spec)

    # Stamp the id so editor tooling and behaviour-binding can find it later.
    widget.widget_id = spec.widget_id
    return widget


# ── Built-in type builders ────────────────────────────────────────────────────
#
# Imports are local to this section so a game that never builds a descriptor
# scene does not pay the import cost, and so this module stays importable
# even mid-refactor of an individual widget.

def _register_builtin_widgets() -> None:
    """Register the engine's built-in widget types. Called once at import."""
    from pygame_engine.ui.containers.panel import Panel
    from pygame_engine.ui.containers.stack import Stack
    from pygame_engine.ui.controls.button import Button
    from pygame_engine.ui.controls.checkbox import Checkbox
    from pygame_engine.ui.controls.input_field import InputField
    from pygame_engine.ui.controls.progress_bar import ProgressBar
    from pygame_engine.ui.controls.slider import Slider
    from pygame_engine.ui.text.label import Label

    _UNSET = object()  # local "argument not supplied" sentinel

    # ── Containers ────────────────────────────────────────────────────────────

    @register("Panel", container=True)
    def _build_panel(spec: WidgetBuildSpec) -> "Widget":
        return Panel(
            spec.rect,
            clip=bool(spec.prop("clip", False)),
        )

    @register("Stack", container=True)
    def _build_stack(spec: WidgetBuildSpec) -> "Widget":
        return Stack(
            spec.rect,
            clip=bool(spec.prop("clip", False)),
        )

    # ── Controls ──────────────────────────────────────────────────────────────

    @register("Button")
    def _build_button(spec: WidgetBuildSpec) -> "Widget":
        # on_click is behaviour, not layout — the scene binds it afterward
        # via widget_id. The builder never touches it.
        return Button(spec.rect, label=str(spec.prop("label", "")))

    @register("Checkbox")
    def _build_checkbox(spec: WidgetBuildSpec) -> "Widget":
        return Checkbox(
            spec.rect,
            label=str(spec.prop("label", "")),
            checked=bool(spec.prop("checked", False)),
        )

    @register("InputField")
    def _build_input_field(spec: WidgetBuildSpec) -> "Widget":
        max_length = spec.prop("max_length", None)
        return InputField(
            spec.rect,
            text=str(spec.prop("text", "")),
            placeholder=str(spec.prop("placeholder", "")),
            max_length=int(max_length) if max_length is not None else None,
        )

    @register("ProgressBar")
    def _build_progress_bar(spec: WidgetBuildSpec) -> "Widget":
        return ProgressBar(
            spec.rect,
            value=float(spec.prop("value", 1.0)),
        )

    @register("Slider")
    def _build_slider(spec: WidgetBuildSpec) -> "Widget":
        return Slider(
            spec.rect,
            value=float(spec.prop("value", 0.5)),
            min_value=float(spec.prop("min_value", 0.0)),
            max_value=float(spec.prop("max_value", 1.0)),
        )

    # ── Text ──────────────────────────────────────────────────────────────────

    @register("Label")
    def _build_label(spec: WidgetBuildSpec) -> "Widget":
        # font_size / colour / font_name are optional — only pass them when
        # the node actually supplies them, so Label falls back to the theme
        # for anything omitted (its constructor uses an _UNSET sentinel).
        kwargs: dict[str, Any] = {
            "text":  str(spec.prop("text", "")),
            "align": str(spec.prop("align", "center")),
            "bold":  bool(spec.prop("bold", False)),
        }
        if spec.has_prop("font_size"):
            kwargs["font_size"] = spec.prop("font_size")
        if spec.has_prop("colour"):
            colour = spec.prop("colour")
            # Descriptor stores colours as lists; Label wants a tuple.
            kwargs["colour"] = tuple(colour) if isinstance(colour, list) else colour
        if spec.has_prop("font_name"):
            kwargs["font_name"] = spec.prop("font_name")
        return Label(spec.rect, **kwargs)


_register_builtin_widgets()
