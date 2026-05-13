"""
game/models/

Domain objects — the core data structures your game works with.

Examples of what belongs here:
- Player (position, health, inventory, stats)
- Enemy (type, AI state, health)
- World / Map (tiles, entities, rooms)
- Item (name, type, stats)
- Quest / Mission

Rules:
- Models are plain Python classes — no pygame, no engine imports
- Models hold data and define domain behaviour
- They do NOT know about rendering, input, or scenes
- Keep them serialisable (use dataclasses where possible)

Example::

    from dataclasses import dataclass, field

    @dataclass
    class Player:
        x: float = 0.0
        y: float = 0.0
        health: int = 100
        max_health: int = 100
        gold: int = 0

        @property
        def is_alive(self) -> bool:
            return self.health > 0

        def take_damage(self, amount: int) -> None:
            self.health = max(0, self.health - amount)
"""
