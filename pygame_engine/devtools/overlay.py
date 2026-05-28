"""
debug/overlay.py

Visual debug overlay for pygame_engine.

Renders a small information panel in the top-left corner of the screen
when ``flags.show_overlay`` is True. Draws after all scene/UI rendering
so it always sits on top.

Displays:
- FPS and frame time
- Current scene class name
- Scene stack depth
- Active runtime flags

Driven by ``flags.show_overlay`` and ``flags.show_fps``.
Toggled at runtime via the DEBUG_TOGGLE action (F1 by default).

Usage::

    # In Application._loop, after scene render and before flip:
    from pygame_engine.devtools.overlay import DebugOverlay
    overlay = DebugOverlay()
    overlay.render(surface, clock, scene_manager)
"""

from __future__ import annotations

import pygame

from pygame_engine.state.runtime_flags import flags


class DebugOverlay:
    """
    On-screen debug information panel.

    Lightweight — creates its font once, renders text each frame.
    Intended to be owned by ``Application`` and rendered last each frame.
    """

    # Visual constants
    PADDING    = 8
    LINE_HEIGHT = 16
    BG_COLOUR  = (0, 0, 0, 160)
    FPS_COLOUR = (100, 220, 100)
    INFO_COLOUR = (200, 200, 200)
    WARN_COLOUR = (220, 180, 60)
    FLAG_COLOUR = (120, 180, 255)

    def __init__(self) -> None:
        self._font: pygame.font.Font | None = None

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(
        self,
        surface:       pygame.Surface,
        clock:         pygame.time.Clock,
        scene_manager: object | None = None,
    ) -> None:
        """
        Draw the debug overlay onto ``surface``.

        Does nothing if ``flags.show_overlay`` is False.

        Args:
            surface:       The display surface to draw onto.
            clock:         The application clock (for FPS/frame-time).
            scene_manager: The SceneManager instance (for scene info).
                           Optional — scene info is skipped if None.
        """
        if not flags.show_overlay:
            return

        if self._font is None:
            self._font = pygame.font.SysFont("consolas,monospace", 13)

        lines = self._build_lines(clock, scene_manager)
        self._draw_panel(surface, lines)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_lines(
        self,
        clock:         pygame.time.Clock,
        scene_manager: object | None,
    ) -> list[tuple[str, tuple[int, int, int]]]:
        """Build the list of (text, colour) lines to display."""
        lines: list[tuple[str, tuple[int, int, int]]] = []

        # FPS / frame time
        fps = clock.get_fps()
        ms  = clock.get_time()
        fps_colour = (
            self.FPS_COLOUR if fps >= 55
            else self.WARN_COLOUR if fps >= 30
            else (220, 80, 60)
        )
        lines.append((f"FPS  {fps:5.1f}   {ms:3d}ms", fps_colour))

        # Scene info
        if scene_manager is not None:
            scene = getattr(scene_manager, "current_scene", None)
            stack = getattr(scene_manager, "_stack", None)
            depth = len(stack) if stack is not None else "?"
            name  = type(scene).__name__ if scene else "None"
            lines.append((f"Scene  {name}", self.INFO_COLOUR))
            lines.append((f"Stack  depth={depth}", self.INFO_COLOUR))

        # Active flags
        active = [k for k, v in flags.as_dict().items() if v]
        if active:
            lines.append((f"Flags  {', '.join(active)}", self.FLAG_COLOUR))

        return lines

    def _draw_panel(
        self,
        surface: pygame.Surface,
        lines:   list[tuple[str, tuple[int, int, int]]],
    ) -> None:
        """Draw the semi-transparent background and all text lines."""
        if not lines or self._font is None:
            return

        p = self.PADDING
        w = max(self._font.size(text)[0] for text, _ in lines) + p * 2
        h = len(lines) * self.LINE_HEIGHT + p * 2

        # Semi-transparent background
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill(self.BG_COLOUR)
        surface.blit(bg, (0, 0))

        # Text lines
        for i, (text, colour) in enumerate(lines):
            rendered = self._font.render(text, True, colour)
            surface.blit(rendered, (p, p + i * self.LINE_HEIGHT))