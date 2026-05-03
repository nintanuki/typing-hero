"""Typing Hero entry point.

Stage 3 scaffold: the screen now hosts three static aliens at fixed
positions in the upper third (red HELLO at left, green WORLD at center,
yellow TYPE at right), each carrying its own word. A ``WordManager``
owns the typing state — pressing the first letter of any word locks
onto the matching alien (the typed prefix renders in cyan, the untyped
suffix in white), further letters extend the lock only when they keep
matching the locked word, wrong letters mid-word are ignored, Enter
destroys the alien if the prefix matches its word, and Backspace
shrinks the prefix (releasing the lock when the prefix empties). Falling
motion, miss counting, the laser visual, audio, and the real word list
all land in later stages.

ESC and the OS close button still quit the window cleanly. All text
that reaches the screen is rendered uppercase per the project-wide
capitalization rule (see ``docs/TODO.md`` Q7).
"""

import sys

import pygame

from core.sprites import Alien
from settings import (
    FontSettings,
    ScreenSettings,
    Stage3Layout,
    TypingSettings,
    WordSettings,
)
from systems.word_manager import WordManager


def run() -> None:
    """Initialize pygame and run the main loop until the user quits."""
    pygame.init()
    screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
    pygame.display.set_caption(ScreenSettings.TITLE)
    clock = pygame.time.Clock()

    # Stage 3 staging: three aliens at fixed positions with deliberately
    # different first letters (H, W, T) so prefix-locking is testable.
    # Real spawning from a word list arrives in Stage 4 — until then,
    # the (color, word, x) tuples come from settings.Stage3Layout so the
    # demo positions are tunable in one place rather than buried here.
    aliens = pygame.sprite.Group()
    for color, word, x in Stage3Layout.ALIENS:
        aliens.add(Alien(color=color, pos=(x, Stage3Layout.ROW_Y), word=word))

    # Fonts are loaded once and passed into render paths so we never
    # call pygame.font.Font(...) inside the per-frame loop. The word
    # font sizes alien labels; the typing font sizes the bottom-of-
    # screen input buffer (slightly larger so it reads as a HUD piece).
    word_font = pygame.font.Font(FontSettings.FONT, WordSettings.SIZE)
    typing_font = pygame.font.Font(FontSettings.FONT, TypingSettings.SIZE)

    # Stage 3: typing state moves into a WordManager that owns the
    # locked target + the active prefix and decides whether each
    # keystroke advances. main.py just routes events to it and reads
    # back its state when rendering. The MAX_LENGTH guard from Stage 2
    # is still enforced here at the call site — the manager itself
    # doesn't care about buffer length, but the keyboard-repeat /
    # paste defense lives at the input boundary.
    word_manager = WordManager()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN:
                    # Enter commits the buffer. The manager returns the
                    # alien to remove if the prefix matched its word,
                    # otherwise None — and clears its own state in
                    # either case (mirroring Stage 2's "Enter always
                    # resets the buffer" feel).
                    killed = word_manager.handle_enter()
                    if killed is not None:
                        killed.kill()
                        print("kill")
                elif event.key == pygame.K_BACKSPACE:
                    word_manager.handle_backspace()
                elif event.unicode.isalpha():
                    # Only accept letters in v1 — no punctuation, no
                    # digits (Q7 in docs/TODO.md). The MAX_LENGTH guard
                    # protects against keyboard repeat / paste growing
                    # the rendered buffer surface unbounded; the
                    # manager itself is silent on length so the cap
                    # lives here at the input boundary.
                    if word_manager.prefix_length < TypingSettings.MAX_LENGTH:
                        word_manager.handle_letter(event.unicode, aliens)

        screen.fill(ScreenSettings.BG_COLOR)
        aliens.draw(screen)
        for alien in aliens:
            # Only the targeted alien gets a non-zero prefix_length;
            # every other alien renders its whole word in
            # WordSettings.COLOR via the default-argument fast path in
            # draw_word. Comparing by identity (``is``) rather than
            # equality so two aliens that happen to share a word
            # wouldn't both light up.
            if alien is word_manager.targeted_alien:
                alien.draw_word(screen, word_font, word_manager.prefix_length)
            else:
                alien.draw_word(screen, word_font)

        # Render the typing buffer at the bottom-center of the screen.
        # Already uppercase coming out of the manager; if the buffer is
        # empty we skip the blit so we don't waste a render on an
        # empty surface.
        if word_manager.current_prefix:
            buffer_surf = typing_font.render(
                word_manager.current_prefix, True, TypingSettings.COLOR
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
