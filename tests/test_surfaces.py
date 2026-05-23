"""
Tests for pygame_engine.graphics.surfaces.
"""

from __future__ import annotations

import pygame
import pytest

from pygame_engine.graphics.surfaces import (
    make_alpha_surface,
    make_solid_surface,
    blit_alpha,
    blit_alpha_surface,
    scale_surface,
    crop_surface,
)


@pytest.fixture(autouse=True)
def init_pygame():
    if not pygame.get_init():
        pygame.init()


# ── make_alpha_surface ────────────────────────────────────────────────────────

def test_make_alpha_surface_correct_size() -> None:
    s = make_alpha_surface(120, 80)
    assert s.get_size() == (120, 80)


def test_make_alpha_surface_has_srcalpha() -> None:
    s = make_alpha_surface(50, 50)
    assert s.get_flags() & pygame.SRCALPHA


def test_make_alpha_surface_is_transparent() -> None:
    s = make_alpha_surface(10, 10)
    assert s.get_at((5, 5))[3] == 0   # alpha channel = 0


# ── make_solid_surface ────────────────────────────────────────────────────────

def test_make_solid_surface_correct_size() -> None:
    s = make_solid_surface(100, 60, (255, 0, 0))
    assert s.get_size() == (100, 60)


def test_make_solid_surface_correct_colour() -> None:
    s = make_solid_surface(10, 10, (0, 128, 255))
    assert s.get_at((5, 5))[:3] == (0, 128, 255)


# ── blit_alpha ────────────────────────────────────────────────────────────────

def test_blit_alpha_zero_does_nothing() -> None:
    dest = make_solid_surface(100, 100, (0, 0, 0))
    src  = make_solid_surface(50, 50, (255, 255, 255))
    blit_alpha(dest, src, (0, 0), alpha=0)
    assert dest.get_at((25, 25))[:3] == (0, 0, 0)


def test_blit_alpha_255_blits_fully() -> None:
    dest = make_solid_surface(100, 100, (0, 0, 0))
    src  = make_solid_surface(50, 50, (200, 200, 200))
    blit_alpha(dest, src, (0, 0), alpha=255)
    assert dest.get_at((25, 25))[:3] == (200, 200, 200)


def test_blit_alpha_does_not_mutate_source() -> None:
    dest = pygame.Surface((100, 100))
    src  = make_solid_surface(50, 50, (100, 100, 100))
    original_alpha = src.get_alpha()
    blit_alpha(dest, src, (0, 0), alpha=128)
    assert src.get_alpha() == original_alpha


def test_blit_alpha_partial_does_not_raise() -> None:
    dest = make_solid_surface(100, 100, (0, 0, 0))
    src  = make_solid_surface(50, 50, (255, 0, 0))
    blit_alpha(dest, src, (25, 25), alpha=128)   # should not raise


# ── blit_alpha_surface ────────────────────────────────────────────────────────

def test_blit_alpha_surface_at_zero_does_nothing() -> None:
    dest = make_solid_surface(100, 100, (0, 0, 0))
    src  = make_solid_surface(50, 50, (255, 255, 255))
    blit_alpha_surface(dest, src, (0, 0), alpha=0.0)
    assert dest.get_at((25, 25))[:3] == (0, 0, 0)


def test_blit_alpha_surface_at_one_blits_fully() -> None:
    dest = make_solid_surface(100, 100, (0, 0, 0))
    src  = make_solid_surface(50, 50, (200, 200, 200))
    blit_alpha_surface(dest, src, (0, 0), alpha=1.0)
    assert dest.get_at((25, 25))[:3] == (200, 200, 200)


def test_blit_alpha_surface_clamps_above_one() -> None:
    dest = make_solid_surface(100, 100, (0, 0, 0))
    src  = make_solid_surface(50, 50, (255, 255, 255))
    blit_alpha_surface(dest, src, (0, 0), alpha=2.0)   # should not raise or crash


def test_blit_alpha_surface_clamps_below_zero() -> None:
    dest = make_solid_surface(100, 100, (0, 0, 0))
    src  = make_solid_surface(50, 50, (255, 255, 255))
    blit_alpha_surface(dest, src, (0, 0), alpha=-1.0)   # should not raise


# ── scale_surface ─────────────────────────────────────────────────────────────

def test_scale_surface_smooth() -> None:
    src = make_solid_surface(100, 100, (255, 0, 0))
    result = scale_surface(src, 50, 50, smooth=True)
    assert result.get_size() == (50, 50)


def test_scale_surface_fast() -> None:
    src = make_solid_surface(100, 100, (0, 255, 0))
    result = scale_surface(src, 200, 100, smooth=False)
    assert result.get_size() == (200, 100)


def test_scale_surface_returns_new_surface() -> None:
    src = make_solid_surface(50, 50, (0, 0, 255))
    result = scale_surface(src, 50, 50)
    assert result is not src


# ── crop_surface ──────────────────────────────────────────────────────────────

def test_crop_surface_correct_size() -> None:
    src = make_solid_surface(200, 200, (100, 100, 100))
    rect = pygame.Rect(50, 50, 60, 40)
    result = crop_surface(src, rect)
    assert result.get_size() == (60, 40)


def test_crop_surface_correct_content() -> None:
    src = pygame.Surface((100, 100))
    src.fill((0, 0, 0))
    pygame.draw.rect(src, (255, 0, 0), pygame.Rect(20, 20, 40, 40))
    result = crop_surface(src, pygame.Rect(20, 20, 40, 40))
    assert result.get_at((0, 0))[:3] == (255, 0, 0)


def test_crop_surface_returns_new_surface() -> None:
    src = make_solid_surface(100, 100, (50, 50, 50))
    result = crop_surface(src, pygame.Rect(0, 0, 100, 100))
    assert result is not src
