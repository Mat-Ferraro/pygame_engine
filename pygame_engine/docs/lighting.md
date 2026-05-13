# 2D Lighting

## Purpose

Simulates 2D lighting using a dark overlay with radial gradient
cut-outs for each light source. Effective for dungeon crawlers, horror
games, night scenes, and any game that benefits from atmospheric lighting.

Not physically accurate — a proven indie game technique used in countless
2D games.

---

## Quick start

```python
from pygame_engine.lighting import Light, LightingSystem

# Create the system
lights = LightingSystem(ambient=(10, 15, 30), darkness=0.92)

# Add light sources
torch = lights.add(Light(
    world_x=400, world_y=300,
    radius=200,
    colour=(255, 180, 80),
    intensity=0.95,
    flicker=0.2,      # subtle torch flicker
))

player_light = lights.add(Light(
    world_x=0, world_y=0,
    radius=100,
    colour=(200, 220, 255),
    intensity=0.6,
))

# Each frame — update positions, then render AFTER world, BEFORE UI
player_light.world_x = player.rect.centerx
player_light.world_y = player.rect.centery
lights.update(dt)
lights.render(surface, camera)
```

---

## LightingSystem

```python
ls = LightingSystem(
    ambient=(10, 15, 30),  # RGB colour of darkness
    darkness=0.92,          # 0 = no overlay, 1 = fully dark
)

light = ls.add(Light(...))   # returns the Light for convenience
ls.remove(light)
ls.clear()
ls.lights                    # list of all lights
ls.darkness = 0.8            # adjust at runtime (fade to dawn, etc.)
ls.update(dt)                # update flicker
ls.render(surface, camera)   # draw overlay
```

---

## Light

```python
light = Light(
    world_x=200, world_y=300,
    radius=180,                    # world pixels
    colour=(255, 200, 100),        # RGB tint
    intensity=0.95,                # 0 = invisible, 1 = fully lit at centre
    flicker=0.15,                  # 0 = steady, 1 = heavy flicker
    enabled=True,
)

light.world_x = new_x   # move the light
light.enabled = False    # toggle without removing
```

---

## Render order

```python
def render(self, surface):
    surface.fill((20, 20, 30))       # 1. clear
    self._tmap.render(surface, cam)  # 2. world
    for entity in self._entities:    # 3. entities
        entity.render(surface, cam)
    self._lights.render(surface, cam) # 4. lighting overlay ← HERE
    super().render(surface)          # 5. UI (not darkened)
```

The lighting overlay **must** go after world rendering but **before** UI
so the HUD stays readable.

---

## Ambient light colours

| Scene | ambient | darkness |
|---|---|---|
| Pitch black dungeon | `(0, 0, 0)` | `1.0` |
| Night exterior | `(10, 15, 30)` | `0.85` |
| Dim cave | `(20, 18, 25)` | `0.75` |
| Overcast day | `(60, 65, 80)` | `0.4` |
| Sunset | `(80, 40, 20)` | `0.5` |

---

## Day/night cycle

```python
# Lerp darkness over time
self._time_of_day += dt / DAY_LENGTH   # 0 = midnight, 0.5 = noon
t = abs(math.sin(self._time_of_day * math.pi))   # 0 at midnight, 1 at noon
self._lights.darkness = lerp(0.95, 0.1, t)
```

---

## Accepted decisions

### Dark overlay + alpha subtract
The overlay is a full-screen SRCALPHA surface filled with the ambient
colour. Light circles are subtracted using `BLEND_RGBA_SUB`. This is
the standard 2D lighting technique — simple, fast, and GPU-agnostic.

### Camera-aware rendering
When a Camera is passed to `render()`, light positions are converted
from world space to screen space, and the radius is scaled by the
camera zoom. Without a Camera, positions are treated as screen coords.

### UI is not darkened
Render the lighting overlay before `super().render(surface)`. The
engine's widget tree (HUD, menus) renders on top of the overlay.
