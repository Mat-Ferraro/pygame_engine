"""
input/input_manager.py

Per-frame input state and action query API for pygame_engine.

InputManager receives the already-polled event list from Application each
frame, updates its internal state, and exposes clean query methods to
scenes and widgets.

Frame semantics (stable contract — many systems depend on this):
- ``was_pressed``  : key/button became active THIS frame only
- ``was_released`` : key/button stopped being active THIS frame only
- ``is_down``      : key/button is currently held (includes the press frame)

Mouse buttons use the same three-state model.
Mouse position and delta are updated every frame from MOUSEMOTION events.
Wheel delta is accumulated per frame and cleared at the start of the next.

Text input is NOT supported in v1. Deferred — text input is a distinct
mode (chat boxes, name entry) that warrants its own handling later.

Usage (from a scene or widget)::

    # Action queries
    if input.was_action_pressed(actions.CONFIRM):
        self._on_confirm()

    if input.is_action_down(actions.NAV_UP):
        self._scroll_up(dt)

    # Direct key queries
    if input.is_key_down(pygame.K_LSHIFT):
        ...

    # Mouse queries
    pos = input.get_mouse_pos()
    if input.was_mouse_pressed(1):   # 1 = left button
        ...
"""

from __future__ import annotations

import pygame

from pygame_engine.input.bindings import DEFAULT_BINDINGS


class InputManager:
    """
    Tracks per-frame input state and resolves action queries.

    Owned by Application. Updated once per frame via ``update(events)``
    before any scene or widget processes input.

    Direct references are safe to pass to scenes; the state updates
    in-place each frame so callers always see the current frame's values.
    """

    def __init__(self, bindings: dict[int, str] | None = None) -> None:
        """
        Args:
            bindings: Key-to-action mapping. Defaults to DEFAULT_BINDINGS.
                      Pass a custom dict to override defaults, or merge with
                      DEFAULT_BINDINGS to extend them.
        """
        self._bindings: dict[int, str] = bindings if bindings is not None \
            else DEFAULT_BINDINGS

        # ── Keyboard state ────────────────────────────────────────────────────
        self._keys_down:     set[int] = set()   # currently held keys
        self._keys_pressed:  set[int] = set()   # became active this frame
        self._keys_released: set[int] = set()   # became inactive this frame

        # ── Mouse state ───────────────────────────────────────────────────────
        self._mouse_pos:      tuple[int, int] = (0, 0)
        self._mouse_prev_pos: tuple[int, int] = (0, 0)

        self._mouse_down:     set[int] = set()  # currently held buttons
        self._mouse_pressed:  set[int] = set()  # pressed this frame
        self._mouse_released: set[int] = set()  # released this frame

        self._wheel_delta: tuple[int, int] = (0, 0)   # (x, y) this frame

    # ── Frame update ──────────────────────────────────────────────────────────

    def update(self, events: list[pygame.event.Event]) -> None:
        """
        Process the event list for this frame and update all input state.

        Called once per frame by Application before any scene or widget
        receives events. Clears one-frame transient state (pressed, released,
        wheel delta) then processes each event in order.

        Args:
            events: The list returned by ``pygame.event.get()`` this frame.
        """
        # Clear one-frame transient state
        self._keys_pressed.clear()
        self._keys_released.clear()
        self._mouse_pressed.clear()
        self._mouse_released.clear()
        self._mouse_prev_pos = self._mouse_pos
        self._wheel_delta = (0, 0)

        for event in events:
            if event.type == pygame.KEYDOWN:
                self._keys_pressed.add(event.key)
                self._keys_down.add(event.key)

            elif event.type == pygame.KEYUP:
                self._keys_released.add(event.key)
                self._keys_down.discard(event.key)

            elif event.type == pygame.MOUSEMOTION:
                self._mouse_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._mouse_pressed.add(event.button)
                self._mouse_down.add(event.button)

            elif event.type == pygame.MOUSEBUTTONUP:
                self._mouse_released.add(event.button)
                self._mouse_down.discard(event.button)

            elif event.type == pygame.MOUSEWHEEL:
                self._wheel_delta = (event.x, event.y)

    # ── Action queries ────────────────────────────────────────────────────────

    def was_action_pressed(self, action: str) -> bool:
        """
        Return True if the action's bound key was pressed this frame.

        Args:
            action: An action string from ``input.actions``.
        """
        return any(
            self._bindings.get(key) == action
            for key in self._keys_pressed
        )

    def was_action_released(self, action: str) -> bool:
        """
        Return True if the action's bound key was released this frame.

        Args:
            action: An action string from ``input.actions``.
        """
        return any(
            self._bindings.get(key) == action
            for key in self._keys_released
        )

    def is_action_down(self, action: str) -> bool:
        """
        Return True if any key bound to the action is currently held.

        Args:
            action: An action string from ``input.actions``.
        """
        return any(
            self._bindings.get(key) == action
            for key in self._keys_down
        )

    # ── Direct key queries ────────────────────────────────────────────────────

    def is_key_down(self, key: int) -> bool:
        """
        Return True if the given pygame key is currently held.

        Args:
            key: A pygame key constant, e.g. ``pygame.K_LSHIFT``.
        """
        return key in self._keys_down

    def was_key_pressed(self, key: int) -> bool:
        """
        Return True if the given pygame key was pressed this frame.

        Args:
            key: A pygame key constant.
        """
        return key in self._keys_pressed

    def was_key_released(self, key: int) -> bool:
        """
        Return True if the given pygame key was released this frame.

        Args:
            key: A pygame key constant.
        """
        return key in self._keys_released

    # ── Mouse queries ─────────────────────────────────────────────────────────

    def get_mouse_pos(self) -> tuple[int, int]:
        """Return the current mouse cursor position in screen coordinates."""
        return self._mouse_pos

    def get_mouse_delta(self) -> tuple[int, int]:
        """
        Return how far the mouse moved since the previous frame.

        Returns:
            (dx, dy) tuple. Both zero if the mouse did not move.
        """
        px, py = self._mouse_prev_pos
        cx, cy = self._mouse_pos
        return (cx - px, cy - py)

    def was_mouse_pressed(self, button: int = 1) -> bool:
        """
        Return True if the given mouse button was pressed this frame.

        Args:
            button: 1 = left, 2 = middle, 3 = right.
        """
        return button in self._mouse_pressed

    def was_mouse_released(self, button: int = 1) -> bool:
        """
        Return True if the given mouse button was released this frame.

        Args:
            button: 1 = left, 2 = middle, 3 = right.
        """
        return button in self._mouse_released

    def is_mouse_down(self, button: int = 1) -> bool:
        """
        Return True if the given mouse button is currently held.

        Args:
            button: 1 = left, 2 = middle, 3 = right.
        """
        return button in self._mouse_down

    def get_wheel_delta(self) -> tuple[int, int]:
        """
        Return the mouse wheel movement this frame.

        Returns:
            (x, y) where y > 0 is scroll up, y < 0 is scroll down.
            Both zero if the wheel did not move this frame.
        """
        return self._wheel_delta

    # ── Rebinding ─────────────────────────────────────────────────────────────

    @property
    def bindings(self) -> dict[int, str]:
        """The current key-to-action binding map."""
        return self._bindings

    @bindings.setter
    def bindings(self, value: dict[int, str]) -> None:
        """Replace the binding map. Takes effect from the next frame."""
        self._bindings = value
