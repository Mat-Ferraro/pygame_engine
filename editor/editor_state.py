"""
EditorState — the single source of truth for all editor-level state.

Pure data. No pygame, no imgui, no engine imports. The panels and the
EditorApplication both read from and write to this object.

Kept flat and simple — no nested dataclasses. This makes it trivial to
snapshot (play mode) and restore (stop mode), and trivial to persist the
durable fields between sessions.

Mode lifecycle
--------------
EDIT  → press Play  → PLAY
PLAY  → press Stop  → EDIT
PLAY  → press Pause → PAUSED
PAUSED→ press Play  → PLAY
PAUSED→ press Stop  → EDIT

Persistence
-----------
Only a subset of fields is durable across sessions — grid settings, overlay
toggles, the play-mode tint, and the paths of the open scene/layout. The
transient fields (``mode``, selection, status message, pending actions) are
deliberately NOT persisted: restoring them would be confusing on the next
launch. ``to_settings()`` / ``apply_settings()`` handle exactly the durable
set and nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.scene.scene_descriptor import WidgetNode  # noqa: F401


class EditorMode(Enum):
    """The current operating mode of the editor."""
    EDIT   = auto()   # time_scale=0, full editing enabled
    PLAY   = auto()   # time_scale=1, editing disabled
    PAUSED = auto()   # time_scale=0, editing disabled (play session paused)


#: Field names that survive across editor sessions. Anything not in this
#: tuple is treated as transient and is never written to or read from the
#: settings file. ``viewport_tint`` is handled separately because it is a
#: tuple and needs explicit list<->tuple conversion for JSON.
PERSISTENT_FIELDS: tuple[str, ...] = (
    "show_grid",
    "grid_size",
    "grid_snap",
    "show_gizmos",
    "scene_path",
    "layout_path",
)


@dataclass
class EditorState:
    """
    All transient editor state in one place.

    Attributes
    ----------
    mode:
        Current editor mode (EDIT, PLAY, PAUSED).
    selected_node_id:
        The ``widget_id`` of the currently selected node, or ``None``.
    hovered_node_id:
        The ``widget_id`` of the node under the mouse in the hierarchy, or ``None``.
    show_grid:
        Whether the snap grid overlay is visible.
    grid_size:
        Grid cell size in pixels.
    grid_snap:
        Whether dragging snaps to the grid.
    show_gizmos:
        Whether gizmo overlays are visible in the viewport.
    viewport_tint:
        RGBA colour applied to the viewport during PLAY mode.
        Alpha=0 means no tint.
    scene_path:
        Path to the currently open scene file, or ``None``.
    layout_path:
        Path to the active layout JSON file, or ``None``.
    status_message:
        One-line message shown in the status bar.
    hierarchy_filter:
        Search string for filtering the hierarchy panel.
    reset_layout:
        Set True to force panel positions back to defaults this frame.
    pending_action:
        A one-shot request raised by a panel (e.g. the toolbar's
        "Save Layout" menu item) for the EditorApplication to act on.
        The application clears it once handled. ``None`` means nothing
        pending. See ``ACTION_*`` constants below.
    """

    mode:               EditorMode  = EditorMode.EDIT
    selected_node_id:   str | None  = None
    hovered_node_id:    str | None  = None

    # Grid
    show_grid:  bool = True
    grid_size:  int  = 8
    grid_snap:  bool = True

    # Overlays
    show_gizmos: bool = True

    # Play mode tint — RGBA 0-255
    viewport_tint: tuple[int, int, int, int] = (0, 80, 180, 40)

    # Open scene
    scene_path:  str | None = None
    layout_path: str | None = None

    # UI state
    status_message:   str  = "Ready"
    hierarchy_filter: str  = ""
    reset_layout:     bool = False   # set True to force panel positions this frame

    # One-shot action requested by a panel, consumed by EditorApplication
    pending_action: str | None = None

    # ── Action constants ──────────────────────────────────────────────────────
    #: Request to save the current scene layout to ``layout_path``.
    ACTION_SAVE_LAYOUT: str = field(default="save_layout", init=False, repr=False)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def is_editing(self) -> bool:
        """True when the editor is in EDIT mode (full editing enabled)."""
        return self.mode == EditorMode.EDIT

    @property
    def is_playing(self) -> bool:
        """True when a play session is active (PLAY or PAUSED)."""
        return self.mode in (EditorMode.PLAY, EditorMode.PAUSED)

    def select(self, node_id: str | None) -> None:
        """Select a node by widget_id. Pass None to deselect."""
        self.selected_node_id = node_id

    def deselect(self) -> None:
        """Clear the current selection."""
        self.selected_node_id = None

    def set_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_message = message

    def request(self, action: str) -> None:
        """
        Raise a one-shot action for the EditorApplication to handle.

        Args:
            action: One of the ``ACTION_*`` constants.
        """
        self.pending_action = action

    def take_pending_action(self) -> str | None:
        """
        Return and clear the pending action.

        Returns ``None`` if nothing is pending. The application calls this
        once per frame and acts on whatever it gets back.
        """
        action = self.pending_action
        self.pending_action = None
        return action

    def enter_play(self) -> None:
        """Transition to PLAY mode."""
        self.mode = EditorMode.PLAY
        self.set_status("Playing...")

    def enter_pause(self) -> None:
        """Transition to PAUSED mode."""
        self.mode = EditorMode.PAUSED
        self.set_status("Paused")

    def enter_edit(self) -> None:
        """Transition back to EDIT mode."""
        self.mode   = EditorMode.EDIT
        self.deselect()
        self.set_status("Ready")

    # ── Persistence ───────────────────────────────────────────────────────────

    def to_settings(self) -> dict[str, Any]:
        """
        Return a JSON-serialisable dict of the durable editor settings.

        Only the fields listed in ``PERSISTENT_FIELDS`` (plus the tint) are
        included. Transient state — mode, selection, status — is omitted on
        purpose so it does not get restored on the next launch.
        """
        data: dict[str, Any] = {
            name: getattr(self, name) for name in PERSISTENT_FIELDS
        }
        data["viewport_tint"] = list(self.viewport_tint)
        return data

    def apply_settings(self, data: dict[str, Any]) -> None:
        """
        Overwrite the durable fields from a settings dict.

        Unknown keys are ignored (forwards compatibility); missing keys keep
        their current value (so a partial or older file degrades gracefully).
        Each value is lightly type-checked — a bad value is skipped rather
        than allowed to poison the editor.

        Args:
            data: A dict previously produced by ``to_settings()``.
        """
        if not isinstance(data, dict):
            return

        if isinstance(data.get("show_grid"), bool):
            self.show_grid = data["show_grid"]
        if isinstance(data.get("grid_snap"), bool):
            self.grid_snap = data["grid_snap"]
        if isinstance(data.get("show_gizmos"), bool):
            self.show_gizmos = data["show_gizmos"]

        gs = data.get("grid_size")
        if isinstance(gs, int) and gs >= 4:
            self.grid_size = gs

        sp = data.get("scene_path")
        if sp is None or isinstance(sp, str):
            self.scene_path = sp
        lp = data.get("layout_path")
        if lp is None or isinstance(lp, str):
            self.layout_path = lp

        tint = data.get("viewport_tint")
        if (isinstance(tint, (list, tuple)) and len(tint) == 4
                and all(isinstance(c, int) for c in tint)):
            self.viewport_tint = (tint[0], tint[1], tint[2], tint[3])

    def __repr__(self) -> str:
        return (
            f"EditorState(mode={self.mode.name}, "
            f"selected={self.selected_node_id!r})"
        )
