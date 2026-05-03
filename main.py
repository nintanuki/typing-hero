"""Typing Hero entry point.

Stage 0 scaffold: opens a single pygame window, runs the event loop, fills
the screen with the background color each frame, and exits cleanly on
window-close or ESC. Game systems (sprites, typing, audio, HUD) come online
in later stages.
"""

import sys

import pygame

from settings import ScreenSettings


def run() -> None:
    """Initialize pygame and run the main loop until the user quits."""
    pygame.init()
    screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
    pygame.display.set_caption(ScreenSettings.TITLE)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(ScreenSettings.BG_COLOR)
        pygame.display.flip()
        clock.tick(ScreenSettings.FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
    sys.exit(0)
