# Decision Log

## Purpose

This document records important architecture and process decisions for `pygame_engine`.

Use it to capture:
- what was decided
- why it was decided
- alternatives considered
- any follow-up actions

This is a living document and should be updated as the engine evolves.

---

## Entry Format

Recommended format:

### YYYY-MM-DD - Topic
**Decision**  
What was decided.

**Reason**  
Why the decision was made.

**Alternatives considered**  
What other options were considered.

**Follow-up**  
Any consequences, future work, or related docs to update.

---

## Decisions

### 2026-05-11 - Project identity
**Decision**  
`pygame_engine` is a reusable lightweight pygame framework, not a game-specific codebase or genre engine.

**Reason**  
The goal is to support multiple future projects and reduce repeated framework work without overbuilding into a genre-specific architecture.

**Alternatives considered**  
Using it as a single game codebase or as a game-template-only repository.

**Follow-up**  
Keep game-specific rules and content out of engine modules.

---

### 2026-05-11 - Public API style
**Decision**  
Prefer clean top-level imports such as:
```python
from pygame_engine.ui import Button
from pygame_engine.scene import Scene
```

**Reason**  
This is clearer and more intentional for engine consumers than relying on deep internal import paths.

**Alternatives considered**  
Exposing primarily deep module imports.

**Follow-up**  
Use package `__init__.py` files to maintain a stable public API surface.

---

### 2026-05-11 - Scene runtime model
**Decision**  
Use a stack-based runtime model for scenes.

**Reason**  
A stack naturally supports overlays, pause menus, modals, debug layers, and replacement behavior through one unified model.

**Alternatives considered**  
A replace-only scene model with a separate overlay mechanism.

**Follow-up**  
`SceneManager` should coordinate a `SceneStack`.

---

### 2026-05-11 - Event consumption contract
**Decision**  
Scene and widget `handle_event` methods should return `bool`.

**Reason**  
This makes layered UI/input routing significantly easier to reason about.

**Alternatives considered**  
Void-return event handlers or out-of-band consumption tracking.

**Follow-up**  
Reflect this in scene and widget contract docs.

---

### 2026-05-11 - Scene and UI relationship
**Decision**  
Scenes may optionally own a `root_widget`.

**Reason**  
This keeps scenes focused on flow/orchestration while allowing a structured UI tree.

**Alternatives considered**  
Keeping scenes fully separate from widget trees or having scenes manually manage many unrelated widgets.

**Follow-up**  
Document the scene/root-widget relationship clearly.

---

### 2026-05-11 - Base widget responsibility
**Decision**  
Base widgets do not automatically manage children.

**Reason**  
This keeps the base widget simpler and assigns hierarchy management to container widgets where it belongs.

**Alternatives considered**  
Making every widget tree-capable by default.

**Follow-up**  
Container widgets should define child traversal behavior.

---

### 2026-05-11 - Layout scope for version one
**Decision**  
Version one layout will use assigned rects and simple layout helpers.

**Reason**  
This provides useful structure without prematurely building a full advanced layout engine.

**Alternatives considered**  
Implementing a more complex measure/layout system immediately.

**Follow-up**  
Leave room for future expansion, but keep v1 simple.

---

### 2026-05-11 - Theme access direction
**Decision**  
Widgets may access styling through a stable runtime theme interface.

**Reason**  
This supports centralized styling without requiring a heavy injected styling architecture in version one.

**Alternatives considered**  
Hardcoded styling or full external style injection from the start.

**Follow-up**  
Keep theme values centralized and documented.

---

### 2026-05-11 - Asset loading philosophy
**Decision**  
Use lazy loading with caching and fail loudly during development.

**Reason**  
This reduces startup complexity while keeping debugging straightforward.

**Alternatives considered**  
Full eager preload by default or placeholder-based silent fallback.

**Follow-up**  
Document missing-asset behavior and cache ownership clearly.

---

### 2026-05-11 - Debug tools position
**Decision**  
Debug tools are important and should be supported, but remain optional runtime layers.

**Reason**  
Game development benefits heavily from debug support, but the core runtime should not depend on debug systems to function.

**Alternatives considered**  
Treating debug systems as mandatory runtime architecture or as an afterthought.

**Follow-up**  
Integrate debug tools cleanly through app/input/runtime design.

---

### 2026-05-11 - Engine state boundary
**Decision**  
Engine-level shared state should remain limited to engine/runtime concerns.

**Reason**  
This keeps the framework generic and prevents it from absorbing game-specific domain state.

**Alternatives considered**  
Using the engine state store as a general-purpose global state container.

**Follow-up**  
Keep gameplay/project state in consuming projects.

---

### 2026-05-11 - Typing philosophy
**Decision**  
Use moderate but intentional typing.

**Reason**  
Important contracts and reusable utilities benefit from typing, but overly strict typing should not block early engine development.

**Alternatives considered**  
Very light typing or very strict typing everywhere immediately.

**Follow-up**  
Type core contracts and public APIs first.

---

### 2026-05-11 - Version one boundary
**Decision**  
Version one will focus on the runtime spine, core UI primitives, basic layout, input, theme, asset loading, and examples.

**Reason**  
This keeps the first usable version focused and achievable.

**Alternatives considered**  
Expanding version one to include more ambitious systems immediately.

**Follow-up**  
Use the roadmap to guide implementation order.

---

### 2026-05-11 - Documentation discipline
**Decision**  
Update docs whenever a core contract changes, a framework-wide design decision is made, or a naming/organization rule changes.

**Reason**  
The docs are intended to be a living development reference, not a stale afterthought.

**Alternatives considered**  
Only updating docs at major milestones.

**Follow-up**  
Use this decision log together with system docs and the accepted-decisions document.
