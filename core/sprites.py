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

from settings import AssetPaths, WordSettings


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
