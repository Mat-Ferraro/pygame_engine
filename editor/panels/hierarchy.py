"""
Hierarchy panel — tree view of the active SceneDescriptor.

Shows all WidgetNodes in a collapsible tree. Clicking a node selects it.
A search box at the top filters nodes by widget_id or type.

When the selection changes (typically because the user clicked a widget
in the viewport), the tree auto-expands all ancestors of the newly
selected node so the highlighted row is always visible. The auto-expand
fires *once* per selection change — after that, the user can collapse
branches freely without the panel fighting them on subsequent frames.

In EDIT mode: nodes are selectable and show editor metadata icons.
In PLAY mode: tree is read-only, shows live node count only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from editor.editor_state import EditorState
    from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode

from imgui_bundle import imgui


# Tracks the selection we showed last frame, so we can detect changes and
# trigger the one-shot auto-expand to the new selection. Stored at module
# scope rather than on EditorState because it is a panel-presentation
# concern, not a true editor state — nothing outside this file needs it.
_last_seen_selection: "str | None" = None


def render_hierarchy(
    state:      "EditorState",
    descriptor: "SceneDescriptor | None",
) -> None:
    """
    Render the Hierarchy panel.

    Args:
        state:      Current editor state. Selection is written here.
        descriptor: The active SceneDescriptor, or None if no scene is open.
    """
    global _last_seen_selection

    imgui.begin("Hierarchy")

    if descriptor is None:
        imgui.text_colored((0.5, 0.5, 0.5, 1.0), "No scene open.")
        imgui.end()
        return

    # ── Detect a selection change since last frame ────────────────────────────
    # If the selection changed and the new value is non-None, compute the
    # set of ancestor widget_ids whose tree nodes we need to force-open
    # this frame. The set is empty otherwise, so the per-node force-open
    # path is a cheap no-op on normal frames.
    selection = state.selected_node_id
    force_open_ids: set[str] = set()
    if selection != _last_seen_selection and selection is not None:
        force_open_ids = _collect_ancestor_ids(descriptor, selection)
    _last_seen_selection = selection

    # ── Search bar ────────────────────────────────────────────────────────────
    imgui.set_next_item_width(-1)
    changed, new_filter = imgui.input_text(
        "##hier_search", state.hierarchy_filter,
        flags=getattr(imgui.InputTextFlags_, "auto_select_all", 0),
    )
    if changed:
        state.hierarchy_filter = new_filter

    imgui.separator()

    # ── Node count ────────────────────────────────────────────────────────────
    count = descriptor.node_count
    imgui.text_colored(
        (0.5, 0.5, 0.5, 1.0),
        f"{count} node{'s' if count != 1 else ''}",
    )
    imgui.separator()

    # ── Tree ──────────────────────────────────────────────────────────────────
    filt = state.hierarchy_filter.lower().strip()
    for root_node in descriptor.roots:
        _render_node(state, root_node, filt, force_open_ids)

    imgui.end()


def _collect_ancestor_ids(
    descriptor: "SceneDescriptor", widget_id: str,
) -> set[str]:
    """
    Return the set of widget_ids that are ancestors of the selected node,
    INCLUDING the node itself.

    Including the node lets a tree row with children auto-expand on
    selection, so its own children become visible — useful when the user
    selects a container that has interesting structure beneath it.
    """
    ids: set[str] = set()
    try:
        node = descriptor.get(widget_id)
    except Exception:
        return ids
    while node is not None:
        ids.add(node.widget_id)
        node = node.parent
    return ids


def _node_matches(node: "WidgetNode", filt: str) -> bool:
    """Return True if the node or any descendant matches the filter."""
    if not filt:
        return True
    if filt in node.widget_id.lower() or filt in node.type.lower():
        return True
    return any(_node_matches(child, filt) for child in node.children)


def _render_node(
    state: "EditorState",
    node:  "WidgetNode",
    filt:  str,
    force_open_ids: set[str],
) -> None:
    """Recursively render one node and its children."""
    # Skip if filtered out
    if not _node_matches(node, filt):
        return

    is_selected = (state.selected_node_id == node.widget_id)
    has_children = len(node.children) > 0

    # Build display label
    vis_icon  = "" if node.editor_visible else "👁 "
    lock_icon = "🔒 " if node.editor_locked else ""
    label     = f"{vis_icon}{lock_icon}{node.widget_id}  [{node.type}]"

    def _tnf(name):
        return getattr(imgui.TreeNodeFlags_, name, 0)

    flags = _tnf("open_on_arrow") | _tnf("span_avail_width")
    if is_selected:
        flags |= _tnf("selected")
    if not has_children:
        flags |= _tnf("leaf") | _tnf("no_tree_push_on_open")

    # Force-open ancestors of the just-selected node so the highlighted
    # row is visible. Cond_.always overrides whatever open-state ImGui
    # would otherwise restore from .ini — but only on the frame the
    # selection changed; subsequent frames clear ``force_open_ids`` and
    # the user can collapse freely again.
    if node.widget_id in force_open_ids and has_children:
        imgui.set_next_item_open(True, imgui.Cond_.always)

    # Dim editor-only nodes
    if node.editor_only:
        imgui.push_style_color(imgui.Col_.text, (0.6, 0.6, 0.4, 1.0))

    opened = imgui.tree_node_ex(f"{label}##{node.widget_id}", flags)  # type: ignore[assignment]

    if node.editor_only:
        imgui.pop_style_color()

    # Click to select
    if imgui.is_item_clicked() and not imgui.is_item_toggled_open():
        if is_selected:
            state.deselect()
        else:
            state.select(node.widget_id)

    # Hover tracking
    if imgui.is_item_hovered():
        state.hovered_node_id = node.widget_id

    # Tooltip: rect info
    if imgui.is_item_hovered() and imgui.get_io().key_alt:
        imgui.begin_tooltip()
        r = node.rect
        imgui.text(f"x={r.x}  y={r.y}  w={r.w}  h={r.h}")
        if node.editor_tags:
            imgui.text(f"tags: {', '.join(node.editor_tags)}")
        imgui.end_tooltip()

    # Children
    if opened and has_children:
        for child in node.children:
            _render_node(state, child, filt, force_open_ids)
        imgui.tree_pop()
