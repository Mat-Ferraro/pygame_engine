"""
Tests for pygame_engine.graphics.draw_utils.

All tests draw onto small in-memory surfaces and check pixel colours
or just verify no exceptions are raised.
"""

from __future__ import annotations

import pygame
import pytest

from pygame_engine.graphics.draw_utils import (
    draw_surface_style,
    draw_rect_bordered,
    draw_horizontal_line,
    draw_vertical_line,
    draw_cross,
    draw_chevron,
)


@pytest.fixture(autouse=True)
def init_pygame():
    if not pygame.get_init():
        pygame.init()


def make_surface(w=200, h=200) -> pygame.Surface:
    s = pygame.Surface((w, h))
    s.fill((0, 0, 0))
    return s


# ── draw_rect_bordered ────────────────────────────────────────────────────────

def test_draw_rect_bordered_fills_area() -> None:
    surf = make_surface()
    rect = pygame.Rect(10, 10, 80, 40)
    draw_rect_bordered(surf, rect, fill=(255, 0, 0))
    colour = surf.get_at((50, 30))[:3]
    assert colour == (255, 0, 0)


def test_draw_rect_bordered_no_border_does_not_raise() -> None:
    surf = make_surface()
    draw_rect_bordered(surf, pygame.Rect(0, 0, 50, 50), fill=(0, 255, 0), border=None)


def test_draw_rect_bordered_with_border_does_not_raise() -> None:
    surf = make_surface()
    draw_rect_bordered(
        surf, pygame.Rect(5, 5, 60, 60),
        fill=(40, 40, 80),
        border=(100, 100, 200),
        border_width=2,
        radius=4,
    )


def test_draw_rect_bordered_with_radius_does_not_raise() -> None:
    surf = make_surface()
    draw_rect_bordered(surf, pygame.Rect(0, 0, 100, 50),
                       fill=(80, 80, 80), radius=8)


# ── draw_surface_style ────────────────────────────────────────────────────────

def test_draw_surface_style_does_not_raise() -> None:
    from dataclasses import dataclass

    @dataclass
    class FakeStyle:
        bg: tuple = (50, 50, 80)
        border: tuple = (80, 80, 120)
        border_width: int = 1
        radius: int = 4

    surf = make_surface()
    rect = pygame.Rect(10, 10, 80, 40)
    draw_surface_style(surf, rect, FakeStyle())


def test_draw_surface_style_zero_border_width_skips_border() -> None:
    from dataclasses import dataclass

    @dataclass
    class NoBorderStyle:
        bg: tuple = (100, 100, 100)
        border: tuple = (255, 0, 0)
        border_width: int = 0
        radius: int = 0

    surf = make_surface()
    rect = pygame.Rect(0, 0, 200, 200)
    draw_surface_style(surf, rect, NoBorderStyle())
    # Interior should be bg colour, not border colour
    colour = surf.get_at((100, 100))[:3]
    assert colour == (100, 100, 100)


# ── draw_horizontal_line ──────────────────────────────────────────────────────

def test_draw_horizontal_line_draws_pixels() -> None:
    surf = make_surface()
    draw_horizontal_line(surf, y=50, x_start=10, x_end=100, colour=(255, 255, 0))
    colour = surf.get_at((55, 50))[:3]
    assert colour == (255, 255, 0)


def test_draw_horizontal_line_does_not_raise_with_width() -> None:
    surf = make_surface()
    draw_horizontal_line(surf, 30, 0, 100, (200, 200, 200), width=3)


# ── draw_vertical_line ────────────────────────────────────────────────────────

def test_draw_vertical_line_draws_pixels() -> None:
    surf = make_surface()
    draw_vertical_line(surf, x=40, y_start=10, y_end=90, colour=(0, 255, 255))
    colour = surf.get_at((40, 50))[:3]
    assert colour == (0, 255, 255)


def test_draw_vertical_line_does_not_raise_with_width() -> None:
    surf = make_surface()
    draw_vertical_line(surf, 50, 0, 100, (150, 150, 150), width=2)


# ── draw_cross ────────────────────────────────────────────────────────────────

def test_draw_cross_does_not_raise() -> None:
    surf = make_surface()
    draw_cross(surf, center=(100, 100), size=10, colour=(255, 0, 0))


def test_draw_cross_draws_at_center() -> None:
    surf = make_surface()
    draw_cross(surf, center=(100, 100), size=10, colour=(255, 0, 0))
    # The cross lines pass through the center area
    # At least some red pixels should be near center
    found = False
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if surf.get_at((100+dx, 100+dy))[:3] == (255, 0, 0):
                found = True
    assert found


# ── draw_chevron ──────────────────────────────────────────────────────────────

def test_draw_chevron_all_directions_do_not_raise() -> None:
    surf = make_surface()
    for direction in ("up", "down", "left", "right"):
        draw_chevron(surf, center=(100, 100), size=6,
                     colour=(200, 200, 200), direction=direction)


def test_draw_chevron_unknown_direction_falls_back() -> None:
    surf = make_surface()
    draw_chevron(surf, center=(100, 100), size=6,
                 colour=(200, 200, 200), direction="diagonal")   # should not raise


def test_draw_chevron_custom_width_does_not_raise() -> None:
    surf = make_surface()
    draw_chevron(surf, center=(50, 50), size=8,
                 colour=(100, 100, 100), width=3)
