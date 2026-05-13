"""
RichLabel — inline-markup text rendering for pygame_engine.

Renders text with BBCode-style inline markup tags:

    [b]bold text[/b]
    [i]italic text[/i]
    [b][i]bold italic[/i][/b]
    [color=#ff4444]red text[/color]
    [color=#80ff80]green text[/color]
    [size=24]big text[/size]

Tags may be nested. Unknown or malformed tags are rendered as literal text.

Usage::

    from pygame_engine.ui.text.rich_label import RichLabel

    lbl = RichLabel(
        rect=pygame.Rect(100, 200, 400, 32),
        text="Collect [color=#ffd700][b]{count} coins[/b][/color] to win!",
    )
    lbl.text = lbl.text.format(count=42)

    # In render:
    lbl.render(surface)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


# ── Span model ────────────────────────────────────────────────────────────────

@dataclass
class _Span:
    """A single styled run of text."""
    text:       str
    colour:     tuple[int, int, int] | None = None   # None = inherit
    font_size:  int | None                  = None   # None = inherit
    bold:       bool                        = False
    italic:     bool                        = False


# ── Tag parser ────────────────────────────────────────────────────────────────

_TAG_RE = re.compile(r'\[(/?)(\w+)(?:=([^\]]+))?\]')


def parse_markup(text: str,
                 base_colour: tuple[int, int, int],
                 base_size:   int) -> list[_Span]:
    """
    Parse BBCode-style markup into a list of styled spans.

    Recognised tags:
        [b]...[/b]           — bold
        [i]...[/i]           — italic
        [color=#rrggbb]...[/color]  — colour (hex)
        [size=N]...[/size]   — font size override

    Args:
        text:         The raw markup string.
        base_colour:  Default text colour.
        base_size:    Default font size.

    Returns:
        List of ``_Span`` objects in order.
    """
    spans:   list[_Span]               = []
    # State stacks
    colours: list[tuple[int,int,int]]  = [base_colour]
    sizes:   list[int]                 = [base_size]
    bolds:   list[bool]                = [False]
    italics: list[bool]                = [False]

    pos = 0
    for m in _TAG_RE.finditer(text):
        start, end = m.span()

        # Flush text before tag
        if start > pos:
            chunk = text[pos:start]
            if chunk:
                spans.append(_Span(chunk,
                                   colours[-1], sizes[-1],
                                   bolds[-1], italics[-1]))
        pos = end

        closing = m.group(1) == "/"
        tag     = m.group(2).lower()
        value   = m.group(3)

        if closing:
            if tag == "b"     and len(bolds)   > 1: bolds.pop()
            elif tag == "i"   and len(italics) > 1: italics.pop()
            elif tag == "color" and len(colours) > 1: colours.pop()
            elif tag == "size"  and len(sizes)   > 1: sizes.pop()
        else:
            if tag == "b":
                bolds.append(True)
            elif tag == "i":
                italics.append(True)
            elif tag == "color" and value:
                colours.append(_parse_hex(value, base_colour))
            elif tag == "size" and value:
                try:
                    sizes.append(int(value))
                except ValueError:
                    pass   # ignore bad size

    # Flush remaining text
    if pos < len(text):
        chunk = text[pos:]
        if chunk:
            spans.append(_Span(chunk,
                               colours[-1], sizes[-1],
                               bolds[-1], italics[-1]))
    return spans


def _parse_hex(value: str, fallback: tuple[int,int,int]) -> tuple[int,int,int]:
    """Parse '#rrggbb' or 'rrggbb' hex colour string."""
    v = value.strip().lstrip("#")
    try:
        if len(v) == 6:
            r = int(v[0:2], 16)
            g = int(v[2:4], 16)
            b = int(v[4:6], 16)
            return (r, g, b)
        if len(v) == 3:
            r = int(v[0]*2, 16)
            g = int(v[1]*2, 16)
            b = int(v[2]*2, 16)
            return (r, g, b)
    except ValueError:
        pass
    return fallback


# ── Widget ────────────────────────────────────────────────────────────────────

class RichLabel(Widget):
    """
    Single-line text widget with inline BBCode markup.

    Supported tags::

        [b]bold[/b]
        [i]italic[/i]
        [color=#rrggbb]coloured[/color]
        [size=24]big[/size]

    Tags may be nested. Unknown tags are rendered as literal text.
    For multi-line rich text, use multiple RichLabel instances or a
    future RichTextBlock widget.

    Args:
        rect:      Position and size.
        text:      Plain or marked-up text string.
        font_size: Base font size. Defaults to theme.
        colour:    Base text colour. Defaults to theme.
        align:     ``"left"``, ``"center"``, ``"right"``.
        font_name: SysFont hint string. Defaults to theme.
    """

    _UNSET = object()

    def __init__(
        self,
        rect:      pygame.Rect,
        text:      str    = "",
        font_size: object = _UNSET,
        colour:    object = _UNSET,
        align:     str    = "left",
        font_name: object = _UNSET,
    ) -> None:
        super().__init__(rect)
        theme = get_theme()

        self._text      = text
        self._base_size: int = (
            int(font_size) if font_size is not self._UNSET          # type: ignore
            else theme.typography.md
        )
        self._base_colour: tuple[int,int,int] = (
            colour if colour is not self._UNSET                     # type: ignore
            else theme.colours.text
        )
        self._font_name: str = (
            font_name if font_name is not self._UNSET               # type: ignore
            else theme.typography.family
        )
        self._align  = align
        self._dirty  = True
        self._cache: list[tuple[pygame.Surface, int]] = []   # (surf, x_offset)
        self._font_cache: dict[tuple, pygame.font.Font] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text  = value
            self._dirty = True

    @property
    def align(self) -> str:
        return self._align

    @align.setter
    def align(self, value: str) -> None:
        if value != self._align:
            self._align = value
            self._dirty = True

    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect   = rect
        self._dirty = True

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        if self._dirty:
            self._rebuild()
        if not self._cache:
            return

        total_w = sum(s.get_width() for s, _ in self._cache)
        if self._align == "right":
            x = self.rect.right - total_w
        elif self._align == "center":
            x = self.rect.centerx - total_w // 2
        else:
            x = self.rect.x

        for surf, _ in self._cache:
            y = self.rect.centery - surf.get_height() // 2
            surface.blit(surf, (x, y))
            x += surf.get_width()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        self._cache = []
        spans = parse_markup(self._text, self._base_colour, self._base_size)
        for span in spans:
            if not span.text:
                continue
            font = self._get_font(span.font_size or self._base_size,
                                  span.bold, span.italic)
            colour = span.colour or self._base_colour
            surf   = font.render(span.text, True, colour)
            self._cache.append((surf, 0))
        self._dirty = False

    def _get_font(self, size: int, bold: bool, italic: bool) -> pygame.font.Font:
        key = (size, bold, italic)
        if key not in self._font_cache:
            self._font_cache[key] = pygame.font.SysFont(
                self._font_name, size, bold=bold, italic=italic
            )
        return self._font_cache[key]
