"""
pygame_engine.events

Pub/sub event bus for loose coupling between game systems.

Public API::

    from pygame_engine.events import bus
    from pygame_engine.events import EventBus

    # Subscribe
    bus.on("player.damaged", on_player_damaged)
    bus.once("scene.entered", on_first_enter)

    # Emit
    bus.emit("player.damaged", amount=30, source="enemy")

    # Unsubscribe
    bus.off("player.damaged", on_player_damaged)
"""

from pygame_engine.events.event_bus import EventBus, bus

__all__ = ["EventBus", "bus"]
