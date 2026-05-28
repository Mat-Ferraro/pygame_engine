"""
Inspector panel — property display and geometry editing for the
selected WidgetNode.

Geometry (x / y / w / h) is editable as of F5. Edits write back to the
node's ObservableRect via a single atomic ``set()`` call, so each change
is one observable event (and, in the future, one undo step). The viewport
selection gizmo and the live widget both update immediately because the
rect is observable.

Everything else — identity, props, editor metadata — remains read-only
display for now. Type-aware editing of arbitrary props is a separate,
larger piece of work.

Behaviour notes
---------------
- When ``state.grid_snap`` is on, typed values snap to the nearest
  ``state.grid_size`` multiple. This is the first real consumer of the
  grid-snap setting.
- Width and height are clamped to a minimum of 1. Zero / negative sizes
  are technically valid for ObservableRect but produce invisible or
  inverted widgets and a degenerate gizmo, so we don't allow them here.
  x / y are left unclamped — negative positions are legitimate.
- If a node is ``editor_locked``, the geometry fields render disabled.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from editor.editor_state import EditorState
    from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode

from imgui_bundle import imgui


# Width of the label column, in pixels, for both read-only rows and
# the geometry input fields. Keeps the two visually aligned.
_LABEL_COL_W = 90


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

    # ── Geometry (editable) ─────────────────────────────────────────────────────
    # collapsing_header with default_open so the fields are visible without
    # an extra click — geometry is the most-used part of the inspector.
    geom_flags = getattr(imgui.TreeNodeFlags_, "default_open", 0)
    if imgui.collapsing_header("Geometry", geom_flags):
        _render_geometry_editor(state, node)

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


# ── Geometry editor ─────────────────────────────────────────────────────────────

def _render_geometry_editor(state: "EditorState", node: "WidgetNode") -> None:
    """
    Render editable x / y / w / h fields for the node's rect.

    Reads the current values, shows an ``input_int`` per coordinate, and
    on any change writes all four back atomically via ``rect.set()`` so
    the update is a single observable event. Width and height are clamped
    to >= 1; values snap to the grid when ``state.grid_snap`` is enabled.
    """
    rect = node.rect

    locked = bool(getattr(node, "editor_locked", False))
    if locked:
        imgui.text_disabled("  (node is editor-locked — read-only)")
        imgui.begin_disabled()

    # Current values up front. We edit a local copy and only commit if
    # something actually changed, to avoid spurious notifications.
    cur_x, cur_y, cur_w, cur_h = rect.x, rect.y, rect.w, rect.h
    new_x, new_y, new_w, new_h = cur_x, cur_y, cur_w, cur_h

    changed = False

    ch, val = _int_field("x", cur_x)
    if ch:
        new_x = val
        changed = True

    ch, val = _int_field("y", cur_y)
    if ch:
        new_y = val
        changed = True

    ch, val = _int_field("w", cur_w)
    if ch:
        new_w = val
        changed = True

    ch, val = _int_field("h", cur_h)
    if ch:
        new_h = val
        changed = True

    if changed and not locked:
        # Snap to grid if enabled.
        if state.grid_snap and state.grid_size > 0:
            g = state.grid_size
            new_x = _snap(new_x, g)
            new_y = _snap(new_y, g)
            new_w = _snap(new_w, g)
            new_h = _snap(new_h, g)

        # Clamp size to a sane minimum. Position is left unconstrained.
        new_w = max(1, new_w)
        new_h = max(1, new_h)

        # Single atomic update — one observable event for the whole edit.
        rect.set(new_x, new_y, new_w, new_h)

    if locked:
        imgui.end_disabled()


def _int_field(label: str, value: int) -> tuple[bool, int]:
    """
    Render one labelled ``input_int`` row matching the read-only row style.

    The visible label is drawn in our own column; ImGui's own label is
    hidden via the ``##`` prefix but still provides a unique widget id.

    Args:
        label: Coordinate name ("x", "y", "w", "h").
        value: Current integer value.

    Returns:
        ``(changed, new_value)`` from ``imgui.input_int``.
    """
    imgui.text_colored((0.55, 0.55, 0.65, 1.0), label)
    imgui.same_line(_LABEL_COL_W)
    # Constrain the field width so it doesn't stretch the whole panel.
    imgui.set_next_item_width(120)
    changed, new_value = imgui.input_int(f"##geom_{label}", value)
    return changed, int(new_value)


def _snap(value: int, grid: int) -> int:
    """Round ``value`` to the nearest multiple of ``grid``."""
    return int(round(value / grid)) * grid


# ── Read-only display helpers ───────────────────────────────────────────────────

def _row(label: str, value: str) -> None:
    """
    Render a label + read-only value as two columns.

    No tooltips, no floating windows — just inline text pairs.
    """
    imgui.text_colored((0.55, 0.55, 0.65, 1.0), label)
    imgui.same_line(_LABEL_COL_W)
    # Clip long values
    display = value if len(value) < 28 else value[:25] + "..."
    imgui.text(display)


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, (list, tuple)):
        return str(list(value))
    return str(value)
