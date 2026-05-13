"""
ui/focus.py

Focus traversal helpers for pygame_engine.

``FocusManager`` is a mixin that adds Tab/Shift+Tab focus cycling to any
container widget. It tracks which child is focused, handles traversal,
and routes keyboard events to the focused child.

Usage — add to a Panel or Stack::

    from pygame_engine.ui.focus import FocusManager
    from pygame_engine.ui.containers.panel import Panel

    panel = Panel(rect, manage_focus=True)
    panel.add(Button(...))    # focusable by default
    panel.add(Label(...))     # not focusable (focusable=False on Widget)
    panel.add(InputField(...))

    # Tab moves through Button → InputField → Button → ...
    # The panel intercepts Tab in handle_event automatically.

Marking a widget as focusable::

    widget.focusable = True    # default for interactive widgets
    widget.focusable = False   # default for display widgets

Engine widgets come pre-configured:
    Button:     focusable = True
    InputField: focusable = True
    ProgressBar: focusable = False
    Label:      focusable = False
    TextBlock:  focusable = False
    Panel:      focusable = False (it manages focus, not receives it)
    Stack:      focusable = False
"""

from __future__ import annotations

import pygame


class FocusManager:
    """
    Mixin that adds Tab/Shift+Tab focus traversal to a container.

    Add this as a mixin to any container that has a ``_children`` list.
    Call ``_focus_handle_event(event)`` from the container's
    ``handle_event`` before routing to children.

    The focused child receives keyboard events. Tab/Shift+Tab cycle
    focus. Pressing Enter/Space on a focused Button fires its click.
    """

    def __init__(self) -> None:
        self._focus_index: int  = -1   # index into focusable children
        self._manage_focus: bool = False

    def _focus_handle_event(
        self,
        event:    pygame.event.Event,
        children: list,
    ) -> bool:
        """
        Handle Tab traversal and route keyboard events to focused child.

        Args:
            event:    The pygame event to process.
            children: The container's child list.

        Returns:
            True if the event was consumed.
        """
        if not self._manage_focus:
            return False

        focusable = self._focusable_children(children)
        if not focusable:
            return False

        # Tab / Shift+Tab
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            if event.key == pygame.K_TAB:
                if mods & pygame.KMOD_SHIFT:
                    self._move_focus(focusable, -1)
                else:
                    self._move_focus(focusable, +1)
                return True

        # Route keyboard events to the focused child
        if event.type in (pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT):
            focused = self._current_focused(focusable)
            if focused is not None:
                return focused.handle_event(event)

        return False

    def focus_first(self, children: list) -> None:
        """Focus the first focusable child."""
        focusable = self._focusable_children(children)
        if focusable:
            self._apply_focus(focusable, 0)

    def focus_none(self, children: list) -> None:
        """Clear focus from all children."""
        for child in children:
            child.focused = False
        self._focus_index = -1

    def _move_focus(self, focusable: list, direction: int) -> None:
        """Move focus by ``direction`` (+1 or -1) through focusable children."""
        if not focusable:
            return

        if self._focus_index < 0:
            # Nothing focused yet — start at beginning or end
            next_idx = 0 if direction > 0 else len(focusable) - 1
        else:
            next_idx = (self._focus_index + direction) % len(focusable)

        self._apply_focus(focusable, next_idx)

    def _apply_focus(self, focusable: list, index: int) -> None:
        """Set focus to the item at ``index`` in ``focusable``."""
        # Clear all
        for child in focusable:
            child.focused = False
        # Set new
        if 0 <= index < len(focusable):
            focusable[index].focused = True
            self._focus_index = index

    def _current_focused(self, focusable: list) -> object | None:
        """Return the currently focused child, or None."""
        if 0 <= self._focus_index < len(focusable):
            return focusable[self._focus_index]
        return None

    @staticmethod
    def _focusable_children(children: list) -> list:
        """Return visible, enabled, focusable children in order."""
        return [
            c for c in children
            if getattr(c, "visible", True)
            and getattr(c, "enabled", True)
            and getattr(c, "focusable", False)
        ]
