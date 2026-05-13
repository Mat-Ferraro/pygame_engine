"""
scene/transitions.py

Scene transition effects for pygame_engine.

Transitions are visual effects that play during a scene change. They
intercept rendering for their duration while the new scene is already
active and receiving updates and events normally.

Architecture
------------
A ``Transition`` captures a screenshot of the outgoing scene's last frame
and animates between it and the live incoming scene. While a transition
is active, ``SceneManager.render()`` delegates to the transition rather
than the scene stack.

All transitions are driven by ``Tween`` + easing functions and are
completely data-driven — no hardcoded frame counts or sleep calls.

Available transitions
---------------------
- ``FadeTransition``      — fade through a solid colour (default black)
- ``SlideTransition``     — slide the incoming scene in from an edge
- ``CrossfadeTransition`` — dissolve between outgoing and incoming scenes

Usage::

    from pygame_engine.scene.transitions import FadeTransition, SlideTransition
    from pygame_engine.animation.easing import ease_out_cubic

    # Replace current scene with a fade through black
    app.scene_manager.replace_with(
        GameplayScene(app),
        FadeTransition(duration=0.4),
    )

    # Push a pause menu sliding in from the top
    app.scene_manager.push_with(
        PauseScene(app),
        SlideTransition(duration=0.3, direction="down"),
    )

    # Pop back with a crossfade
    app.scene_manager.pop_with(
        CrossfadeTransition(duration=0.25),
    )
"""

from __future__ import annotations

from typing import Callable

import pygame

from pygame_engine.animation.easing import ease_in_out_cubic, linear
from pygame_engine.animation.tween import Tween


# ── Base Transition ───────────────────────────────────────────────────────────

class Transition:
    """
    Base class for scene transitions.

    A transition holds a capture of the outgoing scene's last frame and
    knows how to animate between it and the live incoming scene.

    Subclasses implement ``render()`` to define the visual effect.
    ``update(dt)`` drives the internal Tween and returns True when done.

    ``SceneManager`` owns the active transition and calls these methods
    each frame until ``is_done`` is True.
    """

    def __init__(
        self,
        duration: float,
        easing:   Callable[[float], float] = ease_in_out_cubic,
    ) -> None:
        """
        Args:
            duration: Transition duration in seconds.
            easing:   Easing function applied to the progress value.
        """
        self._duration = duration
        self._easing   = easing
        self._tween:    Tween | None          = None
        self._capture:  pygame.Surface | None = None   # outgoing scene frame

    def start(self, capture: pygame.Surface) -> None:
        """
        Start the transition with a screenshot of the outgoing scene.

        Called by SceneManager immediately after the scene change.

        Args:
            capture: A surface containing the last rendered frame of the
                     outgoing scene. The transition owns this surface.
        """
        self._capture = capture
        self._tween   = Tween(
            start=0.0, end=1.0,
            duration=self._duration,
            easing=self._easing,
            auto_start=True,
        )

    def update(self, dt: float) -> bool:
        """
        Advance the transition by one frame.

        Args:
            dt: Delta time in seconds.

        Returns:
            True when the transition is complete.
        """
        if self._tween is None:
            return True
        self._tween.update(dt)
        return self._tween.is_done

    @property
    def progress(self) -> float:
        """Eased progress from 0.0 (start) to 1.0 (done)."""
        if self._tween is None:
            return 1.0
        return self._tween.value

    @property
    def is_done(self) -> bool:
        """True when the transition has completed."""
        if self._tween is None:
            return True
        return self._tween.is_done

    def render(
        self,
        surface:       pygame.Surface,
        scene_surface: pygame.Surface,
    ) -> None:
        """
        Render the transition frame.

        Subclasses must implement this. Called by SceneManager each frame
        while the transition is active.

        Args:
            surface:       The display surface to draw onto.
            scene_surface: The current frame of the incoming (active) scene,
                           pre-rendered by SceneManager onto a temp surface.
        """
        raise NotImplementedError


# ── FadeTransition ────────────────────────────────────────────────────────────

class FadeTransition(Transition):
    """
    Fade through a solid colour (default black).

    Phase 1 (0.0 → 0.5): outgoing scene fades to the fade colour.
    Phase 2 (0.5 → 1.0): incoming scene fades in from the fade colour.

    This gives the classic "fade to black" effect used in most games.
    """

    def __init__(
        self,
        duration:   float                    = 0.4,
        fade_colour: tuple[int, int, int]    = (0, 0, 0),
        easing:     Callable[[float], float] = ease_in_out_cubic,
    ) -> None:
        """
        Args:
            duration:    Total transition duration in seconds.
            fade_colour: The colour to fade through (default black).
            easing:      Easing applied to each half of the transition.
        """
        super().__init__(duration, easing)
        self._fade_colour = fade_colour

    def render(
        self,
        surface:       pygame.Surface,
        scene_surface: pygame.Surface,
    ) -> None:
        p = self.progress   # 0.0 → 1.0

        if p < 0.5:
            # Phase 1: show outgoing, overlay fading to fade_colour
            if self._capture is not None:
                surface.blit(self._capture, (0, 0))
            overlay_alpha = int((p * 2.0) * 255)
        else:
            # Phase 2: show incoming, overlay fading from fade_colour
            surface.blit(scene_surface, (0, 0))
            overlay_alpha = int((1.0 - (p - 0.5) * 2.0) * 255)

        if overlay_alpha > 0:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((*self._fade_colour, overlay_alpha))
            surface.blit(overlay, (0, 0))


# ── SlideTransition ───────────────────────────────────────────────────────────

class SlideTransition(Transition):
    """
    Slide the incoming scene in from an edge while the outgoing scene
    slides out to the opposite edge.

    Directions: ``"left"``, ``"right"``, ``"up"``, ``"down"``.

    ``"right"`` means the new scene slides in from the right (typical
    forward navigation). ``"left"`` means it slides from the left
    (typical back navigation).
    """

    DIRECTIONS = {"left", "right", "up", "down"}

    def __init__(
        self,
        duration:  float                    = 0.35,
        direction: str                      = "right",
        easing:    Callable[[float], float] = ease_in_out_cubic,
    ) -> None:
        """
        Args:
            duration:  Transition duration in seconds.
            direction: Direction the new scene slides IN from.
                       ``"right"`` = new scene enters from right edge.
            easing:    Easing applied to the slide.
        """
        if direction not in self.DIRECTIONS:
            raise ValueError(
                f"Invalid direction {direction!r}. "
                f"Choose from: {sorted(self.DIRECTIONS)}"
            )
        super().__init__(duration, easing)
        self._direction = direction

    def render(
        self,
        surface:       pygame.Surface,
        scene_surface: pygame.Surface,
    ) -> None:
        p  = self.progress
        sw = surface.get_width()
        sh = surface.get_height()

        # Compute offset for the incoming scene
        if self._direction == "right":
            in_x  =  sw - int(sw * p)
            in_y  =  0
            out_x = -int(sw * p)
            out_y =  0
        elif self._direction == "left":
            in_x  = -sw + int(sw * p)
            in_y  =  0
            out_x =  int(sw * p)
            out_y =  0
        elif self._direction == "down":
            in_x  =  0
            in_y  =  sh - int(sh * p)
            out_x =  0
            out_y = -int(sh * p)
        else:  # "up"
            in_x  =  0
            in_y  = -sh + int(sh * p)
            out_x =  0
            out_y =  int(sh * p)

        # Draw outgoing scene at offset position
        if self._capture is not None:
            surface.blit(self._capture, (out_x, out_y))

        # Draw incoming scene sliding in
        surface.blit(scene_surface, (in_x, in_y))


# ── CrossfadeTransition ───────────────────────────────────────────────────────

class CrossfadeTransition(Transition):
    """
    Dissolve directly between the outgoing and incoming scenes.

    The outgoing scene fades out while the incoming scene fades in
    simultaneously. Simpler than FadeTransition — no solid colour phase.
    """

    def __init__(
        self,
        duration: float                    = 0.3,
        easing:   Callable[[float], float] = ease_in_out_cubic,
    ) -> None:
        super().__init__(duration, easing)

    def render(
        self,
        surface:       pygame.Surface,
        scene_surface: pygame.Surface,
    ) -> None:
        p = self.progress   # 0.0 → 1.0

        # Incoming scene at full size, fading in
        incoming_alpha = int(p * 255)
        temp = scene_surface.copy()
        temp.set_alpha(incoming_alpha)

        # Outgoing scene underneath
        if self._capture is not None:
            outgoing_alpha = int((1.0 - p) * 255)
            out = self._capture.copy()
            out.set_alpha(outgoing_alpha)
            surface.blit(out, (0, 0))

        surface.blit(temp, (0, 0))
