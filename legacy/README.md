# Star Hero <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/assets/graphics/player_ship.png" height="32">

Star Hero is a vertically scrolling, space-themed shoot'em up built with Python and Pygame.

This project started as a learning game and continues to grow with new polish, mechanics, and balance updates.

## Requirements

- [Python](https://www.python.org/) 3.10+
- [Pygame](https://www.pygame.org/)

Install Pygame:

```bash
pip install pygame
```

## Run the Game

From the repository root, run through the launcher:

```bash
python main.py
```

Or run Star Hero directly:

```bash
python star-hero/main.py
```

If your Windows environment uses `py`:

```bash
py star-hero/main.py
```

## Core Gameplay Rules

- You start with 3 hearts.
- Taking damage first strips active weapon upgrades/powerups (when applicable) before removing a heart.
- Getting hit by enemy lasers or colliding with enemies removes hearts when no protective/upgrade buffer is active.
- Lose all hearts and the run ends.
- Your score increases as you destroy enemies.
- Difficulty ramps up as score increases (faster spawns, faster enemy fire, faster background scroll).
- Blue aliens can apply a confusion effect that temporarily reverses movement controls.
- Bombs can be launched and detonated manually for area damage.
- Shield and rainbow beam states provide temporary damage immunity.

## Controls

### Keyboard

- `WASD` or Arrow Keys: Move
- `Space`: Fire
- Hold `F`: Move faster (left, right or forward)
- Hold `G`: Brake (slows world speed while meter is available)
- `B`: Launch bomb / detonate active bomb
- `F11`: Toggle fullscreen
- `Enter`: Pause/unpause
- `Esc`: Quit to arcade launcher
- `+` / `-`: Increase or decrease volume

### Controller (Logitech-style mapping)

- Left analog stick: Move
- `A`: Fire
- `Y`: Forward boost (move up faster while held)
- `L1`: Left boost (move left faster while held)
- `R1`: Right boost (move right faster while held)
- `X`: Brake (slows world speed while held)
- `B`: Launch bomb / detonate active bomb
- `Select/Back`: Toggle fullscreen
- `D-Pad Up` / `Down`: Volume up/down
- `Start`: Pause/unpause during run, start/restart from menu
- `L1 + R1 + Start + Select`: Close window and re-open game launcher menu

## Game Flow

- Intro screen: Press Start/Enter to begin.
- Active run: Survive, score, and collect powerups.
- Pause: Available during active gameplay.
- Game over: If your score qualifies, initials entry appears for leaderboard placement.

## Enemy Drops and Powerups

- Hearts: Dropped by red aliens (when not at max hearts); restores health.
- Shield: Rare red alien drop; grants temporary protection.
- Laser Upgrades: Dropped by green aliens (up to Hyper tier).
	- Twin Laser: Hits two side-by-side targets.
	- Hyper Laser: Pierces through enemies.
- Rapid Fire: Tiered fire-rate upgrade dropped by yellow aliens (up to auto-fire tier).
- Rainbow Beam: Temporary screen-wide beam attack dropped by blue aliens.
- Bomb Pickup: Rare drop; increases bomb inventory by 1.

## Damage and Survivability

- Active shield blocks incoming damage.
- On hit, active weapon power states can be stripped first (laser/rapid/rainbow) before hearts are reduced.
- Low-health alarm behavior changes at 2 hearts and 1 heart.
- Damage flash provides a brief invulnerability window.

## Enemy Types and Score Values

Each alien behaves differently and awards different points:

- <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/assets/graphics/red1.png" width="20" height="16"> Red Alien: Slow, drops hearts. **100 points**
- <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/assets/graphics/green1.png" width="20" height="16"> Green Alien: Medium speed, drops laser upgrades. **200 points**
- <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/assets/graphics/yellow1.png" width="20" height="16"> Yellow Alien: Fast zigzag movement, drops rapid fire. **300 points**
- <img src="https://raw.githubusercontent.com/frankiebry/star-hero/refs/heads/main/assets/graphics/blue1.png" width="20" height="10"> Blue Alien: Very fast and rare, may use confusion beam, drops rainbow beam. **500 points**

## Attributions

- Graphics attributions: [assets/graphics/attributions.md](assets/graphics/attributions.md)
- Audio attributions: [assets/audio/attributions.md](assets/audio/attributions.md)

## Learning Resources

This project was heavily inspired by [Clear Code's tutorials](https://www.youtube.com/@ClearCode), especially [The ultimate introduction to Pygame](https://www.youtube.com/watch?v=AY9MnQ4x3zk).
