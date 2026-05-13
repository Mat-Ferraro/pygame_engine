"""
tests/test_colors.py

Tests for pygame_engine.utils.colors.

Covers: lerp_color, lerp_color_alpha, brighten, with_alpha,
hex_to_rgb, rgb_to_hex, hsv_to_rgb.
"""

import pytest

from pygame_engine.utils.colors import (
    brighten,
    hex_to_rgb,
    hsv_to_rgb,
    lerp_color,
    lerp_color_alpha,
    rgb_to_hex,
    with_alpha,
)


# ── lerp_color ────────────────────────────────────────────────────────────────

def test_lerp_color_at_zero_returns_a() -> None:
    assert lerp_color((0, 0, 0), (255, 255, 255), 0.0) == (0, 0, 0)

def test_lerp_color_at_one_returns_b() -> None:
    assert lerp_color((0, 0, 0), (255, 255, 255), 1.0) == (255, 255, 255)

def test_lerp_color_midpoint() -> None:
    result = lerp_color((0, 0, 0), (100, 100, 100), 0.5)
    assert result == (50, 50, 50)

def test_lerp_color_clamps_t_below_zero() -> None:
    result = lerp_color((100, 100, 100), (200, 200, 200), -1.0)
    assert result == (100, 100, 100)

def test_lerp_color_clamps_t_above_one() -> None:
    result = lerp_color((100, 100, 100), (200, 200, 200), 2.0)
    assert result == (200, 200, 200)

def test_lerp_color_channels_independent() -> None:
    result = lerp_color((0, 100, 200), (100, 100, 0), 0.5)
    assert result[0] == 50
    assert result[1] == 100
    assert result[2] == 100


# ── lerp_color_alpha ──────────────────────────────────────────────────────────

def test_lerp_color_alpha_at_zero() -> None:
    a = (0, 0, 0, 0)
    b = (255, 255, 255, 255)
    assert lerp_color_alpha(a, b, 0.0) == a

def test_lerp_color_alpha_at_one() -> None:
    a = (0, 0, 0, 0)
    b = (255, 255, 255, 255)
    assert lerp_color_alpha(a, b, 1.0) == b

def test_lerp_color_alpha_midpoint() -> None:
    a = (0, 0, 0, 0)
    b = (100, 100, 100, 200)
    r = lerp_color_alpha(a, b, 0.5)
    assert r == (50, 50, 50, 100)


# ── brighten ──────────────────────────────────────────────────────────────────

def test_brighten_factor_one_unchanged() -> None:
    assert brighten((100, 150, 200), 1.0) == (100, 150, 200)

def test_brighten_factor_two_doubles() -> None:
    result = brighten((50, 100, 50), 2.0)
    assert result == (100, 200, 100)

def test_brighten_clamped_at_255() -> None:
    result = brighten((200, 200, 200), 2.0)
    assert result == (255, 255, 255)

def test_brighten_factor_half_darkens() -> None:
    result = brighten((100, 200, 50), 0.5)
    assert result == (50, 100, 25)

def test_brighten_clamped_at_zero() -> None:
    result = brighten((50, 50, 50), 0.0)
    assert result == (0, 0, 0)


# ── with_alpha ────────────────────────────────────────────────────────────────

def test_with_alpha_adds_channel() -> None:
    result = with_alpha((100, 150, 200), 128)
    assert result == (100, 150, 200, 128)

def test_with_alpha_zero() -> None:
    assert with_alpha((255, 0, 0), 0) == (255, 0, 0, 0)

def test_with_alpha_255() -> None:
    assert with_alpha((255, 0, 0), 255) == (255, 0, 0, 255)

def test_with_alpha_clamped_above_255() -> None:
    result = with_alpha((0, 0, 0), 300)
    assert result[3] == 255

def test_with_alpha_clamped_below_zero() -> None:
    result = with_alpha((0, 0, 0), -10)
    assert result[3] == 0


# ── hex_to_rgb ────────────────────────────────────────────────────────────────

def test_hex_to_rgb_with_hash() -> None:
    assert hex_to_rgb("#ff0000") == (255, 0, 0)

def test_hex_to_rgb_without_hash() -> None:
    assert hex_to_rgb("00ff00") == (0, 255, 0)

def test_hex_to_rgb_white() -> None:
    assert hex_to_rgb("#ffffff") == (255, 255, 255)

def test_hex_to_rgb_black() -> None:
    assert hex_to_rgb("#000000") == (0, 0, 0)

def test_hex_to_rgb_three_digit() -> None:
    assert hex_to_rgb("#f00") == (255, 0, 0)

def test_hex_to_rgb_three_digit_mixed() -> None:
    assert hex_to_rgb("#abc") == (0xaa, 0xbb, 0xcc)

def test_hex_to_rgb_invalid_raises() -> None:
    with pytest.raises(ValueError):
        hex_to_rgb("gg0000")

def test_hex_to_rgb_wrong_length_raises() -> None:
    with pytest.raises(ValueError):
        hex_to_rgb("#12345")


# ── rgb_to_hex ────────────────────────────────────────────────────────────────

def test_rgb_to_hex_red() -> None:
    assert rgb_to_hex((255, 0, 0)) == "#ff0000"

def test_rgb_to_hex_white() -> None:
    assert rgb_to_hex((255, 255, 255)) == "#ffffff"

def test_rgb_to_hex_black() -> None:
    assert rgb_to_hex((0, 0, 0)) == "#000000"

def test_rgb_hex_roundtrip() -> None:
    colour = (123, 45, 200)
    assert hex_to_rgb(rgb_to_hex(colour)) == colour


# ── hsv_to_rgb ────────────────────────────────────────────────────────────────

def test_hsv_red() -> None:
    r, g, b = hsv_to_rgb(0.0, 1.0, 1.0)
    assert r == 255
    assert g == 0
    assert b == 0

def test_hsv_green() -> None:
    r, g, b = hsv_to_rgb(1/3, 1.0, 1.0)
    assert r == 0
    assert g == 255
    assert b == 0

def test_hsv_blue() -> None:
    r, g, b = hsv_to_rgb(2/3, 1.0, 1.0)
    assert r == 0
    assert g == 0
    assert b == 255

def test_hsv_white() -> None:
    r, g, b = hsv_to_rgb(0.0, 0.0, 1.0)
    assert r == 255
    assert g == 255
    assert b == 255

def test_hsv_black() -> None:
    r, g, b = hsv_to_rgb(0.0, 0.0, 0.0)
    assert r == 0
    assert g == 0
    assert b == 0

def test_hsv_values_in_range() -> None:
    for h in (0.0, 0.25, 0.5, 0.75, 1.0):
        r, g, b = hsv_to_rgb(h, 0.8, 0.9)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255
