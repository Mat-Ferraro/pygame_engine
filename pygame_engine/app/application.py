"""
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

import bisect
import traceback
from typing import Callable

import pygame

from pygame_engine.app.config import AppConfig
from pygame_engine.app.render_context import RenderContext
from pygame_engine.app.time_manager import TimeManager
from pygame_engine.assets.asset_loader import AssetLoader
from pygame_engine.audio.audio_manager import AudioManager
from pygame_engine.devtools.console import DebugConsole
from pygame_engine.devtools.gizmo_renderer import GizmoRenderer
from pygame_engine.devtools.overlay import DebugOverlay
from pygame_engine.events.event_bus import bus as _event_bus
from pygame_engine.input.input_manager import InputManager
from pygame_engine.scene.scene import Scene
from pygame_engine.scene.scene_manager import SceneManager
from pygame_engine.state.runtime_flags import flags as _runtime_flags
from pygame_engine.theme.defaults import Theme
from pygame_engine.theme.runtime import get_theme, set_theme
from pygame_engine.ui.global_focus import GlobalFocusManager

_HOOK_NAMES = frozenset({
    "startup", "shutdown",
    "pre_update", "post_update",
    "pre_render", "post_render",
})


class Application:
    """
    Runtime shell for a pygame_engine project.

    Owns pygame initialisation, the display surface, the master clock,
    and the scene manager. Drives the frame loop until stopped.

    Services (input, theme, audio, assets, debug, time, focus, gizmos)
    are created during startup and exposed as read-only properties.

    Extension hooks
    ---------------
    Optional modules attach behaviour without subclassing::

        app.add_hook("startup",    my_module.on_startup)
        app.add_hook("pre_update", my_module.tick, priority=10)

    Valid hook names: ``startup``, ``shutdown``, ``pre_update``,
    ``post_update``, ``pre_render``, ``post_render``.

    Higher ``priority`` runs **later**. Default priority is ``0``.

    Error handling
    --------------
    Three error tiers apply inside the frame loop:

    - **Developer errors** — wrong API usage. Raise immediately in all modes.
    - **Asset errors**     — missing/corrupt files. Emit ``engine.asset.error``
                             on the event bus and keep running.
    - **Runtime errors**   — scene ``update()``/``render()`` exceptions.
                             In ``development``: push ``ErrorScene`` and keep
                             the window open. In ``testing``: re-raise so
                             pytest can catch it. In ``production``: push
                             ``ErrorScene`` with a friendly message.

    Gizmos
    ------
    ``app.gizmos`` is a ``GizmoRenderer`` in development mode and ``None``
    in production. Scene code guards with::

        if app.gizmos:
            app.gizmos.draw_rect(player.rect, (0, 255, 0))
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self._config: AppConfig = config or AppConfig()

        self._display_surface: pygame.Surface | None = None
        self._clock:           pygame.time.Clock | None = None
        self._is_running:      bool = False

        self._scene_manager:  SceneManager       | None = None
        self._input_manager:  InputManager        | None = None
        self._assets:         AssetLoader         | None = None
        self._audio:          AudioManager        | None = None
        self._time_manager:   TimeManager         | None = None
        self._focus_manager:  GlobalFocusManager = GlobalFocusManager()

        # GizmoRenderer — only in development mode
        self._gizmos: GizmoRenderer | None = (
            GizmoRenderer() if self._config.mode == "development" else None
        )

        self._hooks: dict[str, list[tuple[int, int, Callable]]] = {
            name: [] for name in _HOOK_NAMES
        }
        self._hook_counter: int = 0

        self._debug_overlay: DebugOverlay = DebugOverlay()
        self._debug_console: DebugConsole = DebugConsole()

        # Track whether we are currently inside an error recovery push
        # to prevent infinite error-scene recursion
        self._in_error_recovery: bool = False

    # ── Hook registration ─────────────────────────────────────────────────────

    def add_hook(self, name: str, callback: Callable, priority: int = 0) -> None:
        """Register a callback on the named hook. Higher priority runs later."""
        if name not in _HOOK_NAMES:
            raise ValueError(f"Unknown hook {name!r}. Valid names: {sorted(_HOOK_NAMES)}")
        entry = (priority, self._hook_counter, callback)
        self._hook_counter += 1
        bisect.insort(self._hooks[name], entry)

    def remove_hook(self, name: str, callback: Callable) -> bool:
        """Remove a callback from the named hook. Returns True if found."""
        if name not in _HOOK_NAMES:
            raise ValueError(f"Unknown hook {name!r}. Valid names: {sorted(_HOOK_NAMES)}")
        bucket = self._hooks[name]
        for i, (_, _, cb) in enumerate(bucket):
            if cb is callback:
                del bucket[i]
                return True
        return False

    def _fire_hook(self, name: str, *args) -> None:
        for _, _, cb in self._hooks[name]:
            cb(*args)

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self, initial_scene: Scene) -> None:
        try:
            self._startup(initial_scene)
            self._loop()
        finally:
            self._shutdown()

    def stop(self) -> None:
        self._is_running = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _startup(self, initial_scene: Scene) -> None:
        pygame.init()

        self._display_surface = self._create_display()
        self._clock           = pygame.time.Clock()
        self._is_running      = True

        pygame.display.set_caption(self._config.title)

        self._input_manager = InputManager()
        self._assets = AssetLoader(
            self._config.asset_root,
            debug=(self._config.mode == "development"),
        )
        self._audio = AudioManager()
        self._time_manager = TimeManager(max_delta_time=self._config.max_dt)

        _runtime_flags.reset()
        if self._config.mode == "development":
            _runtime_flags.enable_debug_all()

        self._scene_manager = SceneManager()
        self._scene_manager.push(initial_scene)

        # Wire gizmo post-render hook in development mode
        if self._gizmos is not None:
            self.add_hook("post_render", self._render_gizmos, priority=50)

        self._fire_hook("startup")

    def _loop(self) -> None:
        """
        Frame order:
          1.  Poll events
          2.  Update input snapshot
          3.  Route events to scene flow
          4.  Advance TimeManager
          5.  Update AudioManager buses
          6.  pre_update hooks
          7.  Update scene flow  [error tier: runtime → ErrorScene]
          8.  post_update hooks
          9.  Clear back-buffer
          10. pre_render hooks
          11. Render scene flow  [error tier: runtime → ErrorScene]
          12. Render focus ring
          13. Render debug overlays
          14. post_render hooks  (includes GizmoRenderer)
          15. Flip / present display
        """
        while self._is_running:

            events = pygame.event.get()

            if self._input_manager is not None:
                self._input_manager.update(events)

            for event in events:
                self._handle_event(event)

            assert self._clock is not None
            raw_ms = self._clock.tick(self._config.target_fps)
            raw_dt = raw_ms / 1000.0
            if self._time_manager is not None:
                self._time_manager.advance(raw_dt)
                dt = self._time_manager.delta_time
            else:
                dt = self._compute_dt(raw_ms)

            # Propagate time-scale pause policy to audio buses
            if self._audio is not None and self._time_manager is not None:
                self._audio.update(self._time_manager.time_scale.value)

            self._fire_hook("pre_update", dt)

            if self._scene_manager is not None:
                self._safe_update(self._scene_manager, dt)

            self._fire_hook("post_update", dt)

            assert self._display_surface is not None
            self._display_surface.fill((0, 0, 0))

            self._fire_hook("pre_render", self._display_surface)

            if self._scene_manager is not None:
                ctx = RenderContext(theme=get_theme())
                self._safe_render(self._scene_manager, self._display_surface, ctx)

            # Focus ring — drawn after scene, before debug overlays
            self._focus_manager.render_focus_ring(self._display_surface)

            self._debug_overlay.render(
                self._display_surface, self._clock, self._scene_manager,
            )
            self._debug_console.render(self._display_surface)

            self._fire_hook("post_render", self._display_surface)

            pygame.display.flip()

    def _safe_update(self, scene_manager: SceneManager, dt: float) -> None:
        """Update the scene stack; push ErrorScene on runtime error."""
        try:
            scene_manager.update(dt)
        except Exception as exc:
            self._handle_runtime_error(exc, "update")

    def _safe_render(
        self,
        scene_manager: SceneManager,
        surface: pygame.Surface,
        ctx: RenderContext,
    ) -> None:
        """Render the scene stack; push ErrorScene on runtime error."""
        try:
            scene_manager.render(surface, ctx)
        except Exception as exc:
            self._handle_runtime_error(exc, "render")

    def _handle_runtime_error(self, exc: Exception, phase: str) -> None:
        """
        Apply the three-tier error policy for runtime scene errors.

        - testing: re-raise immediately so pytest catches it.
        - development / production: push ErrorScene.
        """
        from pygame_engine.devtools.debug_log import error as _log_error
        _log_error(
            f"Runtime error in scene {phase}(): {type(exc).__name__}: {exc}",
            tag="engine",
        )
        _event_bus.emit(
            "engine.scene.error",
            exc=exc,
            phase=phase,
            tb="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        )

        if self._config.mode == "testing":
            raise exc

        # Prevent infinite recursion if ErrorScene itself raises
        if self._in_error_recovery:
            self._is_running = False
            return

        self._in_error_recovery = True
        try:
            error_cls = self._config.error_scene_class
            if error_cls is None:
                from pygame_engine.scene.error_scene import ErrorScene
                error_cls = ErrorScene

            if self._scene_manager is not None:
                error_scene = error_cls(exc, self._config.mode)
                self._scene_manager.push(error_scene)
        finally:
            self._in_error_recovery = False

    def _render_gizmos(self, surface: pygame.Surface) -> None:
        """post_render hook that flushes the GizmoRenderer queue."""
        if self._gizmos is not None:
            self._gizmos.render(surface)

    def _shutdown(self) -> None:
        self._fire_hook("shutdown")

        if self._scene_manager is not None:
            while not self._scene_manager.is_empty:
                self._scene_manager.pop()

        if self._audio is not None:
            self._audio.shutdown()

        _event_bus.clear_all()
        pygame.quit()

    # ── Event routing ─────────────────────────────────────────────────────────

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.stop()
            return

        if event.type == pygame.VIDEORESIZE and self._config.resizable:
            self._on_resize(event.w, event.h)
            return

        if self._scene_manager is not None:
            if self._scene_manager.handle_event(event):
                return

        if self._input_manager is not None:
            from pygame_engine.input import actions as _actions
            from pygame_engine.state.runtime_flags import flags as _flags
            if self._input_manager.was_action_pressed(_actions.DEBUG_TOGGLE):
                _flags.toggle("show_overlay")
                return
            if self._input_manager.was_action_pressed(_actions.INSPECTOR_TOGGLE):
                from pygame_engine.devtools.inspector import Inspector
                Inspector().dump(self._scene_manager)
                return
            if self._input_manager.was_action_pressed(_actions.CONSOLE_TOGGLE):
                _flags.toggle("show_console")
                return

    # ── Display helpers ───────────────────────────────────────────────────────

    def _create_display(self) -> pygame.Surface:
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
        self._display_surface = pygame.display.set_mode(
            (width, height), pygame.RESIZABLE,
            vsync=1 if self._config.vsync else 0,
        )
        from pygame_engine.events import bus as _bus
        _bus.emit("window.resized", width=width, height=height)
        if self._scene_manager is not None:
            self._scene_manager.notify_resize(width, height)

    @property
    def screen_rect(self) -> pygame.Rect:
        if self._display_surface is not None:
            return self._display_surface.get_rect()
        return pygame.Rect(0, 0, self._config.width, self._config.height)

    def _compute_dt(self, raw_ms: int) -> float:
        dt = raw_ms / 1000.0
        if self._config.max_dt > 0:
            dt = min(dt, self._config.max_dt)
        return dt

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def gizmos(self) -> GizmoRenderer | None:
        """
        The active GizmoRenderer, or None in production mode.

        Always guard before use::

            if app.gizmos:
                app.gizmos.draw_rect(rect, (0, 255, 0))
        """
        return self._gizmos

    @property
    def focus(self) -> GlobalFocusManager:
        """The global focus manager. Available before ``run()``."""
        return self._focus_manager

    @property
    def time(self) -> TimeManager:
        """The TimeManager. Only valid after ``run()`` is called."""
        if self._time_manager is None:
            raise RuntimeError(
                "time is not available before Application.run() is called."
            )
        return self._time_manager

    @property
    def scene_manager(self) -> SceneManager:
        if self._scene_manager is None:
            raise RuntimeError(
                "scene_manager is not available before Application.run() is called."
            )
        return self._scene_manager

    @property
    def audio(self) -> AudioManager:
        if self._audio is None:
            raise RuntimeError(
                "audio is not available before Application.run() is called."
            )
        return self._audio

    @property
    def assets(self) -> AssetLoader:
        if self._assets is None:
            raise RuntimeError(
                "assets is not available before Application.run() is called."
            )
        return self._assets

    @property
    def theme(self) -> Theme:
        return get_theme()

    def set_theme(self, theme: Theme) -> None:
        set_theme(theme)

    @property
    def input_manager(self) -> InputManager:
        if self._input_manager is None:
            raise RuntimeError(
                "input_manager is not available before Application.run() is called."
            )
        return self._input_manager

    @property
    def mode(self) -> str:
        return self._config.mode

    @property
    def reduced_motion(self) -> bool:
        return self._config.reduced_motion

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def display_surface(self) -> pygame.Surface:
        if self._display_surface is None:
            raise RuntimeError(
                "display_surface is not available before Application.run() is called."
            )
        return self._display_surface

    @property
    def clock(self) -> pygame.time.Clock:
        if self._clock is None:
            raise RuntimeError(
                "clock is not available before Application.run() is called."
            )
        return self._clock