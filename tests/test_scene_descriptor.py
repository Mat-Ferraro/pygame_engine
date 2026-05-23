"""
Tests for SceneDescriptor, WidgetNode, DescribedScene, and LayoutBuilder.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pygame_engine.scene.described_scene import DescribedScene
from pygame_engine.scene.layout_builder import LayoutBuilder
from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode
from pygame_engine.state.observable import Observable
from pygame_engine.state.observable_rect import ObservableRect


# ══════════════════════════════════════════════════════════════════════════════
# WidgetNode
# ══════════════════════════════════════════════════════════════════════════════

def test_widget_node_defaults() -> None:
    node = WidgetNode(widget_id="n1", type="Panel")
    assert node.widget_id == "n1"
    assert node.type == "Panel"
    assert node.parent is None
    assert len(node.children) == 0
    assert node.editor_visible is True
    assert node.editor_locked is False
    assert node.editor_only is False

def test_widget_node_rect_default_zero() -> None:
    node = WidgetNode(widget_id="n1", type="Panel")
    assert (node.rect.x, node.rect.y, node.rect.w, node.rect.h) == (0, 0, 0, 0)

def test_widget_node_custom_rect() -> None:
    node = WidgetNode(widget_id="n1", type="Panel",
                      rect=ObservableRect(10, 20, 300, 200))
    assert node.rect.x == 10

def test_widget_node_repr() -> None:
    node = WidgetNode(widget_id="btn", type="Button")
    assert "btn" in repr(node)
    assert "Button" in repr(node)


# ══════════════════════════════════════════════════════════════════════════════
# SceneDescriptor — node management
# ══════════════════════════════════════════════════════════════════════════════

def make_desc() -> SceneDescriptor:
    return SceneDescriptor()

def make_node(wid: str, typ: str = "Panel",
              x: int = 0, y: int = 0, w: int = 100, h: int = 100) -> WidgetNode:
    return WidgetNode(widget_id=wid, type=typ,
                      rect=ObservableRect(x, y, w, h))


def test_descriptor_starts_empty() -> None:
    d = make_desc()
    assert d.node_count == 0
    assert d.roots == []

def test_add_root_node() -> None:
    d = make_desc()
    d.add(make_node("root"))
    assert d.node_count == 1
    assert d.has("root")

def test_add_child_node() -> None:
    d = make_desc()
    d.add(make_node("parent"))
    d.add(make_node("child"), parent_id="parent")
    assert d.node_count == 2
    assert d.get("child").parent is d.get("parent")

def test_child_appears_in_parent_children() -> None:
    d = make_desc()
    d.add(make_node("p"))
    d.add(make_node("c"), parent_id="p")
    assert d.get("c") in list(d.get("p").children)

def test_duplicate_id_raises() -> None:
    d = make_desc()
    d.add(make_node("n1"))
    with pytest.raises(ValueError, match="n1"):
        d.add(make_node("n1"))

def test_unknown_parent_raises() -> None:
    d = make_desc()
    with pytest.raises(KeyError):
        d.add(make_node("child"), parent_id="nonexistent")

def test_get_returns_node() -> None:
    d = make_desc()
    node = make_node("x")
    d.add(node)
    assert d.get("x") is node

def test_get_unknown_raises() -> None:
    d = make_desc()
    with pytest.raises(KeyError):
        d.get("missing")

def test_has_false_for_unknown() -> None:
    d = make_desc()
    assert d.has("nope") is False

def test_roots_only_top_level() -> None:
    d = make_desc()
    d.add(make_node("r"))
    d.add(make_node("c"), parent_id="r")
    assert len(d.roots) == 1
    assert d.roots[0].widget_id == "r"

def test_all_nodes_includes_all() -> None:
    d = make_desc()
    d.add(make_node("a"))
    d.add(make_node("b"))
    ids = {n.widget_id for n in d.all_nodes}
    assert ids == {"a", "b"}

def test_remove_node() -> None:
    d = make_desc()
    d.add(make_node("n"))
    d.remove("n")
    assert not d.has("n")

def test_remove_also_removes_children() -> None:
    d = make_desc()
    d.add(make_node("p"))
    d.add(make_node("c"), parent_id="p")
    d.remove("p")
    assert not d.has("p")
    assert not d.has("c")

def test_remove_unknown_raises() -> None:
    d = make_desc()
    with pytest.raises(KeyError):
        d.remove("nonexistent")

def test_clear_removes_all() -> None:
    d = make_desc()
    d.add(make_node("a"))
    d.add(make_node("b"))
    d.clear()
    assert d.node_count == 0
    assert d.roots == []


# ══════════════════════════════════════════════════════════════════════════════
# SceneDescriptor — change signals
# ══════════════════════════════════════════════════════════════════════════════

def test_on_structure_change_fires_on_add() -> None:
    d = make_desc()
    vals = []
    d.on_structure_change.subscribe(lambda old, new: vals.append(new))
    d.add(make_node("n"))
    assert len(vals) == 1

def test_on_structure_change_fires_on_remove() -> None:
    d = make_desc()
    d.add(make_node("n"))
    vals = []
    d.on_structure_change.subscribe(lambda old, new: vals.append(new))
    d.remove("n")
    assert len(vals) == 1

def test_on_any_change_fires_on_rect_change() -> None:
    d = make_desc()
    d.add(make_node("n"))
    vals = []
    d.on_any_change.subscribe(lambda old, new: vals.append(new))
    d.get("n").rect.x = 99
    assert len(vals) == 1

def test_on_any_change_counter_increases() -> None:
    d = make_desc()
    d.add(make_node("n"))
    before = d.on_any_change.value
    d.get("n").rect.x = 50
    assert d.on_any_change.value > before


# ══════════════════════════════════════════════════════════════════════════════
# SceneDescriptor — save / load
# ══════════════════════════════════════════════════════════════════════════════

def test_save_creates_file(tmp_path: Path) -> None:
    d = make_desc()
    d.add(make_node("root", x=10, y=20, w=640, h=480))
    p = tmp_path / "scene.layout.json"
    d.save(p)
    assert p.exists()

def test_save_is_valid_json(tmp_path: Path) -> None:
    d = make_desc()
    d.add(make_node("root"))
    p = tmp_path / "s.json"
    d.save(p)
    raw = json.loads(p.read_text())
    assert raw["version"] == 1
    assert isinstance(raw["nodes"], list)

def test_save_includes_rect(tmp_path: Path) -> None:
    d = make_desc()
    d.add(make_node("r", x=5, y=10, w=200, h=100))
    p = tmp_path / "s.json"
    d.save(p)
    raw = json.loads(p.read_text())
    assert raw["nodes"][0]["rect"] == [5, 10, 200, 100]

def test_load_restores_node(tmp_path: Path) -> None:
    d = make_desc()
    d.add(make_node("btn", typ="Button", x=0, y=0, w=80, h=32))
    p = tmp_path / "s.json"
    d.save(p)

    d2 = make_desc()
    d2.load(p)
    assert d2.has("btn")
    assert d2.get("btn").type == "Button"

def test_load_restores_rect(tmp_path: Path) -> None:
    d = make_desc()
    d.add(make_node("r", x=10, y=20, w=300, h=200))
    p = tmp_path / "s.json"
    d.save(p)

    d2 = make_desc()
    d2.load(p)
    node = d2.get("r")
    assert (node.rect.x, node.rect.y, node.rect.w, node.rect.h) == (10, 20, 300, 200)

def test_load_restores_hierarchy(tmp_path: Path) -> None:
    d = make_desc()
    d.add(make_node("parent"))
    d.add(make_node("child"), parent_id="parent")
    p = tmp_path / "s.json"
    d.save(p)

    d2 = make_desc()
    d2.load(p)
    assert d2.has("parent")
    assert d2.has("child")
    assert d2.get("child").parent is d2.get("parent")

def test_load_or_default_loads_when_file_exists(tmp_path: Path) -> None:
    d = make_desc()
    d.add(make_node("existing"))
    p = tmp_path / "s.json"
    d.save(p)

    d2 = make_desc()
    called = []
    d2.load_or_default(p, lambda: called.append(1))
    assert d2.has("existing")
    assert called == []

def test_load_or_default_calls_fn_when_missing(tmp_path: Path) -> None:
    d   = make_desc()
    p   = tmp_path / "nonexistent.json"
    called = []
    d.load_or_default(p, lambda: called.append(1))
    assert called == [1]

def test_load_unknown_version_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 99, "nodes": []}))
    d = make_desc()
    with pytest.raises(ValueError, match="version"):
        d.load(p)

def test_load_missing_file_raises(tmp_path: Path) -> None:
    d = make_desc()
    with pytest.raises(FileNotFoundError):
        d.load(tmp_path / "missing.json")


# ══════════════════════════════════════════════════════════════════════════════
# LayoutBuilder
# ══════════════════════════════════════════════════════════════════════════════

import pygame_engine.scene.layout_builder  # ensure builder() is patched

def test_builder_adds_panel() -> None:
    d = make_desc()
    with d.builder() as L:
        L.panel("p", x=0, y=0, w=400, h=300)
    assert d.has("p")
    assert d.get("p").type == "Panel"

def test_builder_adds_button_with_label() -> None:
    d = make_desc()
    with d.builder() as L:
        L.button("btn", x=0, y=0, w=80, h=32, label="Click me")
    node = d.get("btn")
    assert node.type == "Button"
    assert node.props["label"].value == "Click me"

def test_builder_adds_label_with_text() -> None:
    d = make_desc()
    with d.builder() as L:
        L.label("lbl", x=0, y=0, w=100, h=20, text="Hello")
    assert d.get("lbl").props["text"].value == "Hello"

def test_builder_hierarchy() -> None:
    d = make_desc()
    with d.builder() as L:
        L.panel("panel", x=0, y=0, w=400, h=300)
        L.button("btn", x=10, y=10, w=80, h=32, parent="panel")
    assert d.get("btn").parent is d.get("panel")

def test_builder_dynamic_node() -> None:
    d = make_desc()
    with d.builder() as L:
        L.dynamic("rows", placeholder_count=5, placeholder_height=60)
    node = d.get("rows")
    assert node.type == "Dynamic"
    assert node.props["placeholder_count"].value == 5

def test_builder_custom_node_type() -> None:
    d = make_desc()
    with d.builder() as L:
        L.node("HeroCard", "card1", x=0, y=0, w=200, h=100)
    assert d.get("card1").type == "HeroCard"

def test_builder_rect_stored_correctly() -> None:
    d = make_desc()
    with d.builder() as L:
        L.panel("p", x=10, y=20, w=300, h=200)
    r = d.get("p").rect
    assert (r.x, r.y, r.w, r.h) == (10, 20, 300, 200)


# ══════════════════════════════════════════════════════════════════════════════
# DescribedScene
# ══════════════════════════════════════════════════════════════════════════════

class _SimpleScene(DescribedScene):
    def _build_layout(self) -> None:
        with self.layout.builder() as L:
            L.panel("root", x=0, y=0, w=1280, h=720)
            L.button("btn", x=10, y=10, w=80, h=32, parent="root")

class _ContextScene(DescribedScene):
    @classmethod
    def editor_context(cls) -> dict:
        return {"player": "Test", "level": 1}


def test_described_scene_has_layout() -> None:
    s = _SimpleScene()
    assert isinstance(s.layout, SceneDescriptor)

def test_described_scene_on_enter_builds_layout() -> None:
    s = _SimpleScene()
    s.on_enter()
    assert s.layout.has("root")
    assert s.layout.has("btn")

def test_described_scene_on_exit_clears_layout() -> None:
    s = _SimpleScene()
    s.on_enter()
    s.on_exit()
    assert s.layout.node_count == 0

def test_described_scene_editor_context_default() -> None:
    assert DescribedScene.editor_context() == {}

def test_described_scene_editor_context_override() -> None:
    ctx = _ContextScene.editor_context()
    assert ctx["player"] == "Test"
    assert ctx["level"] == 1

def test_described_scene_layout_path_default_none() -> None:
    assert DescribedScene.layout_path is None

def test_described_scene_subscriptions_disposed_on_exit() -> None:
    s = _SimpleScene()
    s.on_enter()
    calls = []
    s.subscriptions.on(s.layout.on_any_change, lambda old, new: calls.append(1))
    s.on_exit()
    # After exit, layout is cleared — subscriptions group also disposed
    assert s.subscriptions.subscription_count == 0

def test_described_scene_repr() -> None:
    s = _SimpleScene()
    r = repr(s)
    assert "_SimpleScene" in r

def test_described_scene_save_load_roundtrip(tmp_path: Path) -> None:
    s = _SimpleScene()
    s.on_enter()

    p = tmp_path / "scene.layout.json"
    s.layout.save(p)

    d2 = SceneDescriptor()
    d2.load(p)
    assert d2.has("root")
    assert d2.has("btn")
    assert d2.get("btn").parent is d2.get("root")
