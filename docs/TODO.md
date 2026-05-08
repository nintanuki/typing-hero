# Typing Hero — Roadmap

This file tracks work in **phases**. Each phase has a clear goal; finish a phase before moving on. Items inside a phase can move between phases as priorities shift.

> **Status at time of writing:** Phases 1–3 are complete. The game is fully playable end-to-end (title → run → game-over → leaderboard → restart) with audio, CRT, four alien colors, prefix-locking typing, hearts, score + persisted high score, leaderboard initials entry, pause, difficulty ramp, and powerups. Phase 4 (V2 polish) is à la carte.

---

## Phase 1 — Scaffolding & first frame (complete)

**Goal:** Boot a Pygame window from an empty repo and have a single alien sprite with a typed word visible on screen. Establish the architecture skeleton before adding gameplay.

- [x] Create the empty Pygame window, title bar, black background, ESC-to-quit. *(was Stage 0)*
- [x] Render one alien sprite with the word "HELLO" floating above it in the Pixeled font. *(was Stage 1)*
- [x] Wire keyboard input through a `WordManager`: typing the full word destroys the alien; `Backspace` deletes a letter; non-matching letters are ignored. *(was Stage 2)*

## Phase 2 — Core gameplay loop (complete)

**Goal:** A run that is recognizably the game — multiple aliens, real word lists, falling motion, miss penalties, hearts, and a game-over state.

- [x] Multiple aliens on screen with prefix-locking and soft-lock targeting (lowest matching alien gets provisional focus while ambiguous). *(was Stage 3)*
- [x] Word list loaded from `assets/words.txt`; `SpawnDirector` ticks new aliens at `SpawnSettings.SPAWN_RATE`; first-frame spawn so the player never stares at an empty playfield. *(was Stage 4)*
- [x] Aliens drift downward at `AlienSettings.SPEED` using a `Vector2` accumulator (sub-pixel-honest). Aliens past the bottom edge are removed and consume one heart. *(was Stage 5)*
- [x] Hearts HUD in the top-right; zero hearts → frozen playfield + "GAME OVER" / "PRESS ENTER TO RESTART". `Enter` clears all sprites, refills hearts, kicks a fresh first-frame spawn. *(was Stage 6)*

## Phase 3 — Score, audio, menus & polish (complete)

**Goal:** All the systems that make the game feel finished — points, persistent records, sound, an actual title screen, leaderboard, pause, and the CRT look.

- [x] Score by alien color (red 100 / green 200 / yellow 300 / blue 500). Per-color falling speeds. Difficulty ramp by score threshold. High score persisted to `high_score.txt`. *(was Stage 7)*
- [x] Audio: laser SFX on word completion (`laser` normally, `hyper` at max laser tier), explosion SFX + sprite, intro music on title, BGM during runs, game-over music after death, low-hearts alarms at 2 and 1 hearts, pause/unpause cues. *(was Stage 8)*
- [x] Title screen, game-over screen with final score, initials entry (arrow keys + `Enter`), leaderboard, pause via `Enter` during gameplay. Full loop reachable: title → play → game over → (initials) → title. *(was Stage 9)*
- [x] Powerup drops implemented (heart, shield, laser-tier upgrade, burst, rainbow beam). Damage flash + invincibility window. Shield bottom-kill behavior. Word-difficulty bands by level (`assets/words/band1..5_*.txt`).

## Phase 4 — V2 polish (à la carte)

**Goal:** Make Typing Hero feel like a finished arcade product. Items in this phase are **independent** — pick whichever feels right and do them in any combination. Nothing in Phase 4 blocks the game from being playable.

### 4a. Powerups & status effects

- [ ] Pick the final powerup catalog and tune drop rates. The current set (heart, shield, laser-tier, burst, rainbow beam) is implementation-complete but not balance-frozen — see Q8 below.
- [ ] Status effect: blue alien letter-scramble debuff (target word's letters render in randomized order while active). Decide design first — see Q9.

### 4b. Motion & layout

- [ ] Yellow alien zigzag motion faithful to Star Hero's per-color pattern (current frame-counter flip is close; sine-wave variant is on the table).
- [ ] Word readability defense at high spawn rates — spawn-time x-distance check OR fixed lanes — see Q11.
- [ ] Migrate alien descent and laser travel to `delta_time`-driven motion so framerate scaling no longer changes game speed. *(Architecture §13.)*

### 4c. UX & meta

- [ ] Stats screen on game over (WPM, accuracy, longest streak).
- [ ] Difficulty selector on the title screen (easy / normal / hard adjusts spawn rate + word band).
- [ ] Re-theme music if `star_hero.ogg` no longer fits.
- [ ] Custom typing-themed sprites (letter-themed enemies?).
- [ ] Move initials row up a bit, or leaderboard down — current layout has a stray blue line.
- [ ] Smoother shield overlay (gradient/fade) instead of solid blue; preserve fast end-of-duration flash.
- [ ] Optional manual target cycling as accessibility fallback for soft-lock ambiguity in dense waves (off by default).

### 4d. Repo housekeeping

- [ ] Combine root `.gitignore` and `legacy/.gitignore` into one.
- [ ] Delete `legacy/` once everything reusable has been ported. *(Architecture §"Working with legacy/" in copilot-instructions.)*

---

## Open Questions / Known Challenges

Open design decisions that should be resolved before the corresponding Phase 4 work begins. Promote an item to **Known Issues** below the moment it tips from "design call" into "witnessed bug."

### Q6. Word difficulty progression

Color already carries speed and point value. The third axis — word length by color (red = short, blue = long) — is partially in place via the per-level word bands but is **not wired by alien color**, only by current level.

Options:

- Single `words.txt` filtered at spawn time by character-count range per color.
- Per-color word bands replacing the per-level bands (or layered on top).

### Q8. Powerup catalog

All five powerups are implemented and shipping. The open question is which 1–2 should remain enabled for v2 vs. be cut, and what drop rates feel best. Candidates that fit the typing format and aren't yet built:

- **Slow time** — all aliens fall slower for N seconds.
- **Screen wipe** — kills all on-screen aliens (bomb reincarnation).
- **Word skip** — completes the targeted alien's word for free.
- **Shorter words** — only short-band words spawn for N seconds.

### Q9. Status effects

The blue alien's confusion mechanic could become "scrambles the letters of the targeted word" or "displays the word backwards." Resolve before implementing the §4a status-effect item.

### Q11. Word readability at higher spawn rates

At current `WordSettings.SIZE = MEDIUM`, a 7-letter word is ~140 px wide — nearly a quarter of the 600 px screen. As spawn rate ramps and aliens cluster, words can overlap and become unreadable.

Options:

- **Spawn-time x-distance check** — reject a spawn x within `WORD_WIDTH` px of any alien at the same y-band. Cheapest first pass.
- **Lanes** — assign straight-falling aliens to N fixed x-lanes at spawn.
- **Font scale by word length** — shrink longer words to a fixed on-screen width. Inverts the difficulty signal, so probably bad.
- **Vertical word offset variance** — render some words above the sprite, others below.

Recommendation: try the spawn-time x-distance check first.

---

## Known issues

Concrete observed or anticipated problems. Promote items here from **Open Questions** once a design question tips into a witnessed bug or layout problem.

- *(none at Phase 3 completion)* — the Q11 word-overlap concern is still theoretical at current spawn rates; promote here if it becomes visible during play.

---

## Observations / guiding principles

These are the design rails the project runs on. They are not "todo" items — they are constraints that any new work must respect.

### O1. Be faithful to how Star Hero felt

Reuse the same SFX on the same beats, keep CRT + scrolling starfield + alien-color palette + explosion spritesheet. The four alien colors are not interchangeable — each has its own speed, point value, and (eventually) motion pattern and word-difficulty band. Those relationships port from Star Hero verbatim.

### O2. Snappy kill feel beats elaborate animation

Any "ship moves → fires → laser travels → alien dies" sequence introduces delay between Enter and the kill. The current approach (laser spawns from bottom, homes in) keeps the visual narrative without making the player wait. Slight travel time is fine; multi-step choreography is not.

### O3. Screen readable budget

At the spawn cadences the difficulty ramp can reach, word readability becomes the limiting factor before reflexes do. Any work that increases on-screen alien count (faster spawn rate, word-difficulty bands driving longer words) must also defend layout — see Q11.

---

## Dev notes

- **All in-game text is uppercase.** Every string passed to `font.render` must be `.upper()`'d — alien words, typed buffer, HUD score, initials, everything. A bare `font.render(some_string, ...)` without `.upper()` is a bug.
- **Settings discipline.** No magic numbers in code. Everything tunable lives in `settings.py`.
- **CHANGELOG discipline.** Every code change gets an entry in `docs/CHANGELOG.md`. See that file's header for format.
- **Don't dump `legacy/` files into context.** Read specific classes with `grep` + `read` and a line range — never load a full legacy file.
- **Word collisions.** Two aliens sharing a starting letter makes prefix-locking ambiguous. Tie-break rule: lock the lowest-y alien (closest to the bottom = most urgent). Already implemented in `WordManager._update_candidates`.
- **Pygame text rendering.** `font.render` is called per-frame for each alien word. Fine at current alien counts; cache rendered surfaces on `Alien` if performance becomes an issue.

---

## Documentation maintenance

Every pass that touches code must:

1. Update [docs/ARCHITECTURE.md](ARCHITECTURE.md) if the change altered how a system works.
2. Append an entry to [docs/CHANGELOG.md](CHANGELOG.md) per the format in that file.
3. Tick the matching item here from `[ ]` to `[x]` if a roadmap item was advanced or completed (do not delete — leave as a record).
4. Run the relevant section of [docs/TESTING.md](TESTING.md) before declaring done.