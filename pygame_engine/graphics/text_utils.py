"""
Text layout utilities for pygame_engine.

Provides three standalone functions for fitting text into constrained
widths. These are pure functions — no widgets, no theme access, no state.
Any widget or scene that renders text can import and call them directly.

Usage::

    from pygame_engine.graphics.text_utils import truncate, wrap_text, wrap_and_truncate

    font = pygame.font.SysFont(None, 22)

    # Fit a single line into 300 px, trailing ellipsis if needed
    line = truncate(font, hero.name, max_width=300)

    # Break a long string into multiple lines that each fit 400 px
    lines = wrap_text(font, description, max_width=400)

    # Wrap but cap at 3 lines; last line gets ellipsis if content is cut
    lines = wrap_and_truncate(font, long_text, max_width=400, max_lines=3)

Design decisions
----------------
- All three functions are **pure** — they never mutate their arguments and
  have no side effects.
- ``truncate`` guarantees the returned string renders within ``max_width``
  pixels using the supplied font. The ellipsis character itself is measured
  so the result is always accurate, even with proportional fonts.
- ``wrap_text`` splits on whitespace and honours explicit newlines
  (``\\n``) as paragraph breaks, matching the behaviour of
  ``TextBlock._wrap_text``.
- ``wrap_and_truncate`` combines both: wraps to ``max_lines``, then
  appends an ellipsis to the final line if content was cut. This is the
  function to use for fixed-height containers such as list rows, cards,
  and tooltips.
"""

from __future__ import annotations

import pygame


# ── Public API ────────────────────────────────────────────────────────────────

def truncate(
    font:      pygame.font.Font,
    text:      str,
    max_width: int,
    ellipsis:  str = "…",
) -> str:
    """
    Truncate *text* so that it fits within *max_width* pixels.

    If the text already fits it is returned unchanged. If it is too long,
    characters are removed from the right and the *ellipsis* string is
    appended until the result fits.

    Args:
        font:      Font used to measure text width.
        text:      Source string.
        max_width: Maximum allowed width in pixels.
        ellipsis:  Suffix appended when truncation occurs. Default ``"…"``.

    Returns:
        The original string if it fits, otherwise a truncated string ending
        with *ellipsis* that fits within *max_width* pixels.

    Examples::

        truncate(font, "Hero Management", 200)   # may return "Hero Mana…"
        truncate(font, "Short", 200)             # returns "Short" unchanged
        truncate(font, "Text", 0)                # returns ellipsis or ""
    """
    if max_width <= 0:
        return ellipsis if font.size(ellipsis)[0] <= 0 else ""

    if font.size(text)[0] <= max_width:
        return text

    ellipsis_w = font.size(ellipsis)[0]

    # Binary-search for the longest prefix that fits.
    # Falls back to linear scan for very short strings.
    lo, hi = 0, len(text)
    while lo < hi:
        mid  = (lo + hi + 1) // 2
        test = text[:mid]
        if font.size(test)[0] + ellipsis_w <= max_width:
            lo = mid
        else:
            hi = mid - 1

    return text[:lo] + ellipsis


def wrap_text(
    font:      pygame.font.Font,
    text:      str,
    max_width: int,
) -> list[str]:
    """
    Word-wrap *text* into a list of lines, each fitting *max_width* pixels.

    Explicit newlines (``\\n``) are treated as paragraph breaks and always
    produce a new line even when the current line still has space.

    Empty input returns ``[""]``. Lines containing a single word that is
    wider than *max_width* are returned as-is (no character-level breaking).

    Args:
        font:      Font used to measure line widths.
        text:      Source string. May contain ``\\n`` paragraph breaks.
        max_width: Maximum line width in pixels.

    Returns:
        List of strings, each of which renders within *max_width* pixels
        (except for single words wider than *max_width*).

    Examples::

        wrap_text(font, "Hello world", 60)  # may return ["Hello", "world"]
        wrap_text(font, "A\\nB", 400)        # returns ["A", "B"]
        wrap_text(font, "", 400)             # returns [""]
    """
    if not text:
        return [""]

    lines:      list[str] = []
    paragraphs: list[str] = text.splitlines() or [text]

    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)

    return lines


def wrap_and_truncate(
    font:      pygame.font.Font,
    text:      str,
    max_width: int,
    max_lines: int,
    ellipsis:  str = "…",
) -> list[str]:
    """
    Wrap *text* into at most *max_lines* lines, truncating the last line
    with *ellipsis* if content is cut.

    This is the preferred function for fixed-height containers: list rows,
    tooltip bodies, card descriptions, and anywhere the number of visible
    lines is predetermined.

    Args:
        font:      Font used to measure widths.
        text:      Source string. May contain ``\\n`` paragraph breaks.
        max_width: Maximum line width in pixels.
        max_lines: Maximum number of lines to return (must be ≥ 1).
        ellipsis:  Suffix used when the last line is truncated. Default ``"…"``.

    Returns:
        List of at most *max_lines* strings. If the wrapped text required
        more lines, the final line ends with *ellipsis*.

    Examples::

        wrap_and_truncate(font, long_text, 400, 3)
        # → ["First line", "Second line", "Third lin…"]

        wrap_and_truncate(font, "Short", 400, 3)
        # → ["Short"]   (fewer than max_lines, no ellipsis)
    """
    if max_lines < 1:
        raise ValueError(f"max_lines must be at least 1, got {max_lines!r}")

    all_lines = wrap_text(font, text, max_width)

    if len(all_lines) <= max_lines:
        return all_lines

    # More lines than allowed — take the first max_lines and truncate the last.
    result     = all_lines[:max_lines]
    last_line  = result[-1]

    # We need to fit the last line + ellipsis within max_width.
    # If the next line exists, append its first word to give the truncation
    # some context, then truncate.
    if max_lines < len(all_lines):
        next_word  = all_lines[max_lines].split()[0] if all_lines[max_lines].split() else ""
        candidate  = f"{last_line} {next_word}" if next_word else last_line
    else:
        candidate  = last_line

    result[-1] = truncate(font, candidate, max_width, ellipsis)
    return result
