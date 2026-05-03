# Testing Checklist

Run the relevant section after every change. Each stage in [`TODO.md`](TODO.md) ends with a smoke test that gets added here once the stage lands. Earlier stages stay in the list — anything that *was* working should *still* be working.

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
* Typing the alien's word + `Enter` removes the alien and prints `kill` to the console
* Typing a wrong word + `Enter` clears the input but leaves the alien intact
* `Backspace` deletes the most recent character
* All on-screen text renders in UPPERCASE (project-wide rule, see TODO Q7) — alien word, typing buffer, and any future HUD strings must all be uppercase before they hit `font.render`

## Stage 3 — Multiple aliens + prefix-locking ✅

* All previous checks still pass
* Three aliens visible with three different words and different first letters (`HELLO` / `WORLD` / `TYPE`, red / green / yellow, evenly spread across the upper third)
* Pressing the first letter of any word locks onto that alien — the typed letter shows in cyan above the alien, untyped letters stay white
* The bottom-of-screen typing buffer mirrors the typed prefix in real time
* While locked, pressing a letter that does not extend the locked word is ignored — the lock survives, the buffer does not advance, no penalty (Q3 v1 default)
* Letters that match no on-screen alien when no lock is active are silently ignored (no buffer growth, no lock acquired)
* Completing the locked word and pressing `Enter` destroys the alien, clears the lock, and prints `kill` to the console
* Pressing `Enter` on an empty or partial buffer clears the lock + buffer without firing (matches Stage 2's "Enter always commits" feel)
* `Backspace` shrinks the typed prefix by one letter; emptying the buffer releases the lock

## Stage 4 — Word list + spawning ✅

* All previous checks still pass
* One alien is on screen within the first frame after launch (initial spawn) so the player isn't staring at black until the first timer tick
* Subsequent aliens spawn at the top at the `SpawnSettings.SPAWN_RATE` interval (default 3000 ms — visibly "every couple seconds")
* Each alien gets a random word from `assets/words.txt` (lowercased on disk, rendered uppercase per Q7)
* No two on-screen aliens carry the same word at the same time — verifiable by watching a few spawn cycles and confirming every visible word is unique
* Aliens spawn at varied x positions across the playfield (not all stacked at one column); the X_MARGIN keeps the longest words from clipping the screen edge
* Two aliens whose words happen to start with the same letter still resolve correctly: pressing that letter locks onto the lower one (lowest-y tie-break from Stage 3)
* If every word in the list happens to be on screen at once, the next spawn tick is a silent no-op rather than a crash or duplicate

## Stage 5 — Falling + miss ✅

* All previous checks still pass
* Aliens drift downward smoothly at `AlienSettings.SPEED` (no visible stutter — the float `Alien.position` accumulator means SPEED=0.5 advances rect.y by 1 px every other frame on average, not by 0/1 alternating in a jittery pattern)
* Each spawned alien takes roughly 12 s to traverse from spawn band to bottom edge (slow enough to read and type comfortably; tune in Stage 6 once misses cost a heart)
* When an alien's top edge crosses below `ScreenSettings.HEIGHT` the console logs `miss` and the sprite is removed (no lingering off-screen corpses)
* If the alien that just fell off was the active typing target, the prefix lock clears and the bottom-of-screen typing buffer empties — the next letter the player presses re-acquires from scratch
* If a *non-targeted* alien falls off, the active lock is undisturbed (verifiable by typing partway into one alien's word, then letting an unrelated alien fall: the cyan/white split on the locked alien stays exactly as it was)
* Aliens still spawn at `SpawnSettings.SPAWN_Y = 80` so the word floating above is fully on-screen from the moment of spawn (Stage 4 first-frame-spawn check still passes)

## Stage 6 — Hearts + game over ✅

* All previous checks still pass
* Hearts HUD renders in the top-right starting at `HeartSettings.MAX` icons (3) — row pinned to the right edge with `RIGHT_MARGIN` clearance, `SPACING` between adjacent hearts, sitting `TOP_MARGIN` below the screen top
* Each miss decrements one heart from the *left* of the row (rightmost icon is the last to disappear) — verifiable by letting three aliens fall in a row and watching the row shrink one slot per miss
* At zero hearts the run flips into game-over: `aliens.update()` and the miss-detection loop both pause (any aliens still on screen freeze in place rather than vanish), the spawn timer keeps ticking but every tick is silently dropped, the typing buffer + hearts HUD both stop drawing, and a centered "GAME OVER" banner + "PRESS ENTER TO RESTART" prompt overlay draws on top of the frozen playfield
* The active typing lock (if any) is cleared the moment hearts hit zero, so the game-over screen never shows a leftover cyan prefix on a frozen alien
* On the game-over screen, every key except `Enter` and `ESC` is ignored — letter taps don't plant a half-typed prefix that'd carry over into the next run
* `Enter` from the game-over screen clears all on-screen aliens, refills hearts to `HeartSettings.MAX`, kicks a fresh first-frame spawn (so the restarted run isn't blank for `SPAWN_RATE` ms — same behavior as the boot-time first-frame spawn from Stage 4), and flips `game_active` back on
* `ESC` still closes the window cleanly from both the live-run state and the game-over state

## Stage 7 — Score + difficulty ramp (not yet built)

* All previous checks still pass
* Score increments per word killed, visible on the HUD
* High score persists across runs (JSON save from legacy `ScoreManager`)
* Spawn rate visibly increases as score climbs (clamped to a minimum interval)
* Game does not become unplayable — the ramp tops out at "challenging but doable"

## Stage 8 — Audio + explosion (not yet built)

* All previous checks still pass
* Laser SFX plays on word completion
* Explosion sprite + SFX plays at the killed alien's position
* Background music plays during a run, stops on game over
* Master volume can be adjusted with `+` / `-`
* No audio stutter or duplicate-play artifacts

## Stage 9 — Menus + leaderboard (not yet built)

* All previous checks still pass
* Title screen shows on launch with "press Enter to begin" prompt
* Game-over screen shows final score and high score
* If score qualifies, initials entry appears (arrow keys cycle, Enter submits)
* Pause: `Enter` pauses *only* when no word is currently being typed
* Full loop is reachable: title → play → game over → (initials) → title

## Stage 10 — V2 (per feature)

Add per-feature checks as features land.

---

# Refactoring Rules

These rules carry over from the Star Hero codebase and apply to all Typing Hero code. Read them before any non-trivial edit.

* Update `CHANGELOG.md` for every code change (timestamp, file, line numbers, before/after, why) including which AI model made the change. Read it first before making changes so you know the current state.
* All code must be PEP-8 compliant.
* Less code is better than more code, but clean and readable code is the best.
* Keep "middlemen" minimal — if A calls B, and all B does is call C, A should just call C.
* Keep code clean of dead imports, unused variables and functions, and legacy code.
* `GameManager` (or whatever the central coordinator is named) must be light — offload responsibilities to other classes.
* When possible, classes should communicate to each other through `GameManager`.
* Any new class or function names must clearly describe their function.
* Keep all constants declared in `settings.py`. Avoid magic numbers.
* All classes and functions must have a docstring.
* All docstrings must have a summary, `Args` (if applicable), and `Returns` (if applicable).
* Do not change function names unless their role is now completely different.
* Keep functions organized and grouped by role. The `update` and `run` functions in classes should be the last function and do as little as possible — only call other functions if possible.
* Do not change variable names if not necessary.
* Function and variable names must be descriptive.
* Do not remove comments.
* Comments must explain *why*, not just *what*.
* When making a change, do not leave a comment that a change was made — unless it was to fix a bug that wasn't obvious, in which case explain why something was done in an unconventional way.
