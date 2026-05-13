"""
tests/test_easing.py

Tests for pygame_engine.animation.easing.

Covers: boundary conditions (t=0, t=1), monotonicity, overshoot
behaviour for back/elastic/bounce, and registry lookup.
"""

import math

import pytest

from pygame_engine.animation.easing import (
    EASING_FUNCTIONS,
    ease_in_back,
    ease_in_bounce,
    ease_in_circ,
    ease_in_cubic,
    ease_in_elastic,
    ease_in_expo,
    ease_in_out_bounce,
    ease_in_out_cubic,
    ease_in_out_sine,
    ease_in_quad,
    ease_in_sine,
    ease_out_back,
    ease_out_bounce,
    ease_out_circ,
    ease_out_cubic,
    ease_out_elastic,
    ease_out_expo,
    ease_out_quad,
    ease_out_sine,
    get_easing,
    linear,
)

# All standard functions that must map 0→0 and 1→1
STANDARD_FUNCTIONS = [
    linear,
    ease_in_quad,    ease_out_quad,
    ease_in_cubic,   ease_out_cubic,   ease_in_out_cubic,
    ease_in_sine,    ease_out_sine,    ease_in_out_sine,
    ease_in_expo,    ease_out_expo,
    ease_in_circ,    ease_out_circ,
    ease_in_bounce,  ease_out_bounce,  ease_in_out_bounce,
]


# ── Boundary conditions ───────────────────────────────────────────────────────

@pytest.mark.parametrize("fn", STANDARD_FUNCTIONS)
def test_easing_zero_returns_zero(fn) -> None:
    assert abs(fn(0.0)) < 1e-9


@pytest.mark.parametrize("fn", STANDARD_FUNCTIONS)
def test_easing_one_returns_one(fn) -> None:
    assert abs(fn(1.0) - 1.0) < 1e-9


def test_linear_midpoint() -> None:
    assert abs(linear(0.5) - 0.5) < 1e-9


# ── Monotonicity for smooth functions ─────────────────────────────────────────

@pytest.mark.parametrize("fn", [
    ease_in_quad, ease_out_quad, ease_in_out_cubic,
    ease_in_sine, ease_out_sine, ease_in_out_sine,
])
def test_smooth_easing_is_monotonically_increasing(fn) -> None:
    """Smooth easings should never go backwards."""
    steps = [fn(i / 100) for i in range(101)]
    for a, b in zip(steps, steps[1:]):
        assert b >= a - 1e-9, f"{fn.__name__} went backwards: {a} -> {b}"


# ── Ease-in: starts slow ──────────────────────────────────────────────────────

def test_ease_in_cubic_starts_slow() -> None:
    assert ease_in_cubic(0.1) < 0.1   # below linear at t=0.1


def test_ease_out_cubic_starts_fast() -> None:
    assert ease_out_cubic(0.1) > 0.1   # above linear at t=0.1


# ── Expo edge cases ───────────────────────────────────────────────────────────

def test_ease_in_expo_at_zero() -> None:
    assert ease_in_expo(0.0) == 0.0

def test_ease_out_expo_at_one() -> None:
    assert ease_out_expo(1.0) == 1.0


# ── Back: slight overshoot ────────────────────────────────────────────────────

def test_ease_out_back_overshoots_one() -> None:
    """ease_out_back should exceed 1.0 briefly before settling."""
    values = [ease_out_back(t / 100) for t in range(101)]
    assert max(values) > 1.0

def test_ease_in_back_goes_below_zero() -> None:
    """ease_in_back should dip below 0.0 briefly."""
    values = [ease_in_back(t / 100) for t in range(101)]
    assert min(values) < 0.0


# ── Elastic: spring overshoot ─────────────────────────────────────────────────

def test_ease_out_elastic_overshoots() -> None:
    values = [ease_out_elastic(t / 1000) for t in range(1001)]
    assert max(values) > 1.0

def test_ease_in_elastic_at_boundaries() -> None:
    assert ease_in_elastic(0.0) == 0.0
    assert ease_in_elastic(1.0) == 1.0


# ── Bounce ────────────────────────────────────────────────────────────────────

def test_ease_out_bounce_values_in_range() -> None:
    """Bounce stays within [0, 1]."""
    for i in range(101):
        v = ease_out_bounce(i / 100)
        assert -1e-9 <= v <= 1.0 + 1e-9

def test_ease_in_bounce_is_mirror_of_out() -> None:
    """ease_in_bounce(t) == 1 - ease_out_bounce(1 - t)."""
    for i in range(1, 100):
        t = i / 100
        assert abs(ease_in_bounce(t) - (1.0 - ease_out_bounce(1.0 - t))) < 1e-9


# ── Registry ──────────────────────────────────────────────────────────────────

def test_registry_contains_all_expected_functions() -> None:
    expected = [
        "linear",
        "ease_in_quad",   "ease_out_quad",   "ease_in_out_quad",
        "ease_in_cubic",  "ease_out_cubic",  "ease_in_out_cubic",
        "ease_in_bounce", "ease_out_bounce", "ease_in_out_bounce",
    ]
    for name in expected:
        assert name in EASING_FUNCTIONS, f"Missing: {name}"


def test_get_easing_returns_correct_function() -> None:
    fn = get_easing("ease_out_cubic")
    assert fn is ease_out_cubic


def test_get_easing_raises_on_unknown_name() -> None:
    with pytest.raises(KeyError):
        get_easing("nonexistent_easing")
