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
    # Color used for the untyped portion of an alien's word (i.e. the
    # whole word when no target is locked, or the suffix that has not
    # been typed yet on the targeted alien). Renamed concept arrives in
    # Stage 3 alongside PREFIX_COLOR — the plain ``COLOR`` name is kept
    # so Stage 1/2 call sites that pass no prefix still read naturally.
    COLOR = ColorSettings.COLORS['WHITE']
    # Color used for the already-typed prefix on the targeted alien's
    # word (Stage 3). Cyan reads as "active / electric" against the
    # untyped white suffix and is distinguishable on the red/green/
    # yellow/blue alien sprites without clashing with any of them.
    PREFIX_COLOR = ColorSettings.COLORS['CYAN']
    # Pixel gap between the word's baseline and the alien sprite's top
    # edge. Big enough that the word never visually merges with the
    # sprite, small enough that it still reads as "this word belongs to
    # this alien" at typical spawn density.
    OFFSET_ABOVE_SPRITE = 12


class Stage3Layout:
    """Hardcoded positions and words for the three Stage 3 demo aliens.

    Stage 3's job is to prove prefix-locking works — it does not yet
    spawn from a word list (Stage 4) or move (Stage 5). So the three
    aliens are placed at fixed points in the upper third of the screen
    with three deliberately different first letters (H, W, T) so the
    Stage 3 smoke test in ``docs/TESTING.md`` can exercise lock
    acquisition by pressing different first letters. These constants
    are scoped to Stage 3 and will be removed once ``SpawnDirector``
    takes over alien creation in Stage 4.
    """

    # Vertical band where the three demo aliens sit. Upper third keeps
    # them clear of the bottom-of-screen typing buffer and leaves room
    # below for the falling animation Stage 5 will introduce.
    ROW_Y = ScreenSettings.HEIGHT // 4
    # Horizontal positions: 1/4, 1/2, 3/4 of screen width — even spread
    # across the playfield so prefix-locking is unambiguous and the
    # visual highlight has space to breathe.
    LEFT_X = ScreenSettings.WIDTH // 4
    CENTER_X = ScreenSettings.WIDTH // 2
    RIGHT_X = (ScreenSettings.WIDTH * 3) // 4
    # (color, word, x) tuples consumed by main.py to build the demo
    # group. Words are stored lowercase on disk per Q7; the renderer
    # uppercases at draw time.
    ALIENS = (
        ('red', 'hello', LEFT_X),
        ('green', 'world', CENTER_X),
        ('yellow', 'type', RIGHT_X),
    )


class TypingSettings:
    """Tunables for capturing player typing and rendering the typing buffer.

    Project-wide rule (see ``docs/TODO.md`` Q7): all in-game text renders
    in UPPERCASE. The typing buffer follows that rule too, regardless of
    the actual key-case the player presses.
    """

    # Font size for the bottom-of-screen typing buffer. LARGE gives the
    # player's typed letters more visual weight than the per-alien word
    # labels, so the buffer reads as a HUD element rather than another
    # alien's tag.
    SIZE = FontSettings.LARGE
    COLOR = ColorSettings.COLORS['WHITE']
    # Vertical distance between the typing buffer's baseline and the
    # bottom edge of the screen. Big enough that descenders / pixel
    # artifacts in Pixeled don't kiss the screen edge, small enough
    # that the buffer doesn't drift up into the playfield.
    OFFSET_FROM_BOTTOM = 24
    # Maximum buffer length. Words land well under this in v1; the cap
    # exists so a stray keyboard repeat or paste doesn't grow the
    # rendered surface unbounded across the screen.
    MAX_LENGTH = 32
