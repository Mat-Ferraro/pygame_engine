"""
tests/test_scene_manager.py

Tests for pygame_engine.scene.SceneManager.

Covers: push/pop/replace/clear_and_push lifecycle hook ordering.
"""

from pygame_engine.scene import Scene, SceneManager


class LifecycleScene(Scene):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.calls: list[str] = []

    def on_enter(self)  -> None: self.calls.append("enter")
    def on_exit(self)   -> None: self.calls.append("exit")
    def on_pause(self)  -> None: self.calls.append("pause")
    def on_resume(self) -> None: self.calls.append("resume")


def test_push_pauses_previous_scene_and_enters_new_scene() -> None:
    manager = SceneManager()
    first  = LifecycleScene("first")
    second = LifecycleScene("second")

    manager.push(first)
    manager.push(second)

    assert first.calls  == ["enter", "pause"]
    assert second.calls == ["enter"]
    assert manager.current_scene is second


def test_pop_exits_top_scene_and_resumes_scene_below() -> None:
    manager = SceneManager()
    first  = LifecycleScene("first")
    second = LifecycleScene("second")

    manager.push(first)
    manager.push(second)
    removed = manager.pop()

    assert removed is second
    assert second.calls == ["enter", "exit"]
    assert first.calls  == ["enter", "pause", "resume"]
    assert manager.current_scene is first


def test_pop_empty_stack_returns_none() -> None:
    manager = SceneManager()
    assert manager.pop() is None


def test_replace_exits_old_scene_and_enters_new_without_resuming_below() -> None:
    manager  = SceneManager()
    bottom   = LifecycleScene("bottom")
    old_top  = LifecycleScene("old_top")
    new_top  = LifecycleScene("new_top")

    manager.push(bottom)
    manager.push(old_top)
    removed = manager.replace(new_top)

    assert removed is old_top
    assert bottom.calls  == ["enter", "pause"]
    assert old_top.calls == ["enter", "exit"]
    assert new_top.calls == ["enter"]
    assert manager.current_scene is new_top


def test_clear_and_push_exits_stack_top_first_then_enters_new() -> None:
    manager  = SceneManager()
    bottom   = LifecycleScene("bottom")
    middle   = LifecycleScene("middle")
    new_root = LifecycleScene("new_root")

    manager.push(bottom)
    manager.push(middle)
    manager.clear_and_push(new_root)

    assert bottom.calls   == ["enter", "pause", "exit"]
    assert middle.calls   == ["enter", "exit"]
    assert new_root.calls == ["enter"]
    assert manager.current_scene is new_root


def test_is_empty_reflects_stack_state() -> None:
    manager = SceneManager()
    assert manager.is_empty is True

    scene = LifecycleScene("s")
    manager.push(scene)
    assert manager.is_empty is False

    manager.pop()
    assert manager.is_empty is True
