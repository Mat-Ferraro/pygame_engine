"""
Tests for widget_registry — type registration and descriptor-driven
widget construction.

Covers: built-in types are registered; build_widget produces the right
class with widget_id stamped; props are read and unrecognised props
ignored; unknown types raise; the container flag; duplicate registration
is rejected; custom-type registration.
"""

from __future__ import annotations

import pytest

from pygame_engine.scene.scene_descriptor import WidgetNode
from pygame_engine.state.observable import Observable
from pygame_engine.state.observable_rect import ObservableRect
from pygame_engine.ui import widget_registry as wr
from pygame_engine.ui.widget_registry import (
    UnknownWidgetTypeError,
    WidgetBuildSpec,
    build_widget,
    is_container_type,
    is_registered,
    register,
    registered_types,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_node(
    wid: str,
    typ: str,
    x: int = 0, y: int = 0, w: int = 100, h: int = 40,
    **props: object,
) -> WidgetNode:
    """Build a WidgetNode with Observable-wrapped props, as the DSL does."""
    return WidgetNode(
        widget_id=wid,
        type=typ,
        rect=ObservableRect(x, y, w, h),
        props={k: Observable(v) for k, v in props.items()},
    )


# ══════════════════════════════════════════════════════════════════════════════
# Built-in registration
# ══════════════════════════════════════════════════════════════════════════════

def test_builtin_types_are_registered() -> None:
    for typ in ("Panel", "Stack", "Button", "Label", "Checkbox",
                "InputField", "ProgressBar", "Slider"):
        assert is_registered(typ), f"{typ} should be registered at import"


def test_registered_types_is_sorted() -> None:
    types = registered_types()
    assert types == sorted(types)


def test_containers_flagged_controls_not() -> None:
    assert is_container_type("Panel") is True
    assert is_container_type("Stack") is True
    assert is_container_type("Button") is False
    assert is_container_type("Label") is False


def test_is_container_type_unknown_is_false() -> None:
    assert is_container_type("NoSuchType") is False


# ══════════════════════════════════════════════════════════════════════════════
# build_widget — construction
# ══════════════════════════════════════════════════════════════════════════════

def test_build_panel_produces_panel() -> None:
    from pygame_engine.ui import Panel
    node   = make_node("p1", "Panel", 10, 20, 300, 200)
    widget = build_widget(node)
    assert isinstance(widget, Panel)


def test_build_stamps_widget_id() -> None:
    node   = make_node("my_panel", "Panel")
    widget = build_widget(node)
    assert widget.widget_id == "my_panel"


def test_build_applies_rect() -> None:
    node   = make_node("p1", "Panel", 10, 20, 300, 200)
    widget = build_widget(node)
    assert (widget.rect.x, widget.rect.y) == (10, 20)
    assert (widget.rect.w, widget.rect.h) == (300, 200)


def test_build_button_reads_label_prop() -> None:
    node   = make_node("b1", "Button", label="Start Game")
    widget = build_widget(node)
    assert widget.label == "Start Game"


def test_build_button_ignores_unrecognised_prop() -> None:
    # A stray / behaviour-only prop must not break the build.
    node   = make_node("b1", "Button", label="OK", on_click="not-a-callable",
                       mystery_prop=123)
    widget = build_widget(node)          # must not raise
    assert widget.label == "OK"


def test_build_checkbox_reads_checked() -> None:
    node   = make_node("c1", "Checkbox", label="Mute", checked=True)
    widget = build_widget(node)
    assert widget.checked is True


def test_build_label_falls_back_to_theme_when_props_absent() -> None:
    # No font_size / colour given — Label should still construct fine,
    # taking theme defaults.
    node   = make_node("l1", "Label", text="Hello")
    widget = build_widget(node)
    assert widget.text == "Hello"


# ══════════════════════════════════════════════════════════════════════════════
# build_widget — unknown type
# ══════════════════════════════════════════════════════════════════════════════

def test_unknown_type_raises() -> None:
    node = make_node("x", "TotallyMadeUpType")
    with pytest.raises(UnknownWidgetTypeError):
        build_widget(node)


def test_unknown_type_error_names_the_type() -> None:
    node = make_node("x", "TotallyMadeUpType")
    with pytest.raises(UnknownWidgetTypeError) as exc:
        build_widget(node)
    assert "TotallyMadeUpType" in str(exc.value)


def test_unknown_type_error_lists_known_types() -> None:
    node = make_node("x", "TotallyMadeUpType")
    with pytest.raises(UnknownWidgetTypeError) as exc:
        build_widget(node)
    # The message should help — it lists what IS registered.
    assert "Panel" in str(exc.value)


# ══════════════════════════════════════════════════════════════════════════════
# WidgetBuildSpec
# ══════════════════════════════════════════════════════════════════════════════

def test_spec_unwraps_observable_props() -> None:
    node = make_node("n", "Button", label="Hi")
    spec = WidgetBuildSpec(node)
    # prop() returns the plain value, not the Observable wrapper.
    assert spec.prop("label") == "Hi"


def test_spec_prop_default_for_missing() -> None:
    node = make_node("n", "Button")
    spec = WidgetBuildSpec(node)
    assert spec.prop("nonexistent", "fallback") == "fallback"


def test_spec_has_prop() -> None:
    node = make_node("n", "Button", label="Hi")
    spec = WidgetBuildSpec(node)
    assert spec.has_prop("label") is True
    assert spec.has_prop("missing") is False


def test_spec_rect_is_plain_pygame_rect() -> None:
    import pygame
    node = make_node("n", "Panel", 5, 6, 7, 8)
    spec = WidgetBuildSpec(node)
    assert isinstance(spec.rect, pygame.Rect)
    assert (spec.rect.x, spec.rect.y, spec.rect.w, spec.rect.h) == (5, 6, 7, 8)


# ══════════════════════════════════════════════════════════════════════════════
# register — custom types and duplicate rejection
# ══════════════════════════════════════════════════════════════════════════════

def test_register_rejects_duplicate() -> None:
    # "Panel" is already registered; re-registering must raise.
    with pytest.raises(ValueError):
        @register("Panel")
        def _dupe(spec: WidgetBuildSpec):  # pragma: no cover - never runs
            return None


def test_register_custom_type_then_build() -> None:
    from pygame_engine.ui.base.widget import Widget

    type_name = "TestCustomWidget_unique"
    # Guard against a re-run leaving it registered.
    if not is_registered(type_name):
        @register(type_name)
        def _build(spec: WidgetBuildSpec) -> Widget:
            return Widget(spec.rect)

    assert is_registered(type_name)
    node   = make_node("cw", type_name, 1, 2, 3, 4)
    widget = build_widget(node)
    assert isinstance(widget, Widget)
    assert widget.widget_id == "cw"
