# Animation System

## Purpose

Provides time-based value animation and sprite animation for pygame_engine.

The animation system has three layers:

1. **Easing functions** (`easing.py`) — pure math, transform t ∈ [0,1]
2. **Tween** (`tween.py`) — single-value animator driven by delta-time
3. **Sprite animation** (`animator.py`) — frame-based sprite sequences via `SpriteAnimation` and `AnimationPlayer`

---

## Easing Functions

Easing functions transform a normalised time value `t` (0.0 → 1.0) into
a curve. They are pure functions with no state.

```python
from pygame_engine.animation.easing import ease_out_cubic

t     = timer.progress          # 0.0 → 1.0 from a Timer
value = ease_out_cubic(t)       # apply to alpha, position, scale, etc.
```

### Available functions

All standard Robert Penner easing families are provided (30 total):

| Family    | In                | Out                | In-Out                |
|-----------|-------------------|--------------------|-----------------------|
| Linear    | `linear`          | —                  | —                     |
| Quad      | `ease_in_quad`    | `ease_out_quad`    | `ease_in_out_quad`    |
| Cubic     | `ease_in_cubic`   | `ease_out_cubic`   | `ease_in_out_cubic`   |
| Quart     | `ease_in_quart`   | `ease_out_quart`   | `ease_in_out_quart`   |
| Sine      | `ease_in_sine`    | `ease_out_sine`    | `ease_in_out_sine`    |
| Expo      | `ease_in_expo`    | `ease_out_expo`    | `ease_in_out_expo`    |
| Circ      | `ease_in_circ`    | `ease_out_circ`    | `ease_in_out_circ`    |
| Back      | `ease_in_back`    | `ease_out_back`    | `ease_in_out_back`    |
| Elastic   | `ease_in_elastic` | `ease_out_elastic` | `ease_in_out_elastic` |
| Bounce    | `ease_in_bounce`  | `ease_out_bounce`  | `ease_in_out_bounce`  |

Back, Elastic, and Bounce may briefly exceed [0, 1] — this is intentional.

### Registry

```python
from pygame_engine.animation.easing import EASING_FUNCTIONS, get_easing

fn = get_easing("ease_out_cubic")   # look up by name
```

Useful for serialisation or runtime easing selection.

---

## Tween

A `Tween` animates a single float from `start` to `end` over `duration`
seconds using a chosen easing function.

```python
from pygame_engine.animation import Tween
from pygame_engine.animation.easing import ease_out_back

# Slide a panel in from off-screen
slide = Tween(start=-300, end=0, duration=0.4,
              easing=ease_out_back, auto_start=True)

# Each frame:
slide.update(dt)
panel.rect.x = int(slide.value)
```

### Design rules

- **No magic binding.** Tween animates a number. Callers read `value` and
  apply it themselves. This keeps Tweens simple and debuggable.
- **A Tween does not know what it is animating.** It is just a number.
- Looping and ping-pong are opt-in.

### Key properties

| Property     | Description                                      |
|--------------|--------------------------------------------------|
| `value`      | Current animated value (eased)                   |
| `progress`   | Normalised elapsed time 0.0–1.0 (not eased)      |
| `is_running` | True while animating                             |
| `is_done`    | True when the end value has been reached         |

### Control methods

| Method       | Description                                      |
|--------------|--------------------------------------------------|
| `start()`    | Begin from the start value                       |
| `restart()`  | Reset and begin regardless of current state      |
| `stop()`     | Pause at current value                           |
| `complete()` | Jump to end value immediately                    |
| `reverse()`  | Swap start/end and restart                       |

### Looping

```python
# Loop indefinitely
Tween(0, 100, 1.0, loop=True, auto_start=True)

# Ping-pong (reverse direction each cycle)
Tween(0, 100, 1.0, ping_pong=True, auto_start=True)
```

---

## Sprite Animation

`animator.py` provides frame-based sprite animation via two classes:
`SpriteAnimation` (immutable data) and `AnimationPlayer` (mutable state).

### SpriteAnimation

Immutable data object: a named list of `pygame.Surface` frames with timing.
Multiple `AnimationPlayer` instances can share one `SpriteAnimation`.

```python
from pygame_engine.animation import SpriteAnimation

frames = app.assets.spritesheet("player.png", 48, 48)

idle_anim = SpriteAnimation("idle", frames[0:4],  frame_duration=0.15)
run_anim  = SpriteAnimation("run",  frames[4:12], frame_duration=0.08)
jump_anim = SpriteAnimation("jump", frames[12:16],
                            frame_duration=0.1, loop=False)
```

Frame duration can be a single float (uniform) or a list (per-frame).

### AnimationPlayer

Owns the playback state. Maintains a registry of named `SpriteAnimation`
instances and tracks current frame, elapsed time, and direction.

```python
from pygame_engine.animation import AnimationPlayer

player = AnimationPlayer()
player.add("idle", idle_anim)
player.add("run",  run_anim)
player.add("jump", jump_anim)
player.play("idle")

# On-finish callback for non-looping animations:
player.on_finish = lambda name: player.play("idle")

# Each frame:
player.update(dt)
current_surface = player.current_frame
```

### Key properties

| Property            | Description                                        |
|---------------------|----------------------------------------------------|
| `current_frame`     | The `pygame.Surface` for the current frame         |
| `current_animation` | Name of the playing animation, or None             |
| `frame_index`       | Current frame index within the active animation    |
| `is_finished`       | True when a non-looping animation ends             |
| `is_playing`        | True while an animation is active and not finished |

### Control methods

| Method               | Description                                        |
|----------------------|----------------------------------------------------|
| `play(name)`         | Switch to named animation (no-op if already playing) |
| `play(name, restart=True)` | Force restart even if already playing       |
| `stop()`             | Stop playback and hold on current frame            |
| `add(name, anim)`    | Register a named animation                         |
| `add_many(dict)`     | Register multiple animations at once               |

### Ping-pong

```python
breath = SpriteAnimation("breath", frames, frame_duration=0.1, ping_pong=True)
# Plays: 0→1→2→3→2→1→0→1... without jumping back to frame 0
```

### Rendering with sprite_renderer

```python
from pygame_engine.graphics import draw_animation_frame

draw_animation_frame(surface, player, player_rect, flip_x=facing_left)
```

Or use `draw_sprite` for a single frame directly.

---

## Accepted Decisions

### Easing functions are stateless pure functions
No instances, no state. A function takes `t` and returns a value.

### Tween uses explicit value reading, no property binding
Callers read `tween.value` and apply it manually. This avoids reflection,
hidden coupling, and hard-to-debug magic.

### Tween duration must be > 0
Zero-duration tweens are rejected at construction. Use `complete()` to
snap to an end value instantly.

### SpriteAnimation is immutable data; AnimationPlayer is mutable state
Animations are defined once and shared. Players own playback state
independently. This allows many entities to share one animation definition.

### AnimationPlayer uses string names, not enum keys
Simple, extensible, readable. `player.play("run")` is clearer than an enum.
