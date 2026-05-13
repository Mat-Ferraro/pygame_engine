"""
Development entry point for pygame_engine.

Uncomment the example you want to run, or use run_examples.py
for an interactive launcher that lists all available examples.

Not intended as the entry point for games built on top of the engine.

Run from the repo root:
    python main.py
"""

from examples.example_particles import run

# ── Uncomment one example to run it ──────────────────────────────────────────

# Core
#from examples.example_app               import run
#from examples.example_scene             import run
#from examples.example_transitions       import run

# UI
#from examples.example_buttons           import run
#from examples.example_widgets           import run
#from examples.example_feedback          import run
#from examples.example_scrollable        import run
#from examples.example_layout            import run
#from examples.example_responsive_layout import run

# Visuals
#from examples.example_animation         import run
#from examples.example_theme_richtext    import run

# Game systems
#from examples.example_camera            import run
#from examples.example_tilemap           import run
#from examples.example_dialogue          import run
#from examples.example_platformer        import run

# Assets & data
#from examples.example_atlas_locale      import run
#from examples.example_persistence       import run

# Input & audio
#from examples.example_input             import run
#from examples.example_audio             import run

# Debug
#from examples.example_debug             import run

# ─────────────────────────────────────────────────────────────────────────────

run()
