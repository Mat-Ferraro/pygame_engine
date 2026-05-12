## Purpose

The asset pipeline defines how engine and project assets are found, loaded, cached, and used.

The goal is to make asset usage:
- predictable
- reusable
- resilient
- easy to understand

---

## Current Asset Modules

The assets package currently contains:

- `asset_loader.py`
- `sprite_loader.py`
- `fonts.py`
- `sounds.py`
- `paths.py`

Suggested responsibilities:
- `paths.py` = canonical asset locations
- `asset_loader.py` = generic load/cache entry points
- `sprite_loader.py` = image/sprite-specific loading
- `fonts.py` = font-specific helpers
- `sounds.py` = sound-specific helpers

---

## Design Principles

1. Asset paths should be centralized.
2. Loading should be explicit and cache-aware.
3. Asset-type-specific behavior should stay in type-specific modules.
4. Missing asset behavior should be documented and consistent.
5. Asset loading should not be duplicated all over the codebase.

---

## Path Ownership

`paths.py` should define canonical engine asset paths and conventions.

Examples:
- engine asset root
- project asset root if supported later
- font directories
- image directories
- sound directories

Recommended rule:
- do not hardcode scattered file paths throughout the engine

---

## Generic Loader Role

`asset_loader.py` should handle shared loading concerns:
- cache lookup
- cache storage
- generic existence/error handling
- shared load dispatch patterns if useful

It should not absorb all image/font/sound-specific logic if that makes it too broad.

---

## Sprite Loading

`sprite_loader.py` should own image-related loading behavior such as:
- loading images
- loading sprite sheets
- extracting sub-surfaces
- optional scaling or conversion helpers
- optional animation frame extraction helpers later

---

## Font Loading

`fonts.py` should define:
- font loading helpers
- font caching behavior
- standard access patterns for size/style combinations

Recommended rule:
- font size access should not repeatedly reload font files

---

## Sound Loading

`sounds.py` should define:
- sound loading helpers
- sound cache handling
- optional sound-group helpers later

This is distinct from `audio/audio_manager.py`, which should focus on playback/runtime policy.

---

## Loading Timing

Assets may be loaded in several ways:
- eagerly at startup
- lazily on first request
- through explicit preload steps

Recommended initial direction:
- allow lazy loading with cache
- support optional explicit preload for high-use assets

---

## Missing Asset Behavior

This must be defined up front.

Possible approaches:
- fail hard with clear errors
- log warnings and use placeholders
- use placeholders only in debug/dev mode

Recommended direction:
- fail loudly during engine/framework development
- optionally support safe placeholders later for game-facing polish

---

## Caching Policy

Assets should usually be cached after load.

Typical cache keys may include:
- normalized asset path
- font path + size
- sprite sheet identity + frame region

Recommended rule:
- cache ownership lives in the loader layer, not scattered throughout widgets/scenes

---

## Asset Naming Rules

Recommended project rules:
- lowercase file/folder names where practical
- descriptive names
- avoid spaces
- consistent folder grouping by type

Examples:
- `ui/button_primary.png`
- `fonts/inter_regular.ttf`
- `sounds/ui_click.wav`

---

## Engine Assets vs Game Assets

Open design question:
- should the engine support both engine-owned assets and project-owned assets?

Recommended direction:
- yes, keep the concept separate
- engine assets support shared visuals/debug tools
- project assets support game-specific content

This may matter more later than immediately.

---

## Relationship to Rendering

The asset pipeline loads and provides resources.

It should not:
- decide gameplay rendering behavior
- become the sprite animation system
- own scene draw policy

That belongs to `graphics`, `scene`, or higher-level systems.

---

## Rules for Future Development

1. Centralize paths.
2. Centralize caching.
3. Keep loaders type-specific where useful.
4. Define missing-asset behavior clearly.
5. Avoid scattered direct filesystem calls across the engine.

---

## Open Questions

- Should cache invalidation/reload exist in version one?
- Should engine and project asset roots both be supported immediately?
- Should placeholder assets be generated automatically in debug mode?
- Should asset manifests exist later for preload control?
