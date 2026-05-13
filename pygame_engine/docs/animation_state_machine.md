# Animation State Machine

## Purpose

Manages transitions between named animation states based on runtime
conditions. Eliminates per-entity if/else animation logic and makes
character animation behaviour declarative and reusable.

Sits on top of `AnimationPlayer` — the state machine drives which
animation plays; `AnimationPlayer` drives which frame renders.

---

## Quick start

```python
from pygame_engine.animation import AnimationStateMachine

sm = AnimationStateMachine(player.animator)

sm.add_state("idle",  default=True)
sm.add_state("run")
sm.add_state("jump")
sm.add_state("fall")

sm.add_transition("idle", "run",  lambda p: abs(p["vx"]) > 10)
sm.add_transition("run",  "idle", lambda p: abs(p["vx"]) <= 10)
sm.add_transition("idle", "jump", lambda p: p["jumping"])
sm.add_transition("run",  "jump", lambda p: p["jumping"])
sm.add_transition("jump", "fall", lambda p: p["vy"] > 0)
sm.add_transition("fall", "idle", lambda p: p["on_ground"])

# Each frame:
sm.update(dt, params={
    "vx":       self.vx,
    "vy":       self.vy,
    "jumping":  self.jumping,
    "on_ground": self.on_ground,
})
```

---

## API

### add_state

```python
sm.add_state(
    "run",
    default=False,          # True = enter on first update()
    on_enter=lambda: ...,   # fired when entering this state
    on_exit=lambda: ...,    # fired when leaving this state
)
```

### add_transition

```python
sm.add_transition(
    from_state="idle",
    to_state="run",
    condition=lambda params: params["vx"] > 10,
    priority=0,   # higher = checked first among same-source transitions
)

# Any-state transition (fires regardless of current state)
sm.add_transition("*", "dead",
                  condition=lambda p: p["hp"] <= 0,
                  priority=10)
```

### update

```python
sm.update(dt, params={"vx": vx, "vy": vy, "on_ground": on_ground})
```

`params` can be any dict — your conditions receive it as their argument.

### Query and control

```python
sm.current_state        # name of active state, or None
sm.is_in("run")         # bool
sm.force("idle")        # skip conditions, enter state immediately
sm.player               # the AnimationPlayer being driven
```

---

## Patterns

### Any-state death transition

```python
sm.add_transition("*", "dead",
                  condition=lambda p: p.get("dead", False),
                  priority=100)   # always checked first
```

### on_enter / on_exit callbacks

```python
sm.add_state("land",
             on_enter=lambda: audio.play(land_sfx),
             on_exit=lambda: ...)
```

### Multiple characters sharing one machine definition

```python
def build_player_sm(animator):
    sm = AnimationStateMachine(animator)
    sm.add_state("idle", default=True)
    sm.add_state("run")
    # ... transitions ...
    return sm

player1_sm = build_player_sm(player1.animator)
player2_sm = build_player_sm(player2.animator)
```

---

## Accepted decisions

### Conditions receive a dict, not the entity
Conditions take `lambda params: bool` where `params` is whatever dict
you pass to `update()`. This keeps the state machine decoupled from
entity internals — the entity decides what to expose.

### Bad conditions fail silently
If a condition raises an exception, the transition is skipped. This
prevents one broken condition from crashing the whole entity.

### AnimationPlayer.play() called on state entry
The state machine calls `player.play(state_name)` when entering a
state. This means each state name must exactly match an animation
registered in the `AnimationPlayer`.
