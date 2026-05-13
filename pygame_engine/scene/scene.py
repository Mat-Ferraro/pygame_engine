"""
Base scene contract for pygame_engine.

Scenes represent high-level application states: menus, gameplay screens,
settings dialogs, pause overlays, loading screens, etc.

Every scene in a project built on pygame_engine should subclass Scene and
override the lifecycle hooks and frame methods it needs. All hooks have safe
no-op defaults so subclasses only write what they actually use.

Typical usage::

    class MainMenuScene(Scene):

        def on_enter(self) -> None:
            self.root_widget = build_main_menu_ui()

        def update(self, dt: float) -> None:
            if self.root_widget:
                self.root_widget.update(dt)

        def render(self, surface: pygame.Surface) -> None:
            surface.fill((20, 20, 30))
            if self.root_widget:
                self.root_widget.render(surface)
"""

from __future__ import annotations

import pygame

from pygame_engine.ui.base.widget import Widget


class Scene:
    """
    Base class for all scenes in pygame_engine.

    Subclass this and override the methods your scene needs. Every method
    has a safe default (no-op or False) so partial overrides are fine.

    Blocking policy
    ---------------
    Scenes sit in a stack. The three ``blocks_*_below`` flags control what
    happens to scenes further down the stack each frame:

    - ``blocks_input_below``  — lower scenes do not receive events
    - ``blocks_update_below`` — lower scenes do not receive ``update()``
    - ``blocks_render_below`` — lower scenes do not receive ``render()``

    A normal fullscreen scene blocks all three.
    A pause overlay typically blocks input and update but not render
    (so the gameplay scene remains visible behind it).
    A debug overlay blocks nothing.

    Root widget
    -----------
    A scene may own one optional ``root_widget``. Event routing passes
    events to the root widget *before* the scene's own ``handle_event``
    logic, so UI can consume input first. See ``handle_event`` for detail.
    """

    # ── Blocking policy ───────────────────────────────────────────────────────

    blocks_input_below: bool = True
    """If True, scenes below this one on the stack do not receive events."""

    blocks_update_below: bool = True
    """If True, scenes below this one on the stack are not updated."""

    blocks_render_below: bool = True
    """If True, scenes below this one on the stack are not rendered."""

    # ── Optional root widget ──────────────────────────────────────────────────

    root_widget: Widget | None = None
    """
    Optional top-level widget tree owned by this scene.

    When present, ``handle_event``, ``update``, and ``render`` delegate to
    it automatically (root widget is called first in each case). Scenes that
    want different routing can override those methods entirely.
    """

    # ── Lifecycle hooks ───────────────────────────────────────────────────────

    def on_enter(self) -> None:
        """
        Called once when this scene becomes the active scene.

        Use this to:
        - initialise runtime-only state (not persistent data)
        - start animations or timers
        - subscribe to engine events
        - build or assign ``root_widget``

        Not called when a scene *resumes* after a scene above it is popped —
        that is ``on_resume``.
        """

    def on_exit(self) -> None:
        """
        Called once when this scene is permanently removed from the stack.

        Use this to:
        - unsubscribe from engine events
        - release temporary resources
        - stop audio or effects that belong to this scene

        Not called when a scene is merely paused by a push — that is
        ``on_pause``.
        """

    def on_pause(self) -> None:
        """
        Called when another scene is pushed on top of this one.

        This scene remains on the stack but is no longer the top scene.
        Use this to pause timers, animations, or input-sensitive behavior
        that should not continue while covered by another scene.
        """

    def on_resume(self) -> None:
        """
        Called when the scene above this one is popped and this scene
        becomes active again.

        Use this to resume timers, refresh input state assumptions, or
        restart any visual indicators that were paused.
        """

    # ── Frame methods ─────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Process a single pygame event.

        Routing order (root widget first, then scene):
          1. If ``root_widget`` is present, offer the event to it first.
             If the widget consumes it (returns True), stop here.
          2. Otherwise, fall through to scene-level handling in
             ``_handle_event_scene``, which subclasses override.

        This order ensures UI always gets first refusal on input, which
        prevents a button click from also triggering scene-level logic.

        Args:
            event: A raw pygame event.

        Returns:
            True if the event was consumed; False otherwise.
        """
        if self.root_widget is not None:
            if self.root_widget.handle_event(event):
                return True

        return self._handle_event_scene(event)

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        """
        Scene-level event handling, called after the root widget has had
        first opportunity to consume the event.

        Override this in subclasses instead of ``handle_event`` directly
        when you want to keep the standard widget-first routing intact.

        Args:
            event: A raw pygame event not consumed by the root widget.

        Returns:
            True if the event was consumed; False otherwise.
        """
        return False

    def update(self, dt: float) -> None:
        """
        Advance scene state by one frame.

        Default behavior: delegates to ``root_widget.update(dt)`` if a
        root widget is present. Override to add scene-level update logic;
        call ``super().update(dt)`` to keep widget delegation.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        if self.root_widget is not None:
            self.root_widget.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Draw this scene onto the provided surface.

        Default behavior:
        1. Renders ``root_widget`` (the normal widget tree).
        2. Calls ``overlay_render(surface)`` for floating UI (Dropdowns,
           Tooltips) that must appear above all other widgets.

        Override to take full control. Call ``super().render(surface)``
        to keep both passes.

        Args:
            surface: The surface to draw onto (usually the display surface).
        """
        if self.root_widget is not None:
            self.root_widget.render(surface)
        self.overlay_render(surface)

    def overlay_render(self, surface: pygame.Surface) -> None:
        """
        Second render pass for floating UI elements.

        Called automatically by ``render()`` after the main widget tree.
        Override to render Dropdowns, Tooltips, or any widget that must
        appear above everything else::

            def overlay_render(self, surface):
                self._quality_dropdown.overlay_render(surface)

        Default: no-op.

        Args:
            surface: The surface to draw onto.
        """
        pass
