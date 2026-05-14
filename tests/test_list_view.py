"""Tests for ListView widget."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

pygame.init()
pygame.display.set_mode((800, 600))


from pygame_engine.ui.controls.list_view import ListView


def make_lv(**kwargs):
    defaults = dict(rect=pygame.Rect(0, 0, 300, 400), row_height=50, row_gap=4)
    defaults.update(kwargs)
    return ListView(**defaults)


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_state_empty():
    lv = make_lv()
    assert lv.selected_item is None
    assert lv._items == []


def test_set_items_stores_list():
    lv = make_lv()
    items = ["a", "b", "c"]
    lv.set_items(items)
    assert lv._items == items


def test_set_items_does_not_share_reference():
    lv = make_lv()
    items = ["a", "b"]
    lv.set_items(items)
    items.append("c")
    assert len(lv._items) == 2


def test_append_item():
    lv = make_lv()
    lv.set_items(["a"])
    lv.append_item("b")
    assert lv._items == ["a", "b"]


def test_clear_empties_list_and_selection():
    lv = make_lv()
    items = ["x", "y"]
    lv.set_items(items)
    lv.select("x")
    lv.clear()
    assert lv._items == []
    assert lv.selected_item is None


# ── Selection ─────────────────────────────────────────────────────────────────

def test_select_sets_selected_item():
    lv = make_lv()
    items = ["a", "b", "c"]
    lv.set_items(items)
    lv.select("b")
    assert lv.selected_item == "b"


def test_select_nonexistent_does_nothing():
    lv = make_lv()
    lv.set_items(["a"])
    lv.select("z")
    assert lv.selected_item is None


def test_deselect_clears_selection():
    lv = make_lv()
    lv.set_items(["a"])
    lv.select("a")
    lv.deselect()
    assert lv.selected_item is None


def test_on_select_callback_fires():
    called_with = []
    lv = make_lv(on_select=lambda item: called_with.append(item))
    lv.set_items(["x", "y"])
    lv.select("y")
    assert called_with == ["y"]


def test_on_select_callback_fires_once_per_select():
    called = []
    lv = make_lv(on_select=lambda i: called.append(i))
    lv.set_items(["a", "b", "c"])
    lv.select("a")
    lv.select("b")
    assert len(called) == 2


def test_set_items_preserves_selection_if_same_object():
    lv = make_lv()
    obj = object()
    lv.set_items([obj])
    lv.select(obj)
    lv.set_items([obj])  # same object, selection preserved
    assert lv.selected_item is obj


def test_set_items_clears_selection_for_gone_object():
    lv = make_lv()
    obj = object()
    lv.set_items([obj])
    lv.select(obj)
    lv.set_items(["something_else"])
    assert lv.selected_item is None


# ── Scroll ────────────────────────────────────────────────────────────────────

def test_max_scroll_zero_when_few_items():
    lv = make_lv(row_height=50, row_gap=4, padding=8)
    lv.set_items(["a"])
    assert lv._max_scroll() == 0.0


def test_max_scroll_positive_when_many_items():
    lv = make_lv(rect=pygame.Rect(0, 0, 200, 100), row_height=50, row_gap=4)
    lv.set_items(["a", "b", "c", "d", "e"])
    assert lv._max_scroll() > 0


def test_scroll_to_top_resets():
    lv = make_lv(rect=pygame.Rect(0, 0, 200, 100), row_height=50, row_gap=4)
    lv.set_items(["a"] * 10)
    lv._scroll_y = 100.0
    lv.scroll_to_top()
    assert lv._scroll_y == 0.0


def test_scroll_to_bottom_goes_to_max():
    lv = make_lv(rect=pygame.Rect(0, 0, 200, 100), row_height=50, row_gap=4)
    lv.set_items(["a"] * 10)
    lv.scroll_to_bottom()
    assert lv._scroll_y == lv._max_scroll()


def test_set_items_clamps_scroll():
    lv = make_lv(rect=pygame.Rect(0, 0, 200, 100), row_height=50, row_gap=4)
    lv.set_items(["a"] * 10)
    lv._scroll_y = 999.0
    lv.set_items(["a"] * 3)
    assert lv._scroll_y <= lv._max_scroll()


# ── Keyboard navigation ───────────────────────────────────────────────────────

def _make_event(type_, **kwargs):
    return pygame.event.Event(type_, **kwargs)


def test_keyboard_down_selects_first_when_nothing_selected():
    lv = make_lv()
    lv.set_items(["a", "b", "c"])
    lv.focused = True
    ev = _make_event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0, unicode="")
    lv.handle_event(ev)
    assert lv.selected_item == "a"


def test_keyboard_down_moves_to_next():
    lv = make_lv()
    lv.set_items(["a", "b", "c"])
    lv.focused = True
    lv.select("a")
    ev = _make_event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0, unicode="")
    lv.handle_event(ev)
    assert lv.selected_item == "b"


def test_keyboard_up_moves_to_previous():
    lv = make_lv()
    lv.set_items(["a", "b", "c"])
    lv.focused = True
    lv.select("c")
    ev = _make_event(pygame.KEYDOWN, key=pygame.K_UP, mod=0, unicode="")
    lv.handle_event(ev)
    assert lv.selected_item == "b"


def test_keyboard_down_does_not_go_past_last():
    lv = make_lv()
    lv.set_items(["a", "b"])
    lv.focused = True
    lv.select("b")
    ev = _make_event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0, unicode="")
    lv.handle_event(ev)
    assert lv.selected_item == "b"


def test_keyboard_up_does_not_go_past_first():
    lv = make_lv()
    lv.set_items(["a", "b"])
    lv.focused = True
    lv.select("a")
    ev = _make_event(pygame.KEYDOWN, key=pygame.K_UP, mod=0, unicode="")
    lv.handle_event(ev)
    assert lv.selected_item == "a"


# ── Row rect geometry ─────────────────────────────────────────────────────────

def test_row_rect_y_increases_per_row():
    lv = make_lv(row_height=50, row_gap=4, padding=8)
    lv.set_items(["a", "b", "c"])
    r0 = lv._row_rect(0)
    r1 = lv._row_rect(1)
    assert r1.y > r0.y


def test_row_rects_do_not_overlap():
    lv = make_lv(row_height=50, row_gap=4, padding=8)
    lv.set_items(["a", "b", "c"])
    for i in range(2):
        assert lv._row_rect(i).bottom <= lv._row_rect(i + 1).top


def test_row_rect_width_accounts_for_scrollbar():
    lv = make_lv(rect=pygame.Rect(0, 0, 300, 400), row_height=50,
                 row_gap=4, padding=8)
    lv.set_items(["a"])
    rr = lv._row_rect(0)
    assert rr.width == 300 - 8 * 2 - ListView.SCROLLBAR_W


# ── Visible / enabled guards ──────────────────────────────────────────────────

def test_invisible_lv_does_not_handle_events():
    lv = make_lv()
    lv.set_items(["a", "b"])
    lv.visible = False
    ev = _make_event(pygame.MOUSEWHEEL, x=0, y=-3, flipped=False, precise_x=0.0, precise_y=-3.0, touch=False)
    assert lv.handle_event(ev) is False


def test_disabled_lv_does_not_handle_events():
    lv = make_lv()
    lv.set_items(["a", "b"])
    lv.enabled = False
    lv.focused = True
    ev = _make_event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0, unicode="")
    assert lv.handle_event(ev) is False


# ── Render smoke test ─────────────────────────────────────────────────────────

def test_render_does_not_raise_empty():
    surf = pygame.Surface((400, 500))
    lv = make_lv()
    lv.render(surf)


def test_render_does_not_raise_with_items():
    surf = pygame.Surface((400, 500))
    lv = make_lv()
    lv.set_items(["item one", "item two", "item three"])
    lv.render(surf)


def test_render_skips_when_invisible():
    surf = pygame.Surface((400, 500))
    surf.fill((0, 0, 0))
    lv = make_lv()
    lv.set_items(["visible?"])
    lv.visible = False
    lv.render(surf)
    # Surface unchanged (still all black) — no assert beyond no crash


def test_render_uses_custom_renderer():
    rendered_items = []

    def custom_renderer(surface, item, rect, sel, hov):
        rendered_items.append(item)

    surf = pygame.Surface((400, 500))
    lv   = make_lv()
    lv.row_renderer = custom_renderer
    lv.set_items(["a", "b", "c"])
    lv.render(surf)
    assert set(rendered_items) == {"a", "b", "c"}
