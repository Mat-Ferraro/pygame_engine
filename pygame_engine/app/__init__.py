"""
Application bootstrap and configuration.

Public API::

    from pygame_engine.app import Application, AppConfig
"""

from pygame_engine.app.application import Application
from pygame_engine.app.config import AppConfig
from pygame_engine.app.render_context import RenderContext

__all__ = ["Application", "AppConfig", "RenderContext"]