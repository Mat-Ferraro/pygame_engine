"""
On-screen debug log console for pygame_engine.

Renders the most recent debug log entries as a scrolling text panel.
Not interactive in v1 — display only.

Toggled by ``flags.show_console`` (F3 by default).
Positioned at the bottom of the screen.

Usage::

    from pygame_engine.devtools.console import DebugConsole

    console = DebugConsole()

    # After scene render, before flip:
    console.render(surface)
"""

from __future__ import annotations

import pygame

from pygame_engine.devtools.debug_log import LogLevel, get_entries
from pygame_engine.state.runtime_flags import flags


class DebugConsole:
    """
    On-screen tail of the debug log.

    Displays the most recent N entries from ``debug_log`` as a
    semi-transparent panel at the bottom of the screen.
    Not interactive in v1 — display only.
    """

    MAX_LINES  = 12
    PADDING    = 6
    LINE_HEIGHT = 15
    BG_COLOUR  = (0, 0, 0, 140)

    LEVEL_COLOURS = {
        LogLevel.INFO:  (180, 180, 190),
        LogLevel.WARN:  (220, 180, 60),
        LogLevel.ERROR: (220, 80,  60),
    }

    def __init__(self) -> None:
        self._font: pygame.font.Font | None = None

    def render(self, surface: pygame.Surface) -> None:
        """
        Draw the console log panel onto ``surface``.

        Does nothing if ``flags.show_console`` is False.

        Args:
            surface: The display surface to draw onto.
        """
        if not flags.show_console:
            return

        if self._font is None:
            self._font = pygame.font.SysFont("consolas,monospace", 12)

        entries = get_entries(limit=self.MAX_LINES)
        if not entries:
            return

        p  = self.PADDING
        sw = surface.get_width()
        sh = surface.get_height()
        h  = len(entries) * self.LINE_HEIGHT + p * 2
        y  = sh - h

        bg = pygame.Surface((sw, h), pygame.SRCALPHA)
        bg.fill(self.BG_COLOUR)
        surface.blit(bg, (0, y))

        # Entries are newest-first; render oldest at top of panel
        for i, entry in enumerate(reversed(entries)):
            colour = self.LEVEL_COLOURS.get(entry.level, (200, 200, 200))
            text   = f"[{entry.level}][{entry.tag}] {entry.message}"
            rendered = self._font.render(text, True, colour)
            surface.blit(rendered, (p, y + p + i * self.LINE_HEIGHT))