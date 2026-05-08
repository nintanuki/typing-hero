# Typing Hero — Testing Playbook

This file is the manual smoke-test manual for Typing Hero. It is **the** source of truth for "did this change break anything." The fast gut-check version lives in [.github/copilot-instructions.md](../.github/copilot-instructions.md); everything below is the full per-stage playbook.

> **Coding rules** — PEP-8, naming, banner style, docstrings, ALL CAPS UI, etc. — live in [.github/copilot-instructions.md](../.github/copilot-instructions.md), not here.

---

## How to use this document

1. **Before writing code:** read [.github/copilot-instructions.md](../.github/copilot-instructions.md), [docs/TODO.md](TODO.md), [docs/ARCHITECTURE.md](ARCHITECTURE.md), and the recent entries in [docs/CHANGELOG.md](CHANGELOG.md) so you know what should still work.
2. **After every meaningful edit:** boot the game (`python main.py`) and run **Cross-cutting checks** below. They take under a minute and catch the most common regressions (boot crashes, audio failures, fullscreen toggle, ESC).
3. **When a change touches a system:** also run the per-stage section that owns that system. The stages are written in the order the game grew, so a Phase-2 spawn-system change should pass every check from Stage 0 through Stage 4.
4. **When you find a regression:** open an item under **Known issues** in [docs/TODO.md](TODO.md), and log the finding in [docs/CHANGELOG.md](CHANGELOG.md). Don't silently leave a stage failing.
5. **A stage with `✅` was passing as of the most recent change to its system.** If a checkbox below stops being true after your edit, the change is incomplete.

The stage numbers (Stage 0 ... Stage 9) are historical milestones referenced throughout the changelog. They map onto the phases in [docs/TODO.md](TODO.md) like this: Stages 0–2 = Phase 1, Stages 3–6 = Phase 2, Stages 7–9 = Phase 3.

---

## Cross-cutting checks (run after every meaningful change)

These are state-agnostic — every one of them should be true regardless of which subsystem you touched.

* `python main.py` boots without a traceback.
* The 600×800 window opens with the title bar reading "Typing Hero".
* Intro music plays on the title screen; pressing `Enter` starts a run and BGM takes over.
* `F11` toggles fullscreen and back without losing audio or freezing.
* `ESC` closes the window cleanly from any state (intro, playing, paused, game over).
* No new magic numbers in code outside `settings.py`.
* No new tracebacks printed during a normal run cycle (intro → play → game over → restart → quit).

---

## Stage 0 — Scaffold ✅

* `python main.py` opens a 600×800 window titled "Typing Hero"
* Window background is solid black (no errors blitting nothing)
* `ESC` closes the window cleanly
* Closing the window via the OS chrome closes the process cleanly
* No tracebacks on startup or shutdown

## Stage 1 — One alien, one word ✅

* All Stage 0 checks still pass
* A single alien sprite is visible at center-screen
* The word "hello" is rendered above the alien in the Pixeled font
* Sprite and text remain visible across multiple frames (no flicker)

## Stage 2 — Type to destroy ✅

* All previous checks still pass
* Letter keystrokes are echoed to a debug area on screen (bottom-center, uppercase)
* Typing the full word destroys the targeted alien immediately (no `Enter` required)
* Typing a letter that would match no candidate alien is ignored (buffer does not advance)
* `Backspace` deletes the most recent character
* All on-screen text renders in UPPERCASE — alien word, typing buffer, and any future HUD strings must all be uppercase before they hit `font.render`

## Stage 3 — Multiple aliens + prefix-locking ✅

* All previous checks still pass
* Three aliens visible with three different words and different first letters (`HELLO` / `WORLD` / `TYPE`, red / green / yellow, evenly spread across the upper third)
* Targeting uses soft-lock behavior: typing a shared first letter keeps multiple matching candidates alive rather than hard-locking permanently
* While ambiguous, the provisional focus is the lowest matching alien (closest to the bottom)
* The bottom-of-screen typing buffer mirrors the typed prefix in real time
* Typing the next disambiguating letter automatically shifts focus to the correct alien (e.g., `A` ambiguous between APPLE/ARROW, `AP` -> APPLE, `AR` -> ARROW)
* While typing, a letter that would leave zero matches is ignored (no penalty, no lock reset)
* Completing the focused word destroys the alien and clears typing state
* `Backspace` shrinks the typed prefix by one letter; emptying the buffer releases the lock

## Stage 4 — Word list + spawning ✅

* All previous checks still pass
* One alien is on screen within the first frame after launch (initial spawn) so the player isn't staring at black until the first timer tick
* Subsequent aliens spawn at the top at the `SpawnSettings.SPAWN_RATE` interval (default 3000 ms — visibly "every couple seconds")
* Each alien gets a random word from the active difficulty band (`assets/words/band{N}_*.txt`); rendered uppercase
* No two on-screen aliens carry the same word at the same time — verifiable by watching a few spawn cycles and confirming every visible word is unique
* Aliens spawn at varied x positions across the playfield (not all stacked at one column); the X_MARGIN keeps the longest words from clipping the screen edge
* Two aliens whose words start with the same letter still resolve correctly: shared prefixes stay soft-locked, and provisional focus favors the lower alien until disambiguated
* If every word in the active band is on screen at once, `WordManager.pick_word` falls back to the union of all bands; if even that is exhausted, the spawn tick is a silent no-op rather than a crash or duplicate

## Stage 5 — Falling + miss ✅

* All previous checks still pass
* Aliens drift downward smoothly at `AlienSettings.SPEED` (no visible stutter — the float `Alien.position` accumulator means SPEED=0.5 advances rect.y by 1 px every other frame on average, not by 0/1 alternating in a jittery pattern)
* Each spawned alien takes roughly 12 s to traverse from spawn band to bottom edge at level 1 (slow enough to read and type comfortably)
* When an alien's top edge crosses below `ScreenSettings.HEIGHT` the sprite is removed and the miss penalty is applied
* If the alien that just fell off was the active typing target, the prefix lock clears and the bottom-of-screen typing buffer empties — the next letter the player presses re-acquires from scratch
* If a *non-targeted* alien falls off, the active lock is undisturbed (verifiable by typing partway into one alien's word, then letting an unrelated alien fall: the cyan/white split on the locked alien stays exactly as it was)
* Aliens still spawn at `SpawnSettings.SPAWN_Y` so the word floating above is fully on-screen from the moment of spawn

## Stage 6 — Hearts + game over ✅

* All previous checks still pass
* Hearts HUD renders in the top-right starting at `HeartSettings.MAX` icons (3) — row pinned to the right edge with `RIGHT_MARGIN` clearance, `SPACING` between adjacent hearts, sitting `TOP_MARGIN` below the screen top
* Each miss decrements one heart from the *left* of the row (rightmost icon is the last to disappear) — verifiable by letting three aliens fall in a row and watching the row shrink one slot per miss
* At zero hearts the run flips into game-over: aliens, lasers, and powerups freeze; the spawn timer ticks are dropped; the typing buffer + hearts HUD stop drawing; a centered "GAME OVER" banner + restart prompt overlay draws on top of the frozen playfield
* The active typing lock (if any) is cleared the moment hearts hit zero, so the game-over screen never shows a leftover cyan prefix on a frozen alien
* On the game-over screen, every key except the legitimate game-over controls is ignored — letter taps don't plant a half-typed prefix that'd carry over into the next run
* `Enter` from the game-over screen clears all on-screen aliens, refills hearts to `HeartSettings.MAX`, kicks a fresh first-frame spawn, and flips state back to `'playing'`
* `ESC` still closes the window cleanly from both the live-run state and the game-over state

## Stage 7 — Score + difficulty ramp ✅

* All previous checks still pass
* `SCORE: 0` and `HIGH SCORE: <persisted>` both render in the top-left at boot — small `HIGH SCORE` row at the very top, larger `SCORE` row directly below; both uppercase
* Killing a red alien adds 100, green adds 200, yellow adds 300, blue adds 500 — verifiable by typing one word of each color and watching the readout step
* The four alien colors fall at visibly different speeds: red slowest, green medium, yellow faster, blue fastest — easy to confirm by spawning a few of each and watching them reach the bottom in order
* On crossing each level threshold (`ScoreSettings.LEVEL_SCORE_THRESHOLDS`), the spawn interval visibly tightens and the alien-speed multiplier nudges up
* The ramp tops out at "challenging but doable" — at full ramp the screen is busy but a competent typist can keep up
* On game-over, the score is written to `high_score.txt` at the project root — verifiable by looking at the file after death
* If the just-finished run beat the previous high score, the next boot reads it back: the `HIGH SCORE` row in the top-left shows the new record from the title frame onward
* Pressing `Enter` from the game-over screen zeroes `SCORE` (high score row stays) *and* re-arms the spawn timer to the base interval — the restarted run starts at the easy cadence even if the previous run was at full ramp
* If `high_score.txt` is missing (fresh install) or corrupt, boot proceeds without crashing — the `HIGH SCORE` row reads `0` until the first run completes

## Stage 8 — Audio + explosion ✅

* All previous checks still pass
* Laser SFX plays on word completion (`laser` normally, `hyper` at max laser tier)
* Explosion sprite + SFX plays at the killed alien's position
* Intro music plays on title screen; BGM plays during runs; game-over music plays after death
* `Enter` pause/unpause correctly pauses/resumes the run music channel
* Low-hearts alarms play at 2 and 1 hearts, and alarms stop on game over/restart
* No audio stutter or duplicate-play artifacts across kill/pause/game-over transitions

## Stage 9 — Menus + leaderboard ✅

* All previous checks still pass
* Title screen shows on launch with "PRESS ENTER TO BEGIN" prompt
* Game-over screen shows final score and high score
* If score qualifies, initials entry appears (arrow keys cycle, `Enter` submits)
* Pause: `Enter` toggles pause during active gameplay; `Enter` resumes from pause
* During initials entry, only initials controls (`UP` / `DOWN` / `LEFT` / `RIGHT` + `Enter`) are accepted
* Full loop is reachable: title → play → game over → (initials) → title

## Phase 4 — V2 polish (per feature)

Add a per-feature checklist here as each Phase 4 item lands. Until then, the items in [docs/TODO.md](TODO.md) §"Phase 4" carry no smoke tests yet.

---

## Powerup smoke tests (current implementation)

Powerups are implementation-complete (Phase 3 carryover) and should always pass these checks:

* **Heart drop** (red alien) — drops only when `hearts < HeartSettings.MAX`; on bottom contact, hearts increment and `powerup_heart` SFX plays.
* **Shield drop** (red alien) — drops only when no shield is active; on bottom contact, the shield activates for `ShieldSettings.DURATION_MS`, the blue vignette pulses, and bottom-of-screen alien hits become shielded kills (explosion + score, no heart cost).
* **Laser-tier upgrade** (green alien) — drops only below `PowerupSettings.MAX_LASER_LEVEL`; on bottom contact, laser tier increments and `powerup_twin` SFX plays. At max tier, completing a word fires `hyper` SFX instead of `laser`.
* **Burst** (yellow alien) — drops only below `PowerupSettings.MAX_BURST_TIER`; on bottom contact, burst tier increments. Each kill schedules follow-up shots at the configured delays; follow-ups skip dead aliens silently.
* **Rainbow beam** (blue alien) — on bottom contact, a continuous wide cone fires from the bottom for `PowerupSettings.RAINBOW_BEAM_DURATION` ms; the `hyper` SFX sustains; lasers are piercing.
* **Damage flash** — every miss while not shielded and not invincible triggers a red→white screen-edge pulse for `DamageSettings.FLASH_DURATION` ms followed by an invincibility window.
* **Powerup-strip-before-heart** — while above default tier, the first hit strips laser tier + burst tier + cancels pending follow-ups instead of consuming a heart.

