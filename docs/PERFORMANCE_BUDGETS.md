# pygame_engine — Performance Budgets and Policy

**Version:** 2.0-design
**Authority:** Supplements ARCHITECTURE.md

This document defines frame time budgets, when to optimise, and how to
document performance-critical code. Without defined budgets, performance
discussions are subjective. With them, they are not.

---

## 1. The Target

**60 frames per second on modest hardware.**

Modest hardware means a mid-range laptop from 2020 — not a gaming PC,
not a decade-old machine. At 60fps, the total frame budget is 16.7ms.

All budget numbers below assume 60fps. If a game targets 30fps (33.3ms
per frame), budgets scale proportionally.

---

## 2. Frame Budget Allocation

| System | Budget | Notes |
|---|---|---|
| Scene update() | 4.0ms | All game logic, physics queries, AI |
| Scene render() | 8.0ms | All drawing — background, widgets, overlays |
| UI event routing | 0.5ms | Widget tree traversal per event |
| Observable notifications | 0.5ms | All reactive updates combined |
| Engine overhead | 1.7ms | Loop, input polling, display flip |
| Audio processing | 2.0ms | Managed by pygame-ce — rarely exceeded |
| **Total** | **16.7ms** | |

These are soft targets. Occasional spikes are acceptable. Sustained
violation of any budget warrants investigation.

**Frame spike threshold:** A single frame taking more than 33ms (2×
the budget) is a spike. Spikes are acceptable up to once per ten
seconds. More frequent spikes require investigation.

---

## 3. When to Optimise

**Only after profiling confirms a specific system is over budget.**

Never optimise speculatively. Premature optimisation is a documented
source of bugs — it makes code less readable for a performance improvement
that exists only in the developer's imagination, not in measured data.

Profiling tools:
- The frame budget visualiser (Phase 5.1 — built into the engine)
- `cProfile` for identifying hot functions
- `pygame.time.get_ticks()` for manual measurements

When profiling confirms a system is over budget, the optimisation must:
1. Be measured before and after (not just "feels faster")
2. Have the measurement recorded in a comment (see Section 5)
3. Not break any existing tests

---

## 4. When NOT to Optimise

The following are explicitly not performance concerns:

**One-time startup code** — asset loading, scene construction,
`_build_layout()`. These run once. Even 100ms is imperceptible on startup.

**Code that runs once per user action** — button clicks, scene transitions,
save operations. These have human-scale timing (>100ms is fine) and are
not on the critical frame path.

**Code that runs in development mode only** — debug tools, the editor,
the frame budget visualiser itself. Development mode does not need
production-level performance.

**Code that is not in `render()` or `update()`** — if it does not run
every frame, it does not need frame-scale optimisation.

---

## 5. Documenting Performance-Critical Code

Any optimisation that makes code less readable must have a benchmark
comment proving the improvement was measured:

```python
# Binary search over linear scan.
# Benchmark (font.size 22px, 500-char string, 60fps):
#   Linear: ~2.1ms — unacceptable for render()
#   Binary: ~0.04ms — 50x improvement
# The complexity is justified by the measured gain.
lo, hi = 0, len(text)
while lo < hi:
    mid = (lo + hi + 1) // 2
    ...
```

Format:
```
# Benchmark (context):
#   Before: Xms — why that was unacceptable
#   After:  Xms — the improvement
# Justification sentence.
```

Without this comment, a future developer will see complex code and
"simplify" it — re-introducing the performance problem. The benchmark
comment is the defensive note that prevents this.

---

## 6. Observable System Performance

The observable system runs on every frame if subscribed values change.
Specific rules for observable usage:

**Do not subscribe to high-frequency values in render paths.**

A render method must not call observable.subscribe() — subscribe once
in on_enter(), unsubscribe in on_exit() via the SubscriptionGroup.

**High-frequency observables need the equality check.**

`Observable.set()` with the same value must not fire subscribers. The
equality check in `set()` is the primary performance guard for
high-frequency observables like mouse position or frame counter.

**Transaction batching is required for multi-property changes.**

Setting four properties without a transaction fires four events. Setting
them within `with observable.transaction():` fires one. For the inspector,
four events = four redraws. Always use transactions for related changes.

```python
# Wrong — four events for one logical change
node.rect.x = 120
node.rect.y = 64
node.rect.w = 580
node.rect.h = 400

# Correct — one event for one logical change
with node.rect.transaction():
    node.rect.x = 120
    node.rect.y = 64
    node.rect.w = 580
    node.rect.h = 400
```

---

## 7. Render Performance Rules

**Never call `font.render()` in a render method without caching.**

`font.render()` creates a new Surface every call. In a render method at
60fps, this is 60 allocations per second per text element. Use the dirty
flag caching pattern:

```python
def render(self, surface: pygame.Surface) -> None:
    if self._dirty:
        self._cache = self._font.render(self._text, True, self._colour)
        self._dirty = False
    surface.blit(self._cache, self.rect)
```

**Never read from `pygame.time.get_ticks()` in `render()`.**

Time-dependent rendering violates Restriction R10 and prevents caching.
Update a state variable in `update(dt)` and read it in `render()`.

**Clip before drawing lists.**

When drawing a scrollable list of items, set the clip region before the
loop. Items outside the clip region are not drawn even if `blit()` is
called for them, but setting the clip allows pygame to skip GPU work:

```python
old_clip = surface.get_clip()
surface.set_clip(self._list_rect)
for item in self._visible_items():
    item.render(surface)
surface.set_clip(old_clip)
```

---

## 8. Memory Performance

**Target: zero per-frame allocations in steady state.**

Steady state means a scene is running normally with no transitions or
layout changes. The common sources of per-frame allocation to avoid:

- `font.render()` without caching (creates a Surface each call)
- Building lists in render() — `[child for child in ...]` creates a list
- String formatting in render() — f-strings allocate
- Creating `pygame.Rect` objects in render() instead of mutating existing ones

Detection: use the memory inspector (Phase 5.2) to check that object
counts are stable after a few seconds of normal gameplay.

---

## 9. Benchmark Targets for Key Systems

These are the targets we commit to maintaining. If a change causes these
to regress, the change must either include an optimisation or update
the target with a justification.

| Operation | Target | Measured condition |
|---|---|---|
| Observable.set() with change | < 0.001ms | 1000 subscribers |
| Observable.set() no change | < 0.0001ms | equality check only |
| Widget tree event routing | < 0.5ms | 100 widgets |
| truncate() | < 0.05ms | 500-char string |
| wrap_text() | < 0.2ms | 500-char string, 400px width |
| Scene render() (empty) | < 0.1ms | no widgets |
| Tab bar draw() | < 0.5ms | 9 tabs, SysFont |

These targets will be validated by the frame budget visualiser once
it is built (Phase 5.1). Until then, they are design targets.

---

## 10. Performance and the Editor

The editor is a development tool. It does not need production-level
performance. However, it must not make the game noticeably slower during
edit mode.

**Editor overhead target:** Less than 2ms additional per frame beyond
what the game alone costs. The editor panels are ImGui — ImGui is fast
and this target is easily achievable with normal usage.

**The game viewport** renders at the same performance as the standalone
game. The editor subsurface is the same code path — no degradation
is acceptable.

---

## 11. When a Budget Is Exceeded — The Process

### During Development

When the frame budget visualiser shows a system consistently over budget:

1. **Confirm it is real.** Run for 30 seconds under normal gameplay
   conditions. One spike is not a pattern. Sustained violation is.

2. **Profile specifically.** Use `cProfile` or `pygame.time.get_ticks()`
   around the suspected section. Know which function and which line
   before writing a single word of optimised code.

3. **Measure before touching anything.** Record the baseline number.
   "It was slow" is not a baseline. "update() averaged 6.2ms over
   300 frames" is a baseline.

4. **Optimise the confirmed hotspot.** Not the code around it. Not
   the code that looks slow. The measured hotspot.

5. **Measure after.** Record the improvement. If the improvement is
   less than 20%, question whether the optimisation is worth the
   added complexity.

6. **Write the benchmark comment.** Required for any optimisation that
   makes code less readable. No comment = revert in the next review.

7. **Verify all tests still pass.** Performance changes break things.
   Tests catch it.

### In a Shipped Game

When a player or playtester reports slowdown:

1. Ask for the conditions — what scene, what action, what hardware
2. Reproduce in development mode with the frame budget visualiser
3. Treat as a `fix` type bug — same process as any other bug
4. Profile, fix, benchmark, test, commit with the measurement in the
   commit body

Performance bugs that cannot be reproduced are not fixable. If you
cannot reproduce it, add logging to help identify the conditions.

### When Redesign Is the Right Answer

Sometimes the hotspot is not a slow function but a wrong design:

- O(n²) behaviour where n is growing
- Rebuilding something on every frame that only needs rebuilding on change
- A data structure chosen for convenience rather than access patterns

These require a refactor, not a micro-optimisation. Treat the redesign
as a feature with its own branch, tests, and commit. The benchmark
comment documents why the design changed.
