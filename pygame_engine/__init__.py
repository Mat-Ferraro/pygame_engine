"""
pygame_engine

A lightweight reusable framework built on pygame-ce.

Most imports should come from subpackages directly:

    from pygame_engine.app    import Application, AppConfig
    from pygame_engine.scene  import Scene, SceneManager, SceneStack
    from pygame_engine.ui     import Widget, Panel, Stack, Button, Label
    from pygame_engine.layout import anchor, row, column, grid
    from pygame_engine.theme  import get_theme, set_theme, Theme
    from pygame_engine.input  import InputManager, actions
    from pygame_engine.animation import Tween
    from pygame_engine.assets import AssetLoader
    from pygame_engine.audio  import AudioManager

See docs/using_pygame_engine.md for a full usage guide.
"""

__version__ = "0.1.0"
__all__      = ["__version__"]
