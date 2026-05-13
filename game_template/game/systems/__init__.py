"""
game/systems/

Game-specific systems and managers.

This is where your gameplay logic lives — entities, world management,
combat, inventory, progression, etc. These are NOT engine concerns.

Suggested structure as your game grows:

    game/systems/
    ├── __init__.py          ← this file
    ├── world.py             ← world/level management, entity lists
    ├── player.py            ← player entity, input → movement
    ├── enemy.py             ← enemy entity, AI, pathfinding usage
    ├── combat.py            ← damage, hit detection, death
    └── spawner.py           ← entity spawning, waves

Example player system using engine primitives::

    from pygame_engine.animation import AnimationStateMachine
    from pygame_engine.pathfinding import Pathfinder

    class Player:
        def __init__(self, x, y, animator):
            self.rect = pygame.Rect(x, y, 24, 32)
            self.vx = self.vy = 0.0
            self.on_ground = False
            self.hp = 100

            self.sm = AnimationStateMachine(animator)
            self.sm.add_state("idle", default=True)
            self.sm.add_state("run")
            self.sm.add_state("jump")
            self.sm.add_transition("idle", "run",  lambda p: abs(p["vx"]) > 10)
            self.sm.add_transition("run",  "idle", lambda p: abs(p["vx"]) <= 10)
            self.sm.add_transition("*",    "jump", lambda p: p["jumping"])
            self.sm.add_transition("jump", "idle", lambda p: p["on_ground"])

        def update(self, dt, tmap, input_manager):
            # movement, collision, state machine update
            self.sm.update(dt, params={
                "vx": self.vx,
                "jumping": False,
                "on_ground": self.on_ground,
            })

Example enemy using pathfinding::

    class Enemy:
        def __init__(self, x, y, finder, tmap):
            self.rect   = pygame.Rect(x, y, 20, 20)
            self._finder = finder
            self._tmap   = tmap
            self._path: list = []

        def set_target(self, goal_world_pos):
            start = self._tmap.world_to_tile(*self.rect.center)
            goal  = self._tmap.world_to_tile(*goal_world_pos)
            self._path = self._finder.find(start, goal)

        def update(self, dt):
            if self._path:
                # move toward next waypoint
                pass
"""
