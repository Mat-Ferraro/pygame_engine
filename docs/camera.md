# Camera System

## Purpose

Provides 2D world-space / screen-space coordinate conversion for games
where the world is larger than the screen. Also supports smooth target
following, zoom, screen shake, and world-bounds clamping.

---

## Quick start

```python
from pygame_engine.camera import Camera

# Create once — viewport size matches your AppConfig resolution
camera = Camera(viewport_width=1280, viewport_height=720)

# In on_enter: set where the camera starts
camera.move_to(player.rect.center)

# In update: follow the player smoothly
camera.follow(player.rect.center, speed=6.0, dt=dt)
camera.update(dt)   # decays screen shake

# In render: convert world positions to screen positions
screen_rect = camera.world_rect_to_screen(enemy.rect)
pygame.draw.rect(surface, RED, screen_rect)

# Mouse picking
world_pos = camera.screen_to_world(pygame.mouse.get_pos())
```

---

## API reference

### Construction

```python
Camera(viewport_width, viewport_height, zoom=1.0)
```

### Properties

| Property | Type | Description |
|---|---|---|
| `position` | `(float, float)` | World point the camera is centred on |
| `zoom` | `float` | 1.0 = no zoom, 2.0 = 2× magnification |
| `trauma` | `float` | Current shake trauma [0, 1] |
| `viewport_size` | `(int, int)` | Current viewport dimensions |

### Movement

| Method | Description |
|---|---|
| `move_to(world_pos)` | Instantly centre on a world position |
| `follow(target, speed, dt, threshold)` | Smoothly move toward target each frame |

### Coordinate conversion

| Method | Description |
|---|---|
| `world_to_screen(world_pos)` | World → screen pixel `(int, int)` |
| `screen_to_world(screen_pos)` | Screen pixel → world `(float, float)` |
| `world_rect_to_screen(rect)` | World rect → screen rect (zoom applied) |
| `is_visible(rect, margin)` | True if world rect overlaps viewport |

### Screen shake

| Method | Description |
|---|---|
| `add_trauma(amount)` | Add [0, 1] trauma; accumulates up to 1.0 |
| `update(dt)` | Decay trauma and recompute shake offset — call every frame |

### World bounds

| Method | Description |
|---|---|
| `set_world_bounds(rect)` | Clamp camera so viewport never exits this rect |

---

## Patterns

### Entity rendering loop

```python
def render(self, surface):
    surface.fill(theme.colours.bg_dark)
    for entity in self._world.entities:
        if not self._camera.is_visible(entity.rect, margin=64):
            continue   # cull off-screen entities
        screen_rect = self._camera.world_rect_to_screen(entity.rect)
        surface.blit(entity.image, screen_rect)
    super().render(surface)
```

### Screen shake on damage

```python
def on_player_hit(self, damage):
    trauma = clamp(damage / 100.0, 0.1, 0.8)
    self._camera.add_trauma(trauma)
```

### Zoom for dramatic effect

```python
# Zoom in slowly for a boss encounter
self._camera.zoom = lerp(self._camera.zoom, 1.5, dt * 2.0)
```

### Mouse-to-world picking

```python
def _handle_event_scene(self, event):
    if event.type == pygame.MOUSEBUTTONDOWN:
        world_pos = self._camera.screen_to_world(event.pos)
        self._world.click_at(world_pos)
```

---

## Camera with world bounds

Prevents the camera from showing outside the world map:

```python
world_rect = pygame.Rect(0, 0, 4000, 3000)
camera.set_world_bounds(world_rect)
# Now camera.position is always clamped so the viewport stays inside world_rect
```

---

## Accepted decisions

### Camera is a standalone utility, not a scene component
`Camera` is a plain class — not a scene mixin or engine singleton.
Games create and own their own Camera instances. A platformer might have
one camera; a split-screen game might have two. The engine stays generic.

### Exponential decay follow
`follow()` uses `lerp(current, target, clamp(speed * dt, 0, 1))` rather
than a fixed step. This produces a natural ease-in that always approaches
without overshooting, and automatically adapts to frame rate variation.

### Trauma-squared shake model
Shake offset = `trauma² × max_offset`. Squaring trauma means small trauma
values produce almost no shake while full trauma (1.0) produces maximum
shake. The decay is linear, but the perceived shake drops off naturally.

### No built-in sprite rendering
`Camera` converts coordinates; it does not own a render loop. Games call
`world_rect_to_screen()` and render using standard pygame calls. This
keeps the camera decoupled from the asset and sprite systems.
