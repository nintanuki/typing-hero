"""Alien spawning driver.

Stage 4 introduces ``SpawnDirector`` — a minimal port of the legacy
Star Hero class of the same name (``legacy/systems/managers.py``). The
legacy version also handled alien-fired lasers, drop-table rolls, and
score-driven difficulty scaling; Typing Hero keeps only the part that
matters here: own one ``pygame`` custom event, fire it on a timer, and
push a fresh alien onto the screen each tick.

Difficulty scaling (shrinking the spawn interval as the score climbs)
is a Stage 7 concern. Movement (so the spawn origin can move above the
top of the screen and aliens fall *into* view) is Stage 5. Until those
land, the director's job is exactly: pick a color, pick a word, pick an
x, hand the alien to the sprite group.
"""

import random

import pygame

from core.sprites import Alien
from settings import ScreenSettings, SpawnSettings


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
