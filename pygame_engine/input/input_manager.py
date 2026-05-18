"""
Key remapping
-------------
Use ``remap(action, key)`` to change a keyboard binding at runtime.
Use ``bindings_to_dict()`` / ``bindings_from_dict()`` to persist bindings.

Controller support
------------------
Controllers are detected automatically via ``JOYDEVICEADDED`` events.
Axes produce both ``is_axis_down(action)`` (threshold-crossed) and
``get_axis(joystick_id, axis_index)`` (raw float) queries.
"""

from __future__ import annotations

import pygame

from pygame_engine.input.bindings import (
    DEFAULT_BINDINGS,
    DEFAULT_CONTROLLER_BINDINGS,
    key_name,
)


class ControllerConfig:
    """
    Per-joystick axis configuration.

    Args:
        dead_zone:      Axis values below this magnitude are treated as 0.
        axis_nav_up:    Axis index + negative direction maps to NAV_UP.
        axis_nav_down:  Axis index + positive direction maps to NAV_DOWN.
        axis_nav_left:  Axis index + negative direction maps to NAV_LEFT.
        axis_nav_right: Axis index + positive direction maps to NAV_RIGHT.
        threshold:      Axis magnitude to trigger an action. Default 0.5.
    """

    def __init__(
        self,
        dead_zone:      float = 0.15,
        left_x_axis:    int   = 0,
        left_y_axis:    int   = 1,
        threshold:      float = 0.5,
    ) -> None:
        self.dead_zone   = dead_zone
        self.left_x_axis = left_x_axis
        self.left_y_axis = left_y_axis
        self.threshold   = threshold


class InputManager:
    """
    Tracks per-frame input state and resolves action queries.

    Owned by Application. Updated once per frame via ``update(events)``
    before any scene or widget processes input.

    Supports keyboard, mouse, and up to 4 simultaneous controllers.
    """

    def __init__(
        self,
        bindings:            dict[int, str] | None = None,
        controller_bindings: dict[int, str] | None = None,
        controller_config:   ControllerConfig | None = None,
    ) -> None:
        self._bindings:            dict[int, str] = (
            dict(bindings) if bindings is not None else dict(DEFAULT_BINDINGS)
        )
        self._ctrl_bindings:       dict[int, str] = (
            dict(controller_bindings)
            if controller_bindings is not None
            else dict(DEFAULT_CONTROLLER_BINDINGS)
        )
        self._ctrl_config = controller_config or ControllerConfig()

        # ── Keyboard ──────────────────────────────────────────────────────────
        self._keys_down:     set[int] = set()
        self._keys_pressed:  set[int] = set()
        self._keys_released: set[int] = set()

        # ── Mouse ─────────────────────────────────────────────────────────────
        self._mouse_pos:      tuple[int, int] = (0, 0)
        self._mouse_prev_pos: tuple[int, int] = (0, 0)
        self._mouse_down:     set[int] = set()
        self._mouse_pressed:  set[int] = set()
        self._mouse_released: set[int] = set()
        self._wheel_delta:    tuple[int, int] = (0, 0)

        # ── Controller ────────────────────────────────────────────────────────
        self._joysticks:          dict[int, pygame.joystick.JoystickType] = {}
        self._ctrl_down:          set[tuple[int,int]] = set()   # (joy_id, button)
        self._ctrl_pressed:       set[tuple[int,int]] = set()
        self._ctrl_released:      set[tuple[int,int]] = set()
        self._ctrl_axes:          dict[tuple[int,int], float] = {}  # (joy_id, axis)
        self._ctrl_axis_actions_down:     set[str] = set()
        self._ctrl_axis_actions_pressed:  set[str] = set()
        self._ctrl_axis_actions_released: set[str] = set()
        self._ctrl_axis_actions_prev:     set[str] = set()

        # Initialise any already-connected joysticks
        pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            self._joysticks[joy.get_instance_id()] = joy

    # ── Frame update ──────────────────────────────────────────────────────────

    def update(self, events: list[pygame.event.Event]) -> None:
        """Process the event list for this frame."""
        # Clear one-frame transient state
        self._keys_pressed.clear()
        self._keys_released.clear()
        self._mouse_pressed.clear()
        self._mouse_released.clear()
        self._mouse_prev_pos = self._mouse_pos
        self._wheel_delta    = (0, 0)
        self._ctrl_pressed.clear()
        self._ctrl_released.clear()
        self._ctrl_axis_actions_prev     = set(self._ctrl_axis_actions_down)
        self._ctrl_axis_actions_down     = set()
        self._ctrl_axis_actions_pressed  = set()
        self._ctrl_axis_actions_released = set()

        for event in events:
            # ── Keyboard ──────────────────────────────────────────────────────
            if event.type == pygame.KEYDOWN:
                self._keys_pressed.add(event.key)
                self._keys_down.add(event.key)
            elif event.type == pygame.KEYUP:
                self._keys_released.add(event.key)
                self._keys_down.discard(event.key)

            # ── Mouse ─────────────────────────────────────────────────────────
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

            # ── Controller hot-plug ───────────────────────────────────────────
            elif event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                joy.init()
                self._joysticks[joy.get_instance_id()] = joy
            elif event.type == pygame.JOYDEVICEREMOVED:
                self._joysticks.pop(event.instance_id, None)

            # ── Controller buttons ────────────────────────────────────────────
            elif event.type == pygame.JOYBUTTONDOWN:
                key = (event.instance_id, event.button)
                self._ctrl_pressed.add(key)
                self._ctrl_down.add(key)
            elif event.type == pygame.JOYBUTTONUP:
                key = (event.instance_id, event.button)
                self._ctrl_released.add(key)
                self._ctrl_down.discard(key)

            # ── Controller axes ───────────────────────────────────────────────
            elif event.type == pygame.JOYAXISMOTION:
                value = event.value
                if abs(value) < self._ctrl_config.dead_zone:
                    value = 0.0
                self._ctrl_axes[(event.instance_id, event.axis)] = value

        # Resolve axis → actions
        self._update_axis_actions()

    def _update_axis_actions(self) -> None:
        cfg = self._ctrl_config
        thr = cfg.threshold
        # Collect all joystick IDs that have reported axis data, plus any
        # registered joysticks.  This lets synthetic test events work even
        # when no real JOYDEVICEADDED event has fired.
        axis_joy_ids = {joy_id for joy_id, _ in self._ctrl_axes}
        all_joy_ids  = axis_joy_ids | set(self._joysticks.keys())
        from pygame_engine.input import actions
        for joy_id in all_joy_ids:
            x = self._ctrl_axes.get((joy_id, cfg.left_x_axis), 0.0)
            y = self._ctrl_axes.get((joy_id, cfg.left_y_axis), 0.0)
            if y < -thr: self._ctrl_axis_actions_down.add(actions.NAV_UP)
            if y >  thr: self._ctrl_axis_actions_down.add(actions.NAV_DOWN)
            if x < -thr: self._ctrl_axis_actions_down.add(actions.NAV_LEFT)
            if x >  thr: self._ctrl_axis_actions_down.add(actions.NAV_RIGHT)

        for action in self._ctrl_axis_actions_down:
            if action not in self._ctrl_axis_actions_prev:
                self._ctrl_axis_actions_pressed.add(action)
        for action in self._ctrl_axis_actions_prev:
            if action not in self._ctrl_axis_actions_down:
                self._ctrl_axis_actions_released.add(action)

    # ── Action queries ────────────────────────────────────────────────────────

    def was_action_pressed(self, action: str) -> bool:
        """True if the action was triggered this frame (keyboard or controller)."""
        key_hit  = any(self._bindings.get(k) == action for k in self._keys_pressed)
        ctrl_hit = any(self._ctrl_bindings.get(b) == action
                       for _, b in self._ctrl_pressed)
        axis_hit = action in self._ctrl_axis_actions_pressed
        return key_hit or ctrl_hit or axis_hit

    def was_action_released(self, action: str) -> bool:
        """True if the action was released this frame."""
        key_hit  = any(self._bindings.get(k) == action for k in self._keys_released)
        ctrl_hit = any(self._ctrl_bindings.get(b) == action
                       for _, b in self._ctrl_released)
        axis_hit = action in self._ctrl_axis_actions_released
        return key_hit or ctrl_hit or axis_hit

    def is_action_down(self, action: str) -> bool:
        """True if the action is currently held (keyboard or controller)."""
        key_hit  = any(self._bindings.get(k) == action for k in self._keys_down)
        ctrl_hit = any(self._ctrl_bindings.get(b) == action
                       for _, b in self._ctrl_down)
        axis_hit = action in self._ctrl_axis_actions_down
        return key_hit or ctrl_hit or axis_hit

    # ── Direct key queries ────────────────────────────────────────────────────

    def is_key_down(self, key: int) -> bool:
        """Return True while the key is held down."""
        return key in self._keys_down

    def was_key_pressed(self, key: int) -> bool:
        """Return True on the first frame the key was pressed."""
        return key in self._keys_pressed

    def was_key_released(self, key: int) -> bool:
        """Return True on the first frame the key was released."""
        return key in self._keys_released

    # ── Mouse queries ─────────────────────────────────────────────────────────

    def get_mouse_pos(self) -> tuple[int, int]:
        """Return the current mouse position as (x, y)."""
        return self._mouse_pos

    def get_mouse_delta(self) -> tuple[int, int]:
        """Return the mouse movement since the last frame as (dx, dy)."""
        px, py = self._mouse_prev_pos
        cx, cy = self._mouse_pos
        return (cx - px, cy - py)

    def was_mouse_pressed(self, button: int = 1) -> bool:
        """Return True on the first frame the mouse button was pressed."""
        return button in self._mouse_pressed

    def was_mouse_released(self, button: int = 1) -> bool:
        """Return True on the first frame the mouse button was released."""
        return button in self._mouse_released

    def is_mouse_down(self, button: int = 1) -> bool:
        """Return True while the mouse button is held."""
        return button in self._mouse_down

    def get_wheel_delta(self) -> tuple[int, int]:
        """Return the scroll wheel delta as (horizontal, vertical)."""
        return self._wheel_delta

    # ── Controller queries ────────────────────────────────────────────────────

    @property
    def controller_count(self) -> int:
        """Number of currently connected controllers."""
        return len(self._joysticks)

    @property
    def has_controller(self) -> bool:
        """True if at least one controller is connected."""
        return len(self._joysticks) > 0

    def get_axis(self, joystick_id: int, axis: int) -> float:
        """
        Return the raw (dead-zone-filtered) value of a joystick axis.

        Returns 0.0 if the joystick or axis is not present.
        """
        return self._ctrl_axes.get((joystick_id, axis), 0.0)

    def was_controller_button_pressed(self, button: int,
                                       joystick_id: int | None = None) -> bool:
        """
        True if a controller button was pressed this frame.

        Args:
            button:      Button index.
            joystick_id: Specific joystick instance ID, or None = any.
        """
        if joystick_id is not None:
            return (joystick_id, button) in self._ctrl_pressed
        return any(b == button for _, b in self._ctrl_pressed)

    def is_controller_button_down(self, button: int,
                                   joystick_id: int | None = None) -> bool:
        """Return True while the given controller button is held."""
        if joystick_id is not None:
            return (joystick_id, button) in self._ctrl_down
        return any(b == button for _, b in self._ctrl_down)

    def get_controller_name(self, joystick_id: int) -> str:
        """Return the name of a connected controller, or empty string."""
        joy = self._joysticks.get(joystick_id)
        return joy.get_name() if joy else ""

    def get_joystick_ids(self) -> list[int]:
        """Return instance IDs of all connected joysticks."""
        return list(self._joysticks.keys())

    # ── Key remapping ─────────────────────────────────────────────────────────

    def remap(self, action: str, key: int) -> None:
        """
        Bind a keyboard key to an action, removing any existing binding for
        that key first.

        Args:
            action: The action string to bind to.
            key:    The pygame key constant to bind.
        """
        # Remove old binding for this key if any
        self._bindings.pop(key, None)
        # Remove other keys that were bound to the same action (optional:
        # allow multiple keys per action by commenting this out)
        old_keys = [k for k, a in self._bindings.items() if a == action]
        for k in old_keys:
            del self._bindings[k]
        self._bindings[key] = action

    def remap_controller(self, action: str, button: int) -> None:
        """Bind a controller button to an action."""
        old_btns = [b for b, a in self._ctrl_bindings.items() if a == action]
        for b in old_btns:
            del self._ctrl_bindings[b]
        self._ctrl_bindings[button] = action

    def get_key_for_action(self, action: str) -> int | None:
        """Return the keyboard key currently bound to an action, or None."""
        for key, act in self._bindings.items():
            if act == action:
                return key
        return None

    def get_button_for_action(self, action: str) -> int | None:
        """Return the controller button bound to an action, or None."""
        for btn, act in self._ctrl_bindings.items():
            if act == action:
                return btn
        return None

    # ── Serialisation ─────────────────────────────────────────────────────────

    def bindings_to_dict(self) -> dict:
        """
        Serialise current keyboard bindings for persistence.

        Returns a JSON-serialisable dict. Pass to ``bindings_from_dict()``
        to restore.
        """
        return {
            "keyboard": {str(k): v for k, v in self._bindings.items()},
            "controller": {str(k): v for k, v in self._ctrl_bindings.items()},
        }

    def bindings_from_dict(self, data: dict) -> None:
        """
        Restore bindings from a previously serialised dict.

        Args:
            data: Dict produced by ``bindings_to_dict()``.
        """
        if "keyboard" in data:
            self._bindings = {int(k): v for k, v in data["keyboard"].items()}
        if "controller" in data:
            self._ctrl_bindings = {int(k): v
                                   for k, v in data["controller"].items()}

    def reset_to_defaults(self) -> None:
        """Restore all bindings to their defaults."""
        self._bindings      = dict(DEFAULT_BINDINGS)
        self._ctrl_bindings = dict(DEFAULT_CONTROLLER_BINDINGS)

    # ── Haptic feedback ──────────────────────────────────────────────────────

    def rumble(
        self,
        low:         float = 0.5,
        high:        float = 0.5,
        duration_ms: int   = 200,
        joystick_id: int | None = None,
    ) -> None:
        """
        Trigger rumble on connected controller(s).

        Args:
            low:         Low-frequency motor intensity [0.0, 1.0].
                         Typically felt as a deep, heavy rumble.
            high:        High-frequency motor intensity [0.0, 1.0].
                         Typically felt as a sharp, buzzing vibration.
            duration_ms: Duration in milliseconds.
            joystick_id: Specific joystick instance ID, or None = all.
        """
        targets = (
            [self._joysticks[joystick_id]]
            if joystick_id is not None and joystick_id in self._joysticks
            else list(self._joysticks.values())
        )
        for joy in targets:
            try:
                joy.rumble(low, high, duration_ms)
            except Exception:
                pass   # controller does not support rumble — silent

    def stop_rumble(self, joystick_id: int | None = None) -> None:
        """
        Stop rumble on connected controller(s) immediately.

        Args:
            joystick_id: Specific joystick instance ID, or None = all.
        """
        targets = (
            [self._joysticks[joystick_id]]
            if joystick_id is not None and joystick_id in self._joysticks
            else list(self._joysticks.values())
        )
        for joy in targets:
            try:
                joy.stop_rumble()
            except Exception:
                pass

    # ── Existing bindings property ────────────────────────────────────────────

    @property
    def bindings(self) -> dict[int, str]:
        """Return the current action-to-key bindings dict."""
        return self._bindings

    @bindings.setter
    def bindings(self, value: dict[int, str]) -> None:
        """Return the current action-to-key bindings dict."""
        self._bindings = value

    @property
    def controller_bindings(self) -> dict[int, str]:
        """Return the current action-to-controller-button bindings dict."""
        return self._ctrl_bindings

    @controller_bindings.setter
    def controller_bindings(self, value: dict[int, str]) -> None:
        """Return the current action-to-controller-button bindings dict."""
        self._ctrl_bindings = value