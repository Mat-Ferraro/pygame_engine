# pygame_engine — Dependency Policy

**Version:** 2.0-design
**Authority:** Supplements ARCHITECTURE.md Restriction R19

This document defines how dependencies are chosen, categorised,
pinned, and updated. A dependency is a commitment — it is someone
else's code that we cannot change and must keep working with.

---

## 1. The Decision Checklist

Before adding any new dependency, answer all five questions:

**1. Is it truly necessary?**
Can we implement the needed functionality in under 100 lines of
well-tested Python? If yes, implement it ourselves. We control our own
code. We do not control external packages.

**2. Is it actively maintained?**
Check: last commit date, open issues response time, PyPI release
frequency. A package with no commits in two years is a liability.

**3. Does it have a stable public API?**
Check: semantic versioning policy, CHANGELOG, history of breaking
changes. A package that breaks its API between minor versions will
eventually break us.

**4. Does it have acceptable licence terms?**
MIT, BSD, Apache 2.0, and PSF are acceptable. GPL and LGPL require
careful review — they may affect game distribution. Proprietary is
never acceptable for engine dependencies.

**5. Does it have an acceptable size and install footprint?**
A dependency that adds 500MB to the install for a minor convenience
is not acceptable. Prefer small, focused packages.

If any answer is unsatisfactory, do not add the dependency.

---

## 2. Dependency Categories

### Runtime Dependencies

Listed in `pyproject.toml [project.dependencies]`.
Required by anyone who installs and uses `pygame_engine`.

Current runtime dependencies:
- `pygame-ce` — the rendering and event foundation (pinned to exact version)
- `platformdirs` — platform-appropriate save directories

**Standard for adding a new runtime dependency:**
- Must pass all five checklist questions
- Must be used by the engine core — not just one optional module
- Must not significantly increase the engine's install size
- Requires a documented decision in `decision_log.md`

### Optional Runtime Dependencies

Listed in `pyproject.toml [project.optional-dependencies]`.
Required only when a specific engine module is used. Not installed by default.

```toml
[project.optional-dependencies]
editor    = ["pyimgui>=2.0"]
recording = ["some-audio-lib>=1.0"]
```

Games that do not use the editor do not install `pyimgui`. The engine
core never imports from optional dependencies — only the module that
requires them does, and only at the point of use (lazy import).

**Standard for adding an optional dependency:**
- Must pass all five checklist questions
- Must be used only by one specific engine module
- Must be clearly documented in that module's doc file
- The module must degrade gracefully when the optional dep is absent

### Development Dependencies

Listed in `pyproject.toml [project.optional-dependencies.dev]`.
Required to develop the engine. Not required to use it.

```toml
[project.optional-dependencies.dev]
pytest>=8.0
ruff>=0.4
mypy>=1.9
hypothesis>=6.0
pyinstaller>=6.0
pdoc>=14.0
```

**Standard:** any tool used in CI or local development.
Pinned to minimum compatible version (`>=X.Y`), not exact version.
Development tools do not need the same strict pinning as runtime —
a newer version of pytest breaking tests would be caught immediately.

---

## 3. Pinning Policy

### Runtime Dependencies — Pin to Exact Version

`pygame-ce` and `platformdirs` are pinned to an exact version:

```toml
dependencies = [
    "pygame-ce==2.5.7",
    "platformdirs==4.2.2",
]
```

**Why exact pinning:** A runtime dependency version change can
silently change behaviour. "It works with pygame-ce >= 2.4" is not
a guarantee — it is an untested claim. We only know it works with the
version we have tested.

**Why this is not too strict:** Games that install the engine get a
known-good configuration. If a game developer needs a different
pygame-ce version (rare), they override the dependency in their own
`pyproject.toml`.

### Optional Runtime Dependencies — Pin to Minimum Compatible

```toml
[project.optional-dependencies.editor]
pyimgui>=2.0,<3.0
```

Optional dependencies are harder to test exhaustively. A minimum
compatible version with an upper bound on breaking changes is the
correct tradeoff.

### Development Dependencies — Pin to Minimum

```toml
pytest>=8.0
ruff>=0.4
```

Development tools are updated frequently and almost never break in
ways that affect us. Minimum pinning keeps development environments
up to date without requiring synchronisation across contributors.

---

## 4. The Upgrade Process

### Upgrading pygame-ce (Restriction R19)

This is a deliberate, tested process — never automatic:

1. Check the pygame-ce changelog for breaking changes between current
   and target version
2. Update the pin in `pyproject.toml`
3. Run the full test suite (`pytest`) — fix any failures
4. Run all examples (`python run_examples.py`) — verify nothing breaks visually
5. Update the tested version note in README.md and `pygame_engine/__init__.py`
6. Add a `chore(deps)` entry in CHANGELOG.md
7. Commit with message: `chore(deps): upgrade pygame-ce to X.Y.Z`

**Never upgrade pygame-ce as part of a feature commit.** Upgrade in
a dedicated commit or PR so that if it breaks something, the cause
is unambiguous.

### Upgrading Other Dependencies

Same process as pygame-ce. Always in a dedicated commit.

---

## 5. Current Dependencies — Documented Decisions

### pygame-ce

**Version:** 2.5.7 (pinned exact)
**Why chosen:** The maintained fork of pygame with active SDL updates,
better performance, and ongoing development. The only viable
pygame-based rendering foundation for an active project.
**Why not vanilla pygame:** unmaintained, SDL 2 support poor.
**Licence:** LGPL — acceptable, game distribution not affected.

### platformdirs

**Version:** 4.2.2 (pinned exact)
**Why chosen:** Platform-correct directories for save data on Windows
(`%APPDATA%`), macOS (`~/Library/Application Support`), and Linux
(`~/.local/share`). 400 lines of carefully maintained code we do not
want to write and maintain ourselves.
**Why not implement ourselves:** Platform-specific directory resolution
is fiddly and changes with OS versions. This library handles it.
**Licence:** MIT — acceptable.

### pyimgui (optional — editor module)

**Version:** >= 2.0, < 3.0 (minimum compatible)
**Why chosen:** Dear ImGui is the industry standard for game engine
editor UI. pyimgui provides Python bindings. Gives us dockable panels,
tree views, colour pickers, and the full ImGui widget set immediately.
**Why not our own widgets:** Building a full editor UI from engine
widgets is months of work before we can write editor features. ImGui
gives us a professional result on day one.
**Licence:** MIT — acceptable.

---

## 6. Dependencies We Will Not Add

These categories of dependency are explicitly rejected regardless of
quality:

**Any physics engine** — physics is out of scope (R18). Games that
need physics integrate pymunk directly at the game level, not through
the engine.

**Any networking library** — networking is out of scope for the engine
core. If added as a future module, it is optional with lazy imports.

**Any ORM or database** — the save system uses files. A database
dependency for save data would be inappropriate for a game engine.

**Any web framework** — the engine targets desktop. No web server,
no REST client, no WebSocket.

**Any machine learning library** — numpy, torch, tensorflow are
enormous dependencies with no place in a 2D game engine.

---

## 7. Vendoring

Vendoring (copying a dependency's source code into our repository)
is not permitted. It creates a maintenance burden, complicates
licence compliance, and prevents automatic security updates.

The one exception: if a tiny, stable utility (< 50 lines) from
a library is needed and the full library would be disproportionate,
that utility may be reimplemented from scratch (not copied) with a
comment crediting the original source and noting the licence.

---

## 8. Security

If a dependency has a known security vulnerability:
1. Check whether the vulnerability affects our usage
2. If it does: update immediately, create a `fix` commit
3. If it does not: document the decision and monitor for updates

Security updates to runtime dependencies follow the same upgrade
process as regular updates — they are not committed silently.
