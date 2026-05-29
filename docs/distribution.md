# pygame_engine — Distribution: Strategy, Options, Open Items

**Version:** 0.1-deferred
**Status:** Goal document — strategy unresolved, no path scheduled.
**Authority:** Engine-wide. Companion to ENGINE_DIRECTION.md. Supplements
ARCHITECTURE.md.

This document records the goal of one-step installation for end users, and
the analysis behind deferring the work. The engine and editor are not yet
distributed in any packaged form: setup currently requires installing
Python, installing six pip packages by name, and obtaining the project
source. That is fine for the project's developer; it is not fine for any
broader audience.

Nothing here is scheduled. The purpose of writing this down is so that the
distribution decision, when it is made, is made *deliberately* — with the
audience identified, the path chosen, and the foundation already in place —
rather than discovered mid-release as if new.

---

## 1. The goal in one sentence

> Eventually make pygame_engine installable in a single step by end users,
> where "end user" and "installable" are determined by a use case that does
> not yet exist.

The phrasing is deliberate. "End user" has three plausible meanings, each
implying a different distribution path, a different artifact, and a
different amount of work. The choice is not yet forced. Picking too early
commits the project to a shape it may not want.

---

## 2. The three audiences

The right distribution path is determined by who the end user is. The three
candidates are genuinely different products and should not be confused.

### A. Other Python developers

A developer who writes Python, has a Python install, and wants to use
`pygame_engine` as a library inside their own game project.

- **They want:** `pip install pygame-engine`, then
  `from pygame_engine.ui import Button` in their code.
- **They do not need:** the editor as a standalone app, an installer, a
  bundled interpreter.
- **The artifact:** a package on PyPI.

### B. Non-Python game developers

A designer, hobbyist, or game-jam participant who wants a Godot-/
GameMaker-like experience: download an editor, click around, ship a game.
They never touch Python directly.

- **They want:** a downloadable editor application; a way to export their
  scene/game to a runnable artifact without writing Python.
- **They do not need:** to know the engine is a Python library at all.
- **The artifact:** a packaged editor executable, plus an in-editor
  export pipeline.

### C. Players

The end of the chain. Someone who wants to play a game built on
pygame_engine. They do not know the engine exists.

- **They want:** to double-click `MyGame.exe` and play.
- **They do not need:** to know about anything else.
- **The artifact:** per-game executable bundles, produced by individual
  game projects.

These are not the same product. Audience A is solved by packaging metadata
and a PyPI upload. Audience B is solved by a real editor application —
months of work, including an export pipeline this project does not yet
have. Audience C is solved per-game by whoever ships that game, not by the
engine project itself.

---

## 3. The three paths

### Path A — engine as a Python library

**End-user experience:** `pip install pygame-engine`, then import.

**Required work:**

- A `pyproject.toml` at the repo root declaring package name, version,
  dependencies, included files, and entry points.
- Deliberate choice of what ships in the wheel: `pygame_engine/` is in;
  `tests/`, `docs/`, `examples/`, `editor/` need a per-folder decision.
  Examples and the editor are arguably useful to ship; tests and docs
  generally are not.
- A `LICENSE` file. Without one, no one can legally use the code. MIT
  or Apache-2.0 are the low-friction choices for a permissive library.
- A semantic version, and a versioning policy. Pre-1.0 is forgiving;
  post-1.0 implies backward compatibility commitments.
- A README written for a stranger, not a maintainer.
- A PyPI account and the `build` + `twine` tooling for upload.

**Effort:** half a day to a day for a first usable release, plus ongoing
maintenance — issues, version bumps, OS-portability reports.

**Risk:** premature publication locks in an API that is still under
construction. The editor work is mid-flight (F4/F5 active, drag-resize
and click-select unbuilt). The engine has several deferred systems noted
elsewhere. A 0.x release that breaks every minor version is acceptable
but reputation-damaging; a 1.0 release that breaks anything is not.

### Path B — editor as a bundled application

**End-user experience:** download `pygame_engine_editor.exe`, double-click,
the editor opens. No Python install.

**Required work:**

- A bundling tool. **PyInstaller** is the conventional choice for pygame
  projects on Windows/macOS/Linux. Alternatives: Nuitka (smaller and
  faster, more complex), cx_Freeze (older).
- A working `pyproject.toml` (or at least clean entry points). The
  editor's `editor/__main__.py` is the launch script.
- Explicit asset declarations. PyInstaller does not auto-discover
  `assets/`, theme files, fonts, or default layouts; they must be
  named in the spec.
- Verification that the native binary dependencies bundle cleanly.
  `imgui-bundle` ships nanobind C++ bindings; PyOpenGL has a history of
  small PyInstaller friction. Both usually work but should be tested
  early rather than late.
- A choice between `--onefile` (one icon, slow first launch each time)
  and `--onedir` (folder of files, instant launch). Commercial projects
  use `--onedir` plus an installer (NSIS, Inno Setup) for the polished
  experience.
- Per-platform builds. PyInstaller does not cross-compile; a Windows exe
  must be built on Windows, etc. Windows-only is acceptable to start.

**Effort:** two to four hours for a first PyInstaller bundle that
launches. Several more days of iteration to debug missing-asset and
startup-error cases. Per-platform work multiplies the total.

**Risk — the real one:** what does a downloaded editor *do* if there is
nothing to edit? The editor today edits scenes that live inside a Python
project. Strip the Python project away and the editor is a tool with no
content. Audience B (the people who would *want* a downloadable editor)
need an export pipeline that turns "scene I designed in the editor" into
"game artifact I can run" — and that pipeline does not yet exist. Path B
without an export story is shipping half a product.

### Path C — game as a bundled executable

**End-user experience:** download `my_game.exe`, double-click, play.

**Required work:** identical tooling to Path B (PyInstaller, asset
declarations, per-platform builds), but the bundled application is a
*game* (`my_game/main.py`) rather than the editor. The engine is
incidental — one of the bundled dependencies, invisible to the player.

**Effort:** comparable to Path B for a first build of a given game.

**Risk:** very low. The game is the artifact; the engine is plumbing.
The hard part is making a finished game, not packaging it.

**When to do this:** when there is a finished game to ship.

---

## 4. Foundation work — separable from distribution

Independent of which path is eventually chosen, several pieces of
infrastructure are useful in their own right and are prerequisites for
*any* of A, B, or C. They should be done first, regardless.

### 4.1 `pyproject.toml` at the repo root

Currently absent. Adding one unlocks:

- `pip install -e .` works without the `conftest.py` `sys.path` hack
  for tests.
- A declared dependency list, in one canonical place, instead of being
  rediscovered crash-by-crash on every new machine.
- A required precondition for every downstream distribution path.

The cost is a single afternoon. The payoff applies whether distribution
is ever attempted or not — even setting up the project on a new dev
machine becomes `git clone && pip install -e .`.

### 4.2 `LICENSE` file

Currently absent. Without one, the code is legally unusable by anyone
other than the author. Required for any public distribution. Adding a
permissive license (MIT, Apache-2.0) is a one-file change; choosing a
copyleft license (GPL) is a deliberate decision that constrains downstream
use. MIT is the default recommendation unless there is a specific reason
to choose otherwise.

### 4.3 `requirements.txt` or equivalent

Currently the dependency list is reconstructed by trial: each new machine
setup discovers a missing package by importing and crashing.

The known list as of this writing:

    pygame-ce, imgui-bundle, PyOpenGL, pytest, pytest-cov, numpy

This should be canonical, not folklore. `pyproject.toml` can carry it
directly; a `requirements.txt` is the lighter-weight alternative for
development setups.

### 4.4 A repository remote (git)

Strictly orthogonal to distribution, but listed here because the lack of
one has already cost real time. Every time the project moves to a new
machine, files have gone missing — once silently (`gizmo_renderer.py`),
once with a stale `imgui.ini` causing a half-built dock layout, once
requiring a full dependency-discovery cycle. The fix is the same in all
three cases: push the project to a remote, clone on every new machine.

This is not optional infrastructure. It is the floor.

---

## 5. Recommendation

**Do the foundation work (4.1, 4.2, 4.3, 4.4) when convenient.** It is
cheap, it is independent of which distribution path is eventually chosen,
and it is useful on its own merits.

**Defer the distribution choice itself until a trigger fires.** Building
distribution before the audience is real means rebuilding it when the
audience clarifies.

The recommendation against immediate distribution is not a recommendation
against ever distributing. It is a recommendation against committing to a
*specific* distribution shape while the engine itself is still under
construction and the user is still hypothetical.

---

## 6. Triggers — when to revisit

This is the most actionable section. Distribution is not scheduled; it
unblocks when one of the following becomes true:

### T1 — "A friend wants to try the editor."

Indicates Audience B is real. Build a PyInstaller `--onedir` bundle of the
editor (Path B). Accept that without an export pipeline the editor is a
demonstration, not a tool — and decide whether that is enough for the
audience at hand.

### T2 — "I have a small playable game and want to share it."

Indicates Audience C is real. Build a PyInstaller bundle of the game (Path
C). The engine is bundled as a dependency, invisible to the player. This
is the lowest-risk path and the most directly satisfying — it puts
something runnable in someone's hands.

### T3 — "Another Python developer wants to depend on the engine."

Indicates Audience A is real. Publish to PyPI (Path A). Prerequisite: API
stability acceptable to commit to. If the engine is still routinely
breaking its own callers at this point, the answer is *not yet* — the
right response is to push back and ask the would-be user to vendor the
source for now.

### T4 — "We want to export a game *from inside the editor*."

The big trigger. It implies the editor is a real product (Audience B in
its full form), which requires a build pipeline that takes scene
descriptors plus game code and produces a Path-C bundle. This is months of
work, not days. If T4 fires, the response is a dedicated design document
of its own — not a small extension of this one.

### T5 — None of the above, but the engine reaches 1.0.

A 1.0 release implies the API is stable and the engine is "finished
enough" to be relied on. Publishing to PyPI at 1.0 is conventional and
expected. The trigger may not arrive for some time, but it should not be
forgotten.

---

## 7. Open items not yet decided

- **License choice.** MIT vs. Apache-2.0 vs. something else. Default
  recommendation MIT; revisit if there is a reason.
- **Package name on PyPI.** `pygame-engine` is the obvious name. It may
  be taken; if so, alternatives include `pygame-engine-2d`,
  `pgengine`, the author's namespace, or a project rename. Worth
  checking availability *before* committing publicly to the current
  name elsewhere.
- **Editor as part of the PyPI package vs. separate.** If Path A is
  taken, does `pip install pygame-engine` include the editor as an
  optional extra (`pip install pygame-engine[editor]`), or is the
  editor shipped only via Path B bundles? Both are defensible; the
  decision changes the `pyproject.toml` shape.
- **Scope of "single-step installation."** Is `pip install pygame-engine`
  acceptable, or is the bar higher — a `.msi` installer for Windows, a
  signed bundle for macOS? The bar depends on the audience.

None of these block writing the document; all of them block actual
distribution. They are listed so that none of them is *discovered*
mid-release as if new.
