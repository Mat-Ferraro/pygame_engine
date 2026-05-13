"""
tests/test_input_field.py

Tests for pygame_engine.ui.controls.InputField.

Covers: text insertion, backspace, delete, cursor movement, max_length,
callbacks, focus/unfocus, placeholder, password masking.

Note: TEXTINPUT events cannot be simulated in headless tests the same way
as KEYDOWN events. Character insertion is tested via the _insert() method
directly; TEXTINPUT event routing is covered by integration tests / manual
testing.
"""

import pygame

from pygame_engine.ui.controls.input_field import InputField

RECT = pygame.Rect(0, 0, 300, 42)


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_text() -> None:
    f = InputField(RECT, text="hello")
    assert f.text == "hello"


def test_initial_cursor_at_end() -> None:
    f = InputField(RECT, text="hello")
    assert f._cursor_pos == 5


def test_empty_by_default() -> None:
    f = InputField(RECT)
    assert f.text == ""


# ── Text insertion ────────────────────────────────────────────────────────────

def test_insert_appends_characters() -> None:
    f = InputField(RECT)
    f._insert("abc")
    assert f.text == "abc"
    assert f._cursor_pos == 3


def test_insert_at_cursor_middle() -> None:
    f = InputField(RECT, text="ac")
    f._cursor_pos = 1
    f._insert("b")
    assert f.text == "abc"
    assert f._cursor_pos == 2


def test_max_length_respected() -> None:
    f = InputField(RECT, max_length=3)
    f._insert("abcde")
    assert f.text == "abc"
    assert len(f.text) == 3


# ── Backspace and delete ──────────────────────────────────────────────────────

def test_backspace_removes_char_before_cursor() -> None:
    f = InputField(RECT, text="hello")
    f._cursor_pos = 5
    f._backspace()
    assert f.text == "hell"
    assert f._cursor_pos == 4


def test_backspace_at_start_does_nothing() -> None:
    f = InputField(RECT, text="hi")
    f._cursor_pos = 0
    f._backspace()
    assert f.text == "hi"


def test_delete_forward_removes_char_after_cursor() -> None:
    f = InputField(RECT, text="hello")
    f._cursor_pos = 0
    f._delete_forward()
    assert f.text == "ello"
    assert f._cursor_pos == 0


def test_delete_forward_at_end_does_nothing() -> None:
    f = InputField(RECT, text="hi")
    f._cursor_pos = 2
    f._delete_forward()
    assert f.text == "hi"


# ── Cursor movement via key events ────────────────────────────────────────────

def test_left_arrow_moves_cursor_back() -> None:
    f = InputField(RECT, text="hello")
    f.focused = True
    f._cursor_pos = 3
    event = pygame.event.Event(pygame.KEYDOWN, {
        "key": pygame.K_LEFT, "mod": 0, "unicode": "", "scancode": 0
    })
    f._handle_key(event)
    assert f._cursor_pos == 2


def test_right_arrow_moves_cursor_forward() -> None:
    f = InputField(RECT, text="hello")
    f.focused = True
    f._cursor_pos = 2
    event = pygame.event.Event(pygame.KEYDOWN, {
        "key": pygame.K_RIGHT, "mod": 0, "unicode": "", "scancode": 0
    })
    f._handle_key(event)
    assert f._cursor_pos == 3


def test_left_arrow_clamped_at_zero() -> None:
    f = InputField(RECT, text="hi")
    f.focused = True
    f._cursor_pos = 0
    event = pygame.event.Event(pygame.KEYDOWN, {
        "key": pygame.K_LEFT, "mod": 0, "unicode": "", "scancode": 0
    })
    f._handle_key(event)
    assert f._cursor_pos == 0


def test_home_moves_cursor_to_start() -> None:
    f = InputField(RECT, text="hello")
    f.focused = True
    f._cursor_pos = 4
    event = pygame.event.Event(pygame.KEYDOWN, {
        "key": pygame.K_HOME, "mod": 0, "unicode": "", "scancode": 0
    })
    f._handle_key(event)
    assert f._cursor_pos == 0


def test_end_moves_cursor_to_end() -> None:
    f = InputField(RECT, text="hello")
    f.focused = True
    f._cursor_pos = 1
    event = pygame.event.Event(pygame.KEYDOWN, {
        "key": pygame.K_END, "mod": 0, "unicode": "", "scancode": 0
    })
    f._handle_key(event)
    assert f._cursor_pos == 5


# ── Callbacks ─────────────────────────────────────────────────────────────────

def test_on_change_fired_on_insert() -> None:
    changes: list[str] = []
    f = InputField(RECT, on_change=changes.append)
    f._insert("a")
    assert changes == ["a"]


def test_on_change_fired_on_backspace() -> None:
    changes: list[str] = []
    f = InputField(RECT, text="ab", on_change=changes.append)
    f._backspace()
    assert "a" in changes


def test_on_submit_fired_on_enter() -> None:
    submits: list[str] = []
    f = InputField(RECT, text="hello", on_submit=submits.append)
    f.focused = True
    event = pygame.event.Event(pygame.KEYDOWN, {
        "key": pygame.K_RETURN, "mod": 0, "unicode": "", "scancode": 0
    })
    f._handle_key(event)
    assert submits == ["hello"]


# ── Focus ─────────────────────────────────────────────────────────────────────

def test_not_focused_by_default() -> None:
    f = InputField(RECT)
    assert f.focused is False


def test_unfocused_field_ignores_key_events() -> None:
    f = InputField(RECT, text="hi")
    event = pygame.event.Event(pygame.KEYDOWN, {
        "key": pygame.K_BACKSPACE, "mod": 0, "unicode": "", "scancode": 0
    })
    consumed = f._handle_event_widget(event)
    assert consumed is False
    assert f.text == "hi"


# ── Misc ──────────────────────────────────────────────────────────────────────

def test_clear_resets_text_and_cursor() -> None:
    f = InputField(RECT, text="hello")
    f.clear()
    assert f.text == ""
    assert f._cursor_pos == 0


def test_text_setter_clamps_cursor() -> None:
    f = InputField(RECT, text="hello")
    f._cursor_pos = 5
    f.text = "hi"
    assert f._cursor_pos == 2


def test_placeholder_shown_when_empty_and_unfocused() -> None:
    f = InputField(RECT, placeholder="Type here...")
    assert f._display_text() == "Type here..."


def test_placeholder_hidden_when_focused() -> None:
    f = InputField(RECT, placeholder="Type here...")
    f.focused = True
    assert f._display_text() == ""


def test_password_masks_text() -> None:
    f = InputField(RECT, text="secret", password=True)
    assert f._display_text() == "••••••"


def test_password_mask_matches_length() -> None:
    f = InputField(RECT, text="abc", password=True)
    assert len(f._display_text()) == 3
