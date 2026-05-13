"""tests/test_animation_state_machine.py"""
import pygame
import pytest
from pygame_engine.animation import AnimationPlayer, AnimationStateMachine, SpriteAnimation


def make_player(*names):
    p = AnimationPlayer()
    for name in names:
        surf = pygame.Surface((16, 16))
        anim = SpriteAnimation(name, [surf], frame_duration=0.1)
        p.add(name, anim)
    return p


def test_initial_state_is_none():
    sm = AnimationStateMachine(make_player("idle"))
    sm.add_state("idle", default=True)
    assert sm.current_state is None   # not yet updated


def test_first_update_enters_default():
    sm = AnimationStateMachine(make_player("idle"))
    sm.add_state("idle", default=True)
    sm.update(0.016)
    assert sm.current_state == "idle"


def test_transition_fires_when_condition_true():
    p  = make_player("idle", "run")
    sm = AnimationStateMachine(p)
    sm.add_state("idle", default=True)
    sm.add_state("run")
    sm.add_transition("idle", "run", condition=lambda p: p.get("moving", False))
    sm.update(0.016)
    assert sm.current_state == "idle"
    sm.update(0.016, params={"moving": True})
    assert sm.current_state == "run"


def test_transition_back():
    p  = make_player("idle", "run")
    sm = AnimationStateMachine(p)
    sm.add_state("idle", default=True)
    sm.add_state("run")
    sm.add_transition("idle", "run",  condition=lambda p: p.get("moving"))
    sm.add_transition("run",  "idle", condition=lambda p: not p.get("moving"))
    sm.update(0.016)
    sm.update(0.016, params={"moving": True})
    assert sm.current_state == "run"
    sm.update(0.016, params={"moving": False})
    assert sm.current_state == "idle"


def test_any_state_transition():
    p  = make_player("idle", "run", "dead")
    sm = AnimationStateMachine(p)
    sm.add_state("idle", default=True)
    sm.add_state("run")
    sm.add_state("dead")
    sm.add_transition("*", "dead", condition=lambda p: p.get("dead"), priority=10)
    sm.update(0.016)
    sm.update(0.016, params={"dead": True})
    assert sm.current_state == "dead"


def test_priority_respected():
    p  = make_player("idle", "run", "sprint")
    sm = AnimationStateMachine(p)
    sm.add_state("idle", default=True)
    sm.add_state("run")
    sm.add_state("sprint")
    sm.add_transition("idle", "run",    condition=lambda p: True, priority=1)
    sm.add_transition("idle", "sprint", condition=lambda p: True, priority=5)
    sm.update(0.016)
    sm.update(0.016)
    assert sm.current_state == "sprint"   # higher priority wins


def test_force_state():
    p  = make_player("idle", "run")
    sm = AnimationStateMachine(p)
    sm.add_state("idle", default=True)
    sm.add_state("run")
    sm.update(0.016)
    sm.force("run")
    assert sm.current_state == "run"


def test_force_unknown_state_raises():
    sm = AnimationStateMachine(make_player("idle"))
    sm.add_state("idle", default=True)
    with pytest.raises(KeyError):
        sm.force("nonexistent")


def test_is_in():
    sm = AnimationStateMachine(make_player("idle"))
    sm.add_state("idle", default=True)
    sm.update(0.016)
    assert sm.is_in("idle") is True


def test_on_enter_callback_fires():
    entered: list[str] = []
    sm = AnimationStateMachine(make_player("idle", "run"))
    sm.add_state("idle", default=True)
    sm.add_state("run", on_enter=lambda: entered.append("run"))
    sm.add_transition("idle", "run", condition=lambda p: True)
    sm.update(0.016)
    sm.update(0.016)
    assert "run" in entered


def test_on_exit_callback_fires():
    exited: list[str] = []
    sm = AnimationStateMachine(make_player("idle", "run"))
    sm.add_state("idle", default=True, on_exit=lambda: exited.append("idle"))
    sm.add_state("run")
    sm.add_transition("idle", "run", condition=lambda p: True)
    sm.update(0.016)
    sm.update(0.016)
    assert "idle" in exited


def test_bad_condition_does_not_crash():
    sm = AnimationStateMachine(make_player("idle", "run"))
    sm.add_state("idle", default=True)
    sm.add_state("run")
    sm.add_transition("idle", "run", condition=lambda p: 1 / 0)   # will raise
    sm.update(0.016)   # should not raise
    assert sm.current_state == "idle"


def test_player_driven_by_state_machine():
    p  = make_player("idle", "run")
    sm = AnimationStateMachine(p)
    sm.add_state("idle", default=True)
    sm.add_state("run")
    sm.add_transition("idle", "run", condition=lambda _: True)
    sm.update(0.016)
    sm.update(0.016)
    assert p.current_animation == "run"


def test_repr():
    sm = AnimationStateMachine(make_player("idle"))
    sm.add_state("idle", default=True)
    assert "AnimationStateMachine" in repr(sm)
