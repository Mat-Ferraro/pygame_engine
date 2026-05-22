"""
SubscriptionGroup — tracks a set of Observable subscriptions and disposes
them all at once.

The primary use case is scenes. A scene subscribes to several observables
in ``on_enter``; when the scene exits, ``self.subscriptions.dispose()``
unsubscribes all of them in one call with no manual bookkeeping.

Usage::

    from pygame_engine.state import Observable
    from pygame_engine.state.subscription_group import SubscriptionGroup

    health  = Observable(100)
    stamina = Observable(50)

    group = SubscriptionGroup()
    group.on(health,  lambda old, new: hud.set_health(new))
    group.on(stamina, lambda old, new: hud.set_stamina(new))

    # Later — unsubscribe everything:
    group.dispose()

    # In a Scene subclass, this is automatic:
    class MyScene(Scene):
        def on_enter(self) -> None:
            self.subscriptions.on(health,  self._on_health_change)
            self.subscriptions.on(stamina, self._on_stamina_change)

        # on_exit is handled by Scene base — subscriptions.dispose() is called
        # automatically. No manual unsubscription needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pygame_engine.state.observable import Observable

# Token is the value returned by Observable.subscribe — the original callable.
# It is used to unsubscribe later. Treat it as opaque.
Token = Any


class SubscriptionGroup:
    """
    Collects Observable subscriptions and cancels them all on dispose.

    Scenes own one ``SubscriptionGroup`` as ``self.subscriptions``.
    The base ``Scene.on_exit()`` calls ``self.subscriptions.dispose()``
    automatically, so scenes never need to manually unsubscribe from
    observables they subscribed to in ``on_enter``.

    A ``SubscriptionGroup`` can also be used standalone — for any object
    that subscribes to observables and needs a clean teardown path.
    """

    def __init__(self) -> None:
        """Initialise an empty subscription group."""
        self._entries: list[tuple[Observable, Token]] = []

    # ── Primary interface ─────────────────────────────────────────────────────

    def on(self, observable: Observable, callback: Any) -> None:
        """
        Subscribe ``callback`` to ``observable`` and track the subscription.

        Equivalent to calling ``observable.subscribe(callback)`` and then
        ``group.add(observable, token)``.

        Args:
            observable: The ``Observable[T]`` to subscribe to.
            callback:   Callable that will receive ``(old_value, new_value)``
                        on each change.
        """
        token = observable.subscribe(callback)
        self._entries.append((observable, token))

    def add(self, observable: Observable, token: Token) -> None:
        """
        Track an existing subscription token without creating a new one.

        Use this when you called ``observable.subscribe()`` directly and
        want the group to manage unsubscription.

        Args:
            observable: The ``Observable[T]`` that was subscribed to.
            token:      The token returned by ``observable.subscribe()``.
        """
        self._entries.append((observable, token))

    def dispose(self) -> None:
        """
        Cancel all tracked subscriptions and clear the group.

        Safe to call more than once — subsequent calls are no-ops.
        After dispose, the group can be reused by calling ``on()`` or
        ``add()`` again.
        """
        for observable, token in self._entries:
            observable.unsubscribe(token)
        self._entries.clear()

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def subscription_count(self) -> int:
        """Number of active tracked subscriptions."""
        return len(self._entries)

    def __repr__(self) -> str:
        return f"SubscriptionGroup(subscriptions={self.subscription_count})"
