# Change Log

This file is an append-only record of every code change made to Dungeon Digger
by a human, AI assistant, or copilot tool. Read it before making changes so you
know the current state of the codebase.

## Format

Each entry covers one logical change (which may touch multiple files). Use the
template below, with one `**File:** ... **Why:** ...` block per file touched.

    ## YYYY-MM-DD HH:MM — short summary

    **File:** path/to/file.py
    **Lines (at time of edit):** 38-52 (modified)
    **Before:**
        [old code]
    **After:**
        [new code]
    **Why:** explanation

## Conventions

* Line numbers reflect the file as it existed at the moment of the edit. Edits
  above shift line numbers below, so older entries will not match the current
  file. Never go back and "fix" old line numbers.
* Entries are append-only. Never delete history. If a later edit reverts an
  earlier one, write a new entry that references the original.
* For new files, write `(new file)` instead of a line range. The "Before"
  block can be omitted or marked `(file did not exist)`.
* For deletes, write `(deleted)` and put the removed code in "Before" with no
  "After" block.
* Keep "Before" / "After" blocks short. If a change is huge, summarize with a
  diff-style excerpt of the most important lines plus a sentence describing the
  rest, instead of pasting the entire file.

## 2026-04-29 23:18 — Reorganize source tree to match Dungeon Digger layout (Claude Opus 4.7)

The flat top-level layout (`animations.py`, `audio.py`, `debug.py`, `sprites.py`,
`style.py`, plus four manager classes living inside `main.py`) was reorganized
into the same `core/`, `systems/`, `ui/`, `tools/` package layout that
Dungeon Digger uses. No behavior or class/function names changed; this is a
pure structural move with import-path updates. Empty `__init__.py` files were
added in every new package, matching the Dungeon Digger pattern.

**File:** `core/__init__.py`
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** (empty)
**Why:** Make `core` a Python package so `from core.sprites import ...` works.

**File:** `core/sprites.py`
**Lines (at time of edit):** (new file, copied from `sprites.py`)
**Before:** (file did not exist; previously `star-hero/sprites.py`)
**After:** Same content as the deleted `sprites.py` (Laser, BombProjectile,
BombBlast, Player, Alien, PowerUp).
**Why:** Group gameplay entities under `core/`, mirroring
`dungeon-digger/core/sprites.py`.

**File:** `core/animations.py`
**Lines (at time of edit):** (new file)
**Before:** (file did not exist; the same code lived in `star-hero/animations.py`
alongside the `CRT` class.)
**After:** Contains only `Background` and `Explosion`.
**Why:** Sprite-style entities belong in `core/`; the unrelated `CRT` overlay
moved to `ui/` per the Dungeon Digger split.

**File:** `ui/__init__.py`
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** (empty)
**Why:** Make `ui` a Python package.

**File:** `ui/crt.py`
**Lines (at time of edit):** (new file)
**Before:** (file did not exist; `CRT` class was inside `animations.py`)
**After:** Contains only the `CRT` class, unchanged. Imports `pygame`,
`random`, and `from settings import *`.
**Why:** Match `dungeon-digger/ui/crt.py` exactly — overlay/UI code lives in
`ui/`, gameplay sprites do not.

**File:** `ui/style.py`
**Lines (at time of edit):** (new file, copied from `style.py`)
**Before:** (file did not exist; previously `star-hero/style.py`)
**After:** Same content as the deleted `style.py`.
**Why:** Move HUD/menu rendering under `ui/`, mirroring
`dungeon-digger/ui/render.py`. Class name `Style` preserved per the
"do not change names if not necessary" rule.

**File:** `systems/__init__.py`
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** (empty)
**Why:** Make `systems` a Python package.

**File:** `systems/audio.py`
**Lines (at time of edit):** (new file, copied from `audio.py`)
**Before:** (file did not exist; previously `star-hero/audio.py`)
**After:** Same content as the deleted `audio.py`.
**Why:** Match `dungeon-digger/systems/audio.py`.

**File:** `systems/managers.py`
**Lines (at time of edit):** (new file)
**Before:** (file did not exist; the four classes lived in
`main.py` lines 11–574)
**After:** Contains `CollisionManager`, `ScoreManager`,
`SessionStateManager`, and `SpawnDirector` exactly as they were in
`main.py`, plus the imports they need (`os`, `json`, `random`, `pygame`,
`from settings import *`, `from core.sprites import Laser, Alien, PowerUp`).
**Why:** Keep `GameManager` light by offloading its inline manager classes
to a dedicated module, mirroring `dungeon-digger/systems/managers.py`.

**File:** `systems/managers.py`
**Lines (at time of edit):** ScoreManager.__init__ and ScoreManager.save_scores
**Before:**
    score_file_path = os.path.join(os.path.dirname(__file__), 'high_score.txt')
**After:**
    score_file_path = os.path.join(AssetPaths.BASE_DIR, 'high_score.txt')
**Why:** Moving the manager into `systems/` would change `__file__` from the
game root to `systems/`, which would orphan the existing `high_score.txt` at
the game root and silently start a new save file. Anchoring the path to
`AssetPaths.BASE_DIR` (already defined in `settings.py`) keeps the file
exactly where players' saves already live.

**File:** `tools/__init__.py`
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** (empty)
**Why:** Make `tools` a Python package.

**File:** `tools/debug.py`
**Lines (at time of edit):** (new file, copied from `debug.py`)
**Before:** (file did not exist; previously `star-hero/debug.py`)
**After:** Same content as the deleted `debug.py`.
**Why:** Match `dungeon-digger/tools/`, the home for dev/debug helpers
that the game does not import at runtime.

**File:** `main.py`
**Lines (at time of edit):** 1–1038 (rewritten)
**Before:** A 1038-line file containing `CollisionManager`, `ScoreManager`,
`SessionStateManager`, `SpawnDirector`, and `GameManager`, with imports
`from animations import Background, Explosion, CRT`,
`from sprites import Laser, Player, Alien, PowerUp, BombBlast`,
`from style import Style`, `from audio import Audio`.
**After:** A 481-line file with only `GameManager` and the entry-point
guard. Imports updated to:
    from core.animations import Background, Explosion
    from core.sprites import Player, BombBlast
    from ui.style import Style
    from ui.crt import CRT
    from systems.audio import Audio
    from systems.managers import (
        CollisionManager,
        ScoreManager,
        SessionStateManager,
        SpawnDirector,
    )
The previously-imported `Laser`, `Alien`, and `PowerUp` are no longer used
in `main.py` (they are referenced only inside `SpawnDirector`, which now
lives in `systems/managers.py`), so they were dropped from the import list.
The unused `import json` and `import os` at the top of the original
`main.py` were also dropped.
**Why:** Keep `GameManager` light per `TESTING.md` and avoid dead
imports. Behavior is unchanged.

**File:** `animations.py` (deleted)
**Before:** Contained `Background`, `Explosion`, and `CRT`.
**Why:** Content split into `core/animations.py` and `ui/crt.py`.

**File:** `audio.py` (deleted)
**Before:** Contained the `Audio` class.
**Why:** Moved unchanged to `systems/audio.py`.

**File:** `debug.py` (deleted)
**Before:** Contained the `debug()` helper.
**Why:** Moved unchanged to `tools/debug.py`.

**File:** `sprites.py` (deleted)
**Before:** Contained `Laser`, `BombProjectile`, `BombBlast`, `Player`,
`Alien`, `PowerUp`.
**Why:** Moved unchanged to `core/sprites.py`.

**File:** `style.py` (deleted)
**Before:** Contained the `Style` class.
**Why:** Moved unchanged to `ui/style.py`.

## 2026-04-29 23:55 — Slim main.py, named-channel audio API, settings cleanup (Claude Opus 4.7)

A second-pass refactor with Dungeon Digger as the model. The goals (per
`docs/TESTING.md`) were a slimmer `GameManager`, fewer middlemen, fewer
magic numbers, and a single way to talk to the audio system. No gameplay
behavior was intentionally changed.

**File:** `settings.py`
**Lines (at time of edit):** various class additions
**Before:**
    class ScreenSettings: ... CRT_ALPHA_RANGE = (75, 90)
    class ControllerSettings: A_BUTTON, X_BUTTON, Y_BUTTON, L1, R1, sticks
    class AlienSettings: ... ZIGZAG_THRESHOLD = 100
    class BombSettings: PROJECTILE_RADIUS, FLASH_SPEED, BLAST_*
    class UISettings: HEART_*, VOLUME_*
**After:** Added `ScreenSettings.CRT_SCANLINE_HEIGHT`,
`ControllerSettings.B_BUTTON / BACK_BUTTON / START_BUTTON / QUIT_COMBO`,
`AlienSettings.OFFSCREEN_MARGIN` and `CONFUSION_BEAM_*` /
`CONFUSION_PLAYER_TINT`, `BombSettings.PROJECTILE_BASE_COLOR /
PROJECTILE_FLASH_COLOR / PROJECTILE_OUTLINE_COLOR /
PROJECTILE_OUTLINE_WIDTH / BLAST_RING_ALPHA / BLAST_RING_WIDTH /
BLAST_FILL_COLOR`, and `UISettings.HEART_RIGHT_MARGIN /
STATUS_RIGHT_MARGIN / STATUS_ROW_SPACING / BOOST_METER_WIDTH /
BOOST_METER_HEIGHT / BOOST_METER_TOP_GAP / BOOST_METER_BOTTOM_GAP /
BOMBS_ROW_TOP_GAP`.
**Why:** `TESTING.md` requires constants live in `settings.py`. Every
new constant replaces a magic number that previously appeared inline in
`main.py`, `core/sprites.py`, `ui/crt.py`, or `ui/style.py`.

**File:** `systems/audio.py`
**Lines (at time of edit):** 1-219 (rewritten)
**Before:** A flat ~170-line module with raw `self.channel_0` through
`self.channel_10` attributes. Every call site reached into the channel
(`audio.channel_3.play(audio.laser_sound)`) and the music plumbing was
spread across the main loop and managers.
**After:** A class organized as `CHANNEL_IDS` + `SOUND_BINDINGS` (mirroring
`dungeon-digger/systems/audio.py`) with a single `play(name)` SFX entry
point and explicit music helpers (`play_intro_music`, `stop_intro_music`,
`ensure_bgm_playing`, `stop_bgm`, `pause_music`, `unpause_music`,
`stop_alarms`). The dead `tractor_beam` placeholder, `channel_9`, and
their commented-out volume update were dropped.
**Why:** Hides channel allocation behind one named API, removes the
dead tractor-beam scaffolding, and matches the Dungeon Digger pattern.

**File:** `systems/managers.py`
**Lines (at time of edit):** 1-580 (rewritten in place)
**Before:** Four manager classes wired to the raw `audio.channel_X`
attributes; `SpawnDirector.get_bomb_drop_chance` referenced
nonexistent `AlienSettings.BOMB_DROP_BASE` / `BOMB_DROP_BONUS`
constants and was never called; `SpawnDirector.volume_display_timer`
lived here for no reason; `SessionStateManager.unpause_game` and
`pause` reached into `channel_0/1/4/9` directly.
**After:** All audio goes through the new `audio.play(name)` /
`audio.unpause_music()` / `audio.stop_alarms()` API. The dead
`get_bomb_drop_chance` is gone. `volume_display_timer` is moved to
`GameManager` (it has nothing to do with spawning). The pause inner
loop now uses `ControllerSettings.START_BUTTON / BACK_BUTTON` and the
public `game.handle_joystick_hotplug`. A new
`CollisionManager._confusion_beams` performs the player-vs-beam
overlap test (was inline in `main.py`).
**Why:** Fewer middlemen, less dead code, magic-number-free button
handling, and the player-confusion gameplay rule no longer lives in
the rendering path.

**File:** `core/sprites.py`
**Lines (at time of edit):** Player.shoot_laser, Alien (animate/destroy),
new `update_confusion_beam` / `draw_confusion_beam` /
`get_confusion_beam_mask`, BombProjectile, BombBlast, Player tint
**Before:** `Player.shoot_laser` called `self.audio.channel_10.play(...)`
and `self.audio.channel_3.play(...)`. `BombProjectile` hard-coded
`(10,10,10)`, `(55,55,55)`, `(255,40,40)`, outline width `2`.
`BombBlast._redraw` hard-coded `(255,255,255,235)`, ring width `3`.
`Alien.destroy` killed at `screen_height + 50`. The Player's confusion
tint was inline `(200, 0, 255, 255)`.
**After:** `Player.shoot_laser` calls `audio.play('hyper')` /
`audio.play('laser')`. All bomb projectile + blast colors and widths
read from `BombSettings`. `Alien.destroy` reads
`AlienSettings.OFFSCREEN_MARGIN`. The Player tint reads
`AlienSettings.CONFUSION_PLAYER_TINT`. `Alien.update` now caches the
per-frame confusion beam in `self.confusion_beam_surf` (built once by
`update_confusion_beam`) so both rendering (`draw_confusion_beam`) and
collision (`get_confusion_beam_mask`) share the exact same pixels —
this fixes a latent double-step in `confusion_growth` if both paths
had built the surface independently.
**Why:** Eliminates magic numbers, lifts the confusion-beam visuals
out of `main.py` so they can be tested and reasoned about per-alien.

**File:** `ui/crt.py`
**Lines (at time of edit):** create_crt_lines
**Before:** `line_height = 3` literal.
**After:** `line_height = ScreenSettings.CRT_SCANLINE_HEIGHT`.
**Why:** `TESTING.md` rule: no magic numbers.

**File:** `ui/style.py`
**Lines (at time of edit):** Style.__init__ + new `display_hearts` +
`display_player_status` layout
**Before:** Heart icon ownership lived in `GameManager`; `Style` had no
hearts API. `display_player_status` hard-coded `right_margin = 10`,
`row_spacing = 15`, `meter_width = 100`, `meter_height = 8`, and the
`+9` / `+10` / `+16` HUD anchors.
**After:** `Style.__init__` loads the heart sprite once and computes
`heart_x_start_pos` itself. `Style.display_hearts(hearts)` renders
the hearts row. `display_player_status` reads the new
`UISettings.STATUS_* / BOOST_METER_* / BOMBS_ROW_TOP_GAP` constants.
**Why:** HUD rendering belongs in the UI module; offloading hearts
keeps `GameManager` light per `TESTING.md`.

**File:** `main.py`
**Lines (at time of edit):** 1-468 (rewritten)
**Before:** A 481-line `GameManager` with a `run()` method that
contained ~250 lines of inline event handling, drawing logic, and
the entire blue-alien confusion-beam render-and-collide block.
Magic button numbers (`event.button == 7`, `6`, `1`, `0`) were
sprinkled throughout. `_is_joystick_device_event` /
`_handle_joystick_hotplug` were a middleman pair. `display_hearts`
and the heart sprite lived on `GameManager`. Music plumbing was
inline (`self.audio.channel_0.stop()`, `if not
self.audio.channel_1.get_busy(): ...`). The dead `channel_9.stop()`
calls and `# Tractor beam sound disabled (file deleted)` block
remained from a prior cleanup.
**After:** A 468-line file split into clearly-roled sections:
`__init__`, BOOT/LIFECYCLE (`_show_loading_screen`, `close_game`,
`refresh_joysticks`, `quit_combo_pressed`, `handle_joystick_hotplug`),
GAMEPLAY ACTIONS (`handle_alien_destroyed`, `trigger_bomb_blast`,
`handle_bomb_input`, `explode`), AUDIO/VOLUME ACTIONS
(`toggle_debug_mute`, `adjust_master_volume`, `pause_game`),
EVENT HANDLING (`_process_events`, `_handle_keydown`,
`_handle_joybuttondown`, `_handle_joyhatmotion`,
`_handle_active_gameplay_timer`, `_on_player_death_timer`),
PER-FRAME UPDATE/RENDER (`_world_speed_multiplier`,
`_update_world`, `_draw_active_gameplay`, `_draw_inactive_screen`,
`_update_music`, `_render_frame`), and a 9-line `run()`. Every
controller-button check uses `ControllerSettings.*_BUTTON`. The
`_is_joystick_device_event` middleman is folded into
`handle_joystick_hotplug`. `display_hearts` is delegated to
`Style`. The confusion-beam draw loop calls
`alien.draw_confusion_beam(self.screen)` for each alien;
collision is handled by `CollisionManager._confusion_beams`. All
audio uses the new `audio.play(name)` / `audio.pause_music()` /
`audio.ensure_bgm_playing()` / `audio.stop_intro_music()` /
`audio.stop_bgm()` API. The dead `channel_9` references and the
"Tractor beam sound disabled" block are gone.
**Why:** `TESTING.md`: GameManager must be light, classes communicate
through GameManager, no middlemen, magic numbers in `settings.py`,
update/render functions stay short and only call other functions.

## 2026-04-30 00:10 — Move bundled media under assets/ (Claude Opus 4.7)

The four top-level media folders (`audio/`, `font/`, `graphics/`, `music/`)
were moved into a single `assets/` folder so the project root only carries
code + docs + saves. This matches the `dungeon-digger/assets/` layout.

**File:** `audio/`, `font/`, `graphics/`, `music/` (moved)
**Before:** Four sibling folders at the project root
(`star-hero/audio/`, `star-hero/font/`, `star-hero/graphics/`,
`star-hero/music/`).
**After:** Re-rooted under `star-hero/assets/`
(`star-hero/assets/audio/`, `star-hero/assets/font/`,
`star-hero/assets/graphics/`, `star-hero/assets/music/`). Folder names
inside `assets/` are unchanged so attribution links and any external
tooling that walks them by name still work.
**Why:** Match Dungeon Digger's layout and tidy the project root.

**File:** `settings.py`
**Lines (at time of edit):** FontSettings.FONT, AudioSettings.MUSIC_DIR /
AUDIO_DIR / new ASSETS_DIR, AssetPaths.ASSETS_DIR / GRAPHICS_DIR
**Before:**
    FONT = os.path.join(os.path.dirname(__file__), 'font', 'Pixeled.ttf')
    ...
    BASE_DIR = os.path.dirname(__file__)
    MUSIC_DIR = os.path.join(BASE_DIR, 'music')
    AUDIO_DIR = os.path.join(BASE_DIR, 'audio')
    ...
    GRAPHICS_DIR = os.path.join(BASE_DIR, 'graphics')
**After:**
    FONT = os.path.join(os.path.dirname(__file__), 'assets', 'font', 'Pixeled.ttf')
    ...
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    MUSIC_DIR = os.path.join(ASSETS_DIR, 'music')
    AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')
    ...
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    GRAPHICS_DIR = os.path.join(ASSETS_DIR, 'graphics')
**Why:** Point every asset-path constant at the new `assets/` root.
`ASSETS_DIR` is added to both `AudioSettings` and `AssetPaths` (each
class already had its own `BASE_DIR`, so each gets its own `ASSETS_DIR`
in the same style — no cross-class import needed).

**File:** `README.md`
**Lines (at time of edit):** title image + alien example images +
attribution links
**Before:** Image URLs `.../refs/heads/main/graphics/<file>.png` and
attribution links `[graphics/attributions.md](graphics/attributions.md)` /
`[audio/attributions.md](audio/attributions.md)`.
**After:** Image URLs `.../refs/heads/main/assets/graphics/<file>.png`
and attribution links `[assets/graphics/attributions.md](...)` /
`[assets/audio/attributions.md](...)`.
**Why:** Reflect the new on-disk layout so README links and
GitHub-rendered images keep working once the rename is pushed.

**File:** four leftover `.bak` files (deleted)
**Before:** `settings.py.bak`, `systems/audio.py.bak`,
`core/sprites.py.bak`, `ui/style.py.bak` were left behind by an
earlier in-session `cp` that the workspace sandbox would not let
`rm`.
**Why:** Clean up the working tree; verified after re-enabling delete
permissions.

**Verification:** A fresh Python process (started after the move)
imported `settings`, walked every `FontSettings.FONT`,
`AudioSettings.MUSIC_DIR`/`AUDIO_DIR`, every `AssetPaths.*` PNG,
every BGM track in `AudioSettings.BGM_PLAYLIST`, every SFX file
referenced by `Audio.__init__`, and every `{color}{n}.png` alien
spritesheet. All paths resolved to existing files under `assets/`.
The interactive `docs/TESTING.md` checklist (intro music, leaderboard,
game-active music + volume + pause + fullscreen, lasers, powerups /
upgrades / damage / heal, death + initials + game-over music) should
be re-run on Windows since the sandbox here has no display or
`pygame` install.


