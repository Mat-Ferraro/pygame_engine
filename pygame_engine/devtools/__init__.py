"""
pygame_engine.devtools

Development-time debug tools.

All tools are optional — they do nothing unless the relevant
``RuntimeFlags`` are enabled. Safe to leave in production builds.

Public API::

    from pygame_engine.devtools import DebugOverlay, DebugConsole, Inspector
    from pygame_engine.devtools.debug_log import log, warn, error, get_entries
    from pygame_engine.devtools.crash_log import install_crash_handler, crash_guard
"""

from pygame_engine.devtools.console import DebugConsole
from pygame_engine.devtools.crash_log import crash_guard, install_crash_handler
from pygame_engine.devtools.inspector import Inspector
from pygame_engine.devtools.overlay import DebugOverlay

__all__ = [
    "DebugOverlay",
    "DebugConsole",
    "Inspector",
    "install_crash_handler",
    "crash_guard",
]