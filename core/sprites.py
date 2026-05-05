"""Sprite classes for Typing Hero."""

import os

import pygame

from core.animations import Explosion
from settings import AlienSettings, AssetPaths, ColorSettings, ScreenSettings, WordSettings


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

    def update(self):
        """Advance one frame of descent at color speed scaled by level multiplier."""
        self.position.y += AlienSettings.SPEED[self.color] * self.level_speed_multiplier
        self.rect.y = round(self.position.y)

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
    """A vertical beam that travels up the screen to destroy a targeted alien."""

    def __init__(self, target_alien, explosion_group, audio):
        super().__init__()
        self.image = pygame.Surface((4, 20))
        self.image.fill(ColorSettings.COLORS['WHITE'])
        self.rect = self.image.get_rect(midbottom=(target_alien.rect.centerx, ScreenSettings.HEIGHT))
        self.target = target_alien
        self.explosion_group = explosion_group
        self.speed = -8
        self.audio = audio

    def update(self):
        """Move up and kill both laser and target on contact."""
        self.rect.y += self.speed
        if self.rect.colliderect(self.target.rect) or self.rect.top <= self.target.rect.centery:
            impact_explosion = Explosion(self.target.rect.centerx, self.target.rect.centery)
            self.explosion_group.add(impact_explosion)
            if self.audio:
                self.audio.play('explosion')
            self.target.kill()
            self.kill()
        elif self.rect.bottom < 0:
            self.kill()