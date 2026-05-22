import pygame
import pytest

from pygame_engine.ui.text.rich_label import RichLabel, _parse_hex, parse_markup


# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    """Return a default RenderContext for render() calls in tests."""
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

RECT = pygame.Rect(0, 0, 400, 32)
BASE_COLOUR = (200, 200, 200)
BASE_SIZE   = 18


# ── parse_markup ──────────────────────────────────────────────────────────────

def test_plain_text_single_span():
    spans = parse_markup("hello", BASE_COLOUR, BASE_SIZE)
    assert len(spans) == 1
    assert spans[0].text == "hello"
    assert spans[0].bold   is False
    assert spans[0].italic is False
    assert spans[0].colour == BASE_COLOUR


def test_bold_tag():
    spans = parse_markup("[b]bold[/b]", BASE_COLOUR, BASE_SIZE)
    assert any(s.bold and s.text == "bold" for s in spans)


def test_italic_tag():
    spans = parse_markup("[i]italic[/i]", BASE_COLOUR, BASE_SIZE)
    assert any(s.italic and s.text == "italic" for s in spans)


def test_color_tag_hex():
    spans = parse_markup("[color=#ff0000]red[/color]", BASE_COLOUR, BASE_SIZE)
    coloured = [s for s in spans if s.text == "red"]
    assert coloured and coloured[0].colour == (255, 0, 0)


def test_color_tag_short_hex():
    spans = parse_markup("[color=#f00]red[/color]", BASE_COLOUR, BASE_SIZE)
    coloured = [s for s in spans if s.text == "red"]
    assert coloured and coloured[0].colour == (255, 0, 0)


def test_size_tag():
    spans = parse_markup("[size=24]big[/size]", BASE_COLOUR, BASE_SIZE)
    big = [s for s in spans if s.text == "big"]
    assert big and big[0].font_size == 24


def test_nested_bold_color():
    spans = parse_markup("[b][color=#00ff00]green bold[/color][/b]",
                          BASE_COLOUR, BASE_SIZE)
    styled = [s for s in spans if s.text == "green bold"]
    assert styled
    assert styled[0].bold is True
    assert styled[0].colour == (0, 255, 0)


def test_text_before_and_after_tag():
    spans = parse_markup("before[b]BOLD[/b]after", BASE_COLOUR, BASE_SIZE)
    texts = [s.text for s in spans]
    assert "before" in texts
    assert "BOLD"   in texts
    assert "after"  in texts


def test_colour_reverts_after_closing_tag():
    spans = parse_markup("[color=#ff0000]red[/color]normal",
                          BASE_COLOUR, BASE_SIZE)
    normal = [s for s in spans if s.text == "normal"]
    assert normal and normal[0].colour == BASE_COLOUR


def test_unknown_tag_rendered_as_literal():
    spans = parse_markup("[unknown]text[/unknown]", BASE_COLOUR, BASE_SIZE)
    all_text = "".join(s.text for s in spans)
    assert "text" in all_text


def test_empty_string():
    assert parse_markup("", BASE_COLOUR, BASE_SIZE) == []


def test_only_tags_no_text():
    spans = parse_markup("[b][/b]", BASE_COLOUR, BASE_SIZE)
    # No text content between tags — spans list is empty or has no non-empty text
    assert all(s.text == "" or not s.text for s in spans)


def test_bold_italic_combined():
    spans = parse_markup("[b][i]bi[/i][/b]", BASE_COLOUR, BASE_SIZE)
    bi = [s for s in spans if s.text == "bi"]
    assert bi and bi[0].bold and bi[0].italic


# ── _parse_hex ────────────────────────────────────────────────────────────────

def test_parse_hex_full():
    assert _parse_hex("#1a2b3c", (0,0,0)) == (0x1a, 0x2b, 0x3c)


def test_parse_hex_no_hash():
    assert _parse_hex("ff8800", (0,0,0)) == (255, 136, 0)


def test_parse_hex_short():
    assert _parse_hex("#f80", (0,0,0)) == (255, 136, 0)


def test_parse_hex_invalid_returns_fallback():
    assert _parse_hex("zzzzzz", (1, 2, 3)) == (1, 2, 3)


# ── RichLabel widget ──────────────────────────────────────────────────────────

def test_rich_label_construction():
    lbl = RichLabel(RECT, "hello")
    assert lbl.text == "hello"


def test_rich_label_text_setter_marks_dirty():
    lbl = RichLabel(RECT, "a")
    lbl._dirty = False
    lbl.text = "b"
    assert lbl._dirty is True


def test_rich_label_same_text_no_dirty():
    lbl = RichLabel(RECT, "same")
    lbl._dirty = False
    lbl.text = "same"
    assert lbl._dirty is False


def test_rich_label_align_setter():
    lbl = RichLabel(RECT, "x", align="left")
    lbl.align = "right"
    assert lbl.align == "right"
    assert lbl._dirty is True


def test_rich_label_render_plain_text(display_surface):
    RichLabel(RECT, "Hello world").render(display_surface, _ctx())


def test_rich_label_render_bold(display_surface):
    RichLabel(RECT, "[b]bold[/b]").render(display_surface, _ctx())


def test_rich_label_render_colored(display_surface):
    RichLabel(RECT, "[color=#ff4444]red[/color] and normal").render(display_surface, _ctx())


def test_rich_label_render_mixed(display_surface):
    RichLabel(RECT,
              "[b]Bold[/b] [i]italic[/i] [size=14]small[/size]"
              ).render(display_surface, _ctx())


def test_rich_label_invisible_skips_render(display_surface):
    lbl = RichLabel(RECT, "hidden")
    lbl.visible = False
    lbl.render(display_surface, _ctx())   # should not raise


def test_rich_label_empty_text(display_surface):
    RichLabel(RECT, "").render(display_surface, _ctx())


def test_rich_label_set_rect_marks_dirty():
    lbl = RichLabel(RECT, "x")
    lbl._dirty = False
    lbl.set_rect(pygame.Rect(10, 10, 200, 32))
    assert lbl._dirty is True


def test_rich_label_cache_built_on_first_render(display_surface):
    lbl = RichLabel(RECT, "[b]test[/b]")
    assert lbl._dirty is True
    lbl.render(display_surface, _ctx())
    assert lbl._dirty is False
    assert len(lbl._cache) > 0


def test_rich_label_font_cache_reused():
    lbl = RichLabel(RECT, "[b]a[/b][b]b[/b]")
    lbl._rebuild()
    # Both spans are bold same size — should share font cache entry
    assert len(lbl._font_cache) == 1


def test_rich_label_align_center(display_surface):
    RichLabel(RECT, "centered", align="center").render(display_surface, _ctx())


def test_rich_label_align_right(display_surface):
    RichLabel(RECT, "right", align="right").render(display_surface, _ctx())