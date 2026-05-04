"""Project-wide constants for Typing Hero."""

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
    BG_COLOR = ColorSettings.COLORS['BLACK']
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3
    DEFAULT_BG_SCROLL_SPEED = 50
    BG_SCROLL_STEP = 25
    BG_SCROLL_MAX = 500
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
    INTRO_VOL_BOOST = 2.0
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    MUSIC_DIR = os.path.join(ASSETS_DIR, 'music')
    AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')
    BGM_PLAYLIST = [
        'star_hero.ogg',
    ]

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

    SIZE = FontSettings.MEDIUM
    COLOR = ColorSettings.COLORS['WHITE']
    PREFIX_COLOR = ColorSettings.COLORS['CYAN']
    OFFSET_ABOVE_SPRITE = 12
    WORDLIST_PATH = os.path.join(
        os.path.dirname(__file__), 'assets', 'words.txt'
    )


class SpawnSettings:
    """Tunables for alien spawning."""

    SPAWN_RATE = 3000  # ms between spawns
    SPAWN_Y = 80
    X_MARGIN = 80  # keep words from clipping screen edges
    COLORS = ('red', 'green', 'yellow', 'blue')


class AlienSettings:
    """Per-color speed and point values. Red is slowest/cheapest; blue is fastest/most valuable."""

    # px/frame at 120 FPS: red ~12 s, green ~8.6 s, yellow ~6.7 s, blue ~5.5 s top-to-bottom
    SPEED = {
        'red':    0.5,
        'green':  0.7,
        'yellow': 0.9,
        'blue':   1.1,
    }
    POINTS = {
        'red':    100,
        'green':  200,
        'yellow': 300,
        'blue':   500,
    }


class ExplosionSettings:
    """Explosion sprite sheet tunables."""

    FRAMES = 7
    ANIMATION_SPEED = 0.15  # smaller = slower
    SIZE = 192
    SCALE = 0.5


class TypingSettings:
    """Typing buffer capture and rendering tunables. All on-screen text renders uppercase."""

    SIZE = FontSettings.LARGE
    COLOR = ColorSettings.COLORS['WHITE']
    OFFSET_FROM_BOTTOM = 24
    MAX_LENGTH = 32  # guard against keyboard-repeat / paste flooding the buffer


class HeartSettings:
    """Player-health HUD tunables."""

    MAX = 3
    TOP_MARGIN = 8
    RIGHT_MARGIN = 30
    SPACING = 10


class GameOverSettings:
    """Game-over overlay text and layout."""

    BANNER_TEXT = "GAME OVER"
    BANNER_SIZE = FontSettings.LARGE
    PROMPT_TEXT = "PRESS ENTER TO RESTART"
    PROMPT_SIZE = FontSettings.MEDIUM
    COLOR = ColorSettings.COLORS['WHITE']
    BANNER_OFFSET = 40   # px above screen center
    PROMPT_OFFSET = 30   # px below screen center


class ScoreSettings:
    """Run-score, difficulty ramp, and HUD layout tunables."""

    SAVE_FILENAME = 'high_score.txt'
    SAVE_PATH = os.path.join(os.path.dirname(__file__), SAVE_FILENAME)

    DIFFICULTY_STEP = 5000    # points between ramp steps
    SPAWN_RATE_DROP = 200     # ms removed per step
    MIN_SPAWN_RATE = 1200     # ms floor (9 steps from 3000 ms)

    HIGH_SCORE_TOPLEFT = (10, 5)
    SCORE_TOPLEFT = (10, 20)
    HIGH_SCORE_SIZE = FontSettings.SMALL
    SCORE_SIZE = FontSettings.MEDIUM
    COLOR = ColorSettings.COLORS['WHITE']
