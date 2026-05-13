"""
tests/test_particles.py

Tests for pygame_engine.particles — Particle, Emitter, and presets.

Covers: particle lifecycle, emitter spawn/update/clear, burst mode,
continuous mode, max_particles cap, preset construction.
"""

import pytest

from pygame_engine.particles.emitter import Emitter, _rand, _rand_colour
from pygame_engine.particles.particle import Particle
from pygame_engine.particles.presets import (
    explosion,
    fire_emitter,
    hit_effect,
    smoke,
    sparkle,
    trail,
)


# ── Particle ──────────────────────────────────────────────────────────────────

def test_particle_initial_age_is_zero() -> None:
    p = Particle(0, 0, 0, 0, 255, 0, 0, lifetime=1.0)
    assert p.age == 0.0


def test_particle_progress_zero_at_start() -> None:
    p = Particle(0, 0, 0, 0, 255, 0, 0, lifetime=1.0)
    assert p.progress == 0.0


def test_particle_not_dead_at_start() -> None:
    p = Particle(0, 0, 0, 0, 255, 0, 0, lifetime=1.0)
    assert p.is_dead is False


def test_particle_dead_when_age_exceeds_lifetime() -> None:
    p = Particle(0, 0, 0, 0, 255, 0, 0, lifetime=0.5)
    p.age = 0.6
    assert p.is_dead is True


def test_particle_progress_at_midlife() -> None:
    p = Particle(0, 0, 0, 0, 255, 0, 0, lifetime=2.0)
    p.age = 1.0
    assert abs(p.progress - 0.5) < 1e-6


def test_particle_progress_capped_at_one() -> None:
    p = Particle(0, 0, 0, 0, 255, 0, 0, lifetime=1.0)
    p.age = 999.0
    assert p.progress == 1.0


def test_particle_zero_lifetime_is_immediately_dead() -> None:
    p = Particle(0, 0, 0, 0, 255, 0, 0, lifetime=0.0)
    assert p.progress == 1.0


# ── Emitter — construction ────────────────────────────────────────────────────

def test_emitter_starts_with_no_particles() -> None:
    e = Emitter(0, 0)
    assert e.particle_count == 0
    assert e.is_empty is True


def test_emitter_not_running_by_default() -> None:
    e = Emitter(0, 0)
    assert e.is_running is False


# ── Emitter — burst ───────────────────────────────────────────────────────────

def test_burst_spawns_correct_count() -> None:
    e = Emitter(0, 0)
    e.burst(10)
    assert e.particle_count == 10


def test_burst_respects_max_particles() -> None:
    e = Emitter(0, 0, max_particles=5)
    e.burst(100)
    assert e.particle_count == 5


def test_burst_does_not_require_start() -> None:
    e = Emitter(0, 0)
    e.burst(5)
    assert e.particle_count == 5
    assert e.is_running is False


# ── Emitter — continuous ──────────────────────────────────────────────────────

def test_start_sets_running() -> None:
    e = Emitter(0, 0, rate=10)
    e.start()
    assert e.is_running is True


def test_stop_clears_running() -> None:
    e = Emitter(0, 0, rate=10)
    e.start()
    e.stop()
    assert e.is_running is False


def test_continuous_emitter_spawns_over_time() -> None:
    e = Emitter(0, 0, rate=100, lifetime=10.0)
    e.start()
    e.update(0.1)   # should emit ~10 particles
    assert e.particle_count > 0


def test_stopped_emitter_does_not_spawn() -> None:
    e = Emitter(0, 0, rate=100, lifetime=10.0)
    e.update(1.0)   # not started
    assert e.particle_count == 0


# ── Emitter — update ──────────────────────────────────────────────────────────

def test_particles_die_after_lifetime() -> None:
    e = Emitter(0, 0, lifetime=0.1)
    e.burst(10)
    assert e.particle_count == 10
    e.update(0.5)   # well past lifetime
    assert e.particle_count == 0


def test_particles_move_with_velocity() -> None:
    e = Emitter(100, 100, speed=100, angle=0.0,
                lifetime=10.0, drag=1.0, gravity=0)
    e.burst(1)
    p = e._particles[0]
    initial_x = p.x
    e.update(0.1)
    assert e._particles[0].x > initial_x   # moved right (angle=0)


def test_gravity_moves_particles_down() -> None:
    e = Emitter(0, 0, speed=0, angle=0.0,
                lifetime=10.0, gravity=100.0, drag=1.0)
    e.burst(1)
    initial_y = e._particles[0].y
    e.update(0.1)
    assert e._particles[0].y > initial_y


def test_clear_removes_all_particles() -> None:
    e = Emitter(0, 0, lifetime=10.0)
    e.burst(20)
    e.clear()
    assert e.particle_count == 0
    assert e.is_empty is True


# ── Emitter — position update ─────────────────────────────────────────────────

def test_emitter_position_can_be_updated() -> None:
    e = Emitter(0, 0, rate=60, lifetime=5.0)
    e.start()
    e.x = 200
    e.y = 300
    e.update(0.1)
    # New particles should spawn near (200, 300)
    for p in e._particles:
        assert abs(p.x - 200) < 20
        assert abs(p.y - 300) < 20


# ── Helper functions ──────────────────────────────────────────────────────────

def test_rand_fixed_value() -> None:
    assert _rand(5.0) == 5.0


def test_rand_range_within_bounds() -> None:
    for _ in range(100):
        v = _rand((2.0, 8.0))
        assert 2.0 <= v <= 8.0


def test_rand_colour_fixed() -> None:
    assert _rand_colour((255, 0, 128)) == (255, 0, 128)


def test_rand_colour_interpolates() -> None:
    for _ in range(50):
        c = _rand_colour(((0, 0, 0), (255, 255, 255)))
        assert 0 <= c[0] <= 255
        assert 0 <= c[1] <= 255
        assert 0 <= c[2] <= 255


# ── Presets ───────────────────────────────────────────────────────────────────

def test_explosion_preset_creates_emitter() -> None:
    e = explosion(400, 300)
    assert isinstance(e, Emitter)
    e.burst(20)
    assert e.particle_count == 20


def test_sparkle_preset_creates_emitter() -> None:
    e = sparkle(200, 200)
    assert isinstance(e, Emitter)
    e.burst(10)
    assert e.particle_count == 10


def test_smoke_preset_creates_running_emitter() -> None:
    e = smoke(100, 100)
    assert isinstance(e, Emitter)
    e.start()
    e.update(0.5)
    assert e.particle_count > 0


def test_fire_emitter_preset() -> None:
    e = fire_emitter(300, 400)
    assert isinstance(e, Emitter)
    e.start()
    e.update(0.2)
    assert e.particle_count > 0


def test_trail_preset_follows_position() -> None:
    e = trail(0, 0)
    e.start()
    e.x, e.y = 100, 100
    e.update(0.1)
    for p in e._particles:
        assert abs(p.x - 100) < 10
        assert abs(p.y - 100) < 10


def test_hit_effect_preset() -> None:
    e = hit_effect(50, 50)
    assert isinstance(e, Emitter)
    e.burst(12)
    assert e.particle_count == 12
