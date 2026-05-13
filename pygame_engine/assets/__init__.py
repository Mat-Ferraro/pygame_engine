"""
pygame_engine.assets

Asset loading, caching, and path resolution.

Public API::

    from pygame_engine.assets import AssetLoader

    # Via Application (preferred):
    image = app.assets.image("ui/button.png")
    font  = app.assets.font("inter.ttf", size=18)
    sound = app.assets.sound("click.wav")
"""

from pygame_engine.assets.asset_loader import AssetLoader, AssetNotFoundError

__all__ = ["AssetLoader", "AssetNotFoundError"]
