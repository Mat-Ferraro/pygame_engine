"""
app/application.py

The top-level runtime owner for a project built on pygame_engine.

Application is responsible for:
- Bootstrapping and shutting down pygame
- Creating and owning the display surface / window
- Owning the master clock and producing delta-time each frame
- Driving the main loop (event → update → render → present)
- Routing pygame events into the active scene flow
- Initialising and exposing shared runtime services
- Integrating optional debug systems as non-blocking layers

It is the runtime shell of the engine. It should not contain gameplay logic,
scene-specific logic, or widget logic, and it should not become a general-
purpose global store.

Typical usage::

    from pygame_engine.app import Application, AppConfig
    from mygame.scenes import MainMenuScene

    config = AppConfig(title="My Game", width=1280, height=720)
    Application(config).run(MainMenuScene())
"""

from __future__ import annotations

import pygame

from pygame_engine.app.config import AppConfig
from pygame_engine.assets.asset_loader import AssetLoader
from pygame_engine.debug.console import DebugConsole
from pygame_engine.debug.overlay import DebugOverlay
from pygame_engine.state.runtime_flags import flags as _runtime_flags
from pygame_engine.audio.audio_manager import AudioManager
from pygame_engine.input.input_manager import InputManager
from pygame_engine.theme.runtime import get_theme, set_theme
from pygame_engine.theme.defaults import Theme
from pygame_engine.scene.scene import Scene
from pygame_engine.scene.scene_manager import SceneManager


class Application:
    """
    Runtime shell for a pygame_engine project.

    Owns pygame initialisation, the display surface, the master clock,
    and the scene manager. Drives the frame loop until stopped.

    Services (input, theme, audio, assets, debug) are created during
    startup and exposed as read-only properties. Only cross-cutting
    services belong here; scene/widget-specific concerns do not.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        """
        Store configuration. Do not call pygame or create any resources here.

        Pygame is not initialised until :meth:`run` is called. This keeps
        construction side-effect-free and makes the object cheap to create
        in tests or tool scripts.

        Args:
            config: Runtime configuration. Defaults to ``AppConfig()`` if
                    not supplied.
        """
        self._config: AppConfig = config or AppConfig()

        # These are all set during _startup(); declared here so the type
        # checker knows they exist and their types.
        self._display_surface: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None
        self._is_running: bool = False

        # Services — all None until _startup() wires them up.
        # SceneManager, InputManager etc. will be imported and instantiated
        # here once those modules are written.
        self._scene_manager: SceneManager | None = None
        self._input_manager: InputManager | None = None
        self._assets: AssetLoader | None = None
        self._audio: AudioManager | None = None
        self._debug_overlay: DebugOverlay = DebugOverlay()
        self._debug_console: DebugConsole = DebugConsole()

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self, initial_scene: Scene) -> None:
        """
        Start up, run the main loop, then shut down cleanly.

        This is the single public entry point for running the engine. It calls
        :meth:`_startup`, enters :meth:`_loop`, and guarantees
        :meth:`_shutdown` runs even if an exception is raised.

        Args:
            initial_scene: The first scene to push onto the scene stack.
                           Type will be ``Scene`` once that module exists.
        """
        try:
            self._startup(initial_scene)
            self._loop()
        finally:
            self._shutdown()

    def stop(self) -> None:
        """
        Signal the main loop to exit cleanly after the current frame.

        Safe to call from anywhere (scene callbacks, input handlers, etc.).
        Does not immediately stop execution — the loop checks ``_is_running``
        at the top of each iteration.
        """
        self._is_running = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _startup(self, initial_scene: Scene) -> None:
        """
        Initialise pygame, create the window, set up services, push the
        initial scene.

        Called once by :meth:`run` before the loop starts. Order matters:
        pygame must be initialised before any Surface or Clock is created,
        and the scene manager must exist before the initial scene is pushed.
        """
        pygame.init()

        self._display_surface = self._create_display()
        self._clock = pygame.time.Clock()
        self._is_running = True

        pygame.display.set_caption(self._config.title)

        self._input_manager = InputManager()
        self._assets = AssetLoader(
            self._config.asset_root,
            debug=self._config.debug,
        )
        # Theme is globally accessible via get_theme(); no per-app instance needed.
        # Projects can call set_theme() before or after run() to customise.
        # TODO: initialise AssetLoader
        self._audio = AudioManager()

        # Reset runtime flags to defaults, then apply config.debug
        _runtime_flags.reset()
        if self._config.debug:
            _runtime_flags.enable_debug_all()
        # TODO: initialise debug tools if config.debug

        self._scene_manager = SceneManager()
        self._scene_manager.push(initial_scene)

    def _loop(self) -> None:
        """
        Drive the frame loop until ``_is_running`` becomes False.

        Frame order (fixed, do not reorder without updating the doc):
          1. poll events
          2. update input snapshot
          3. route events to scene flow
          4. update scene flow
          5. update debug / runtime overlays  (no-op when debug is off)
          6. clear back-buffer
          7. render scene flow
          8. render overlays / debug          (no-op when debug is off)
          9. flip / present display
         10. tick clock → compute dt for next frame
        """
        dt: float = 0.0

        while self._is_running:

            # 1. Poll events
            events = pygame.event.get()

            # 2. Update input snapshot
            if self._input_manager is not None:
                self._input_manager.update(events)

            # 3. Route events to scene flow
            for event in events:
                self._handle_event(event)

            # 4. Update scene flow
            if self._scene_manager is not None:
                self._scene_manager.update(dt)

            # 5. Update debug overlays (skipped when debug is off)
            # TODO: debug overlay update

            # 6. Clear back-buffer
            assert self._display_surface is not None
            self._display_surface.fill((0, 0, 0))

            # 7. Render scene flow
            if self._scene_manager is not None:
                self._scene_manager.render(self._display_surface)

            # 8. Render debug overlays
            self._debug_overlay.render(
                self._display_surface,
                self._clock,
                self._scene_manager,
            )
            self._debug_console.render(self._display_surface)

            # 9. Present
            pygame.display.flip()

            # 10. Tick clock → dt for next frame
            assert self._clock is not None
            raw_ms = self._clock.tick(self._config.target_fps)
            dt = self._compute_dt(raw_ms)

    def _shutdown(self) -> None:
        """
        Release resources and quit pygame.

        Called by :meth:`run` in a ``finally`` block so it always runs, even
        if the loop exits via an exception. Should not raise.
        """
        if self._scene_manager is not None:
            # Pop all scenes cleanly so on_exit() is called on each.
            while not self._scene_manager.is_empty:
                self._scene_manager.pop()
        if self._audio is not None:
            self._audio.shutdown()
        # TODO: shutdown debug tools

        pygame.quit()

    # ── Event routing ─────────────────────────────────────────────────────────

    def _handle_event(self, event: pygame.event.Event) -> None:
        """
        Route a single pygame event through the engine's priority layers.

        Routing order (from highest to lowest priority):
          1. Application-level essential handling (quit, window resize)
          2. Topmost / modal scene or overlay via SceneManager
          3. Focused widget / UI layer              (handled inside scene)
          4. Scene-level logic                      (handled inside scene)
          5. Global debug / runtime shortcuts

        Layers return True if they consume the event; lower layers are then
        skipped. This matches the accepted engine input-routing contract.
        """
        # 1. Application-level essentials
        if event.type == pygame.QUIT:
            self.stop()
            return

        if event.type == pygame.VIDEORESIZE and self._config.resizable:
            self._on_resize(event.w, event.h)
            return

        # 2–4. Scene flow (InputManager has already updated this frame)
        if self._scene_manager is not None:
            if self._scene_manager.handle_event(event):
                return

        # 5. Global debug shortcuts
        if self._input_manager is not None:
            from pygame_engine.input import actions as _actions
            from pygame_engine.state.runtime_flags import flags as _flags
            if self._input_manager.was_action_pressed(_actions.DEBUG_TOGGLE):
                _flags.toggle('show_overlay')
                return
            if self._input_manager.was_action_pressed(_actions.INSPECTOR_TOGGLE):
                from pygame_engine.debug.inspector import Inspector
                Inspector().dump(self._scene_manager)
                return

    # ── Display helpers ───────────────────────────────────────────────────────

    def _create_display(self) -> pygame.Surface:
        """
        Create and return the pygame display surface.

        Reads window dimensions, fullscreen, resizable, and vsync from config.
        Called once during :meth:`_startup`.
        """
        flags = 0

        if self._config.fullscreen:
            flags |= pygame.FULLSCREEN
        elif self._config.resizable:
            flags |= pygame.RESIZABLE

        if self._config.vsync:
            flags |= pygame.SCALED  # SCALED enables vsync support

        return pygame.display.set_mode(
            (self._config.width, self._config.height),
            flags,
            vsync=1 if self._config.vsync else 0,
        )

    def _on_resize(self, width: int, height: int) -> None:
        """
        Handle a window resize event.

        Updates the display surface reference so the new dimensions are
        reflected everywhere that reads ``display_surface``.

        Args:
            width:  New window width in pixels.
            height: New window height in pixels.
        """
        self._display_surface = pygame.display.set_mode(
            (width, height),
            pygame.RESIZABLE,
            vsync=1 if self._config.vsync else 0,
        )
        # TODO: notify SceneManager / layout system of new surface size

    # ── Delta-time ────────────────────────────────────────────────────────────

    def _compute_dt(self, raw_ms: int) -> float:
        """
        Convert the raw millisecond tick from the clock into a clamped
        seconds-based delta-time value.

        Args:
            raw_ms: Milliseconds returned by ``pygame.time.Clock.tick()``.

        Returns:
            Delta time in seconds, clamped to ``config.max_dt`` if non-zero.
        """
        dt = raw_ms / 1000.0
        if self._config.max_dt > 0:
            dt = min(dt, self._config.max_dt)
        return dt

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def scene_manager(self) -> SceneManager:
        """
        The scene manager.

        Only valid after ``run()`` has been called.
        Raises ``RuntimeError`` if accessed before startup.
        """
        if self._scene_manager is None:
            raise RuntimeError(
                "scene_manager is not available before Application.run() is called."
            )
        return self._scene_manager

    @property
    def audio(self) -> AudioManager:
        """
        The audio manager.

        Only valid after ``run()`` has been called.
        Raises ``RuntimeError`` if accessed before startup.
        """
        if self._audio is None:
            raise RuntimeError(
                "audio is not available before Application.run() is called."
            )
        return self._audio

    @property
    def assets(self) -> AssetLoader:
        """
        The asset loader.

        Only valid after ``run()`` has been called.
        Raises ``RuntimeError`` if accessed before startup.
        """
        if self._assets is None:
            raise RuntimeError(
                "assets is not available before Application.run() is called."
            )
        return self._assets

    @property
    def theme(self) -> Theme:
        """
        The active theme.

        Convenience accessor — equivalent to ``get_theme()`` from
        ``pygame_engine.theme.runtime``. Projects can replace the theme
        via ``set_theme()`` or ``app.set_theme()``.
        """
        return get_theme()

    def set_theme(self, theme: Theme) -> None:
        """
        Replace the active theme.

        Equivalent to calling ``pygame_engine.theme.runtime.set_theme()``.
        Takes effect on the next frame.

        Args:
            theme: The new ``Theme`` instance to activate.
        """
        set_theme(theme)

    @property
    def input_manager(self) -> InputManager:
        """
        The input manager.

        Only valid after ``run()`` has been called.
        Raises ``RuntimeError`` if accessed before startup.
        """
        if self._input_manager is None:
            raise RuntimeError(
                "input_manager is not available before Application.run() is called."
            )
        return self._input_manager

    @property
    def config(self) -> AppConfig:
        """The configuration this application was created with."""
        return self._config

    @property
    def is_running(self) -> bool:
        """True while the main loop is active."""
        return self._is_running

    @property
    def display_surface(self) -> pygame.Surface:
        """
        The main display surface.

        Only valid after :meth:`run` has been called (i.e. after startup).
        Raises ``RuntimeError`` if accessed before startup.
        """
        if self._display_surface is None:
            raise RuntimeError(
                "display_surface is not available before Application.run() is called."
            )
        return self._display_surface

    @property
    def clock(self) -> pygame.time.Clock:
        """
        The master clock.

        Only valid after :meth:`run` has been called.
        Raises ``RuntimeError`` if accessed before startup.
        """
        if self._clock is None:
            raise RuntimeError(
                "clock is not available before Application.run() is called."
            )
        return self._clock
