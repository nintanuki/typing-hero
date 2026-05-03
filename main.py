"""Typing Hero entry point.

Stage 2 scaffold: opens the pygame window, runs the event loop, and
renders a single static red alien at center-screen with the word
"hello" floating above it. The player builds up a typing buffer with
letter keys, sees it rendered at the bottom of the screen, and on
``Enter`` the buffer is compared (case-insensitively) against the
alien's word — a match destroys the alien and prints "kill" to the
console; a mismatch just clears the buffer. Falling motion, miss
counting, the laser visual, and audio all land in later stages.

ESC and the OS close button still quit the window cleanly. All text
that reaches the screen is rendered uppercase per the project-wide
capitalization rule (see ``docs/TODO.md`` Q7).
"""

import sys

import pygame

from core.sprites import Alien
from settings import FontSettings, ScreenSettings, TypingSettings, WordSettings


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

    # Fonts are loaded once and passed into render paths so we never
    # call pygame.font.Font(...) inside the per-frame loop. The word
    # font sizes alien labels; the typing font sizes the bottom-of-
    # screen input buffer (slightly larger so it reads as a HUD piece).
    word_font = pygame.font.Font(FontSettings.FONT, WordSettings.SIZE)
    typing_font = pygame.font.Font(FontSettings.FONT, TypingSettings.SIZE)

    # Stage 2: the typing buffer accumulates characters from KEYDOWN
    # events. Stored verbatim (we render uppercase at draw time) and
    # cleared on Enter regardless of whether the submission matched a
    # word. Backspace removes the most recent character — small QoL
    # call mentioned in TESTING.md Stage 2.
    current_input = ""

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN:
                    # Enter submits the buffer. Stage 2 has only one
                    # alien on screen, so the only matching candidate
                    # is whichever alien (if any) carries the typed
                    # word. Multi-alien prefix-locking arrives in
                    # Stage 3 — until then this loop is effectively a
                    # one-element scan. Comparison is case-insensitive
                    # because in-game text is always uppercase but the
                    # underlying word can be stored in any case.
                    submission = current_input.upper()
                    for alien in list(aliens):
                        if submission == alien.word.upper():
                            alien.kill()
                            print("kill")
                            break
                    current_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    current_input = current_input[:-1]
                elif event.unicode.isalpha():
                    # Only accept letters into the buffer in v1 — no
                    # punctuation, no digits (Q7 in docs/TODO.md).
                    # MAX_LENGTH guards against keyboard repeat /
                    # accidental paste growing the buffer unbounded.
                    if len(current_input) < TypingSettings.MAX_LENGTH:
                        current_input += event.unicode

        screen.fill(ScreenSettings.BG_COLOR)
        aliens.draw(screen)
        for alien in aliens:
            alien.draw_word(screen, word_font)

        # Render the typing buffer at the bottom-center of the screen.
        # Always uppercase per the project-wide capitalization rule;
        # if the buffer is empty we skip the blit so we don't waste a
        # render on an empty surface.
        if current_input:
            buffer_surf = typing_font.render(
                current_input.upper(), True, TypingSettings.COLOR
            )
            buffer_rect = buffer_surf.get_rect(
                midbottom=(
                    ScreenSettings.WIDTH / 2,
                    ScreenSettings.HEIGHT - TypingSettings.OFFSET_FROM_BOTTOM,
                )
            )
            screen.blit(buffer_surf, buffer_rect)

        pygame.display.flip()
        clock.tick(ScreenSettings.FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
    sys.exit(0)
