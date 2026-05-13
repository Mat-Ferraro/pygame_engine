"""
game/systems/

Gameplay systems — logic that operates on models each frame.

Examples of what belongs here:
- MovementSystem   — applies velocity to positions
- CollisionSystem  — detects and resolves collisions
- CombatSystem     — resolves attack/damage calculations
- AISystem         — updates enemy behaviour
- SpawnSystem      — manages entity spawning
- QuestSystem      — tracks and evaluates quest progress

Rules:
- Systems receive models as input and mutate them
- Systems may read engine services (timers, input) but don't own them
- Keep systems focused — one responsibility per system
- Systems are called from GameScene.update(dt)

Example::

    class MovementSystem:
        def update(self, player: Player, dt: float,
                   input_manager) -> None:
            speed = 200.0   # pixels per second
            inp = input_manager
            if inp.is_action_down(actions.NAV_LEFT):
                player.x -= speed * dt
            if inp.is_action_down(actions.NAV_RIGHT):
                player.x += speed * dt
"""
