# Typing Hero — Architecture

This document explains **how the Typing Hero code is put together and why**. It is meant for anyone touching the code — human or AI. It deliberately skips things any Pygame project does (open a window, fill a background, flip the buffer) and focuses on the parts that are specific to this game.

> **Maintenance rule:** every pass that meaningfully changes a system must update the matching section here. Out-of-date architecture docs are worse than none.

---

## 1. The shape of the program

```
                              +-------------------+
                              |   main.py         |
                              |   GameManager     |   (thin coordinator)
                              +---------+---------+
                                        |
        +----------------+--------------+--------------+----------------+
        |                |              |              |                |
        v                v              v              v                v
   WordManager     SpawnDirector   ScoreManager      Audio          HUD layer
   (systems/)      (systems/)      (systems/)     (systems/)        (ui/)
        |                |              |              |                |
        |                v              |              |                +-- HeartsHUD
        |          spawns Alien         |              |                +-- ScoreHUD
        |           sprites into        |              |                +-- IntroScreen
        |           pygame Group        |              |                +-- PauseScreen
        |                               |              |                +-- GameOverScreen
        |                               v              v
        |                          high_score.txt     mixer channels
        |                          (json on disk)     (intro / bgm /
        |                                              sfx / alarms / ...)
        |
        +-- prefix lock + candidate set + word pool

                +------------------+         +-------------------+
                |  CRT (ui/crt.py) |         |  Background +     |
                |  scanline + flash|         |  Explosion        |
                |  + shield vignet.|         |  (core/animations)|
                +------------------+         +-------------------+
```

`GameManager` is intentionally thin. Its only jobs are:

- own the Pygame display, clock, and sprite groups,
- drain the event queue and route each event to a small handler,
- call `_update(delta_time)` and `_draw()` on the frame,
- own per-run scalar state (current `state`, hearts, laser tier, burst tier, shield/flash/invincibility deadlines) and pass that state into the systems that need it.

Anything that has its *own* persistent state (word pool, spawn timer, score + leaderboard, audio channels, HUD widgets, CRT overlay) lives in its own class. `GameManager` stitches them together; it does not implement them.

The `state` field is the high-level state machine — `'intro' | 'playing' | 'paused' | 'game_over'`. Every input handler and the `_update` / `_draw` paths branch on it.

---

## 2. The frame loop

Each frame, in order (see `GameManager.run` and `_update` in `main.py`):

1. **`_handle_events`** drains `pygame.event.get()` and dispatches each event to a typed handler (`_handle_keydown`, `_handle_spawn_event`). The keydown handler then forks again on `self.state` so intro / playing / paused / game-over each have their own keyboard contract.
2. **`_update(delta_time)`** advances per-frame state. The background scrolls in every state except `paused`; only the `'playing'` state runs `_update_playing`, which ticks alien movement, lasers, explosions, powerup drops, collisions, and miss/heart resolution.
3. **`_draw()`** paints the background, then the gameplay layer for the current state, then the HUD, the typing buffer, the CRT overlay, and finally the shield + damage vignettes on top so a future "disable CRT" toggle cannot suppress damage feedback.
4. **`pygame.display.flip()`** then **`clock.tick(ScreenSettings.FPS)`** caps the frame rate.

`delta_time` comes from `clock.get_time() / 1000.0` and is currently consumed only by the scrolling background; alien descent and laser travel are still expressed as per-frame pixel deltas (their `update()` methods don't take `dt`). That's a known asymmetry — see §13.

The `update` and `draw` methods are split on purpose: state advancement is deterministic given input, render is a pure function of state. That split is what will let pause and screenshots stay clean.

---

## 3. The word & typing subsystem

`systems/word_manager.py` owns everything related to the player's typing. It never touches Pygame or the screen — `GameManager` feeds it `KEYDOWN` events and reads back its state for rendering.

### 3.1 Data the manager owns

- `current_prefix` — the letters typed so far, **stored uppercase**. Storing uppercase is deliberate: every comparison in the codebase normalizes alien words with `.upper()`, and rendering is uppercase too (project rule), so storing uppercase eliminates a per-keystroke re-cast.
- `targeted_alien` — the alien currently provisionally focused (gets the cyan prefix split when drawn).
- `candidate_aliens` — every alien whose word still starts with the current prefix.
- `_word_bands` — five lists keyed `1..5` (very easy → very hard), loaded from `assets/words/band{N}_*.txt`.
- `_all_words` — flat de-duplicated union of all bands; used as a fallback when the active band is exhausted.

### 3.2 Soft-lock targeting

There is no hard lock in this codebase. On every `handle_letter`:

1. The provisional next prefix is computed (`current_prefix + char_upper`).
2. `_matching_aliens` filters live aliens by prefix.
3. If **no alien** matches, the keystroke is ignored — the prefix does not advance, no penalty.
4. If **at least one alien** matches, the prefix advances and `_update_candidates` re-sorts the candidates by `rect.top` descending. The first one (lowest on screen, most urgent) becomes `targeted_alien`.

This means typing `A` in the presence of both `APPLE` and `ARROW` keeps both alive; typing `AP` shifts focus to `APPLE`; if `APPLE` falls off, the next live word starting with `AP` (if any) takes over without any explicit "release lock" event.

`handle_enter` is only called by `GameManager` after it has already confirmed the prefix matches the targeted alien's full word, so completion is always unambiguous.

### 3.3 Word pools and difficulty bands

`pick_word(in_use, level)` returns a random word from the band mapped to the current level (`WordSettings.LEVEL_WORD_BAND`). It excludes any word currently on screen. If the active band is fully consumed, it falls back to `_all_words` (still excluding live words) so a busy frame never starves the spawner. When even the union is exhausted, it returns `None` — the spawn director silently skips that tick rather than crashing.

A legacy single-file `assets/words.txt` is still present and is used as a last-resort fallback only if every band file is missing (e.g. a partial install).

---

## 4. The spawn director

`systems/spawn_director.py` owns the spawn timer and is the only place where new `Alien` instances are constructed.

- A custom Pygame event (`pygame.event.custom_type()`) is allocated in `__init__` and registered with `pygame.time.set_timer`. `GameManager._handle_event` recognizes the event type and calls `_handle_spawn_event`, which calls `spawn(...)`.
- `spawn(...)` picks a color via weighted random (`SpawnSettings.COLORS` × `SpawnSettings.SPAWN_CHANCE`), picks a random x within `SpawnSettings.X_MARGIN` of the edges, requests a word from `WordManager.pick_word`, and adds the new `Alien` to the supplied sprite group. It returns the spawned alien (or `None` when the word pool is empty) so `GameManager` can react — currently only used to play the `ufo` SFX on blue spawns.
- `adjust_difficulty(score)` recomputes the spawn interval and the global `Alien.level_speed_multiplier` from the score. The interval table lives in `ScoreSettings.SPAWN_RATE_BY_LEVEL_MS` and the speed table in `ScoreSettings.ALIEN_SPEED_MULTIPLIER_BY_LEVEL`. If the new interval differs from the live one, `pygame.time.set_timer` is re-armed. This is called every time the score changes.
- `level(score)` walks `ScoreSettings.LEVEL_SCORE_THRESHOLDS` to map a score to a 1..`MAX_LEVEL` integer. `GameManager` caches the result in `self.current_level` for the HUD.
- `background_speed(score)` and `sync_background_speed(...)` handle a cosmetic-only ramp: starfield scroll speed grows in fixed steps independently of gameplay level. This intentionally produces motion-feedback that the player feels even between level breakpoints.

The first-frame spawn is triggered explicitly in `_reset_run_state` so the player never stares at a blank playfield while waiting for the timer to fire.

---

## 5. Score, hearts, and the leaderboard

`systems/score_manager.py` is the run-and-persistence layer. It is pure data — it never touches Pygame — and is read by `ScoreHUD` and by `main.py`.

- **`score`** — the current run's running total. Incremented by `add_for_color(color)` using `AlienSettings.POINTS` (red 100, green 200, yellow 300, blue 500).
- **`save_data`** — the JSON payload persisted to `high_score.txt` at the project root. Schema: `{ "high_score": int, "leaderboard": [{ "name": str, "score": int }, ...up to 10] }`.
- **Initials entry** is inlined here, not in a separate UI controller, because the data and the cursor position are inseparable. `entering_initials`, `initials`, and `initials_index` form a tiny three-key state machine driven by `cycle_char`, `move_cursor`, and `submit_initials`.
- **`finalize_game_over`** runs once per run. If the score qualifies (top-10 or any score when the leaderboard isn't full), it transitions into initials entry; otherwise it writes immediately. The `score_processed` flag prevents double-writes if `finalize_game_over` is called twice.

Hearts are **not** owned by `ScoreManager`. They live as a scalar `self.hearts` on `GameManager` because they're tightly coupled to the powerup-strip-before-heart-loss damage logic in `_apply_miss_penalty`. `HeartsHUD` is a pure renderer that reads the count.

Damage and shield deadlines (`_invincible_until`, `_flash_start`, `_flash_end`, `_shield_until`) also live on `GameManager` for the same reason — they're orchestration state, not score state.

---

## 6. Audio

`systems/audio.py` (`Audio`) is a single class that loads every music track and SFX up front, reserves a fixed set of mixer channels, and exposes a small named API.

- `CHANNEL_IDS` maps logical names (`'intro_music'`, `'bg_music'`, `'explosion'`, `'laser'`, `'alarm'`, `'ufo'`, `'pause'`, `'unpause'`, `'powerup'`, `'hyper'`) to mixer-channel indexes. Channel separation is deliberate — sharing a channel means a new play cuts the previous one off (e.g. rapid lasers replace each other), and reserved channels mean mid-frame SFX never steal music.
- `SOUND_BINDINGS` maps logical SFX names (`'laser'`, `'explosion'`, `'hyper'`, `'alarm_med'`, `'alarm_low'`, `'powerup_*'`, `'ufo'`, `'pause'`, `'unpause'`) to their channel + Sound attribute. Call sites use `audio.play('laser')` and never touch channel objects directly.
- Music helpers (`play_intro_music`, `ensure_bgm_playing`, `play_game_over_music`, `pause_music`, `unpause_music`, `stop_alarms`, `stop_bgm`) sit on top of those primitives and encode the gameplay rules: intro plays on title, BGM plays during runs, game-over music plays after death, pause suspends only the active music channel, alarms stop on game-over.
- All assets are loaded in `__init__`. A loading screen should be displayed before constructing this object on slower hardware because pre-loading can briefly freeze the UI.
- `AudioSettings.DEBUG_MUTE = True` silences everything for debugging without code changes.

---

## 7. Sprites & animations

The visible-but-not-system content lives in `core/`.

### 7.1 `core/sprites.py`

- **`Alien`** — falling enemy carrying a word.
  - Holds a `Vector2` `position` accumulator so sub-pixel `AlienSettings.SPEED[color]` values advance honestly (a SPEED of 0.5 px/frame becomes 1 px every other frame, not a stutter of 0/1).
  - Stores its color, word, and zigzag state. Yellow flips horizontal direction every `ZIGZAG_THRESHOLD` frames (wide sweep). Blue uses wall-bounce only (tighter). Red and green don't zigzag.
  - Class-level `level_speed_multiplier` is updated by `SpawnDirector.adjust_difficulty` and applied to every alien's per-color base speed each frame. One number scales the whole population.
  - `draw_word(surface, font, prefix_length=0)` renders the word in the slot above the sprite. When `prefix_length > 0`, the typed prefix renders in `WordSettings.PREFIX_COLOR` (cyan) and the rest in `WordSettings.COLOR` (white), centered as one combined block.
- **`KillLaser`** — vertical projectile. Optionally `is_piercing=True` (rainbow-tier) so it stays alive after a hit; otherwise it dies on first contact. Cycles through a color list per frame for the rainbow shimmer.
- **`RainbowLaser`** — wider, growing slice spawned every frame while the rainbow beam powerup is active. The cone shape emerges from stacking older slices that have grown wider and traveled further.
- **`PowerUp`** — drop sprite that descends from a killed alien and applies its effect when it reaches the bottom of the screen. Kinds are flagged by `PowerupSettings.{HEART_TYPE, SHIELD_TYPE, LASER_UPGRADE_TYPE, BURST_TYPE, RAINBOW_BEAM_TYPE}`.

### 7.2 `core/animations.py`

- **`Background`** — scrolling starfield. `scroll_speed` is rewritten by `SpawnDirector.sync_background_speed`. Owns its own `update(dt)` that scrolls by `scroll_speed * dt`.
- **`Explosion`** — short-lived spritesheet animation spawned at an alien's position on kill or shield-bottom-kill.

---

## 8. HUD & CRT overlay

### 8.1 `ui/hud.py`

Five small classes, all stateless beyond what's needed to lay themselves out:

- **`HeartsHUD`** — top-right row of heart icons; one disappears from the **left** of the row per heart lost (rightmost is the last to go). Reads `HeartSettings.MAX`, `SPACING`, `RIGHT_MARGIN`, `TOP_MARGIN`.
- **`ScoreHUD`** — top-left two-row readout: small `HIGH SCORE: ...` above the larger `SCORE: ...`. Also draws the current level.
- **`IntroScreen`** — the title + "PRESS ENTER TO BEGIN" prompt + leaderboard preview. Drawn while `state == 'intro'`.
- **`PauseScreen`** — centered overlay drawn over the frozen playfield while `state == 'paused'`.
- **`GameOverScreen`** — final score + leaderboard + initials-entry cursor. Reads from `ScoreManager` to know whether to show the cursor and where it is.

All five render only their own ALL-CAPS text — they take render data through their `draw()` arguments and never reach back into `GameManager`.

### 8.2 `ui/crt.py`

`CRT` adds two effects on top of every frame:

- a **TV-frame image** (`assets/graphics/tv.png`) blitted at a random alpha each frame in `ScreenSettings.CRT_ALPHA_RANGE`. The randomness produces the flicker.
- **horizontal scanlines** drawn onto a copy of that image every frame so the overlay does not accumulate between frames.

It also exposes two single-blit helpers for transient gameplay vignettes:

- **`draw_damage_flash(show_red)`** — alternates `tv_red.png` and `tv_white.png` while the post-hit flash window is active. Drawn **after** the CRT overlay and explicitly outside `draw()` so a future "disable CRT" toggle cannot accidentally suppress damage feedback.
- **`draw_shield_flash(blue_alpha)`** — composites the blue vignette on top of the white one. The white layer is always blitted at `ShieldSettings.FLASH_ALPHA`; the caller passes a blue alpha (0–255) for the layer on top. `GameManager` drives that alpha two ways: a smooth `(1 - cos(2π·phase)) / 2` crossfade with period `ShieldSettings.PULSE_PERIOD_MS` for the bulk of the shield window, and a rapid binary strobe in the final `WARNING_MS` ms so the impending expiry reads as urgent. The CRT layer doesn't know which mode it's in — it just blits whatever alpha it's handed.

---

## 9. Settings as the only knob panel

`settings.py` is the single place every tunable lives. Each class groups one subsystem (`ScreenSettings`, `FontSettings`, `AudioSettings`, `AssetPaths`, `WordSettings`, `SpawnSettings`, `AlienSettings`, `LaserSettings`, `PowerupSettings`, `ShieldSettings`, `DamageSettings`, `HeartSettings`, `TypingSettings`, `ScoreSettings`, `ColorSettings`). The rest of the codebase imports from here and never hard-codes a number.

This matters for two reasons:

1. **No magic numbers.** A reviewer reading gameplay code never has to guess what `0.5` means; they look up the named constant in `settings.py` and read the comment.
2. **Designer-friendly.** Tuning feel — alien speeds, spawn intervals, drop chances, flash durations, leaderboard size — is editing one file with comments next to each value, not hunting through implementation.

Adding a new tunable? Put it in `settings.py` with a comment explaining its **units** and what changing it does.

---

## 10. The asset pipeline

`assets/` is partitioned by type:

```
assets/
├── audio/        # SFX (explosion, laser, hyper, alarms, powerups, ufo, pause, unpause)
├── font/         # Pixeled.ttf — the only font, used at SMALL/MEDIUM/LARGE
├── graphics/     # Sprite PNGs (red1, green1, yellow1, blue1, player_ship, heart, explosion, background, tv, tv_blue, tv_red, tv_white)
├── music/        # Music tracks; AudioSettings.BGM_PLAYLIST picks from here
├── words/        # Difficulty-banded word lists (band1_very_easy ... band5_very_hard)
└── words.txt     # Legacy flat list — fallback only when band files are missing
```

Filesystem paths are not hand-typed at call sites. They're constructed once in `settings.py` (`AssetPaths`, `AudioSettings`, `WordSettings.WORD_BANK_PATHS`) and imported. When you add a new asset:

1. Drop the file in the right `assets/` subfolder.
2. Add its path to the matching settings class.
3. Reference the constant from the loader code; never write a literal `os.path.join('assets', ...)` outside `settings.py`.

Attribution files (`assets/audio/attributions.md`, `assets/graphics/attributions.md`, `assets/music/attributions.md`) record source credit and licenses. Update them whenever you add or replace an asset.

---

## 11. Input model

Keyboard-only. There is no controller path in this codebase (the launcher cabinet may eventually wrap this game, but the game itself doesn't enumerate joysticks).

Two cross-cutting bindings are global and intentionally fall through every state's handler:

- **`ESC`** quits cleanly from any state (`self.running = False` on the next loop).
- **`F11`** toggles fullscreen via `pygame.display.toggle_fullscreen()`.

Per-state contracts (see `_handle_*_keydown`):

- **`'intro'`** — `Enter` starts a run.
- **`'playing'`** — letter keys feed `WordManager.handle_letter`; `Backspace` feeds `handle_backspace`; completing a word triggers `_resolve_completed_word`; `Enter` pauses the run; `Space` is reserved (currently a no-op) for a future gameplay action.
- **`'paused'`** — only `Enter` resumes.
- **`'game_over'`** — if the score qualifies and `entering_initials` is set, only the initials controls (`Up`/`Down`/`Left`/`Right`/`Enter`) are accepted; otherwise `Enter` restarts.

Letter keys are filtered with `event.unicode.isalpha()` and capped at `TypingSettings.MAX_LENGTH` so a stuck key can't grow the buffer unbounded.

---

## 12. Code conventions worth knowing

Most rules live in [.github/copilot-instructions.md](../.github/copilot-instructions.md). Three are worth surfacing here because they shape how files **look**:

**Section banners.** Inside any class with multiple logical groupings, sections are separated by an all-caps banner comment:

```python
    # -------------------------
    # SECTION NAME
    # -------------------------
```

This is the style used in `main.py` (e.g. `BOOT / LIFECYCLE`, `GAMEPLAY ACTIONS`, `EVENT HANDLING`, `PER-FRAME UPDATE / RENDER`). New code must follow it; existing code that pre-dates the rule will be retrofitted as the surrounding section is touched.

**Function order inside a class.** Functions are grouped by role (boot, gameplay actions, audio, event handling, per-frame update/render). `update`, `_update`, and `run` go **last** and only call other functions on the class — they are coordinators, not implementations.

**ALL CAPS UI.** Every string passed to `font.render` (or to a HUD class that renders it) must be `.upper()`'d before it hits the screen. This is enforced project-wide.

---

## 13. What's *not* here yet

The following items will get their own sections in this document as they're built. If you're implementing one of these, please add the section as part of your pass. The full work plan lives in [docs/TODO.md](TODO.md).

- **Powerup design freeze for v2.** Heart-drop, shield, laser-tier upgrade, burst, and rainbow-beam are already implemented; the v2 pass narrows the catalog and tunes drop rates.
- **Yellow alien zigzag faithfulness.** The current frame-counter flip is close but not pixel-faithful to Star Hero; a sine-wave variant is on the table.
- **Status effects (e.g. blue alien letter-scramble).** Deferred — needs a design call before implementation.
- **Word-overlap defense at high spawn rates.** Spawn-time x-distance check vs. fixed lanes; not yet decided.
- **Frame-rate-independent alien & laser motion.** Today these are per-frame pixel deltas. Migrating to `dt`-driven motion is on the list and will let the game scale beyond 120 FPS without speeding up.
- **Stats screen on game over** (WPM, accuracy, longest streak).
- **Difficulty selector on the title screen.**
