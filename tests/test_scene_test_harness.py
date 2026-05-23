"""Tests for SceneTestHarness."""

from __future__ import annotations
import pygame
import pytest
from pygame_engine.testing.scene_test_harness import SceneTestHarness
from pygame_engine.scene.scene import Scene


class CounterScene(Scene):
    """Simple scene that counts key presses and clicks."""

    def __init__(self) -> None:
        super().__init__()
        self.key_presses:  int = 0
        self.mouse_clicks: int = 0
        self.text_input:   str = ""
        self.frames:       int = 0
        self.entered:      bool = False
        self.exited:       bool = False

    def on_enter(self) -> None:
        self.entered = True

    def on_exit(self) -> None:
        self.exited = True

    def update(self, dt: float) -> None:
        self.frames += 1

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            self.key_presses += 1
            return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_clicks += 1
            return True
        if event.type == pygame.TEXTINPUT:
            self.text_input += event.text
            return True
        return False


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def test_enter_calls_on_enter() -> None:
    scene = CounterScene()
    h = SceneTestHarness(scene)
    h.enter()
    assert scene.entered is True
    h.exit()

def test_exit_calls_on_exit() -> None:
    scene = CounterScene()
    h = SceneTestHarness(scene)
    h.enter()
    h.exit()
    assert scene.exited is True

def test_enter_twice_is_noop() -> None:
    scene = CounterScene()
    h = SceneTestHarness(scene)
    h.enter()
    h.enter()   # second call should be noop
    h.exit()
    assert scene.entered is True

def test_context_manager_enters_and_exits() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        assert scene.entered is True
    assert scene.exited is True

def test_entered_property() -> None:
    scene = CounterScene()
    h = SceneTestHarness(scene)
    assert h.entered is False
    h.enter()
    assert h.entered is True
    h.exit()
    assert h.entered is False


# ── advance() ────────────────────────────────────────────────────────────────

def test_advance_calls_update() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        h.advance(frames=5)
    assert scene.frames == 5

def test_advance_default_one_frame() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        h.advance()
    assert scene.frames == 1

def test_advance_returns_self_for_chaining() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        result = h.advance(2)
        assert result is h


# ── Input simulation ──────────────────────────────────────────────────────────

def test_press_key_fires_keydown() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        h.press_key(pygame.K_SPACE)
    assert scene.key_presses == 1

def test_press_key_multiple() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        h.press_key(pygame.K_a)
        h.press_key(pygame.K_b)
        h.press_key(pygame.K_c)
    assert scene.key_presses == 3

def test_click_fires_mousebutton() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        h.click(100, 200)
    assert scene.mouse_clicks == 1

def test_type_text_sends_textinput() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        h.type_text("hello")
    assert scene.text_input == "hello"

def test_move_mouse_sends_event() -> None:
    """move_mouse should not raise; scene ignores it in this case."""
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        h.move_mouse(50, 50)   # must not raise

def test_scroll_sends_event() -> None:
    scene = CounterScene()
    with SceneTestHarness(scene) as h:
        h.scroll(3)   # must not raise


# ── find_widget() ─────────────────────────────────────────────────────────────

def test_find_widget_by_id() -> None:
    from pygame_engine.ui.controls.button import Button

    scene = CounterScene()
    btn = Button(pygame.Rect(0, 0, 80, 32), "OK")
    btn.widget_id = "ok_btn"

    class FakeContainer:
        def __init__(self):
            self._children = [btn]
        widget_id = None

    scene.root_widget = FakeContainer()
    with SceneTestHarness(scene) as h:
        found = h.find_widget("ok_btn")
    assert found is btn

def test_find_widget_not_found_raises() -> None:
    scene = CounterScene()
    scene.root_widget = None
    with SceneTestHarness(scene) as h:
        with pytest.raises(LookupError):
            h.find_widget("nonexistent")


# ── scene property ────────────────────────────────────────────────────────────

def test_scene_property_returns_scene() -> None:
    scene = CounterScene()
    h = SceneTestHarness(scene)
    assert h.scene is scene

def test_surface_property_is_pygame_surface() -> None:
    h = SceneTestHarness(CounterScene())
    assert isinstance(h.surface, pygame.Surface)


# ── Error handling in testing mode ───────────────────────────────────────────

def test_runtime_error_reraises_in_advance() -> None:
    class BrokenScene(Scene):
        def update(self, dt):
            raise ValueError("scene broke")

    with SceneTestHarness(BrokenScene()) as h:
        with pytest.raises(ValueError, match="scene broke"):
            h.advance()


# ── Repr ──────────────────────────────────────────────────────────────────────

def test_repr() -> None:
    h = SceneTestHarness(CounterScene())
    assert "CounterScene" in repr(h)
    assert "idle" in repr(h)
    h.enter()
    assert "active" in repr(h)
    h.exit()
