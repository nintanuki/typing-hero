# Typing Hero — Project Reference

> Stages 0–9 are complete. The game has: title screen, spawning aliens (4 colors, per-color speed + points), prefix-locking word mechanics, kill laser + explosion, hearts HUD, score + high score, difficulty ramp, initials entry, leaderboard, pause, BGM, and CRT/background effects. `legacy/` remains read-only for reference.

---

## 1. Open design questions

Decisions deferred from earlier stages that Stage 10 work will depend on.

### Q6. Word difficulty progression
Color already carries speed and point value. The third axis — word length by color (red = short words, blue = long words) — requires splitting `assets/words.txt` into per-difficulty lists. Not yet done.

Options:
- Single `words.txt` filtered at spawn time by character-count range per color.
- Separate `words_easy.txt` / `words_hard.txt` loaded by difficulty band.

### Q8. Powerups in a typing context
All cut for v1. Candidates that still fit the typing format:
- **Heal** — drops from a destroyed alien, restores a heart.
- **Slow time** — all aliens fall slower for N seconds.
- **Screen wipe** — kills all on-screen aliens (bomb reincarnation).
- **Word skip** — completes the targeted alien's word for free.
- **Shorter words** — only short words spawn for N seconds.

Decide which 1–2 to implement before starting Stage 10 powerup work.

### Q9. Status effects
The blue alien's confusion mechanic could become "scrambles the letters of the targeted word" or "displays the word backwards." Deferred to v2. Resolve before implementing.

### Q11. Word readability at higher spawn rates
At current `WordSettings.SIZE = MEDIUM`, a 7-letter word is ~140 px wide — nearly a quarter of the 600 px screen. As spawn rate ramps and aliens cluster, words overlap and become unreadable.

Options:
- **Spawn-time x-distance check** — reject a spawn x within `WORD_WIDTH` px of any alien at the same y-band. Cheapest first pass.
- **Lanes** — assign straight-falling aliens to N fixed x-lanes at spawn so they never overlap horizontally.
- **Font scale by word length** — shrink longer words to a fixed on-screen width. Inverts the difficulty signal (long word looks smaller = easier?).
- **Vertical word offset variance** — render some words above the sprite, others below, so stacked aliens don't collide.

Recommendation: try the spawn-time x-distance check first.

---

## 2. Stage 10 — V2 polish (pick à la carte)

No fixed order — these are independent. Pick whichever items feel right and do them in any combination.

- [ ] 1–2 powerups (see Q8 for candidates — decide first, then implement).
- [ ] Word difficulty bands by alien color — short words for red, long words for blue (see Q6).
- [ ] Yellow alien zigzag motion (faithful to Star Hero's per-color patterns).
- [ ] Word readability fix at high spawn rates (see Q11 for options).
- [ ] Status effect: scrambled-letters debuff from blue aliens (see Q9).
- [ ] Stats screen on game over: WPM, accuracy, longest streak.
- [ ] Difficulty selector on title screen (easy / normal / hard adjusts spawn rate + word length band).
- [ ] Re-theme the music if `star_hero.ogg` no longer fits.
- [ ] Custom typing-themed sprites (letter-themed enemies instead of alien ships?).

---

## 3. Known issues

Concrete observed or anticipated problems. Promote items here from §1 once a design question tips into a witnessed bug or layout problem.

- None at Stage 9 completion. The Q11 word-overlap concern is still theoretical at current spawn rates — promote here if it becomes visible during play.

---

## 4. Observations / guiding principles

### O1. Be faithful to how Star Hero felt
Reuse the same SFX on the same beats, keep CRT + scrolling starfield + alien-color palette + explosion spritesheet. The four alien colors are not interchangeable — each has its own speed, point value, and (eventually) motion pattern and word-difficulty band. Those relationships port from Star Hero verbatim.

### O2. Snappy kill feel beats elaborate animation
Any "ship moves → fires → laser travels → alien dies" sequence introduces delay between Enter and the kill. The current approach (laser spawns from bottom, homes in) keeps the visual narrative without making the player wait. Slight travel time is fine; multi-step choreography is not.

### O3. Screen readable budget
At the spawn cadences the difficulty ramp can reach, word readability becomes the limiting factor before reflexes do. Any work that increases on-screen alien count (faster spawn rate, word-difficulty bands driving longer words) must also defend layout. See Q11.

---

## 5. Dev notes

- **All in-game text is uppercase.** Every string passed to `font.render` must be `.upper()`'d — alien words, typed buffer, HUD score, initials, everything. A bare `font.render(some_string, ...)` without `.upper()` is a bug.
- **Settings discipline.** No magic numbers in code. Everything tunable lives in `settings.py`.
- **CHANGELOG discipline.** Every code change gets an entry in `docs/CHANGELOG.md`.
- **Don't dump `legacy/` files into context.** Read specific classes with `grep` + `read` and a line range — never load a full legacy file.
- **Word collisions.** Two aliens sharing a starting letter makes prefix-locking ambiguous. Tie-break rule: lock the lowest-y alien (closest to the bottom = most urgent). This is already implemented in `WordManager._acquire_target`.
- **Pygame text rendering.** `font.render` is called per-frame for each alien word. Fine at current alien counts; cache rendered surfaces on the Alien sprite if performance becomes an issue.

---

## 6. Parking lot

- Combine `.gitignore` files (root + `legacy/`) into one.
- Delete `legacy/` entirely once it has no more reference value (after all needed pieces have been ported).
- initials still need to be moved up a little, or leaderboard down... or remove the blue line