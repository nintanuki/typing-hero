"""HUD overlays: hearts row, score readout, and game-over banner."""

import pygame

from settings import (
    AssetPaths,
    FontSettings,
    GameOverSettings,
    HeartSettings,
    ScoreSettings,
    ScreenSettings,
)


class HeartsHUD:
    """Renders the player-health row in the top-right corner."""

    def __init__(self):
        self.heart_surf = pygame.image.load(AssetPaths.HEART).convert_alpha()
        self._heart_width = self.heart_surf.get_width()
        self._row_left_x = ScreenSettings.WIDTH - (
            self._heart_width * HeartSettings.MAX
            + HeartSettings.RIGHT_MARGIN
        )

    def draw(self, surface, hearts):
        """Blit ``hearts`` heart icons starting at the row's left edge."""
        hearts = max(0, min(hearts, HeartSettings.MAX))
        for index in range(hearts):
            x = self._row_left_x + index * (
                self._heart_width + HeartSettings.SPACING
            )
            surface.blit(self.heart_surf, (x, HeartSettings.TOP_MARGIN))


class ScoreHUD:
    """Renders the current score and persistent high score in the top-left."""

    def __init__(self):
        self._high_score_font = pygame.font.Font(
            FontSettings.FONT, ScoreSettings.HIGH_SCORE_SIZE
        )
        self._score_font = pygame.font.Font(
            FontSettings.FONT, ScoreSettings.SCORE_SIZE
        )

    def draw(self, surface, score, high_score):
        """Render the high-score row above the current-score row."""
        high_surf = self._high_score_font.render(
            f'HIGH SCORE: {high_score}', True, ScoreSettings.COLOR
        )
        surface.blit(high_surf, ScoreSettings.HIGH_SCORE_TOPLEFT)

        score_surf = self._score_font.render(
            f'SCORE: {score}', True, ScoreSettings.COLOR
        )
        surface.blit(score_surf, ScoreSettings.SCORE_TOPLEFT)


class GameOverScreen:
    """Renders the game-over banner and restart prompt."""

    def __init__(self):
        banner_font = pygame.font.Font(
            FontSettings.FONT, GameOverSettings.BANNER_SIZE
        )
        prompt_font = pygame.font.Font(
            FontSettings.FONT, GameOverSettings.PROMPT_SIZE
        )
        self._banner_surf = banner_font.render(
            GameOverSettings.BANNER_TEXT.upper(),
            True,
            GameOverSettings.COLOR,
        )
        self._prompt_surf = prompt_font.render(
            GameOverSettings.PROMPT_TEXT.upper(),
            True,
            GameOverSettings.COLOR,
        )
        cx, cy = ScreenSettings.CENTER
        self._banner_rect = self._banner_surf.get_rect(
            center=(cx, cy - GameOverSettings.BANNER_OFFSET)
        )
        self._prompt_rect = self._prompt_surf.get_rect(
            center=(cx, cy + GameOverSettings.PROMPT_OFFSET)
        )

    def draw(self, surface):
        """Blit the banner and prompt onto ``surface``."""
        surface.blit(self._banner_surf, self._banner_rect)
        surface.blit(self._prompt_surf, self._prompt_rect)
