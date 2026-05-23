# pygame_engine — Advanced 2D Lighting: Design

**Version:** 0.1-stretch
**Status:** Stretch goal — not scheduled. Design only.
**Authority:** Supplements ARCHITECTURE.md. Supersedes `lighting.md` if and
when this work is scheduled.

This document defines the *design* of an advanced 2D lighting system: what it
should do, how it should be structured, and — equally important — what it
should deliberately *not* do. Optimisation strategy lives in
`LIGHTING_PERFORMANCE.md`. The phased delivery plan lives in
`LIGHTING_ROADMAP.md`.

This is a stretch goal. Nothing here is committed. The purpose of writing it
down now is so that the decisions are made deliberately rather than discovered
mid-implementation.

---

## 1. Why Revisit Lighting

The current system (`pygame_engine/lighting/lighting.py`, shipped in Phase 11)
is a dark overlay with radial-gradient cut-outs. It is cheap, atmospheric, and
adequate for a first pass. It has three structural limits:

1. **No occlusion.** Light passes through walls. A torch lights the room
   behind a wall as brightly as the room it sits in. This is the single
   largest gap between "atmospheric" and "convincing".
2. **The gradient is rebuilt every frame, per light**, from up to 48 concentric
   `draw.circle` calls. This is wasteful and produces visible banding.
3. **Lighting is purely subtractive.** Lights only *remove* darkness; they
   cannot *add* coloured light to a surface. A blue torch cannot tint a wall.

The advanced system addresses all three. It is a larger piece of work than the
current module and should only be undertaken if 2D lighting becomes a priority
for games built on the engine.

---

## 2. The Technique Ladder

Lighting techniques form a ladder of rising realism and rising cost. The design
below targets tiers 1 through 3. Tier 4 is an explicit non-goal (Section 9).

| Tier | Technique | Realism | Cost | In scope |
|---|---|---|---|---|
| 0 | Radial overlay cut-outs (current) | Low | Very low | Shipped |
| 1 | Cached buffer + additive light map | Low–Med | Low | **Yes** |
| 2 | Shadow casting (visibility polygon) | High | Moderate | **Yes** |
| 3 | Soft shadows, bloom, falloff curves | High+ | Moderate+ | **Yes** |
| 4 | Normal-mapped / shader lighting | Highest | High (needs GPU) | No — Section 9 |

Tier 1 is a prerequisite refactor: it makes everything above it cheaper and
unlocks coloured light. Tier 2 is the realism centrepiece. Tier 3 is polish
applied on top of tier 2, each item independently optional.

---

## 3. Tier 1 — Cached Buffer and Additive Light Map

Tier 1 is not a feature so much as the compositing model the rest of the system
is built on.

### 3.1 Cached falloff texture

A light's gradient depends only on its radius, colour, and intensity. It must
not be rebuilt every frame. The system bakes a single white radial-falloff
texture once at a fixed size. Each light is then a scaled, colour-tinted blit
of that texture. Scaling smooths the banding away as a side effect.

### 3.2 Separate light map, multiply composite

The current system subtracts darkness. The advanced system instead accumulates
light into a dedicated **light-map surface**:

1. The light map starts filled with the ambient colour (a dark floor value,
   not pure black, unless the scene wants pitch darkness).
2. Each light is blitted additively (`BLEND_RGBA_ADD`) into the light map.
3. After the world is drawn, the light map is multiplied
   (`BLEND_RGBA_MULT`) onto the world surface.

Multiply means lit areas keep their colour, unlit areas fall toward the ambient
value, and a coloured light genuinely tints whatever it falls on. This is the
standard model for 2D engines and is the foundation tiers 2 and 3 build on.

---

## 4. Tier 2 — Shadow Casting

Tier 2 is what makes a scene look *lit* rather than merely *atmospheric*.

### 4.1 The visibility polygon

For each shadow-casting light, the system computes a **visibility polygon**:
the exact region that light can reach, given a set of occluder edges (wall
segments).

The algorithm is 2D raycasting. From the light, cast a ray toward every
occluder vertex, plus two rays slightly offset to either side of each vertex so
rays can slip past corners. Each ray returns its nearest intersection. Sorting
the hit points by angle produces a polygon describing everything the light
sees. The light gradient is then drawn clipped to that polygon instead of as a
full circle.

### 4.2 Rendering the polygon

The polygon is not rendered as geometry directly. Each light gets a mask
surface; the visibility polygon is filled white on the mask; the light's
falloff texture is combined with the mask so the polygon zeroes out shadowed
regions and the texture supplies the falloff. Cost is one polygon fill plus one
combine per light.

### 4.3 Where occluder edges come from — the `LightOccluder` interface

Occluder edges must come from somewhere, and the lighting system must not
import the tilemap or entity classes directly — that would violate the
decoupling the rest of the engine maintains (see DEPENDENCY_POLICY.md).

The design introduces a `LightOccluder` concept: anything that can emit a list
of `(x1, y1, x2, y2)` world-space segments. The tilemap emits occluders for its
collidable tiles; entities (a crate, a closed door) can also emit them. The
scene collects occluders each frame and hands them to the lighting system. The
lighting system never needs to know what a tilemap is.

**Edge merging.** Emitting one edge per tile face is wasteful — a 10×10 wall
would yield 400 tiny edges. Collinear adjacent faces must collapse into single
long segments. This happens once when the tilemap loads. See
`LIGHTING_PERFORMANCE.md` Section 4.

### 4.4 Coordinate space

Raycasting is performed in **world space**. Occluder edges are world-space and
lights are world-space; keeping the raycast in world space avoids re-deriving
geometry whenever the camera moves. The finished polygon is transformed to
screen space only at composite time.

---

## 5. Tier 3 — Soft Shadows, Bloom, Falloff

Tier 3 items are polish passes on tier 2. Each is independently optional and
can be scheduled separately.

**Soft shadows.** Hard visibility polygons have razor edges. The cheap,
recommended approach is to render the light's mask, then blur it slightly
(downscale then upscale, or a small box-blur). A truer penumbra — casting
boundary rays from two offset points so the overlap forms a gradient — is
documented as an option but not the default; the downscale-blur trick is
sufficient for a pixel-art aesthetic and far cheaper.

**Bloom.** Extract the bright parts of the final frame, blur them at reduced
resolution, add them back (`BLEND_RGBA_ADD`). Sells the intensity of a light.
Cheap because the blur runs at quarter resolution.

**Falloff curves.** The current gradient is linear. Real light falls off closer
to inverse-square. The design makes the falloff curve a per-light parameter
(`linear`, `quadratic`, `smooth`). `smooth` (smoothstep) is the recommended
default: softer than linear without the harsh near-light brightness of true
quadratic.

---

## 6. The Lighting Layer Model

A request that motivated this design: certain scene layers should *occlude*
light while others — foreground layers such as a tree canopy — should only be
*backlit*. Handling this correctly requires care.

### 6.1 Two depths, not one

The engine already has **draw order** (the painter's-algorithm sequence). That
is a rendering concern and is unchanged.

Lighting needs a separate, smaller concept: a **lighting role** that answers
two *independent* questions per renderable:

1. Does this thing block light? (is it an occluder?)
2. Does this thing receive light, and how?

These are orthogonal. Glass receives light but does not block it. Fog blocks
light but is not itself "lit". Collapsing them into a single z-number is a
trap.

### 6.2 The four roles

A small fixed set of named roles covers essentially every 2D lighting scenario.
Continuous z-depth is deliberately rejected (Section 9) — it invites a second
numbering system that must be kept in sync with draw order.

| Role | Blocks light | Receives light | Typical content |
|---|---|---|---|
| `BACKGROUND` | No | Yes (lit normally) | Far walls, sky, floor |
| `OCCLUDER` | Yes | Yes (lit normally) | Walls, crates, closed doors |
| `ACTOR` | Optional | Yes (lit normally) | Player, enemies, items |
| `FOREGROUND` | No | Backlit only | Canopy, fog, overhangs |

The role is an annotation on the engine's *existing* draw layers, not a
competing axis. It must not become a parallel numbering system.

### 6.3 `LightProfile`

Anything that participates in lighting carries a small `LightProfile`:

- `blocks_light: bool`
- `receives_light: bool`
- `light_mode`: one of `lit`, `silhouette`, `backlit`

The role mostly exists so a designer can declare "this is foreground" once and
get sane defaults for these three fields rather than setting them by hand.

### 6.4 Render pipeline with planes

Occlusion is decided when each light's visibility polygon is built (only
`blocks_light` renderables contribute edges). Reception is decided at composite
time. "Backlit only" is simply a *different blend operation* applied to the
foreground plane. The per-frame flow becomes:

1. Draw background plane onto the world surface.
2. Draw occluder plane onto the world surface.
3. Draw actor plane onto the world surface.
4. Build the light map: for each light, raycast against `blocks_light`
   occluders only; accumulate falloff textures additively.
5. Multiply the light map onto the world surface — this lights planes 1–3.
6. Draw the foreground plane on top of the now-lit world.
7. Backlight the foreground (Section 6.5).
8. Draw UI, untouched, exactly as the current pipeline does.

The crucial ordering point: the foreground plane composites *after* the light
multiply, which is exactly why it can have its own lighting rule.

### 6.5 What "backlit only" means in practice

Three approaches, increasing fidelity:

- **Silhouette (cheap).** Foreground renders dark toward the ambient value,
  ignoring the light map. A canopy becomes a near-black shape. Costs nothing.
  Implement this first.
- **Rim light (recommended).** Render the foreground sprite, then sample the
  light map at the sprite's outline pixels and add a thin glow there. A backlit
  canopy gets a bright fringe where light leaks past it. This is the target
  look.
- **True light bleed (expensive).** The foreground becomes a soft, blurred
  occluder so light scatters around it. This re-introduces the foreground into
  the raycast — the cost the plane model was designed to avoid. Documented as
  an option; not recommended.

"Backlit only" is best understood as: the foreground does not receive a light
*multiply*; it receives an additive *rim* contribution sampled from the light
map. Same buffer, different blend op.

---

## 7. Light Taxonomy: Static, Dynamic, Semi-static

For performance reasons detailed in `LIGHTING_PERFORMANCE.md`, lights fall into
three categories that the API should make explicit:

- **Static** — never moves, geometry never changes. Visibility polygon computed
  once on scene load and cached. A wall torch.
- **Dynamic** — moves every frame. Recomputed every frame. The player's
  lantern.
- **Semi-static** — mostly still, changes on discrete events. Recomputed on
  event, not on a timer. A light on a door that only changes when the door
  opens.

**Flicker is decoupled from geometry.** Naive flicker would make every torch
"dynamic" and defeat the static optimisation. The visibility polygon
(expensive, geometric) is cached; flicker modulates only intensity and colour
(cheap, a blit alpha or multiply). A flickering wall torch is still
geometrically static.

---

## 8. API Decisions

These are the decisions that must be settled before any code is written.
Backward compatibility is *not* a constraint — the engine is unreleased — so
the API can be designed cleanly rather than grafted onto the current one.

| Decision | Resolution |
|---|---|
| Who owns the render sequence | The **scene** owns plane ordering and composite timing. The lighting system is a service: "give me occluders and a surface, receive a light map." Keeps lighting decoupled. |
| Raycast coordinate space | World space. Polygon transformed to screen at composite time. |
| Surface allocation | A persistent, reused light-map surface plus a small scratch-surface pool. No per-frame `SRCALPHA` allocation. |
| Flicker RNG | Injected or seeded, never an inline `import random`. The raycaster and flicker must be deterministic so geometry is testable. |
| Occluder source | The `LightOccluder` interface (Section 4.3). Lighting never imports tilemap or entity types. Add a line to DEPENDENCY_POLICY.md. |
| Shadows on/off | Per-light `cast_shadows: bool` plus a system-wide `quality` enum. Cheap radial path remains available for decorative lights. |
| Particle interaction | Glowing particles do **not** contribute to the light map by default. Revisit only if a concrete need appears. |
| Light tinted by what it passes through | Out of scope. A torch behind stained glass is a non-goal. |

---

## 9. Non-Goals

Stated explicitly so the design does not quietly grow:

- **Normal-mapped / per-pixel shader lighting (tier 4).** Gorgeous, but
  requires an OpenGL context (`moderngl` or `pygame._sdl2` with shaders) and a
  fragment shader. That is a meaningful dependency and a different rendering
  backend. Tiers 2 + 3 deliver roughly 90% of the visual payoff at a fraction
  of the effort. Tier 4 is recorded here as a possible future *optional GL
  backend*, not a goal of this work.
- **Continuous z-depth for lighting.** Four named roles cover the 2D scenarios.
  A continuous depth value invites a second numbering system kept in sync with
  draw order — a classic bug source. If a scene ever needs a fifth role, that
  is the moment to add one, not now.
- **True light bleed through foreground** (Section 6.5).
- **Coloured light filtered by translucent occluders** (Section 8).
- **Threaded polygon computation.** Discussed in `LIGHTING_PERFORMANCE.md` as a
  known avenue; not built. Python's GIL makes `threading` ineffective for CPU
  work and `multiprocessing` serialisation cost tends to eat the gain for
  frame-rate-sensitive work.

---

## 10. Open Questions

To be resolved if and when this work is scheduled:

1. Should `LightProfile` live on the existing draw-layer abstraction, or be a
   separate component attached to renderables? The design leans toward
   annotating existing draw layers (Section 6.2) but the exact attachment point
   depends on how draw layers are currently modelled.
2. Should the soft-shadow blur be a global quality setting or per-light? Leaning
   global, since mixing blurred and razor-edged shadows in one scene looks
   inconsistent.
3. Does the day/night cycle (currently a `darkness` lerp) map cleanly onto the
   ambient-colour-of-the-light-map model? Likely yes — the cycle becomes an
   ambient-colour lerp — but it should be confirmed against the existing
   `lighting.md` day/night example.
