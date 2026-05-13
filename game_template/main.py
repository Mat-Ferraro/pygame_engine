"""
main.py

Entry point for MY_GAME.

This file wires together the engine configuration and launches the
first scene. Keep this file thin — application setup only. All game
logic lives in game/.

Steps to customise:
1. Replace MY_GAME with your game title everywhere
2. Set your desired resolution and FPS in AppConfig
3. Add your asset_root path (default is Path("assets"))
4. Register any custom keybindings in _build_bindings()
5. Apply a custom theme in _build_theme() if desired
6. Replace MainMenuScene with your actual first scene
"""

from pathlib import Path

from pygame_engine.app import Application, AppConfig
from pygame_engine.input.bindings import DEFAULT_BINDINGS

from game.scenes.main_menu import MainMenuScene


def _build_config() -> AppConfig:
    """Build and return the application configuration."""
    return AppConfig(
        title       = "MY_GAME",
        width       = 1280,
        height      = 720,
        target_fps  = 60,
        asset_root  = Path("assets"),
        debug       = False,   # set True during development for debug overlay
    )


def _build_bindings() -> dict:
    """
    Build the key-to-action binding map.

    Start from DEFAULT_BINDINGS and add game-specific bindings.
    Import your custom action constants from game/actions.py.
    """
    from game import actions as game_actions

    return {
        **DEFAULT_BINDINGS,
        # Add game-specific bindings here, e.g.:
        # pygame.K_z:      game_actions.ATTACK,
        # pygame.K_x:      game_actions.INTERACT,
        # pygame.K_LSHIFT: game_actions.SPRINT,
    }


def main() -> None:
    config = _build_config()
    app    = Application(config)

    # Apply custom bindings before the loop starts
    # (InputManager is created in app._startup, so set after run() is
    #  called — do it in your first scene's on_enter instead if needed)

    app.run(MainMenuScene(app))


if __name__ == "__main__":
    main()
