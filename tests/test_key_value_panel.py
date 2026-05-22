import pygame
import pytest


# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    """Return a default RenderContext for render() calls in tests."""
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

pygame.init()
pygame.display.set_mode((800, 600))

from pygame_engine.ui.controls.key_value_panel import KeyValuePanel


def make_kvp(**kwargs):
    defaults = dict(rect=pygame.Rect(0, 0, 400, 300))
    defaults.update(kwargs)
    return KeyValuePanel(**defaults)


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_empty():
    kv = make_kvp()
    assert kv._rows == []


def test_rows_passed_at_construction():
    kv = make_kvp(rows=[("Name", "Kira"), ("Level", 5)])
    assert len(kv._rows) == 2


def test_values_converted_to_str():
    kv = make_kvp(rows=[("Level", 7), ("Power", 123.4)])
    assert kv._rows[0][1] == "7"
    assert kv._rows[1][1] == "123.4"


def test_title_stored():
    kv = make_kvp(title="Hero Details")
    assert kv.title == "Hero Details"


# ── set_rows ──────────────────────────────────────────────────────────────────

def test_set_rows_replaces():
    kv = make_kvp(rows=[("a", 1)])
    kv.set_rows([("b", 2), ("c", 3)])
    assert len(kv._rows) == 2
    assert kv._rows[0] == ("b", "2")


def test_set_rows_empty_clears():
    kv = make_kvp(rows=[("x", 1), ("y", 2)])
    kv.set_rows([])
    assert kv._rows == []


def test_append_row():
    kv = make_kvp()
    kv.append_row("Gold", 500)
    assert kv._rows == [("Gold", "500")]


def test_append_multiple_rows():
    kv = make_kvp()
    kv.append_row("A", 1)
    kv.append_row("B", 2)
    assert len(kv._rows) == 2


def test_clear():
    kv = make_kvp(rows=[("x", 1), ("y", 2)])
    kv.clear()
    assert kv._rows == []


# ── Render ────────────────────────────────────────────────────────────────────

def test_render_empty_does_not_raise():
    surf = pygame.Surface((500, 400))
    kv = make_kvp()
    kv.render(surf, _ctx())


def test_render_with_rows_does_not_raise():
    surf = pygame.Surface((500, 400))
    kv = make_kvp(rows=[
        ("Name",    "Aldric"),
        ("Class",   "Warrior"),
        ("Level",   5),
        ("Power",   87),
        ("Age",     34),
    ])
    kv.render(surf, _ctx())


def test_render_with_title_does_not_raise():
    surf = pygame.Surface((500, 400))
    kv = make_kvp(title="Stats", rows=[("HP", 100)])
    kv.render(surf, _ctx())


def test_render_invisible_skips():
    surf = pygame.Surface((500, 400))
    surf.fill((3, 3, 3))
    kv = make_kvp(rows=[("x", 1)])
    kv.visible = False
    kv.render(surf, _ctx())
    assert surf.get_at((0, 0)) == (3, 3, 3, 255)


def test_render_many_rows_does_not_raise():
    surf = pygame.Surface((500, 400))
    rows = [(f"key_{i}", i) for i in range(50)]
    kv = make_kvp(rows=rows)
    kv.render(surf, _ctx())


def test_render_with_explicit_split():
    surf = pygame.Surface((500, 400))
    kv = make_kvp(rows=[("Name", "Hero")], split=200)
    kv.render(surf, _ctx())


def test_render_custom_colours():
    surf = pygame.Surface((500, 400))
    kv = make_kvp(
        rows=[("Label", "Value")],
        label_colour=(100, 100, 100),
        value_colour=(200, 200, 255),
    )
    kv.render(surf, _ctx())


def test_set_rect():
    kv = make_kvp()
    new_rect = pygame.Rect(50, 50, 300, 200)
    kv.set_rect(new_rect)
    assert kv.rect == new_rect