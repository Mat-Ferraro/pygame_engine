"""
pygame_engine.ui

Reusable UI primitives.

Public API::

    from pygame_engine.ui import Widget, Panel, Stack, Button, Label, TextBlock
"""

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.containers.panel import Panel
from pygame_engine.ui.containers.stack import Stack
from pygame_engine.ui.controls.button import Button
from pygame_engine.ui.text.label import Label
from pygame_engine.ui.text.text_block import TextBlock

__all__ = [
    "Widget",
    "Panel",
    "Stack",
    "Button",
    "Label",
    "TextBlock",
    # feedback — coming soon
]
