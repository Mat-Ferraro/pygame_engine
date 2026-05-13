"""
pygame_engine.scene

Scene system: base contract, stack, manager, and transitions.

Public API::

    from pygame_engine.scene import Scene, SceneManager, SceneStack
    from pygame_engine.scene.transitions import (
        FadeTransition,
        SlideTransition,
        CrossfadeTransition,
    )
"""

from pygame_engine.scene.scene import Scene
from pygame_engine.scene.scene_manager import SceneManager
from pygame_engine.scene.scene_stack import SceneStack

__all__ = ["Scene", "SceneManager", "SceneStack"]
