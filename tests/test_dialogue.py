"""
Tests for pygame_engine.dialogue: DialogueScript, DialogueRunner, DialogueBox.

Script and runner tests are fully headless (no pygame rendering needed).
DialogueBox tests use the display_surface fixture for render smoke tests.
"""

import pygame
import pytest

from pygame_engine.dialogue import (
    Choice,
    DialogueBox,
    DialogueNode,
    DialogueRunner,
    DialogueScript,
)


# ── Shared test scripts ───────────────────────────────────────────────────────

LINEAR_SCRIPT = {
    "start": {"speaker": "NPC",  "text": "Hello!", "next": "middle"},
    "middle": {"speaker": "NPC", "text": "How are you?", "next": "end"},
    "end":   {"text": ""},
}

BRANCHING_SCRIPT = {
    "start": {
        "speaker": "Guard",
        "text": "Who goes there?",
        "choices": [
            {"label": "A friend.", "next": "friendly"},
            {"label": "No one.",   "next": "hostile"},
        ]
    },
    "friendly": {"speaker": "Guard", "text": "Pass.",        "next": "done"},
    "hostile":  {"speaker": "Guard", "text": "Seize them!",  "next": "done"},
    "done":     {"text": ""},
}

ACTION_SCRIPT = {
    "start": {"text": "Enter.",  "action": "door_open",  "next": "end"},
    "end":   {"text": ""},
}

CHOICE_ACTION_SCRIPT = {
    "start": {
        "text": "Choose.",
        "choices": [
            {"label": "Good",  "next": "end", "action": "good_choice"},
            {"label": "Evil",  "next": "end", "action": "evil_choice"},
        ]
    },
    "end": {"text": ""},
}


# ══════════════════════════════════════════════════════════════════════════════
# DialogueScript
# ══════════════════════════════════════════════════════════════════════════════


# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    """Return a default RenderContext for render() calls in tests."""
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

def test_script_parses_nodes() -> None:
    s = DialogueScript(LINEAR_SCRIPT)
    assert s.has("start")
    assert s.has("middle")
    assert s.has("end")


def test_script_node_count() -> None:
    s = DialogueScript(LINEAR_SCRIPT)
    assert len(s.node_ids) == 3


def test_script_get_node() -> None:
    s    = DialogueScript(LINEAR_SCRIPT)
    node = s.get("start")
    assert node.text    == "Hello!"
    assert node.speaker == "NPC"
    assert node.next    == "middle"


def test_script_default_start_node() -> None:
    assert DialogueScript(LINEAR_SCRIPT).start_node == "start"


def test_script_custom_start_node() -> None:
    s = DialogueScript(LINEAR_SCRIPT, start_node="middle")
    assert s.start_node == "middle"


def test_script_missing_start_raises() -> None:
    with pytest.raises(ValueError, match="Start node"):
        DialogueScript(LINEAR_SCRIPT, start_node="nonexistent")


def test_script_missing_text_raises() -> None:
    with pytest.raises(ValueError, match="missing required 'text'"):
        DialogueScript({"start": {"speaker": "Bob"}})


def test_script_broken_next_raises() -> None:
    with pytest.raises(ValueError, match="unknown next node"):
        DialogueScript({"start": {"text": "Hi", "next": "nowhere"}})


def test_script_broken_choice_next_raises() -> None:
    bad = {
        "start": {
            "text": "Choose",
            "choices": [{"label": "Go", "next": "missing"}]
        }
    }
    with pytest.raises(ValueError, match="unknown node"):
        DialogueScript(bad)


def test_script_choices_parsed() -> None:
    s       = DialogueScript(BRANCHING_SCRIPT)
    node    = s.get("start")
    assert len(node.choices) == 2
    assert node.choices[0].label == "A friend."
    assert node.choices[0].next  == "friendly"


def test_script_get_missing_raises() -> None:
    s = DialogueScript(LINEAR_SCRIPT)
    with pytest.raises(KeyError):
        s.get("nonexistent")


def test_script_repr() -> None:
    assert "DialogueScript" in repr(DialogueScript(LINEAR_SCRIPT))


# ══════════════════════════════════════════════════════════════════════════════
# DialogueRunner
# ══════════════════════════════════════════════════════════════════════════════

def test_runner_not_started_initially() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    assert r.current_node is None
    assert r.is_complete  is False
    assert r.is_started   is False


def test_runner_start_sets_current_node() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    assert r.current_node is not None
    assert r.current_node.node_id == "start"


def test_runner_advance_moves_to_next() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    r.advance()
    assert r.current_node.node_id == "middle"


def test_runner_advance_to_end_completes() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    r.advance()   # start → middle
    r.advance()   # middle → end (empty, auto-completes)
    assert r.is_complete is True


def test_runner_advance_noop_when_complete() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    r.advance(); r.advance()
    assert r.is_complete
    r.advance()   # should not raise
    assert r.is_complete


def test_runner_advance_noop_when_not_started() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.advance()   # should not raise
    assert r.current_node is None


def test_runner_has_choices_true() -> None:
    r = DialogueRunner(DialogueScript(BRANCHING_SCRIPT))
    r.start()
    assert r.has_choices is True


def test_runner_has_choices_false_on_linear() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    assert r.has_choices is False


def test_runner_advance_noop_when_awaiting_choice() -> None:
    r = DialogueRunner(DialogueScript(BRANCHING_SCRIPT))
    r.start()
    r.advance()   # should be ignored — must choose
    assert r.current_node.node_id == "start"


def test_runner_select_choice_advances() -> None:
    r = DialogueRunner(DialogueScript(BRANCHING_SCRIPT))
    r.start()
    r.select_choice(0)   # "A friend." → "friendly"
    assert r.current_node.node_id == "friendly"


def test_runner_select_choice_branch_b() -> None:
    r = DialogueRunner(DialogueScript(BRANCHING_SCRIPT))
    r.start()
    r.select_choice(1)   # "No one." → "hostile"
    assert r.current_node.node_id == "hostile"


def test_runner_select_choice_out_of_range_raises() -> None:
    r = DialogueRunner(DialogueScript(BRANCHING_SCRIPT))
    r.start()
    with pytest.raises(ValueError):
        r.select_choice(99)


def test_runner_select_choice_without_choices_raises() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    with pytest.raises(ValueError):
        r.select_choice(0)


def test_runner_choices_property() -> None:
    r = DialogueRunner(DialogueScript(BRANCHING_SCRIPT))
    r.start()
    assert len(r.choices) == 2
    assert r.choices[0].label == "A friend."


def test_runner_on_complete_callback() -> None:
    fired: list[bool] = []
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.on_complete = lambda: fired.append(True)
    r.start()
    r.advance(); r.advance()
    assert fired == [True]


def test_runner_on_action_callback_on_node() -> None:
    tags: list[str] = []
    r = DialogueRunner(DialogueScript(ACTION_SCRIPT))
    r.on_action = lambda tag, node: tags.append(tag)
    r.start()
    assert "door_open" in tags


def test_runner_on_action_callback_on_choice() -> None:
    tags: list[str] = []
    r = DialogueRunner(DialogueScript(CHOICE_ACTION_SCRIPT))
    r.on_action = lambda tag, node: tags.append(tag)
    r.start()
    r.select_choice(0)
    assert "good_choice" in tags


def test_runner_on_node_enter_callback() -> None:
    ids: list[str] = []
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.on_node_enter = lambda node: ids.append(node.node_id)
    r.start()
    r.advance()
    assert ids[:2] == ["start", "middle"]


def test_runner_jump() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    r.jump("middle")
    assert r.current_node.node_id == "middle"


def test_runner_reset() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    r.advance(); r.advance()
    r.reset()
    assert r.current_node is None
    assert r.is_complete  is False
    assert r.is_started   is False


def test_runner_start_with_custom_node() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start(node_id="middle")
    assert r.current_node.node_id == "middle"


def test_runner_repr() -> None:
    r = DialogueRunner(DialogueScript(LINEAR_SCRIPT))
    r.start()
    assert "DialogueRunner" in repr(r)
    assert "start" in repr(r)


# ══════════════════════════════════════════════════════════════════════════════
# DialogueBox
# ══════════════════════════════════════════════════════════════════════════════

BOX_RECT = pygame.Rect(60, 400, 680, 180)


def make_box(script_raw=None, chars_per_sec=0.0):
    """Helper: box with instant text reveal by default."""
    raw    = script_raw or LINEAR_SCRIPT
    script = DialogueScript(raw)
    runner = DialogueRunner(script)
    box    = DialogueBox(
        rect=BOX_RECT,
        runner=runner,
        on_advance=lambda: runner.advance(),
        chars_per_sec=chars_per_sec,
    )
    runner.start()
    return box, runner


def test_box_not_revealing_with_instant_speed() -> None:
    box, _ = make_box(chars_per_sec=0.0)
    box.update(0.016)
    assert box.is_revealing is False


def test_box_is_revealing_with_slow_speed() -> None:
    box, _ = make_box(chars_per_sec=1.0)
    box.update(0.016)
    assert box.is_revealing is True


def test_box_complete_reveal_ends_typewriter() -> None:
    box, _ = make_box(chars_per_sec=1.0)
    box.update(0.016)
    box.complete_reveal()
    assert box.is_revealing is False


def test_box_confirm_key_completes_reveal_first() -> None:
    box, runner = make_box(chars_per_sec=1.0)
    box.update(0.016)
    assert box.is_revealing
    box.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                        {"key": pygame.K_SPACE, "mod": 0,
                                         "unicode": " ", "scancode": 0}))
    assert not box.is_revealing
    assert runner.current_node.node_id == "start"   # not yet advanced


def test_box_confirm_key_advances_when_text_revealed() -> None:
    box, runner = make_box(chars_per_sec=0.0)
    box.update(0.016)
    assert not box.is_revealing
    box.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                        {"key": pygame.K_SPACE, "mod": 0,
                                         "unicode": " ", "scancode": 0}))
    assert runner.current_node.node_id == "middle"


def test_box_number_key_selects_choice() -> None:
    box, runner = make_box(BRANCHING_SCRIPT, chars_per_sec=0.0)
    box.update(0.016)
    box.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                        {"key": pygame.K_1, "mod": 0,
                                         "unicode": "1", "scancode": 0}))
    assert runner.current_node.node_id == "friendly"


def test_box_render_does_not_raise(display_surface) -> None:
    box, _ = make_box()
    box.update(0.016)
    box.render(display_surface, _ctx())


def test_box_render_with_choices(display_surface) -> None:
    box, _ = make_box(BRANCHING_SCRIPT, chars_per_sec=0.0)
    box.update(0.016)
    box.render(display_surface, _ctx())


def test_box_invisible_skips_render(display_surface) -> None:
    box, _ = make_box()
    box.visible = False
    box.render(display_surface, _ctx())   # should not raise


def test_box_render_no_crash_when_runner_not_started(display_surface) -> None:
    script = DialogueScript(LINEAR_SCRIPT)
    runner = DialogueRunner(script)
    box    = DialogueBox(BOX_RECT, runner)
    box.render(display_surface, _ctx())   # runner not started — should be no-op


def test_box_node_change_resets_typewriter() -> None:
    box, runner = make_box(chars_per_sec=0.0)
    box.update(0.016)
    runner.advance()   # move to "middle"
    box._chars_per_sec = 1.0
    box.update(0.001)  # very short dt — should be revealing again
    assert box.is_revealing