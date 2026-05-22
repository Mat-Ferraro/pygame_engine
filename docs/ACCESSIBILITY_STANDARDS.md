# pygame_engine — Accessibility Standards

**Version:** 2.0-design
**Authority:** Supplements ARCHITECTURE.md

This document defines the accessibility requirements for pygame_engine
and all games built with it. Accessibility is not a feature added after
the fact — it is a property of decisions made during design and
implementation.

---

## 1. Why This Matters

Players who cannot use a mouse rely on keyboard navigation. Players
with colour vision deficiency rely on more than colour to understand
UI state. Players with vestibular disorders are affected by motion.

These are not edge cases. Roughly 8% of men have some form of colour
vision deficiency. Keyboard-only navigation is used by players with
motor disabilities, players using controllers, and players who simply
prefer the keyboard.

Making a game accessible costs little when done from the start.
Retrofitting it costs significantly more.

---

## 2. Keyboard Navigation

### Every Interactive Widget Must Support Keyboard

If a widget responds to mouse clicks, it must respond to keyboard
activation. The standard keyboard interactions are:

| Widget | Keyboard activation |
|---|---|
| Button | Space or Enter when focused |
| Checkbox | Space when focused |
| Slider | Left/Right arrow keys when focused |
| Dropdown | Enter to open, arrows to navigate, Enter to select, Escape to close |
| RadioGroup | Arrow keys to change selection |
| InputField | Type to enter, Enter to submit, Escape to cancel |
| ListView | Arrow keys to navigate, Enter to select |
| TabBar | Arrow keys to move between tabs |

Widgets that are display-only (Label, Badge, ProgressBar) do not need
keyboard interaction — they are not interactive.

### Tab Order

Tab moves focus forward through interactive widgets. Shift+Tab moves
backward. Focus wraps — tabbing past the last widget returns to the first.

Tab order follows the `tab_index` property if set, otherwise the child
list order. Child list order is the natural reading order (left to right,
top to bottom) — use it. Only set `tab_index` explicitly when the natural
order is wrong for keyboard navigation.

### Focus Trapping

Modal dialogs must trap focus. A `ConfirmDialog` on screen means Tab
must cycle through the dialog's buttons — never to the scene behind it.

Set `focus_trap = True` on any container that should trap focus:

```python
class ConfirmDialog(Scene):
    def __init__(self, ...):
        self._container = Panel(rect, focus_trap=True)
```

The `FocusManager` enforces trapping automatically.

### Focus Indicators

The focus ring is drawn by `FocusManager` as a post-render pass.

**Never draw your own focus indicator.** Individual widgets must not
draw their own focus state. This creates inconsistency — some widgets
have one style of focus ring, others have another, and some have none.
The `FocusManager` draws a consistent ring for all focused widgets.

The focus ring colour and width are configurable through the theme.

---

## 3. Colour

### Colour Alone Must Never Convey Information

If the only difference between "success" and "failure" is green vs red,
a player with deuteranopia (the most common colour deficiency, affecting
~5% of men) cannot tell the difference.

Every use of colour to convey meaning must be accompanied by text,
icon, pattern, or position:

```python
# Wrong — colour is the only signal
Badge(rect, "Hired", colour=GREEN)
Badge(rect, "Unavailable", colour=RED)

# Correct — text reinforces the colour
Badge(rect, "✓ Hired", style="good")        # green + checkmark
Badge(rect, "✗ Unavailable", style="danger") # red + X
```

### WCAG AA Contrast Ratio

Text must have a contrast ratio of at least **4.5:1** against its
background for normal text, and **3:1** for large text (18pt+ or
14pt+ bold).

The desk/parchment palette in `desk_theme.py` has been designed to
meet these ratios. When adding new colour pairs, verify contrast
using any WCAG contrast checker before committing.

```
PARCH_TEXT  (210, 185, 135) on PARCH_BG (42, 38, 30) → ~5.2:1  ✓
PARCH_MUTED (130, 110, 80)  on PARCH_BG (42, 38, 30) → ~3.1:1  ✓ (large text)
PARCH_MUTED (130, 110, 80)  on PARCH_BG (42, 38, 30) → 3.1:1   ✗ (normal text)
```

### Colour-Blind Modes

The theme system supports alternative colour palettes. Games provide
one or more colour-blind friendly palettes. Players select them in
settings. The engine does not dictate the palette content — it provides
the theme-switching mechanism.

Name palettes descriptively, not by deficiency type:
```python
# Correct
"High Contrast"
"Deuteranopia Friendly"  # acceptable — this is the technical term

# Wrong — medical labels without context
"Colour Blind Mode"
```

---

## 4. Motion

### Reduced Motion Must Be Respected

`app.reduced_motion` is a global flag settable by the player in settings
or read from the OS's accessibility preferences.

**Every animation and transition must check this flag.**

The engine checks it at the primitive level — `Tween`, transitions, and
the scene editor animations all respect it. Game code must check it for
any animations it controls directly:

```python
def update(self, dt: float) -> None:
    if not self._app.reduced_motion:
        # Animate the wood grain phase
        self._grain_phase += dt * 0.3
    # When reduced_motion is True, _grain_phase stays at 0.0
    # and the background is static
```

**What reduced motion means for each animation type:**

| Animation | Reduced motion behaviour |
|---|---|
| Scene transitions (Fade, Slide, Crossfade) | Instant cut — no animation |
| Tweens | Complete instantly at the end value |
| Particle systems | Disabled — no particles emitted |
| Background animations (wood grain, patterns) | Static — no movement |
| Tab bar highlights | Static — no pulse animation |
| Loading indicators | Simple text "Loading..." instead of animation |

The engine handles transitions automatically. Tweens check `app.reduced_motion`
before advancing. Games are responsible for background animations and
particle systems in their own scenes.

---

## 5. Widget Requirements

### widget_id Is Required for Editor and Accessibility Support

Any widget that needs editor support or that should be navigable by
future screen reader integration must have `widget_id` set:

```python
# Required for any widget the editor should know about
self._hire_button = Button(rect, "Hire Hero", on_click=self._hire)
self._hire_button.widget_id = "hire_button"

# For a list of dynamically created widgets, generate stable ids
for i, hero in enumerate(roster):
    row = HeroRow(hero)
    row.widget_id = f"hero_row_{hero.id}"  # stable across session
```

`widget_id` must be stable — the same widget always gets the same id.
Do not use loop indices (`f"row_{i}"`) if items can be reordered.
Use the item's own stable identifier.

### Labels Are Required for Icon-Only Widgets

If a widget is icon-only with no visible text, it must still have a
descriptive label accessible to the focus system:

```python
Button(rect, icon=CLOSE_ICON, on_click=self._close)
# Wrong — no accessible label

Button(rect, icon=CLOSE_ICON, label="Close dialog", on_click=self._close)
# Correct — label is used by focus ring and will be used by screen readers
```

---

## 6. Text

### Minimum Font Size

Normal text: 16px minimum.
Small text (badges, captions, footnotes): 14px minimum.
Never render text below 12px regardless of context — it becomes
unreadable for players with low vision.

The `SysFont(None, size)` calls in our scenes use size values of 19-26px.
These are within the acceptable range.

### Text Scaling

The theme system provides a `text_scale` multiplier. Games that set
`AppConfig.text_scale` apply it to all text rendering. Players who
need larger text set this in settings.

Widget authors must multiply their font sizes by the theme's text
scale factor rather than hardcoding sizes. The engine applies this
automatically to widgets that use the theme for font access.

---

## 7. Audio Accessibility

### No Audio-Only Information

Never use audio as the only way to convey game-critical information.
Players who have their volume off, players who are deaf, and players
in noisy environments cannot rely on audio signals.

Any audio signal that indicates something important must have a visual
counterpart:
- A "success" sound when hiring a hero → also show a visual confirmation
- A "warning" sound when approaching a deadline → also show a visual indicator
- Combat sounds → also show HP changes visually

### Volume Controls

Master, music, SFX, and UI volumes must be independently controllable.
Players who cannot hear music but can hear UI feedback should not be
forced to choose between them.

The AudioManager bus topology (Section 3.9 of ARCHITECTURE.md) handles
this — games expose volume sliders for each bus in their settings scene.

---

## 8. Testing Accessibility

### Keyboard-Only Test

Before considering any interactive scene complete, navigate it entirely
without touching the mouse:
- Tab through all interactive elements
- Verify focus ring is visible at each stop
- Activate each widget with Space or Enter
- Verify all actions are reachable

If any action requires a mouse click, it is an accessibility violation.

### Colour Contrast Test

Use an OS-level colour picker or a browser contrast checker to verify
any new colour pair meets WCAG AA ratios before committing.

### Reduced Motion Test

Set `app.reduced_motion = True` before running the game. Verify:
- Scene transitions are instant cuts
- Background animations are static
- No animation that relied on movement is completely broken (static
  state must still be readable)

### Focus Trap Test

Open every modal dialog in the game. Verify Tab does not escape the
dialog to the content behind it.

---

## 9. Accessibility in the Editor

The editor itself must be accessible. Since the editor uses Dear ImGui,
which has its own accessibility support, most keyboard navigation is
provided automatically. Engine-specific requirements:

- The game viewport during play mode must be keyboard navigable
  (the game inside the viewport follows all the rules above)
- Editor panels must have Tab navigation between fields
- The hierarchy panel must be navigable by keyboard
- All editor actions must be available without a mouse

The editor is a developer tool — not shipped to players — but the
developers using it deserve accessible tooling.
