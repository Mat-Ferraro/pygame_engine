"""
GlobalFocusManager — application-level focus coordinator.

This is separate from the container-local ``FocusManager`` mixin in
``pygame_engine.ui.focus``, which handles Tab traversal within a single
Panel or Stack. The ``GlobalFocusManager`` tracks which widget has focus
*across the entire scene*, provides programmatic focus control, draws the
focus ring as a post-render pass, and emits ``ui.focus.changed`` on the
event bus when focus moves.

Typical usage (wired into Application automatically)::

    # Programmatic focus
    app.focus.set_focus(my_button)

    # Clear focus
    app.focus.clear_focus()

    # Tab to next focusable widget in the current candidate list
    app.focus.next_focus()

    # Draw the focus ring after the scene has rendered
    app.focus.render_focus_ring(display_surface)

    # React to focus changes
    from pygame_engine.events.event_bus import bus
    bus.on("ui.focus.changed", lambda widget=None: print(f"focused: {widget}"))

Focus ring
----------
A 2-pixel coloured rectangle drawn just outside the focused widget's rect.
Colour defaults to ``(100, 180, 255)`` (accessible blue). Both the colour
and width are public attributes and can be overridden at any time.

focus_trap
----------
If a widget has ``focus_trap = True``, ``next_focus`` and ``prev_focus``
will never move focus to a widget outside that trapping widget's subtree.
This is checked via a simple ancestor walk: if any ancestor of the current
focused widget has ``focus_trap = True``, Tab navigation is constrained to
siblings of the trapping ancestor.  ConfirmDialog uses this to prevent
focus escaping while the dialog is active.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from pygame_engine.ui.base.widget import Widget


class GlobalFocusManager:
    """
    Application-level focus coordinator.

    Tracks the globally focused widget, provides programmatic focus
    control, draws the focus ring, and emits ``ui.focus.changed`` on
    the event bus when focus changes.

    Attributes
    ----------
    focused : Widget | None
        The currently focused widget, or ``None`` if nothing is focused.
    focus_ring_colour : tuple[int, int, int]
        RGB colour of the focus ring rectangle. Default ``(100, 180, 255)``.
    focus_ring_width : int
        Line width of the focus ring in pixels. Default ``2``.
    """

    def __init__(self) -> None:
        self._focused: Widget | None = None
        self.focus_ring_colour: tuple[int, int, int] = (100, 180, 255)
        self.focus_ring_width:  int = 2

        # Ordered list of candidate widgets for next/prev traversal.
        # Populated externally by the scene or application each frame.
        self._candidates: list[Widget] = []

    # ── Focus candidates ──────────────────────────────────────────────────────

    def set_candidates(self, widgets: list[Widget]) -> None:
        """
        Set the ordered list of widgets eligible for Tab traversal.

        Call this from the scene's ``on_enter`` or whenever the widget tree
        changes. Widgets are visited in order by ``next_focus``/``prev_focus``.
        Widgets with a ``tab_index`` set are sorted to the front, lowest first;
        widgets with ``tab_index=None`` follow in the supplied order.

        Only widgets that are ``visible``, ``enabled``, and ``focusable``
        are retained.

        Args:
            widgets: All candidate widgets, unsorted or pre-sorted.
        """
        eligible = [
            w for w in widgets
            if getattr(w, "visible",   True)
            and getattr(w, "enabled",  True)
            and getattr(w, "focusable", False)
        ]
        # Stable sort: indexed widgets first (ascending), then unindexed
        indexed   = [w for w in eligible if w.tab_index is not None]
        unindexed = [w for w in eligible if w.tab_index is     None]
        indexed.sort(key=lambda w: w.tab_index)  # type: ignore[arg-type]
        self._candidates = indexed + unindexed

    # ── Focus control ─────────────────────────────────────────────────────────

    @property
    def focused(self) -> Widget | None:
        """The currently focused widget, or ``None``."""
        return self._focused

    def set_focus(self, widget: Widget) -> None:
        """
        Move focus to ``widget`` and emit ``ui.focus.changed``.

        If ``widget`` is already focused this is a no-op (no event emitted).

        Args:
            widget: The widget to receive focus. Must be a ``Widget`` instance.
        """
        if self._focused is widget:
            return
        self._clear_internal()
        widget.focused = True
        self._focused = widget
        self._emit_changed(widget)

    def clear_focus(self) -> None:
        """
        Remove focus from the current widget and emit ``ui.focus.changed``.

        No-op if nothing is currently focused.
        """
        if self._focused is None:
            return
        self._clear_internal()
        self._emit_changed(None)

    def next_focus(self) -> None:
        """
        Move focus to the next candidate widget (Tab forward).

        Respects ``focus_trap``: if the current widget has an ancestor with
        ``focus_trap=True``, focus cycles only within that ancestor's
        candidates.

        If no candidates are registered this is a no-op.
        """
        self._move(+1)

    def prev_focus(self) -> None:
        """
        Move focus to the previous candidate widget (Shift+Tab backward).

        Respects ``focus_trap`` the same way as ``next_focus``.
        """
        self._move(-1)

    # ── Focus ring ────────────────────────────────────────────────────────────

    def render_focus_ring(self, surface: pygame.Surface) -> None:
        """
        Draw a focus ring around the currently focused widget.

        Called as a post-render pass — after the scene and all widgets have
        been drawn — so the ring always appears on top.

        Does nothing when ``focused`` is ``None`` or the focused widget's
        ``rect`` is zero-size.

        Args:
            surface: The surface to draw onto (usually the display surface).
        """
        if self._focused is None:
            return
        rect = self._focused.rect
        if rect.width <= 0 or rect.height <= 0:
            return
        # Inflate by 1 px on each side so the ring sits just outside the widget
        ring_rect = rect.inflate(2, 2)
        pygame.draw.rect(
            surface,
            self.focus_ring_colour,
            ring_rect,
            self.focus_ring_width,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _clear_internal(self) -> None:
        """Clear focused state on the widget object without emitting an event."""
        if self._focused is not None:
            self._focused.focused = False
            self._focused = None

    def _move(self, direction: int) -> None:
        """Move focus by ``direction`` (+1 or -1) through candidates."""
        candidates = self._candidates
        if not candidates:
            return

        if self._focused is None:
            # Nothing focused: start at beginning or end
            idx = 0 if direction > 0 else len(candidates) - 1
        elif self._focused in candidates:
            current_idx = candidates.index(self._focused)
            idx = (current_idx + direction) % len(candidates)
        else:
            idx = 0

        self.set_focus(candidates[idx])

    @staticmethod
    def _emit_changed(widget: Widget | None) -> None:
        """Emit ``ui.focus.changed`` on the application event bus."""
        try:
            from pygame_engine.events.event_bus import bus
            bus.emit("ui.focus.changed", widget=widget)
        except Exception:
            pass  # Never crash the render loop on a bus error

    def __repr__(self) -> str:
        wid = getattr(self._focused, "widget_id", None)
        name = wid or (type(self._focused).__name__ if self._focused else "None")
        return f"GlobalFocusManager(focused={name!r}, candidates={len(self._candidates)})"
