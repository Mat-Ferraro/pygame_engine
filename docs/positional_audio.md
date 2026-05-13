## Purpose

2D distance-based audio: sounds fade with distance and pan left/right
based on position relative to the listener. A stereo approximation
using pygame's per-channel volume.

---

## Quick start

```python
from pygame_engine.audio.positional import PositionalAudio

pos = PositionalAudio(max_distance=600)
pos.set_listener(player.rect.centerx, player.rect.centery)

# One-shot
pos.play(explosion_sfx, world_x=enemy.x, world_y=enemy.y)

# Looping source
src = pos.create_source(fire_sfx, loop=True, world_x=tx, world_y=ty)
src.start(pos)
src.update(pos)   # each frame
```

---

## PositionalAudio

```python
pos = PositionalAudio(max_distance=500, rolloff=1.0)
pos.set_listener(world_x, world_y)        # call every frame
pos.play(sound, world_x, world_y, volume=1.0)
pos.max_distance = 800
pos.listener_position   # (x, y)
```

## PositionalSource

```python
src = pos.create_source(sound, world_x, world_y, loop=True, volume=1.0)
src.start(pos)
src.world_x = npc.rect.centerx   # update position
src.update(pos)                   # recompute volume/pan
src.stop()
src.is_playing   # bool
```

---

## Integration

```python
# Listener = player (most common)
pos.set_listener(player.rect.centerx, player.rect.centery)

# Listener = camera centre (better for scrolling games)
cam_x, cam_y = camera.position
pos.set_listener(cam_x, cam_y)
```