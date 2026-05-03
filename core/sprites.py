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

    def draw_word(self, surface, font):
        """Render ``self.word`` horizontally centered above the sprite.

        The word's baseline sits ``WordSettings.OFFSET_ABOVE_SPRITE``
        pixels above the alien's top edge so the text stays clear of
        the sprite art at any sprite scale.

        Args:
            surface (pygame.Surface): Destination surface, typically the
                main game screen.
            font (pygame.font.Font): Pre-loaded font used to rasterize
                the word. Caller owns the font so it can be reused
                across many aliens without re-loading per frame.
        """
        word_surf = font.render(self.word, True, WordSettings.COLOR)
        word_rect = word_surf.get_rect(
            midbottom=(self.rect.centerx, self.rect.top - WordSettings.OFFSET_ABOVE_SPRITE)
        )
        surface.blit(word_surf, word_rect)
