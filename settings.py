"""Project-wide tunable constants for Typing Hero.

This file is intentionally minimal at Stage 0 — it carries only the constants
needed to open a window and locate bundled assets. Game-mechanic constants
(typing rules, alien speeds, scoring) will be added in later stages as the
features that need them land.
"""

import os


class ColorSettings:
    """RGB color values used throughout the game (text, backgrounds, etc.)."""

    COLORS = {
        'RED':    (255,  80,  80),
        'GREEN':  ( 60, 255, 100),
        'YELLOW': (255, 220,  60),
        'BLUE':   ( 80, 160, 255),
        'WHITE':  (255, 255, 255),
        'CYAN':   ( 80, 255, 255),
        'BLACK':  (  0,   0,   0),
    }


class ScreenSettings:
    """Display geometry and frame timing for the main game window."""

    WIDTH = 600
    HEIGHT = 800
    RESOLUTION = (WIDTH, HEIGHT)
    CENTER = (WIDTH / 2, HEIGHT / 2)
    FPS = 120
    # Stage 0 fills the screen with a solid black each frame; once the
    # scrolling background ports over (Stage 8 polish), this constant becomes
    # a fallback that is never actually visible.
    BG_COLOR = ColorSettings.COLORS['BLACK']
    TITLE = "Typing Hero"


class FontSettings:
    """Font file path and standard sizes for HUD and on-screen text."""

    FONT = os.path.join(os.path.dirname(__file__), 'assets', 'font', 'Pixeled.ttf')
    SMALL = 10
    MEDIUM = 20
    LARGE = 30
    COLOR = 'white'


class AudioSettings:
    """Audio system tunables and paths to the bundled music/SFX folders."""

    DEFAULT_MASTER_VOLUME = 0.5
    DEBUG_MUTE = False  # set True to silence all audio for debugging
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    MUSIC_DIR = os.path.join(ASSETS_DIR, 'music')
    AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')


class AssetPaths:
    """Filesystem paths to bundled graphics used by the game."""

    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    GRAPHICS_DIR = os.path.join(ASSETS_DIR, 'graphics')
    BACKGROUND = os.path.join(GRAPHICS_DIR, 'background.png')
    EXPLOSION = os.path.join(GRAPHICS_DIR, 'explosion.png')
    PLAYER = os.path.join(GRAPHICS_DIR, 'player_ship.png')
    HEART = os.path.join(GRAPHICS_DIR, 'heart.png')
    TV = os.path.join(GRAPHICS_DIR, 'tv.png')


class WordSettings:
    """Tunables for rendering the word floating above each alien."""

    # Font size used when rasterizing alien words. MEDIUM keeps short
    # 4-6 letter words readable without crowding the sprite; revisit if
    # Stage 6+ tuning makes longer words common.
    SIZE = FontSettings.MEDIUM
    COLOR = ColorSettings.COLORS['WHITE']
    # Pixel gap between the word's baseline and the alien sprite's top
    # edge. Big enough that the word never visually merges with the
    # sprite, small enough that it still reads as "this word belongs to
    # this alien" at typical spawn density.
    OFFSET_ABOVE_SPRITE = 12
