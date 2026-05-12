## Purpose

The persistence system provides reusable save/load infrastructure for projects built with `pygame_engine`.

Its purpose is to handle the generic parts of persistence, such as:
- safe file read/write behavior
- save slot support
- version tagging
- migration hooks
- serializer infrastructure
- save metadata handling

It should **not** define game-specific save schemas or gameplay state rules.

---

## Accepted Direction

The current accepted direction is:

- persistence infrastructure belongs in the engine
- save schema and game-state meaning belong in the game project
- the engine should provide a lightweight persistence layer, not a game-specific save framework
- save behavior should be safe, explicit, and version-aware

This follows the broader framework philosophy of keeping `pygame_engine` generic.

---

## Current Persistence Modules

The persistence package currently contains:

- `save_manager.py`
- `storage.py`
- `serializers.py`
- `migrations.py`

Suggested responsibilities:

### `save_manager.py`
High-level save/load orchestration.
- save slot access
- coordinating serialization and storage
- version metadata handling
- top-level save/load entry points

### `storage.py`
Low-level file storage behavior.
- reading files
- writing files
- atomic writes where supported
- backup or temp-file flow
- path-safe read/write handling

### `serializers.py`
Generic serialization helpers.
- object to serializable form conversion helpers
- JSON-friendly conversion patterns
- shared serialization utilities

### `migrations.py`
Version migration helpers.
- old save version detection
- migration pipeline entry points
- schema upgrade hooks

---

## Responsibility Split

### Engine responsibilities
The engine persistence layer may handle:
- file path resolution
- save slot organization
- metadata structure
- storage safety
- version fields
- migration hooks/infrastructure
- backup strategy
- corruption detection helpers
- serialization support helpers

### Game responsibilities
The game project should handle:
- what data gets saved
- what the save schema means
- entity reconstruction
- progression state reconstruction
- inventory/content/state semantics
- game-specific migration logic
- validation of game-specific fields

This boundary should remain explicit.

---

## Save File Philosophy

Recommended direction:
- save files should be structured, inspectable, and versioned
- top-level save data should be serializable to stable plain data
- game projects should provide the data model that is handed to persistence

Possible top-level save structure:

```json
{
  "save_version": 1,
  "created_at": "...",
  "updated_at": "...",
  "game_id": "my_game",
  "slot_id": "slot_1",
  "payload": { ... game-specific data ... }
}
```

The exact schema may vary, but the split between metadata and payload is strongly recommended.

---

## Versioning

Every save should include a version field.

Why:
- save formats change
- schema changes are normal over time
- migrations need a stable starting point

Recommended rule:
- engine-level save metadata contains a `save_version`
- game payload may also contain project-level versioning if helpful

---

## Migrations

The engine should support migration infrastructure, but not necessarily own all concrete migration logic.

The engine may provide:
- migration dispatch
- version comparison flow
- helper pipeline structure

A game may provide:
- version-specific transformation steps
- validation of migrated content
- domain-specific reconstruction rules

Recommended rule:
- the engine defines the migration path structure
- the game defines what its data changes actually mean

---

## Serialization Boundaries

Serialization should stay generic at the engine level.

The engine may help with:
- converting dataclasses or simple objects to serializable structures
- JSON-safe conversion helpers
- common primitive conversions

The engine should not assume:
- specific game entities
- specific game systems
- specific save payload layout

Recommended pattern:
- game builds plain serializable save payload
- engine persists it safely

---

## Storage Safety

Persistence should prefer safe write behavior.

Recommended practices:
- write to temp file first
- validate or flush write
- replace final file atomically if possible
- keep optional backup behavior later

This matters because save corruption is one of the most painful failure modes in games.

---

## Missing or Corrupt Saves

The persistence system should define clear failure behavior.

Recommended direction:
- missing saves should fail gracefully with clear “not found” behavior
- corrupt saves should fail loudly and clearly
- future fallback/backup recovery may be supported, but should not silently hide problems

---

## Save Slots

The persistence system may support save slots generically.

Possible slot responsibilities:
- slot listing
- slot metadata
- slot existence checks
- slot delete behavior
- slot rename/display name support later

Recommended rule:
- slot behavior belongs in persistence infrastructure
- slot content meaning belongs in the game

---

## Engine Assets vs Save Data

Persistence is not an asset system.

It should not:
- load textures, sprites, or sounds as part of save logic
- manage runtime rendering resources
- become the general-purpose data loading layer

It is specifically about persistent runtime state written to disk.

---

## Relationship to State

Persistence and runtime state are related but different:
- runtime state = current in-memory truth
- persistence = stored representation of selected state over time

The engine should not assume that the entire runtime state store is always directly serializable.

---

## Rules for Future Development

1. Keep persistence infrastructure generic.
2. Keep save schema meaning in the game project.
3. Version all saves.
4. Support migration explicitly.
5. Prefer safe writes over convenience.
6. Keep storage, serialization, and migration concerns separated.

---

## Open Questions

- Should slot metadata be standardized by the engine?
- Should backups be part of version one or later?
- Should the engine provide dataclass serialization helpers by default?
- Should migrations be engine-driven, game-driven, or hybrid?
