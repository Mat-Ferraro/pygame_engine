"""
DialogueBox widget for pygame_engine.

Renders the current state of a DialogueRunner: speaker name, body text
with typewriter effect, and choice buttons when the player must choose.

The box does not drive the runner — it only reads from it and fires
callbacks on player input. Connect it to a runner and call update/render
each frame.

Usage::

    from pygame_engine.dialogue import DialogueBox, DialogueRunner, DialogueScript

    script = DialogueScript({...})
    runner = DialogueRunner(script)
    box    = DialogueBox(
        rect=pygame.Rect(60, 480, 800, 180),
        runner=runner,
        on_advance=lambda: runner.advance(),
    )
    runner.start()

    # Each frame:
    box.update(dt)
    box.render(surface)
"""

from __future__ import annotations

from typing import Callable

import pygame

from pygame_engine.dialogue.runner import DialogueRunner
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget
from pygame_engine.utils.mathx import clamp


class DialogueBox(Widget):
    """
    Dialogue rendering widget.

    Displays speaker name, body text with a typewriter effect, and
    choice buttons when the current node has choices.

    Input handling:
    - SPACE / RETURN / click:  If typewriter is still printing, completes
                               it immediately. Otherwise calls on_advance.
    - Number keys 1–9 / click on choice button: Select that choice.

    Args:
        rect:         Position and size. Recommend height ≥ 140px.
        runner:       The DialogueRunner to read state from.
        on_advance:   Called when the player wants to advance (no choices).
        on_choice:    Called with the choice index when a choice is selected.
                      If not provided, the box calls runner.select_choice()
                      directly.
        chars_per_sec: Typewriter speed. 0 = instant reveal.
    """

    PADDING     = 16
    SPEAKER_H   = 28
    CHOICE_H    = 36

    def __init__(
        self,
        rect:          pygame.Rect,
        runner:        DialogueRunner,
        on_advance:    Callable[[], None] | None = None,
        on_choice:     Callable[[int], None] | None = None,
        chars_per_sec: float = 40.0,
    ) -> None:
        super().__init__(rect)
        self._runner        = runner
        self._on_advance    = on_advance
        self._on_choice     = on_choice
        self._chars_per_sec = chars_per_sec

        # Typewriter state
        self._revealed:     float = 0.0   # chars revealed (float for smooth speed)
        self._full_text:    str   = ""
        self._node_id:      str   = ""    # tracks when runner node changes

        self._fonts: dict[str, pygame.font.Font] = {}

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        node = self._runner.current_node
        if node is None:
            return

        # Detect node change → reset typewriter
        if node.node_id != self._node_id:
            self._node_id  = node.node_id
            self._full_text = node.text
            self._revealed  = 0.0 if self._chars_per_sec > 0 else float(len(node.text))

        # Advance typewriter
        if self._revealed < len(self._full_text):
            if self._chars_per_sec > 0:
                self._revealed = min(
                    len(self._full_text),
                    self._revealed + self._chars_per_sec * dt,
                )

    @property
    def is_revealing(self) -> bool:
        """True while the typewriter effect is still printing."""
        return self._revealed < len(self._full_text)

    def complete_reveal(self) -> None:
        """Instantly reveal all text on the current node."""
        self._revealed = float(len(self._full_text))

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        node = self._runner.current_node
        if node is None or self._runner.is_complete:
            return False

        # Click or confirm key
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self._handle_confirm(event.pos)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._handle_confirm(None)

            # Number key shortcuts for choices
            if node.choices:
                num = event.key - pygame.K_1   # K_1=0, K_2=1, ...
                if 0 <= num < len(node.choices):
                    self._select_choice(num)
                    return True

        return False

    def _handle_confirm(self, mouse_pos: tuple[int, int] | None) -> bool:
        node = self._runner.current_node
        if node is None:
            return False

        # Complete typewriter first
        if self.is_revealing:
            self.complete_reveal()
            return True

        # Choice selection by click
        if node.choices and mouse_pos is not None:
            for i, choice_rect in enumerate(self._choice_rects()):
                if choice_rect.collidepoint(mouse_pos):
                    self._select_choice(i)
                    return True

        # Advance (no choices)
        if not node.choices:
            if self._on_advance:
                self._on_advance()
            return True

        return False

    def _select_choice(self, index: int) -> None:
        if self._on_choice:
            self._on_choice(index)
        else:
            self._runner.select_choice(index)

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        node = self._runner.current_node
        if node is None:
            return

        theme   = get_theme()
        colours = theme.colours
        pad     = self.PADDING

        # Background panel
        pygame.draw.rect(surface, colours.bg_raised, self.rect, border_radius=8)
        pygame.draw.rect(surface, colours.border,    self.rect, width=1, border_radius=8)

        # Speaker name bar
        if node.speaker:
            speaker_rect = pygame.Rect(
                self.rect.x, self.rect.y - self.SPEAKER_H,
                min(200, self.rect.width // 3), self.SPEAKER_H,
            )
            pygame.draw.rect(surface, colours.bg_raised, speaker_rect,
                             border_radius=6)
            pygame.draw.rect(surface, colours.border, speaker_rect,
                             width=1, border_radius=6)
            font = self._get_font("speaker", theme.typography.family,
                                  theme.typography.sm)
            txt = font.render(node.speaker, True, colours.text)
            surface.blit(txt, (
                speaker_rect.x + pad // 2,
                speaker_rect.centery - txt.get_height() // 2,
            ))

        # Body text
        body_rect = pygame.Rect(
            self.rect.x + pad,
            self.rect.y + pad,
            self.rect.width  - pad * 2,
            self.rect.height - pad * 2,
        )
        revealed_text = self._full_text[:int(self._revealed)]
        font = self._get_font("body", theme.typography.family,
                              theme.typography.md)
        self._render_wrapped(surface, font, revealed_text,
                             body_rect, colours.text)

        # Choices
        if node.choices and not self.is_revealing:
            choice_font = self._get_font("choice", theme.typography.family,
                                         theme.typography.sm)
            for i, (choice, crect) in enumerate(
                zip(node.choices, self._choice_rects())
            ):
                # Hover highlight
                mx, my = pygame.mouse.get_pos()
                hovered = crect.collidepoint(mx, my)
                bg = (theme.button.hovered.bg if hovered
                      else theme.button.normal.bg)
                pygame.draw.rect(surface, bg, crect, border_radius=4)
                pygame.draw.rect(surface, colours.border, crect,
                                 width=1, border_radius=4)

                label = f"{i+1}. {choice.label}"
                ctxt  = choice_font.render(label, True, colours.text)
                surface.blit(ctxt, (
                    crect.x + 8,
                    crect.centery - ctxt.get_height() // 2,
                ))

        # Advance indicator (▶) when text is fully revealed and no choices
        elif not self.is_revealing and not node.choices and not self._runner.is_complete:
            ind_font = self._get_font("indicator", theme.typography.family,
                                      theme.typography.sm)
            ind = ind_font.render("▶", True, colours.text_secondary)
            surface.blit(ind, (
                self.rect.right  - pad - ind.get_width(),
                self.rect.bottom - pad - ind.get_height(),
            ))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _choice_rects(self) -> list[pygame.Rect]:
        node = self._runner.current_node
        if not node or not node.choices:
            return []
        pad    = self.PADDING
        y      = self.rect.y + pad
        rects  = []
        for i in range(len(node.choices)):
            rects.append(pygame.Rect(
                self.rect.x + pad,
                y + i * (self.CHOICE_H + 4),
                self.rect.width - pad * 2,
                self.CHOICE_H,
            ))
        return rects

    def _get_font(self, key: str, family: str, size: int) -> pygame.font.Font:
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont(family, size)
        return self._fonts[key]

    def _render_wrapped(
        self,
        surface: pygame.Surface,
        font:    pygame.font.Font,
        text:    str,
        rect:    pygame.Rect,
        colour:  tuple[int, int, int],
    ) -> None:
        """Render word-wrapped text within rect."""
        words   = text.split(" ")
        lines: list[str] = []
        current = ""

        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= rect.width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_h = font.get_linesize()
        for i, line in enumerate(lines):
            y = rect.y + i * line_h
            if y + line_h > rect.bottom:
                break
            surf = font.render(line, True, colour)
            surface.blit(surf, (rect.x, y))
