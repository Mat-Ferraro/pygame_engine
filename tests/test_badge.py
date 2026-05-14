"""Tests for Badge widget."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

pygame.init()
pygame.display.set_mode((800, 600))

from pygame_engine.ui.controls.badge import Badge, _STYLES


def make_badge(text="Test", style="default", rect=None):
    r = rect or pygame.Rect(0, 0, 90, 26)
    return Badge(r, text, style)


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_text():
    b = make_badge(text="Hello")
    assert b.text == "Hello"


def test_default_style():
    b = make_badge()
    assert b.style == "default"


def test_all_styles_defined():
    for style in ("default", "info", "good", "warning", "danger"):
        b = make_badge(style=style)
        assert b.style == style


def test_unknown_style_falls_back_gracefully():
    b = make_badge(style="nonexistent")
    surf = pygame.Surface((200, 60))
    b.render(surf)   # should not raise


# ── Property setters ──────────────────────────────────────────────────────────

def test_set_text_marks_dirty():
    b = make_badge(text="Old")
    b._dirty = False
    b.text = "New"
    assert b._dirty is True


def test_set_text_same_value_no_dirty():
    b = make_badge(text="Same")
    b._dirty = False
    b.text = "Same"
    assert b._dirty is False


def test_set_style_marks_dirty():
    b = make_badge(style="info")
    b._dirty = False
    b.style = "warning"
    assert b._dirty is True


def test_set_style_same_no_dirty():
    b = make_badge(style="danger")
    b._dirty = False
    b.style = "danger"
    assert b._dirty is False


def test_set_rect_marks_dirty():
    b = make_badge()
    b._dirty = False
    b.set_rect(pygame.Rect(10, 20, 80, 28))
    assert b._dirty is True


# ── Render ────────────────────────────────────────────────────────────────────

def test_render_does_not_raise():
    surf = pygame.Surface((200, 60))
    for style in _STYLES:
        b = Badge(pygame.Rect(10, 10, 90, 26), style.capitalize(), style)
        b.render(surf)


def test_render_invisible_does_nothing():
    surf = pygame.Surface((200, 60))
    surf.fill((12, 34, 56))
    b = make_badge()
    b.visible = False
    b.render(surf)
    assert surf.get_at((0, 0)) == (12, 34, 56, 255)


def test_render_produces_non_transparent_surface():
    """Badge should paint something (not leave rect entirely transparent)."""
    surf = pygame.Surface((200, 60), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    b = Badge(pygame.Rect(10, 10, 90, 26), "Ready", "good")
    b.render(surf)
    # At least one pixel in the badge area should be non-transparent
    found_opaque = False
    for x in range(10, 100):
        for y in range(10, 36):
            if surf.get_at((x, y))[3] > 0:
                found_opaque = True
                break
        if found_opaque:
            break
    assert found_opaque


def test_rebuild_called_once_and_cached():
    b = make_badge()
    surf = pygame.Surface((200, 60))
    b.render(surf)
    first_surf = b._surf
    b.render(surf)   # second render — same cached surface
    assert b._surf is first_surf


def test_text_change_triggers_rebuild():
    b = make_badge(text="Before")
    surf = pygame.Surface((200, 60))
    b.render(surf)
    first = b._surf
    b.text = "After"
    b.render(surf)
    assert b._surf is not first
