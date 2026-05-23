"""
Tests for the LayoutBuilder.stack() method added during the
descriptor-authority sprint.

The pre-existing LayoutBuilder behaviour is covered by
test_scene_descriptor.py; this file covers only the new stack() method,
which fills the gap of having panel() but no stack() container helper.
"""

from __future__ import annotations

from pygame_engine.scene import layout_builder  # noqa: F401  (patches builder())
from pygame_engine.scene.scene_descriptor import SceneDescriptor


def test_stack_creates_a_stack_node() -> None:
    d = SceneDescriptor()
    with d.builder() as L:
        L.stack("root", x=0, y=0, w=800, h=600)
    node = d.get("root")
    assert node.type == "Stack"


def test_stack_applies_geometry() -> None:
    d = SceneDescriptor()
    with d.builder() as L:
        L.stack("root", x=5, y=10, w=320, h=240)
    r = d.get("root").rect
    assert (r.x, r.y, r.w, r.h) == (5, 10, 320, 240)


def test_stack_accepts_children() -> None:
    d = SceneDescriptor()
    with d.builder() as L:
        L.stack("root", x=0, y=0, w=800, h=600)
        L.panel("panel", x=10, y=10, w=200, h=200, parent="root")
        L.button("btn", x=0, y=0, w=80, h=30, parent="root", label="Go")
    root = d.get("root")
    assert len(root.children) == 2


def test_stack_as_nested_child() -> None:
    d = SceneDescriptor()
    with d.builder() as L:
        L.panel("outer", x=0, y=0, w=800, h=600)
        L.stack("inner_stack", x=10, y=10, w=400, h=400, parent="outer")
    inner = d.get("inner_stack")
    assert inner.type == "Stack"
    assert inner.parent is d.get("outer")
