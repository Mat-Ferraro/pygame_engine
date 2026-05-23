"""
Inspector panel — property display for the selected WidgetNode.

Read-only in F3. Editable geometry fields come in F5.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from editor.editor_state import EditorState
    from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode

from imgui_bundle import imgui


def render_inspector(
    state:      "EditorState",
    descriptor: "SceneDescriptor | None",
) -> None:
    imgui.begin("Inspector")

    if descriptor is None:
        imgui.text_disabled("No scene open.")
        imgui.end()
        return

    if state.selected_node_id is None:
        imgui.text_disabled("Nothing selected.")
        imgui.text_disabled("Click a node in the hierarchy.")
        imgui.end()
        return

    if not descriptor.has(state.selected_node_id):
        imgui.text_colored((0.8, 0.3, 0.3, 1.0), "Selected node not found.")
        imgui.end()
        return

    node = descriptor.get(state.selected_node_id)

    # Wrap everything in a scrollable child so content never overflows
    avail = imgui.get_content_region_avail()
    imgui.begin_child("##inspector_scroll", imgui.ImVec2(0, avail.y), False)

    # ── Identity ──────────────────────────────────────────────────────────────
    if imgui.collapsing_header("Identity"):
        _row("widget_id", node.widget_id)
        _row("type",      node.type)
        parent_id = node.parent.widget_id if node.parent else "(root)"
        _row("parent",    parent_id)
        _row("children",  str(len(node.children)))

    # ── Geometry ──────────────────────────────────────────────────────────────
    if imgui.collapsing_header("Geometry"):
        r = node.rect
        _row("x", str(r.x))
        _row("y", str(r.y))
        _row("w", str(r.w))
        _row("h", str(r.h))
        imgui.text_disabled("  (editing enabled in F6)")

    # ── Properties ────────────────────────────────────────────────────────────
    if node.props:
        if imgui.collapsing_header("Properties"):
            for key, obs in node.props.items():
                _row(key, _fmt(obs.value))

    # ── Editor metadata ───────────────────────────────────────────────────────
    if imgui.collapsing_header("Editor"):
        _row("editor_visible", str(node.editor_visible))
        _row("editor_locked",  str(node.editor_locked))
        _row("editor_only",    str(node.editor_only))
        if node.editor_tags:
            _row("tags", ", ".join(node.editor_tags))

    imgui.end_child()
    imgui.end()


def _row(label: str, value: str) -> None:
    """
    Render a label + read-only value as two columns.

    No tooltips, no floating windows — just inline text pairs.
    """
    col_w = 90
    imgui.text_colored((0.55, 0.55, 0.65, 1.0), label)
    imgui.same_line(col_w)
    # Clip long values
    display = value if len(value) < 28 else value[:25] + "..."
    imgui.text(display)


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, (list, tuple)):
        return str(list(value))
    return str(value)
