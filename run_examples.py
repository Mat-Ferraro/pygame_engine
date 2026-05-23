"""
Lists all available examples with descriptions and lets you pick one
to run. Supports number selection, partial name matching, and
command-line arguments.

Usage:
    python run_examples.py           # interactive menu
    python run_examples.py 3         # run example #3 directly
    python run_examples.py audio     # partial name match
    python run_examples.py --list    # print list and exit

Not intended for use in games built on top of the engine.
"""

import importlib
import sys


# ── Example registry ──────────────────────────────────────────────────────────
# (module_name, one-line description, category)

EXAMPLES: list[tuple[str, str, str]] = [
    # Core
    ("example_observable",        "Observable: weak refs, transactions, SubscriptionGroup", "Core"),
    ("example_app",               "Application spine, Tween, animated widget, Timer",        "Core"),
    ("example_scene",             "Scene push / pop / replace, overlay blocking flags",       "Core"),
    ("example_transitions",       "Fade, Slide (4 dirs), Crossfade between scenes",           "Core"),
    ("example_time_manager",      "TimeManager: pause, slow-mo, fast-forward, fixed-step",   "Core"),
    ("example_hooks",             "Extension hooks: attach modules without subclassing",      "Core"),
    # UI
    ("example_buttons",           "Panel, Button, Label, disabled state",                     "UI"),
    ("example_widgets",           "Slider, Checkbox, RadioGroup, Dropdown",                   "UI"),
    ("example_feedback",          "Toast notifications, Tooltip on hover",                    "UI"),
    ("example_scrollable",        "Scrollable container, TextBlock wrapping",                 "UI"),
    ("example_layout",            "anchor, row, column, grid helpers",                        "UI"),
    ("example_responsive_layout", "FlexRow, FlexColumn, AnchorLayout on resize",              "UI"),
    ("example_focus",             "GlobalFocusManager: tab_index, focus_trap, focus ring",   "UI"),
    # Visuals
    ("example_particles",         "All 6 particle presets — click to spawn",                  "Visuals"),
    ("example_animation",         "Tween easings, AnimationPlayer, AnimationStateMachine",    "Visuals"),
    ("example_theme_richtext",    "JSON theme file loading, hot-reload, RichLabel markup",    "Visuals"),
    # Game systems
    ("example_camera",            "Camera follow, zoom, shake, world bounds, culling",        "Game"),
    ("example_tilemap",           "Tileset, TileLayer, Tilemap collision queries",            "Game"),
    ("example_dialogue",          "DialogueScript, DialogueRunner, typewriter box",           "Game"),
    ("example_platformer",        "2D platformer: A* enemies, lighting, positional audio, state machine", "Game"),
    # Assets & data
    ("example_atlas_locale",      "SpriteAtlas packing, LocaleStore key lookup",              "Assets"),
    ("example_persistence",       "SaveManager save / load / delete / list slots",            "Assets"),
    # Input & audio
    ("example_input",             "Key remapping, controller detection, binding reset",       "Input"),
    ("example_audio",             "AudioManager buses, volume, mute, SFX routing",           "Input"),
    # Debug
    ("example_debug",             "debug_log, RuntimeFlags, DebugOverlay (F1/F2/F3)",        "Debug"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_menu() -> None:
    current_cat = ""
    print()
    print("  pygame_engine — example launcher")
    print("  " + "─" * 62)
    for i, (name, desc, cat) in enumerate(EXAMPLES, start=1):
        if cat != current_cat:
            current_cat = cat
            print(f"\n  ── {cat} {'─' * (56 - len(cat))}")
        short = name.replace("example_", "")
        print(f"  {i:2d}.  {short:<28}  {desc}")
    print()
    print("  ── Commands " + "─" * 50)
    print("  q / 0 / exit   — quit")
    print("  <name>         — partial name match  (e.g. 'audio', 'trans')")
    print("  " + "─" * 62)
    print()


def _matches(query: str) -> list[int]:
    q = query.lower().replace("-", "_").replace("example_", "")
    return [i for i, (name, _, _) in enumerate(EXAMPLES)
            if q in name.replace("example_", "")]


def _run(idx: int) -> None:
    name, desc, _ = EXAMPLES[idx]
    print(f"\n  → {name}")
    print(f"    {desc}\n")
    mod = importlib.import_module(f"examples.{name}")
    mod.run()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    # ── Command-line mode ────────────────────────────────────────────────────
    args = sys.argv[1:]

    if "--list" in args or "-l" in args:
        _print_menu()
        return

    if args:
        arg = args[0]
        try:
            n = int(arg)
            if 1 <= n <= len(EXAMPLES):
                _run(n - 1)
                return
            print(f"  Number out of range: {n}")
            sys.exit(1)
        except ValueError:
            pass
        hits = _matches(arg)
        if len(hits) == 1:
            _run(hits[0])
            return
        if len(hits) > 1:
            print(f"  Multiple matches for {arg!r}:")
            for i in hits:
                print(f"    {i+1:2d}. {EXAMPLES[i][0]}")
            sys.exit(1)
        print(f"  No example matching {arg!r}")
        sys.exit(1)

    # ── Interactive menu ─────────────────────────────────────────────────────
    while True:
        _print_menu()
        try:
            choice = input("  Choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not choice:
            continue

        if choice in ("q", "0", "quit", "exit"):
            break

        try:
            n = int(choice)
            if 1 <= n <= len(EXAMPLES):
                _run(n - 1)
                continue
            print(f"\n  Please enter 1–{len(EXAMPLES)}.")
            continue
        except ValueError:
            pass

        hits = _matches(choice)
        if len(hits) == 1:
            _run(hits[0])
        elif len(hits) > 1:
            print(f"\n  Multiple matches:")
            for i in hits:
                print(f"    {i+1:2d}. {EXAMPLES[i][0]}")
        else:
            print(f"\n  No match for {choice!r}. Try a number or partial name.")


if __name__ == "__main__":
    main()
