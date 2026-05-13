"""
pygame_engine.ui.containers

Container widgets that group and manage child widgets.

Public API::

    from pygame_engine.ui.containers import Panel, Stack, Scrollable
"""

from pygame_engine.ui.containers.panel import Panel
from pygame_engine.ui.containers.scrollable import Scrollable
from pygame_engine.ui.containers.stack import Stack

__all__ = ["Panel", "Scrollable", "Stack"]
