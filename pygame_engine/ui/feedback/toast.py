"""
A short-lived message that appears briefly then fades out automatically.
Useful for non-blocking feedback: "Saved", "Error", "Level complete", etc.

The toast manages its own lifetime via a Timer. It fades in, holds, then
fades out. The caller checks ``is_expired`` each frame and removes or
recycles the toast when True.

Position is assigned externally (typically via anchor()). The toast does
not pick its own screen position.

Usage::

    from pygame_engine.ui.feedback.toast import Toast
    from pygame_engine.layout import anchor

    # Create and position
    screen = pygame.Rect(0, 0, 1280, 720)
    toast = Toast("Game saved!", duration=2.5)
    toast.set_rect(anchor(screen, (260, 48), "bottom", margin=40))
    toast.show()

    # Each frame:
    toast.update(dt)
    toast.render(surface)

    # Clean up when done:
    if toast.is_expired:
        toast = None
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame

from pygame_engine.graphics.surfaces import blit_alpha_surface, make_alpha_surface
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget
from pygame_engine.utils.timers import Timer


# Toast lifecycle phases
_PHASE_IDLE    = "idle"
_PHASE_FADE_IN = "fade_in"
_PHASE_HOLD    = "hold"
_PHASE_FADE_OUT = "fade_out"
_PHASE_EXPIRED  = "expired"


class Toast(Widget):
    """
    Short-lived notification message with auto-dismiss.

    Lifecycle
    ---------
    idle → fade_in → hold → fade_out → expired

    ``show()`` starts the cycle. ``is_expired`` becomes True when the
    fade-out completes. The toast can be re-shown by calling ``show()``
    again, which resets it to the fade-in phase.

    Styling
    -------
    Background, border, and text colours come from the active theme.
    An optional ``kind`` parameter selects a semantic colour tint:
    ``"info"`` (default), ``"success"``, ``"warning"``, ``"error"``.
    """

    FADE_IN_DURATION:  float = 0.15
    FADE_OUT_DURATION: float = 0.30

    def __init__(
        self,
        text: str = "",
        duration: float = 2.5,
        kind: str = "info",
        padding: int = 12,
    ) -> None:
        """
        Args:
            text:     The message to display.
            duration: How long the toast holds (fully visible) in seconds.
            kind:     Semantic colour — ``"info"``, ``"success"``,
                      ``"warning"``, or ``"error"``.
            padding:  Inner padding between text and background edge.
        """
        super().__init__(pygame.Rect(0, 0, 0, 0))
        self.visible = False

        self._text:     str   = text
        self._duration: float = duration
        self._kind:     str   = kind
        self._padding:  int   = padding

        self._phase:      str   = _PHASE_IDLE
        self._alpha:      float = 0.0
        self._phase_timer: Timer = Timer(0.0)

        self._font:      pygame.font.Font | None  = None
        self._text_surf: pygame.Surface | None    = None
        self._bg_surf:   pygame.Surface | None    = None
        self._dirty:     bool                     = True

        self._build_font()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def text(self) -> str:
        """Return the current toast message text."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Return the current toast message text."""
        if value != self._text:
            self._text = value
            self._dirty = True

    @property
    def is_expired(self) -> bool:
        """True when the toast has fully faded out and should be removed."""
        return self._phase == _PHASE_EXPIRED

    @property
    def is_active(self) -> bool:
        """True while the toast is visible in any phase."""
        return self._phase not in (_PHASE_IDLE, _PHASE_EXPIRED)

    def show(self) -> None:
        """Start or restart the toast lifecycle."""
        self.visible = True
        self._dirty  = True
        self._enter_phase(_PHASE_FADE_IN)

    def dismiss(self) -> None:
        """Immediately begin the fade-out phase."""
        if self._phase in (_PHASE_FADE_IN, _PHASE_HOLD):
            self._enter_phase(_PHASE_FADE_OUT)

    def set_rect(self, rect: pygame.Rect) -> None:
        """Update the toast rect and reposition content."""
        self.rect  = rect
        self._dirty = True

    # ── Frame methods ─────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Advance the toast lifecycle — fade in, hold, fade out."""
        if self._phase == _PHASE_IDLE or self._phase == _PHASE_EXPIRED:
            return

        self._phase_timer.update(dt)
        progress = self._phase_timer.progress

        if self._phase == _PHASE_FADE_IN:
            self._alpha = progress
            if self._phase_timer.is_done:
                self._enter_phase(_PHASE_HOLD)

        elif self._phase == _PHASE_HOLD:
            self._alpha = 1.0
            if self._phase_timer.is_done:
                self._enter_phase(_PHASE_FADE_OUT)

        elif self._phase == _PHASE_FADE_OUT:
            self._alpha = 1.0 - progress
            if self._phase_timer.is_done:
                self._phase   = _PHASE_EXPIRED
                self.visible  = False
                self._alpha   = 0.0

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """Draw the toast onto surface."""
        if not self.visible or self._alpha <= 0:
            return
        if self._dirty:
            self._rebuild_surfaces()
        if self._bg_surf is None or self._text_surf is None:
            return

        text_x = self.rect.x + self._padding
        text_y = self.rect.centery - self._text_surf.get_height() // 2
        blit_alpha_surface(surface, self._bg_surf, self.rect.topleft, self._alpha)
        blit_alpha_surface(surface, self._text_surf, (text_x, text_y), self._alpha)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _enter_phase(self, phase: str) -> None:
        self._phase = phase
        durations = {
            _PHASE_FADE_IN:  self.FADE_IN_DURATION,
            _PHASE_HOLD:     self._duration,
            _PHASE_FADE_OUT: self.FADE_OUT_DURATION,
        }
        self._phase_timer = Timer(durations.get(phase, 0.0), auto_start=True)

    def _build_font(self) -> None:
        theme = get_theme()
        self._font = pygame.font.SysFont(
            theme.typography.family,
            theme.typography.sm,
        )
        self._dirty = True

    def _resolve_bg_colour(self) -> tuple[int, int, int]:
        theme = get_theme()
        return {
            "success": theme.colours.bg_raised,
            "warning": theme.colours.bg_raised,
            "error":   theme.colours.bg_raised,
        }.get(self._kind, theme.colours.bg_raised)

    def _resolve_accent_colour(self) -> tuple[int, int, int]:
        theme = get_theme()
        return {
            "success": (60,  170, 100),
            "warning": (210, 150,  40),
            "error":   (200,  70,  60),
        }.get(self._kind, theme.colours.border)

    def _rebuild_surfaces(self) -> None:
        if self._font is None:
            return

        theme = get_theme()
        self._text_surf = self._font.render(
            self._text, True, theme.colours.text
        )

        # Size the background to fit the text if rect has no size yet
        tw = max(self.rect.width,
                 self._text_surf.get_width() + self._padding * 2)
        th = max(self.rect.height,
                 self._text_surf.get_height() + self._padding * 2)

        # Update rect dimensions (preserve position)
        self.rect.width  = tw
        self.rect.height = th

        bg_colour     = self._resolve_bg_colour()
        accent_colour = self._resolve_accent_colour()

        self._bg_surf = make_alpha_surface(tw, th)

        # Background fill
        pygame.draw.rect(
            self._bg_surf,
            (*bg_colour, 240),
            pygame.Rect(0, 0, tw, th),
            border_radius=6,
        )
        # Accent left bar
        pygame.draw.rect(
            self._bg_surf,
            (*accent_colour, 255),
            pygame.Rect(0, 0, 4, th),
            border_radius=3,
        )
        # Border
        pygame.draw.rect(
            self._bg_surf,
            (*theme.colours.border, 180),
            pygame.Rect(0, 0, tw, th),
            width=1,
            border_radius=6,
        )

        self._dirty = False