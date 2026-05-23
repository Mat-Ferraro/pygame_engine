"""
pygame_engine.scene

Scene base class, manager, stack, transitions, descriptor system.

Public API::

    from pygame_engine.scene import Scene
    from pygame_engine.scene import SceneManager
    from pygame_engine.scene import SceneStack
    from pygame_engine.scene import FadeTransition, SlideTransition, CrossfadeTransition
    from pygame_engine.scene import DescribedScene
    from pygame_engine.scene import SceneDescriptor, WidgetNode
"""

from pygame_engine.scene.described_scene import DescribedScene
from pygame_engine.scene.scene import Scene
from pygame_engine.scene.scene_descriptor import SceneDescriptor, WidgetNode
from pygame_engine.scene.scene_manager import SceneManager
from pygame_engine.scene.scene_stack import SceneStack
from pygame_engine.scene.transitions import (
    CrossfadeTransition,
    FadeTransition,
    SlideTransition,
)

__all__ = [
    "CrossfadeTransition",
    "DescribedScene",
    "FadeTransition",
    "Scene",
    "SceneDescriptor",
    "SceneManager",
    "SceneStack",
    "SlideTransition",
    "WidgetNode",
]
