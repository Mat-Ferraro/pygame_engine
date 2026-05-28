"""
tests/test_widget_smoke_render.py

Smoke tests that every registered widget type can be constructed and
rendered without raising.

Why this exists
---------------
The rest of the suite tests widget *logic* — event handling, state
transitions, property getters — but almost never calls ``render()``.
That left a whole class of bug invisible: a widget that computes the
right thing but explodes when actually drawn (e.g. calling a child's
``render(surface)`` without the required ``ctx``, or referencing an
undefined name inside ``render``/``update``).

These tests close that gap cheaply. For every type in the widget
registry we build a default instance and:

- call ``render(surface, ctx)`` and assert it doesn't raise
- call ``update(dt)`` and assert it doesn't raise

This is deliberately shallow — we do NOT assert pixels. The goal is
"survives being drawn / updated", which is exactly the seam that unit
logic tests miss. Pixel-level assertions belong in targeted per-widget
tests, not in a smoke pass.

Covers: build_widget for every registered type; render() with a real
RenderContext; update() with a representative dt.
"""

from __future__ import annotations

import pygame
import pytest

from pygame_engine.scene.scene_descriptor import WidgetNode
from pygame_engine.state.observable import Observable
from pygame_engine.state.observable_rect import ObservableRect
from pygame_engine.ui.widget_registry import build_widget, registered_types


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_node(typ: str, **props: object) -> WidgetNode:
    """
    Build a WidgetNode of the given type with Observable-wrapped props,
    mirroring how the layout DSL constructs nodes.
    """
    return WidgetNode(
        widget_id=f"smoke_{typ.lower()}",
        type=typ,
        rect=ObservableRect(10, 20, 120, 48),
        props={k: Observable(v) for k, v in props.items()},
    )


# ── Tests ───────────────────────────────────────────────────────────────────

def test_registry_is_non_empty() -> None:
    """A guard: if the registry is empty the parametrized tests below
    would silently pass by collecting nothing."""
    assert len(registered_types()) > 0


@pytest.mark.parametrize("widget_type", registered_types())
def test_widget_builds_without_error(widget_type: str) -> None:
    """Every registered type constructs from a default node."""
    widget = build_widget(_make_node(widget_type))
    assert widget is not None
    assert widget.widget_id == f"smoke_{widget_type.lower()}"


@pytest.mark.parametrize("widget_type", registered_types())
def test_widget_renders_without_error(
    widget_type: str, display_surface, make_ctx
) -> None:
    """
    Every registered type renders to a surface with a real RenderContext
    without raising.

    This is the test that would have caught Button.render() passing only
    `surface` to its inner Label, and Button.update() referencing an
    undefined `ctx`.
    """
    widget = build_widget(_make_node(widget_type))
    ctx = make_ctx()

    # Should not raise.
    widget.render(display_surface, ctx)


@pytest.mark.parametrize("widget_type", registered_types())
def test_widget_updates_without_error(widget_type: str) -> None:
    """Every registered type survives an update() tick."""
    widget = build_widget(_make_node(widget_type))
    # A representative non-zero dt — exercises any time-based logic.
    widget.update(1.0 / 60.0)


@pytest.mark.parametrize("widget_type", registered_types())
def test_widget_renders_when_disabled(
    widget_type: str, display_surface, make_ctx
) -> None:
    """
    Disabled widgets still render (they grey out, they don't vanish).
    This exercises the disabled-state styling path, which is a common
    place for state-dependent render bugs to hide.
    """
    widget = build_widget(_make_node(widget_type))
    widget.enabled = False
    ctx = make_ctx()

    widget.render(display_surface, ctx)


def test_button_render_and_update_specifically(display_surface, make_ctx) -> None:
    """
    A focused regression test for the two Button bugs found during editor
    bring-up: render() must pass ctx to the inner label, and update() must
    not reference an undefined name. Kept separate from the parametrized
    pass so the failure message names Button directly.
    """
    button = build_widget(_make_node("Button", label="Click Me"))
    ctx = make_ctx()

    button.update(1.0 / 60.0)            # must not raise (was: NameError)
    button.render(display_surface, ctx)  # must not raise (was: missing ctx)

    # Disabled path resolves a different label colour — exercise it too.
    button.enabled = False
    button.render(display_surface, ctx)
