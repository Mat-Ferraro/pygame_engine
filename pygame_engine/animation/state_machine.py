"""
Animation state machine for pygame_engine.

Manages transitions between named animation states based on conditions.
Sits on top of AnimationPlayer to eliminate per-entity if/else boilerplate.

Usage::

    from pygame_engine.animation.state_machine import AnimationStateMachine

    sm = AnimationStateMachine(player)     # player is an AnimationPlayer

    sm.add_state("idle",   default=True)
    sm.add_state("run")
    sm.add_state("jump")
    sm.add_state("fall")

    sm.add_transition("idle",  "run",  condition=lambda p: abs(p["vx"]) > 10)
    sm.add_transition("run",   "idle", condition=lambda p: abs(p["vx"]) <= 10)
    sm.add_transition("idle",  "jump", condition=lambda p: p["jumping"])
    sm.add_transition("run",   "jump", condition=lambda p: p["jumping"])
    sm.add_transition("jump",  "fall", condition=lambda p: p["vy"] > 0)
    sm.add_transition("fall",  "idle", condition=lambda p: p["on_ground"])

    # Each frame, pass a params dict:
    sm.update(dt, params={"vx": player.vx, "vy": player.vy,
                           "jumping": player.jumping,
                           "on_ground": player.on_ground})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from pygame_engine.animation.animator import AnimationPlayer


@dataclass
class _Transition:
    from_state: str
    to_state:   str
    condition:  Callable[[dict], bool]
    priority:   int = 0   # higher = checked first among transitions from same state


class AnimationStateMachine:
    """
    Manages transitions between animation states.

    Each state maps to a named animation in the attached ``AnimationPlayer``.
    Transitions fire automatically when their condition evaluates True.

    Args:
        player: The ``AnimationPlayer`` to drive.
    """

    def __init__(self, player: AnimationPlayer) -> None:
        self._player:        AnimationPlayer          = player
        self._states:        dict[str, bool]          = {}   # name → is_default
        self._transitions:   list[_Transition]        = []
        self._current:       str | None               = None
        self._default:       str | None               = None
        self._on_enter_cbs:  dict[str, Callable]      = {}
        self._on_exit_cbs:   dict[str, Callable]      = {}

    # ── Building the machine ──────────────────────────────────────────────────

    def add_state(
        self,
        name:     str,
        default:  bool = False,
        on_enter: Callable[[], None] | None = None,
        on_exit:  Callable[[], None] | None = None,
    ) -> "AnimationStateMachine":
        """
        Register a state.

        Args:
            name:     State name. Must match an animation registered in
                      the AnimationPlayer.
            default:  If True, this state is entered on the first
                      ``update()`` call. Only one state may be default.
            on_enter: Optional callback fired when entering this state.
            on_exit:  Optional callback fired when leaving this state.

        Returns:
            self — for chaining.
        """
        self._states[name] = default
        if default:
            self._default = name
        if on_enter:
            self._on_enter_cbs[name] = on_enter
        if on_exit:
            self._on_exit_cbs[name] = on_exit
        return self

    def add_transition(
        self,
        from_state: str,
        to_state:   str,
        condition:  Callable[[dict], bool],
        priority:   int = 0,
    ) -> "AnimationStateMachine":
        """
        Add a transition between two states.

        Args:
            from_state: State to transition from. Use ``"*"`` to match
                        any current state (any-state transition).
            to_state:   State to transition into.
            condition:  ``lambda params: bool`` — evaluated each frame.
                        ``params`` is the dict passed to ``update()``.
            priority:   Higher priority transitions are checked first.
                        Default 0.

        Returns:
            self — for chaining.
        """
        self._transitions.append(
            _Transition(from_state, to_state, condition, priority)
        )
        return self

    # ── Runtime ───────────────────────────────────────────────────────────────

    def update(self, dt: float, params: dict | None = None) -> None:
        """
        Evaluate transitions and advance the current animation.

        Args:
            dt:     Delta-time from the frame loop.
            params: Arbitrary dict of game state values passed to
                    transition conditions. Can be any structure your
                    conditions expect.
        """
        p = params or {}

        # Initialise to default on first update
        if self._current is None:
            self._enter(self._default or (next(iter(self._states), None)))

        if self._current is None:
            return

        # Check transitions ordered by priority (highest first)
        candidates = [
            t for t in self._transitions
            if (t.from_state == self._current or t.from_state == "*")
            and t.to_state != self._current
        ]
        candidates.sort(key=lambda t: t.priority, reverse=True)

        for transition in candidates:
            try:
                if transition.condition(p):
                    self._enter(transition.to_state)
                    break
            except Exception:
                pass   # bad condition — skip silently

        self._player.update(dt)

    def force(self, state: str) -> None:
        """
        Immediately enter a state, bypassing transition conditions.

        Args:
            state: The state name to enter.

        Raises:
            KeyError: If the state is not registered.
        """
        if state not in self._states:
            raise KeyError(f"State {state!r} not registered.")
        self._enter(state)

    # ── Query ─────────────────────────────────────────────────────────────────

    @property
    def current_state(self) -> str | None:
        """Name of the currently active state."""
        return self._current

    @property
    def player(self) -> AnimationPlayer:
        """The AnimationPlayer being driven."""
        return self._player

    def is_in(self, state: str) -> bool:
        """Return True if the machine is currently in ``state``."""
        return self._current == state

    # ── Internal ──────────────────────────────────────────────────────────────

    def _enter(self, state: str | None) -> None:
        if state is None:
            return
        if state == self._current:
            return

        # Fire exit callback for old state
        if self._current and self._current in self._on_exit_cbs:
            try:
                self._on_exit_cbs[self._current]()
            except Exception:
                pass

        self._current = state
        self._player.play(state)

        # Fire enter callback for new state
        if state in self._on_enter_cbs:
            try:
                self._on_enter_cbs[state]()
            except Exception:
                pass

    def __repr__(self) -> str:
        return (f"AnimationStateMachine("
                f"state={self._current!r}, "
                f"states={list(self._states.keys())})")
