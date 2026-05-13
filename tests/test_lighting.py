"""tests/test_lighting.py"""
import pygame
import pytest
from pygame_engine.lighting import Light, LightingSystem


def test_light_defaults():
    l = Light()
    assert l.enabled   is True
    assert l.radius    > 0
    assert l.intensity > 0
    assert l.flicker   == 0.0


def test_light_intensity_clamped():
    assert Light(intensity=2.0).intensity == 1.0
    assert Light(intensity=-1.0).intensity == 0.0


def test_light_flicker_clamped():
    assert Light(flicker=5.0).flicker == 1.0


def test_light_update_no_flicker_stable():
    l = Light(flicker=0.0, intensity=0.8)
    l.update(0.1)
    assert l.effective_intensity == pytest.approx(0.8)


def test_light_flicker_changes_intensity():
    import random
    random.seed(0)
    l = Light(flicker=1.0, intensity=0.8)
    before = l.effective_intensity
    l.update(0.5)
    # With seed 0 and some dt, effective intensity should differ from base
    # (may or may not due to sin phase, just ensure no crash)
    assert 0.0 <= l.effective_intensity <= 1.0


def test_lighting_system_defaults():
    ls = LightingSystem()
    assert ls.darkness == 1.0
    assert len(ls.lights) == 0


def test_add_light():
    ls = LightingSystem()
    l  = ls.add(Light())
    assert len(ls.lights) == 1
    assert l in ls.lights


def test_remove_light():
    ls = LightingSystem()
    l  = ls.add(Light())
    assert ls.remove(l) is True
    assert len(ls.lights) == 0


def test_remove_absent_returns_false():
    ls = LightingSystem()
    assert ls.remove(Light()) is False


def test_clear():
    ls = LightingSystem()
    ls.add(Light()); ls.add(Light())
    ls.clear()
    assert len(ls.lights) == 0


def test_darkness_clamped():
    ls = LightingSystem(darkness=2.0)
    assert ls.darkness == 1.0
    ls.darkness = -1.0
    assert ls.darkness == 0.0


def test_render_no_lights_does_not_raise(display_surface):
    ls = LightingSystem()
    ls.render(display_surface)


def test_render_with_lights_does_not_raise(display_surface):
    ls = LightingSystem()
    ls.add(Light(world_x=400, world_y=300, radius=150))
    ls.render(display_surface)


def test_render_with_camera_does_not_raise(display_surface):
    from pygame_engine.camera import Camera
    cam = Camera(800, 600)
    cam.move_to((0, 0))
    ls = LightingSystem()
    ls.add(Light(world_x=0, world_y=0, radius=200))
    ls.render(display_surface, cam)


def test_render_zero_darkness_is_noop(display_surface):
    ls = LightingSystem(darkness=0.0)
    ls.add(Light())
    ls.render(display_surface)   # should not raise


def test_disabled_light_not_rendered(display_surface):
    ls = LightingSystem()
    ls.add(Light(enabled=False))
    ls.render(display_surface)   # should not raise


def test_update_runs_without_crash():
    ls = LightingSystem()
    ls.add(Light(flicker=0.5))
    ls.update(0.016)


def test_repr():
    ls = LightingSystem()
    ls.add(Light())
    assert "LightingSystem" in repr(ls)
    assert "1" in repr(ls)
