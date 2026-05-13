"""
pygame_engine.state

Engine-level runtime state primitives.

Public API::

    from pygame_engine.state import flags          # RuntimeFlags singleton
    from pygame_engine.state import RuntimeFlags   # class for subclassing
    from pygame_engine.state import Observable     # reactive value wrapper
"""

from pygame_engine.state.observable import Observable
from pygame_engine.state.runtime_flags import RuntimeFlags, flags

__all__ = ["Observable", "RuntimeFlags", "flags"]
