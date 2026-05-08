# Typing Hero

A retro-arcade typing game built with Python and Pygame. Aliens drop from the top of the screen with a word floating above each one. Type the word — fast and clean — and a laser fires from your ship to destroy it. Miss too many and the run ends. The longer you survive, the faster they come and the harder the words get.

It's "Galaga, but the gun is your keyboard." A CRT shader and a scrolling starfield round out the arcade-cabinet vibe.

This project began life as **Star Hero**, a more conventional vertical shoot-'em-up. The original Star Hero source lives in [legacy/](legacy/) as a frozen, read-only reference library — code, sprites, and audio cues port across selectively as Typing Hero grows. Once nothing reusable remains, the `legacy/` folder will be deleted.

---

## Status

**Phase 4 — V2 polish, à la carte.** The full game loop is playable end-to-end (title → run → game over → leaderboard → restart) with audio, CRT, four alien colors, prefix-locking typing, hearts, score with persisted high score, leaderboard initials entry, pause, difficulty ramp, and a powerup catalog. Phase 4 items are independent polish tasks. See [docs/TODO.md](docs/TODO.md) for the full roadmap.

---

## How to play

1. Aliens spawn at the top of the screen, each one carrying a word.
2. **Type the word.** The first letter you press locks onto a matching alien and starts a typing buffer at the bottom of the screen.
3. Finish the word and a laser instantly destroys that alien — score depends on its color (red 100 / green 200 / yellow 300 / blue 500).
4. Aliens that reach the bottom of the screen cost you one heart.
5. **Lose all three hearts and the run ends.** If your score qualifies, enter your initials with the arrow keys.

A few details worth knowing:

- **Soft-lock targeting:** if your typed prefix matches more than one alien, the lowest one (closest to the bottom — most urgent) gets provisional focus. Keep typing and focus snaps to whichever alien still matches.
- **Faster colors are worth more.** Blue aliens fall fastest and pay 500. Red aliens are slow and pay 100.
- **Powerups drop from kills.** Heart, shield, laser-tier upgrade, burst, and rainbow beam — each tied to a specific alien color. Pick them up by letting them reach the bottom of the screen.
- **All in-game text is uppercase.** That's deliberate — it's the arcade font.

---

## Controls

| Key                         | Action                                                       |
| --------------------------- | ------------------------------------------------------------ |
| Letter keys (`A`–`Z`)       | Type into the active word buffer                             |
| `Backspace`                 | Delete the most recent typed letter                          |
| `Enter`                     | Start a run / pause / unpause / restart from game-over       |
| `↑` `↓` `←` `→` then `Enter`| Cycle initials and submit on the leaderboard entry screen    |
| `F11`                       | Toggle fullscreen                                            |
| `ESC`                       | Quit the game cleanly from any state                         |

---

## Requirements

- [Python](https://www.python.org/) 3.10 or newer
- [Pygame](https://www.pygame.org/) 2.5 or newer

---

## Install & run

```bash
git clone <this-repo-url>
cd typing-hero
pip install -r requirements.txt
python main.py
```

On Windows, `py main.py` works as an alternative to `python main.py`.

The game opens in a 600×800 window. Press `F11` for fullscreen, `Enter` to start, and `ESC` to quit.

---

## Project layout

```
typing-hero/
├── main.py              # GameManager + main loop entry point
├── settings.py          # Every tunable constant in the game
├── high_score.txt       # Persisted high score + leaderboard
├── requirements.txt     # Python dependencies
├── core/                # Sprites (Alien, lasers, powerups) and animations
├── systems/             # WordManager, SpawnDirector, ScoreManager, AudioManager
├── ui/                  # HUD widgets, menu screens, CRT post-process
├── assets/              # Graphics, audio, font, music, and word lists
│   ├── audio/
│   ├── font/
│   ├── graphics/
│   ├── music/
│   └── words/           # band1..5 word lists by difficulty
├── docs/                # ARCHITECTURE, TODO, TESTING, CHANGELOG
└── legacy/              # Read-only Star Hero reference codebase
```

---

## Documentation

If you plan to read or contribute to the code, read the docs in this order:

1. **This README** — what the game is and how to run it.
2. [docs/TODO.md](docs/TODO.md) — the phased roadmap and open design questions.
3. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how the code actually works, system by system.
4. [docs/TESTING.md](docs/TESTING.md) — the manual smoke-test playbook to run after any change.
5. [docs/CHANGELOG.md](docs/CHANGELOG.md) — append-only history of every code edit.
6. [.github/copilot-instructions.md](.github/copilot-instructions.md) — coding rules that apply to every editor (human and AI).

---

## Working with `legacy/`

`legacy/` is a frozen snapshot of Star Hero — read-only reference, never edited. When porting a subsystem, read specific classes with grep + a line range; do not load whole legacy files into context. The folder will be deleted once it has no remaining reference value.

---

## Credits

- **Star Hero** — the original Pygame shoot-'em-up project this codebase grew out of. Most of the visual style, audio cues, and CRT shader came from there.
- **[Clear Code](https://www.youtube.com/@ClearCode)** — the Pygame tutorials that taught the original patterns, especially [The ultimate introduction to Pygame](https://www.youtube.com/watch?v=AY9MnQ4x3zk).
- Asset attributions live alongside the assets themselves: see [assets/graphics/attributions.md](assets/graphics/attributions.md), [assets/audio/attributions.md](assets/audio/attributions.md), and [assets/music/attributions.md](assets/music/attributions.md).
