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
    FPS = 120 # Do we want to keep it at 120? Or should we drop to 60?
    # Stage 0 fills the screen with a solid black each frame; once the
    # scrolling background ports over (Stage 8 polish), this constant becomes
    # a fallback that is never actually visible.
    BG_COLOR = ColorSettings.COLORS['BLACK']
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3 # vertical pixels between scanlines drawn on the CRT overlay
    DEFAULT_BG_SCROLL_SPEED = 50
    BG_SCROLL_STEP = 25 # how many pixels the background moves each difficulty step (lower = smoother, higher = more noticeable)
    BG_SCROLL_MAX = 500 # maximum scroll speed for the background, to prevent it from becoming too fast at high scores
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
    # Path to the on-disk word list ``WordManager`` loads at boot
    # (Stage 4). Stored lowercase per Q7 — the renderer and the
    # comparator both uppercase at use. Kept under ``assets/`` so
    # editing the word list doesn't require touching code, and so the
    # "everything bundled" layout from ``docs/TODO.md`` Stage 0 holds.
    WORDLIST_PATH = os.path.join(
        os.path.dirname(__file__), 'assets', 'words.txt'
    )


class SpawnSettings:
    """Tunables for the Stage 4 alien spawner.

    ``SpawnDirector`` reads these to drive the single pygame timer
    event that pushes new aliens onto the screen. Difficulty scaling
    (shrinking ``SPAWN_RATE`` as score climbs) is a Stage 7 concern;
    Stage 4 keeps the rate constant.
    """

    # Milliseconds between alien spawns. Star Hero's legacy default of
    # 600 ms is brutal for a typing game (``docs/TODO.md`` §6 pitfall
    # "The legacy alien spawn rate is way too fast for typing");
    # 3000 ms gives the player real time to read the next word and
    # commit to a target before the screen fills. Tune downward in
    # Stage 5 once aliens fall and a "miss" actually costs something.
    SPAWN_RATE = 3000
    # Vertical center y of newly-spawned aliens. Stage 4 aliens don't
    # move (Stage 5 ports falling), so the spawn y has to leave the
    # alien sprite *and* the word floating above it both fully on
    # screen. With WordSettings.OFFSET_ABOVE_SPRITE=12 and a MEDIUM
    # font, y=80 keeps the word baseline around y=52 — clear of the
    # screen top with a small breathing margin. Once Stage 5 lands,
    # this becomes a negative y so aliens fall *into* the screen.
    SPAWN_Y = 80
    # Horizontal margin from each screen edge so the word floating
    # above an alien doesn't clip the screen when the sprite spawns
    # near a wall. Sized for the longest words in ``assets/words.txt``
    # (e.g. "thunder", "crystal") rendered at WordSettings.SIZE — a
    # ~140 px word centered on x needs ~70 px of breathing room each
    # side; 80 keeps a small buffer. Revisit if longer words land in
    # Stage 6+ tuning.
    X_MARGIN = 80
    # Alien colors the spawner picks from. Stage 4 picks uniformly —
    # color-keyed difficulty bands and per-color point values are a
    # Stage 7+ concern (``docs/TODO.md`` Q6). All four sprite colors
    # exist in ``assets/graphics/`` already so any of them is fair
    # game from the spawner's perspective.
    COLORS = ('red', 'green', 'yellow', 'blue')


class AlienSettings:
    """Tunables for alien behavior once on screen (Stage 5+).

    Stage 5 introduces vertical-only descent — no zigzag, no confusion
    beam, no per-color motion variation. The legacy ``AlienSettings``
    in ``legacy/settings.py`` carried per-color SPEED, ZIGZAG_THRESHOLD,
    POINTS, drop-table chances, and a confusion-attack tunable block;
    those land (or stay cut) in their own stages — POINTS in Stage 7,
    per-color SPEED bands also in Stage 7 alongside Q6's color-as-
    difficulty work, drops/confusion deferred indefinitely (§2 cuts).
    """

    # Pixels per frame an alien drops, applied uniformly to all four
    # colors at Stage 5. ``docs/TODO.md`` §5 step 1 calls for "1 px/
    # frame at 60 FPS, tune later"; this project runs at 120 FPS, so
    # the equivalent is 0.5 px/frame. With ``SpawnSettings.SPAWN_Y =
    # 80`` and ``ScreenSettings.HEIGHT = 800``, an alien takes roughly
    # (800 - 80) / 0.5 / 120 ≈ 12 s to traverse the screen — squarely
    # in the §6 pitfall's "8–10 s window" once we account for the
    # alien sprite extending below ``rect.top``. Stored as a float so
    # the sub-pixel accumulator on ``Alien.position`` actually advances
    # each frame; integer 1 (or rounding the multiply) would either
    # double the speed or stall it depending on the path.
    SPEED = 0.5
    # Per-color SPEED band lives in Stage 7 (``docs/TODO.md`` Q6)
    # alongside POINTS — both are about color-as-difficulty and want
    # to land together so the harder-color = higher-reward contract
    # is wired up in one pass. Pattern from the legacy class kept as
    # a comment so the future port has a target shape:
    #     SPEED = {'red': 0.5, 'green': 0.7, 'yellow': 0.9, 'blue': 1.1}


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


class HeartSettings:
    """Tunables for the player-health HUD ported in Stage 6.

    Carries the hearts-row geometry from the legacy ``UISettings`` block
    (``HEART_TOP_MARGIN``, ``HEART_RIGHT_MARGIN``, ``HEART_SPACING``) and
    adds ``MAX`` for the starting heart count. The legacy class also held
    boost-meter / status-row / bombs-row constants — those are forever-
    cut per ``docs/TODO.md`` §2 and don't make the trip.
    """

    # Starting (and maximum) hearts. Q5 resolved as "3 hearts × 1 miss
    # each" paired with the slow ``AlienSettings.SPEED`` that gives a
    # ~12 s window per alien — three misses worth of slow descent reads
    # as forgiving without removing the threat. Stage 6's tuning
    # checkpoint revisits if play-testing says otherwise.
    MAX = 3
    # Pixels between the top of the screen and the top of the heart
    # icons. Matches legacy ``UISettings.HEART_TOP_MARGIN`` so the row
    # sits in the same visual slot players who knew Star Hero are used
    # to (and so the asset still reads as "hearts" without re-tuning).
    TOP_MARGIN = 8
    # Pixels between the rightmost heart and the screen's right edge.
    # Matches legacy ``UISettings.HEART_RIGHT_MARGIN``.
    RIGHT_MARGIN = 30
    # Pixels between adjacent hearts in the row. Matches legacy
    # ``UISettings.HEART_SPACING``.
    SPACING = 10


class GameOverSettings:
    """Tunables for the minimal Stage 6 game-over overlay.

    Stage 6 only needs the banner + a "press Enter to restart" prompt so
    the run-loop can close. The richer game-over screen (final score,
    high-score, initials entry) lands in Stage 9 alongside the intro
    screen and the ``SessionStateManager`` port — at which point this
    class likely gets folded into a broader ``MenuSettings``.
    """

    # Banner text + size. LARGE matches the legacy game-over banner and
    # reads as the dominant element of the screen at this font.
    BANNER_TEXT = "GAME OVER"
    BANNER_SIZE = FontSettings.LARGE
    # Restart-prompt text + size. MEDIUM is a step down from BANNER so
    # the banner stays the heading and the prompt reads as instruction.
    PROMPT_TEXT = "PRESS ENTER TO RESTART"
    PROMPT_SIZE = FontSettings.MEDIUM
    COLOR = ColorSettings.COLORS['WHITE']
    # Pixels the banner sits *above* screen center, and the prompt sits
    # *below*. Centering both around CENTER (rather than stacking from
    # the top) keeps the overlay vertically balanced so the eye lands
    # on the banner first and the prompt second without scanning the
    # whole screen.
    BANNER_OFFSET = 40
    PROMPT_OFFSET = 30
