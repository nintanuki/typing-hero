import pygame
import random
from settings import *


class CRT:
    """CRT scanline overlay and damage-flash vignette compositor."""

    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.tv = pygame.image.load(AssetPaths.TV).convert_alpha()
        self.tv = pygame.transform.scale(self.tv, ScreenSettings.RESOLUTION)

        # Damage flash overlays — loaded once, reused every flash frame.
        self.tv_blue = pygame.image.load(AssetPaths.TV_BLUE).convert_alpha()
        self.tv_blue = pygame.transform.scale(self.tv_blue, ScreenSettings.RESOLUTION)
        self.tv_red = pygame.image.load(AssetPaths.TV_RED).convert_alpha()
        self.tv_red = pygame.transform.scale(self.tv_red, ScreenSettings.RESOLUTION)
        self.tv_white = pygame.image.load(AssetPaths.TV_WHITE).convert_alpha()
        self.tv_white = pygame.transform.scale(self.tv_white, ScreenSettings.RESOLUTION)

    def _create_crt_lines(self):
        """Draw horizontal scanlines onto the tv surface each frame."""
        line_height = ScreenSettings.CRT_SCANLINE_HEIGHT
        line_amount = int(ScreenSettings.HEIGHT / line_height)
        for line in range(line_amount):
            y_pos = line * line_height
            pygame.draw.line(self.tv, 'black', (0, y_pos), (ScreenSettings.WIDTH, y_pos), 1)

    def draw(self):
        """Composite the CRT scanline overlay onto the screen with a randomized alpha flicker.

        Future: accept a crt_enabled flag here to skip the blit when the player
        turns off the CRT effect — damage flashes are unaffected because they
        use a separate draw_damage_flash() call.
        """
        self.tv.set_alpha(random.randint(*ScreenSettings.CRT_ALPHA_RANGE))
        self._create_crt_lines()
        self.screen.blit(self.tv, (0, 0))

    def draw_damage_flash(self, show_red: bool) -> None:
        """Blit the red or white vignette for hit feedback.

        Intentionally separate from draw() so a future CRT-disable toggle
        cannot accidentally suppress the damage indicator.

        Args:
            show_red: True for the red phase, False for the white phase.
        """
        overlay = self.tv_red if show_red else self.tv_white
        overlay.set_alpha(DamageSettings.FLASH_ALPHA)
        self.screen.blit(overlay, (0, 0))

    def draw_shield_flash(self, show_blue: bool) -> None:
        """Blit the shield vignette while the shield powerup is active.

        Args:
            show_blue: True for the blue phase, False for the white phase.
        """
        overlay = self.tv_blue if show_blue else self.tv_white
        overlay.set_alpha(ShieldSettings.FLASH_ALPHA)
        self.screen.blit(overlay, (0, 0))
