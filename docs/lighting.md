## Purpose

Dark overlay with radial gradient cutouts for each light source.
Effective for dungeon crawlers, horror games, and night scenes.

---

## Quick start

```python
from pygame_engine.lighting import Light, LightingSystem

lights = LightingSystem(ambient=(10, 15, 30), darkness=0.92)
torch  = lights.add(Light(world_x=400, world_y=300,
                           radius=200, colour=(255,180,80),
                           intensity=0.95, flicker=0.15))
player_light = lights.add(Light(radius=100, colour=(200,220,255), intensity=0.6))

# each frame:
player_light.world_x = player.rect.centerx
player_light.world_y = player.rect.centery
lights.update(dt)
lights.render(surface, camera)   # after world, before UI
```

---

## Render order

```python
def render(self, surface):
    surface.fill((20, 20, 30))           # 1. clear
    self._tmap.render(surface, camera)   # 2. world
    for e in self._entities: ...         # 3. entities
    self._lights.render(surface, camera) # 4. lighting ← here
    super().render(surface)              # 5. UI (not darkened)
```

---

## LightingSystem

```python
ls = LightingSystem(ambient=(10,15,30), darkness=0.92)
ls.add(Light(...))     # returns Light
ls.remove(light)
ls.clear()
ls.darkness = 0.5      # adjust at runtime
ls.update(dt)          # update flicker
ls.render(surface, camera)
```

## Light

```python
light = Light(world_x=0, world_y=0,
              radius=150, colour=(255,220,160),
              intensity=0.9, flicker=0.0,
              enabled=True)
light.world_x = new_x
light.enabled = False
```

---

## Ambient colours

| Scene | ambient | darkness |
|---|---|---|
| Pitch black | `(0,0,0)` | `1.0` |
| Night exterior | `(10,15,30)` | `0.85` |
| Dim cave | `(20,18,25)` | `0.75` |
| Overcast | `(60,65,80)` | `0.4` |

---

## Day/night cycle

```python
t = abs(math.sin(time_of_day * math.pi))   # 0=midnight, 1=noon
lights.darkness = lerp(0.95, 0.1, t)
```