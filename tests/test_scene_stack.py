

# ── Additional coverage ───────────────────────────────────────────────────────

def test_top_returns_none_on_empty_stack() -> None:
    from pygame_engine.scene.scene_stack import SceneStack
    stack = SceneStack()
    assert stack.top is None


def test_is_empty_true_on_empty_stack() -> None:
    from pygame_engine.scene.scene_stack import SceneStack
    stack = SceneStack()
    assert stack.is_empty is True


def test_is_empty_false_after_push() -> None:
    from pygame_engine.scene.scene_stack import SceneStack
    from pygame_engine.scene.scene import Scene
    stack = SceneStack()
    stack.push(Scene())
    assert stack.is_empty is False


def test_clear_returns_all_scenes_topmost_first() -> None:
    from pygame_engine.scene.scene_stack import SceneStack
    from pygame_engine.scene.scene import Scene
    stack  = SceneStack()
    s1, s2, s3 = Scene(), Scene(), Scene()
    stack.push(s1)
    stack.push(s2)
    stack.push(s3)
    removed = stack.clear()
    assert removed == [s3, s2, s1]
    assert stack.is_empty is True
