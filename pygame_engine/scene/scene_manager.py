"""
scene/scene_manager.py

SceneManager orchestrates scene flow for pygame_engine.

It owns the SceneStack and is the only place that calls scene lifecycle
hooks (on_enter, on_exit, on_pause, on_resume). Application drives
SceneManager each frame; game code interacts with it to change scenes.

Responsibilities
----------------
- Push / pop / replace scenes with correct lifecycle hook calls
- Delegate frame methods (handle_event, update, render) to SceneStack
- Prevent lifecycle hook calls from being scattered across the codebase

Non-responsibilities
--------------------
- Game-specific logic
- Widget logic
- Becoming a general state store
"""

from __future__ import annotations

import pygame

from pygame_engine.scene.scene import Scene
from pygame_engine.scene.scene_stack import SceneStack


class SceneManager:
    """
    Coordinates scene flow and owns the scene stack.

    All scene transitions go through SceneManager so that lifecycle hooks
    are always called in the correct order. SceneStack handles frame
    traversal policy; SceneManager handles the transition semantics.

    Usage::

        manager = SceneManager()
        manager.push(MainMenuScene())   # called once at startup by Application

        # Each frame (called by Application):
        manager.handle_event(event)
        manager.update(dt)
        manager.render(surface)

        # From inside a scene:
        app.scene_manager.push(PauseMenuScene())
        app.scene_manager.pop()
        app.scene_manager.replace(GameplayScene())
    """

    def __init__(self) -> None:
        self._stack: SceneStack = SceneStack()

    # ── Scene transitions ─────────────────────────────────────────────────────

    def push(self, scene: Scene) -> None:
        """
        Push a new scene onto the stack and make it active.

        Lifecycle hooks called:
          - ``on_pause()`` on the previously active scene (if any)
          - ``on_enter()`` on the new scene

        Args:
            scene: The scene to push.
        """
        current = self._stack.top
        if current is not None:
            current.on_pause()

        self._stack.push(scene)
        scene.on_enter()

    def pop(self) -> Scene | None:
        """
        Remove the top scene and resume the one below it (if any).

        Lifecycle hooks called:
          - ``on_exit()`` on the removed scene
          - ``on_resume()`` on the scene that becomes active (if any)

        Returns:
            The scene that was removed, or None if the stack was empty.
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
        Replace the current top scene with a new one.

        Equivalent to pop() followed by push(), but keeps it as one
        intentional operation with clear semantics. The scene below the
        replaced scene is NOT paused or resumed — replace() is a lateral
        move, not a stack depth change.

        Lifecycle hooks called:
          - ``on_exit()`` on the removed scene
          - ``on_enter()`` on the new scene

        Args:
            scene: The scene to push in place of the current top.

        Returns:
            The scene that was replaced, or None if the stack was empty.
        """
        removed = self._stack.pop()
        if removed is not None:
            removed.on_exit()

        self._stack.push(scene)
        scene.on_enter()

        return removed

    def clear_and_push(self, scene: Scene) -> None:
        """
        Exit and remove all current scenes, then push a fresh one.

        Useful for hard transitions like returning to the main menu from
        deep inside a gameplay session.

        Lifecycle hooks called:
          - ``on_exit()`` on every removed scene, topmost first
          - ``on_enter()`` on the new scene

        Args:
            scene: The scene to push after clearing the stack.
        """
        removed_scenes = self._stack.clear()
        for removed in removed_scenes:
            removed.on_exit()

        self._stack.push(scene)
        scene.on_enter()

    # ── Frame delegation ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Route an event through the scene stack.

        Delegates directly to SceneStack, which applies the blocking policy.

        Args:
            event: The pygame event to route.

        Returns:
            True if any scene consumed the event.
        """
        return self._stack.handle_event(event)

    def update(self, dt: float) -> None:
        """
        Update the scene stack for this frame.

        Delegates directly to SceneStack, which applies the blocking policy.

        Args:
            dt: Delta time in seconds.
        """
        self._stack.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Render the scene stack onto the provided surface.

        Delegates directly to SceneStack, which applies the blocking policy
        and bottom-up render order.

        Args:
            surface: The surface to render onto.
        """
        self._stack.render(surface)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def current_scene(self) -> Scene | None:
        """The currently active (topmost) scene, or None."""
        return self._stack.top

    @property
    def is_empty(self) -> bool:
        """True if no scenes are on the stack."""
        return self._stack.is_empty
