# Audio System

## Purpose

Provides runtime audio management for pygame_engine.

The audio system has two layers:

1. **Asset loading** (`assets/sounds.py`) — loads and caches
   ``pygame.mixer.Sound`` objects. Handled by ``AssetLoader``.
2. **Playback management** (`audio/audio_manager.py`) — controls what
   plays, at what volume, and when. Owned by ``Application``.

---

## AudioManager

Accessible via ``app.audio``. Handles:
- Background music streaming via ``pygame.mixer.music``
- Sound effect playback via ``pygame.mixer.Sound`` channels
- Master, music, and SFX volume controls
- Global mute toggle

### Music

One track plays at a time. Music is streamed from disk.

```python
app.audio.play_music(app.assets.asset_root / "music" / "theme.ogg")
app.audio.pause_music()
app.audio.resume_music()
app.audio.stop_music(fade_out_ms=500)
```

### Sound effects

```python
click_sound = app.assets.sound("click.wav")   # loaded once, cached

app.audio.play_sfx(click_sound)
app.audio.play_sfx(click_sound, volume=0.5)   # per-call volume multiplier
```

Passing ``None`` to ``play_sfx`` is a safe no-op — missing sounds from
``app.assets.sound()`` return ``None`` and produce no errors at playback.

### Volume

```python
app.audio.master_volume = 0.8    # scales all audio
app.audio.music_volume  = 0.6    # music-specific multiplier
app.audio.sfx_volume    = 1.0    # sfx-specific multiplier

app.audio.muted = True           # silence without losing settings
app.audio.toggle_mute()          # flip mute state
```

Effective music volume = ``master × music × (0 if muted)``.
Effective SFX volume   = ``master × sfx   × (0 if muted)``.

---

## Asset / Audio Boundary

The boundary is intentional:

| Layer           | Responsibility                                      |
|-----------------|-----------------------------------------------------|
| `assets/sounds` | Loading sound files from disk, caching, path errors |
| `audio/`        | Playback policy, volume, channels, music streaming  |

``AudioManager`` never loads files itself. All sound data comes through
``app.assets.sound()``. This keeps the two concerns cleanly separated.

---

## Accepted Decisions

### AudioManager owns playback policy, not asset loading
Sound files are loaded via ``AssetLoader``. ``AudioManager`` receives
``pygame.mixer.Sound`` objects and decides when and how to play them.

### Music and SFX are treated separately
Music uses ``pygame.mixer.music`` (streamed, one track at a time).
SFX uses ``pygame.mixer.Sound`` (in-memory, multiple simultaneous).

### Three independent volume levels
Master, music, and SFX volumes combine multiplicatively. Mute overrides
all to zero without destroying the stored volume values.

### Missing sounds are non-fatal
``app.assets.sound()`` returns ``None`` for missing files. ``play_sfx(None)``
is a safe no-op. Audio should never crash a game.

### AudioManager.shutdown() called before pygame.quit()
``Application._shutdown()`` calls ``audio.stop()`` on all channels and
music before quitting pygame, ensuring clean teardown.
