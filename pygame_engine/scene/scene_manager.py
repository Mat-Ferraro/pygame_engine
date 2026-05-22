"""
It owns the SceneStack and is the only place that calls scene lifecycle
hooks (on_enter, on_exit, on_pause, on_resume). Application drives
SceneManager each frame; game code interacts with it to change scenes.

Responsibilities
----------------
- Push / pop / replace scenes with correct lifecycle hook calls
- Delegate frame methods (handle_event, update, render) to SceneStack
- Manage optional scene transition effects
- Prevent lifecycle hook calls from being scattered across the codebase

Non-responsibilities
--------------------
- Game-specific logic
- Widget logic
- Becoming a general state store
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame

from pygame_engine.scene.scene import Scene
from pygame_engine.scene.scene_stack import SceneStack


class SceneManager:
    """
    Coordinates scene flow and owns the scene stack.

    All scene changes go through SceneManager so that lifecycle hooks
    are always called in the correct order. Optional transitions can be
    passed to ``push_with``, ``replace_with``, and ``pop_with``.

    Usage::

        manager = SceneManager()
        manager.push(MainMenuScene())   # no transition

        # With transition:
        from pygame_engine.scene.transitions import FadeTransition
        manager.replace_with(GameplayScene(), FadeTransition(duration=0.4))

        # Each frame (called by Application):
        manager.handle_event(event)
        manager.update(dt)
        manager.render(surface)
    """

    def __init__(self) -> None:
        self._stack:      SceneStack = SceneStack()
        self._transition: object | None = None   # active Transition | None
        self._trans_surf: pygame.Surface | None = None  # temp render surface

    # ── Scene changes — no transition ─────────────────────────────────────────

    def push(self, scene: Scene) -> None:
        """
        Push a new scene onto the stack and make it active.

        Lifecycle hooks: ``on_pause()`` on previous, ``on_enter()`` on new.
        """
        current = self._stack.top
        if current is not None:
            current.on_pause()
        self._stack.push(scene)
        scene.on_enter()

    def pop(self) -> Scene | None:
        """
        Remove the top scene and resume the one below it (if any).

        Lifecycle hooks: ``on_exit()`` on removed, ``on_resume()`` on resumed.

        Returns:
            The removed scene, or None if the stack was empty.
        """
        removed = self._stack.pop()
        if removed is not None:
            removed.on_exit()
        resumed = self._stack.top
        if resumed is not None:
            resumed.on_resume()
        return removed

    def replace(self, scene: Scene) -> Scene | None:
        """
        Replace the current top scene with a new one (lateral move).

        Lifecycle hooks: ``on_exit()`` on removed, ``on_enter()`` on new.
        The scene below is NOT paused or resumed.

        Returns:
            The replaced scene, or None if the stack was empty.
        """
        removed = self._stack.pop()
        if removed is not None:
            removed.on_exit()
        self._stack.push(scene)
        scene.on_enter()
        return removed

    def clear_and_push(self, scene: Scene) -> None:
        """
        Exit all scenes then push a fresh one.

        Lifecycle hooks: ``on_exit()`` on every removed (topmost first),
        ``on_enter()`` on the new scene.
        """
        for removed in self._stack.clear():
            removed.on_exit()
        self._stack.push(scene)
        scene.on_enter()

    # ── Scene changes — with transition ───────────────────────────────────────

    def push_with(
        self,
        scene:      Scene,
        transition: object,
        surface:    pygame.Surface | None = None,
    ) -> None:
        """
        Push a scene with a visual transition effect.

        The outgoing scene's current frame is captured, the scene change
        happens immediately, and the transition animates between the two.

        Args:
            scene:      The scene to push.
            transition: A ``Transition`` instance (Fade, Slide, Crossfade…).
            surface:    The display surface (used for capture). If None,
                        uses ``pygame.display.get_surface()``.
        """
        capture = self._capture_frame(surface)
        self.push(scene)
        self._start_transition(transition, capture)

    def replace_with(
        self,
        scene:      Scene,
        transition: object,
        surface:    pygame.Surface | None = None,
    ) -> Scene | None:
        """
        Replace the current scene with a visual transition.

        Args:
            scene:      The replacement scene.
            transition: A ``Transition`` instance.
            surface:    The display surface for capture.

        Returns:
            The replaced scene.
        """
        capture  = self._capture_frame(surface)
        removed  = self.replace(scene)
        self._start_transition(transition, capture)
        return removed

    def pop_with(
        self,
        transition: object,
        surface:    pygame.Surface | None = None,
    ) -> Scene | None:
        """
        Pop the top scene with a visual transition.

        Args:
            transition: A ``Transition`` instance.
            surface:    The display surface for capture.

        Returns:
            The removed scene.
        """
        capture = self._capture_frame(surface)
        removed = self.pop()
        self._start_transition(transition, capture)
        return removed

    # ── Frame delegation ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Route an event through the scene stack (blocking policy applies)."""
        return self._stack.handle_event(event)

    def update(self, dt: float) -> None:
        """Update the scene stack and advance any active transition."""
        self._stack.update(dt)

        if self._transition is not None:
            done = self._transition.update(dt)
            if done:
                self._transition = None
                self._trans_surf  = None

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """
        Render the scene stack, compositing any active transition.

        When a transition is active:
        1. The incoming scene renders to a temporary surface.
        2. The transition composites the capture + temp onto ``surface``.

        When no transition is active: delegates directly to SceneStack.
        """
        if self._transition is None:
            self._stack.render(surface, ctx)
            return

        # Ensure temp surface matches display size
        w, h = surface.get_size()
        if self._trans_surf is None or self._trans_surf.get_size() != (w, h):
            self._trans_surf = pygame.Surface((w, h))

        # Render incoming scene onto temp surface
        self._trans_surf.fill((0, 0, 0))
        self._stack.render(self._trans_surf, ctx)

        # Let transition composite everything onto the display surface
        self._transition.render(surface, self._trans_surf)

    def notify_resize(self, width: int, height: int) -> None:
        """
        Notify the current top-of-stack scene that the window was resized.

        Calls ``on_resize(width, height)`` on the active scene only.
        Scenes beneath the top are not notified — they will receive the
        update when they resume.

        Args:
            width:  New window width in pixels.
            height: New window height in pixels.
        """
        scene = self.current_scene
        if scene is not None:
            scene.on_resize(width, height)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def current_scene(self) -> Scene | None:
        """The currently active (topmost) scene, or None."""
        return self._stack.top

    @property
    def is_empty(self) -> bool:
        """True if no scenes are on the stack."""
        return self._stack.is_empty

    @property
    def is_transitioning(self) -> bool:
        """True while a visual transition is playing."""
        return self._transition is not None

    # ── Internal ──────────────────────────────────────────────────────────────

    def _capture_frame(
        self,
        surface: pygame.Surface | None,
    ) -> pygame.Surface:
        """Capture a copy of the current display surface."""
        src = surface or pygame.display.get_surface()
        if src is None:
            # Fallback: return a blank surface if display isn't ready
            return pygame.Surface((1, 1))
        capture = pygame.Surface(src.get_size())
        capture.blit(src, (0, 0))
        return capture

    def _start_transition(
        self,
        transition: object,
        capture:    pygame.Surface,
    ) -> None:
        """Start a transition with the given outgoing frame capture."""
        self._transition = transition
        self._trans_surf  = None
        transition.start(capture)  # type: ignore[attr-defined]