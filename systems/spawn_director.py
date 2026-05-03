"""Alien spawning driver.

Stage 4 introduced ``SpawnDirector`` — a minimal port of the legacy
Star Hero class of the same name (``legacy/systems/managers.py``). The
legacy version also handled alien-fired lasers and drop-table rolls;
Typing Hero stays cut on those (§2). Stage 7 adds the third leg of the
legacy class — score-driven difficulty scaling via
``adjust_difficulty`` — so the spawn interval visibly tightens as the
player's score climbs.

Movement (the per-frame fall) lives on ``Alien.update``; the director
only knows about *when* aliens appear, not what they do once on screen.
"""

import random

import pygame

from core.sprites import Alien
from settings import ScoreSettings, ScreenSettings, SpawnSettings


class SpawnDirector:
    """Owns the alien-spawn timer and creates new ``Alien`` sprites on tick.

    The director is told nothing about the broader game state — the
    caller passes the sprite group and the ``WordManager`` into
    ``spawn`` each tick. That keeps it honest with the
    "communicate through GameManager" rule in ``docs/TESTING.md`` once
    a real GameManager arrives in Stage 9, and makes the director
    trivial to construct in unit tests (no game context needed).
    """

    def __init__(self):
        """Allocate one custom pygame event and start its timer.

        ``pygame.event.custom_type`` reserves a fresh event id the OS
        won't collide with; ``pygame.time.set_timer`` then has pygame
        post that event onto the queue every ``SpawnSettings.SPAWN_RATE``
        milliseconds. The main loop sees it as just another event type
        and routes it back here through ``spawn``.
        """
        self.spawn_event = pygame.event.custom_type()
        pygame.time.set_timer(self.spawn_event, SpawnSettings.SPAWN_RATE)

    def spawn(self, aliens, word_manager):
        """Add one new alien to ``aliens`` with a unique word.

        The word is pulled from ``word_manager.pick_word`` with the set
        of words already on screen excluded — duplicate words would
        make prefix-locking ambiguous (typing a shared starting prefix
        would resolve only one of them, which reads as a bug). The
        color and x are uniformly random; the y is fixed at
        ``SpawnSettings.SPAWN_Y`` since aliens don't move yet.

        Args:
            aliens (pygame.sprite.Group): Live alien group; the new
                sprite is added here. Iterated to compute the in-use
                word set, so order doesn't matter.
            word_manager (WordManager): Source of the next word.
                ``pick_word`` may return ``None`` if every loaded word
                is already on screen — in that case we skip this tick
                rather than spawn a duplicate.
        """
        # Build the in-use set at the call site so WordManager doesn't
        # have to know about pygame sprite groups. Set comprehension
        # is O(n) over current aliens and pick_word does its own O(n)
        # filter on the pool — both negligible at typing-game scales
        # (a few aliens, ~75 words).
        in_use = {alien.word for alien in aliens}
        word = word_manager.pick_word(in_use)
        if word is None:
            # Pool exhausted: every loaded word is currently on screen.
            # Skipping this tick lets the next on-screen completion
            # free up a word naturally, instead of either crashing or
            # spawning a duplicate.
            return

        color = random.choice(SpawnSettings.COLORS)
        # Inclusive range; X_MARGIN keeps the word floating above the
        # alien on-screen even when the sprite spawns near a wall.
        x = random.randint(
            SpawnSettings.X_MARGIN,
            ScreenSettings.WIDTH - SpawnSettings.X_MARGIN,
        )
        aliens.add(Alien(color=color, pos=(x, SpawnSettings.SPAWN_Y), word=word))

    def adjust_difficulty(self, score):
        """Re-arm the spawn timer based on the current score.

        Every full ``ScoreSettings.DIFFICULTY_STEP`` points the player
        has earned, the spawn interval drops by
        ``ScoreSettings.SPAWN_RATE_DROP`` ms, clamped at
        ``ScoreSettings.MIN_SPAWN_RATE`` so the ramp can't run away
        into unplayability. Mirrors the legacy
        ``SpawnDirector.adjust_difficulty`` shape but only the spawn-
        timer leg — alien-fired lasers and the background-scroll
        speedup are forever-cut (§2 / §6 cuts).

        Called from ``main.py`` on every successful kill (score
        changes), not on a timer of its own — that keeps the ramp
        deterministic ("at exactly N points, spawns are M ms apart")
        and avoids the legacy footgun where two timers could fight
        each other on a frame ScoreManager and SpawnDirector
        disagreed about the current score.

        Args:
            score (int): Current run score from
                ``ScoreManager.score``. Negative scores are not
                expected (no penalties at Stage 7) but would clamp to
                step=0 via the floor division anyway.

        Returns:
            int: The new spawn interval in ms — useful for tests /
            debugging. The pygame timer is also re-armed in-place as
            a side effect.
        """
        steps = max(0, score) // ScoreSettings.DIFFICULTY_STEP
        new_rate = max(
            ScoreSettings.MIN_SPAWN_RATE,
            SpawnSettings.SPAWN_RATE - (steps * ScoreSettings.SPAWN_RATE_DROP),
        )
        # ``set_timer`` replaces the existing timer for ``spawn_event``
        # with the new interval; the next post happens ``new_rate`` ms
        # from now, not ``new_rate`` ms from the *previous* tick. That
        # gives a small "jitter" at each step boundary which reads as
        # natural pacing rather than a visible cadence shift.
        pygame.time.set_timer(self.spawn_event, new_rate)
        return new_rate
