"""Alien spawning driver."""

import random

import pygame

from core.sprites import Alien
from settings import ScoreSettings, ScreenSettings, SpawnSettings


class SpawnDirector:
    """Owns the alien-spawn timer and creates new ``Alien`` sprites on tick."""

    def __init__(self):
        self.spawn_event = pygame.event.custom_type()
        self._spawn_rate_ms = SpawnSettings.SPAWN_RATE
        pygame.time.set_timer(self.spawn_event, self._spawn_rate_ms)

    def spawn(self, aliens, word_manager, score=0):
        """Add one new alien to ``aliens`` with a unique word.

        Skips the tick if every word in the pool is already on screen.
        """
        level = self.level(score)
        in_use = {alien.word for alien in aliens}
        word = word_manager.pick_word(in_use, level)
        if word is None:
            return

        color = random.choices(
            SpawnSettings.COLORS,
            weights=SpawnSettings.SPAWN_CHANCE,
            k=1,
        )[0]
        x = random.randint(
            SpawnSettings.X_MARGIN,
            ScreenSettings.WIDTH - SpawnSettings.X_MARGIN,
        )
        aliens.add(Alien(color=color, pos=(x, SpawnSettings.SPAWN_Y), word=word))

    def adjust_difficulty(self, score):
        """Apply level-based spawn timing and alien speed multiplier.

        Returns the active spawn interval (ms).
        """
        level = self.level(score)
        new_rate = ScoreSettings.SPAWN_RATE_BY_LEVEL_MS[level - 1]
        if new_rate != self._spawn_rate_ms:
            self._spawn_rate_ms = new_rate
            pygame.time.set_timer(self.spawn_event, self._spawn_rate_ms)

        Alien.set_level_speed_multiplier(
            ScoreSettings.ALIEN_SPEED_MULTIPLIER_BY_LEVEL[level - 1]
        )
        return self._spawn_rate_ms

    def level(self, score):
        """Return score-derived level from configured threshold table."""
        safe_score = max(0, int(score))
        level = 1
        for idx, threshold in enumerate(ScoreSettings.LEVEL_SCORE_THRESHOLDS, start=1):
            if safe_score < threshold:
                break
            level = idx
        return min(ScoreSettings.MAX_LEVEL, level)

    def background_speed(self, score):
        """Return cosmetic background speed decoupled from gameplay level pacing."""
        steps = max(0, int(score)) // ScoreSettings.BACKGROUND_SPEED_SCORE_STEP
        return min(
            ScreenSettings.BG_SCROLL_MAX,
            ScreenSettings.DEFAULT_BG_SCROLL_SPEED + (steps * ScreenSettings.BG_SCROLL_STEP),
        )

    def sync_background_speed(self, backgrounds, score):
        """Apply the current difficulty's background speed to every background sprite."""
        new_speed = self.background_speed(score)
        for background in backgrounds:
            background.scroll_speed = new_speed
        return new_speed
