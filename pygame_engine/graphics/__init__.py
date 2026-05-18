"""
Rendering helpers and surface utilities.

Public API::

    from pygame_engine.graphics import draw_surface_style, draw_chevron
    from pygame_engine.graphics import draw_nine_slice, NineSlicePanel
    from pygame_engine.graphics import draw_sprite, draw_animation_frame
    from pygame_engine.graphics import make_alpha_surface, scale_surface
"""

from pygame_engine.graphics.draw_utils import (
    draw_chevron,
    draw_cross,
    draw_horizontal_line,
    draw_rect_bordered,
    draw_surface_style,
    draw_vertical_line,
)
from pygame_engine.graphics.nine_slice import (
    NineSlicePanel,
    draw_nine_slice,
    make_nine_slice_surface,
)
from pygame_engine.graphics.sprite_renderer import (
    draw_animation_frame,
    draw_sprite,
)
from pygame_engine.graphics.surfaces import (
    blit_alpha,
    blit_alpha_surface,
    crop_surface,
    make_alpha_surface,
    make_solid_surface,
    scale_surface,
)

from pygame_engine.graphics.text_utils import (
    truncate,
    wrap_and_truncate,
    wrap_text,
)

__all__ = [
    # draw_utils
    "draw_surface_style",
    "draw_rect_bordered",
    "draw_horizontal_line",
    "draw_vertical_line",
    "draw_cross",
    "draw_chevron",
    # surfaces
    "make_alpha_surface",
    "make_solid_surface",
    "blit_alpha",
    "blit_alpha_surface",
    "scale_surface",
    "crop_surface",
    # nine_slice
    "draw_nine_slice",
    "make_nine_slice_surface",
    "NineSlicePanel",
    # sprite_renderer
    "draw_sprite",
    "draw_animation_frame",
    # text_utils
    "truncate",
    "wrap_text",
    "wrap_and_truncate",
]