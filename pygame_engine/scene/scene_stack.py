"""
scene/scene_stack.py

Stack-based scene container for pygame_engine.

SceneStack owns the ordered list of active scenes and handles the three
traversal passes (input, update, render) according to each scene's blocking
policy flags.

Traversal rules
---------------
- Input:  top → bottom, stops when a scene returns True (consumed) or when
          a scene has ``blocks_input_below = True``.
- Update: top → bottom, stops when a scene has ``blocks_update_below = True``.
- Render: bottom → top (so lower scenes draw first), starting from the lowest
          scene that is not hidden by a ``blocks_render_below`` scene above it.

SceneStack does not call lifecycle hooks directly. SceneManager is responsible
for calling on_enter, on_exit, on_pause, and on_resume at the right times.
SceneStack only manages the container and the frame traversals.
"""

from __future__ import annotations

import pygame

from pygame_engine.scene.scene import Scene


class SceneStack:
    """
    Ordered stack of active scenes.

    The last scene in ``_stack`` is the top (active) scene.
    Scenes are pushed and popped by SceneManager; SceneStack provides the
    container and the per-frame traversal logic.
    """

    def __init__(self) -> None:
        self._stack: list[Scene] = []

    # ── Stack access ──────────────────────────────────────────────────────────

    @property
    def top(self) -> Scene | None:
        """The currently active (topmost) scene, or None if the stack is empty."""
        return self._stack[-1] if self._stack else None

    @property
    def is_empty(self) -> bool:
        """True if no scenes are on the stack."""
        return len(self._stack) == 0

    def __len__(self) -> int:
        return len(self._stack)

    # ── Mutation (called by SceneManager only) ────────────────────────────────

    def push(self, scene: Scene) -> None:
        """
        Push a scene onto the top of the stack.

        Does not call any lifecycle hooks — that is SceneManager's job.

        Args:
            scene: The scene to push.
        """
        self._stack.append(scene)

    def pop(self) -> Scene | None:
        """
        Remove and return the top scene.

        Does not call any lifecycle hooks — that is SceneManager's job.

        Returns:
            The removed scene, or None if the stack was already empty.
        """
        return self._stack.pop() if self._stack else None

    def clear(self) -> list[Scene]:
        """
        Remove all scenes from the stack and return them in top-first order.

        Does not call any lifecycle hooks — SceneManager must handle that
        before calling this.

        Returns:
            All scenes that were on the stack, topmost first.
        """
        scenes = list(reversed(self._stack))
        self._stack.clear()
        return scenes

    # ── Frame traversals ──────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Route an event top-down through the stack.

        Stops early if:
        - a scene consumes the event (returns True), or
        - a scene has ``blocks_input_below = True``

        Args:
            event: The pygame event to route.

        Returns:
            True if any scene consumed the event; False otherwise.
        """
        for scene in reversed(self._stack):
            consumed = scene.handle_event(event)
            if consumed:
                return True
            if scene.blocks_input_below:
                break
        return False

    def update(self, dt: float) -> None:
        """
        Update scenes top-down through the stack.

        Stops when a scene has ``blocks_update_below = True`` (that scene
        is still updated; scenes below it are not).

        Args:
            dt: Delta time in seconds.
        """
        for scene in reversed(self._stack):
            scene.update(dt)
            if scene.blocks_update_below:
                break

    def render(self, surface: pygame.Surface) -> None:
        """
        Render scenes bottom-up, starting from the lowest visible scene.

        Finds the lowest scene that should be rendered by scanning top-down
        for ``blocks_render_below`` flags, then renders from there upward
        so that higher scenes draw on top of lower ones.

        Args:
            surface: The surface to render onto.
        """
        if not self._stack:
            return

        # Find the index of the lowest scene that should be rendered.
        # Walk top-down; the first scene with blocks_render_below=True is
        # the bottom of the visible window.
        render_from = 0
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].blocks_render_below:
                render_from = i
                break

        # Render bottom-up from render_from so higher scenes composite on top.
        for scene in self._stack[render_from:]:
            scene.render(surface)
