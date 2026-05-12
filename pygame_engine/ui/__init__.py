"""
pygame_engine.ui

Reusable UI primitives.

Public API::

    from pygame_engine.ui import Widget
    from pygame_engine.ui import Panel
    from pygame_engine.ui import Button
    from pygame_engine.ui import Label
"""

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.containers.panel import Panel
from pygame_engine.ui.controls.button import Button
from pygame_engine.ui.text.label import Label

__all__ = [
    "Widget",
    "Panel",
    "Button",
    "Label",
    # feedback — coming soon
]
