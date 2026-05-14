"""Tests for LogPanel widget."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

pygame.init()
pygame.display.set_mode((800, 600))

from pygame_engine.ui.controls.log_panel import LogPanel


def make_log(**kwargs):
    defaults = dict(rect=pygame.Rect(0, 0, 400, 300))
    defaults.update(kwargs)
    return LogPanel(**defaults)


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_empty():
    log = make_log()
    assert log.line_count == 0


def test_initial_scroll_zero():
    log = make_log()
    assert log._scroll_y == 0.0


# ── Append ────────────────────────────────────────────────────────────────────

def test_append_single_line():
    log = make_log()
    log.append("Hello")
    assert log.line_count == 1


def test_append_multiple_lines():
    log = make_log()
    for i in range(5):
        log.append(f"Line {i}")
    assert log.line_count == 5


def test_append_stores_text():
    log = make_log()
    log.append("test message")
    assert log._lines[0][0] == "test message"


def test_append_stores_custom_colour():
    log = make_log()
    colour = (255, 100, 100)
    log.append("red text", colour=colour)
    assert log._lines[0][1] == colour


def test_append_uses_default_colour():
    log = make_log()
    log.append("default")
    col = log._lines[0][1]
    assert isinstance(col, tuple) and len(col) == 3


def test_append_lines_adds_all():
    log = make_log()
    log.append_lines(["a", "b", "c"])
    assert log.line_count == 3


def test_append_lines_correct_text():
    log = make_log()
    log.append_lines(["x", "y"])
    assert log._lines[0][0] == "x"
    assert log._lines[1][0] == "y"


# ── Max lines ─────────────────────────────────────────────────────────────────

def test_max_lines_enforced():
    log = make_log(max_lines=5)
    for i in range(10):
        log.append(f"line {i}")
    assert log.line_count == 5


def test_max_lines_keeps_newest():
    log = make_log(max_lines=3)
    for i in range(5):
        log.append(f"line {i}")
    assert log._lines[0][0] == "line 2"
    assert log._lines[-1][0] == "line 4"


# ── Clear ─────────────────────────────────────────────────────────────────────

def test_clear_removes_all_lines():
    log = make_log()
    log.append_lines(["a", "b", "c"])
    log.clear()
    assert log.line_count == 0


def test_clear_resets_scroll():
    log = make_log()
    log._scroll_y = 99.0
    log.clear()
    assert log._scroll_y == 0.0


# ── Auto-scroll ───────────────────────────────────────────────────────────────

def test_auto_scroll_enabled_by_default():
    log = make_log()
    assert log._auto_scroll is True


def test_append_auto_scrolls_to_bottom():
    log = make_log(rect=pygame.Rect(0, 0, 300, 100))
    for _ in range(20):
        log.append("line")
    assert log._scroll_y == log._max_scroll()


def test_scroll_to_bottom_reenables_auto_scroll():
    log = make_log()
    log._auto_scroll = False
    log.scroll_to_bottom()
    assert log._auto_scroll is True


# ── Scroll bounds ─────────────────────────────────────────────────────────────

def test_max_scroll_zero_when_content_fits():
    log = make_log(rect=pygame.Rect(0, 0, 400, 800))
    log.append("one line")
    assert log._max_scroll() == 0.0


def test_max_scroll_positive_with_overflow():
    log = make_log(rect=pygame.Rect(0, 0, 300, 60))
    for _ in range(20):
        log.append("line")
    assert log._max_scroll() > 0.0


# ── Mouse wheel ───────────────────────────────────────────────────────────────

def test_wheel_outside_rect_not_consumed():
    log = make_log(rect=pygame.Rect(100, 100, 200, 200))
    pygame.mouse.set_pos((0, 0))
    ev = pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-3,
                            flipped=False, precise_x=0.0, precise_y=-3.0, touch=False)
    result = log.handle_event(ev)
    assert result is False


# ── Render ────────────────────────────────────────────────────────────────────

def test_render_empty_does_not_raise():
    surf = pygame.Surface((500, 400))
    log = make_log()
    log.render(surf)


def test_render_with_lines_does_not_raise():
    surf = pygame.Surface((500, 400))
    log = make_log()
    log.append_lines(["line one", "line two", "line three"])
    log.render(surf)


def test_render_invisible_skips():
    surf = pygame.Surface((500, 400))
    surf.fill((7, 8, 9))
    log = make_log()
    log.append("text")
    log.visible = False
    log.render(surf)
    assert surf.get_at((0, 0)) == (7, 8, 9, 255)


def test_render_with_overflow_does_not_raise():
    surf = pygame.Surface((300, 100))
    log = make_log(rect=pygame.Rect(0, 0, 300, 100))
    for i in range(30):
        log.append(f"line {i}")
    log.render(surf)
