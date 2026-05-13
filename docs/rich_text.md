# Rich Text

## Purpose

`RichLabel` renders single-line text with inline BBCode-style markup —
bold, italic, colour, and size changes within a single text string.

---

## Quick start

```python
from pygame_engine.ui.text.rich_label import RichLabel

lbl = RichLabel(
    rect=pygame.Rect(100, 200, 400, 32),
    text="Collect [color=#ffd700][b]{count} coins[/b][/color] to win!",
)
lbl.text = lbl.text.format(count=42)

# In render:
lbl.render(surface)
```

---

## Supported tags

| Tag | Example | Effect |
|---|---|---|
| `[b]...[/b]` | `[b]bold[/b]` | Bold weight |
| `[i]...[/i]` | `[i]italic[/i]` | Italic style |
| `[color=#rrggbb]...[/color]` | `[color=#ff4444]red[/color]` | Colour (hex) |
| `[size=N]...[/size]` | `[size=24]big[/size]` | Font size override |

Tags may be freely nested:

```python
"[b][color=#ffd700]golden bold[/color][/b]"
"[i][size=14]small italic[/size][/i] normal"
```

Unknown or malformed tags are rendered as literal text — they never crash.

---

## API

```python
lbl = RichLabel(
    rect=pygame.Rect(x, y, w, h),
    text="[b]Hello[/b] world",
    font_size=18,           # base size (default: theme.typography.md)
    colour=(220, 220, 232), # base colour (default: theme.colours.text)
    align="left",           # "left", "center", "right"
    font_name="segoeui",    # SysFont hint (default: theme.typography.family)
)

lbl.text  = "Updated [b]text[/b]"
lbl.align = "center"
lbl.render(surface)
```

---

## Patterns

### Dialogue with speaker name

```python
box_text = f"[b]{speaker}:[/b] {dialogue_text}"
lbl = RichLabel(rect, box_text)
```

### Item tooltip

```python
tooltip_text = (
    f"[b]{item.name}[/b]\n"   # Note: RichLabel is single-line
    f"[color=#aaaaff]{item.rarity}[/color]  "
    f"[color=#88ff88]+{item.stat} ATK[/color]"
)
```

### HUD with colour-coded values

```python
hp_text = (
    f"HP: [color={'#88ff88' if hp > 50 else '#ff4444'}]{hp}[/color]/{max_hp}"
)
```

---

## Notes

`RichLabel` is single-line. For multi-line rich text, stack multiple
`RichLabel` instances or use `TextBlock` for plain wrapped text.

Font variants (bold, italic, size combinations) are cached per `RichLabel`
instance — no font is recreated between frames unless text changes.
