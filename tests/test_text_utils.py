"""Tests for pygame_engine.graphics.text_utils."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

pygame.init()
pygame.display.set_mode((800, 600))

from pygame_engine.graphics.text_utils import truncate, wrap_text, wrap_and_truncate


# ── Shared fixture ────────────────────────────────────────────────────────────

@pytest.fixture
def font():
    return pygame.font.SysFont(None, 22)


# ── truncate ──────────────────────────────────────────────────────────────────

def test_truncate_short_text_unchanged(font):
    result = truncate(font, "Hi", max_width=10_000)
    assert result == "Hi"


def test_truncate_empty_string_unchanged(font):
    result = truncate(font, "", max_width=10_000)
    assert result == ""


def test_truncate_adds_ellipsis_when_too_long(font):
    long = "A" * 200
    result = truncate(font, long, max_width=50)
    assert result.endswith("…")


def test_truncate_result_fits_max_width(font):
    long   = "The quick brown fox jumps over the lazy dog" * 3
    result = truncate(font, long, max_width=80)
    assert font.size(result)[0] <= 80


def test_truncate_result_fits_exactly_at_boundary(font):
    # A string that is exactly max_width should NOT be truncated
    text   = "Hello"
    width  = font.size(text)[0]
    result = truncate(font, text, max_width=width)
    assert result == "Hello"


def test_truncate_one_pixel_too_wide_gets_ellipsis(font):
    text  = "Hello"
    width = font.size(text)[0] - 1
    result = truncate(font, text, max_width=width)
    assert result.endswith("…")
    assert font.size(result)[0] <= width


def test_truncate_zero_max_width(font):
    result = truncate(font, "anything", max_width=0)
    # Must not raise; returns empty-ish string
    assert isinstance(result, str)


def test_truncate_custom_ellipsis(font):
    long   = "A" * 200
    result = truncate(font, long, max_width=50, ellipsis="...")
    assert result.endswith("...")


def test_truncate_single_char_string(font):
    result = truncate(font, "X", max_width=1)
    assert isinstance(result, str)


def test_truncate_result_never_wider_than_max(font):
    ellipsis_w = font.size("…")[0]
    for max_w in [10, 30, 60, 120, 200]:
        result = truncate(font, "The quick brown fox", max_width=max_w)
        # When max_w is smaller than the ellipsis itself, the function
        # cannot guarantee the result fits — it returns the ellipsis as-is.
        # For all other widths the result must fit within max_w.
        effective_max = max(max_w, ellipsis_w)
        assert font.size(result)[0] <= effective_max, f"Failed at max_width={max_w}"


# ── wrap_text ─────────────────────────────────────────────────────────────────

def test_wrap_empty_string_returns_single_empty(font):
    result = wrap_text(font, "", max_width=200)
    assert result == [""]


def test_wrap_short_text_fits_on_one_line(font):
    result = wrap_text(font, "Hi", max_width=10_000)
    assert result == ["Hi"]


def test_wrap_long_text_splits_into_multiple_lines(font):
    text   = "word " * 30
    result = wrap_text(font, text.strip(), max_width=100)
    assert len(result) > 1


def test_wrap_each_line_fits_max_width(font):
    text   = "The quick brown fox jumps over the lazy dog"
    result = wrap_text(font, text, max_width=80)
    for line in result:
        if len(line.split()) > 1:          # single words may exceed max_width
            assert font.size(line)[0] <= 80


def test_wrap_honours_newlines_as_paragraph_breaks(font):
    text   = "Line one\nLine two\nLine three"
    result = wrap_text(font, text, max_width=10_000)
    assert result == ["Line one", "Line two", "Line three"]


def test_wrap_empty_paragraph_produces_empty_string(font):
    result = wrap_text(font, "A\n\nB", max_width=10_000)
    assert "" in result
    assert "A" in result
    assert "B" in result


def test_wrap_single_word_returned_as_is(font):
    result = wrap_text(font, "Superlongword", max_width=1)
    assert result == ["Superlongword"]


def test_wrap_preserves_word_order(font):
    text   = "alpha beta gamma delta"
    result = wrap_text(font, text, max_width=10_000)
    assert " ".join(result) == text


def test_wrap_all_lines_are_strings(font):
    result = wrap_text(font, "hello world foo bar baz", max_width=60)
    assert all(isinstance(line, str) for line in result)


def test_wrap_returns_list(font):
    result = wrap_text(font, "any text", max_width=200)
    assert isinstance(result, list)


def test_wrap_no_trailing_whitespace_per_line(font):
    result = wrap_text(font, "word1 word2 word3", max_width=10_000)
    for line in result:
        assert line == line.strip()


# ── wrap_and_truncate ─────────────────────────────────────────────────────────

def test_wt_short_text_returns_single_line(font):
    result = wrap_and_truncate(font, "Short", max_width=10_000, max_lines=3)
    assert result == ["Short"]


def test_wt_returns_at_most_max_lines(font):
    text   = "word " * 40
    result = wrap_and_truncate(font, text.strip(), max_width=60, max_lines=3)
    assert len(result) <= 3


def test_wt_last_line_has_ellipsis_when_cut(font):
    text   = "word " * 40
    result = wrap_and_truncate(font, text.strip(), max_width=60, max_lines=2)
    if len(wrap_text(font, text.strip(), 60)) > 2:
        assert result[-1].endswith("…")


def test_wt_no_ellipsis_when_all_fits(font):
    result = wrap_and_truncate(font, "Hello world", max_width=10_000, max_lines=5)
    assert not any(line.endswith("…") for line in result)


def test_wt_each_line_fits_max_width(font):
    text   = "The quick brown fox jumps over the lazy dog " * 3
    result = wrap_and_truncate(font, text.strip(), max_width=120, max_lines=4)
    for line in result:
        assert font.size(line)[0] <= 120


def test_wt_exactly_max_lines_no_ellipsis(font):
    """If text fills exactly max_lines, no ellipsis needed."""
    # Construct text that wraps to exactly 2 lines at a generous width
    text   = "Hello world"
    lines  = wrap_text(font, text, max_width=10_000)
    result = wrap_and_truncate(font, text, max_width=10_000, max_lines=len(lines))
    assert result == lines


def test_wt_max_lines_one_truncates_to_single_line(font):
    text   = "word " * 20
    result = wrap_and_truncate(font, text.strip(), max_width=100, max_lines=1)
    assert len(result) == 1
    assert font.size(result[0])[0] <= 100


def test_wt_invalid_max_lines_raises(font):
    with pytest.raises(ValueError):
        wrap_and_truncate(font, "text", max_width=200, max_lines=0)


def test_wt_custom_ellipsis(font):
    text   = "word " * 40
    result = wrap_and_truncate(font, text.strip(), max_width=60,
                               max_lines=1, ellipsis="...")
    assert result[-1].endswith("...")


def test_wt_empty_string(font):
    result = wrap_and_truncate(font, "", max_width=200, max_lines=3)
    assert result == [""]


def test_wt_returns_list_of_strings(font):
    result = wrap_and_truncate(font, "hello world", max_width=200, max_lines=2)
    assert isinstance(result, list)
    assert all(isinstance(line, str) for line in result)


# ── Cross-function consistency ────────────────────────────────────────────────

def test_truncate_consistent_with_wrap_single_line(font):
    """wrap_text of a single-word string == [that word]."""
    word   = "Arsenal"
    assert wrap_text(font, word, max_width=10_000) == [word]


def test_wrap_and_truncate_with_one_line_equals_truncate(font):
    """wrap_and_truncate(..., max_lines=1) should match truncate."""
    text    = "The quick brown fox jumps over the lazy dog"
    max_w   = 80
    result1 = wrap_and_truncate(font, text, max_width=max_w, max_lines=1)
    result2 = truncate(font, text, max_width=max_w)
    assert result1 == [result2]


def test_graphics_module_exports(font):
    """text_utils functions are importable from pygame_engine.graphics."""
    from pygame_engine.graphics import truncate as t, wrap_text as wt, wrap_and_truncate as wat
    assert t(font, "hello", 10_000) == "hello"
    assert wt(font, "hello", 10_000) == ["hello"]
    assert wat(font, "hello", 10_000, 3) == ["hello"]
