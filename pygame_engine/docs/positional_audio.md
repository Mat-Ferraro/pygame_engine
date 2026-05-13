# Positional Audio

## Purpose

Simulates 2D distance-based audio: sounds fade out with distance and
pan left/right based on position relative to the listener.

Not true 3D audio — a stereo approximation using pygame's per-channel
volume that is convincing for top-down and platformer games.

---

## Quick start

```python
from pygame_engine.audio.positional import PositionalAudio

pos_audio = PositionalAudio(max_distance=600.0)

# Each frame — update listener position (usually the player or camera)
pos_audio.set_listener(player.rect.centerx, player.rect.centery)

# One-shot: play a sound at a world position
pos_audio.play(explosion_sound, world_x=enemy.rect.centerx,
                                world_y=enemy.rect.centery)

# Looping ambient: create a managed source
fire_source = pos_audio.create_source(fire_sound, loop=True)
fire_source.world_x = torch.rect.centerx
fire_source.world_y = torch.rect.centery
fire_source.start(pos_audio)

# Each frame — update moving sources
fire_source.world_x = torch.rect.centerx  # if it moves
fire_source.update(pos_audio)
```

---

## PositionalAudio

```python
pos = PositionalAudio(
    max_distance=500.0,   # silence beyond this distance
    rolloff=1.0,          # 1.0 = linear, 2.0 = quadratic falloff
)

pos.set_listener(world_x, world_y)   # call every frame
pos.play(sound, world_x, world_y, volume=1.0)   # one-shot
pos.max_distance = 800.0             # update at runtime
pos.listener_position                # (x, y) tuple
```

---

## PositionalSource (looping / managed)

```python
source = pos_audio.create_source(
    sound,
    world_x=0.0, world_y=0.0,
    loop=True,
    volume=1.0,
)
source.start(pos_audio)    # begin playing
source.world_x = npc.x    # update position
source.update(pos_audio)   # recompute volume/pan — call each frame
source.stop()              # stop playback
source.is_playing          # bool
```

---

## Integration with Camera

The listener should track what the player hears from — usually the
player position, but sometimes the camera centre:

```python
# Option A: listener = player
pos_audio.set_listener(player.rect.centerx, player.rect.centery)

# Option B: listener = camera (better for scrolling games)
cam_x, cam_y = camera.position
pos_audio.set_listener(cam_x, cam_y)
```

---

## Scene pattern

```python
class GameScene(Scene):
    def on_enter(self):
        self._pos_audio = PositionalAudio(max_distance=600)
        self._ambient   = self._pos_audio.create_source(
            app.assets.sound("wind.wav"), loop=True,
            world_x=800, world_y=400,
        )
        self._ambient.start(self._pos_audio)

    def update(self, dt):
        self._pos_audio.set_listener(*player.rect.center)
        self._ambient.update(self._pos_audio)
        # One-shots need no update — fire and forget
        if enemy_exploded:
            self._pos_audio.play(boom_sfx, enemy.x, enemy.y)
```
