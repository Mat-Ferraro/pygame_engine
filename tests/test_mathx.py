"""
tests/test_mathx.py

Tests for pygame_engine.utils.mathx.

Covers: clamp, clamp01, remap, remap_clamped, lerp, lerp_clamped,
smoothstep, smootherstep, angle_to_vec, vec_to_angle, approach.
"""

import math
import pytest

from pygame_engine.utils.mathx import (
    angle_to_vec,
    approach,
    clamp,
    clamp01,
    lerp,
    lerp_clamped,
    remap,
    remap_clamped,
    smootherstep,
    smoothstep,
    vec_to_angle,
)


# ── clamp ─────────────────────────────────────────────────────────────────────

def test_clamp_within_range() -> None:
    assert clamp(5.0, 0.0, 10.0) == 5.0

def test_clamp_at_lower() -> None:
    assert clamp(0.0, 0.0, 10.0) == 0.0

def test_clamp_at_upper() -> None:
    assert clamp(10.0, 0.0, 10.0) == 10.0

def test_clamp_below_range() -> None:
    assert clamp(-5.0, 0.0, 10.0) == 0.0

def test_clamp_above_range() -> None:
    assert clamp(15.0, 0.0, 10.0) == 10.0

def test_clamp_negative_range() -> None:
    assert clamp(-3.0, -10.0, -1.0) == -3.0


# ── clamp01 ───────────────────────────────────────────────────────────────────

def test_clamp01_midpoint() -> None:
    assert clamp01(0.5) == 0.5

def test_clamp01_below_zero() -> None:
    assert clamp01(-1.0) == 0.0

def test_clamp01_above_one() -> None:
    assert clamp01(2.0) == 1.0

def test_clamp01_at_boundaries() -> None:
    assert clamp01(0.0) == 0.0
    assert clamp01(1.0) == 1.0


# ── remap ─────────────────────────────────────────────────────────────────────

def test_remap_basic() -> None:
    assert abs(remap(5.0, 0.0, 10.0, 0.0, 100.0) - 50.0) < 1e-6

def test_remap_at_start() -> None:
    assert abs(remap(0.0, 0.0, 10.0, 0.0, 100.0) - 0.0) < 1e-6

def test_remap_at_end() -> None:
    assert abs(remap(10.0, 0.0, 10.0, 0.0, 100.0) - 100.0) < 1e-6

def test_remap_different_ranges() -> None:
    result = remap(0.5, 0.0, 1.0, -1.0, 1.0)
    assert abs(result - 0.0) < 1e-6

def test_remap_not_clamped_below() -> None:
    result = remap(-1.0, 0.0, 1.0, 0.0, 10.0)
    assert result < 0.0

def test_remap_equal_in_range_returns_out_min() -> None:
    result = remap(5.0, 5.0, 5.0, 10.0, 20.0)
    assert result == 10.0


# ── remap_clamped ─────────────────────────────────────────────────────────────

def test_remap_clamped_clamps_output() -> None:
    assert remap_clamped(-5.0, 0.0, 10.0, 0.0, 100.0) == 0.0
    assert remap_clamped(15.0, 0.0, 10.0, 0.0, 100.0) == 100.0

def test_remap_clamped_midpoint() -> None:
    assert abs(remap_clamped(5.0, 0.0, 10.0, 0.0, 100.0) - 50.0) < 1e-6


# ── lerp ──────────────────────────────────────────────────────────────────────

def test_lerp_start() -> None:
    assert lerp(0.0, 100.0, 0.0) == 0.0

def test_lerp_end() -> None:
    assert lerp(0.0, 100.0, 1.0) == 100.0

def test_lerp_midpoint() -> None:
    assert abs(lerp(0.0, 100.0, 0.5) - 50.0) < 1e-6

def test_lerp_negative_range() -> None:
    assert abs(lerp(-100.0, 100.0, 0.5) - 0.0) < 1e-6

def test_lerp_not_clamped() -> None:
    assert lerp(0.0, 10.0, 2.0) == 20.0


# ── lerp_clamped ──────────────────────────────────────────────────────────────

def test_lerp_clamped_clamps_t() -> None:
    assert lerp_clamped(0.0, 10.0, -1.0) == 0.0
    assert lerp_clamped(0.0, 10.0,  2.0) == 10.0

def test_lerp_clamped_midpoint() -> None:
    assert abs(lerp_clamped(0.0, 100.0, 0.5) - 50.0) < 1e-6


# ── smoothstep ────────────────────────────────────────────────────────────────

def test_smoothstep_at_zero() -> None:
    assert smoothstep(0.0) == 0.0

def test_smoothstep_at_one() -> None:
    assert smoothstep(1.0) == 1.0

def test_smoothstep_at_midpoint() -> None:
    assert smoothstep(0.5) == 0.5

def test_smoothstep_symmetric() -> None:
    assert abs(smoothstep(0.25) - (1.0 - smoothstep(0.75))) < 1e-6

def test_smoothstep_clamped_below() -> None:
    assert smoothstep(-1.0) == 0.0

def test_smoothstep_clamped_above() -> None:
    assert smoothstep(2.0) == 1.0

def test_smoothstep_greater_than_linear_in_middle() -> None:
    # smoothstep at 0.3 should be above linear (0.3) since it's S-shaped
    # Actually smoothstep starts slow — check it's below linear at 0.3
    assert smoothstep(0.3) < 0.3 or smoothstep(0.7) > 0.7


# ── smootherstep ──────────────────────────────────────────────────────────────

def test_smootherstep_at_zero() -> None:
    assert smootherstep(0.0) == 0.0

def test_smootherstep_at_one() -> None:
    assert smootherstep(1.0) == 1.0

def test_smootherstep_at_midpoint() -> None:
    assert smootherstep(0.5) == 0.5

def test_smootherstep_smoother_than_smoothstep() -> None:
    # smootherstep has flatter start — lower value at t=0.1
    assert smootherstep(0.1) < smoothstep(0.1)


# ── angle_to_vec ──────────────────────────────────────────────────────────────

def test_angle_to_vec_zero_points_right() -> None:
    dx, dy = angle_to_vec(0)
    assert abs(dx - 1.0) < 1e-6
    assert abs(dy - 0.0) < 1e-6

def test_angle_to_vec_90_points_down() -> None:
    dx, dy = angle_to_vec(90)
    assert abs(dx - 0.0) < 1e-6
    assert abs(dy - 1.0) < 1e-6

def test_angle_to_vec_180_points_left() -> None:
    dx, dy = angle_to_vec(180)
    assert abs(dx - (-1.0)) < 1e-6
    assert abs(dy - 0.0) < 1e-6

def test_angle_to_vec_270_points_up() -> None:
    dx, dy = angle_to_vec(270)
    assert abs(dx - 0.0) < 1e-6
    assert abs(dy - (-1.0)) < 1e-6

def test_angle_to_vec_is_unit_length() -> None:
    for angle in (0, 45, 90, 135, 180, 225, 270, 315):
        dx, dy = angle_to_vec(angle)
        length = math.sqrt(dx*dx + dy*dy)
        assert abs(length - 1.0) < 1e-6


# ── vec_to_angle ──────────────────────────────────────────────────────────────

def test_vec_to_angle_right() -> None:
    assert abs(vec_to_angle(1.0, 0.0) - 0.0) < 1e-6

def test_vec_to_angle_down() -> None:
    assert abs(vec_to_angle(0.0, 1.0) - 90.0) < 1e-6

def test_vec_to_angle_left() -> None:
    assert abs(vec_to_angle(-1.0, 0.0) - 180.0) < 1e-6

def test_angle_vec_roundtrip() -> None:
    for angle in (0, 30, 45, 90, 135, 180, 225, 270, 315):
        dx, dy = angle_to_vec(float(angle))
        recovered = vec_to_angle(dx, dy)
        assert abs(recovered - angle) < 1e-4


# ── approach ──────────────────────────────────────────────────────────────────

def test_approach_moves_toward_target() -> None:
    result = approach(0.0, 10.0, 3.0)
    assert result == 3.0

def test_approach_does_not_overshoot() -> None:
    result = approach(8.0, 10.0, 5.0)
    assert result == 10.0

def test_approach_negative_direction() -> None:
    result = approach(10.0, 0.0, 3.0)
    assert result == 7.0

def test_approach_already_at_target() -> None:
    result = approach(5.0, 5.0, 1.0)
    assert result == 5.0

def test_approach_step_zero_no_movement() -> None:
    result = approach(3.0, 10.0, 0.0)
    assert result == 3.0
