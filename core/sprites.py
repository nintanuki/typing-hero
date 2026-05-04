"""Sprite classes for Typing Hero.

Stage 1 introduces a single class: ``Alien``. The Stage 1 scope is
deliberately tiny — load a sprite, expose a ``word`` attribute, and draw
that word above the sprite when asked. Movement, animation cycling,
removal-on-completion, and per-color point values arrive in later
stages as the gameplay loop fills in. Other sprites (lasers, the
player ship, explosions) will land in their own stages and may live in
this file or be split out later.
"""

import os

import pygame

from core.animations import Explosion
from settings import AlienSettings, AssetPaths, ColorSettings, ScreenSettings, WordSettings


class Alien(pygame.sprite.Sprite):
    """A static enemy that carries a word the player must type to destroy it.

    The Alien is the smallest possible enemy at Stage 1: it loads one
    frame of its color sprite, sits at the position passed in, holds a
    ``word`` attribute, and knows how to render that word above itself.
    Per-frame animation, downward motion, and removal-on-completion are
    intentionally absent here — they will be added in later stages so
    earlier scaffolding stays trivial to read.
    """

    def __init__(self, color, pos, word):
        """Create an alien at ``pos`` displaying ``word``.

        Args:
            color (str): Sprite color, one of 'red', 'green', 'yellow',
                'blue'. Selects which ``<color>1.png`` is loaded from
                ``assets/graphics/``.
            pos (tuple[int, int]): Center (x, y) position for the sprite
                on the screen.
            word (str): The word rendered above the sprite for the
                player to type.
        """
        super().__init__()
        self.color = color
        self.word = word

        # Load only the first animation frame for now. Frame cycling
        # (e.g. red1.png ↔ red2.png) is a Stage 8 polish concern and is
        # left out so Stage 1 stays a one-image sprite.
        sprite_path = os.path.join(AssetPaths.GRAPHICS_DIR, f'{color}1.png')
        self.image = pygame.image.load(sprite_path).convert_alpha()
        self.rect = self.image.get_rect(center=pos)

        # Stage 5: store position as a Vector2 (not just rect.x/y)
        # because ``AlienSettings.SPEED`` is sub-pixel — adding 0.5 to
        # an int rect every frame would alternate between "move 0" and
        # "move 1" depending on rounding direction, which reads as
        # stutter. Float position accumulates honestly; rect is a
        # rounded mirror updated in ``update``. Mirrors the legacy
        # ``apply_movement`` pattern in ``legacy/core/sprites.py``.
        self.position = pygame.math.Vector2(self.rect.topleft)
        self.is_dying = False

    def update(self):
        """Advance one frame of motion.

        Vertical-only descent at the per-color
        ``AlienSettings.SPEED[self.color]`` px per frame. The legacy
        ``Alien.calculate_movement`` branched on color for zigzag
        (yellow / blue) and stalled mid-descent for the blue confusion
        attack; Typing Hero cuts the confusion stall (§2) and defers
        the yellow zigzag to Stage 8 polish (§2 update / §10) — Stage
        7's yellow falls straight down, just faster than green so the
        per-color difficulty contract still reads correctly.

        Off-screen detection is intentionally *not* done in this
        method — the main loop owns the miss callback so it can also
        clear the typing lock if the targeted alien is the one that
        just fell. Putting the kill here would force ``Alien`` to know
        about ``WordManager``, which the package layout deliberately
        avoids.

        Returns:
            None. Mutates ``self.position`` and ``self.rect``.
        """
        # if not self.is_dying: # removed this check so aliens don't stop moving when targeted by a laser
        self.position.y += AlienSettings.SPEED[self.color]
        # ``round`` (vs ``int``) keeps the rect honest at the half-
        # pixel boundary — at SPEED=0.5 the alien drops 1 px every two
        # frames rather than oscillating between flooring and ceiling.
        # The same logic applies for the other colors at their floats.
        self.rect.y = round(self.position.y)

        

    def draw_word(self, surface, font, prefix_length=0):
        """Render ``self.word`` horizontally centered above the sprite.

        The word's baseline sits ``WordSettings.OFFSET_ABOVE_SPRITE``
        pixels above the alien's top edge so the text stays clear of
        the sprite art at any sprite scale. The word is uppercased on
        render to honor the project-wide capitalization rule (see
        ``docs/TODO.md`` Q7) — storing ``self.word`` in any case is
        fine; what reaches the screen is always all caps.

        Stage 3 introduces two-color rendering: when ``prefix_length``
        is greater than zero, the first ``prefix_length`` letters are
        rasterized in ``WordSettings.PREFIX_COLOR`` (the typed portion)
        and the remainder in ``WordSettings.COLOR`` (the untyped
        suffix). The two surfaces are blitted side by side so the
        boundary between typed and untyped is exactly where the
        player's progress sits. ``prefix_length=0`` falls through to a
        single-color render — Stage 1/2 callers don't need to change.

        Args:
            surface (pygame.Surface): Destination surface, typically the
                main game screen.
            font (pygame.font.Font): Pre-loaded font used to rasterize
                the word. Caller owns the font so it can be reused
                across many aliens without re-loading per frame.
            prefix_length (int): Number of leading letters of
                ``self.word`` that have already been typed. Defaults to
                0 (whole word renders in ``WordSettings.COLOR``).
                Clamped at the word's length so callers don't have to
                guard against off-by-one when the player just completed
                the word.
        """
        full = self.word.upper()
        # Clamp defensively — a caller could pass len(word) on the same
        # frame they kill the alien; rather than raise, we render the
        # whole word as "typed" and let the kill happen on the next
        # frame. Negative values fall back to "no prefix" semantics.
        prefix_length = max(0, min(prefix_length, len(full)))

        if prefix_length == 0:
            word_surf = font.render(full, True, WordSettings.COLOR)
            word_rect = word_surf.get_rect(
                midbottom=(self.rect.centerx, self.rect.top - WordSettings.OFFSET_ABOVE_SPRITE)
            )
            surface.blit(word_surf, word_rect)
            return

        # Two-color path: render the typed prefix and the untyped suffix
        # on separate surfaces, then position them so the combined width
        # is centered above the sprite. Centering the *combined* width
        # (rather than each piece independently) keeps the word visually
        # locked to the alien's centerline as letters get typed.
        prefix_surf = font.render(
            full[:prefix_length], True, WordSettings.PREFIX_COLOR
        )
        suffix_surf = font.render(
            full[prefix_length:], True, WordSettings.COLOR
        )
        total_width = prefix_surf.get_width() + suffix_surf.get_width()
        # Both surfaces share the same baseline (same font, same render
        # mode), so we can align tops and let the font's internal metrics
        # handle vertical placement. ``midbottom`` style positioning is
        # done on the combined rect so the word sits at the same y as
        # the single-color path.
        baseline_y = self.rect.top - WordSettings.OFFSET_ABOVE_SPRITE
        left_x = self.rect.centerx - total_width // 2
        prefix_rect = prefix_surf.get_rect(bottomleft=(left_x, baseline_y))
        suffix_rect = suffix_surf.get_rect(
            bottomleft=(left_x + prefix_surf.get_width(), baseline_y)
        )
        surface.blit(prefix_surf, prefix_rect)
        surface.blit(suffix_surf, suffix_rect)

class KillLaser(pygame.sprite.Sprite):
    """A vertical beam that shoots up from the bottom of the screen to destroy an alien."""
    def __init__(self, target_alien, explosion_group, audio):
        """
        Create a laser aimed at the given alien.
        Args:
            target_alien (Alien): The alien this laser is targeting. The
                laser will destroy itself when it collides with the
                alien or passes its center y.
            audio: Audio object to play sound effects.
        """
        super().__init__()
        # Create a simple vertical beam.
        self.image = pygame.Surface((4, 20)) 
        self.image.fill(ColorSettings.COLORS['WHITE'])
        
        # Start at the bottom, locked to the target's X to align with the alien
        self.rect = self.image.get_rect(midbottom=(target_alien.rect.centerx, ScreenSettings.HEIGHT))
        
        self.target = target_alien
        self.explosion_group = explosion_group
        self.speed = -8
        self.audio = audio

    def update(self):
        """Move the laser up and check for collision with the target alien."""
        self.rect.y += self.speed
        # Check for contact:
        # We check BOTH a collision and if the laser has passed the alien's center.
        # This prevents the laser from "teleporting" past the alien at high speeds.
        if self.rect.colliderect(self.target.rect) or self.rect.top <= self.target.rect.centery:
            # CREATE: We create the actual instance right here.
            impact_explosion = Explosion(self.target.rect.centerx, self.target.rect.centery)
            self.explosion_group.add(impact_explosion)
            # Play explosion sound
            if self.audio:
                self.audio.play('explosion')
            self.target.kill() # Remove the alien
            self.kill()        # Remove the laser
        # Safety cleanup if it misses
        elif self.rect.bottom < 0:
            self.kill()