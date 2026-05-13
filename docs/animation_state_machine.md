## Purpose

Manages transitions between named animation states based on runtime
conditions. Eliminates per-entity if/else animation logic.

Drives an `AnimationPlayer` — the state machine picks which animation
plays; `AnimationPlayer` picks which frame renders.

---

## Quick start

```python
from pygame_engine.animation import AnimationStateMachine

sm = AnimationStateMachine(player.animator)
sm.add_state("idle", default=True)
sm.add_state("run")
sm.add_state("jump")

sm.add_transition("idle", "run",  lambda p: abs(p["vx"]) > 10)
sm.add_transition("run",  "idle", lambda p: abs(p["vx"]) <= 10)
sm.add_transition("*",    "dead", lambda p: p["hp"] <= 0, priority=10)

# each frame:
sm.update(dt, params={"vx": vx, "hp": hp})
```

---

## API

### add_state

```python
sm.add_state("run",
             default=False,
             on_enter=lambda: audio.play(run_sfx),
             on_exit=lambda: ...)
```

### add_transition

```python
sm.add_transition(
    from_state="idle",
    to_state="run",
    condition=lambda params: params["vx"] > 10,
    priority=0,   # higher = checked first
)
sm.add_transition("*", "dead", lambda p: p["hp"] <= 0, priority=10)
```

### Query and control

```python
sm.current_state      # name or None
sm.is_in("run")       # bool
sm.force("idle")      # bypass conditions
sm.player             # the AnimationPlayer
```

---

## Notes

- Each state name must match an animation registered in the `AnimationPlayer`.
- Bad conditions (that raise exceptions) are skipped silently.
- `params` is whatever dict you pass — conditions receive it as their argument.
- Multiple characters can share a machine definition by constructing separate instances.