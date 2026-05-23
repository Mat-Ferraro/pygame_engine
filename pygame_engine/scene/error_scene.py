"""
Built-in fallback scene for unhandled runtime errors.

When ``Application._loop()`` catches an exception during ``update()`` or
``render()``, it pushes ``ErrorScene`` rather than crashing. The scene
displays enough information for the developer to diagnose the problem and
provides a clean recovery path.

Behaviour by mode
-----------------
- **development** — shows the full Python traceback on screen. ESC pops
  back to the previous scene (which may be broken) or quits if the stack
  is now empty.
- **production** — shows a simple, player-facing message. No technical
  details. ESC quits the application.
- **testing** — never used; Application re-raises in testing mode so
  pytest can catch the exception.

Custom error scene
------------------
Games can supply their own error scene via ``AppConfig.error_scene_class``::

    config = AppConfig(
        error_scene_class=MyErrorScene,
    )

``MyErrorScene`` must accept ``(exc, mode)`` as constructor arguments.

Usage (internal — called by Application)::

    from pygame_engine.scene.error_scene import ErrorScene
    scene_manager.push(ErrorScene(exc, mode="development"))
"""

from __future__ import annotations

import traceback
from typing import Literal

import pygame

from pygame_engine.scene.scene import Scene
from pygame_engine.theme.runtime import get_theme

AppMode = Literal["development", "production", "testing"]


class ErrorScene(Scene):
    """
    Fallback scene displayed when a runtime error occurs in a scene.

    In development mode: renders the full traceback so the developer
    can read the error without leaving the window.

    In production mode: renders a simple, friendly message.

    Args:
        exc:  The exception that was caught.
        mode: The application mode (``"development"`` or ``"production"``).
    """

    # Scenes below remain visible (nice fallback visual behind the overlay)
    blocks_render_below: bool = False
    blocks_update_below: bool = True
    blocks_input_below:  bool = True

    def __init__(
        self,
        exc:  BaseException,
        mode: AppMode = "development",
    ) -> None:
        super().__init__()
        self._exc  = exc
        self._mode = mode
        self._font:       pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._lines: list[str] = []
        self._scroll: int = 0

    def on_enter(self) -> None:
        pygame.font.init()
        self._font       = pygame.font.SysFont("monospace", 14)
        self._small_font = pygame.font.SysFont("monospace", 12)

        if self._mode == "development":
            tb_lines = traceback.format_exception(
                type(self._exc), self._exc, self._exc.__traceback__
            )
            self._lines = []
            for block in tb_lines:
                self._lines.extend(block.splitlines())
        else:
            self._lines = [
                "An unexpected error occurred.",
                "",
                "Please restart the application.",
                "",
                "If this keeps happening, contact support.",
            ]

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Signal caller to pop or quit — handled by Application
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return True
            if event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll - 1)
                return True
            if event.key == pygame.K_DOWN:
                self._scroll = min(
                    max(0, len(self._lines) - 20), self._scroll + 1
                )
                return True
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(
                0, min(max(0, len(self._lines) - 20),
                       self._scroll - event.y)
            )
            return True
        return False

    def render(self, surface: pygame.Surface, ctx=None) -> None:
        w, h = surface.get_size()

        # Semi-transparent dark overlay (scenes below still visible)
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 220))
        surface.blit(overlay, (0, 0))

        if self._font is None:
            return

        pad   = 24
        line_h = 18

        # ── Header ────────────────────────────────────────────────────────────
        if self._mode == "development":
            header   = f"  Runtime Error: {type(self._exc).__name__}"
            subhead  = "  ESC = quit   ↑↓ / scroll = navigate"
            h_colour = (255, 80, 80)
        else:
            header   = "  Something went wrong"
            subhead  = "  ESC = quit"
            h_colour = (255, 160, 80)

        hdr_surf = self._font.render(header, True, h_colour)
        surface.blit(hdr_surf, (pad, pad))

        sub_surf = self._small_font.render(subhead, True, (160, 160, 160))
        surface.blit(sub_surf, (pad, pad + line_h + 4))

        pygame.draw.line(
            surface, (80, 80, 100),
            (pad, pad + line_h * 2 + 8),
            (w - pad, pad + line_h * 2 + 8),
        )

        # ── Traceback / message ───────────────────────────────────────────────
        y      = pad + line_h * 2 + 16
        colour = (220, 220, 200) if self._mode == "development" else (200, 200, 200)

        visible = self._lines[self._scroll:]
        for line in visible:
            if y + line_h > h - pad:
                break
            # Indent detection for readable colouring
            c = colour
            ls = line.strip()
            if ls.startswith("File "):
                c = (140, 180, 255)
            elif ls.startswith("raise") or "Error" in ls or "Exception" in ls:
                c = (255, 120, 100)

            rendered = self._small_font.render(line, True, c)
            surface.blit(rendered, (pad, y))
            y += line_h

    def __repr__(self) -> str:
        return f"ErrorScene(exc={type(self._exc).__name__!r}, mode={self._mode!r})"
