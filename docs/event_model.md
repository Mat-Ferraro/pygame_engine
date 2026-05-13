# Event Model

## Purpose

Defines how game systems communicate in `pygame_engine` projects.

Two mechanisms exist for different use cases:

| Mechanism | Use when |
|---|---|
| `Observable` | One value, multiple consumers, reactive UI |
| `EventBus` | Discrete game events, loose coupling between systems |

Direct callbacks (`on_click`, `on_change`, `on_finish`) remain the right
choice for tight, local coupling — widget → scene, tween → callback.

---

## Observable

`Observable[T]` wraps a single value and notifies subscribers when it changes.

Best for: health points, volume level, selected inventory slot, any value
that multiple UI elements or systems need to react to.

```python
from pygame_engine.state.observable import Observable

self.hp = Observable(100)
self.hp.subscribe(lambda new, old: hud.update_hp(new))
self.hp.value = 70   # → hud.update_hp(70) fires automatically
```

---

## EventBus

`EventBus` is a pub/sub bus for discrete game events. Publishers and
subscribers are completely decoupled — neither knows the other exists.

Accessible via the module-level singleton:

```python
from pygame_engine.events import bus
```

Or inject a fresh instance for isolated testing:

```python
from pygame_engine.events.event_bus import EventBus
bus = EventBus()
```

### Subscribing

```python
# Permanent subscription
bus.on("player.damaged", on_player_damaged)

# One-shot — auto-unsubscribes after first call
bus.once("tutorial.first_kill", show_tip)

# Wildcard — matches any event starting with "player."
bus.on("player.*", analytics.record_player_event)
```

### Emitting

All payload values are keyword arguments:

```python
bus.emit("player.damaged", amount=30, source="spike_trap")
bus.emit("item.collected", item_id="sword_01", rarity="rare")
bus.emit("scene.entered",  scene_name="dungeon_level_3")
```

### Unsubscribing

```python
bus.off("player.damaged", on_player_damaged)   # remove one handler
bus.clear("player.damaged")                     # remove all handlers for event
bus.clear_all()                                 # remove everything
```

### Signals (optional typed wrapper)

`Signal` wraps a specific event for a cleaner API on game classes:

```python
from pygame_engine.events.signals import Signal
from pygame_engine.events import bus

class Player:
    damaged     = Signal("player.damaged",     bus)
    died        = Signal("player.died",        bus)
    levelled_up = Signal("player.levelled_up", bus)

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        Player.damaged.emit(amount=amount)
        if self.hp <= 0:
            Player.died.emit()

# Subscribing via Signal
Player.damaged.connect(hud.on_player_damaged)
Player.died.connect(game_over_screen.show)
```

---

## Naming conventions

Use dot-separated namespaces:

```
"player.damaged"        player took damage
"player.died"           player died
"player.levelled_up"    player gained a level
"enemy.spawned"         enemy created
"enemy.died"            enemy destroyed
"item.collected"        player picked up item
"scene.entered"         scene became active
"scene.exited"          scene removed
"save.completed"        save finished
"audio.muted"           audio muted/unmuted
```

---

## Accepted Decisions

### EventBus uses string event names, not enums or classes
**Reason:** Strings are fast to write, readable in logs, and easily wildcard-
matched. Enums would require all event names to be registered in one place,
which doesn't fit a multi-system game architecture.

### All payload values are keyword arguments
**Reason:** `bus.emit("player.damaged", amount=30)` is readable and forwards-
compatible. Handlers can accept only the kwargs they care about.

### Synchronous, no queuing
**Reason:** Queued/deferred events add complexity with no concrete benefit
for single-threaded game loops. All handlers fire immediately on emit.

### Broken handlers are isolated with a warning
**Reason:** A broken event handler should not crash the game or prevent other
handlers from receiving the event. Exceptions are caught, a `warnings.warn`
is emitted, and execution continues.

### bus.clear_all() called on Application shutdown
**Reason:** Prevents stale handler references from surviving between test
runs or game sessions when the bus singleton persists.

### Observable for reactive values, EventBus for discrete events
**Reason:** These are genuinely different patterns. Observable is the right
tool when something needs to react to "what is the current value". EventBus
is right for "something just happened". Using one for everything creates
awkward code.
