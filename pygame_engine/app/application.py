"""
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
from pygame_engine.audio.audio_manager import AudioManager
from pygame_engine.debug.console import DebugConsole
from pygame_engine.debug.overlay import DebugOverlay
from pygame_engine.events.event_bus import bus as _event_bus
from pygame_engine.input.input_manager import InputManager
from pygame_engine.scene.scene import Scene
from pygame_engine.scene.scene_manager import SceneManager
from pygame_engine.state.runtime_flags import flags as _runtime_flags
from pygame_engine.theme.defaults import Theme
from pygame_engine.theme.runtime import get_theme, set_theme


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

        self._display_surface: pygame.Surface | None = None
        self._clock:           pygame.time.Clock | None = None
        self._is_running:      bool = False

        self._scene_manager: SceneManager | None = None
        self._input_manager: InputManager | None = None
        self._assets:        AssetLoader  | None = None
        self._audio:         AudioManager | None = None

        # Debug tools are always created; they self-check RuntimeFlags
        # and are no-ops when debug mode is off.
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
        Initialise pygame, create the window, set up all services, push the
        initial scene.

        Called once by :meth:`run` before the loop starts. Order matters:
        pygame must be initialised before any Surface or Clock is created,
        and the scene manager must exist before the initial scene is pushed.
        """
        pygame.init()

        self._display_surface = self._create_display()
        self._clock           = pygame.time.Clock()
        self._is_running      = True

        pygame.display.set_caption(self._config.title)

        # Initialise all services
        self._input_manager = InputManager()
        self._assets = AssetLoader(
            self._config.asset_root,
            debug=self._config.debug,
        )
        self._audio = AudioManager()

        # Reset runtime flags to defaults, then apply config.debug.
        # Debug overlay and console check these flags themselves each frame.
        _runtime_flags.reset()
        if self._config.debug:
            _runtime_flags.enable_debug_all()

        self._scene_manager = SceneManager()
        self._scene_manager.push(initial_scene)

    def _loop(self) -> None:
        """
        Drive the frame loop until ``_is_running`` becomes False.

        Frame order (fixed — do not reorder without updating this docstring):
          1.  Poll events
          2.  Update input snapshot
          3.  Route events to scene flow
          4.  Update scene flow
          5.  Clear back-buffer
          6.  Render scene flow
          7.  Render debug overlays (no-op when debug flags are off)
          8.  Flip / present display
          9.  Tick clock → compute dt for next frame
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

            # 5. Clear back-buffer
            assert self._display_surface is not None
            self._display_surface.fill((0, 0, 0))

            # 6. Render scene flow
            if self._scene_manager is not None:
                self._scene_manager.render(self._display_surface)

            # 7. Render debug overlays (self-check flags; no-op when off)
            self._debug_overlay.render(
                self._display_surface,
                self._clock,
                self._scene_manager,
            )
            self._debug_console.render(self._display_surface)

            # 8. Present
            pygame.display.flip()

            # 9. Tick clock → dt for next frame
            assert self._clock is not None
            raw_ms = self._clock.tick(self._config.target_fps)
            dt     = self._compute_dt(raw_ms)

    def _shutdown(self) -> None:
        """
        Release resources and quit pygame.

        Called by :meth:`run` in a ``finally`` block so it always runs,
        even if the loop exits via an exception. Should not raise.
        """
        if self._scene_manager is not None:
            # Pop all scenes cleanly so on_exit() is called on each.
            while not self._scene_manager.is_empty:
                self._scene_manager.pop()

        if self._audio is not None:
            self._audio.shutdown()

        # Clear event bus so stale handlers don't survive between runs.
        _event_bus.clear_all()

        pygame.quit()

    # ── Event routing ─────────────────────────────────────────────────────────

    def _handle_event(self, event: pygame.event.Event) -> None:
        """
        Route a single pygame event through the engine's priority layers.

        Routing order (highest → lowest priority):
          1. Application-level essentials (quit, window resize)
          2. Scene flow via SceneManager
          3. Global debug / runtime shortcuts (F1, F2)

        Layers return True if they consume the event; lower layers are skipped.
        """
        # 1. Application-level essentials
        if event.type == pygame.QUIT:
            self.stop()
            return

        if event.type == pygame.VIDEORESIZE and self._config.resizable:
            self._on_resize(event.w, event.h)
            return

        # 2. Scene flow
        if self._scene_manager is not None:
            if self._scene_manager.handle_event(event):
                return

        # 3. Global debug shortcuts
        if self._input_manager is not None:
            from pygame_engine.input import actions as _actions
            from pygame_engine.state.runtime_flags import flags as _flags
            if self._input_manager.was_action_pressed(_actions.DEBUG_TOGGLE):
                _flags.toggle("show_overlay")
                return
            if self._input_manager.was_action_pressed(_actions.INSPECTOR_TOGGLE):
                from pygame_engine.debug.inspector import Inspector
                Inspector().dump(self._scene_manager)
                return
            if self._input_manager.was_action_pressed(_actions.CONSOLE_TOGGLE):
                _flags.toggle("show_console")
                return

    # ── Display helpers ───────────────────────────────────────────────────────

    def _create_display(self) -> pygame.Surface:
        """Create and return the pygame display surface from config."""
        flags = 0
        if self._config.fullscreen:
            flags |= pygame.FULLSCREEN
        elif self._config.resizable:
            flags |= pygame.RESIZABLE
        if self._config.vsync:
            flags |= pygame.SCALED

        return pygame.display.set_mode(
            (self._config.width, self._config.height),
            flags,
            vsync=1 if self._config.vsync else 0,
        )

    def _on_resize(self, width: int, height: int) -> None:
        """
        Handle a window resize event.

        Recreates the display surface at the new size. Scenes and widgets
        use the surface dimensions they receive in ``render()`` each frame,
        so no further notification is needed — they adapt naturally.

        After recreating the surface, notifies the active scene via
        ``scene_manager.notify_resize()`` and fires ``window.resized``
        on the event bus. Scenes override ``on_resize()`` to rebuild
        their layout. Subscribe to ``window.resized`` for non-scene code.

        Args:
            width:  New window width in pixels.
            height: New window height in pixels.
        """
        self._display_surface = pygame.display.set_mode(
            (width, height),
            pygame.RESIZABLE,
            vsync=1 if self._config.vsync else 0,
        )

        # Notify the active scene so it can rebuild its layout.
        if self._scene_manager is not None:
            self._scene_manager.notify_resize(width, height)

        # Fire a bus event so any subscriber can react.
        _event_bus.emit("window.resized", width=width, height=height)


    def set_resolution(self, width: int, height: int) -> None:
        """
        Change the window resolution at runtime.

        Recreates the display surface, notifies the active scene via
        ``on_resize()``, and fires ``window.resized`` on the event bus.

        Args:
            width:  New window width in pixels.
            height: New window height in pixels.
        """
        self._on_resize(width, height)

    def set_fullscreen(self, fullscreen: bool) -> None:
        """
        Toggle fullscreen mode at runtime.

        Recreates the display surface, notifies the active scene via
        ``on_resize()``, and fires ``window.fullscreen_changed`` on the bus.

        Args:
            fullscreen: True to enter fullscreen, False for windowed.
        """
        if self._display_surface is None:
            return
        w, h  = self._display_surface.get_size()
        flags = pygame.FULLSCREEN if fullscreen else (
            pygame.RESIZABLE if self._config.resizable else 0
        )
        self._display_surface = pygame.display.set_mode(
            (w, h), flags,
            vsync=1 if self._config.vsync else 0,
        )
        # Read actual size after mode change (may differ in fullscreen)
        nw, nh = self._display_surface.get_size()
        if self._scene_manager is not None:
            self._scene_manager.notify_resize(nw, nh)
        _event_bus.emit("window.fullscreen_changed", fullscreen=fullscreen)
        _event_bus.emit("window.resized", width=nw, height=nh)

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen on/off."""
        if self._display_surface is None:
            return
        currently = bool(self._display_surface.get_flags() & pygame.FULLSCREEN)
        self.set_fullscreen(not currently)

    # ── Delta-time ────────────────────────────────────────────────────────────

    def _compute_dt(self, raw_ms: int) -> float:
        """Convert raw milliseconds from the clock into a clamped dt in seconds."""
        dt = raw_ms / 1000.0
        if self._config.max_dt > 0:
            dt = min(dt, self._config.max_dt)
        return dt

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def scene_manager(self) -> SceneManager:
        """The scene manager. Only valid after ``run()`` is called."""
        if self._scene_manager is None:
            raise RuntimeError(
                "scene_manager is not available before Application.run() is called."
            )
        return self._scene_manager

    @property
    def audio(self) -> AudioManager:
        """The audio manager. Only valid after ``run()`` is called."""
        if self._audio is None:
            raise RuntimeError(
                "audio is not available before Application.run() is called."
            )
        return self._audio

    @property
    def assets(self) -> AssetLoader:
        """The asset loader. Only valid after ``run()`` is called."""
        if self._assets is None:
            raise RuntimeError(
                "assets is not available before Application.run() is called."
            )
        return self._assets

    @property
    def theme(self) -> Theme:
        """The active theme. Equivalent to ``get_theme()``."""
        return get_theme()

    def set_theme(self, theme: Theme) -> None:
        """Replace the active theme. Takes effect on the next frame."""
        set_theme(theme)

    @property
    def input_manager(self) -> InputManager:
        """The input manager. Only valid after ``run()`` is called."""
        if self._input_manager is None:
            raise RuntimeError(
                "input_manager is not available before Application.run() is called."
            )
        return self._input_manager

    @property
    def screen_rect(self) -> "pygame.Rect":
        """
        A rect covering the full screen at the current resolution.

        Equivalent to ``pygame.Rect(0, 0, config.width, config.height)``.
        Use this in ``on_enter`` instead of hardcoding dimensions::

            screen = self._app.screen_rect
            panel  = Panel(anchor(screen, (320, 400), "center"))

        Always reflects the current window size, even after resize.
        """
        if self._display_surface is not None:
            return self._display_surface.get_rect()
        return pygame.Rect(0, 0, self._config.width, self._config.height)

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
        """The main display surface. Only valid after ``run()`` is called."""
        if self._display_surface is None:
            raise RuntimeError(
                "display_surface is not available before Application.run() is called."
            )
        return self._display_surface

    @property
    def clock(self) -> pygame.time.Clock:
        """The master clock. Only valid after ``run()`` is called."""
        if self._clock is None:
            raise RuntimeError(
                "clock is not available before Application.run() is called."
            )
        return self._clock
