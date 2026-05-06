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
    DEFAULT_INITIALS = 'AAA'


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
    TV_RED = os.path.join(GRAPHICS_DIR, 'tv_red.png')
    TV_WHITE = os.path.join(GRAPHICS_DIR, 'tv_white.png')


class WordSettings:
    """Tunables for rendering the word floating above each alien."""

    SIZE = FontSettings.MEDIUM
    COLOR = ColorSettings.COLORS['WHITE']
    PREFIX_COLOR = ColorSettings.COLORS['CYAN']
    OFFSET_ABOVE_SPRITE = 12
    WORDS_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'words')
    WORDLIST_PATH = os.path.join(
        os.path.dirname(__file__), 'assets', 'words.txt'
    )
    # One file per difficulty band, all lowercase words on disk.
    WORD_BANK_PATHS = {
        1: os.path.join(WORDS_DIR, 'band1_very_easy.txt'),
        2: os.path.join(WORDS_DIR, 'band2_easy.txt'),
        3: os.path.join(WORDS_DIR, 'band3_medium.txt'),
        4: os.path.join(WORDS_DIR, 'band4_hard.txt'),
        5: os.path.join(WORDS_DIR, 'band5_very_hard.txt'),
    }
    # Level 1..20 -> word band index.
    LEVEL_WORD_BAND = (
        1, 1, 1,
        2, 2, 2, 2,
        3, 3, 3, 3,
        4, 4, 4, 4,
        5, 5, 5, 5, 5,
    )


class SpawnSettings:
    """Tunables for alien spawning."""

    SPAWN_RATE = 3000  # ms between spawns
    SPAWN_Y = 80
    X_MARGIN = 80  # keep words from clipping screen edges
    COLORS = ('red', 'green', 'yellow', 'blue')
    SPAWN_CHANCE = (50, 30, 15, 5)


class AlienSettings:
    """Per-color speed and point values. Red is slowest/cheapest; blue is fastest/most valuable."""

    SPEED = {
        'red':    0.5,
        'green':  1,
        'yellow': 1.5,
        'blue':   2.5,
    }
    POINTS = {
        'red':    100,
        'green':  200,
        'yellow': 300,
        'blue':   500,
    }
    DROP_CHANCE = {
        'red':    0.50,
        'green':  0.30,
        'yellow': 0.20,
        'blue':   0.10,
    }
    # Yellow and blue aliens drift horizontally while descending.
    # ZIGZAG_THRESHOLD is the frame count before yellow reverses direction;
    # blue reverses only on hitting a screen edge.
    ZIGZAG_HORIZONTAL_SPEED = 2
    ZIGZAG_THRESHOLD = 100


class PowerupSettings:
    """Powerup drop, movement, and laser-upgrade progression tunables."""

    SPEED = 2
    RADIUS = 12

    HEART_TYPE = 'heal'
    LASER_UPGRADE_TYPE = 'laser_upgrade'
    BURST_TYPE = 'burst'
    RAINBOW_BEAM_TYPE = 'rainbow_beam'
    TWIN_BEAM_OFFSET = 12

    # Laser modes: 1=single, 2=twin, 3=twin+piercing.
    MAX_LASER_LEVEL = 3

    # Burst fire (yellow powerup): each completed word fires 1 + tier_level lasers.
    # Tier 1: one follow-up at BURST_TIER1_DELAY_MS after the primary shot.
    # Tier 2: two follow-ups at the BURST_TIER2_DELAYS_MS intervals (shorter gap
    #         between them so the salvo feels faster than tier 1).
    MAX_BURST_TIER = 2
    BURST_TIER1_DELAY_MS = 250
    BURST_TIER2_DELAYS_MS = (200, 400)

    # Rainbow beam (blue powerup): a slow wide expanding beam fired from the
    # bottom-center.  Starts 1 px wide, grows to full screen width at
    # RAINBOW_BEAM_GROWTH_SPEED px/frame, then drifts upward until off-screen.
    RAINBOW_BEAM_SPEED = -1          # px per frame (slow enough to sweep ~6 s)
    RAINBOW_BEAM_HEIGHT = 40         # sprite height in px
    RAINBOW_BEAM_GROWTH_SPEED = 5    # px of width added per frame
    RAINBOW_BEAM_HUE_STEP = 4        # degrees of hue advance per frame
    RAINBOW_BEAM_SEGMENTS = 5        # number of rainbow color bands
    RAINBOW_BEAM_SEGMENT_SHIFT = 20  # hue offset between adjacent bands


class LaserSettings:
    """Player-shot visual tuning shared by kill beams and cosmetic twin beams."""

    WIDTH = 4
    HEIGHT = 20
    SPEED = -8
    COLORS = {
        'single': (ColorSettings.COLORS['GREEN'], ColorSettings.COLORS['WHITE']),
        'twin': (ColorSettings.COLORS['GREEN'], ColorSettings.COLORS['WHITE']),
        'piercing': (ColorSettings.COLORS['CYAN'], ColorSettings.COLORS['WHITE']),
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


class DamageSettings:
    """Tunables for player damage feedback: invincibility frames and screen flash."""

    INVINCIBILITY_MS = 1500  # ms the player is protected after a hit
    FLASH_DURATION = 600     # ms the red/white vignette flashes after a hit
    FLASH_INTERVAL = 120     # ms per red↔white toggle (~5 toggles across FLASH_DURATION)
    FLASH_ALPHA = 200        # opacity of the damage vignette overlay (0-255)


class GameOverSettings:
    """Game-over overlay text and layout."""

    BANNER_TEXT = "GAME OVER"
    BANNER_SIZE = FontSettings.LARGE
    HIGH_SCORE_CENTER_Y = 520
    SCORE_SIZE = FontSettings.MEDIUM
    SCORE_CENTER_Y = 560
    PROMPT_TEXT = "PRESS ENTER TO PLAY AGAIN"
    INITIALS_PROMPT_TEXT = "PRESS ENTER TO SUBMIT"
    NEW_HIGH_SCORE_TEXT = 'NEW HIGH SCORE! ENTER YOUR INITIALS'
    PROMPT_SIZE = FontSettings.MEDIUM
    COLOR = ColorSettings.COLORS['WHITE']
    CURSOR_COLOR = ColorSettings.COLORS['CYAN']
    NEW_HIGH_SCORE_COLOR = ColorSettings.COLORS['YELLOW']
    BANNER_CENTER_Y = 70
    INITIALS_CENTER_Y = 180
    INITIALS_PROMPT_CENTER_Y = 125
    LEADERBOARD_START_Y = 130
    INITIALS_LEADERBOARD_START_Y = 220
    PROMPT_CENTER_Y = 730


class LeaderboardSettings:
    """Shared leaderboard table layout."""

    TITLE = 'TOP 10'
    ROW_HEIGHT = 22
    SIZE = FontSettings.SMALL
    COLOR = ColorSettings.COLORS['WHITE']


class IntroSettings:
    """Title screen layout and text."""

    TITLE_TEXT = 'TYPING HERO'
    TITLE_SIZE = FontSettings.LARGE
    PROMPT_TEXT = 'PRESS ENTER TO PLAY'
    PROMPT_SIZE = FontSettings.MEDIUM
    HIGH_SCORE_TEXT_PREFIX = 'HIGH SCORE: '
    HIGH_SCORE_SIZE = FontSettings.MEDIUM
    COLOR = ColorSettings.COLORS['WHITE']
    TITLE_CENTER_Y = 70
    SHIP_CENTER_Y = 210
    LEADERBOARD_START_Y = 330
    HIGH_SCORE_CENTER_Y = 560
    PROMPT_CENTER_Y = 720


class PauseSettings:
    """Pause-screen overlay text."""

    TEXT = 'PAUSED'
    SIZE = FontSettings.LARGE
    COLOR = ColorSettings.COLORS['WHITE']


class ScoreSettings:
    """Run-score, difficulty ramp, and HUD layout tunables."""

    SAVE_FILENAME = 'high_score.txt'
    SAVE_PATH = os.path.join(os.path.dirname(__file__), SAVE_FILENAME)

    MAX_LEVEL = 20

    # Level thresholds (Level 1 starts at 0). Index 0 == L1, index 19 == L20.
    LEVEL_SCORE_THRESHOLDS = (
        0,
        500,
        1200,
        2200,
        3500,
        5000,
        7000,
        9500,
        12500,
        16000,
        20000,
        24500,
        29500,
        35000,
        41000,
        47500,
        54500,
        62000,
        70000,
        78500,
    )

    # Level 1..20 spawn interval table in ms.
    SPAWN_RATE_BY_LEVEL_MS = (
        3000,
        2800,
        2600,
        2400,
        2200,
        2000,
        1850,
        1700,
        1550,
        1400,
        1400,
        1400,
        1400,
        1400,
        1400,
        1400,
        1400,
        1400,
        1400,
        1400,
    )

    # Level 1..20 scalar applied on top of per-color alien base speeds.
    ALIEN_SPEED_MULTIPLIER_BY_LEVEL = (
        1.00,
        1.10,
        1.20,
        1.30,
        1.40,
        1.50,
        1.60,
        1.70,
        1.80,
        1.90,
        1.90,
        1.90,
        1.90,
        1.90,
        1.90,
        1.90,
        1.90,
        1.90,
        1.90,
        1.90,
    )

    # Cosmetic-only background pacing, intentionally decoupled from gameplay level.
    BACKGROUND_SPEED_SCORE_STEP = 2500

    HIGH_SCORE_TOPLEFT = (10, 5)
    SCORE_TOPLEFT = (10, 20)
    LEVEL_BOTTOMLEFT = (10, ScreenSettings.HEIGHT - 36)
    HIGH_SCORE_SIZE = FontSettings.SMALL
    SCORE_SIZE = FontSettings.MEDIUM
    LEVEL_SIZE = FontSettings.SMALL
    COLOR = ColorSettings.COLORS['WHITE']
