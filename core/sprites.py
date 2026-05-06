"""Sprite classes for Typing Hero."""

import os
import random

import pygame

from core.animations import Explosion
from settings import (
    AlienSettings,
    AssetPaths,
    ColorSettings,
    LaserSettings,
    PowerupSettings,
    ScreenSettings,
    WordSettings,
)


class Alien(pygame.sprite.Sprite):
    """An enemy that carries a word the player must type to destroy it."""

    level_speed_multiplier = 1.0

    def __init__(self, color, pos, word):
        super().__init__()
        self.color = color
        self.word = word

        sprite_path = os.path.join(AssetPaths.GRAPHICS_DIR, f'{color}1.png')
        self.image = pygame.image.load(sprite_path).convert_alpha()
        self.rect = self.image.get_rect(center=pos)

        # Float accumulator so sub-pixel SPEED values advance honestly.
        self.position = pygame.math.Vector2(self.rect.topleft)
        self.is_dying = False

        # Zigzag state: active for yellow and blue only.
        # Yellow flips direction on a frame counter; blue wall-bounces only.
        self.zigzag_direction = random.choice((-1, 1)) if color in ('yellow', 'blue') else 0
        self.zigzag_counter = 0

    def _move_zigzag(self):
        """Advance horizontal zigzag oscillation for yellow and blue aliens.

        Yellow flips direction every ZIGZAG_THRESHOLD frames (wide sweep).
        Blue wall-bounces continuously without a timer (tighter bounce).
        Both reverse immediately on hitting a screen edge.
        """
        self.position.x += (
            self.zigzag_direction
            * AlienSettings.ZIGZAG_HORIZONTAL_SPEED
            * self.level_speed_multiplier
        )
        self.rect.x = round(self.position.x)

        if self.color == 'yellow':
            self.zigzag_counter += 1
            if self.zigzag_counter >= AlienSettings.ZIGZAG_THRESHOLD:
                self.zigzag_counter = 0
                self.zigzag_direction *= -1

        # Both colors bounce off screen edges.
        if self.rect.left < 0:
            self.rect.left = 0
            self.position.x = float(self.rect.x)
            self.zigzag_direction = 1
        elif self.rect.right > ScreenSettings.WIDTH:
            self.rect.right = ScreenSettings.WIDTH
            self.position.x = float(self.rect.x)
            self.zigzag_direction = -1

    def update(self):
        """Advance one frame of descent at color speed scaled by level multiplier."""
        self.position.y += AlienSettings.SPEED[self.color] * self.level_speed_multiplier
        self.rect.y = round(self.position.y)
        if self.color in ('yellow', 'blue'):
            self._move_zigzag()

    @classmethod
    def set_level_speed_multiplier(cls, multiplier):
        """Set shared scalar applied to all aliens' per-color base speeds."""
        cls.level_speed_multiplier = max(0.0, float(multiplier))

    def draw_word(self, surface, font, prefix_length=0):
        """Render ``self.word`` centered above the sprite.

        When ``prefix_length > 0``, the typed prefix renders in
        ``PREFIX_COLOR`` and the remaining suffix in ``COLOR``.
        The combined width is centered over the sprite so the word
        stays aligned as letters are typed.
        """
        full = self.word.upper()
        prefix_length = max(0, min(prefix_length, len(full)))

        if prefix_length == 0:
            word_surf = font.render(full, True, WordSettings.COLOR)
            word_rect = word_surf.get_rect(
                midbottom=(self.rect.centerx, self.rect.top - WordSettings.OFFSET_ABOVE_SPRITE)
            )
            surface.blit(word_surf, word_rect)
            return

        # Two-color path: center the combined prefix+suffix width over the sprite.
        prefix_surf = font.render(
            full[:prefix_length], True, WordSettings.PREFIX_COLOR
        )
        suffix_surf = font.render(
            full[prefix_length:], True, WordSettings.COLOR
        )
        total_width = prefix_surf.get_width() + suffix_surf.get_width()
        baseline_y = self.rect.top - WordSettings.OFFSET_ABOVE_SPRITE
        left_x = self.rect.centerx - total_width // 2
        prefix_rect = prefix_surf.get_rect(bottomleft=(left_x, baseline_y))
        suffix_rect = suffix_surf.get_rect(
            bottomleft=(left_x + prefix_surf.get_width(), baseline_y)
        )
        surface.blit(prefix_surf, prefix_rect)
        surface.blit(suffix_surf, suffix_rect)

class KillLaser(pygame.sprite.Sprite):
    """A real player laser projectile that travels upward and may pierce aliens."""

    def __init__(self, x, colors=None, is_piercing=False):
        super().__init__()
        self.colors = colors or LaserSettings.COLORS['single']
        self.color_index = 0
        self.image = pygame.Surface((LaserSettings.WIDTH, LaserSettings.HEIGHT))
        self.image.fill(self.colors[self.color_index])
        self.rect = self.image.get_rect(midbottom=(x, ScreenSettings.HEIGHT))
        self.speed = LaserSettings.SPEED
        self.is_piercing = is_piercing
        self.hit_aliens = set()

    def _animate_flicker(self):
        """Alternate between the configured beam colors each frame."""
        self.color_index = 1 - self.color_index
        self.image.fill(self.colors[self.color_index])

    def update(self):
        """Advance the projectile upward until it leaves the screen."""
        self.rect.y += self.speed
        self._animate_flicker()
        if self.rect.bottom < 0:
            self.kill()


class RainbowLaser(pygame.sprite.Sprite):
    """One slice of the rainbow beam: starts 1 px wide, grows wide, travels up.

    The cone effect emerges from the GameManager spawning one of these per frame
    while the rainbow beam is active.  Older slices have grown wider and traveled
    further, so a stack of them forms an upside-down triangle naturally — same
    technique as the legacy game.
    """

    def __init__(self):
        """Spawn at the bottom-center of the screen, 1 px wide."""
        super().__init__()
        self.is_piercing = True
        self.hit_aliens = set()
        self.hue = 0
        self.current_width = 1
        self.target_width = PowerupSettings.RAINBOW_BEAM_WIDTH
        self.image = pygame.Surface(
            (self.current_width, PowerupSettings.RAINBOW_BEAM_HEIGHT)
        )
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect(
            midbottom=(ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT)
        )
        self.pos_y = float(self.rect.y)
        self.speed = LaserSettings.SPEED  # negative; same upward speed as kill lasers

    def _grow(self):
        """Widen the slice toward target_width, rebuilding the surface in place."""
        if self.current_width >= self.target_width:
            return
        self.current_width = min(
            self.target_width,
            self.current_width + PowerupSettings.RAINBOW_BEAM_GROWTH_SPEED,
        )
        old_center = self.rect.center
        self.image = pygame.Surface(
            (self.current_width, PowerupSettings.RAINBOW_BEAM_HEIGHT)
        )
        self.rect = self.image.get_rect(center=old_center)
        self.pos_y = float(self.rect.y)

    def _animate_rainbow(self):
        """Repaint the slice with shifting rainbow segments stacked vertically."""
        self.hue = (self.hue + PowerupSettings.RAINBOW_BEAM_HUE_STEP) % 360
        segment_height = (
            PowerupSettings.RAINBOW_BEAM_HEIGHT // PowerupSettings.RAINBOW_BEAM_SEGMENTS
        )
        for i in range(PowerupSettings.RAINBOW_BEAM_SEGMENTS):
            seg_hue = (self.hue + i * PowerupSettings.RAINBOW_BEAM_SEGMENT_SHIFT) % 360
            color = pygame.Color(0)
            color.hsva = (seg_hue, 100, 100, 100)
            self.image.fill(
                color,
                pygame.Rect(0, i * segment_height, self.current_width, segment_height),
            )

    def update(self):
        """Grow, animate, drift upward one frame, and self-destruct when off-screen."""
        self._grow()
        self._animate_rainbow()
        self.pos_y += self.speed
        self.rect.y = round(self.pos_y)
        if self.rect.bottom < 0:
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    """A falling powerup that triggers once it reaches the bottom of the screen."""

    def __init__(self, pos, kind):
        super().__init__()
        self.kind = kind
        self._anim_tick = 0
        self._anim_interval = 6
        self._anim_frame = 0

        if self.kind == PowerupSettings.HEART_TYPE:
            self.image = pygame.image.load(AssetPaths.HEART).convert_alpha()
            self.rect = self.image.get_rect(center=pos)
            return

        diameter = PowerupSettings.RADIUS * 2
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        if self.kind == PowerupSettings.BURST_TYPE:
            self._draw_yellow_diamond()
        elif self.kind == PowerupSettings.SHIELD_TYPE:
            self._draw_shield_circle()
        elif self.kind == PowerupSettings.RAINBOW_BEAM_TYPE:
            self._draw_rainbow_star()
        else:
            self._draw_green_diamond()
        self.rect = self.image.get_rect(center=pos)

    def _draw_green_diamond(self):
        """Render the green laser-upgrade token as a small filled diamond."""
        radius = PowerupSettings.RADIUS
        points = [
            (radius, 0),
            (radius * 2, radius),
            (radius, radius * 2),
            (0, radius),
        ]
        pygame.draw.polygon(self.image, ColorSettings.COLORS['GREEN'], points)
        pygame.draw.polygon(self.image, ColorSettings.COLORS['WHITE'], points, width=2)

    def _draw_yellow_diamond(self):
        """Render the yellow burst token as a small filled diamond."""
        radius = PowerupSettings.RADIUS
        points = [
            (radius, 0),
            (radius * 2, radius),
            (radius, radius * 2),
            (0, radius),
        ]
        pygame.draw.polygon(self.image, ColorSettings.COLORS['YELLOW'], points)
        pygame.draw.polygon(self.image, ColorSettings.COLORS['WHITE'], points, width=2)

    def _draw_shield_circle(self):
        """Render the shield token as a blue circle with a white outline."""
        radius = PowerupSettings.RADIUS
        center = (radius, radius)
        pygame.draw.circle(self.image, ColorSettings.COLORS['BLUE'], center, radius)
        pygame.draw.circle(self.image, ColorSettings.COLORS['WHITE'], center, radius, width=2)

    def _draw_star(self, fill_color, outline_color):
        """Draw a five-point star centered in the token surface.

        Args:
            fill_color: RGB tuple used to fill the star.
            outline_color: RGB tuple used for the star border.
        """
        radius = PowerupSettings.RADIUS
        cx, cy = radius, radius
        outer_radius = radius
        inner_radius = max(3, int(radius * 0.45))
        points = []
        for point_index in range(10):
            angle = (point_index * 36) - 90
            active_radius = outer_radius if point_index % 2 == 0 else inner_radius
            vector = pygame.math.Vector2()
            vector.from_polar((active_radius, angle))
            points.append((cx + vector.x, cy + vector.y))

        pygame.draw.polygon(self.image, fill_color, points)
        pygame.draw.polygon(self.image, outline_color, points, width=2)

    def _draw_rainbow_star(self):
        """Render the rainbow-beam token as a flashing rainbow star."""
        rainbow_frames = (
            ColorSettings.COLORS['RED'],
            ColorSettings.COLORS['YELLOW'],
            ColorSettings.COLORS['GREEN'],
            ColorSettings.COLORS['CYAN'],
            ColorSettings.COLORS['BLUE'],
            ColorSettings.COLORS['WHITE'],
        )
        frame_color = rainbow_frames[self._anim_frame % len(rainbow_frames)]
        self._draw_star(frame_color, ColorSettings.COLORS['WHITE'])

    def _animate(self):
        """Advance token-only animation frames for animated powerups."""
        if self.kind not in (PowerupSettings.RAINBOW_BEAM_TYPE,):
            return

        self._anim_tick += 1
        if self._anim_tick < self._anim_interval:
            return

        self._anim_tick = 0
        self._anim_frame += 1
        center = self.rect.center
        self.image.fill((0, 0, 0, 0))
        self._draw_rainbow_star()
        self.rect = self.image.get_rect(center=center)

    def update(self):
        """Move down one frame at configured speed."""
        self.rect.y += PowerupSettings.SPEED
        self._animate()

    def reached_bottom(self):
        """Return True once the powerup has reached the bottom edge of the screen."""
        return self.rect.top >= ScreenSettings.HEIGHT