# pygame_engine — Advanced 2D Lighting: Roadmap

**Version:** 0.1-stretch
**Status:** Stretch goal — not scheduled.
**Authority:** Supplements roadmap.md. Companion to LIGHTING_DESIGN.md and
LIGHTING_PERFORMANCE.md.

This document phases the advanced 2D lighting work into deliverable units. It
exists so that, *if* the work is scheduled, it can be picked up incrementally —
each phase shippable on its own, each leaving the engine in a working state.

This is a stretch goal. It is not on the committed roadmap. roadmap.md tracks
Phases 1–13 plus Phase A and Phase B as complete; this work would slot in as a
later, optional phase only if 2D lighting becomes a priority for the engine.

---

## 1. Guiding Principles

- **Every phase ships.** No phase leaves lighting half-working. The current
  radial system keeps functioning until a phase explicitly replaces it.
- **Cheap path always survives.** Shadow casting is opt-in per light
  (`cast_shadows`). Decorative lights stay cheap radial circles forever.
- **Measure from the start.** The debug overlay and benchmark harness land in
  Phase L1, not at the end, so every later phase is measured.
- **Optimisation is architectural, then incremental.** Phase L1–L2 bake in the
  caching model; later micro-optimisation follows PERFORMANCE_BUDGETS.md
  ("profile first").

---

## 2. Phase Overview

| Phase | Title | Delivers | Depends on |
|---|---|---|---|
| L0 | Design sign-off | Decisions in LIGHTING_DESIGN.md Section 8 resolved | — |
| L1 | Tier 1 refactor + instrumentation | Light map, baked texture, debug overlay, benchmark harness | L0 |
| L2 | Tier 2 shadow casting | Visibility polygon, `LightOccluder`, dirtiness model | L1 |
| L3 | Lighting layer model | Roles, `LightProfile`, multi-plane composite, backlit foreground | L2 |
| L4 | Tier 3 polish | Soft shadows, bloom, falloff curves | L2 |
| L5 | Crowd-scene scaling | LOD throttling, shadow-caster cap, predictable degradation | L2, L3 |

L4 and L5 are independent of each other and may be reordered or dropped.

---

## 3. Phase L0 — Design Sign-off

**Goal:** Resolve the open questions before any code is written.

| Item | Detail |
|---|---|
| Resolve API decisions | All of LIGHTING_DESIGN.md Section 8 confirmed |
| Resolve open questions | LIGHTING_DESIGN.md Section 10 — `LightProfile` attachment point, blur scope, day/night mapping |
| DEPENDENCY_POLICY.md entry | Add the `LightOccluder` interface rule: lighting must not import tilemap or entity types |
| PERFORMANCE_BUDGETS.md entry | Add the proposed lighting budget (LIGHTING_PERFORMANCE.md Section 9) as provisional |

**Exit criteria:** No unresolved design decision. No code.

---

## 4. Phase L1 — Tier 1 Refactor and Instrumentation

**Goal:** Replace the subtractive overlay with the additive light-map model,
and stand up measurement *before* the expensive work begins.

| Item | Detail |
|---|---|
| Baked falloff texture | One white radial texture at startup; lights are tinted scaled blits |
| Light-map surface | Persistent, reused; ambient fill; additive accumulation; multiply composite |
| Surface pool | Small scratch-surface pool; no per-frame `SRCALPHA` allocation |
| Coloured light | Verify a coloured light tints surfaces (the multiply model's payoff) |
| Deterministic flicker | Replace inline `import random`; inject or seed the RNG |
| Debug overlay | Light count, fill time — in the existing `debug/` module |
| Benchmark harness | Headless fixed scene; asserts composite time under budget; wired into CI |

**Exit criteria:** The light map renders coloured light correctly; the old
radial path is gone or wrapped; the benchmark harness runs in CI. No shadows
yet.

---

## 5. Phase L2 — Tier 2 Shadow Casting

**Goal:** Lights stop at walls. The realism centrepiece.

| Item | Detail |
|---|---|
| `LightOccluder` interface | Anything emitting `(x1,y1,x2,y2)` world-space segments |
| Tilemap occluder source | Tilemap emits occluders for collidable tiles |
| Edge merging | Collinear adjacent faces collapse at scene load |
| Visibility polygon raycaster | World-space; corner rays with ±offset; deterministic; pure |
| Polygon → mask render | Polygon fills a mask; falloff texture combined against it |
| `cast_shadows` flag | Per-light; system-wide `quality` enum |
| Dirtiness model | Static / dynamic / semi-static; skip raycast when clean |
| Tile-based occluder culling | Lights pull edges only from overlapped grid cells |
| Tests | Raycaster geometry under test — corners, collinear edges, fully-occluded light |
| Benchmark update | Harness extended to assert polygon-update time under budget |

**Exit criteria:** Shadow-casting lights are correctly occluded by walls; static
lights compute once and cache; the cheap radial path still works for
`cast_shadows=False` lights; raycaster tests pass.

---

## 6. Phase L3 — Lighting Layer Model

**Goal:** Layers occlude or are backlit, per LIGHTING_DESIGN.md Section 6.

| Item | Detail |
|---|---|
| `LightLayer` roles | `BACKGROUND`, `OCCLUDER`, `ACTOR`, `FOREGROUND` |
| `LightProfile` | `blocks_light`, `receives_light`, `light_mode`; role-driven defaults |
| Multi-plane composite | Scene-owned plane ordering; light multiply before foreground |
| Silhouette mode | Foreground renders dark toward ambient — implement first, trivial |
| Backlit rim light | Sample light map at foreground outline; additive rim — the target look |
| Example | A scene demonstrating canopy/overhang backlighting |

**Exit criteria:** A foreground plane (e.g. a tree canopy) is backlit while
occluder walls cast shadows correctly, in one scene.

---

## 7. Phase L4 — Tier 3 Polish

**Goal:** Visual refinement on top of L2. Each item independently optional.

| Item | Detail |
|---|---|
| Soft shadows | Downscale-blur the light mask; global quality setting |
| Falloff curves | Per-light `linear` / `quadratic` / `smooth`; `smooth` default |
| Bloom | Extract bright regions, blur at quarter-res, add back |

**Exit criteria:** Soft-shadowed, bloomed lighting renders within the
LIGHTING_PERFORMANCE.md Section 9 budget. Any subset of items may ship; none is
mandatory.

---

## 8. Phase L5 — Crowd-Scene Scaling

**Goal:** Graceful behaviour when a scene exceeds its lighting budget.

| Item | Detail |
|---|---|
| LOD update throttling | Distant / marginal lights recompute every 3rd–5th frame |
| Shadow-caster cap | System-wide maximum; configurable |
| Predictable degradation | Over the cap: nearest N cast, rest fall back to radial; log a warning |
| Debug overlay update | Surface shadow-caster count and "degraded" state |

**Exit criteria:** A deliberately over-budget scene degrades predictably and
logs the degradation, instead of silently dropping frames.

---

## 9. Explicitly Out of Scope

Carried over from LIGHTING_DESIGN.md Section 9, restated so the roadmap does not
quietly grow:

- Normal-mapped / shader lighting (tier 4) — would require a GL backend.
- Continuous z-depth for lighting — four roles suffice.
- True light bleed through foreground planes.
- Coloured light filtered by translucent occluders.
- Threaded polygon computation — documented in LIGHTING_PERFORMANCE.md Section
  7 as a known avenue; not built.

If any of these is ever wanted, it is a *new* design effort with its own
sign-off, not an extension of this roadmap.

---

## 10. Effort Shape

A rough sense of relative size, not a schedule. No calendar estimates — this is
a stretch goal with no committed timeline.

| Phase | Relative size | Risk |
|---|---|---|
| L0 | Small | Low — it is decision-making |
| L1 | Medium | Low — well-understood compositing |
| L2 | Large | Medium — raycaster geometry is bug-prone; tests mitigate |
| L3 | Medium | Low–Medium — mostly compositing order |
| L4 | Medium | Low — independent, droppable items |
| L5 | Small–Medium | Low — built on L2/L3 primitives |

The honest assessment: L2 is the hard phase and the one that delivers the
"whoa". L1 must precede it to make it measurable. Everything else is additive
polish that can be scheduled, reordered, or dropped without harming what
shipped before it.
