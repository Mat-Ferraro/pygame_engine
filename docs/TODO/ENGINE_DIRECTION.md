# pygame_engine — Engine Direction: Principles, Additions, Open Questions

**Version:** 0.1-draft
**Status:** Direction document — principles proposed, additions unscheduled.
**Authority:** Engine-wide. Supplements ARCHITECTURE.md. Companion to the
LIGHTING_* document set.

This document compiles the outcome of a design review of the engine. It has
three parts:

1. **Design principles** — rules that should govern how every new system is
   built. These are proposed; they become binding once accepted.
2. **Recommended additions** — a ranked list of systems the engine is missing,
   with the design constraints each must satisfy.
3. **Open questions** — decisions to make before, or alongside, the additions.

The engine's stated purpose: **a starting point for any and all 2D games.** It
must stay flexible and generic. Every recommendation below is shaped by that
purpose. Nothing here is scheduled; the purpose of writing it down is so the
decisions are made deliberately rather than discovered mid-implementation.

---

## Part 1 — Design Principles

These are the principles that keep a general-purpose engine general. They are
not features; they are constraints on how features are built.

### P1 — Primitive, not policy

The engine provides primitives. Games provide policy.

A primitive is genre-neutral: swept collision, an update loop, a spatial query.
Policy is genre-specific: gravity, jump height, "how a platformer character
moves." Policy belongs in the game, never in the engine.

**The test:** for any proposed system, state it as a genre-neutral primitive.
If it cannot be stated without assuming a genre, it does not belong in the
engine. Example: `move_and_collide(rect, velocity) -> collision_info` is a
primitive — it resolves movement and reports what happened. A `PlatformerBody`
with built-in gravity is policy.

"Flexible" does not mean "build less and leave gaps." An unfilled gap is not
flexibility; it is unfinished work that every game must then redo. Genuinely
generic engines are *opinionated about primitives and silent about policy* —
they ship a sharp, well-built foundation and decline to dictate what is built
on it.

### P2 — Editor parity / no privileged path

A game can be built **entirely in code, with no editor**. A game can be built
**with the editor**. Neither path is privileged, and a developer can **switch
between them at any point in development** without penalty.

This is a no-privileged-path rule, and it is architecturally demanding. The
principle that makes it hold:

> **The editor is a program that uses the public API. It has no private door.**

Consequences, all binding:

- The editor produces the **same** scene-descriptor data a developer could
  write by hand. No editor-only format, no editor-only fields.
- The scene-descriptor format is **fully hand-authorable** and **fully
  round-trippable**: anything the editor expresses, a human can write; anything
  the descriptor holds, code can construct directly.
- There is **no "editor mode"** in the engine. The engine loads a scene and
  does not know or care whether a human, the editor, or pure code produced it.
- **Build-vs-load convergence:** a scene built by code and the "same" scene
  loaded from a descriptor must produce an indistinguishable object graph. This
  is a property that must be asserted by an automated test in CI.
- **Round-trip in both directions:** code can serialize an existing scene *out*
  to a descriptor the editor can open; an editor-authored descriptor can be
  picked up by code. Every engine object that can appear in a scene must be
  both constructable in code and serializable back to descriptor form.

This principle is cheap to state and expensive to maintain — it erodes every
time a feature is "just easier" to do editor-side. Defences: the convergence
test in CI, a `REVIEW_CHECKLIST.md` line ("does this work code-only? does it
round-trip?"), and building one real game fully code-only and one fully
editor-first to exercise both paths.

### P3 — Extensible without forking

A general-purpose engine succeeds by being *extended*, not by anticipating
every genre. A game must be able to add its own entity types, components, and
systems **without modifying engine source**.

The engine already has `extension_hooks` and a plugin loader — the right
instinct. The principle raises it to a first-class concern: "can a game extend
this without modifying it?" is a review question for every new system.

Interaction with P2: a game's custom entity type must round-trip through the
descriptor. At minimum the editor preserves unknown custom data rather than
dropping it on save; ideally it is taught the type through a registration
hook. An editor that silently discards a game's custom entities violates P2.

### P4 — Stated non-goals

A general-purpose engine has no natural finish line — there is always another
genre to support better. Without a stated scope boundary the roadmap is
infinite.

Every major system declares what it deliberately does **not** do. The LIGHTING_*
documents model this well. The engine as a whole needs the same: a maintained
list of non-goals (see Part 3).

### P5 — Validate with real games

Until a complete game ships on the engine, every priority in this document is a
hypothesis. The fastest way to validate the roadmap is not more analysis — it
is one finished small game.

The engine exists to make games. Planning that outruns building is a known
failure mode; the validation of an engine is a finished game, not a finished
specification.

---

## Part 2 — Recommended Additions

The engine is well-developed as an application/UI framework — strong UI,
scenes, state, animation, audio, theming, debug. It is thin as a *game*
framework. The additions below fill that gap. All are subject to the Part 1
principles, P1 (primitive, not policy) especially.

### Ranking

Importance weighs value-to-the-engine against effort and risk, and toward
"does the engine need this to be what it is trying to be."

| # | Addition | Importance | Effort | Notes |
|---|---|---|---|---|
| 1 | Move-and-collide kinematic helper | Critical | Low–Med | The platformer example already hand-rolls this. |
| 2 | Entity / actor base + group | Critical | Medium | The structural gap — no spine for the level. |
| 3 | Spatial partition (grid / quadtree) | High | Low–Med | Shared by collision, entity queries, lighting. |
| 4 | Collision layers / masks + rect-vs-rect | High | Low–Med | Player-vs-enemy-not-pickup. |
| 5 | Trigger / region volumes | High | Low | Room transitions, traps, zones. |
| 6 | Fixed-timestep / update-loop decision | High | Low | Architectural; invisible until it bites. |
| 7 | Extension surface hardening | Med–High | Medium | The mechanism that keeps the engine generic (P3). |
| 8 | Coroutine / sequencing scheduler | Med–High | Low | Cutscenes, scripted events, combos. |
| 9 | Game-object serialization story | Medium | Medium | Constraint on #2; shares design with the descriptor. |
| 10 | 2D Transform with parenting | Medium | Medium | Attached objects move for free. |
| 11 | Input action-mapping layer | Medium | Low–Med | Bind *actions*, not keys. May partly exist already. |
| 12 | Debug/inspector hook for game objects | Medium | Low–Med | Extensible inspection; pairs with #7. |
| 13 | Tiled (`.tmx`) importer | Medium | Medium | High-leverage for the *designer*. |

### Per-item design constraints

**#1 — Move-and-collide kinematic helper.** A primitive:
`move_and_collide(rect, velocity) -> collision_info`. It resolves movement
against solids (axis-separated swept resolution) and *reports* what happened.
It must not bake in gravity, jump height, or character-movement behaviour —
that is policy (P1). Currently the engine offers only broadphase
(`Tilemap.collides_rect`, `get_colliding_tiles`); resolution is missing.

**#2 — Entity / actor base + group.** The engine has a `Widget` base for UI and
no equivalent for game objects. Provide a deliberately **minimal** `Entity` —
position, lifecycle hooks, group membership, draw order — that assumes nothing
about genre. Not a full ECS: an ECS imposes a paradigm on every game and fights
the engine's existing clean OOP style (`Widget`, `Scene`, `Observable`). A
heavyweight `GameObject` with built-in health/physics/AI imposes a *genre*.
Thin is the feature.

**#3 — Spatial partition.** A genre-neutral structure: register rects, query a
region. It must not know about "tiles" or "characters". Build once, well — it
serves collision (#4), entity queries (#2), and the lighting `LightOccluder`
grid precisely *because* it knows about none of them.

**#4 — Collision layers / masks + rect-vs-rect.** Bitmask layers plus general
rect-vs-rect overlap. Naturally generic; no genre assumptions. Pairs with #1
and #3.

**#5 — Trigger / region volumes.** A rect plus enter/exit/stay callbacks.
Naturally generic. Small once #3 and #4 exist.

**#6 — Fixed-timestep / update-loop decision.** Decide: fixed timestep with
interpolation, or variable delta-time. It affects collision stability (swept
collision is far more stable at fixed step), determinism, replays, and any
future multiplayer. Nearly free to decide now; very expensive to change once
games depend on current behaviour. High importance *because* it is invisible
until it bites.

**#7 — Extension surface hardening.** Per P3 — a clean, documented way for a
game to register entity types, components, and systems without forking. The
mechanism by which the engine stays generic. Must satisfy the P2 interaction:
custom types round-trip through the descriptor.

**#8 — Coroutine / sequencing scheduler.** A small scheduler for scripted
sequences (`yield wait(1.0)`). Cutscenes, scripted events, ability combos.
Roughly 100 lines; natural sibling to the existing `TimeManager` and
`state_machine`. Genre-neutral.

**#9 — Game-object serialization story.** The existing `save_manager.py` serves
application/scene state; a *world of entities* raises a new question. Entities
serializable by default, addressable by stable id. This shares its design with
the scene-descriptor format — under P2 they are effectively the same problem
(the descriptor is serialized scene data). Design #9 *with* #2, not after.

**#10 — 2D Transform with parenting.** Lightweight parent/child transform
(offset, optionally rotation/scale) so attached objects — turret on a tank,
health bar over an enemy — move for free. Also cleans up the lighting "light
follows the player" case.

**#11 — Input action-mapping layer.** The generic primitive is *actions*: the
game binds "jump" to a key/button/axis and queries the action, not the key.
Enables rebinding and gamepad support for free. Check the existing
`input_manager` first — this may partly exist.

**#12 — Debug/inspector hook for game objects.** The `debug/` module inspects
the engine; once entities exist, they need inspection too. A general-purpose
engine cannot know what a game's entities contain, so this is an *extensible*
inspection interface, not a hardcoded panel. Pairs with #7.

**#13 — Tiled (`.tmx`) importer.** The tilemap is currently hand-constructed in
code. Tiled is the de facto 2D map editor. An importer lets designers use a
real tool. Standalone, low risk; high-leverage for the *designer* experience.

### Items 1–6 form one phase

Items 1 through 6 are not six separate features — they are one coherent layer:
the missing middle between "renders a tilemap" and "is a game." They share
infrastructure (the spatial grid underpins collision, entity queries, and
lighting occluders) and are most efficient built together, in roughly the
listed order, because each makes the next easier. In `roadmap.md` phase style
this is a single **"Phase 14 — Gameplay Foundations."** Items 7–13 are more
independent and can slot in as needed.

### Explicitly not recommended

- **A full ECS** — imposes a paradigm; fights the engine's OOP style. See #2.
- **A rigid-body physics engine** (rotation, joints, friction). Almost no 2D
  game on a UI-leaning engine needs it. If one does, integrating `pymunk` is a
  `DEPENDENCY_POLICY.md` decision, not an engine feature.
- **Networking** — huge surface area, niche demand; would dwarf everything
  else.
- **Genre-specific helpers** — platformer physics, top-down movement. These are
  the "policy" P1 forbids.

---

## Part 3 — Open Questions

To resolve before or alongside the additions.

### Q1 — What kind of games is the engine for?

Resolved by the user: **any and all 2D games.** The engine must stay flexible
and generic. This answer is why Part 1 exists and why every Part 2 item carries
a "primitive, not policy" constraint. Recorded here as the premise of the
document.

### Q2 — What is the engine's definition of "done"?

A general-purpose engine has no natural finish line. Per P4, the engine needs a
maintained list of non-goals — a stated scope boundary — or the roadmap is
infinite. Starting list (to be expanded):

- No full ECS, no rigid-body physics, no networking (Part 2).
- No genre-specific gameplay helpers.
- No GL/shader rendering backend (see the LIGHTING_* set; revisit only as a
  deliberate future backend decision).

### Q3 — Are we building an engine, or building games?

The honest question (P5). A growing specification for an engine that has not
yet shipped a game is a sign planning may be outrunning building. The
recommended response: freeze the list, pick the smallest game the list claims
cannot yet be built well, and build it. Let that game rank the list.

### Q4 — Fixed or variable timestep?

See addition #6. This is both an open question and a recommended addition
because it is a single architectural decision that shapes several systems. It
should be decided before the gameplay-foundations phase begins, not during it.

### Q5 — Is the scene descriptor ready to be the round-trip format?

P2 requires the scene-descriptor format to be fully hand-authorable and
round-trippable in both directions. Before the gameplay layer is built, audit
`scene_descriptor.py` against that requirement: can every existing scene
construct be both hand-written and serialized back out? Gaps found now are
cheap; gaps found after entities depend on the format are not.

### Q6 — How do custom (game-defined) types round-trip?

Per P3 + P2: when a game defines its own entity type, the editor must at
minimum preserve unknown data across a save round-trip, and ideally be taught
the type via a registration hook. Decide which — graceful preservation is the
floor, registration is the goal — before #7 (extension surface) is built.

---

## Part 4 — Recommended Next Step

The list in Part 2 is thorough — thorough enough. The most valuable next move
is not extending it further; it is **contact with reality** (P5):

1. Accept or revise the Part 1 principles. They are load-bearing and should be
   settled first — they constrain everything built afterward.
2. Resolve Q4 (timestep) and audit Q5 (descriptor round-trip). Both gate the
   gameplay-foundations phase.
3. Pick the smallest game that the list claims cannot yet be built well. Build
   it, code-only, to exercise P2 from the code side.
4. Let that game's friction re-rank Part 2. Every priority here is a hypothesis
   until a real game tests it.

More items can always be added. What is missing now is a finished game, not
more coverage.

---

## Appendix — Companion Documents

This document is engine-wide direction. The advanced 2D lighting work is
specified separately, as an unscheduled stretch goal, in:

- `LIGHTING_DESIGN.md` — architecture and design decisions.
- `LIGHTING_PERFORMANCE.md` — optimisation strategy and frame budget.
- `LIGHTING_ROADMAP.md` — phased delivery plan (L0–L5).
- `LIGHTING_OPEN_ITEMS.md` — backlog of considered-but-undecided items.

The lighting set and this document share design DNA: pin the architecture hard,
state non-goals explicitly, validate with real use. Principle P1 (primitive,
not policy) and P4 (stated non-goals) apply to the lighting work as much as to
the gameplay layer.
