"""
utils/mathx.py

Generic math helpers for pygame_engine.

Small functions that extend Python's math module for common game/UI
needs: clamping, mapping, easing, vector helpers. None of these are
specific to pygame — they work on plain numbers and tuples.

The ``x`` suffix distinguishes this from the stdlib ``math`` module.
"""

from __future__ import annotations

import math


# ── Clamping ──────────────────────────────────────────────────────────────────

def clamp(value: float, lo: float, hi: float) -> float:
    """
    Clamp ``value`` to the range [lo, hi].

    Args:
        value: Input value.
        lo:    Minimum output value.
        hi:    Maximum output value.

    Returns:
        Clamped value.
    """
    return max(lo, min(hi, value))


def clamp01(value: float) -> float:
    """Clamp ``value`` to [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


# ── Mapping / remapping ───────────────────────────────────────────────────────

def remap(
    value: float,
    in_min: float,
    in_max: float,
    out_min: float,
    out_max: float,
) -> float:
    """
    Remap ``value`` from one range to another.

    Args:
        value:   Input value.
        in_min:  Input range minimum.
        in_max:  Input range maximum.
        out_min: Output range minimum.
        out_max: Output range maximum.

    Returns:
        Remapped value. Not clamped — may exceed output range if input
        exceeds input range.
    """
    if in_max == in_min:
        return out_min
    t = (value - in_min) / (in_max - in_min)
    return out_min + t * (out_max - out_min)


def remap_clamped(
    value: float,
    in_min: float,
    in_max: float,
    out_min: float,
    out_max: float,
) -> float:
    """
    Remap ``value`` from one range to another, clamping the output.

    Like ``remap`` but the result is clamped to [out_min, out_max].
    """
    result = remap(value, in_min, in_max, out_min, out_max)
    lo, hi = (out_min, out_max) if out_min <= out_max else (out_max, out_min)
    return max(lo, min(hi, result))


# ── Interpolation ─────────────────────────────────────────────────────────────

def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation between ``a`` and ``b``.

    Args:
        a: Start value.
        b: End value.
        t: Blend factor 0.0–1.0. Not clamped.

    Returns:
        Interpolated value.
    """
    return a + (b - a) * t


def lerp_clamped(a: float, b: float, t: float) -> float:
    """Linear interpolation with ``t`` clamped to [0.0, 1.0]."""
    return lerp(a, b, max(0.0, min(1.0, t)))


def smoothstep(t: float) -> float:
    """
    Smooth hermite interpolation for ``t`` in [0.0, 1.0].

    Produces a smooth S-curve: starts and ends slowly, fast in the
    middle. Useful for UI transitions and easing.

    Args:
        t: Input value, expected in [0.0, 1.0]. Not clamped.

    Returns:
        Smoothed value.
    """
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    """
    Ken Perlin's improved smoothstep — zero first and second derivatives
    at t=0 and t=1. Smoother than ``smoothstep`` for most transitions.

    Args:
        t: Input value, expected in [0.0, 1.0]. Not clamped.

    Returns:
        Smoothed value.
    """
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


# ── Angle helpers ─────────────────────────────────────────────────────────────

def angle_to_vec(angle_deg: float) -> tuple[float, float]:
    """
    Convert an angle in degrees to a unit direction vector.

    0° points right (+x), 90° points down (+y) in screen space.

    Args:
        angle_deg: Angle in degrees.

    Returns:
        (dx, dy) unit vector.
    """
    rad = math.radians(angle_deg)
    return (math.cos(rad), math.sin(rad))


def vec_to_angle(dx: float, dy: float) -> float:
    """
    Convert a direction vector to an angle in degrees.

    Args:
        dx: X component.
        dy: Y component.

    Returns:
        Angle in degrees, 0–360.
    """
    return math.degrees(math.atan2(dy, dx)) % 360


def approach(current: float, target: float, step: float) -> float:
    """
    Move ``current`` toward ``target`` by at most ``step`` per call.

    Useful for smooth value chasing without overshooting.

    Args:
        current: Current value.
        target:  Target value.
        step:    Maximum change per call (positive).

    Returns:
        New value, no further from target than ``step``.
    """
    diff = target - current
    if abs(diff) <= step:
        return target
    return current + math.copysign(step, diff)
