"""tests/test_positional_audio.py — headless tests (no mixer needed)."""
import pytest
from pygame_engine.audio.positional import PositionalAudio


def test_default_listener_at_origin():
    pa = PositionalAudio()
    assert pa.listener_position == (0.0, 0.0)


def test_set_listener():
    pa = PositionalAudio()
    pa.set_listener(100.0, 200.0)
    assert pa.listener_position == (100.0, 200.0)


def test_max_distance_property():
    pa = PositionalAudio(max_distance=400.0)
    assert pa.max_distance == 400.0


def test_max_distance_setter():
    pa = PositionalAudio()
    pa.max_distance = 800.0
    assert pa.max_distance == 800.0


def test_max_distance_clamped_above_zero():
    pa = PositionalAudio(max_distance=-50.0)
    assert pa.max_distance >= 1.0


def test_volume_at_listener_position_max():
    pa = PositionalAudio(max_distance=500.0)
    pa.set_listener(0.0, 0.0)
    left, right = pa._compute_volumes(0.0, 0.0, 1.0)
    assert left  == pytest.approx(1.0, abs=0.01)
    assert right == pytest.approx(1.0, abs=0.01)


def test_volume_zero_beyond_max_distance():
    pa = PositionalAudio(max_distance=500.0)
    pa.set_listener(0.0, 0.0)
    left, right = pa._compute_volumes(600.0, 0.0, 1.0)
    assert left  == 0.0
    assert right == 0.0


def test_left_louder_when_source_is_left():
    pa = PositionalAudio(max_distance=500.0)
    pa.set_listener(0.0, 0.0)
    left, right = pa._compute_volumes(-200.0, 0.0, 1.0)
    assert left > right


def test_right_louder_when_source_is_right():
    pa = PositionalAudio(max_distance=500.0)
    pa.set_listener(0.0, 0.0)
    left, right = pa._compute_volumes(200.0, 0.0, 1.0)
    assert right > left


def test_equal_volumes_when_directly_ahead():
    pa = PositionalAudio(max_distance=500.0)
    pa.set_listener(0.0, 0.0)
    left, right = pa._compute_volumes(0.0, 200.0, 1.0)
    assert abs(left - right) < 0.01


def test_base_volume_scales_output():
    pa = PositionalAudio(max_distance=500.0)
    pa.set_listener(0.0, 0.0)
    l1, r1 = pa._compute_volumes(0.0, 0.0, 1.0)
    l2, r2 = pa._compute_volumes(0.0, 0.0, 0.5)
    assert l2 == pytest.approx(l1 * 0.5, abs=0.01)
    assert r2 == pytest.approx(r1 * 0.5, abs=0.01)


def test_repr():
    assert "PositionalAudio" in repr(PositionalAudio())
