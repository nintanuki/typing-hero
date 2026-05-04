"""Alien spawning driver."""

import random

import pygame

from core.sprites import Alien
from settings import ScoreSettings, ScreenSettings, SpawnSettings


class SpawnDirector:
    """Owns the alien-spawn timer and creates new ``Alien`` sprites on tick."""

    def __init__(self):
        self.spawn_event = pygame.event.custom_type()
        pygame.time.set_timer(self.spawn_event, SpawnSettings.SPAWN_RATE)

    def spawn(self, aliens, word_manager):
        """Add one new alien to ``aliens`` with a unique word.

        Skips the tick if every word in the pool is already on screen.
        """
        in_use = {alien.word for alien in aliens}
        word = word_manager.pick_word(in_use)
        if word is None:
            return

        color = random.choice(SpawnSettings.COLORS)
        x = random.randint(
            SpawnSettings.X_MARGIN,
            ScreenSettings.WIDTH - SpawnSettings.X_MARGIN,
        )
        aliens.add(Alien(color=color, pos=(x, SpawnSettings.SPAWN_Y), word=word))

    def adjust_difficulty(self, score):
        """Re-arm the spawn timer based on current score.

        Every full ``DIFFICULTY_STEP`` points, the interval shrinks by
        ``SPAWN_RATE_DROP`` ms, clamped at ``MIN_SPAWN_RATE``.

        Returns the new interval in ms.
        """
        steps = self.level(score) - 1
        new_rate = max(
            ScoreSettings.MIN_SPAWN_RATE,
            SpawnSettings.SPAWN_RATE - (steps * ScoreSettings.SPAWN_RATE_DROP),
        )
        pygame.time.set_timer(self.spawn_event, new_rate)
        return new_rate

    def level(self, score):
        """Return the current level derived from score, capped at ``MAX_LEVEL``."""
        base_level = (max(0, score) // ScoreSettings.DIFFICULTY_STEP) + 1
        return min(ScoreSettings.MAX_LEVEL, base_level)

    def background_speed(self, score):
        """Return the background scroll speed for the current score tier."""
        steps = self.level(score) - 1
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
