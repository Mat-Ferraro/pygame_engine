"""
Base widget contract for pygame_engine.

Every UI element in the engine subclasses Widget. This base class provides
the minimal shared contract: rect, interaction state, and the three frame
methods. It does NOT manage children — that belongs to container widgets.

Typical subclass pattern::

    class Button(Widget):

        def __init__(self, rect: pygame.Rect, label: str) -> None:
            super().__init__(rect)
            self.label = label
            self._pressed = False

        def _handle_event_widget(self, event: pygame.event.Event) -> bool:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos) and self.is_interactive:
                    self._pressed = True
                    return True
            if event.type == pygame.MOUSEBUTTONUP:
                if self._pressed:
                    self._pressed = False
                    return True
            return False

        def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
            if not self.visible:
                return
            colour = (80, 80, 200) if not self._pressed else (60, 60, 160)
            pygame.draw.rect(surface, colour, self.rect, border_radius=4)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame


class Widget:
    """
    Base class for all UI elements in pygame_engine.

    Provides:
    - rect (position and size)
    - interaction state (visible, enabled, hovered, focused)
    - the three frame methods (handle_event, update, render)
    - hit-testing helpers

    Does NOT provide:
    - child management (see container widgets: Panel, Stack)
    - theme access (deferred until theme/runtime.py exists)
    - layout measurement (v1 uses assigned rects only)

    Interaction state rules
    -----------------------
    - A widget that is not ``visible`` skips rendering and does not receive
      events or update calls.
    - A widget that is not ``enabled`` skips event handling but still renders
      (typically greyed out). It still receives update calls so animations
      can continue.
    - ``hovered`` is maintained automatically in ``handle_event`` by checking
      MOUSEMOTION events against the widget rect. Subclasses do not need to
      manage this manually.
    - ``focused`` is set externally by a container or scene managing focus
      traversal. The base widget does not implement focus traversal itself.

    Subclassing
    -----------
    Override ``_handle_event_widget`` for event logic (not ``handle_event``
    directly) to preserve the visibility/enabled guard automatically.
    Override ``update`` and ``render`` as needed; call ``super()`` if you
    want the base behaviour to run.
    """

    def __init__(self, rect: pygame.Rect) -> None:
        """
        Initialise the widget with a rect and default interaction state.

        Args:
            rect: The position and size of this widget. Stored by reference —
                  mutations to the rect object are reflected immediately.
        """
        self.rect: pygame.Rect = rect

        # ── Interaction state ─────────────────────────────────────────────────
        self.visible: bool = True
        """
        When False the widget is not rendered and does not receive events
        or update calls.
        """

        self.enabled: bool = True
        """
        When False the widget does not process events (greyed-out state).
        It still renders and receives update calls.
        """

        self.hovered: bool = False
        """
        True when the mouse cursor is inside the widget rect.
        Maintained automatically via MOUSEMOTION in handle_event.
        """

        self.focused: bool = False
        """
        True when this widget has keyboard focus.
        Set externally by a container or scene; not managed internally.
        """

        self.focusable: bool = False
        """
        When True this widget participates in Tab focus traversal.
        Interactive widgets (Button, InputField) default to True.
        Display widgets (Label, TextBlock, ProgressBar) default to False.
        Set on each subclass, or override per-instance.
        """

    # ── Convenience ───────────────────────────────────────────────────────────

    @property
    def is_interactive(self) -> bool:
        """
        True when the widget can receive and respond to input.

        A widget is interactive only when both visible and enabled.
        Use this guard at the start of event handlers.
        """
        return self.visible and self.enabled

    # ── Frame methods ─────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Process a single pygame event.

        Guards:
        - returns False immediately if the widget is not visible
        - returns False immediately if the widget is not enabled
          (after updating hover state, which should still track)

        Hover is updated before the enabled check so that a disabled widget
        still shows correct hover state visually (e.g. a not-allowed cursor).

        Subclasses override ``_handle_event_widget`` rather than this method
        to keep the guards intact.

        Args:
            event: A raw pygame event.

        Returns:
            True if the event was consumed; False otherwise.
        """
        if not self.visible:
            return False

        # Update hover state regardless of enabled status.
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if not self.enabled:
            return False

        return self._handle_event_widget(event)

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        """
        Widget-specific event handling.

        Called by ``handle_event`` after visibility and enabled guards pass.
        Override this in subclasses rather than ``handle_event`` directly.

        Args:
            event: A raw pygame event.

        Returns:
            True if the event was consumed; False otherwise.
        """
        return False

    def update(self, dt: float) -> None:
        """
        Advance widget state by one frame.

        Not called when ``visible`` is False.

        Override to drive animations, timers, or state transitions.
        The base implementation is a no-op.

        Args:
            dt: Delta time in seconds since the last frame.
        """

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """
        Draw the widget onto the provided surface.

        Not called (and returns immediately) when ``visible`` is False.
        Override to draw widget content.

        The base implementation draws nothing.

        Args:
            surface: The surface to draw onto.
        """

    # ── Layout ────────────────────────────────────────────────────────────────

    def set_rect(self, rect: pygame.Rect) -> None:
        """
        Assign a new rect to this widget.

        Called by layout helpers to position widgets. Replacing the rect
        rather than mutating it in-place ensures subclasses that cache
        derived values can override this method to invalidate those caches.

        Args:
            rect: The new position and size.
        """
        self.rect = rect

    # ── Hit-testing ───────────────────────────────────────────────────────────

    def contains_point(self, point: tuple[int, int]) -> bool:
        """
        Return True if the given point falls within this widget's rect.

        Args:
            point: An (x, y) position in surface coordinates.
        """
        return self.rect.collidepoint(point)