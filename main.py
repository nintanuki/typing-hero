"""Typing Hero entry point.

Stage 1 scaffold: opens the pygame window, runs the event loop, and
renders a single static red alien at center-screen with the word
"hello" floating above it. No keyboard input handling, no falling
motion, no destruction — those land in later stages. The game still
exits cleanly on QUIT or ESC, just as in Stage 0.
"""

import sys

import pygame

from core.sprites import Alien
from settings import FontSettings, ScreenSettings, WordSettings


def run() -> None:
    """Initialize pygame and run the main loop until the user quits."""
    pygame.init()
    screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
    pygame.display.set_caption(ScreenSettings.TITLE)
    clock = pygame.time.Clock()

    # Stage 1 staging: a single red alien parked at center-screen with
    # a hardcoded word. The word list, spawn director, and per-alien
    # color randomization arrive in Stage 4 — for now we just need
    # something on screen to look at.
    aliens = pygame.sprite.Group()
    aliens.add(Alien(color='red', pos=ScreenSettings.CENTER, word='hello'))

    # Font is loaded once and passed into each alien's draw_word so
    # we never call pygame.font.Font(...) inside the per-frame loop.
    word_font = pygame.font.Font(FontSettings.FONT, WordSettings.SIZE)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(ScreenSettings.BG_COLOR)
        aliens.draw(screen)
        for alien in aliens:
            alien.draw_word(screen, word_font)
        pygame.display.flip()
        clock.tick(ScreenSettings.FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
    sys.exit(0)
