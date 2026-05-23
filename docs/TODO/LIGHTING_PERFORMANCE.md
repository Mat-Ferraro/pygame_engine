# pygame_engine — Advanced 2D Lighting: Performance

**Version:** 0.1-stretch
**Status:** Stretch goal — not scheduled. Strategy only.
**Authority:** Supplements PERFORMANCE_BUDGETS.md and LIGHTING_DESIGN.md.

Lighting is a known performance hit. This document defines the optimisation
strategy for the advanced lighting system *before* it is built, so that the
expensive parts are designed to be cheap from the start rather than retrofitted
after a profiler says so.

This does not contradict PERFORMANCE_BUDGETS.md Section 3 ("only optimise after
profiling"). The strategies here are *architectural* — they shape the design,
not micro-optimise finished code. Choosing a caching model up front is
architecture; shaving a loop after profiling is optimisation.

---

## 1. The Core Insight: Most of a Lit Scene Is Static

The single highest-leverage fact about 2D lighting performance:

> A torch bolted to a dungeon wall, in a room whose walls do not move, produces
> the **exact same light every frame**.

Recomputing its visibility polygon 60 times a second is pure waste. The entire
optimisation strategy follows from exploiting what does not change.

This is why the design (`LIGHTING_DESIGN.md` Section 7) splits lights into
**static**, **dynamic**, and **semi-static**. In a typical scene — one moving
player light, several fixed wall torches — this turns "N lights, N raycasts"
into "1 raycast, N−1 cached blits". That is frequently a 5–10× win for the cost
of one boolean and an invalidation call.

The mechanism is a **dirtiness model**: each light tracks whether anything
affecting it has changed since last frame — its own position, radius or colour,
or any occluder within its radius. If nothing is dirty, the raycast is skipped
and last frame's cached light surface is reused.

**Flicker must not defeat this.** Flicker modulates intensity and colour only,
never geometry. A flickering wall torch keeps its cached polygon and varies
only blit alpha. See `LIGHTING_DESIGN.md` Section 7.

---

## 2. Ownership: Who Pays the Cost

Every optimisation lives at one of three levels. Confusing them is how engines
end up either bloated or slow. The guiding principle:

> The engine makes the cheap thing automatic and the expensive thing opt-in.
> The game decides how much it spends.

### 2.1 Engine — automatic, no API surface

The game gets these for free and should not have to think about them:

- Viewport culling and per-light culling.
- The baked falloff texture (Section 3).
- Surface pooling — no per-frame `SRCALPHA` allocation.
- Edge merging (Section 4).
- The static / dynamic / semi-static dirtiness model.
- Light-map resolution scaling, with a sane default (Section 5).
- Static-light precompute on scene load.

### 2.2 Shared — engine exposes, game tunes

Dials the game turns:

- `cast_shadows: bool` per light.
- A `LightQuality` enum (`low` / `medium` / `high`) mapping to resolution
  scale, soft-shadow on/off, and the shadow-caster cap.
- Explicit light-map resolution scale, overriding the default.
- A maximum shadow-caster count.
- Per-light update-throttle / level-of-detail priority (Section 6).

### 2.3 Game — authoring discipline, engine assists

The engine cannot enforce taste. The *budget discipline* — few hero lights,
sane radii, reasonable occluder counts per room — is the game's job. But the
engine assists in three concrete ways (Section 8): it documents the budget, it
makes costs visible through a debug overlay, and it degrades loudly rather than
silently.

---

## 3. The Baked Falloff Texture

The current system rebuilds a light's gradient every frame from up to 48
concentric `draw.circle` calls, per light. This is the first thing to remove.

A light's gradient depends only on radius, colour, and intensity. The system
bakes **one** white radial-falloff texture at a fixed size (e.g. 256×256) at
startup. Each light becomes a scaled, colour-tinted blit of that texture.

This collapses per-frame cost from thousands of circle draws to one scaled blit
per light. The scaling also removes the concentric-circle banding for free.

---

## 4. Occluder Optimisations

### 4.1 Edge merging

A 20-tile wall is **one** segment, not 20. Collinear adjacent tile faces
collapse into single long segments when the tilemap loads. Fewer edges means
fewer rays, smaller polygons, faster fills — and the saving compounds with
every other optimisation. This is a one-time cost at scene load, not a
per-frame cost.

### 4.2 Tile-based occluder culling

A light must not raycast against every wall on the map. Occluder edges are
bucketed into a spatial grid — the tilemap is already a grid, so this is nearly
free — and a light pulls edges only from the cells its radius overlaps. This
keeps each raycast `O(nearby edges)` rather than `O(all edges)`.

---

## 5. Light-Map Resolution Scaling

The highest-impact knob that is easiest to overlook.

Lighting is low-frequency information: smooth gradients, no sharp detail. The
entire light map can be rendered at **half or quarter resolution** and upscaled
at composite time. Quarter resolution is 1/16th the pixels to fill. Because the
upscale is bilinear, it makes shadows look *softer*, not worse.

This single setting can be the difference between 30 and 60 fps. It is one
integer in the configuration and belongs to the `LightQuality` enum.

---

## 6. Culling and Level-of-Detail

**Viewport cull.** A light whose circle does not intersect the viewport is
skipped entirely. (The current system already does a version of this.)

**Occlusion cull.** A light whose circle intersects the viewport but which is
fully behind an occluder relative to the camera can also be skipped. A
nice-to-have, not essential.

**Update throttling / LOD.** A light several screens away does not need 60 Hz
updates. Lights carry an update-priority; distant or marginal lights recompute
every 3rd or 5th frame. This is the graceful-degradation lever for crowded
scenes.

---

## 7. Optimisations Documented but Not Committed

These are recorded so they are not "discovered" later as if new. They are not
part of the initial build.

**Dirty-rectangle compositing.** If only the player's light moved, only the
screen region it touched (this frame ∪ last frame) needs recompositing; the
rest of the lit frame is identical. Genuinely effective, but it interacts with
the whole render pipeline. Defer to a later phase, build only if profiling
demands it.

**Threaded polygon computation.** Visibility-polygon computation is
embarrassingly parallel across lights and is pure math. However: Python's GIL
means `threading` gives no real parallelism for CPU work, and `multiprocessing`
serialisation overhead tends to eat the gain for frame-rate-sensitive work.
**Documented as a known avenue; not built.** If lighting is still the
bottleneck after every cheaper optimisation here, that is the time to revisit —
not before.

---

## 8. Observability Is Part of the Optimisation

A performance feature without observability is a trap: the game developer
cannot optimise what they cannot measure. The engine assists game-side budget
discipline in three ways.

### 8.1 Document the budget

PERFORMANCE_BUDGETS.md gains a lighting section with concrete numbers — see
Section 9 below. A budget that is written down is enforceable; one that is not
is aspirational.

### 8.2 Make costs visible

The engine's existing `debug/` module gains a lighting overlay showing, per
frame: total light count, shadow-caster count, rays cast, and light-map fill
time. A developer who can *see* "shadow casters: 47" will fix it. Invisible
costs are the ones that bite. This overlay is part of the lighting work, not
optional polish.

### 8.3 Degrade loudly, not silently

If the game exceeds the shadow-caster cap, the engine degrades **predictably**
— for example, the nearest N lights cast shadows and the rest fall back to
cheap radial circles — and logs a warning. It must never quietly tank the frame
rate. Predictable degradation plus a log line is the difference between a bug
the developer can find and one they cannot.

---

## 9. Proposed Lighting Frame Budget

To be merged into PERFORMANCE_BUDGETS.md Section 2 if this work is scheduled.
All numbers assume the 60fps / 16.7ms target and modest hardware, consistent
with the existing budget document.

| Lighting work | Proposed budget | Notes |
|---|---|---|
| Light map composite | 1.5ms | Additive accumulation + multiply onto world |
| Shadow polygon updates | 1.5ms | *Dynamic and semi-static lights only* |
| Foreground backlight pass | 0.5ms | Rim-light sampling |
| **Lighting total** | **3.5ms** | Drawn from the 8.0ms `Scene render()` budget |

Static lights contribute **zero** per-frame polygon cost — their cost is paid
once at scene load and is governed by PERFORMANCE_BUDGETS.md Section 4
("one-time startup code"), not the frame budget.

**Reference target for game authors:** at `LightQuality.medium`, a scene should
sustain **8–12 shadow-casting lights plus any number of cheap radial lights**
within this budget. Beyond that, authors should rely on the static/dynamic
split, LOD throttling, and the shadow-caster cap.

These numbers are provisional. They must be validated by the benchmark harness
(Section 10) before being treated as real.

---

## 10. Benchmark and Regression Harness

Lighting performance dies by a thousand cuts: a feature is "only" 0.3ms slower,
nobody notices, six commits later the scene runs at 45fps and someone is
bisecting. The defence is a benchmark that fails CI the day a regression lands.

**Specification:**

- A fixed, headless scene — for example 30 lights and 200 occluders in a
  fixed layout — runnable without a display.
- It measures average light-update time and light-map composite time across a
  fixed number of frames.
- It asserts both stay under the Section 9 budgets, with a tolerance margin.
- It runs in CI and fails the build on regression.
- It is wired into `testing_strategy.md` alongside the existing suite.

The harness should exist from the first phase of implementation, not be added
at the end. An enforced budget is worth more than an aspirational one — and the
project already values this kind of rigor (PERFORMANCE_BUDGETS.md,
REVIEW_CHECKLIST.md, the existing test suite).

---

## 11. Summary — Build Order for Performance

If and when this work is scheduled, the optimisations should land in this
order, because each makes the next easier to measure:

1. Baked falloff texture + surface pooling (Section 3) — removes the current
   per-frame waste; do this with the tier-1 refactor.
2. The dirtiness model and static/dynamic split (Section 1) — the largest
   single win; build it *with* shadow casting, not after.
3. Edge merging + tile-based occluder culling (Section 4) — keeps raycasts
   bounded as scenes grow.
4. Light-map resolution scaling (Section 5) — the cheapest large win; one
   integer.
5. The debug overlay (Section 8.2) and benchmark harness (Section 10) — so
   every subsequent change is measured.
6. LOD throttling and the shadow-caster cap (Section 6) — graceful degradation
   for crowded scenes.
7. Dirty-rectangle compositing and threading (Section 7) — only if profiling
   still demands it.
