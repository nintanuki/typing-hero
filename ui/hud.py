"""HUD overlays: hearts row, score readout, game-over banner, intro screen, and pause."""

import pygame

from settings import (
    AssetPaths,
    FontSettings,
    GameOverSettings,
    HeartSettings,
    IntroSettings,
    LeaderboardSettings,
    PauseSettings,
    ScoreSettings,
    ScreenSettings,
)


def _draw_leaderboard(surface, leaderboard, font, start_y):
    """Draw a 'TOP 10' leaderboard table centered on ``surface``."""
    cx = ScreenSettings.WIDTH // 2
    title_surf = font.render(LeaderboardSettings.TITLE, True, LeaderboardSettings.COLOR)
    surface.blit(title_surf, title_surf.get_rect(center=(cx, start_y)))
    y = start_y + LeaderboardSettings.ROW_HEIGHT
    for i, entry in enumerate(leaderboard, start=1):
        text = f"{i:>2}. {entry['name']}  {entry['score']}"
        row_surf = font.render(text, True, LeaderboardSettings.COLOR)
        surface.blit(row_surf, row_surf.get_rect(center=(cx, y)))
        y += LeaderboardSettings.ROW_HEIGHT


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
    """Renders the game-over banner, run score, initials entry or leaderboard, and prompt."""

    def __init__(self):
        banner_font = pygame.font.Font(FontSettings.FONT, GameOverSettings.BANNER_SIZE)
        self._score_font = pygame.font.Font(FontSettings.FONT, GameOverSettings.SCORE_SIZE)
        self._initials_font = pygame.font.Font(FontSettings.FONT, GameOverSettings.BANNER_SIZE)
        self._lb_font = pygame.font.Font(FontSettings.FONT, LeaderboardSettings.SIZE)
        prompt_font = pygame.font.Font(FontSettings.FONT, GameOverSettings.PROMPT_SIZE)

        self._banner_surf = banner_font.render(
            GameOverSettings.BANNER_TEXT.upper(), True, GameOverSettings.COLOR
        )
        self._prompt_surf = prompt_font.render(
            GameOverSettings.PROMPT_TEXT.upper(), True, GameOverSettings.COLOR
        )
        self._initials_prompt_surf = prompt_font.render(
            GameOverSettings.INITIALS_PROMPT_TEXT.upper(), True, GameOverSettings.COLOR
        )
        self._hint_font = pygame.font.Font(FontSettings.FONT, FontSettings.SMALL)
        self._hint_surf = self._hint_font.render(
            'UP/DN: CHANGE  L/R: MOVE', True, GameOverSettings.COLOR
        )

        cx = ScreenSettings.WIDTH // 2
        self._banner_rect = self._banner_surf.get_rect(
            center=(cx, GameOverSettings.BANNER_CENTER_Y)
        )
        self._prompt_rect = self._prompt_surf.get_rect(
            center=(cx, GameOverSettings.PROMPT_CENTER_Y)
        )
        self._initials_prompt_rect = self._initials_prompt_surf.get_rect(
            center=(cx, GameOverSettings.PROMPT_CENTER_Y)
        )

    def draw(self, surface, score, scores):
        """Draw banner, run score, then either initials entry or leaderboard + prompt."""
        cx = ScreenSettings.WIDTH // 2

        surface.blit(self._banner_surf, self._banner_rect)

        score_surf = self._score_font.render(
            f'YOUR SCORE: {score}', True, GameOverSettings.COLOR
        )
        surface.blit(score_surf, score_surf.get_rect(
            center=(cx, GameOverSettings.SCORE_CENTER_Y)
        ))

        if scores.entering_initials:
            self._draw_initials(surface, scores.initials, scores.initials_index)
            hint_rect = self._hint_surf.get_rect(
                center=(cx, GameOverSettings.INITIALS_CENTER_Y + 45)
            )
            surface.blit(self._hint_surf, hint_rect)
            surface.blit(self._initials_prompt_surf, self._initials_prompt_rect)
        else:
            lb = scores.save_data.get('leaderboard', [])
            if lb:
                _draw_leaderboard(
                    surface, lb, self._lb_font, GameOverSettings.LEADERBOARD_START_Y
                )
            surface.blit(self._prompt_surf, self._prompt_rect)

    def _draw_initials(self, surface, initials, cursor_idx):
        """Render the 3-letter initials with cursor highlighting."""
        cx = ScreenSettings.WIDTH // 2
        cy = GameOverSettings.INITIALS_CENTER_Y
        spacing = 44
        offsets = [-spacing, 0, spacing]
        for i, (letter, x_offset) in enumerate(zip(initials, offsets)):
            color = (
                GameOverSettings.CURSOR_COLOR
                if i == cursor_idx
                else GameOverSettings.COLOR
            )
            surf = self._initials_font.render(letter, True, color)
            rect = surf.get_rect(center=(cx + x_offset, cy))
            surface.blit(surf, rect)
            if i == cursor_idx:
                underline = pygame.Rect(rect.left, rect.bottom + 3, rect.width, 3)
                pygame.draw.rect(surface, GameOverSettings.CURSOR_COLOR, underline)


class IntroScreen:
    """Renders the title screen: game name, ship, leaderboard or high score, and start prompt."""

    def __init__(self):
        title_font = pygame.font.Font(FontSettings.FONT, IntroSettings.TITLE_SIZE)
        prompt_font = pygame.font.Font(FontSettings.FONT, IntroSettings.PROMPT_SIZE)
        self._hs_font = pygame.font.Font(FontSettings.FONT, IntroSettings.HIGH_SCORE_SIZE)
        self._lb_font = pygame.font.Font(FontSettings.FONT, LeaderboardSettings.SIZE)

        self._title_surf = title_font.render(
            IntroSettings.TITLE_TEXT.upper(), True, IntroSettings.COLOR
        )
        self._prompt_surf = prompt_font.render(
            IntroSettings.PROMPT_TEXT.upper(), True, IntroSettings.COLOR
        )

        cx = ScreenSettings.WIDTH // 2
        self._title_rect = self._title_surf.get_rect(
            center=(cx, IntroSettings.TITLE_CENTER_Y)
        )
        self._prompt_rect = self._prompt_surf.get_rect(
            center=(cx, IntroSettings.PROMPT_CENTER_Y)
        )

        ship_raw = pygame.image.load(AssetPaths.PLAYER).convert_alpha()
        self._ship_surf = pygame.transform.rotozoom(ship_raw, 0, 0.2)
        self._ship_rect = self._ship_surf.get_rect(
            center=(cx, IntroSettings.SHIP_CENTER_Y)
        )

    def draw(self, surface, scores):
        """Draw title, ship, leaderboard or high score, and start prompt."""
        cx = ScreenSettings.WIDTH // 2
        surface.blit(self._title_surf, self._title_rect)
        surface.blit(self._ship_surf, self._ship_rect)

        lb = scores.save_data.get('leaderboard', [])
        if lb:
            _draw_leaderboard(
                surface, lb, self._lb_font, IntroSettings.LEADERBOARD_START_Y
            )
        else:
            hs_surf = self._hs_font.render(
                f'{IntroSettings.HIGH_SCORE_TEXT_PREFIX}{scores.high_score}',
                True,
                IntroSettings.COLOR,
            )
            surface.blit(hs_surf, hs_surf.get_rect(
                center=(cx, IntroSettings.HIGH_SCORE_CENTER_Y)
            ))

        surface.blit(self._prompt_surf, self._prompt_rect)


class PauseScreen:
    """Renders a centered 'PAUSED' banner."""

    def __init__(self):
        font = pygame.font.Font(FontSettings.FONT, PauseSettings.SIZE)
        self._surf = font.render(PauseSettings.TEXT.upper(), True, PauseSettings.COLOR)
        self._rect = self._surf.get_rect(center=ScreenSettings.CENTER)

    def draw(self, surface):
        """Blit the pause banner onto ``surface``."""
        surface.blit(self._surf, self._rect)

