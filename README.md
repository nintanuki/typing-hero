# Typing Hero

Typing Hero is a typing-based arcade game built with Python and Pygame. Words appear above descending aliens; type a word and the player's ship shoots a laser that destroys it. Aliens that reach the bottom of the screen cost the player a heart. Lose all hearts and the run ends.

The repository began life as **Star Hero**, a vertically-scrolling shoot-'em-up. The original Star Hero source has been moved into `legacy/` and is preserved unchanged as a reference library — code, sprites, audio cues, and patterns from it will be selectively ported over while building Typing Hero. Once Typing Hero is feature-complete the `legacy/` folder will be deleted.

## Status

Pre-scaffolding. The repository currently contains only documentation and the frozen `legacy/` source. See [`docs/TODO.md`](docs/TODO.md) for the staged build plan and the open design questions that still need answers.

## Requirements

- [Python](https://www.python.org/) 3.10+
- [Pygame](https://www.pygame.org/)

```bash
pip install pygame
```

## Run

Once Stage 0 of the build plan is complete:

```bash
python main.py
```

(On Windows you may need `py main.py`.)

## Planned Project Layout

```
typing-hero/
├── main.py              # Game entry point + main loop
├── settings.py          # Tunable constants (screen, fonts, colors, audio paths)
├── core/                # Sprites and animations
├── systems/             # Game-state managers (spawning, scoring, words, sessions)
├── ui/                  # HUD, menus, optional CRT shader
├── assets/              # Graphics, audio, fonts (carried over from Star Hero)
├── docs/                # README, TODO, TESTING, CHANGELOG for Typing Hero
└── legacy/              # Frozen Star Hero codebase — read-only reference
```

## Working with `legacy/`

Treat `legacy/` as a read-only reference. Anything inside it is the exact, working Star Hero codebase as of the moment Typing Hero began. It is the source of truth when porting reusable subsystems (audio, hearts HUD, explosion sprite, score saving, CRT shader, scrolling background, etc.). Do not edit files in `legacy/`. The folder will be deleted once it has nothing left to teach us.

## Attributions

Graphics and audio attributions live in the legacy assets folders for now and will be carried over with the assets. See `legacy/assets/graphics/attributions.md` and `legacy/assets/audio/attributions.md`.

## Learning Resources

The original Star Hero project (and therefore the patterns inherited here) was heavily inspired by [Clear Code's Pygame tutorials](https://www.youtube.com/@ClearCode), especially [The ultimate introduction to Pygame](https://www.youtube.com/watch?v=AY9MnQ4x3zk).
