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

**What stays from Star Hero (added on Stage 7 review):** per-color alien movement
patterns — yellow zigzag, blue fastest, etc. — are *not* cut. The original Star
Hero "feel" (Frankie's note: "be faithful") is a guiding principle, and the four
alien colors carrying distinct motion is part of that feel. Per-color SPEED bands
land in Stage 7 alongside POINTS (Q6's color-as-difficulty contract); the
yellow zigzag and any other shape-of-motion variation lands in a follow-up step
(see Stage 7 entry / Stage 10 polish).

**What gets cut (for now, may revisit):**
- Confusion attack (blue alien beam). Could be reimagined as letter-scrambling later.
- Most powerups — rework them as typing-flavored buffs in a later stage.

---

## 3. Open design questions

These are the questions we deferred. Resolve them with Frankie before starting the stage that depends on them.

### Q1. Ship behavior
Options on the table:
- **(a) Static ship, laser appears on completion.** Ship sits centered at the bottom; laser shoots straight up or arcs to the targeted alien. Simplest.
- **(b) Static ship that auto-rotates to aim at the targeted alien before firing.** Visually satisfying, more code.
- **(c) No ship at all, laser materializes at the bottom of the screen.** Most minimal, loses some visual interest.
- **(d) Static ship, laser spawns from the bottom and homes in on the targeted alien.** *(Added Stage 7 review.)* Frankie's read: a teleporting ship that snaps under each new target reads as jank, and any "ship moves → fires → travels → kills" animation adds delay between Enter and the kill. Spawning the laser from the bottom (or from a static ship's nose) and letting it home in keeps the kill feel snappy without the snap-around.

**Open sub-question for (d):** the homing laser still has flight time, so a fast-falling alien near the bottom might cross the screen edge before the laser reaches it. Two ways to interpret that:
- **Soft "point of no return":** if the alien is too low when Enter fires, the laser misses (the kill is registered as a miss). The player effectively has *less* than the full screen-height to type each word — the threat zone starts above the screen edge. This adds skill depth: experienced players read the screen and prioritize bottom aliens.
- **Always-hit:** the laser homes regardless of distance and always lands. Simpler. The "miss when off-screen bottom" rule from Stage 5 stays the only failure mode.

Recommendation, parking for now: **(d) with always-hit homing for v1**, revisit "point of no return" once core loop is fun. (a) is still the cheapest v1 if (d) feels expensive; (b) is the polish version of (a).

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

**Stage 7 update:** combined with Frankie's "be faithful to the original" note (see
§8 Observations) and the per-color motion patterns from Star Hero, color now
carries *three* axes of difficulty: word length (this question), fall speed
(per-color SPEED, ported from legacy `AlienSettings.SPEED`), and motion shape
(yellow zigzag, etc.). Stage 7 lands per-color SPEED + POINTS; the word-length
band is deferred to Stage 10 (needs per-difficulty word lists in
`assets/words.txt` to be split — separate work).

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

### Q11. Word readability when many aliens are on screen
*Raised at Stage 7 review.* At the current `WordSettings.SIZE = MEDIUM`, a 7-letter
word is ~140 px wide — that's almost a quarter of the 600 px screen. As the
spawn rate ramps in Stage 7 and aliens cluster, neighboring words can overlap
and become unreadable. Options to investigate:
- **Scale font with word length.** Shrink longer words so they all occupy roughly
  the same on-screen width. Pro: predictable layout. Con: short words read as
  "louder" than long words, which inverts the difficulty signal (long word
  should *feel* harder, not smaller).
- **Lanes.** Slow / straight-falling aliens (red, green) get assigned to one of
  N vertical lanes at spawn. Within a lane they never overlap horizontally
  because spawn x is locked to the lane. Yellow zigzag aliens (per Q6) drift
  across lanes and are accepted as the "uncatchable in a lane" exception.
- **Spawn-time x-distance check.** Reject a spawn x that's within `WORD_WIDTH`
  pixels of any other alien at the same y-band. Cheaper than lanes; degrades
  gracefully when many aliens are on screen (just skips that spawn tick).
- **Vertical word offset variance.** Render some alien words above and others
  below the sprite, so two aliens stacked vertically don't have their words
  collide. Lightweight first pass.

Recommendation, no decision: try the **spawn-time x-distance check** first — it's
the smallest code change and addresses the worst case (two aliens spawning at
adjacent x). If clusters at high difficulty still overlap, escalate to lanes.

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

### Stage 4 — Word list + spawning over time ✅
**Goal:** Aliens spawn at the top of the screen at intervals, each picking a random word from `assets/words.txt`. They still don't move.

**Steps:**

- [x] 1. Add `assets/words.txt` with 50–100 short common words.
- [x] 2. `WordManager` loads the file at boot and serves random words on demand. Ensure no duplicate words on screen at once (otherwise prefix-locking is ambiguous).
- [x] 3. Port a stripped `SpawnDirector` from `legacy/systems/managers.py` that fires a pygame timer event every N ms and spawns one alien at a random x position near the top.
- [x] 4. Smoke test: aliens appear at the top every couple seconds, with unique words. Typing still works against any of them.

**Resolution this stage:** the word pool lives on `WordManager` (rather than a separate `WordPool` class) — the manager already owns prefix state and the pool is the same shape of "give me the next word for the typing flow," so co-locating them keeps the systems folder lighter. `WordManager.pick_word(in_use)` is the single read path; the `in_use` set is built by the caller as `{a.word for a in aliens}` so the manager never has to know about pygame sprite groups. Duplicate-word avoidance is per-spawn-tick (filter the pool against the on-screen set) rather than a stateful "checkout/checkin" — simpler and means a killed alien's word is automatically eligible to spawn again on the next tick. **`SpawnDirector` is a 70-line port** vs the legacy 145-line version — alien-fired lasers, drop-table rolls, and `adjust_difficulty` all stayed in legacy (lasers + drops are forever-cut per §2; difficulty scaling lives in Stage 7). The director takes no `game` reference: each `spawn(aliens, word_manager)` call gets its dependencies passed in, which keeps it trivial to construct in tests.

**Tunables landed:** `WordSettings.WORDLIST_PATH`, plus a new `SpawnSettings` carrying `SPAWN_RATE = 3000` ms (per §6 pitfall: "legacy 600 ms is way too fast for typing"), `SPAWN_Y = 80` (visible top band — Stage 5 will move this above the screen once aliens fall), `X_MARGIN = 80` (keeps the longest words from clipping), and `COLORS = ('red', 'green', 'yellow', 'blue')` picked uniformly. Color-keyed difficulty bands (Q6) deferred to Stage 7+.

**`Stage3Layout` deleted** as planned in the Stage 3 entry. **First-frame spawn** is called once after `SpawnDirector()` so the screen isn't blank for the first 3000 ms after boot — the timer still drives every subsequent spawn. **Pool exhaustion is a silent no-op** in `pick_word` (returns `None`) rather than a crash; the director skips that tick and the next on-screen completion frees a word naturally.

### Stage 5 — Aliens fall + miss mechanic ✅
**Goal:** Aliens drift downward. Reaching the bottom edge counts as a miss (just print "miss" for now).

**Steps:**

- [x] 1. Port the alien movement loop from `legacy/core/sprites.py` `Alien.calculate_movement` — vertical-only for now, slow speed (start with `1` px/frame at 60 FPS, tune later).
- [x] 2. When `alien.rect.top > ScreenSettings.HEIGHT`, trigger a miss callback and `alien.kill()`.
- [x] 3. If the killed alien was the active target, clear the lock.
- [x] 4. Smoke test: aliens fall slowly, untyped aliens disappear off the bottom and print a miss.

**Resolution this stage:** ported the smallest possible slice of `Alien.calculate_movement` — vertical-only, no zigzag, no confusion-stall — into a new `Alien.update()` that does just `self.position.y += AlienSettings.SPEED; self.rect.y = round(self.position.y)`. The legacy `apply_movement(dx, dy)` helper is collapsed into the one motion that matters here (Typing Hero aliens never move horizontally per §2). `pygame.math.Vector2` is added on the sprite so the sub-pixel `SPEED = 0.5` actually accumulates — adding 0.5 to an int rect every frame would oscillate between 0 and 1 px deltas depending on rounding direction; the float accumulator gives the smooth 0/1/1/0/0/1 pattern that reads as steady descent at 120 FPS. The miss callback is **inlined in `main.py`** rather than passed to the Alien — `Alien.update()` doesn't know about `WordManager`, and putting the kill in the sprite would force that coupling. Order in the miss block: lock-clear (if the missed alien was the target) → `alien.kill()` → `print("miss")` so `WordManager` is never holding a dead reference between frames.

**SPEED chosen, color-bands deferred.** `AlienSettings.SPEED = 0.5` is uniform across all four colors — the §5 step 1 hint of "1 px/frame at 60 FPS" translates to 0.5 px/frame at this project's 120 FPS. Per-color bands (red slow, blue fast — Q6's color-as-difficulty tie-in) are deferred to Stage 7 alongside `POINTS` so the harder-color = higher-reward contract lands in one pass. Time-to-miss at SPEED=0.5 from `SPAWN_Y = 80` is ~12.5 seconds (verified by a pure-Python simulation of the float accumulator, no pygame), which is on the slow side of §6's "8–10 s window" but a fine starting point — Stage 6's tuning checkpoint after hearts land is the right place to tighten it once a miss actually costs something.

**`SPAWN_Y` stays at 80 (visible top band), not pushed negative as the Stage 4 entry hinted.** The original plan was to flip it negative so aliens "fall *into* the screen," but the word floating above an alien is a key gameplay element — spawning the sprite with its top at y=0 means the word above it is *off-screen*, and the player can't read what to type until the alien has fallen far enough for the word to clear y=0. With Stage 5's slow descent that takes a few seconds, which feels worse than just spawning visibly. So aliens spawn fully readable at y=80 and have ~12 s to be typed before they cross the bottom. The Stage 4 first-frame-spawn behavior also keeps working unchanged.

**`Alien.update()` is its own function, not folded into `draw_word`.** Per the Refactoring Rule "Keep functions organized and grouped by role; the `update` and `run` functions ... do as little as possible — only call other functions if possible." Stage 5's `update` is a 2-liner today; Stages 7 (difficulty multiplier) and 8 (frame-cycle animation) will grow it by adding more *calls*, not more inline logic.

### Stage 6 — Hearts + game over ✅
**Goal:** Hearts HUD in top-right. Each miss removes one. Zero hearts → game over screen → restart.

**Steps:**

- [x] 1. Port heart rendering from `legacy/ui/style.py` (`display_hearts`).
- [x] 2. Add a `hearts` counter in main; decrement on miss. At zero, set `game_active = False`.
- [x] 3. Show a minimal "GAME OVER — press Enter to restart" screen.
- [x] 4. On Enter from game-over, reset hearts, clear aliens, set `game_active = True`.
- [x] 5. Smoke test: misses subtract hearts; at zero, game-over appears; Enter restarts.

**Resolution this stage:** the heart-rendering port lives in a new `ui/hud.py` as `HeartsHUD` — a small class that loads `assets/graphics/heart.png` once at construction and on each frame walks the row left-to-right blitting one icon per remaining heart. Mirrors `legacy/ui/style.py` `display_hearts` but stripped of the `Style` god-object it was a method on (legacy `Style` also drew the title, the player ship, the boost meter, the bombs row, the volume bar, the leaderboard, the score readout — Stage 6 needs none of those). The same module also gets a `GameOverScreen` class that pre-rasterizes the "GAME OVER" banner and "PRESS ENTER TO RESTART" prompt at construction so the per-frame draw is two pure blits — the text never changes between frames, so paying `font.render` once at boot is strictly better than redoing it every tick. **Co-locating both in `hud.py`** rather than splitting `hud.py` + `game_over.py` keeps `ui/` lean while only two HUD pieces exist; Stage 9's intro/game-over port likely splits this into `hud.py` (in-game) + `menus.py` (overlays) once the intro screen, score/high-score readouts, and initials entry land.

**`hearts` + `game_active` live in `main.py`, not on a manager.** The temptation was to introduce `SessionStateManager` here so the gating concern lived in one place — but the legacy version of that class also owns intro music + pause routing + the "first frame after restart" arrow, all of which are Stage 9 concerns. Pre-wiring it now would mean writing a stub that does almost nothing, then rewriting it in Stage 9 once the other states arrive. Two locals on `run()` are good enough for one stage; Stage 9's `SessionStateManager` port pulls the flag in then. **Spawn timer keeps ticking on game-over** but the spawn handler is gated on `game_active` — restarting picks up the same cadence without re-arming, and the next on-game-over tick is silently dropped. **Aliens freeze in place behind the banner** rather than disappearing because we still call `aliens.draw(screen)` and `draw_word(...)` while skipping `aliens.update()`; the frozen scene reads as "this is the run you just finished" which is more informative than a black background. **Restart order:** clear alien group → clear lock (idempotent — already cleared at game-over) → refill hearts → kick a fresh first-frame spawn → flip `game_active` back on. Matches the Stage 4 first-frame-spawn behavior so the restarted run isn't blank for `SPAWN_RATE` ms. **Game-over keypress filter** ignores everything except Enter and ESC — a player still tapping at the keyboard when they died can't accidentally plant a half-typed prefix that'd carry over into the next run.

**Miss path order matters.** Inside the `for alien in list(aliens):` scan: lock-clear → `alien.kill()` → `print("miss")` → `hearts -= 1` → check for game-over → `break`. The `break` is new — once the run is over, additional misses in the same frame don't matter and shouldn't print extra "miss" lines or further decrement past zero. The `print("miss")` Stage 5 placeholder stays for now (smoke-test parity); Stage 8's audio hook will replace it with a SFX cue.

**Tunables landed:** `HeartSettings` (MAX = 3, TOP_MARGIN = 8, RIGHT_MARGIN = 30, SPACING = 10 — geometry mirrors legacy `UISettings.HEART_*` exactly so the row sits in the same visual slot Star Hero players were used to), and `GameOverSettings` (BANNER_TEXT = "GAME OVER" at LARGE, PROMPT_TEXT = "PRESS ENTER TO RESTART" at MEDIUM, BANNER_OFFSET = 40 above center, PROMPT_OFFSET = 30 below center). The legacy `UISettings` carried boost-meter / status-row / bombs-row constants too — those are forever-cut per §2 and don't make the trip.

**Tuning checkpoint.** Play it. Are misses too punishing? Adjust alien speed and spawn rate before moving on. (Q5.) Time-to-miss is currently ~12 s per alien at `AlienSettings.SPEED = 0.5`; with 3 hearts that's a generous window before the run ends. If it feels too long (run never ends in practice), bump SPEED first, then SPAWN_RATE down. If it feels too short (every miss compounds before you can read the next word), lower SPEED to 0.4.

### Stage 7 — Score + simple difficulty ramp (SOME CREATIVE DECISIONS HAVE BEEN MADE AHEAD OF THIS THAT WERE NOT ADDED TO THE CHANGELOG, SUCH AS ADDING THE LASER, ALIEN NO LONGER STOPS MOVING WHEN TARGETED, EXPLOSION AND BACKGROUND 






ANIMATIONS, SOUND EFFECTS, ETC. CHECK THE CODE FIRST AND ADAPT! IT MIGHT HAVE BEEN MESSY SO REFACTOR IF NECESSARY BUT KEEP FUNCTIONALITY)
**Goal:** Word kills award points (varied by alien color). Score visible top-left. Per-color fall speed lands so the four colors carry distinct motion identity. Spawn rate ramps down as score climbs.

**Steps:**

- [ ] 1. Port `ScoreManager` from `legacy/systems/managers.py` — score field, JSON save/load to `high_score.txt`, `reset()` for new runs. **Defer the initials entry flow to Stage 9** (TODO §5 Stage 9 specifically owns "if keeping leaderboards, port `ScoreManager` initials entry path"). Stage 7 only needs the score and the high-score persistence.
- [ ] 2. Award points per kill via `AlienSettings.POINTS[color]`. Per-color values mirror legacy (red 100, green 200, yellow 300, blue 500) — see §8 O1 ("be faithful"). Word-length bonuses (Q6's other axis) deferred to Stage 10 alongside the per-difficulty word lists.
- [ ] 3. Promote `AlienSettings.SPEED` from a single float to a per-color dict (red < green < yellow < blue). Values scaled from legacy 60-FPS numbers down for typing pace — the harder-color = faster + more-points contract from Q6 lands here in one pass. Yellow zigzag motion (per Frankie's note 2 / §2 update) is a follow-up step deferred to Stage 8 polish; Stage 7's yellow falls straight down, just faster than green.
- [ ] 4. Add `ScoreHUD` in `ui/hud.py` — top-left, mirrors legacy `display_in_game_score` (small high-score row, medium current-score below).
- [ ] 5. Port `SpawnDirector.adjust_difficulty` — every `ScoreSettings.DIFFICULTY_STEP` points, drop spawn interval by `SPAWN_RATE_DROP` (clamped to `MIN_SPAWN_RATE`). Re-arm the pygame timer with `pygame.time.set_timer`. Per-frame *fall* speed scaling deferred — per-color SPEED already gives the difficulty gradient in step 3, and adding a multiplier on top makes balance tuning a two-knob problem.
- [ ] 6. Smoke test: score climbs, high-score persists across restarts, spawn rate visibly tightens at the first difficulty step, the four colors fall at visibly different speeds, ramp tops out without becoming unplayable.

### Stage 8 — Audio + explosion polish
**Goal:** Laser SFX on kill, explosion sprite + SFX at killed alien's position, background music.

**Steps:**

- [ ] 1. Port `Audio` system from `legacy/systems/audio.py`. Drop powerup-related cue keys we don't use.
- [x] 2. Port `Explosion` sprite from `legacy/core/animations.py`.
- [x] 3. On a successful kill: spawn an explosion at the alien's position, play `explosion`. Also play `laser` sound (consider: does laser play on key-press, on full-word completion, or both? Probably full-word.).
- [ ] 4. Start `star_hero.ogg` BGM on game start. (Optionally re-theme the music later.)
- [ ] 5. Port `Background` scroll + `CRT` shader for visual flavor (later BG and aliens will move faster with levels, also harder words on harder levels?)
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

---

## 8. Observations

Curated, durable design-direction notes — distilled from Frankie's brainstorming
into a stable home so future passes don't have to re-derive them. Each entry is
a guiding principle that influences several stages, not a single-stage TODO.

### O1. Be faithful to how Star Hero *felt*
The "feel" of the original game is a guiding principle, not just nostalgia:
the same sound effects on the same beats, the same visual effects (CRT,
explosions, the four alien colors), and a scoreboard that reads in the same
visual slot. Concretely, this means:
- **SFX:** reuse the legacy `assets/audio/` files — laser, explosion, alarms,
  unpause cue. Don't rescore. Stage 8.
- **Visuals:** keep the CRT shader, the scrolling starfield, the alien-color
  palette, the explosion spritesheet. All ports, no redesigns.
- **Scoreboard:** top-left score readout (legacy `display_in_game_score`) and
  the high-score / leaderboard layout from `legacy/ui/style.py`. Stage 7 / 9.
- **Per-color alien identity:** red / green / yellow / blue are not
  interchangeable. Each color has its own *speed*, its own *motion pattern*,
  its own *point value*, and (eventually) its own *word-difficulty band* — and
  the relationships between them (yellow zigzags, blue is fastest) port from
  Star Hero verbatim. See §2 / Q6 / Stage 7.

### O2. Snappy kill feel beats elaborate kill animation
Frankie's read on the ship behavior question (Q1): any sequence of "ship
moves under target → fires → laser travels → alien dies" introduces delay
between the player pressing Enter and the alien being destroyed. That delay
is more punishing than a simpler-looking kill. The chosen direction (Q1
option d) — laser spawns from the bottom and homes — keeps the visual
narrative ("you fired, it hit, it died") without making the player wait for
ship choreography. *Slight* travel time is fine and even desirable for the
"point of no return" mechanic; multi-step ship animation is not.

### O3. The screen has a finite readable budget
At spawn cadences the typing-game can sustain (Stage 7 difficulty ramp), the
screen will accumulate enough aliens that *word readability* becomes the
limiting factor before reflexes do. Future stages need to defend layout
explicitly — see Q11. This is a "design has implications" note, not a "do this
now" note: it informs spawn placement, font sizing, and any future word-length
distribution choices.

---

## 9. Issues

Concrete problems observed in the running game (or known to be lurking) that
need a fix in a future stage. Distinct from §3 (Open design questions, where
the *design* is unresolved) and §6 (Pitfalls, which are gotchas to remember,
not bugs). Move items here when they're actionable bugs / layout problems /
balance complaints, not when they're still open questions.

*(None yet at Stage 7 start. The Q11 word-readability concern lives in §3 as a
design question rather than here because the *behavior* isn't observed-broken
yet — the spawn rate at 3000 ms is currently slow enough that overlap is rare.
Promote to §9 once Stage 7's faster spawn rates make it visible.)*

---

## 10. Brainstorm scratch

Free-form brainstorming dump for Frankie. Drop raw thoughts here without
worrying about organization — each pass, the working session promotes them
into §3 (questions), §8 (observations), §9 (issues), or directly into a
stage's plan. Items that have been promoted get checked off and stay here as
a paper trail; items still raw stay un-checked.

- [x] Try to be faithful to how the original game felt, same sound effects,
  visual effects, scoreboard, etc. → **promoted to §8 O1.**
- [x] Aliens should move in patterns just like the original game (yellow
  zigzag, blue the fastest, etc). → **promoted to §2 ("What stays from Star
  Hero, added on Stage 7 review") + Q6 update + Stage 7 plan (per-color SPEED
  + POINTS) + Stage 10 (zigzag motion port).**
- [x] Instead of the player ship moving / "teleporting" around the bottom of
  the screen and shooting aliens — any animation is a delay between Enter and
  the kill — perhaps lasers just appear from the bottom of the screen and
  home in on moving aliens. There will still be a slight "delay" but for
  visual effect that is okay. The player doesn't have until the alien
  *touches* the bottom, just until it's *too far for the laser to reach*
  (point of no return). → **promoted to Q1 (new option d + sub-question on
  point-of-no-return) + §8 O2.**
- [x] Words might be too big? When words get longer, shrink them? What
  about when there are multiple aliens on screen — should the slow
  straight-down movers have lanes so the words stay readable? → **promoted to
  Q11.**

*(Add new raw notes below this line — anything goes. Future passes will
organize them.)*