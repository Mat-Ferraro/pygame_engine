import pygame

from pygame_engine.scene import Scene, SceneStack


class RecordingScene(Scene):
    def __init__(
        self,
        name: str,
        *,
        consume_event: bool = False,
        blocks_input_below: bool = True,
        blocks_update_below: bool = True,
        blocks_render_below: bool = True,
    ) -> None:
        super().__init__()
        self.name = name
        self.consume_event = consume_event
        self.blocks_input_below = blocks_input_below
        self.blocks_update_below = blocks_update_below
        self.blocks_render_below = blocks_render_below

        self.events_handled: list[str] = []
        self.update_calls: list[float] = []
        self.render_calls: int = 0

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        self.events_handled.append(self.name)
        return self.consume_event

    def update(self, dt: float) -> None:
        self.update_calls.append(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.render_calls += 1


def test_handle_event_routes_top_to_bottom_until_consumed() -> None:
    stack = SceneStack()
    bottom = RecordingScene("bottom", blocks_input_below=False)
    middle = RecordingScene("middle", consume_event=True, blocks_input_below=False)
    top = RecordingScene("top", blocks_input_below=False)

    stack.push(bottom)
    stack.push(middle)
    stack.push(top)

    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
    consumed = stack.handle_event(event)

    assert consumed is True
    assert top.events_handled == ["top"]
    assert middle.events_handled == ["middle"]
    assert bottom.events_handled == []


def test_handle_event_stops_when_scene_blocks_input_below() -> None:
    stack = SceneStack()
    bottom = RecordingScene("bottom", blocks_input_below=False)
    top = RecordingScene("top", consume_event=False, blocks_input_below=True)

    stack.push(bottom)
    stack.push(top)

    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
    consumed = stack.handle_event(event)

    assert consumed is False
    assert top.events_handled == ["top"]
    assert bottom.events_handled == []


def test_update_stops_below_blocking_scene() -> None:
    stack = SceneStack()
    bottom = RecordingScene("bottom", blocks_update_below=False)
    middle = RecordingScene("middle", blocks_update_below=True)
    top = RecordingScene("top", blocks_update_below=False)

    stack.push(bottom)
    stack.push(middle)
    stack.push(top)

    stack.update(0.25)

    assert top.update_calls == [0.25]
    assert middle.update_calls == [0.25]
    assert bottom.update_calls == []


def test_render_starts_from_lowest_visible_scene(display_surface: pygame.Surface) -> None:
    stack = SceneStack()
    bottom = RecordingScene("bottom", blocks_render_below=True)
    middle = RecordingScene("middle", blocks_render_below=False)
    top = RecordingScene("top", blocks_render_below=False)

    stack.push(bottom)
    stack.push(middle)
    stack.push(top)

    stack.render(display_surface)

    assert bottom.render_calls == 1
    assert middle.render_calls == 1
    assert top.render_calls == 1


def test_render_skips_scenes_hidden_by_blocking_render_scene(display_surface: pygame.Surface) -> None:
    stack = SceneStack()
    hidden_bottom = RecordingScene("hidden_bottom", blocks_render_below=False)
    visible_base = RecordingScene("visible_base", blocks_render_below=True)
    top = RecordingScene("top", blocks_render_below=False)

    stack.push(hidden_bottom)
    stack.push(visible_base)
    stack.push(top)

    stack.render(display_surface)

    assert hidden_bottom.render_calls == 0
    assert visible_base.render_calls == 1
    assert top.render_calls == 1
