import os

class ColorSettings:
    """Defines the RGB color values for various named colors used throughout the game, such as for drawing lasers, powerups, and other visual elements."""
    COLORS = {
        'RED': (255, 80, 80),
        'GREEN': (60, 255, 100),
        'YELLOW': (255, 220, 60),
        'BLUE': (80, 160, 255),
        'WHITE': (255, 255, 255),
        'CYAN': (80, 255, 255),
        'BLACK': (0, 0, 0)
    }

class ScreenSettings:
    """Holds all the settings related to the game screen, such as dimensions, frame rate, background color, and other visual parameters."""
    WIDTH = 600
    HEIGHT = 800
    RESOLUTION = (WIDTH,HEIGHT)
    CENTER = (WIDTH / 2, HEIGHT / 2)
    FPS = 120
    BG_COLOR = (30, 30, 30) # Not visibile since we are using a scrolling image
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3 # vertical pixels between scanlines drawn on the CRT overlay
    DEFAULT_BG_SCROLL_SPEED = 50
    BG_SCROLL_STEP = 25 # how many pixels the background moves each difficulty step (lower = smoother, higher = more noticeable)
    BG_SCROLL_MAX = 500 # maximum scroll speed for the background, to prevent it from becoming too fast at high scores
    TITLE = "Typing Hero"

class PlayerSettings:
    """Contains all the settings related to the player, including movement speed, rotation, scale, laser cooldowns, and other gameplay parameters."""
    MAX_HEALTH = 3
    SPEED = 2
    SPEED_BOOST = 2
    BRAKE_WORLD_SPEED_MULT = 0.45
    BOOST_DRAIN_PER_SECOND = 0.70 # meter drained per second while boost is held
    BOOST_RECHARGE_PER_SECOND = 0.25 # meter recharged per second when not boosting
    SCALE = 0.15
    DEFAULT_LASER_COOLDOWN = 600 # lower numbers = faster rate of fire
    RAPID_FIRE_TIER_1_COOLDOWN = DEFAULT_LASER_COOLDOWN / 2
    RAPID_FIRE_TIER_2_COOLDOWN = 150
    SHIELD_DURATION = 7000 # how long the shield lasts in milliseconds
    RAINBOW_BEAM_DURATION = 5000        # 5 seconds (shorter than rapid fire)
    DEATH_DELAY = 500
    FLASH_DURATION = 1000 # Total time to flash in milliseconds
    FLASH_INTERVAL = 50 # How fast it toggles (smaller = faster flicker)
    JOYSTICK_DEADZONE = 0.2
    CONFUSION_TIMEOUT = 4000 # how long the confusion effect lasts after being hit by a blue alien attack (in milliseconds)

class ControllerSettings:
    """Holds all the settings related to the game controller, including button mappings and joystick axes."""
    A_BUTTON = 0
    B_BUTTON = 1
    X_BUTTON = 2
    Y_BUTTON = 3
    L1_BUTTON = 4
    R1_BUTTON = 5
    BACK_BUTTON = 6
    START_BUTTON = 7
    # Held simultaneously, this chord exits the game from anywhere — matches the
    # arcade cabinet panel labels (L1+R1+START+SELECT).
    QUIT_COMBO = (START_BUTTON, BACK_BUTTON, L1_BUTTON, R1_BUTTON)
    LEFT_STICK_X = 0
    LEFT_STICK_Y = 1

class AlienSettings:
    """
    Defines all the settings related to the alien enemies,
    including spawn rates, movement speeds, point values, colors,
    and probabilities for spawning and dropping powerups.
    """
    SPAWN_RATE = 600 # lower numbers = faster rate of enemy spawn
    MIN_SPAWN_RATE = 150  # Hard limit on how fast they spawn

    LASER_RATE = 400 # lower numbers = more lasers
    MIN_LASER_RATE = 100  # Hard limit on how fast they shoot

    DIFFICULTY_STEP = 5000 # Increase difficulty every x amount of points

    SPAWN_OFFSET = (-300, -100)
    COLOR = ['red', 'green', 'yellow', 'blue']
    SPAWN_CHANCE = [50, 30, 15, 5] # probability of each color alien appearing
    ANIMATION_SPEED = 0.015  # higher is faster, lower is slower

    # Movement speeds for each alien color (how fast each alien moves down the screen)
    SPEED = {
        'red':    1,
        'green':  2,
        'yellow': 3,
        'blue':   5
        }

    ZIGZAG_THRESHOLD = 100 # how wide the zigzag pattern is for yellow aliens (in pixels)
    # Aliens are killed once they fall this many pixels past the bottom edge.
    # The cushion prevents them dying mid-score-display.
    OFFSCREEN_MARGIN = 50

    # Point values for each alien color
    POINTS = {
        'red':    100,
        'green':  200,
        'yellow': 300,
        'blue':   500
        }

    # Probability of each alien dropping a powerup upon destruction, by color
    DROP_CHANCE = {
        'red':    0.20,
        'green':  0.20,
        'yellow': 0.20,
        'blue':   0.10,
    }

    # Blue alien confusion attack settings
    CONFUSION_CHANCE = 0.1 # chance that a blue alien will trigger the confusion attack
    CONFUSION_STOP_Y = ScreenSettings.HEIGHT // 2 # Halfway down screen
    CONFUSION_DURATION = 3000 # How long the alien stays to project it's confusion attack (in milliseconds)
    # Visual tuning for the downward-fanning confusion beam (drawn by Alien
    # while is_confusing is True). The beam starts narrow and widens by a
    # fraction of its current length each frame.
    CONFUSION_BEAM_TOP_WIDTH = 10
    CONFUSION_BEAM_WIDEN_RATIO = 0.2
    CONFUSION_BEAM_GROWTH_PER_FRAME = 15
    CONFUSION_BEAM_COLOR = (200, 0, 255, 80)
    # Tint the player ship is multiplied by while confused (purple/magenta).
    CONFUSION_PLAYER_TINT = (200, 0, 255, 255)

class LaserSettings:
    """Contains all the settings related to lasers fired by both the player and aliens, including dimensions, speeds, and colors for different laser types."""
    DEFAULT_WIDTH = 4
    HEIGHT = 20
    PLAYER_LASER_SPEED = -8
    ALIEN_LASER_SPEED = 4
    COLORS = {
        'single': ('green', 'white'),
        'twin': ('green', 'white'),
        'burst': ('cyan', 'white'),
        'hyper': ('cyan', 'white'), # Hyper
        'rapid': ('yellow', 'white'), # Rapid (any tier)
        'hyper_rapid': ('cyan', 'yellow'), # Hyper + Rapid alternation
        'alien': ('red', 'white'),
        'rainbow': None
    }

    # Rainbow Beam Settings
    RAINBOW_BEAM_WIDTH = ScreenSettings.WIDTH
    RAINBOW_BEAM_GROWTH_SPEED = 5 # Pixels added per frame
    RAINBOW_HUE_STEP = 4
    RAINBOW_SEGMENTS = 5
    # Divide the laser into 5 vertical segments for a "flow" effect
    SEGMENT_HEIGHT = HEIGHT // RAINBOW_SEGMENTS
    RAINBOW_SEGMENT_SHIFT = 20

class PowerupSettings:
    """
    Defines all the settings related to powerups that the player can collect,
    including their size, movement speed, flashing animation speed,
    and the different types of powerups with their associated colors, effects, and shapes.
    """
    RADIUS = 12
    SPEED = 2 # how fast the powerup floats down?
    FLASH_SPEED = 200 # 200 milliseconds .2 seconds?
    RAINBOW_STAR_HUE_DIVISOR = 4 # lower = faster rainbow cycling

    DATA = {
    'red':    {'draw_color': (255, 80, 80),  'type': 'heal',       'shape': 'heart'},
    'red_shield': {'draw_color': (80, 255, 255), 'type': 'shield', 'shape': 'circle'},
    'green':  {'draw_color': (60, 255, 100), 'type': 'laser_upgrade', 'shape': 'diamond'},
    'yellow': {'draw_color': (255, 220, 60), 'type': 'rapid_fire', 'shape': 'diamond'},
    'blue':   {'draw_color': (80, 160, 255), 'type': 'rainbow_beam', 'shape': 'star'},
    'bomb':   {'draw_color': (255, 40, 40),  'type': 'bomb',        'shape': 'circle'},
    }

class BombSettings:
    """Contains tuning values for bomb inventory, drops, projectile behavior, and blast visuals."""
    START_COUNT = 3
    PROJECTILE_RADIUS = 10
    PROJECTILE_SPEED = -2
    FLASH_SPEED = 220

    # Projectile colors flip between BASE and FLASH every FLASH_SPEED ms.
    PROJECTILE_BASE_COLOR = (10, 10, 10)
    PROJECTILE_FLASH_COLOR = (55, 55, 55)
    PROJECTILE_OUTLINE_COLOR = (255, 40, 40)
    PROJECTILE_OUTLINE_WIDTH = 2

    BLAST_START_RADIUS = 10
    BLAST_MAX_RADIUS = 160
    BLAST_GROWTH = 3
    BLAST_ALPHA = 110
    BLAST_RING_ALPHA = 235
    BLAST_RING_WIDTH = 3
    BLAST_FILL_COLOR = (255, 255, 255)

class ExplosionSettings:
    """
    Contains all the settings related to explosion animations,
    including the number of frames in the sprite sheet, animation speed,
    size of each frame, and scale for rendering.
    """
    FRAMES = 7 # there are seven unique images in the explosion sprite sheet
    ANIMATION_SPEED = 0.15 # smaller numbers = slower explosion animation. Always 0.x
    SIZE = 192 # size of each frame in the spritesheet, definse both width and height
    SCALE = 0.5

class FontSettings:
    """
    Defines the settings related to fonts used in the game,
    including the path to the font file, sizes for different text elements,
    and the color of the text.
    """
    FONT = os.path.join(os.path.dirname(__file__), 'assets', 'font', 'Pixeled.ttf')
    SMALL = 10
    MEDIUM = 20
    LARGE = 30
    COLOR = 'white'
    DEFAULT_INITIALS = "AAA"

class UISettings:
    """
    Contains settings related to the user interface elements,
    such as the size and spacing of heart sprites for health display,
    and the duration for which volume changes are displayed on the screen.
    """
    HEART_SPRITE_SIZE = (24, 24)
    HEART_SPACING = 10
    HEART_TOP_MARGIN = 8
    HEART_RIGHT_MARGIN = 30 # space between rightmost heart and screen edge
    VOLUME_DISPLAY_TIME = 1000

    # Player status row anchored under the hearts row.
    STATUS_RIGHT_MARGIN = 10
    STATUS_ROW_SPACING = 15
    # Boost meter geometry — sits directly under the hearts.
    BOOST_METER_WIDTH = 100
    BOOST_METER_HEIGHT = 8
    # Vertical gap between the hearts row and the meter.
    BOOST_METER_TOP_GAP = 9
    # Vertical gap between the meter and the first status row.
    BOOST_METER_BOTTOM_GAP = 10
    # Vertical gap between the last status row and the bombs row.
    BOMBS_ROW_TOP_GAP = 16

    # Volume Bar Settings
    MAX_VOLUME = 1000
    VOLUME_BAR__LENGTH = 150
    VOLUME_BAR_RATIO = MAX_VOLUME / VOLUME_BAR__LENGTH

class AudioSettings:
    """
    Defines settings related to audio in the game,
    including the volume boost applied during the intro sequence
    and the default master volume level for all sounds.
    """
    INTRO_VOL_BOOST = 2.0
    DEFAULT_MASTER_VOLUME = 0.5 # default value is 1.0
    DEBUG_MUTE = False # set True to silence all audio for debugging
    # All bundled media now lives under a single assets/ folder
    # (assets/audio, assets/font, assets/graphics, assets/music) so the
    # project root only carries code + docs + saves.
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    MUSIC_DIR = os.path.join(ASSETS_DIR, 'music')
    AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')
    BGM_PLAYLIST = [
        'star_hero.ogg'
    ]

class AssetPaths:
    """Centralized filesystem paths for static graphics used by the game."""
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    GRAPHICS_DIR = os.path.join(ASSETS_DIR, 'graphics')
    BACKGROUND = os.path.join(GRAPHICS_DIR, 'background.png')
    EXPLOSION = os.path.join(GRAPHICS_DIR, 'explosion.png')
    PLAYER = os.path.join(GRAPHICS_DIR, 'player_ship.png')
    HEART = os.path.join(GRAPHICS_DIR, 'heart.png')
    TV = os.path.join(GRAPHICS_DIR, 'tv.png')
