# pygame_engine — Git Standards

**Version:** 2.0-design
**Authority:** Supplements CODING_STANDARDS.md

This document defines how we use version control. Consistent commit
history and branch structure make the project navigable, debuggable,
and collaborative. These are not suggestions — they apply to every
commit in the repository.

---

## 1. Commit Messages

We use Conventional Commits format. It is machine-readable, drives
CHANGELOG.md generation, and makes the history scannable.

### Format

```
type(scope): short description

Body paragraph explaining why the change was made and what the impact
is. Not required for trivial changes. Required for anything that a
future developer would need context to understand.

References:
  Resolves: CODEBASE_CHANGES.md C8
  See: ARCHITECTURE.md Section 3.3
  Breaks: Observable subscriber signature — see migration note below
```

### The Short Description

- Imperative mood: "add", "fix", "remove" — not "added", "fixes", "removing"
- No capital letter at the start
- No period at the end
- 72 characters maximum
- Describes what changes, not how

```
# Good
feat(observable): add transaction batching for multiple changes
fix(tab_bar): navigation fails when scene registry is empty
docs(architecture): add play mode restriction to editor section

# Bad
feat(observable): Added transaction batching.
fix: fixed the tab bar
docs: updated stuff
```

### Types

| Type | Use for |
|---|---|
| `feat` | New feature or capability added to the public API |
| `fix` | Bug fix — incorrect behaviour corrected |
| `docs` | Documentation only — no code change |
| `refactor` | Code restructure with no behaviour change |
| `test` | Tests added or corrected — no production code change |
| `perf` | Performance improvement — behaviour unchanged |
| `chore` | Build, CI, dependency, tooling changes |
| `style` | Formatting, naming — no behaviour change |

### Scope

The scope names the system or module affected. Use the module name
or a short name that unambiguously identifies what changed.

```
feat(observable)        — pygame_engine/state/observable.py
fix(scene_manager)      — pygame_engine/scene/scene_manager.py
docs(architecture)      — docs/ARCHITECTURE.md
refactor(management)    — game/scenes/management_scene.py
test(text_utils)        — tests/test_text_utils.py
chore(deps)             — pyproject.toml dependency update
```

Scope is required for all types except `docs` when the change touches
multiple doc files.

### The Commit Body

Required when:
- The change might surprise a future reader
- A non-obvious decision was made
- A restriction or codebase change is being addressed
- The commit breaks backwards compatibility

Not required for:
- Simple bug fixes where the cause is obvious from the diff
- Documentation typo fixes
- Test additions that mirror the implementation

Good body example:
```
feat(observable): add weak reference subscriptions

Strong references prevented garbage collection of subscriber objects.
A scene with 50 widgets each subscribing to game state observables
would retain all 50 widgets in memory after the scene was popped,
even though nothing else held a reference to them.

Subscribers are now stored as weakref.ref instances. _notify() checks
liveness before calling each subscriber and removes dead refs lazily.

Breaks: existing subscribers stored as bound methods must ensure the
owning object remains alive. Lambdas and closures work unchanged.

Addresses: CODEBASE_CHANGES.md C8
```

### Breaking Changes

Any commit that breaks the public API must include a `BREAKING CHANGE:`
footer. This is the signal that triggers a major version bump.

```
feat(observable): change subscriber signature to (old, new)

Previously subscribers received only the new value. They now receive
(old_value, new_value) to support undo/redo correctness.

BREAKING CHANGE: all subscribers must update their signature from
  callback(new_value) to callback(old_value, new_value).
  Affected: any code passing a callback to Observable.subscribe().
```

---

## 2. Branching Strategy

We use feature branches off `main`. `main` is always in a releasable
state — all tests pass, all CI checks pass.

### Branch Naming

```
feat/observable-upgrade
feat/time-manager
fix/theme-singleton-leak
fix/tab-bar-navigation-crash
docs/coding-standards-update
refactor/management-scene-decompose
test/observable-property-tests
chore/bump-pygame-ce-2-5-8
```

Format: `type/short-description-in-kebab-case`

The type matches the commit type. The description identifies the work
clearly enough that anyone reading the branch list knows what it contains.

### Branch Lifecycle

1. Create branch from latest `main`
2. Work on the branch — commit frequently (see commit granularity below)
3. Keep the branch up to date with `main` via rebase (not merge)
4. When complete: all tests pass, CI passes, docs updated
5. Merge to `main` — squash or preserve history depending on scope

### When to Squash vs Preserve

**Squash** — when the branch has many "wip" or "fix typo" commits that
add noise to the history without adding meaning. The squashed commit
must have a complete, accurate message covering the full change.

**Preserve** — when the branch contains distinct logical steps that are
each meaningful on their own. A refactor branch that does three
separate decompositions benefits from three commits.

When in doubt: squash. A clean history is more valuable than a complete
history of every wrong turn.

### Direct Commits to Main

Permitted only for:
- Single-line documentation fixes (typos, broken links)
- Version number bumps after a release
- Trivial CI configuration fixes

Everything else goes through a branch regardless of how small.

---

## 3. Commit Granularity

A commit should represent one logical change — something that could be
reverted independently without breaking other things.

**Too large:**
```
feat(phase-1): implement observable upgrade, time manager,
subscription group, theme fix, and shared game UI extraction
```
This cannot be reverted in pieces. If the theme fix is wrong, you
cannot revert it without also reverting the observable upgrade.

**Too small:**
```
fix: add missing import
fix: fix typo in comment
fix: actually fix the import
```
These belong as a single commit or as part of a larger logical change.
Fixup commits should be squashed into their parent before pushing.

**Just right:**
```
feat(observable): add transaction batching
test(observable): add transaction batching tests
docs(observable): document transaction() in CODING_STANDARDS.md
```
Three commits, each independently meaningful. Each can be reverted
without affecting the others.

---

## 4. What Goes in a Commit

A commit for a new engine feature includes:
- The implementation code
- Tests for that specific change
- Updated CHANGELOG.md entry
- Updated doc files if public API changed

A commit does NOT mix:
- Feature work and unrelated bug fixes
- Multiple unrelated features
- Code changes and large formatting reformats

If you discover a bug while working on a feature, fix it in a separate
commit with a `fix` type.

---

## 5. Tags and Releases

Version tags follow semantic versioning: `v1.0.0`, `v1.1.0`, `v1.1.1`.

Tag at the commit that bumps the version number in `pyproject.toml`.
The tag message is the CHANGELOG.md section for that version.

```
git tag -a v1.1.0 -m "$(cat CHANGELOG-fragment.md)"
```

Never tag a commit that does not have all tests passing.

---

## 6. CHANGELOG.md Format

```markdown
## [Unreleased]

### Added
- feat(observable): transaction batching — multiple changes fire one event
- feat(time_manager): TimeManager with time_scale and fixed timestep

### Fixed
- fix(tab_bar): navigation crash when scene registry is empty

### Changed
- refactor(observable): subscriber signature now receives (old_value, new_value)

### Deprecated
- Observable.subscribe with single-argument callback — use (old, new) signature

### Breaking Changes
- Observable subscriber signature changed — see migration guide in docs/

## [1.3.0] — 2025-XX-XX

...previous release entries...
```

Sections that have no entries are omitted. The `[Unreleased]` section
accumulates changes until a release is cut, then is renamed to the
version number and a new `[Unreleased]` section is added above it.

---

## 7. .gitignore Standards

The following are always ignored:

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# pygame-ce compiled assets
*.pyc

# Editor and OS
.DS_Store
Thumbs.db
.idea/
.vscode/
*.swp

# Test and coverage artifacts
.pytest_cache/
.hypothesis/
htmlcov/
.coverage

# Game outputs
saves/
crash.log
*.layout.json.bak

# PyInstaller build outputs
dist/
build/
*.spec.bak
```

Never commit:
- Save files from test runs
- Crash logs
- IDE project files
- Local `.env` files
- Generated documentation (pdoc output)

---

## 8. Squash vs Preserve — Precise Criteria

The guiding question: **would a developer bisecting a bug need to land
on an intermediate commit to understand or fix the problem?**

**Squash when:**
- The branch implements one logical feature or fix
- Intermediate commits are implementation steps, not milestones
- Commit messages include "wip", "fix typo", "oops", "try again"
- The final diff would make a single coherent commit message

**Preserve when:**
- The branch contains sequential changes each independently meaningful
- Each commit could be reverted without breaking the others
- Example: a decomposition branch that splits three files in three
  separate commits — each split is independently correct and revertable

**When in doubt: squash.** A clean, accurate history is more valuable
than a complete record of every wrong turn.

---

## 9. Handling Bugs Discovered During a PR

If you discover a bug while working on a feature branch:

**If the bug is in code you are already changing:** fix it as part of
the same logical commit. It is the same change.

**If the bug is in unrelated code:**
1. Stash your current work
2. Create a new branch from `main`: `fix/bug-description`
3. Fix the bug and open a separate PR
4. Return to your feature branch and rebase onto the updated `main`

Never mix a feature commit with an unrelated bug fix in the same
commit. If the feature is later reverted, the bug fix must not
be reverted with it.

---

## 10. Fixup Commits During Review

When a reviewer requests changes:

```bash
# Make the fix
git add -p                          # stage only the fix
git commit --fixup <original-sha>   # create a fixup commit

# Before merge — squash fixups into their parents
git rebase -i --autosquash main
```

Never leave `fixup!` commits in the branch history at merge time.
The merged history should look as if the review feedback was
incorporated from the start.

Do not create "address review comments" commits. They add noise to
the history and make bisecting harder. Fixup commits squashed into
their parent are the correct approach.
