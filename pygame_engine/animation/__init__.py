"""
pygame_engine.animation

Time-based animation helpers.

Public API::

    from pygame_engine.animation import Tween
    from pygame_engine.animation import SpriteAnimation, AnimationPlayer
    from pygame_engine.animation.easing import ease_out_cubic, ease_in_back
    from pygame_engine.animation.easing import EASING_FUNCTIONS, get_easing
"""

from pygame_engine.animation.animator import AnimationPlayer, SpriteAnimation
from pygame_engine.animation.tween import Tween

__all__ = ["Tween", "SpriteAnimation", "AnimationPlayer"]
