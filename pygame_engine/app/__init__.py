"""
pygame_engine.app

Application bootstrap and configuration.

Public API::

    from pygame_engine.app import Application, AppConfig
"""

from pygame_engine.app.application import Application
from pygame_engine.app.config import AppConfig

__all__ = ["Application", "AppConfig"]
