"""
Toolbar — two-row layout.

Row 1 (main menu bar): File, View menus only.
Row 2 (toolbar window): Play/Stop, grid controls, status message.

Separating menus from controls prevents the cramping that occurs when
mixing menu items and inline widgets in a single menu bar.

The toolbar never touches the scene descriptor directly. When the user
picks "Save Layout" it raises a one-shot ``pending_action`` on the state;
the EditorApplication owns the descriptor and performs the actual save.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from editor.editor_state import EditorState

from imgui_bundle import imgui


# Height of the second toolbar row in pixels
TOOLBAR_ROW2_H = 32


def render_toolbar(state: "EditorState") -> None:
    """
    Render both toolbar rows.

    Row 1: main menu bar (File, View).
    Row 2: play controls, grid controls, status bar.

    Args:
        state: Current editor state. Modified in place.
    """
    _render_menu_bar(state)
    _render_controls_bar(state)


def _render_menu_bar(state: "EditorState") -> None:
    """Row 1 — File / View menus only. Kept minimal so nothing overlaps."""
    if not imgui.begin_main_menu_bar():
        return

    if imgui.begin_menu("File"):
        if imgui.menu_item("Open Scene...", "", False)[0]:
            state.set_status("Open Scene: not yet implemented")

        # "Save Layout" is greyed out until there is somewhere to save to.
        can_save = state.layout_path is not None
        if imgui.menu_item("Save Layout", "Ctrl+S", False, can_save)[0]:
            state.request(state.ACTION_SAVE_LAYOUT)

        imgui.separator()
        if imgui.menu_item("Quit", "Alt+F4", False)[0]:
            import pygame
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        imgui.end_menu()

    if imgui.begin_menu("View"):
        _activated, state.show_grid   = imgui.menu_item("Show Grid",   "", state.show_grid)
        _activated, state.show_gizmos = imgui.menu_item("Show Gizmos", "", state.show_gizmos)
        imgui.separator()
        if imgui.menu_item("Reset Layout", "", False)[0]:
            state.reset_layout = True
            state.set_status("Layout reset to default")
        imgui.end_menu()

    imgui.end_main_menu_bar()


def _render_controls_bar(state: "EditorState") -> None:
    """Row 2 — play controls, grid controls, status message."""
    from editor.editor_state import EditorMode

    # Pin immediately below the menu bar, full width, fixed height
    menu_h = imgui.get_frame_height()
    vp     = imgui.get_main_viewport()
    vp_w   = vp.size.x

    imgui.set_next_window_pos(imgui.ImVec2(0, menu_h), imgui.Cond_.always)
    imgui.set_next_window_size(imgui.ImVec2(vp_w, TOOLBAR_ROW2_H), imgui.Cond_.always)
    imgui.set_next_window_bg_alpha(1.0)

    flags = (
        getattr(imgui.WindowFlags_, "no_title_bar",       0)
        | getattr(imgui.WindowFlags_, "no_resize",         0)
        | getattr(imgui.WindowFlags_, "no_move",           0)
        | getattr(imgui.WindowFlags_, "no_scrollbar",      0)
        | getattr(imgui.WindowFlags_, "no_saved_settings", 0)
        | getattr(imgui.WindowFlags_, "no_nav",            0)
        | getattr(imgui.WindowFlags_, "no_decoration",     0)
    )

    imgui.push_style_var(imgui.StyleVar_.window_padding, imgui.ImVec2(6, 4))
    imgui.begin("##toolbar_controls", None, flags)
    imgui.pop_style_var()

    # ── Play controls ─────────────────────────────────────────────────────────
    if state.mode == EditorMode.EDIT:
        if imgui.button("Play"):
            state.enter_play()

    elif state.mode == EditorMode.PLAY:
        _coloured_button("Play", (0.2, 0.6, 0.2, 1.0))
        imgui.same_line()
        if imgui.button("Pause"):
            state.enter_pause()
        imgui.same_line()
        if imgui.button("Stop"):
            state.enter_edit()

    elif state.mode == EditorMode.PAUSED:
        if imgui.button("Resume"):
            state.enter_play()
        imgui.same_line()
        _coloured_button("Paused", (0.6, 0.5, 0.1, 1.0))
        imgui.same_line()
        if imgui.button("Stop"):
            state.enter_edit()

    # ── Divider ───────────────────────────────────────────────────────────────
    imgui.same_line()
    imgui.text("  |  ")
    imgui.same_line()

    # ── Save Layout button ────────────────────────────────────────────────────
    # Only enabled when there is a layout file to write to. In EDIT mode only;
    # editing is disabled during PLAY/PAUSED so saving then would be confusing.
    can_save = state.layout_path is not None and state.is_editing
    if not can_save:
        imgui.begin_disabled()
    if imgui.button("Save Layout"):
        state.request(state.ACTION_SAVE_LAYOUT)
    if not can_save:
        imgui.end_disabled()
    imgui.same_line()
    imgui.text("  |  ")
    imgui.same_line()

    # ── Grid controls ─────────────────────────────────────────────────────────
    _, state.show_grid = imgui.checkbox("Grid", state.show_grid)
    imgui.same_line()
    _, state.grid_snap = imgui.checkbox("Snap", state.grid_snap)
    imgui.same_line()
    imgui.text("Size:")
    imgui.same_line()
    imgui.set_next_item_width(48)
    changed, new_size = imgui.input_int("##gs", state.grid_size, 0, 0)
    if changed and new_size >= 4:
        state.grid_size = new_size

    # ── Status message (right-aligned) ────────────────────────────────────────
    status  = state.status_message
    text_w  = imgui.calc_text_size(status).x
    avail   = imgui.get_content_region_avail().x
    if avail > text_w + 8:
        imgui.same_line(imgui.get_cursor_pos_x() + avail - text_w - 8)
    imgui.text_colored((0.55, 0.55, 0.55, 1.0), status)

    imgui.end()


def _coloured_button(label: str, colour: tuple) -> bool:
    """Render a button with a custom background colour."""
    imgui.push_style_color(getattr(imgui.Col_, "button", 2), colour)
    clicked = imgui.button(label)
    imgui.pop_style_color()
    return clicked
