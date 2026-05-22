"""
RenderContext — render-time context passed to every widget render call.

All data a widget needs at render time that is not stored on the widget
itself lives here. Currently carries the active theme. Future slots are
reserved for camera, gizmo renderer, and debug flags so those can be
added without changing render() signatures again.

Usage (Application builds one per frame)::

    ctx = RenderContext(theme=get_theme())
    scene_manager.render(surface, ctx)

Usage (widgets read theme through ctx)::

    def render(self, surface: pygame.Surface, ctx: RenderContext) -> None:
        colour = ctx.theme.button.normal.bg
        pygame.draw.rect(surface, colour, self.rect)
"""

from __future__ import annotations

from dataclasses import dataclass

from pygame_engine.theme.defaults import Theme


@dataclass(frozen=True)
class RenderContext:
    """
    Immutable render-time context passed from Application down to every widget.

    Attributes:
        theme: The active theme for this frame. All widgets read colours,
               sizes, and styles from here instead of calling get_theme().

    Future slots (reserved, not yet used):
        camera:      Camera for world-space coordinate translation.
        gizmos:      GizmoRenderer for debug overlays (None in production).
        debug_flags: Fine-grained rendering debug controls.
    """

    theme: Theme
