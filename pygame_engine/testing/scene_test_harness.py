"""
SceneTestHarness — headless scene testing without a display window.

Lets you load a scene, advance frames, simulate input events, and assert
on observable values — all in a pytest test, no window required.

Usage::

    from pygame_engine.testing.scene_test_harness import SceneTestHarness

    def test_button_increments_counter():
        harness = SceneTestHarness(MyScene())
        harness.enter()

        harness.advance(frames=1)
        harness.press_key(pygame.K_SPACE)
        harness.advance(frames=1)

        scene = harness.scene
        assert scene.counter == 1

        harness.exit()

Context manager usage::

    with SceneTestHarness(MyScene()) as h:
        h.click(100, 200)
        h.advance(frames=5)
        assert h.scene.state == "active"

The harness uses ``AppConfig(mode="testing")`` semantics — runtime errors
are re-raised instead of being swallowed by ``ErrorScene``.
"""

from __future__ import annotations

from typing import Any

import pygame


class SceneTestHarness:
    """
    Headless test driver for a single scene.

    Does not open a window. Creates a minimal off-screen surface for
    render calls. Scene ``on_enter()`` and ``on_exit()`` lifecycle hooks
    fire correctly.

    Args:
        scene:   The scene instance to test.
        width:   Off-screen surface width. Default 1280.
        height:  Off-screen surface height. Default 720.
        dt:      Fixed delta-time used for ``advance()``. Default 1/60.
    """

    def __init__(
        self,
        scene:  Any,        # Scene — avoid circular import
        width:  int   = 1280,
        height: int   = 720,
        dt:     float = 1 / 60,
    ) -> None:
        self._scene   = scene
        self._dt      = dt
        self._entered = False

        # Minimal pygame init (headless — no display)
        if not pygame.get_init():
            pygame.init()

        # Off-screen render surface
        self._surface = pygame.Surface((width, height))

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def enter(self) -> "SceneTestHarness":
        """
        Call ``scene.on_enter()`` and mark the harness as active.

        Returns:
            ``self`` for chaining.
        """
        if not self._entered:
            self._scene.on_enter()
            self._entered = True
        return self

    def exit(self) -> None:
        """
        Call ``scene.on_exit()`` and tear down the harness.
        """
        if self._entered:
            self._scene.on_exit()
            self._entered = False

    def __enter__(self) -> "SceneTestHarness":
        return self.enter()

    def __exit__(self, *args: object) -> None:
        self.exit()

    # ── Frame advancement ─────────────────────────────────────────────────────

    def advance(self, frames: int = 1) -> "SceneTestHarness":
        """
        Advance the scene by ``frames`` update/render cycles.

        Each cycle calls ``scene.update(dt)`` then ``scene.render(surface, ctx)``.
        Runtime errors are re-raised (testing mode semantics).

        Args:
            frames: Number of frames to advance. Default 1.

        Returns:
            ``self`` for chaining.
        """
        from pygame_engine.app.render_context import RenderContext
        from pygame_engine.theme.runtime import get_theme

        ctx = RenderContext(theme=get_theme())
        for _ in range(frames):
            self._scene.update(self._dt)
            self._scene.render(self._surface, ctx)
        return self

    # ── Input simulation ──────────────────────────────────────────────────────

    def press_key(
        self,
        key:    int,
        mods:   int = 0,
        unicode: str = "",
    ) -> "SceneTestHarness":
        """
        Simulate a KEYDOWN event followed by a KEYUP event.

        Both events are routed through ``scene.handle_event()``.

        Args:
            key:     pygame key constant (e.g. ``pygame.K_SPACE``).
            mods:    Modifier key mask (e.g. ``pygame.KMOD_SHIFT``).
            unicode: Unicode character string for the key.

        Returns:
            ``self`` for chaining.
        """
        down = pygame.event.Event(
            pygame.KEYDOWN,
            key=key, mod=mods, unicode=unicode, scancode=0,
        )
        up = pygame.event.Event(
            pygame.KEYUP,
            key=key, mod=mods, unicode=unicode, scancode=0,
        )
        self._scene.handle_event(down)
        self._scene.handle_event(up)
        return self

    def type_text(self, text: str) -> "SceneTestHarness":
        """
        Simulate typing a string of characters via TEXTINPUT events.

        Args:
            text: The string to type. Each character is a separate event.

        Returns:
            ``self`` for chaining.
        """
        for char in text:
            event = pygame.event.Event(pygame.TEXTINPUT, text=char)
            self._scene.handle_event(event)
        return self

    def click(
        self,
        x:      int,
        y:      int,
        button: int = 1,
    ) -> "SceneTestHarness":
        """
        Simulate a mouse click (MOUSEBUTTONDOWN + MOUSEBUTTONUP) at (x, y).

        Args:
            x:      Horizontal position in screen coordinates.
            y:      Vertical position in screen coordinates.
            button: Mouse button number. 1 = left, 2 = middle, 3 = right.

        Returns:
            ``self`` for chaining.
        """
        pos = (x, y)
        down = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, pos=pos, button=button,
        )
        up = pygame.event.Event(
            pygame.MOUSEBUTTONUP, pos=pos, button=button,
        )
        self._scene.handle_event(down)
        self._scene.handle_event(up)
        return self

    def move_mouse(self, x: int, y: int) -> "SceneTestHarness":
        """
        Simulate a MOUSEMOTION event to the given position.

        Args:
            x: Horizontal position in screen coordinates.
            y: Vertical position in screen coordinates.

        Returns:
            ``self`` for chaining.
        """
        event = pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=(x, y), rel=(0, 0), buttons=(0, 0, 0),
        )
        self._scene.handle_event(event)
        return self

    def scroll(self, dy: int) -> "SceneTestHarness":
        """
        Simulate a MOUSEWHEEL event.

        Args:
            dy: Vertical scroll amount. Positive = scroll up.

        Returns:
            ``self`` for chaining.
        """
        event = pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=dy)
        self._scene.handle_event(event)
        return self

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def scene(self) -> Any:
        """The scene being tested."""
        return self._scene

    @property
    def surface(self) -> pygame.Surface:
        """The off-screen render surface."""
        return self._surface

    @property
    def entered(self) -> bool:
        """True if ``enter()`` has been called and ``exit()`` has not."""
        return self._entered

    def find_widget(self, widget_id: str) -> Any:
        """
        Find a widget in the scene's root widget tree by ``widget_id``.

        Performs a depth-first search through the widget tree starting at
        ``scene.root_widget``.

        Args:
            widget_id: The ``widget_id`` string to search for.

        Returns:
            The matching widget.

        Raises:
            LookupError: If no widget with the given id is found.
        """
        root = getattr(self._scene, "root_widget", None)
        if root is None:
            raise LookupError(
                f"Scene has no root_widget — cannot search for {widget_id!r}"
            )
        result = self._dfs(root, widget_id)
        if result is None:
            raise LookupError(
                f"No widget with widget_id={widget_id!r} found in scene tree"
            )
        return result

    def _dfs(self, widget: Any, widget_id: str) -> Any:
        """Depth-first widget search."""
        if getattr(widget, "widget_id", None) == widget_id:
            return widget
        children = getattr(widget, "_children", None) or getattr(widget, "children", None)
        if children:
            for child in children:
                result = self._dfs(child, widget_id)
                if result is not None:
                    return result
        return None

    def __repr__(self) -> str:
        state = "active" if self._entered else "idle"
        return f"SceneTestHarness({self._scene.__class__.__name__!r}, {state})"
