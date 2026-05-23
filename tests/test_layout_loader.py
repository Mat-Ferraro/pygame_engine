"""
Tests for layout_loader — building a live widget tree from a
SceneDescriptor, with live rect binding.

Covers: a descriptor builds into a widget tree; nested containers parent
correctly; widgets are looked up by id; the live rect binding pushes
descriptor changes into the widget; multiple roots wrap in a Stack;
dispose() releases subscriptions; and the fail-loud cases (empty
descriptor, duplicate id, children on a non-container).
"""

from __future__ import annotations

import pytest

from pygame_engine.scene.layout_loader import (
    LayoutLoader,
    LayoutLoadError,
    LoadedLayout,
)
from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode
from pygame_engine.state.observable_rect import ObservableRect


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_node(
    wid: str,
    typ: str = "Panel",
    x: int = 0, y: int = 0, w: int = 100, h: int = 100,
) -> WidgetNode:
    return WidgetNode(widget_id=wid, type=typ,
                      rect=ObservableRect(x, y, w, h))


def single_root_descriptor() -> SceneDescriptor:
    """A descriptor with one Panel root containing one Button child."""
    d = SceneDescriptor()
    d.add(make_node("root", "Panel", 0, 0, 400, 300))
    d.add(make_node("child_btn", "Button", 10, 10, 80, 30),
          parent_id="root")
    return d


# ══════════════════════════════════════════════════════════════════════════════
# Basic load
# ══════════════════════════════════════════════════════════════════════════════

def test_load_returns_loaded_layout() -> None:
    loaded = LayoutLoader().load(single_root_descriptor())
    assert isinstance(loaded, LoadedLayout)


def test_load_single_root_is_that_widget() -> None:
    from pygame_engine.ui import Panel
    loaded = LayoutLoader().load(single_root_descriptor())
    assert isinstance(loaded.root, Panel)


def test_load_builds_child_into_container() -> None:
    loaded = LayoutLoader().load(single_root_descriptor())
    # The root Panel should contain exactly one child (the button).
    assert len(loaded.root.children) == 1


def test_load_populates_id_lookup() -> None:
    loaded = LayoutLoader().load(single_root_descriptor())
    assert loaded.by_id("root") is loaded.root
    assert loaded.find("child_btn") is not None


def test_by_id_unknown_raises() -> None:
    loaded = LayoutLoader().load(single_root_descriptor())
    with pytest.raises(KeyError):
        loaded.by_id("no_such_widget")


def test_find_unknown_returns_none() -> None:
    loaded = LayoutLoader().load(single_root_descriptor())
    assert loaded.find("no_such_widget") is None


# ══════════════════════════════════════════════════════════════════════════════
# Live rect binding — the F3 mechanism
# ══════════════════════════════════════════════════════════════════════════════

def test_descriptor_rect_change_moves_widget() -> None:
    d = single_root_descriptor()
    loaded = LayoutLoader().load(d)
    btn = loaded.by_id("child_btn")

    # Move the descriptor node — the live widget must follow.
    node = d.get("child_btn")
    node.rect.set(50, 60, 120, 40)

    assert (btn.rect.x, btn.rect.y) == (50, 60)
    assert (btn.rect.w, btn.rect.h) == (120, 40)


def test_descriptor_rect_change_moves_root() -> None:
    d = single_root_descriptor()
    loaded = LayoutLoader().load(d)
    root = loaded.root

    d.get("root").rect.move_to(25, 35)
    assert (root.rect.x, root.rect.y) == (25, 35)


def test_dispose_stops_the_binding() -> None:
    d = single_root_descriptor()
    loaded = LayoutLoader().load(d)
    btn = loaded.by_id("child_btn")

    loaded.dispose()

    # After dispose, descriptor changes must NOT reach the widget.
    d.get("child_btn").rect.set(999, 999, 10, 10)
    assert btn.rect.x != 999


# ══════════════════════════════════════════════════════════════════════════════
# Nested containers
# ══════════════════════════════════════════════════════════════════════════════

def test_nested_containers_parent_correctly() -> None:
    d = SceneDescriptor()
    d.add(make_node("outer", "Panel", 0, 0, 500, 500))
    d.add(make_node("inner", "Panel", 10, 10, 200, 200), parent_id="outer")
    d.add(make_node("leaf", "Button", 5, 5, 50, 20), parent_id="inner")

    loaded = LayoutLoader().load(d)
    outer = loaded.by_id("outer")
    inner = loaded.by_id("inner")

    assert len(outer.children) == 1          # outer holds inner
    assert outer.children[0] is inner
    assert len(inner.children) == 1          # inner holds leaf


# ══════════════════════════════════════════════════════════════════════════════
# Multiple roots
# ══════════════════════════════════════════════════════════════════════════════

def test_multiple_roots_wrap_in_stack() -> None:
    from pygame_engine.ui import Stack
    d = SceneDescriptor()
    d.add(make_node("root_a", "Panel", 0, 0, 100, 100))
    d.add(make_node("root_b", "Panel", 200, 0, 100, 100))

    loaded = LayoutLoader().load(d)
    # Two roots → a synthetic Stack wraps them.
    assert isinstance(loaded.root, Stack)
    assert len(loaded.root.children) == 2


# ══════════════════════════════════════════════════════════════════════════════
# Fail-loud cases
# ══════════════════════════════════════════════════════════════════════════════

def test_empty_descriptor_raises() -> None:
    with pytest.raises(LayoutLoadError):
        LayoutLoader().load(SceneDescriptor())


def test_children_on_non_container_raises() -> None:
    # A Button is not a container — giving it a child is an authoring error.
    d = SceneDescriptor()
    d.add(make_node("btn_root", "Button", 0, 0, 100, 40))
    d.add(make_node("orphan", "Label", 0, 0, 50, 20), parent_id="btn_root")

    with pytest.raises(LayoutLoadError):
        LayoutLoader().load(d)


def test_loader_is_reusable() -> None:
    # One loader instance can load multiple descriptors.
    loader = LayoutLoader()
    a = loader.load(single_root_descriptor())
    b = loader.load(single_root_descriptor())
    assert a.root is not b.root
