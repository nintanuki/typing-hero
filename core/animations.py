import pygame
from settings import *

# see https://www.youtube.com/watch?v=VUFvY349ess for more details
class Background(pygame.sprite.Sprite):
    """Seamlessly scrolling space background."""

    def __init__(self, groups):
        super().__init__(groups)
        bg_image = pygame.image.load(AssetPaths.BACKGROUND).convert()
        full_height = bg_image.get_height()
        full_width = bg_image.get_width()
        self.image = pygame.Surface((full_width, full_height * 2))
        self.image.blit(bg_image, (0, 0))
        self.image.blit(bg_image, (0, full_height))
        self.rect = self.image.get_rect(bottomleft=(0, ScreenSettings.HEIGHT))
        self.pos = pygame.math.Vector2(self.rect.bottomleft)
        self.scroll_speed = ScreenSettings.DEFAULT_BG_SCROLL_SPEED

    def update(self, delta_time, speed_multiplier=1.0):
        """Scroll downward and loop when the image has fully passed."""
        self.pos.y += self.scroll_speed * delta_time * speed_multiplier
        if self.rect.top >= 0:
            self.pos.y = -self.image.get_height() / 2
        self.rect.y = round(self.pos.y)


class Explosion(pygame.sprite.Sprite):
    """Sprite-sheet explosion animation."""

    def __init__(self, pos_x, pos_y):
        super().__init__()
        self.is_animating = True

        sprite_sheet = pygame.image.load(AssetPaths.EXPLOSION).convert_alpha()

        self.sprites = [
            self.get_image(sprite_sheet,
                           frame,
                           ExplosionSettings.SIZE,
                           ExplosionSettings.SIZE,
                           ExplosionSettings.SCALE)
            for frame in range(ExplosionSettings.FRAMES)
        ]

        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=(pos_x, pos_y))

    @staticmethod
    def get_image(sheet, frame, width, height, scale):
        """Extract and scale a single frame from a sprite sheet."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.blit(sheet, (0, 0), ((frame * width), 0, width, height))
        surf = pygame.transform.scale(surf, (width * scale, height * scale))
        return surf

    def update(self):
        """Advance one animation frame; kill the sprite when the animation ends."""
        if self.is_animating:
            self.current_sprite += ExplosionSettings.ANIMATION_SPEED
            if int(self.current_sprite) >= len(self.sprites):
                self.kill()
            else:
                self.image = self.sprites[int(self.current_sprite)]
