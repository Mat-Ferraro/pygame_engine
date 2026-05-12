"""
pygame_engine.input

Input abstraction: actions, bindings, and per-frame state queries.

Public API::

    from pygame_engine.input import actions
    from pygame_engine.input import InputManager
    from pygame_engine.input.bindings import DEFAULT_BINDINGS
"""

from pygame_engine.input.input_manager import InputManager

__all__ = ["InputManager", "actions"]
