"""
tests/test_button.py

Tests for pygame_engine.ui.controls.Button.

Covers: click semantics, disabled state, hover/press state transitions.
"""

import pygame

from pygame_engine.ui.controls import Button


def test_click_fires_when_pressed_and_released_inside() -> None:
    clicks: list[str] = []
    button = Button(
        pygame.Rect(10, 10, 120, 40),
        "Click Me",
        on_click=lambda: clicks.append("clicked"),
    )

    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (20, 20), "button": 1})
    up   = pygame.event.Event(pygame.MOUSEBUTTONUP,   {"pos": (20, 20), "button": 1})

    consumed_down = button.handle_event(down)
    consumed_up   = button.handle_event(up)

    assert consumed_down is True
    assert consumed_up   is True
    assert clicks == ["clicked"]


def test_click_does_not_fire_when_released_outside() -> None:
    clicks: list[str] = []
    button = Button(
        pygame.Rect(10, 10, 120, 40),
        "Click Me",
        on_click=lambda: clicks.append("clicked"),
    )

    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (20, 20),   "button": 1})
    up   = pygame.event.Event(pygame.MOUSEBUTTONUP,   {"pos": (500, 500), "button": 1})

    button.handle_event(down)
    consumed_up = button.handle_event(up)

    assert consumed_up is False
    assert clicks == []


def test_disabled_button_never_fires() -> None:
    clicks: list[str] = []
    button = Button(
        pygame.Rect(10, 10, 120, 40),
        "Disabled",
        on_click=lambda: clicks.append("clicked"),
    )
    button.enabled = False

    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (20, 20), "button": 1})
    up   = pygame.event.Event(pygame.MOUSEBUTTONUP,   {"pos": (20, 20), "button": 1})

    assert button.handle_event(down) is False
    assert button.handle_event(up)   is False
    assert clicks == []


def test_hover_and_pressed_state_transitions() -> None:
    button = Button(pygame.Rect(10, 10, 120, 40), "State Test")

    move_inside  = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (20, 20),   "rel": (0, 0), "buttons": (0, 0, 0)})
    down         = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (20, 20),   "button": 1})
    up           = pygame.event.Event(pygame.MOUSEBUTTONUP,   {"pos": (20, 20),   "button": 1})
    move_outside = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (500, 500), "rel": (0, 0), "buttons": (0, 0, 0)})

    button.handle_event(move_inside)
    assert button.hovered is True

    button.handle_event(down)
    assert getattr(button, "_pressed_inside") is True

    button.handle_event(up)
    assert getattr(button, "_pressed_inside") is False

    button.handle_event(move_outside)
    assert button.hovered is False


def test_no_click_without_prior_press_inside() -> None:
    """Releasing without ever pressing inside should not fire on_click."""
    clicks: list[str] = []
    button = Button(
        pygame.Rect(10, 10, 120, 40),
        "No Press",
        on_click=lambda: clicks.append("clicked"),
    )

    # Release inside without any prior press
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (20, 20), "button": 1})
    consumed = button.handle_event(up)

    assert consumed is False
    assert clicks == []
