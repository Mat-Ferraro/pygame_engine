"""
scene/transitions.py

Scene transition helpers (fade, slide, crossfade, etc.).

Transitions are visual effects that play during a scene change. They are
handled here, separately from scene logic, so scenes do not need to
implement transition math themselves.

Status: stub — not implemented in v1 spine pass.
Transitions are deferred until the core scene/widget system is stable.

Planned responsibilities:
- Transition base class with update(dt) -> bool (returns True when done)
- FadeTransition, SlideTransition, CrossfadeTransition implementations
- SceneManager will accept an optional Transition on push/replace/pop
"""
