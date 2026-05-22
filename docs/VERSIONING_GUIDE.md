# pygame_engine — Versioning Guide

**Version:** 2.0-design
**Authority:** Supplements ARCHITECTURE.md and GIT_STANDARDS.md

This document covers the practical process of versioning pygame_engine
— what constitutes a version bump, how to cut a release, and how to
communicate changes to developers who build on the engine.

---

## 1. Semantic Versioning

We follow semver: `MAJOR.MINOR.PATCH`

| Increment | When |
|---|---|
| `MAJOR` | Any breaking change to the stable public API |
| `MINOR` | New feature added — no breaking changes |
| `PATCH` | Bug fix — behaviour corrected, no new API |

**Current version:** 1.3.0 (as of the design phase for 2.0.0)

**The stable public API tier** is defined in ARCHITECTURE.md Section 7.
A breaking change is any change to the stable tier that requires game
developers to modify their code. Changes to internal modules, optional
modules, or game code do not trigger a MAJOR bump.

---

## 2. What Constitutes a Breaking Change

A change is breaking if a game developer who has not read the changelog
would find their game broken after upgrading.

**Definitely breaking:**
- Removing a class, method, or property from the stable tier
- Renaming a class, method, or property in the stable tier
- Changing a method signature (parameters or return type) in the stable tier
- Changing the semantics of a method (what it does, not how)
- Changing a file format in a way that makes old files unreadable

**Not breaking:**
- Adding new classes or methods to the stable tier
- Adding new optional parameters with defaults
- Changes to internal modules (prefixed `_` or in `_internal/`)
- Changes to optional engine modules (editor, MusicPlayer, etc.)
- Bug fixes that correct previously incorrect behaviour

**Grey area — document explicitly:**
- Changing error message text (not breaking, but may affect tests that
  assert on message content)
- Changing default values of optional parameters
- Performance changes that alter timing (not semantic, but observable)

When in doubt: treat it as breaking and bump MAJOR. It is better to
be conservative than to break games silently.

---

## 3. The Deprecation Process

Breaking changes should be preceded by a deprecation period. The
sequence is:

```
Version 1.3.0 — Feature X works as before
Version 1.4.0 — Feature X deprecated, DeprecationWarning emitted,
                Feature Y (the replacement) introduced
Version 2.0.0 — Feature X removed, Feature Y is the only option
```

This gives game developers at least one minor version to migrate before
the breaking change lands.

**Deprecation in code:**
```python
import warnings

def old_method(self) -> None:
    """
    .. deprecated:: 1.4.0
        Use :meth:`new_method` instead. Will be removed in 2.0.0.
    """
    warnings.warn(
        "old_method() is deprecated and will be removed in 2.0.0. "
        "Use new_method() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return self.new_method()
```

**In CHANGELOG.md:**
```markdown
### Deprecated
- `Observable.subscribe(callback)` with single-argument callback.
  Use `callback(old_value, new_value)` instead. Will raise in 2.0.0.
  See migration guide: docs/migrations/observable_subscriber_update.md
```

**Migration guides** — any breaking change in a MAJOR version must have
a migration guide in `docs/migrations/` explaining what changed and how
to update game code. Reference the guide in CHANGELOG.md.

---

## 4. The Release Checklist

Run through this checklist in order before every release.

### Pre-Release Verification

- [ ] All tests pass: `pytest`
- [ ] Linter passes: `ruff check .`
- [ ] All examples run without error: `python run_examples.py --list`
  (verify at least the recently changed ones manually)
- [ ] No files over the 600-line hard cap without a decomposition plan
- [ ] No unresolved TODO(bug) comments in code being released
- [ ] CHANGELOG.md `[Unreleased]` section is complete and accurate

### Version Number Update

Update the version in exactly these four places:

1. `pyproject.toml` — `version = "X.Y.Z"`
2. `pygame_engine/__init__.py` — `__version__ = "X.Y.Z"`
3. `README.md` — the version badge and "Version X.Y.Z" text
4. `CHANGELOG.md` — rename `[Unreleased]` to `[X.Y.Z] — YYYY-MM-DD`
   and add a new empty `[Unreleased]` section above it

All four in a single commit:
```
chore(release): bump version to X.Y.Z
```

### Git Tag

```bash
git tag -a vX.Y.Z -m "pygame_engine vX.Y.Z

$(sed -n '/## \[X.Y.Z\]/,/## \[/p' CHANGELOG.md | head -n -1)"
git push origin vX.Y.Z
```

The tag message is the CHANGELOG section for this version.

### Post-Release

- [ ] Tag is pushed to origin
- [ ] Any game projects that depend on this engine are updated to the
  new version and verified working
- [ ] Any migration guides referenced in CHANGELOG.md are complete

---

## 5. Version in Code

The version is accessible at runtime:

```python
import pygame_engine
print(pygame_engine.__version__)   # "1.3.0"
```

The engine also exposes the tested pygame-ce version:

```python
pygame_engine.__pygame_ce_version__  # "2.5.7"
```

Games that want to verify compatibility can check these at startup:

```python
import pygame_engine
from packaging.version import Version

REQUIRED_ENGINE = "1.3.0"
if Version(pygame_engine.__version__) < Version(REQUIRED_ENGINE):
    raise RuntimeError(
        f"This game requires pygame_engine {REQUIRED_ENGINE} or later. "
        f"Installed: {pygame_engine.__version__}"
    )
```

---

## 6. CHANGELOG.md Format

```markdown
# Changelog

All notable changes to pygame_engine are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).
Versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- feat(time_manager): TimeManager with time_scale, delta_time, frame_count

### Fixed
- fix(tab_bar): navigation crash when scene registry is empty on first frame

### Changed
- refactor(observable): subscriber signature now receives (old_value, new_value)

### Deprecated
- Observable.subscribe() with single-argument callback — use (old, new) form

### Removed
- (nothing removed in unreleased)

### Breaking Changes
- (none in unreleased)

---

## [1.3.0] — 2025-03-15

### Added
- feat(text_utils): truncate(), wrap_text(), wrap_and_truncate() functions
- feat(badge): Badge widget with five semantic styles
- ...

### Fixed
- fix(confirm_dialog): keyboard Enter triggered underlying scene after dismiss
```

Sections with no entries are omitted. Do not write "None" or "N/A" —
just leave the section out.

**Entry format:** Use the same `type(scope): description` format as
commit messages. This makes it easy to generate CHANGELOG entries from
commit history.

---

## 7. Pre-Release Versions

For significant feature work before a stable release, use pre-release
version identifiers:

```
2.0.0-alpha.1   — early development, API not stable
2.0.0-beta.1    — feature complete, API stable, bugs expected
2.0.0-rc.1      — release candidate, only critical bugs warrant another RC
```

Pre-release versions are not recommended for game projects in production.
Document this clearly in the README.

---

## 8. Engine Version vs Game Version

`pygame_engine` has its own version. Games built on it have their own
version. These are independent.

A game at version 1.0.0 built on pygame_engine 1.3.0 is valid. When
the engine updates to 1.4.0, the game does not need to update if nothing
it uses changed. When the game updates to version 1.1.0, the engine
version it uses is unchanged.

Each game should record the engine version it is built against in its
own `pyproject.toml` or README. This makes it clear which version of
the engine was used when the game shipped.

---

## 9. Long-Term Compatibility Policy

The stable API tier (defined in ARCHITECTURE.md Section 7) is supported
across MINOR versions. Game code that uses only the stable tier will not
need changes for a MINOR version bump.

Internal APIs (prefixed `_`, in `_internal/` subpackages) may change
in any release including PATCH releases. Game code that uses internal
APIs has no compatibility guarantee.

The `@deprecated` decorator provides a one-major-version migration
window. A feature deprecated in 1.4.0 is removed no earlier than 2.0.0.
