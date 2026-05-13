# Input System

## Purpose

Device-agnostic action-based input. Scenes query actions (`CONFIRM`,
`NAV_UP`, etc.) rather than physical keys. Keyboard, mouse, and
controllers all resolve to the same action strings.

---

## Quick start

```python
from pygame_engine.input import actions

# In a scene:
inp = self._app.input_manager

if inp.was_action_pressed(actions.CONFIRM):   ...
if inp.is_action_down(actions.NAV_LEFT):      ...
if inp.was_action_released(actions.CANCEL):   ...
```

---

## Actions

Actions are plain strings defined in `pygame_engine/input/actions.py`.

| Constant | String | Default keys |
|---|---|---|
| `CONFIRM` | `"confirm"` | Enter, Numpad Enter, Space |
| `CANCEL` | `"cancel"` | Escape |
| `NAV_UP` | `"nav_up"` | Up, W |
| `NAV_DOWN` | `"nav_down"` | Down, S |
| `NAV_LEFT` | `"nav_left"` | Left, A |
| `NAV_RIGHT` | `"nav_right"` | Right, D |
| `PAUSE` | `"pause"` | P |

Add game-specific actions in your game project:

```python
from pygame_engine.input.actions import CONFIRM, CANCEL
ATTACK   = "attack"
INTERACT = "interact"
DASH     = "dash"
```

Then remap them at startup or in settings:

```python
app.input_manager.remap("attack",   pygame.K_z)
app.input_manager.remap("interact", pygame.K_x)
```

---

## Keyboard

```python
# Action queries (device-agnostic — works for keyboard and controller)
inp.was_action_pressed(actions.CONFIRM)
inp.is_action_down(actions.NAV_LEFT)
inp.was_action_released(actions.CANCEL)

# Direct key queries
inp.is_key_down(pygame.K_LSHIFT)
inp.was_key_pressed(pygame.K_TAB)
```

---

## Mouse

```python
inp.get_mouse_pos()         # (x, y) screen coords
inp.get_mouse_delta()       # (dx, dy) since last frame
inp.was_mouse_pressed(1)    # 1=left, 2=middle, 3=right
inp.is_mouse_down(1)
inp.was_mouse_released(1)
inp.get_wheel_delta()       # (x, y); y>0 = scroll up
```

---

## Controller

Controllers are detected automatically when connected (hot-plug via
`JOYDEVICEADDED` events). All connected controllers contribute to
action queries.

```python
# Action queries work transparently for controllers too
inp.was_action_pressed(actions.CONFIRM)   # A button or Enter
inp.is_action_down(actions.NAV_LEFT)      # D-pad or left stick

# Controller-specific queries
inp.has_controller              # True if any controller connected
inp.controller_count            # number of connected controllers
inp.get_joystick_ids()          # list of instance IDs
inp.get_controller_name(id)     # name string
inp.get_axis(joy_id, axis)      # raw axis value (dead-zone filtered)
inp.was_controller_button_pressed(button)
inp.is_controller_button_down(button)
```

### Default controller mappings

| Button | Action |
|---|---|
| A / Cross (0) | CONFIRM |
| B / Circle (1) | CANCEL |
| Start / Options (7) | PAUSE |
| D-pad (11–14) | NAV_UP/DOWN/LEFT/RIGHT |
| Left stick | NAV_UP/DOWN/LEFT/RIGHT (threshold 0.5) |

### Dead zones

```python
from pygame_engine.input.input_manager import ControllerConfig

config = ControllerConfig(dead_zone=0.2, threshold=0.6)
app = Application(config)   # pass via AppConfig or post-init
```

---

## Key remapping

```python
# Remap a keyboard key to an action
inp.remap(actions.CONFIRM, pygame.K_z)

# Remap a controller button
inp.remap_controller(actions.CONFIRM, 2)

# Query current binding
key = inp.get_key_for_action(actions.CONFIRM)   # pygame key int or None
btn = inp.get_button_for_action(actions.CANCEL)

# Reset to defaults
inp.reset_to_defaults()

# Human-readable key names (for settings UI)
from pygame_engine.input.bindings import key_name, controller_button_name
key_name(pygame.K_RETURN)         # "Enter"
controller_button_name(0)         # "A / Cross"
```

---

## Saving and loading bindings

```python
# Save
saved = inp.bindings_to_dict()   # JSON-serialisable dict
save_manager.save("settings", {"bindings": saved})

# Load
data = save_manager.load("settings")
inp.bindings_from_dict(data["payload"]["bindings"])
```

---

## Custom bindings at startup

```python
from pygame_engine.input.bindings import DEFAULT_BINDINGS
from pygame_engine.input import actions

bindings = {
    **DEFAULT_BINDINGS,
    pygame.K_z:    actions.CONFIRM,
    pygame.K_x:    actions.CANCEL,
    pygame.K_j:    "attack",
    pygame.K_k:    "jump",
}
app = Application(config)
# After run() initialises input_manager:
app.input_manager.bindings = bindings
```

---

## Haptic feedback

```python
# Rumble all connected controllers
inp.rumble(low=0.3, high=0.8, duration_ms=200)

# Rumble a specific controller
inp.rumble(low=0.5, high=0.5, duration_ms=300, joystick_id=joy_id)

# Stop rumble immediately
inp.stop_rumble()              # all controllers
inp.stop_rumble(joystick_id=0) # specific controller
```

| Parameter | Range | Notes |
|---|---|---|
| `low` | `0.0–1.0` | Low-frequency motor — deep, heavy rumble |
| `high` | `0.0–1.0` | High-frequency motor — sharp, buzzing vibration |
| `duration_ms` | int | Duration in milliseconds |

Controllers that don't support rumble silently ignore the call.
Always safe to call regardless of whether a controller is connected.

### Common patterns

```python
# Player takes damage
inp.rumble(low=0.3, high=0.8, duration_ms=200)

# Heavy impact / explosion
inp.rumble(low=0.9, high=0.4, duration_ms=400)

# Subtle feedback (footstep, pickup)
inp.rumble(low=0.0, high=0.2, duration_ms=60)

# Stop on pause
def on_pause(self):
    self._app.input_manager.stop_rumble()
```

---

## Accepted decisions

### Actions are strings, not enums
Plain strings are easy to extend from game projects, require no import
of an enum class, and work naturally as dict keys for serialisation.

### Controllers contribute to the same action queries
`was_action_pressed(CONFIRM)` returns True for both Enter and the A
button. Games don't need separate code paths per device.

### Dead zones are applied at axis-read time
Axis values below `dead_zone` are clamped to 0.0 immediately on the
`JOYAXISMOTION` event. This keeps all downstream code clean.

### Remapping removes the old binding
`remap(action, key)` removes any previous key bound to that action
before adding the new one. This keeps the binding map 1:1 (one key
per action). If you want multiple keys per action, add them manually
to `input_manager.bindings` without using `remap()`.
