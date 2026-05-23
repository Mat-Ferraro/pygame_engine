# pygame_engine — Advanced 2D Lighting: Open Items

**Version:** 0.1-stretch
**Status:** Stretch goal — backlog. Nothing here is decided.
**Authority:** Companion to LIGHTING_DESIGN.md, LIGHTING_PERFORMANCE.md, and
LIGHTING_ROADMAP.md.

The three companion documents describe a *committed design direction* for an
advanced lighting system. This document is different: it is the **backlog** —
items that have been considered but not decided, integration points that need
attention, and tooling worth building.

Each item carries context and a recommendation. A recommendation is not a
decision; it is a starting position for the discussion that happens if this
work is ever scheduled. The purpose of writing them down is so that none of
them is *discovered* mid-implementation as if new.

---

## 1. Unresolved Design Questions

### 1.1 Light shapes beyond the radial point light

The committed design assumes a radial point light. Most games need more:

- **Spotlight / cone** — a point light masked to an angular wedge. A
  flashlight, a security camera. Shares the raycaster; only adds an angle mask.
- **Directional / sun light** — parallel rays, no distance falloff, shadows
  cast in a single direction. Needed the moment anyone builds an outdoor scene.
- **Line / area light** — a glowing strip, a window. Softer, no single origin.

**Why it must be pinned now:** the `Light` data model has to anticipate these
or it gets widened repeatedly later. The choice is between one `Light` class
with a `shape` field versus a small class hierarchy.

**Recommendation:** one `Light` class with a `shape` enum (`point`, `cone`,
`directional`, `line`). Cone is the highest-value addition and the cheapest —
schedule it within or immediately after Phase L2.

### 1.2 Light cookies (gobos)

A texture mask multiplied into a light so it projects a pattern — window
blinds, foliage dapple, a caustics ripple. Mechanically tiny (one extra texture
multiply) with a large visual payoff. Interacts with the cone decision (1.1),
since a cookie is most useful on a spotlight.

**Recommendation:** in scope as a small, high-value feature. Pin the data model
hook now (`Light` carries an optional cookie texture); build after L2.

### 1.3 Occluders: strictly binary?

The committed design treats occluders as binary — block or do not. A coloured
glass window casting a tinted shadow, or a curtain casting a partial one, is
the same feature as "translucent occluder", which LIGHTING_DESIGN.md Section 9
already lists as a non-goal.

**Recommendation:** confirm occluders are strictly binary and state it as an
explicit decision in LIGHTING_DESIGN.md, so it reads as a choice rather than an
omission.

### 1.4 Ambient ownership

A scene may have both a day/night cycle *and* scripted ambient changes (a cave
entrance darkening the scene). Something must arbitrate when both want to set
ambient. This expands LIGHTING_DESIGN.md open question 3.

**Recommendation:** model ambient as a small *stack of contributors* (base,
day/night, scripted) resolved each frame, rather than a single mutable value.
Cleaner to design than to retrofit.

### 1.5 Colour space for blending

Additive light blending is only physically correct in **linear** colour space.
pygame blends in sRGB by default, which makes overlapping lights slightly
wrong — typically too bright in the mid-tones. Most 2D engines accept this
error; it is a legitimate choice.

**Recommendation:** accept sRGB blending for simplicity, but record it as a
known, deliberate decision in LIGHTING_DESIGN.md — not an accident. Revisit only
if a game's art direction demands physically-accurate light mixing.

### 1.6 CPU normal mapping without a GL backend

LIGHTING_DESIGN.md rules out tier-4 shader lighting. There is a middle option:
normal-mapped lighting computed on the CPU with NumPy — the light-direction dot
product as per-pixel array math, per light, per sprite. Too slow for many
dynamic lights; viable for a few hero lights.

**Recommendation:** remains a non-goal, but add a line to LIGHTING_DESIGN.md
Section 9 noting that CPU normal mapping via NumPy was considered — so a future
reader knows normal mapping is not strictly gated on a GL backend.

### 1.7 Light data format versioning

Once lights appear in scene-descriptor files and save files, the light schema
is a serialized format. The engine has `migrations.py` and a
`VERSIONING_GUIDE.md`.

**Recommendation:** light data must participate in the existing migration
system from the first version it is serialized. A schema version field on
serialized light data, and a migration path, or old scene/save files break on
any change.

---

## 2. Integration With Existing Systems

The committed documents describe lighting largely in isolation. It touches many
shipped systems; each needs a decision.

### 2.1 Camera and zoom

`Camera` supports zoom. When the player zooms, the light map can either
re-render at the new scale or scale the cached surface. This directly affects
the resolution-scaling maths in LIGHTING_PERFORMANCE.md Section 5.

**Recommendation:** re-render dynamic lights at the new scale; scale-blit
cached static lights and accept minor softness during the zoom. Confirm against
`camera.md`.

### 2.2 Scene transitions

`transitions.py` performs scene fades. A fade composited *before* the light
multiply behaves differently from one composited *after*. A fade-to-black over
an already-dark lit scene is not the same as over a bright one.

**Recommendation:** transitions composite *after* lighting — they act on the
final lit frame. State the ordering in LIGHTING_DESIGN.md Section 6.4 as a
pipeline step.

### 2.3 Accessibility

The engine has a `reduced_motion` flag and an `ACCESSIBILITY_STANDARDS.md`.
Lighting introduces two photosensitivity risks: **flicker** and **bloom
pulsing**. Rapid, high-contrast flashing can trigger seizures.

**Recommendation:** a "reduced flashing" lighting mode, gated by the existing
accessibility flag — clamps flicker amplitude and bloom pulse rate. This is not
optional polish; it belongs in `ACCESSIBILITY_STANDARDS.md` and should land with
the flicker work in Phase L1.

### 2.4 Save system

`save_manager.py` persists game state. If the player turns a light off, that
state is probably expected to persist.

**Recommendation:** lights must be serializable and addressable by id.
Cosmetic-only properties (flicker phase) are *not* saved; gameplay-relevant
state (enabled, colour if scripted) is. Ties to item 1.7.

### 2.5 Particles

LIGHTING_DESIGN.md Section 8 already decided glowing particles do not
contribute to the light map by default. The inverse is unaddressed: should
particles be *lit* by the light map?

**Recommendation:** particles are lit as part of whichever plane they render
on (usually `ACTOR` or `FOREGROUND`) — no special case. Confirm and record.

### 2.6 Asset pipeline

Light cookies (1.2), normal maps (1.6), and baked light maps (4.1) are all
**assets**. `asset_loader.py` and `paths.py` do not know about them.

**Recommendation:** baked light maps are generated artefacts, written to a
known cache path, not checked into source control. Cookies and normal maps are
authored assets loaded like sprites. Decide before any baking feature is built.

---

## 3. Gameplay Lighting (Light as a Mechanic)

Every committed document treats lighting as *rendering*. In many games light is
a *mechanic*: stealth visibility, light-based puzzles, enemies reacting to being
lit or to standing in shadow.

This needs a **light query API**, distinct from the rendering path:

```
lighting.is_lit(world_point) -> float   # 0.0 fully dark .. 1.0 fully lit
lighting.light_level(world_rect) -> float
```

It samples the light map or tests visibility polygons. It is a different code
path from compositing and is far easier to design in than to bolt on.

**Why it must be pinned now:** if the light map is the source of truth for
queries, the light map must be readable on the CPU at query time — which
constrains the resolution-scaling and GPU-backend decisions
(LIGHTING_PERFORMANCE.md Section 5, item 5.3 below). A GPU-resident light map is
expensive to read back.

**Recommendation:** decide explicitly whether gameplay lighting is in scope. If
yes, it shapes the backend choice and should be a named phase. If no, state it
as a non-goal so no one assumes it.

---

## 4. Deferred Optimisations

Recorded so they are not "discovered" later. None is part of the initial build.

### 4.1 Baking static light maps to disk

The logical endpoint of the static-light insight (LIGHTING_PERFORMANCE.md
Section 1). For a fully static scene — a hand-authored dungeon with no dynamic
lights — the entire light map is computed once, saved as an asset, and at
runtime merely loaded and blitted. Runtime lighting cost: effectively zero.

**Recommendation:** worth a dedicated late phase. It is the cheapest possible
"optimisation" because it moves the cost out of the game entirely. Depends on
the asset-pipeline decision (2.6).

### 4.2 Combined-light spatial batching

When many small lights overlap (a row of candles), their combined contribution
to a region can sometimes be computed once rather than per-light. More complex
than it is worth early.

**Recommendation:** documented, not committed — alongside dirty-rect
compositing and threading in LIGHTING_PERFORMANCE.md Section 7.

### 4.3 SDL2 hardware-accelerated compositing

The significant one. `pygame-ce` exposes `pygame._sdl2` with `Texture` and
`Renderer` — GPU-accelerated blitting and blend modes, *without* writing
shaders. Most light-map compositing (additive accumulation, multiply) maps onto
SDL2 texture blend modes and would run on the GPU.

This is not the tier-4 shader story; it is a *backend* decision. The engine is
`Surface`-based throughout, so this is engine-wide, not lighting-specific — but
lighting is the system most likely to need it.

**Caveat:** a GPU-resident light map is expensive to read back to the CPU,
which conflicts with the gameplay-query API (Section 3). The two decisions are
coupled.

**Recommendation:** out of scope for the lighting work itself, but it deserves
a paragraph in LIGHTING_DESIGN.md Section 9 as a known future backend, with the
read-back caveat noted.

### 4.4 Multiply precision loss (known issue)

Repeated `BLEND_RGBA_MULT` compositing at 8 bits per channel crushes dark tones
into visible banding.

**Recommendation:** accept it initially; record it as a known issue. If quality
demands it later, accumulate the light map at higher precision before the final
multiply.

---

## 5. Failure Modes and Edge Cases

The raycaster has corner cases that become bug reports if not given defined
behaviour up front. They need an explicit "expected behaviour" list before
Phase L2:

| Case | Question |
|---|---|
| Light exactly on an occluder edge | Does the ray self-intersect? Define a tolerance. |
| Light inside a solid wall | Emit nothing? Emit a tiny polygon? |
| Zero-length merged edge | Skipped silently during edge merging. |
| Fully enclosed light (sealed room) | Polygon is the room interior — confirm it terminates. |
| Degenerate / collinear polygon | Defined output, not a crash. |
| Light radius zero or negative | Clamped, as the current `Light` already clamps intensity. |

**Recommendation:** this table becomes a section of LIGHTING_DESIGN.md when
Phase L0 sign-off happens, and each row becomes a raycaster unit test in Phase
L2.

---

## 6. Tools for Developing the Engine

Distinct from player-facing tools — these help build and debug the lighting
system itself. The engine already has a `debug/` module with an overlay and
inspector.

| Tool | Purpose |
|---|---|
| Lighting geometry visualiser | Draw the visibility polygons, raw occluder edges (to see edge-merging work or fail), and each light's bounding circle. When a shadow looks wrong, you must *see* the geometry. |
| Single-light isolation (solo / mute) | Debug one light's polygon without others on screen — like an audio mixer solo. |
| Benchmark harness — visual mode | The harness (LIGHTING_PERFORMANCE.md Section 10) should also render to a window so a human can confirm "fast" also means "correct". |
| Golden-image regression test | Render a fixed lit scene, diff against a committed reference image. Lighting bugs are often visual, not numeric — a polygon-winding bug fails a pixel diff but not a timing test. Pairs with the raycaster unit tests. |

**Recommendation:** the geometry visualiser is the highest priority and should
land in Phase L2 alongside the raycaster — debugging the raycaster blind is
very slow.

---

## 7. Tools to Provide to Engine Users

The most underdeveloped area in the committed documents, and arguably the
highest-value — this is what makes the lighting system *pleasant* rather than
merely *capable*. The engine's existing systems set the expectation.

### 7.1 Light presets

`particles/presets.py` already establishes the pattern. Lighting should match
it: named constructors — `Light.torch()`, `Light.candle()`,
`Light.flashlight()`, `Light.moonlight()` — with colour, radius, falloff, and
flicker pre-tuned. A good-looking torch should be one line, not six tuned
numbers.

### 7.2 Lights in the scene-descriptor format

The engine has `scene_descriptor.py` and a `SCENE_AUTHORING_GUIDE.md` —
declarative, file-driven scenes. Lights should be placeable *in that file
format*, not only in code. This is the difference between lighting being a
programmer feature and a designer feature, and the committed documents do not
mention it.

**Recommendation:** in scope. Add a lights section to the scene-descriptor
schema and to `SCENE_AUTHORING_GUIDE.md`. Depends on lights being serializable
(item 2.4).

### 7.3 Live light editor

Given the scene-descriptor system and the live theme-reload the engine already
has, an in-game editor to drag lights and tune them with sliders while the game
runs is squarely in the engine's spirit. Likely a late phase.

**Recommendation:** name it as a goal now, even if unscheduled, so the data
model stays editor-friendly — lights serializable, addressable by id, tunable
at runtime.

### 7.4 Authoring-time lint / warnings

Tie the performance budget to the tooling. If a scene loads with 60
shadow-casters, or a light radius larger than the whole tilemap, the engine
logs a warning at load time. This makes LIGHTING_PERFORMANCE.md's budget
*self-enforcing* — the game developer does not have to remember to read it.

**Recommendation:** in scope, low cost. Land it with Phase L5 (the
shadow-caster cap), since they share the same thresholds.

### 7.5 Recipes in the using-guide

`using_pygame_engine.md` and the `examples/` directory set the expectation of
concrete worked examples. Lighting should match it: "flashlight that follows
the mouse", "lightning flash", "campfire with flicker", "torch the player
carries".

**Recommendation:** one example file per phase as it lands, mirroring how every
existing phase shipped an example.

---

## 8. Priority Summary

If this work is scheduled, the items above sort roughly into:

**Decide before any code (Phase L0):** light shapes (1.1), occluder binary
decision (1.3), colour space (1.5), data versioning (1.7), gameplay-query scope
(Section 3), the failure-mode table (Section 5), and the SDL2 backend question
(4.3) — because it is coupled to the gameplay-query decision.

**Build alongside the committed phases:** accessibility / reduced flashing
(2.3, with L1), the geometry visualiser (Section 6, with L2), cone lights and
cookies (1.1, 1.2, after L2), scene-descriptor lights and presets (7.1, 7.2,
with L3), authoring lint (7.4, with L5).

**Genuinely deferrable:** baked light maps (4.1), the live editor (7.3),
combined-light batching (4.2) — all valuable, none blocking.

The single most important item to resolve early is **Section 3 (gameplay
lighting)**: whether light is a mechanic or only a visual. It changes the
backend choice, the resolution strategy, and whether the light map must be
CPU-readable — and almost nothing else can be safely designed until it is
answered.
