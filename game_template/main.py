"""
Entry point for MY_GAME.

This file wires together the engine configuration and launches the
first scene. Keep this file thin — application setup only. All game
logic lives in game/.

Steps to customise:
1. Replace MY_GAME with your game title everywhere
2. Set your desired resolution and FPS in AppConfig
3. Add your asset_root path (default is Path("assets"))
4. Set debug=True during development to enable the debug overlay
5. Replace MainMenuScene with your actual first scene if needed
"""

import sys
from pathlib import Path

from pygame_engine.app import Application, AppConfig
from pygame_engine.debug.crash_log import crash_guard

from game.locale import load_locales
from game.scenes.main_menu import MainMenuScene


def _build_config() -> AppConfig:
    """Build and return the application configuration."""
    return AppConfig(
        title      = "MY_GAME",
        width      = 1280,
        height     = 720,
        target_fps = 60,
        asset_root = Path("assets"),
        debug      = False,   # set True during development for debug overlay
    )


def main() -> None:
    load_locales()   # load all locale files before the first frame
    config = _build_config()
    app    = Application(config)

    crash_log = Path("crash.log")
    with crash_guard(crash_log):
        app.run(MainMenuScene(app))

    # If a crash log was written, print its location so it's not silent
    if crash_log.exists():
        print(f"\nCrash report written to: {crash_log.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
