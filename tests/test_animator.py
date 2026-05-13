"""
tests/test_animator.py

Tests for pygame_engine.animation.SpriteAnimation and AnimationPlayer.

Frame surfaces are faked with small pygame.Surface objects.
Covers: construction, frame advancement, loop, ping-pong, on_finish,
play/stop, per-frame durations.
"""

import pygame
import pytest

from pygame_engine.animation.animator import AnimationPlayer, SpriteAnimation


def make_frames(n: int) -> list[pygame.Surface]:
    """Create n distinct 1x1 surfaces."""
    return [pygame.Surface((1, 1)) for _ in range(n)]


# ── SpriteAnimation ───────────────────────────────────────────────────────────

def test_sprite_animation_stores_frames() -> None:
    frames = make_frames(4)
    anim   = SpriteAnimation("idle", frames)
    assert anim.frame_count == 4
    assert anim.frames is frames


def test_sprite_animation_uniform_duration() -> None:
    anim = SpriteAnimation("run", make_frames(3), frame_duration=0.1)
    assert anim.durations == [0.1, 0.1, 0.1]


def test_sprite_animation_per_frame_duration() -> None:
    anim = SpriteAnimation("jump", make_frames(3),
                           frame_duration=[0.1, 0.2, 0.3])
    assert anim.durations == [0.1, 0.2, 0.3]


def test_sprite_animation_total_duration() -> None:
    anim = SpriteAnimation("x", make_frames(3), frame_duration=0.1)
    assert abs(anim.total_duration - 0.3) < 1e-9


def test_sprite_animation_empty_frames_raises() -> None:
    with pytest.raises(ValueError):
        SpriteAnimation("bad", [])


def test_sprite_animation_mismatched_durations_raises() -> None:
    with pytest.raises(ValueError):
        SpriteAnimation("bad", make_frames(3), frame_duration=[0.1, 0.2])


def test_sprite_animation_loop_default_true() -> None:
    anim = SpriteAnimation("idle", make_frames(2))
    assert anim.loop is True


def test_sprite_animation_no_loop() -> None:
    anim = SpriteAnimation("idle", make_frames(2), loop=False)
    assert anim.loop is False


# ── AnimationPlayer — basic ───────────────────────────────────────────────────

def test_player_no_frame_before_play() -> None:
    player = AnimationPlayer()
    assert player.current_frame is None
    assert player.is_playing is False


def test_player_play_sets_animation() -> None:
    frames = make_frames(4)
    anim   = SpriteAnimation("idle", frames)
    player = AnimationPlayer()
    player.add("idle", anim)
    player.play("idle")
    assert player.current_animation == "idle"
    assert player.current_frame is frames[0]


def test_player_play_unknown_name_raises() -> None:
    player = AnimationPlayer()
    with pytest.raises(KeyError):
        player.play("nonexistent")


def test_player_play_same_animation_no_restart() -> None:
    frames = make_frames(4)
    anim   = SpriteAnimation("idle", frames, frame_duration=0.1)
    player = AnimationPlayer()
    player.add("idle", anim)
    player.play("idle")
    player.update(0.15)   # advance past frame 0
    idx_before = player.frame_index
    player.play("idle")   # same animation — should not restart
    assert player.frame_index == idx_before


def test_player_play_same_animation_with_restart() -> None:
    frames = make_frames(4)
    anim   = SpriteAnimation("idle", frames, frame_duration=0.1)
    player = AnimationPlayer()
    player.add("idle", anim)
    player.play("idle")
    player.update(0.25)
    player.play("idle", restart=True)
    assert player.frame_index == 0


def test_player_stop_clears_current() -> None:
    frames = make_frames(2)
    anim   = SpriteAnimation("idle", frames)
    player = AnimationPlayer()
    player.add("idle", anim)
    player.play("idle")
    player.stop()
    assert player.current_frame   is None
    assert player.current_animation is None


# ── Frame advancement ─────────────────────────────────────────────────────────

def test_player_advances_frame_after_duration() -> None:
    frames = make_frames(4)
    anim   = SpriteAnimation("run", frames, frame_duration=0.1)
    player = AnimationPlayer()
    player.add("run", anim)
    player.play("run")
    player.update(0.15)
    assert player.frame_index == 1


def test_player_loops_back_to_zero() -> None:
    frames = make_frames(3)
    anim   = SpriteAnimation("idle", frames, frame_duration=0.1, loop=True)
    player = AnimationPlayer()
    player.add("idle", anim)
    player.play("idle")
    # 0.3s = exactly 3 frames → wraps back to frame 0
    # 0.35s = 0.05s into the next cycle → still frame 0
    player.update(0.35)
    assert player.frame_index == 0   # wrapped: 0→1→2→0, then 0.05s into frame 0
    assert player.is_finished is False
    # Advance further to confirm it keeps cycling
    player.update(0.1)   # 0.05+0.1 = 0.15s → frame 1
    assert player.frame_index == 1


def test_player_no_loop_stops_at_last_frame() -> None:
    frames = make_frames(3)
    anim   = SpriteAnimation("jump", frames, frame_duration=0.1, loop=False)
    player = AnimationPlayer()
    player.add("jump", anim)
    player.play("jump")
    player.update(1.0)   # well past end
    assert player.frame_index == 2
    assert player.is_finished is True


def test_player_on_finish_called_for_non_loop() -> None:
    finished: list[str] = []
    frames = make_frames(2)
    anim   = SpriteAnimation("hit", frames, frame_duration=0.1, loop=False)
    player = AnimationPlayer()
    player.add("hit", anim)
    player.on_finish = finished.append
    player.play("hit")
    player.update(0.5)
    assert finished == ["hit"]


def test_player_on_finish_not_called_for_loop() -> None:
    finished: list[str] = []
    frames = make_frames(2)
    anim   = SpriteAnimation("idle", frames, frame_duration=0.1, loop=True)
    player = AnimationPlayer()
    player.add("idle", anim)
    player.on_finish = finished.append
    player.play("idle")
    player.update(1.0)
    assert finished == []


# ── Ping-pong ─────────────────────────────────────────────────────────────────

def test_player_ping_pong_reverses() -> None:
    frames = make_frames(4)   # indices 0 1 2 3
    anim   = SpriteAnimation("breath", frames,
                             frame_duration=0.1, ping_pong=True)
    player = AnimationPlayer()
    player.add("breath", anim)
    player.play("breath")

    # 0→1→2→3→2→1→0→1...
    player.update(0.1)   # → frame 1
    assert player.frame_index == 1
    player.update(0.1)   # → frame 2
    assert player.frame_index == 2
    player.update(0.1)   # → frame 3
    assert player.frame_index == 3
    player.update(0.1)   # → frame 2 (reversing)
    assert player.frame_index == 2


# ── Per-frame duration ────────────────────────────────────────────────────────

def test_player_per_frame_duration() -> None:
    frames = make_frames(3)
    anim   = SpriteAnimation("x", frames,
                             frame_duration=[0.05, 0.2, 0.1])
    player = AnimationPlayer()
    player.add("x", anim)
    player.play("x")
    player.update(0.06)   # past first frame (0.05) → frame 1
    assert player.frame_index == 1
    player.update(0.1)    # 0.1 < 0.2 → still frame 1
    assert player.frame_index == 1
    player.update(0.11)   # 0.1+0.11 > 0.2 → frame 2
    assert player.frame_index == 2


# ── add_many ──────────────────────────────────────────────────────────────────

def test_add_many_registers_all() -> None:
    player = AnimationPlayer()
    player.add_many({
        "idle": SpriteAnimation("idle", make_frames(2)),
        "run":  SpriteAnimation("run",  make_frames(4)),
    })
    player.play("idle")
    assert player.current_animation == "idle"
    player.play("run")
    assert player.current_animation == "run"
