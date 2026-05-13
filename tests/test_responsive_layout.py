"""
tests/test_responsive_layout.py

Tests for FlexRow, FlexColumn, and AnchorLayout.
"""

import pygame
import pytest

from pygame_engine.layout import AnchorLayout, FlexColumn, FlexRow


# ── Stub widget ───────────────────────────────────────────────────────────────

class RectWidget:
    """Minimal widget stub — just tracks set_rect calls."""
    def __init__(self, w=100, h=40):
        self.rect = pygame.Rect(0, 0, w, h)
    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect = pygame.Rect(rect)


BOUNDS = pygame.Rect(0, 0, 600, 400)


# ══════════════════════════════════════════════════════════════════════════════
# FlexRow
# ══════════════════════════════════════════════════════════════════════════════

def test_flexrow_equal_weights_split_width() -> None:
    a, b, c = RectWidget(), RectWidget(), RectWidget()
    row = FlexRow()
    row.add(a, weight=1).add(b, weight=1).add(c, weight=1)
    row.layout(BOUNDS)
    assert a.rect.width == b.rect.width == c.rect.width == 200


def test_flexrow_weighted_proportional() -> None:
    a, b = RectWidget(), RectWidget()
    row = FlexRow()
    row.add(a, weight=1).add(b, weight=3)
    row.layout(BOUNDS)
    assert b.rect.width == 3 * a.rect.width


def test_flexrow_fixed_item_exact_width() -> None:
    a, b = RectWidget(), RectWidget()
    row = FlexRow()
    row.add(a, fixed=100).add(b, weight=1)
    row.layout(BOUNDS)
    assert a.rect.width == 100
    assert b.rect.width == 500   # remaining space


def test_flexrow_spacing_reduces_free_space() -> None:
    a, b = RectWidget(), RectWidget()
    row = FlexRow(spacing=20)
    row.add(a, weight=1).add(b, weight=1)
    row.layout(BOUNDS)
    # 600 - 20 gap = 580 / 2 = 290
    assert a.rect.width == 290
    assert b.rect.width == 290


def test_flexrow_items_left_to_right() -> None:
    a, b, c = RectWidget(), RectWidget(), RectWidget()
    row = FlexRow()
    row.add(a, weight=1).add(b, weight=1).add(c, weight=1)
    row.layout(BOUNDS)
    assert a.rect.x < b.rect.x < c.rect.x


def test_flexrow_items_fill_height() -> None:
    a = RectWidget()
    row = FlexRow()
    row.add(a, weight=1)
    row.layout(BOUNDS)
    assert a.rect.height == BOUNDS.height


def test_flexrow_item_height_override() -> None:
    a = RectWidget()
    row = FlexRow(item_height=40)
    row.add(a, weight=1)
    row.layout(BOUNDS)
    assert a.rect.height == 40


def test_flexrow_min_size_enforced() -> None:
    a, b = RectWidget(), RectWidget()
    row = FlexRow()
    row.add(a, weight=1, min_size=400).add(b, weight=1)
    row.layout(pygame.Rect(0, 0, 200, 100))
    assert a.rect.width >= 400


def test_flexrow_max_size_enforced() -> None:
    a = RectWidget()
    row = FlexRow()
    row.add(a, weight=1, max_size=50)
    row.layout(BOUNDS)
    assert a.rect.width <= 50


def test_flexrow_padding_insets_bounds() -> None:
    a = RectWidget()
    row = FlexRow(padding=20)
    row.add(a, weight=1)
    row.layout(BOUNDS)
    assert a.rect.x >= 20
    assert a.rect.right <= BOUNDS.right - 20


def test_flexrow_relayout_uses_last_bounds() -> None:
    a = RectWidget()
    row = FlexRow()
    row.add(a, weight=1)
    row.layout(pygame.Rect(0, 0, 200, 100))
    row.relayout()
    assert a.rect.width == 200


def test_flexrow_relayout_noop_before_layout() -> None:
    a = RectWidget()
    row = FlexRow()
    row.add(a, weight=1)
    result = row.relayout()   # never laid out
    assert result == []


def test_flexrow_item_count() -> None:
    row = FlexRow()
    row.add(RectWidget(), weight=1)
    row.add(RectWidget(), weight=1)
    assert row.item_count == 2


def test_flexrow_clear() -> None:
    row = FlexRow()
    row.add(RectWidget(), weight=1)
    row.clear()
    assert row.item_count == 0


def test_flexrow_returns_rects() -> None:
    a, b = RectWidget(), RectWidget()
    row = FlexRow()
    row.add(a, weight=1).add(b, weight=1)
    rects = row.layout(BOUNDS)
    assert len(rects) == 2
    assert all(isinstance(r, pygame.Rect) for r in rects)


# ══════════════════════════════════════════════════════════════════════════════
# FlexColumn
# ══════════════════════════════════════════════════════════════════════════════

def test_flexcolumn_equal_weights_split_height() -> None:
    a, b = RectWidget(), RectWidget()
    col = FlexColumn()
    col.add(a, weight=1).add(b, weight=1)
    col.layout(BOUNDS)
    assert a.rect.height == b.rect.height == 200


def test_flexcolumn_fixed_and_weighted() -> None:
    header, content, footer = RectWidget(), RectWidget(), RectWidget()
    col = FlexColumn(spacing=0)
    col.add(header,  fixed=60)
    col.add(content, weight=1)
    col.add(footer,  fixed=40)
    col.layout(BOUNDS)
    assert header.rect.height  == 60
    assert footer.rect.height  == 40
    assert content.rect.height == 300   # 400 - 60 - 40


def test_flexcolumn_items_top_to_bottom() -> None:
    a, b, c = RectWidget(), RectWidget(), RectWidget()
    col = FlexColumn()
    col.add(a, weight=1).add(b, weight=1).add(c, weight=1)
    col.layout(BOUNDS)
    assert a.rect.y < b.rect.y < c.rect.y


def test_flexcolumn_items_fill_width() -> None:
    a = RectWidget()
    col = FlexColumn()
    col.add(a, weight=1)
    col.layout(BOUNDS)
    assert a.rect.width == BOUNDS.width


def test_flexcolumn_spacing() -> None:
    a, b = RectWidget(), RectWidget()
    col = FlexColumn(spacing=10)
    col.add(a, weight=1).add(b, weight=1)
    col.layout(BOUNDS)
    assert a.rect.height == b.rect.height == 195   # (400-10)/2


def test_flexcolumn_relayout() -> None:
    a = RectWidget()
    col = FlexColumn()
    col.add(a, weight=1)
    col.layout(pygame.Rect(0, 0, 100, 300))
    col.relayout()
    assert a.rect.height == 300


def test_flexcolumn_returns_rects() -> None:
    a = RectWidget()
    col = FlexColumn()
    col.add(a, weight=1)
    rects = col.layout(BOUNDS)
    assert len(rects) == 1


# ══════════════════════════════════════════════════════════════════════════════
# AnchorLayout
# ══════════════════════════════════════════════════════════════════════════════

def test_anchorlayout_center() -> None:
    w = RectWidget(100, 40)
    layout = AnchorLayout()
    layout.add(w, "center", size=(100, 40))
    layout.apply(BOUNDS)
    assert w.rect.centerx == BOUNDS.centerx
    assert w.rect.centery == BOUNDS.centery


def test_anchorlayout_top_left() -> None:
    w = RectWidget(100, 40)
    layout = AnchorLayout()
    layout.add(w, "top_left", size=(100, 40), margin=0)
    layout.apply(BOUNDS)
    assert w.rect.topleft == BOUNDS.topleft


def test_anchorlayout_top_left_with_margin() -> None:
    w = RectWidget(100, 40)
    layout = AnchorLayout()
    layout.add(w, "top_left", size=(100, 40), margin=16)
    layout.apply(BOUNDS)
    assert w.rect.x == 16
    assert w.rect.y == 16


def test_anchorlayout_bottom_right() -> None:
    w = RectWidget(100, 40)
    layout = AnchorLayout()
    layout.add(w, "bottom_right", size=(100, 40), margin=0)
    layout.apply(BOUNDS)
    assert w.rect.right  == BOUNDS.right
    assert w.rect.bottom == BOUNDS.bottom


def test_anchorlayout_multiple_widgets() -> None:
    a = RectWidget(80, 32)
    b = RectWidget(80, 32)
    layout = AnchorLayout()
    layout.add(a, "top_left",     size=(80, 32))
    layout.add(b, "bottom_right", size=(80, 32))
    layout.apply(BOUNDS)
    assert a.rect.topleft    == (0, 0)
    assert b.rect.bottomright == (BOUNDS.right, BOUNDS.bottom)


def test_anchorlayout_uses_widget_rect_when_size_none() -> None:
    w = RectWidget(100, 40)   # w.rect is (0,0,100,40)
    layout = AnchorLayout()
    layout.add(w, "center", size=None)
    layout.apply(BOUNDS)
    assert w.rect.width  == 100
    assert w.rect.height == 40
    assert w.rect.centerx == BOUNDS.centerx


def test_anchorlayout_offset_applied() -> None:
    w = RectWidget(100, 40)
    layout = AnchorLayout()
    layout.add(w, "center", size=(100, 40), offset=(10, -5))
    layout.apply(BOUNDS)
    assert w.rect.centerx == BOUNDS.centerx + 10
    assert w.rect.centery == BOUNDS.centery - 5


def test_anchorlayout_invalid_point_raises() -> None:
    layout = AnchorLayout()
    with pytest.raises(ValueError):
        layout.add(RectWidget(), "middle_nowhere", size=(10, 10))


def test_anchorlayout_reapply_updates_positions() -> None:
    w = RectWidget(100, 40)
    layout = AnchorLayout()
    layout.add(w, "center", size=(100, 40))
    layout.apply(pygame.Rect(0, 0, 400, 300))
    assert w.rect.centerx == 200

    layout.apply(pygame.Rect(0, 0, 800, 600))
    assert w.rect.centerx == 400   # recentred in new bounds


def test_anchorlayout_reapply_uses_last_bounds() -> None:
    w = RectWidget(100, 40)
    layout = AnchorLayout()
    layout.add(w, "center", size=(100, 40))
    layout.apply(pygame.Rect(0, 0, 400, 300))
    layout.reapply()
    assert w.rect.centerx == 200


def test_anchorlayout_reapply_noop_before_apply() -> None:
    layout = AnchorLayout()
    layout.add(RectWidget(), "center", size=(10, 10))
    result = layout.reapply()
    assert result == []


def test_anchorlayout_remove_widget() -> None:
    w = RectWidget()
    layout = AnchorLayout()
    layout.add(w, "center", size=(10, 10))
    assert layout.rule_count == 1
    assert layout.remove(w) is True
    assert layout.rule_count == 0


def test_anchorlayout_remove_absent_returns_false() -> None:
    layout = AnchorLayout()
    assert layout.remove(RectWidget()) is False


def test_anchorlayout_clear() -> None:
    layout = AnchorLayout()
    layout.add(RectWidget(), "center", size=(10, 10))
    layout.add(RectWidget(), "top_left", size=(10, 10))
    layout.clear()
    assert layout.rule_count == 0


def test_anchorlayout_returns_rects() -> None:
    w = RectWidget(100, 40)
    layout = AnchorLayout()
    layout.add(w, "center", size=(100, 40))
    rects = layout.apply(BOUNDS)
    assert len(rects) == 1
    assert isinstance(rects[0], pygame.Rect)


def test_anchorlayout_chaining() -> None:
    layout = AnchorLayout()
    result = (layout
              .add(RectWidget(), "top_left",     size=(80, 32))
              .add(RectWidget(), "bottom_right", size=(80, 32)))
    assert result is layout
    assert layout.rule_count == 2


def test_anchorlayout_repr() -> None:
    layout = AnchorLayout()
    layout.add(RectWidget(), "center", size=(10, 10))
    assert "AnchorLayout" in repr(layout)
    assert "1" in repr(layout)


# ── Integration: on_resize pattern ───────────────────────────────────────────

def test_on_resize_pattern_with_anchor_layout() -> None:
    """Simulates the typical on_resize usage pattern."""
    hud = RectWidget(400, 32)
    btn = RectWidget(120, 40)

    layout = AnchorLayout()
    layout.add(hud, "top",    size=(400, 32), margin=8)
    layout.add(btn, "bottom_right", size=(120, 40), margin=16)

    # Initial layout at 1280x720
    layout.apply(pygame.Rect(0, 0, 1280, 720))
    assert hud.rect.centerx == 640
    assert btn.rect.right   == 1280 - 16

    # Resize to 1920x1080
    layout.apply(pygame.Rect(0, 0, 1920, 1080))
    assert hud.rect.centerx == 960
    assert btn.rect.right   == 1920 - 16


def test_on_resize_pattern_with_flex_column() -> None:
    """Simulates header+content+footer layout rebuilding on resize."""
    header  = RectWidget()
    content = RectWidget()
    footer  = RectWidget()

    col = FlexColumn(spacing=4)
    col.add(header,  fixed=60)
    col.add(content, weight=1)
    col.add(footer,  fixed=40)

    col.layout(pygame.Rect(0, 0, 800, 600))
    assert header.rect.height  == 60
    assert footer.rect.height  == 40
    assert content.rect.height == 600 - 60 - 40 - 8   # 2 gaps of 4

    col.layout(pygame.Rect(0, 0, 800, 900))
    assert header.rect.height  == 60
    assert footer.rect.height  == 40
    assert content.rect.height == 900 - 60 - 40 - 8
