"""
tests/test_camera.py

Tests for pygame_engine.camera.Camera.

Covers: construction, coordinate conversion, follow, zoom,
world bounds clamping, screen shake, is_visible culling.
"""

import math

import pygame
import pytest

from pygame_engine.camera import Camera


VP_W, VP_H = 800, 600


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_position_is_viewport_centre() -> None:
    cam = Camera(VP_W, VP_H)
    assert cam.position == (VP_W / 2, VP_H / 2)


def test_initial_zoom_is_one() -> None:
    assert Camera(VP_W, VP_H).zoom == pytest.approx(1.0)


def test_custom_zoom() -> None:
    assert Camera(VP_W, VP_H, zoom=2.0).zoom == pytest.approx(2.0)


def test_zero_zoom_clamped() -> None:
    cam = Camera(VP_W, VP_H, zoom=0.0)
    assert cam.zoom > 0


def test_initial_trauma_is_zero() -> None:
    assert Camera(VP_W, VP_H).trauma == pytest.approx(0.0)


def test_viewport_size_property() -> None:
    cam = Camera(VP_W, VP_H)
    assert cam.viewport_size == (VP_W, VP_H)


# ── world_to_screen ───────────────────────────────────────────────────────────

def test_world_to_screen_centre_maps_to_viewport_centre() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0, 0))
    sx, sy = cam.world_to_screen((0, 0))
    assert sx == VP_W // 2
    assert sy == VP_H // 2


def test_world_to_screen_offset() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0, 0))
    # 100px right of camera centre
    sx, sy = cam.world_to_screen((100, 0))
    assert sx == VP_W // 2 + 100
    assert sy == VP_H // 2


def test_world_to_screen_with_camera_offset() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((200, 150))
    sx, sy = cam.world_to_screen((200, 150))
    assert sx == VP_W // 2
    assert sy == VP_H // 2


# ── screen_to_world ───────────────────────────────────────────────────────────

def test_screen_to_world_centre() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0, 0))
    wx, wy = cam.screen_to_world((VP_W // 2, VP_H // 2))
    assert wx == pytest.approx(0.0)
    assert wy == pytest.approx(0.0)


def test_roundtrip_world_screen_world() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((300, 200))
    world = (450.0, 350.0)
    screen = cam.world_to_screen(world)
    back = cam.screen_to_world(screen)
    assert back[0] == pytest.approx(world[0], abs=1)
    assert back[1] == pytest.approx(world[1], abs=1)


# ── world_rect_to_screen ──────────────────────────────────────────────────────

def test_world_rect_to_screen_position() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0, 0))
    rect = pygame.Rect(0, 0, 64, 64)
    sr = cam.world_rect_to_screen(rect)
    assert sr.x == VP_W // 2
    assert sr.y == VP_H // 2


def test_world_rect_to_screen_size_with_zoom() -> None:
    cam = Camera(VP_W, VP_H, zoom=2.0)
    cam.move_to((0, 0))
    rect = pygame.Rect(0, 0, 64, 32)
    sr = cam.world_rect_to_screen(rect)
    assert sr.width  == 128
    assert sr.height == 64


# ── Zoom ──────────────────────────────────────────────────────────────────────

def test_zoom_doubles_screen_distance() -> None:
    cam = Camera(VP_W, VP_H, zoom=2.0)
    cam.move_to((0, 0))
    sx1, _ = cam.world_to_screen((100, 0))
    cam.zoom = 1.0
    sx2, _ = cam.world_to_screen((100, 0))
    assert sx1 - VP_W // 2 == pytest.approx(2 * (sx2 - VP_W // 2))


def test_zoom_setter_clamps_below_zero() -> None:
    cam = Camera(VP_W, VP_H)
    cam.zoom = -5.0
    assert cam.zoom > 0


# ── move_to / position ────────────────────────────────────────────────────────

def test_move_to_updates_position() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((500, 300))
    assert cam.position == (pytest.approx(500.0), pytest.approx(300.0))


def test_position_setter() -> None:
    cam = Camera(VP_W, VP_H)
    cam.position = (100.0, 200.0)
    assert cam.position == (pytest.approx(100.0), pytest.approx(200.0))


# ── follow ────────────────────────────────────────────────────────────────────

def test_follow_moves_toward_target() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0.0, 0.0))
    cam.follow((100.0, 0.0), speed=5.0, dt=0.1)
    x, _ = cam.position
    assert x > 0.0


def test_follow_does_not_overshoot() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0.0, 0.0))
    for _ in range(100):
        cam.follow((100.0, 0.0), speed=5.0, dt=0.1)
    x, _ = cam.position
    assert x <= 100.0 + 1.0


def test_follow_threshold_stops_near_target() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((99.9, 0.0))
    cam.follow((100.0, 0.0), speed=5.0, dt=0.1, threshold=1.0)
    x, _ = cam.position
    assert x == pytest.approx(99.9)


# ── World bounds ──────────────────────────────────────────────────────────────

def test_world_bounds_clamps_position() -> None:
    cam = Camera(VP_W, VP_H)
    bounds = pygame.Rect(0, 0, 1000, 800)
    cam.set_world_bounds(bounds)
    cam.move_to((-500, -500))   # way outside bounds
    x, y = cam.position
    assert x >= bounds.left
    assert y >= bounds.top


def test_world_bounds_none_removes_clamping() -> None:
    cam = Camera(VP_W, VP_H)
    cam.set_world_bounds(None)
    cam.move_to((-9999, -9999))
    x, y = cam.position
    assert x == pytest.approx(-9999.0)
    assert y == pytest.approx(-9999.0)


# ── Screen shake ──────────────────────────────────────────────────────────────

def test_add_trauma_increases_trauma() -> None:
    cam = Camera(VP_W, VP_H)
    cam.add_trauma(0.5)
    assert cam.trauma == pytest.approx(0.5)


def test_trauma_clamped_at_one() -> None:
    cam = Camera(VP_W, VP_H)
    cam.add_trauma(0.8)
    cam.add_trauma(0.8)
    assert cam.trauma <= 1.0


def test_trauma_decays_on_update() -> None:
    cam = Camera(VP_W, VP_H)
    cam.add_trauma(1.0)
    cam.update(0.5)
    assert cam.trauma < 1.0


def test_trauma_reaches_zero_over_time() -> None:
    cam = Camera(VP_W, VP_H)
    cam.add_trauma(1.0)
    for _ in range(100):
        cam.update(0.1)
    assert cam.trauma == pytest.approx(0.0)


def test_zero_trauma_no_shake_offset() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0, 0))
    cam.update(0.016)  # no trauma added
    # At zero trauma, shake offsets should be near zero
    sx, sy = cam.world_to_screen((0, 0))
    assert abs(sx - VP_W // 2) <= 1
    assert abs(sy - VP_H // 2) <= 1


# ── is_visible culling ────────────────────────────────────────────────────────

def test_is_visible_rect_on_screen() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0, 0))
    rect = pygame.Rect(-32, -32, 64, 64)  # centred near camera
    assert cam.is_visible(rect) is True


def test_is_visible_rect_off_screen() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0, 0))
    rect = pygame.Rect(5000, 5000, 64, 64)
    assert cam.is_visible(rect) is False


def test_is_visible_margin_extends_visibility() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((0, 0))
    # Just outside right edge
    rect = pygame.Rect(VP_W // 2 + 10, 0, 32, 32)
    assert cam.is_visible(rect, margin=0)  is False
    assert cam.is_visible(rect, margin=64) is True


# ── repr ──────────────────────────────────────────────────────────────────────

def test_repr_contains_position_and_zoom() -> None:
    cam = Camera(VP_W, VP_H)
    cam.move_to((100, 200))
    r = repr(cam)
    assert "Camera" in r
    assert "100" in r
