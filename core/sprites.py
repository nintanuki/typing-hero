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


class RainbowBeam(pygame.sprite.Sprite):
    """A slow wide expanding beam fired from the bottom-center of the screen.

    Starts 1 px wide and grows to full screen width over ~1 second while drifting
    upward.  Any alien the beam overlaps is destroyed once.
    """

    def __init__(self):
        """Spawn at the bottom-center of the screen with a 1-pixel starting width."""
        super().__init__()
        self.is_piercing = True
        self.hit_aliens = set()
        self.hue = 0
        self.current_width = 1
        self.target_width = ScreenSettings.WIDTH
        self.image = pygame.Surface(
            (self.current_width, PowerupSettings.RAINBOW_BEAM_HEIGHT)
        )
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect(
            midbottom=(ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT)
        )
        self.pos_y = float(self.rect.y)

    def _rebuild_surface(self):
        """Recreate the surface at the new width, preserving vertical position."""
        self.image = pygame.Surface(
            (self.current_width, PowerupSettings.RAINBOW_BEAM_HEIGHT)
        )
        self.rect = self.image.get_rect(
            midtop=(ScreenSettings.WIDTH // 2, round(self.pos_y))
        )

    def _grow(self):
        """Widen the beam by RAINBOW_BEAM_GROWTH_SPEED px until target width is reached."""
        if self.current_width < self.target_width:
            self.current_width = min(
                self.target_width,
                self.current_width + PowerupSettings.RAINBOW_BEAM_GROWTH_SPEED,
            )
            self._rebuild_surface()

    def _animate_rainbow(self):
        """Advance the hue and fill the beam surface with shifting rainbow segments."""
        self.hue = (self.hue + PowerupSettings.RAINBOW_BEAM_HUE_STEP) % 360
        segment_height = (
            PowerupSettings.RAINBOW_BEAM_HEIGHT // PowerupSettings.RAINBOW_BEAM_SEGMENTS
        )
        for i in range(PowerupSettings.RAINBOW_BEAM_SEGMENTS):
            seg_hue = (self.hue + i * PowerupSettings.RAINBOW_BEAM_SEGMENT_SHIFT) % 360
            color = pygame.Color(0)
            color.hsva = (seg_hue, 100, 100, 100)
            seg_rect = pygame.Rect(
                0, i * segment_height, self.current_width, segment_height
            )
            self.image.fill(color, seg_rect)

    def update(self):
        """Grow, animate, drift upward one frame, and self-destruct when off-screen."""
        self._grow()
        self._animate_rainbow()
        self.pos_y += PowerupSettings.RAINBOW_BEAM_SPEED
        self.rect.y = round(self.pos_y)
        if self.rect.bottom < 0:
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    """A falling powerup that triggers once it reaches the bottom of the screen."""

    def __init__(self, pos, kind):
        super().__init__()
        self.kind = kind

        if self.kind == PowerupSettings.HEART_TYPE:
            self.image = pygame.image.load(AssetPaths.HEART).convert_alpha()
            self.rect = self.image.get_rect(center=pos)
            return

        diameter = PowerupSettings.RADIUS * 2
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        if self.kind == PowerupSettings.BURST_TYPE:
            self._draw_yellow_diamond()
        elif self.kind == PowerupSettings.RAINBOW_BEAM_TYPE:
            self._draw_blue_diamond()
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

    def _draw_blue_diamond(self):
        """Render the blue rainbow-beam token as a wider, flatter diamond."""
        # A flatter (wider) diamond distinguishes it visually from the other tokens.
        r = PowerupSettings.RADIUS
        points = [
            (r, 4),
            (r * 2, r),
            (r, r * 2 - 4),
            (0, r),
        ]
        pygame.draw.polygon(self.image, ColorSettings.COLORS['BLUE'], points)
        pygame.draw.polygon(self.image, ColorSettings.COLORS['WHITE'], points, width=2)

    def update(self):
        """Move down one frame at configured speed."""
        self.rect.y += PowerupSettings.SPEED

    def reached_bottom(self):
        """Return True once the powerup has reached the bottom edge of the screen."""
        return self.rect.top >= ScreenSettings.HEIGHT