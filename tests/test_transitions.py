"""
tests/test_transitions.py

Tests for pygame_engine.scene.transitions.

Covers: base Transition progress/is_done, FadeTransition phases,
SlideTransition direction validation, SceneManager transition integration.
Rendering output is not asserted (visual) but render() is called to
confirm it doesn't raise.
"""

import pygame
import pytest

from pygame_engine.scene.transitions import (
    CrossfadeTransition,
    FadeTransition,
    SlideTransition,
    Transition,
)
from pygame_engine.scene import Scene, SceneManager


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_surface(w: int = 100, h: int = 80) -> pygame.Surface:
    s = pygame.Surface((w, h))
    s.fill((0, 0, 0))
    return s


def start_transition(t: Transition, w: int = 100, h: int = 80) -> None:
    """Start a transition with a blank capture surface."""
    t.start(make_surface(w, h))


# ── Base Transition ───────────────────────────────────────────────────────────

def test_transition_not_done_before_start() -> None:
    t = FadeTransition(duration=0.5)
    assert t.is_done is True   # no tween yet — treated as done


def test_transition_progress_zero_at_start() -> None:
    t = FadeTransition(duration=0.5)
    start_transition(t)
    assert t.progress == 0.0


def test_transition_advances_with_update() -> None:
    t = FadeTransition(duration=1.0)
    start_transition(t)
    t.update(0.5)
    assert abs(t.progress - 0.5) < 0.05   # easing may shift this slightly


def test_transition_done_after_full_duration() -> None:
    t = FadeTransition(duration=0.3)
    start_transition(t)
    done = t.update(0.3)
    assert done is True
    assert t.is_done is True


def test_transition_update_returns_false_while_running() -> None:
    t = FadeTransition(duration=1.0)
    start_transition(t)
    done = t.update(0.1)
    assert done is False


# ── FadeTransition ────────────────────────────────────────────────────────────

def test_fade_transition_renders_without_raising(display_surface) -> None:
    t = FadeTransition(duration=0.4)
    start_transition(t, *display_surface.get_size())
    scene_surf = make_surface(*display_surface.get_size())
    t.render(display_surface, scene_surf)


def test_fade_at_midpoint_renders_without_raising(display_surface) -> None:
    t = FadeTransition(duration=0.4)
    start_transition(t, *display_surface.get_size())
    t.update(0.2)
    scene_surf = make_surface(*display_surface.get_size())
    t.render(display_surface, scene_surf)


def test_fade_custom_colour_accepted() -> None:
    t = FadeTransition(duration=0.3, fade_colour=(255, 0, 0))
    assert t._fade_colour == (255, 0, 0)


# ── SlideTransition ───────────────────────────────────────────────────────────

def test_slide_valid_directions_accepted() -> None:
    for direction in ("left", "right", "up", "down"):
        t = SlideTransition(direction=direction)
        assert t._direction == direction


def test_slide_invalid_direction_raises() -> None:
    with pytest.raises(ValueError):
        SlideTransition(direction="diagonal")


def test_slide_renders_without_raising(display_surface) -> None:
    t = SlideTransition(duration=0.3, direction="right")
    start_transition(t, *display_surface.get_size())
    t.update(0.15)
    scene_surf = make_surface(*display_surface.get_size())
    t.render(display_surface, scene_surf)


# ── CrossfadeTransition ───────────────────────────────────────────────────────

def test_crossfade_renders_without_raising(display_surface) -> None:
    t = CrossfadeTransition(duration=0.3)
    start_transition(t, *display_surface.get_size())
    t.update(0.15)
    scene_surf = make_surface(*display_surface.get_size())
    t.render(display_surface, scene_surf)


# ── SceneManager transition integration ──────────────────────────────────────

class SimpleScene(Scene):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.entered = False
    def on_enter(self): self.entered = True


def test_replace_with_transition_changes_scene() -> None:
    manager = SceneManager()
    s1 = SimpleScene("first")
    s2 = SimpleScene("second")
    manager.push(s1)

    t = FadeTransition(duration=0.3)
    manager.replace_with(s2, t, surface=make_surface())

    assert manager.current_scene is s2
    assert s2.entered is True


def test_push_with_transition_pushes_scene() -> None:
    manager = SceneManager()
    s1 = SimpleScene("first")
    s2 = SimpleScene("second")
    manager.push(s1)

    t = SlideTransition(duration=0.2)
    manager.push_with(s2, t, surface=make_surface())

    assert manager.current_scene is s2
    assert manager.is_transitioning is True


def test_transition_clears_after_duration() -> None:
    manager = SceneManager()
    s1 = SimpleScene("first")
    s2 = SimpleScene("second")
    manager.push(s1)

    t = FadeTransition(duration=0.2)
    manager.replace_with(s2, t, surface=make_surface())

    assert manager.is_transitioning is True
    manager.update(0.25)   # past duration
    assert manager.is_transitioning is False


def test_pop_with_transition() -> None:
    manager = SceneManager()
    s1 = SimpleScene("first")
    s2 = SimpleScene("second")
    manager.push(s1)
    manager.push(s2)

    t = CrossfadeTransition(duration=0.2)
    removed = manager.pop_with(t, surface=make_surface())

    assert removed is s2
    assert manager.current_scene is s1
    assert manager.is_transitioning is True
