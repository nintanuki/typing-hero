# Typing Hero — Build Plan

> **Read this first if you are a future Claude session picking this up.** This file is the project handoff. It captures the conversation that led to this plan, the design decisions made so far, the open questions still on the table, and the staged build path. Read it end-to-end before writing any code.

---

## 1. Context (what this project is and why)

The repo started as **Star Hero**, a vertically scrolling shoot-'em-up built with Python + Pygame. Frankie (the owner) wants to transform it into **Typing Hero** — a typing-based arcade game where words appear above descending aliens and the player destroys them by typing.

The Star Hero source has been frozen into `legacy/` and is **read-only**. Treat it as a reference library to port pieces from, not a codebase to mutate. The root of the repo is currently empty of code (only docs + `legacy/`); we are building Typing Hero fresh, reusing assets and selectively porting subsystems.

### Why a fresh build instead of gutting in place

Star Hero's gameplay code is tightly coupled — `Player` owns lasers, bombs, boost meter, confusion state, and three powerup tracks; `CollisionManager` runs six discrete collision passes; `SpawnDirector` is wired to score-based difficulty. Commenting things out in place would mean repeated re-reads of tangled code and a messy file full of dead branches. A fresh build is cleaner, smaller (target: ~600-800 lines vs Star Hero's ~3000+), and lets us "pull forward" features deliberately when we need them. Git history + `legacy/` together preserve everything.

---

## 2. Gameplay vision (what we agreed on)

**Core loop.** Aliens spawn at the top of the screen, each carrying a word floating above (or below) them. The player types — the game auto-locks onto whichever alien's word starts with what's been typed so far (ZType / Typing of the Dead style). When the word is completed (Enter or auto-fire — TBD), a laser fires from the player's ship and destroys the targeted alien. Aliens that reach the bottom of the screen cost the player a heart.

**What stays from Star Hero:**
- The ship sprite (still on screen as a visual anchor).
- Hearts HUD, but rebalanced — three "misses" at Star Hero's spawn rate is brutal. Either slow alien speed dramatically, lower spawn rate, or give each heart multiple miss-absorption.
- Background scroll, CRT shader (visual flavor — ports cleanly).
- Explosion sprite/animation on alien kill.
- Audio system (laser SFX, explosion SFX, music, master volume).
- Score system + initials entry leaderboard.
- Title screen / game over screen / pause flow.
- The four alien colors and their visual identity (red, green, yellow, blue).

**What gets cut (probably forever):**
- Player movement (WASD/arrow keys/joystick). The ship is now static or auto-aiming.
- Boost meter, brake meter, world-speed multiplier. Pacing is driven by typing speed, not movement.
- Alien lasers. Aliens threaten by *reaching the bottom*, not by shooting.
- Bombs (cut for v1; might return as a "screen wipe" powerup later).
- All five laser tiers + rapid fire + rainbow beam. One word = one kill, so weapon upgrades don't translate.
- Most powerups in their current form.

**What gets cut (for now, may revisit):**
- Confusion attack (blue alien beam). Could be reimagined as letter-scrambling later.
- Most powerups — rework them as typing-flavored buffs in a later stage.

---

## 3. Open design questions

These are the questions we deferred. Resolve them with Frankie before starting the stage that depends on them.

### Q1. Ship behavior
Three options on the table:
- **(a) Static ship, laser appears on completion.** Ship sits centered at the bottom; laser shoots straight up or arcs to the targeted alien. Simplest.
- **(b) Static ship that auto-rotates to aim at the targeted alien before firing.** Visually satisfying, more code.
- **(c) No ship at all, laser materializes at the bottom of the screen.** Most minimal, loses some visual interest.

Frankie hasn't picked. Recommend (b) as the "feels best" option but (a) is the right v1 choice — defer (b) to a polish stage.

### Q2. Word completion trigger
- Auto-fire the moment the last letter is typed correctly?
- Or require Enter to confirm?

User mentioned "every time they successfully type a word and hit enter." So: **Enter required, leaning yes** — but worth confirming. Auto-fire feels snappier; Enter feels deliberate and matches arcade-cabinet "commit" feel. Could be a setting.

### Q3. Wrong character handling
- Silently ignore? (forgiving)
- Beep / flash? (feedback but no penalty)
- Break the active prefix lock? (punishing — forces re-typing from scratch)
- Count toward a typo stat shown on game over? (lightweight metric)

No decision yet. Default for v1: ignore wrong characters but reset the prefix match if the typed prefix no longer matches any alien's word start.

### Q4. Word source
- Built-in list inside `settings.py`? (simple, visible in source)
- Plain text file in `assets/words.txt`? (easier to edit without touching code — recommended)
- Word API at runtime? (network dependency, overkill)

Recommend `assets/words.txt`, plus optionally separate lists by difficulty (`words_easy.txt`, `words_hard.txt`).

### Q5. Heart / miss balance
- 3 hearts, 1 miss = 1 heart? (matches Star Hero, harsh)
- 3 hearts, each absorbs N misses? (softer, more readable)
- 5 hearts, 1 miss = 1 heart? (just bump the count)

Decision: start with 3 hearts × 1 miss each but **tune alien speed and spawn rate way down** so reaching the bottom takes 8–10 seconds. Revisit only if it still feels harsh.

### Q6. Word difficulty progression
- Same word pool throughout?
- Short common words → longer rarer words as score climbs?
- Different alien colors carry different difficulty bands? (red = 3-4 letter, blue = 7+ letter)

Tentatively: tie difficulty to alien color, since the four colors already exist in the asset set. Red = easy/short, blue = hard/long. This also gives a reason to vary point values by color.

### Q7. Capitalization & punctuation
**Decision:** all in-game text is displayed in UPPERCASE. This is a project-wide rule
(see §6 pitfall "All in-game text is uppercase"): alien words, the player's typed
buffer, HUD score, "GAME OVER" banner, leaderboard initials — every string we
``font.render`` goes through ``.upper()`` (or is stored uppercase) before it hits
the screen. The Pixeled font already reads as a chunky pixel-arcade face, and
keeping everything in caps reinforces the cabinet vibe and removes a class of
"typed 'h' but the alien word starts with 'H'" matching bugs.

Comparisons against typed input are case-insensitive (compare ``input.upper()``
against ``alien.word.upper()``) so the underlying word list can stay lowercase
on disk if that's easier to maintain. No punctuation in v1.

### Q8. Powerups in a typing context
Most don't translate. Candidates that *could* fit:
- **Heal:** drops from a destroyed alien, restores a heart. Trivial port from Star Hero.
- **Slow time:** all aliens fall slower for N seconds. New mechanic.
- **Screen wipe:** kills all on-screen aliens. (Could be the bomb's reincarnation.)
- **Word skip:** completes the targeted alien's word for free.
- **Shorter words:** for N seconds, only short words spawn.

Cut *all* powerups for v1. Add 1–2 in a later stage once the core loop feels good.

### Q9. Status effects (debuffs)
The blue alien's "confusion" effect (reverses controls in Star Hero) could become "scrambles the letters of the targeted word" or "displays the word backwards." Cute but punishing — defer to v2.

### Q10. Pause
Does it make sense in a typing game? Pause-mid-word breaks flow. Probably keep it for accessibility (Esc / Enter), but disable it during an active typing prefix (only pausable when no word is in progress).

---

## 4. What's in `legacy/` and how to reuse it

`legacy/` contains the full Star Hero source. **Do not edit anything inside it.** Read selectively — never dump entire files into context. The most useful pieces, ranked by reuse value:

### Reusable verbatim or near-verbatim
- `legacy/assets/` — all graphics, audio, fonts, music. Copy the whole folder to `assets/` at the repo root in Stage 0.
- `legacy/core/animations.py` — `Background` (scrolling) and `Explosion` (spritesheet animation). Both port directly.
- `legacy/systems/audio.py` — Audio system with master volume, music handling, SFX channels. Drop the powerup sounds we don't need.
- `legacy/ui/crt.py` — CRT scanline overlay. Ports as-is.
- `legacy/tools/debug.py` — debug utilities. Optional.

### Reuse with significant trimming
- `legacy/settings.py` — keep `ScreenSettings`, `ColorSettings`, `FontSettings`, `AudioSettings`, `AssetPaths`, `UISettings` (heart geometry only). Drop `PlayerSettings` (mostly), `ControllerSettings`, `LaserSettings` (mostly), `PowerupSettings`, `BombSettings`, most of `AlienSettings`. Add a new `WordSettings`, `TypingSettings`.
- `legacy/ui/style.py` — heavy edits. Keep heart rendering, font helpers, intro/game-over screens. Drop boost meter, bombs row, status row.
- `legacy/systems/managers.py` `ScoreManager` — keeps mostly intact (initials entry + JSON save).
- `legacy/systems/managers.py` `SessionStateManager` — keep, it just toggles `game_active`/`player_alive` and routes pause/intro/game-over.
- `legacy/systems/managers.py` `SpawnDirector` — keep skeleton (timer events, difficulty step), replace difficulty curve.
- `legacy/core/sprites.py` `Alien` class — keep the per-color sprite loading + frame animation + downward movement. Drop confusion attack, zigzag for blue (probably). Add `word` attribute and a method to render the word above the sprite.
- `legacy/core/sprites.py` `Laser` class — strip to the minimum: position, color, vertical motion, off-screen kill. No piercing, no rainbow, no growth.
- `legacy/core/sprites.py` `Player` class — strip to image + rect + a `fire_at(target)` method. No input handling, no powerup state, no boost.

### Replace entirely
- `legacy/systems/managers.py` `CollisionManager` — typing games don't need spatial collision. Replace with a `WordManager` / `TypingManager` that tracks the active prefix and the targeted alien.
- `legacy/main.py` — too many shooter-specific event handlers. Write fresh, keeping the same skeleton (subsystem init, event pump, update, render, flip).

### New files we'll need
- `systems/word_manager.py` — owns the word list, the active prefix, the targeted alien selection logic.
- `systems/typing_input.py` (maybe folded into the above) — converts pygame KEYDOWN events into typing actions.
- `assets/words.txt` (or per-difficulty files).

---

## 5. Staged build plan (baby steps)

Each stage is small enough to finish, run, and *see something change* in one sitting. Each ends with a manual smoke test (mirrored in `docs/TESTING.md`). Do not skip ahead — earlier stages give later stages somewhere to dock.

### Stage 0 — Scaffold ✅
**Goal:** `python main.py` opens a 600×800 black pygame window titled "Typing Hero" that closes on ESC or window-close.

**Steps:**

- [x] 1. Copy `legacy/assets/` to `assets/` at the repo root.
- [x] 2. Create `core/__init__.py`, `systems/__init__.py`, `ui/__init__.py` (empty).
- [x] 3. Create a stripped `settings.py` containing only: `ColorSettings`, `ScreenSettings`, `FontSettings`, `AudioSettings`, `AssetPaths`. No game-mechanic constants yet.
- [x] 4. Create `main.py` that initializes pygame, opens the display, runs an event loop (QUIT + ESC), fills the screen black each frame, flips, and ticks the clock.
- [x] 5. Smoke test: window opens, ESC closes it, no errors.

**Out of scope:** anything else. Resist adding a player sprite here.

### Stage 1 — One alien, one word on screen ✅
**Goal:** A single red alien sprite is rendered at center-screen with the word "hello" displayed above it. Nothing moves, nothing reacts to input.

**Steps:**

- [x] 1. Create `core/sprites.py` with a stripped-down `Alien` class: loads one sprite, has a `word` attribute, has a `draw_word(surface, font)` method that renders the word above its rect.
- [x] 2. In `main.py`, instantiate one alien at `(WIDTH/2, HEIGHT/2)` with `word="hello"`. Add it to a sprite group. Draw the group + the word each frame.
- [x] 3. Smoke test: window shows alien + "hello" above it.

### Stage 2 — Type the word to destroy the alien ✅
**Goal:** Typing "hello" + Enter removes the alien and prints "kill" to the console (no laser visual yet).

**Steps:**

- [x] 1. Capture `pygame.KEYDOWN` events; build up a `current_input` string from letter keys.
- [x] 2. Render `current_input` somewhere visible (e.g. bottom-center of screen) so we can debug.
- [x] 3. On Enter, if `current_input == alien.word`, kill the alien and reset `current_input`. If not, just reset `current_input`.
- [x] 4. Smoke test: typing "hello" + Enter removes the alien; typing "wrong" + Enter does nothing but clears the buffer.

**Resolution this stage:** went with **Enter required** to fire (Q2), keeping the deliberate cabinet-commit feel — auto-fire is easy to add later by moving the comparison out of the `K_RETURN` branch into the letter-append branch. Wrong-character handling (Q3) is moot at Stage 2 because there is no prefix lock yet; the buffer just accumulates whatever letters the player presses until Enter. Backspace removes the most recent character (TESTING.md asks for this as an optional QoL).

**Capitalization rule lands here.** Q7 is now resolved: every string we render goes through `.upper()`. The Stage 2 work threads this through three places — `Alien.draw_word`, the typing-buffer blit in `main.py`, and the Enter-comparison (which uppercases both sides before checking equality). Future stages must keep that pattern.

### Stage 3 — Multiple aliens with prefix-locking ✅
**Goal:** Three aliens visible with different words. Typing the first letter of one of them locks onto it (visual highlight); typing the rest of the word + Enter destroys it.

**Steps:**

- [x] 1. Spawn three hardcoded aliens at fixed positions with three different words (different first letters).
- [x] 2. Build a small `WordManager` (in `systems/word_manager.py`) that tracks `current_prefix` and `targeted_alien`. On each KEYDOWN: if no target locked, find the alien whose word starts with the new prefix; if a target is locked, append the letter only if the new prefix still matches the target's word.
- [x] 3. Visually highlight the targeted alien (e.g. tint its word color or draw a bracket around it). Render typed prefix in a different color than untyped letters in the targeted word.
- [x] 4. On Enter (or full match), if the prefix equals the target's word, kill it and clear the lock.
- [x] 5. Smoke test: pressing different first letters locks onto the matching alien; typing the wrong continuation does not advance.

**Resolution this stage:** Q3 is now resolved as **ignore wrong-letter keystrokes; the lock survives** — the most forgiving option, easy to relax to "break lock" later by deleting one branch in `WordManager.handle_letter`. Highlight style is the **two-color word** (typed prefix in `WordSettings.PREFIX_COLOR` cyan, untyped suffix in `WordSettings.COLOR` white) — a bracket/reticle around the alien sprite was considered but cut as redundant once the prefix split made the lock unmistakable. The three demo aliens (red `HELLO` left, green `WORLD` center, yellow `TYPE` right) live in `Stage3Layout` in `settings.py` so they're tunable in one place; that class will be deleted when `SpawnDirector` takes over alien creation in Stage 4.

**Tie-break rule landed.** When two aliens share a starting letter (Stage 3 deliberately avoids it; Stage 4+ word-list spawning will produce it), `WordManager._acquire_target` picks the **lowest-y alien** — the one closest to the bottom edge, i.e. most about to be missed. This matches the `§6` pitfall note about ambiguous prefix-locking. Sort key is `rect.top` (descending); revisit if Stage 5 motion makes a `centery`-based key feel more natural.

**Enter on a partial prefix** clears the lock + buffer without firing — same "Enter always commits" feel as Stage 2. Could become a no-op (silent ignore) later if it feels punishing in practice.

### Stage 4 — Word list + spawning over time
**Goal:** Aliens spawn at the top of the screen at intervals, each picking a random word from `assets/words.txt`. They still don't move.

**Steps:**

- [ ] 1. Add `assets/words.txt` with 50–100 short common words.
- [ ] 2. `WordManager` loads the file at boot and serves random words on demand. Ensure no duplicate words on screen at once (otherwise prefix-locking is ambiguous).
- [ ] 3. Port a stripped `SpawnDirector` from `legacy/systems/managers.py` that fires a pygame timer event every N ms and spawns one alien at a random x position near the top.
- [ ] 4. Smoke test: aliens appear at the top every couple seconds, with unique words. Typing still works against any of them.

### Stage 5 — Aliens fall + miss mechanic
**Goal:** Aliens drift downward. Reaching the bottom edge counts as a miss (just print "miss" for now).

**Steps:**

- [ ] 1. Port the alien movement loop from `legacy/core/sprites.py` `Alien.calculate_movement` — vertical-only for now, slow speed (start with `1` px/frame at 60 FPS, tune later).
- [ ] 2. When `alien.rect.top > ScreenSettings.HEIGHT`, trigger a miss callback and `alien.kill()`.
- [ ] 3. If the killed alien was the active target, clear the lock.
- [ ] 4. Smoke test: aliens fall slowly, untyped aliens disappear off the bottom and print a miss.

### Stage 6 — Hearts + game over
**Goal:** Hearts HUD in top-right. Each miss removes one. Zero hearts → game over screen → restart.

**Steps:**

- [ ] 1. Port heart rendering from `legacy/ui/style.py` (`display_hearts`).
- [ ] 2. Add a `hearts` counter in main; decrement on miss. At zero, set `game_active = False`.
- [ ] 3. Show a minimal "GAME OVER — press Enter to restart" screen.
- [ ] 4. On Enter from game-over, reset hearts, clear aliens, set `game_active = True`.
- [ ] 5. Smoke test: misses subtract hearts; at zero, game-over appears; Enter restarts.

**Tuning checkpoint.** Play it. Are misses too punishing? Adjust alien speed and spawn rate before moving on. (Q5.)

### Stage 7 — Score + simple difficulty ramp
**Goal:** Word kills award points. Score visible. Spawn rate (and maybe fall speed) increases as score climbs.

**Steps:**

- [ ] 1. Port `ScoreManager` from `legacy/systems/managers.py` — keep the JSON save and initials flow if Frankie wants leaderboards.
- [ ] 2. Award points per kill. Tentatively scale by word length (longer words = more points) or by alien color (Q6).
- [ ] 3. Port `SpawnDirector.adjust_difficulty` skeleton — every N points, drop spawn interval by a step (clamped to a minimum). Same for fall speed.
- [ ] 4. Smoke test: score climbs, harder over time, doesn't ramp into impossibility.

### Stage 8 — Audio + explosion polish
**Goal:** Laser SFX on kill, explosion sprite + SFX at killed alien's position, background music.

**Steps:**

- [ ] 1. Port `Audio` system from `legacy/systems/audio.py`. Drop powerup-related cue keys we don't use.
- [ ] 2. Port `Explosion` sprite from `legacy/core/animations.py`.
- [ ] 3. On a successful kill: spawn an explosion at the alien's position, play `explosion`. Also play `laser` sound (consider: does laser play on key-press, on full-word completion, or both? Probably full-word.).
- [ ] 4. Start `star_hero.ogg` BGM on game start. (Optionally re-theme the music later.)
- [ ] 5. Optional: port `Background` scroll + `CRT` shader for visual flavor.
- [ ] 6. Smoke test: feels arcade-y. Audio doesn't stutter.

### Stage 9 — Menus + leaderboard
**Goal:** Title screen → game → game over → optional initials entry → restart loop. Pause works.

**Steps:**

- [ ] 1. Port intro/game-over rendering from `legacy/ui/style.py`. Strip any boost-meter / bombs / status-row leftovers.
- [ ] 2. Port `SessionStateManager` toggle (`game_active`, `player_alive`, intro music).
- [ ] 3. If keeping leaderboards, port `ScoreManager` initials entry path (arrow keys to cycle letters, Enter to submit).
- [ ] 4. Pause: Enter pauses *only when no word is mid-typing* (Q10).
- [ ] 5. Smoke test: full loop — title → play → game over → initials → title.

### Stage 10 — V2 / polish (pick à la carte)

- [ ] 1–2 powerups (heal, screen-wipe, slow-time, word-skip — see Q8).
- [ ] Difficulty bands by alien color (Q6).
- [ ] Status effect: scrambled-letters debuff from blue aliens (Q9).
- [ ] Re-theme the music if Star Hero's track no longer fits the vibe.
- [ ] Custom typing-themed sprites (replace alien sprites with letter-themed enemies?).
- [ ] Stats tracking: WPM, accuracy, longest streak.
- [ ] Difficulty selector on title screen (easy/normal/hard alters spawn rate + word length distribution).

---

## 6. Pitfalls and notes for future-me

- **All in-game text is uppercase.** Project-wide rule (see Q7). Every string that gets rendered to the screen — alien words, the typing buffer, HUD score, "GAME OVER", leaderboard initials — must be uppercased before ``font.render``. Word comparisons against typed input are case-insensitive. Storing words lowercase on disk is fine; just `.upper()` at render time and at compare time. If you find a bare ``font.render(some_string, ...)`` that hasn't been uppercased, that's a bug.
- **Don't dump `legacy/` files into context.** They're long. Read the specific class or function you're porting, not the whole file. Use `Grep` and `Read` with `offset`/`limit`.
- **Settings discipline.** The Refactoring Rules in `docs/TESTING.md` say no magic numbers — everything tunable goes in `settings.py`. Keep that habit; Star Hero's `settings.py` is well-organized and worth emulating.
- **CHANGELOG discipline.** Every code change gets an entry. See `docs/CHANGELOG.md` for the format.
- **The legacy alien spawn rate is way too fast for typing.** Star Hero's `AlienSettings.SPAWN_RATE = 600` (ms) means an alien every 0.6 seconds, plus `MIN_SPAWN_RATE = 150`. For typing, start at 3000+ ms and scale down slowly.
- **Star Hero's `Player.update()` is 500 lines of input handling.** Do not port it. The new Player is essentially a static sprite.
- **Word collisions.** If two aliens happen to share a starting letter, prefix-locking is ambiguous. Either prevent duplicate-starting-letter spawns at high alien-on-screen counts, or pick the lowest-y alien on tie-break (the most urgent target). Worth discussing at Stage 3.
- **Pygame text rendering is per-frame work.** If we render every alien's word every frame with `font.render`, it's fine at 60 FPS for a few aliens, but cache the rendered surface on the Alien sprite if performance matters later.
- **Frankie is also using `Enter` for the active in-game pause + the restart confirm + the initials submit in legacy.** With Enter now meaning "fire the laser," this needs rework — pause likely moves to Esc (currently a hard quit in legacy), restart confirm stays Enter only on inactive screens, initials submit stays Enter.
- **`legacy/.gitignore` and the root `.gitignore` both exist.** TODO note from the previous version of this file said "combine them." Look at both during Stage 0.

---

## 7. Misc / parking lot

- Combine `.gitignore` files (root + `legacy/`) — one of the original TODOs.
- Decide whether `legacy/` should be in `.gitignore` or committed. Probably committed for now (so future-me can read it on a fresh clone), then deleted entirely once we're done.
- Once Stage 0 lands, delete `legacy/__pycache__/` directories from disk (they're already gitignored but they're noise on local greps).
