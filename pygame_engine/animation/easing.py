"""
Easing functions for pygame_engine.

Every function takes a normalised time value ``t`` in [0.0, 1.0] and
returns a transformed value, also generally in [0.0, 1.0] (some
functions like Back and Elastic may overshoot briefly beyond this range).

All functions are stateless — they are pure math, no instances needed.

Naming convention
-----------------
- ``ease_in_*``     — starts slow, ends fast
- ``ease_out_*``    — starts fast, ends slow
- ``ease_in_out_*`` — starts slow, fast in the middle, ends slow

Usage::

    from pygame_engine.animation.easing import ease_out_cubic

    t = timer.progress          # 0.0 → 1.0
    alpha = ease_out_cubic(t)   # apply to whatever you are animating

Available functions
-------------------
    linear
    ease_in_quad,        ease_out_quad,        ease_in_out_quad
    ease_in_cubic,       ease_out_cubic,       ease_in_out_cubic
    ease_in_quart,       ease_out_quart,       ease_in_out_quart
    ease_in_sine,        ease_out_sine,        ease_in_out_sine
    ease_in_expo,        ease_out_expo,        ease_in_out_expo
    ease_in_circ,        ease_out_circ,        ease_in_out_circ
    ease_in_back,        ease_out_back,        ease_in_out_back
    ease_in_elastic,     ease_out_elastic,     ease_in_out_elastic
    ease_in_bounce,      ease_out_bounce,      ease_in_out_bounce
"""

from __future__ import annotations

import math

# Type alias for easing functions
EasingFn = "Callable[[float], float]"


# ── Linear ────────────────────────────────────────────────────────────────────

def linear(t: float) -> float:
    """No easing — constant rate of change."""
    return t


# ── Quadratic ─────────────────────────────────────────────────────────────────

def ease_in_quad(t: float) -> float:
    """Accelerate from zero — quadratic."""
    return t * t

def ease_out_quad(t: float) -> float:
    """Decelerate to zero — quadratic."""
    return 1.0 - (1.0 - t) * (1.0 - t)

def ease_in_out_quad(t: float) -> float:
    """Accelerate then decelerate — quadratic."""
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0


# ── Cubic ─────────────────────────────────────────────────────────────────────

def ease_in_cubic(t: float) -> float:
    """Accelerate from zero — cubic."""
    return t * t * t

def ease_out_cubic(t: float) -> float:
    """Decelerate to zero — cubic."""
    return 1.0 - (1.0 - t) ** 3

def ease_in_out_cubic(t: float) -> float:
    """Accelerate then decelerate — cubic."""
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


# ── Quartic ───────────────────────────────────────────────────────────────────

def ease_in_quart(t: float) -> float:
    """Accelerate from zero — quartic."""
    return t * t * t * t

def ease_out_quart(t: float) -> float:
    """Decelerate to zero — quartic."""
    return 1.0 - (1.0 - t) ** 4

def ease_in_out_quart(t: float) -> float:
    """Accelerate then decelerate — quartic."""
    if t < 0.5:
        return 8.0 * t * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 4 / 2.0


# ── Sine ──────────────────────────────────────────────────────────────────────

def ease_in_sine(t: float) -> float:
    """Accelerate from zero — sinusoidal."""
    return 1.0 - math.cos(t * math.pi / 2.0)

def ease_out_sine(t: float) -> float:
    """Decelerate to zero — sinusoidal."""
    return math.sin(t * math.pi / 2.0)

def ease_in_out_sine(t: float) -> float:
    """Accelerate then decelerate — sinusoidal."""
    return -(math.cos(math.pi * t) - 1.0) / 2.0


# ── Exponential ───────────────────────────────────────────────────────────────

def ease_in_expo(t: float) -> float:
    """Accelerate from zero — exponential."""
    return 0.0 if t == 0.0 else 2.0 ** (10.0 * t - 10.0)

def ease_out_expo(t: float) -> float:
    """Decelerate to zero — exponential."""
    return 1.0 if t == 1.0 else 1.0 - 2.0 ** (-10.0 * t)

def ease_in_out_expo(t: float) -> float:
    """Accelerate then decelerate — exponential."""
    if t == 0.0: return 0.0
    if t == 1.0: return 1.0
    if t < 0.5:
        return 2.0 ** (20.0 * t - 10.0) / 2.0
    return (2.0 - 2.0 ** (-20.0 * t + 10.0)) / 2.0


# ── Circular ──────────────────────────────────────────────────────────────────

def ease_in_circ(t: float) -> float:
    """Accelerate from zero — circular."""
    return 1.0 - math.sqrt(max(0.0, 1.0 - t * t))

def ease_out_circ(t: float) -> float:
    """Decelerate to zero — circular."""
    return math.sqrt(max(0.0, 1.0 - (t - 1.0) ** 2))

def ease_in_out_circ(t: float) -> float:
    """Accelerate then decelerate — circular."""
    if t < 0.5:
        return (1.0 - math.sqrt(max(0.0, 1.0 - (2.0 * t) ** 2))) / 2.0
    return (math.sqrt(max(0.0, 1.0 - (-2.0 * t + 2.0) ** 2)) + 1.0) / 2.0


# ── Back (slight overshoot) ───────────────────────────────────────────────────

_BACK_C1 = 1.70158
_BACK_C2 = _BACK_C1 * 1.525
_BACK_C3 = _BACK_C1 + 1.0

def ease_in_back(t: float) -> float:
    """Overshoot backward then accelerate forward."""
    return _BACK_C3 * t * t * t - _BACK_C1 * t * t

def ease_out_back(t: float) -> float:
    """Overshoot forward then settle."""
    return 1.0 + _BACK_C3 * (t - 1.0) ** 3 + _BACK_C1 * (t - 1.0) ** 2

def ease_in_out_back(t: float) -> float:
    """Overshoot backward then forward then settle."""
    if t < 0.5:
        return ((2.0 * t) ** 2 * ((_BACK_C2 + 1.0) * 2.0 * t - _BACK_C2)) / 2.0
    return ((2.0 * t - 2.0) ** 2 * ((_BACK_C2 + 1.0) * (2.0 * t - 2.0) + _BACK_C2) + 2.0) / 2.0


# ── Elastic (spring overshoot) ────────────────────────────────────────────────

_ELASTIC_C4 = (2.0 * math.pi) / 3.0
_ELASTIC_C5 = (2.0 * math.pi) / 4.5

def ease_in_elastic(t: float) -> float:
    """Elastic snap from zero."""
    if t == 0.0: return 0.0
    if t == 1.0: return 1.0
    return -(2.0 ** (10.0 * t - 10.0)) * math.sin((t * 10.0 - 10.75) * _ELASTIC_C4)

def ease_out_elastic(t: float) -> float:
    """Elastic snap to zero."""
    if t == 0.0: return 0.0
    if t == 1.0: return 1.0
    return 2.0 ** (-10.0 * t) * math.sin((t * 10.0 - 0.75) * _ELASTIC_C4) + 1.0

def ease_in_out_elastic(t: float) -> float:
    """Elastic snap in and out."""
    if t == 0.0: return 0.0
    if t == 1.0: return 1.0
    if t < 0.5:
        return -(2.0 ** (20.0 * t - 10.0) * math.sin((20.0 * t - 11.125) * _ELASTIC_C5)) / 2.0
    return (2.0 ** (-20.0 * t + 10.0) * math.sin((20.0 * t - 11.125) * _ELASTIC_C5)) / 2.0 + 1.0


# ── Bounce ────────────────────────────────────────────────────────────────────

def ease_out_bounce(t: float) -> float:
    """Bounce to zero."""
    n1, d1 = 7.5625, 2.75
    if t < 1.0 / d1:
        return n1 * t * t
    elif t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

def ease_in_bounce(t: float) -> float:
    """Bounce from zero."""
    return 1.0 - ease_out_bounce(1.0 - t)

def ease_in_out_bounce(t: float) -> float:
    """Bounce in and out."""
    if t < 0.5:
        return (1.0 - ease_out_bounce(1.0 - 2.0 * t)) / 2.0
    return (1.0 + ease_out_bounce(2.0 * t - 1.0)) / 2.0


# ── Registry ──────────────────────────────────────────────────────────────────
# Useful for serialisation, tooling, or selecting easings by name at runtime.

EASING_FUNCTIONS: dict[str, "Callable[[float], float]"] = {
    "linear":            linear,
    "ease_in_quad":      ease_in_quad,
    "ease_out_quad":     ease_out_quad,
    "ease_in_out_quad":  ease_in_out_quad,
    "ease_in_cubic":     ease_in_cubic,
    "ease_out_cubic":    ease_out_cubic,
    "ease_in_out_cubic": ease_in_out_cubic,
    "ease_in_quart":     ease_in_quart,
    "ease_out_quart":    ease_out_quart,
    "ease_in_out_quart": ease_in_out_quart,
    "ease_in_sine":      ease_in_sine,
    "ease_out_sine":     ease_out_sine,
    "ease_in_out_sine":  ease_in_out_sine,
    "ease_in_expo":      ease_in_expo,
    "ease_out_expo":     ease_out_expo,
    "ease_in_out_expo":  ease_in_out_expo,
    "ease_in_circ":      ease_in_circ,
    "ease_out_circ":     ease_out_circ,
    "ease_in_out_circ":  ease_in_out_circ,
    "ease_in_back":      ease_in_back,
    "ease_out_back":     ease_out_back,
    "ease_in_out_back":  ease_in_out_back,
    "ease_in_elastic":   ease_in_elastic,
    "ease_out_elastic":  ease_out_elastic,
    "ease_in_out_elastic": ease_in_out_elastic,
    "ease_in_bounce":    ease_in_bounce,
    "ease_out_bounce":   ease_out_bounce,
    "ease_in_out_bounce": ease_in_out_bounce,
}


def get_easing(name: str) -> "Callable[[float], float]":
    """
    Look up an easing function by name.

    Args:
        name: One of the keys in ``EASING_FUNCTIONS``.

    Returns:
        The easing function.

    Raises:
        KeyError: If ``name`` is not recognised.
    """
    if name not in EASING_FUNCTIONS:
        raise KeyError(
            f"Unknown easing {name!r}. "
            f"Available: {sorted(EASING_FUNCTIONS)}"
        )
    return EASING_FUNCTIONS[name]