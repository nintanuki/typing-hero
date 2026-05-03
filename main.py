"""Typing Hero entry point.

Stage 5 scaffold: aliens now *fall*. Each frame, ``aliens.update()``
advances every alien down the screen by ``AlienSettings.SPEED``
(sub-pixel accurate via the new ``Alien.position`` Vector2). After
the update pass, the main loop scans for any alien whose top edge
has cleared the bottom of the screen, prints ``miss`` to the console,
clears the typing lock if the missed alien was the active target, and
removes the sprite. Hearts / game-over land in Stage 6 — Stage 5
just establishes the miss signal.

The Stage 4 spawning loop (``SpawnDirector`` + timer + first-frame
spawn) is unchanged; the Stage 3 typing state machine (``WordManager``
with prefix-lock, two-color word render, Enter/Backspace) is also
unchanged. Laser visual + audio + the hearts HUD all land in later
stages.

ESC and the OS close button still quit the window cleanly. All text
that reaches the screen is rendered uppercase per the project-wide
capitalization rule (see ``docs/TODO.md`` Q7).
"""

import sys

import pygame

from settings import (
    FontSettings,
    ScreenSettings,
    TypingSettings,
    WordSettings,
)
from systems.spawn_director import SpawnDirector
from systems.word_manager import WordManager


def run() -> None:
    """Initialize pygame and run the main loop until the user quits."""
    pygame.init()
    screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
    pygame.display.set_caption(ScreenSettings.TITLE)
    clock = pygame.time.Clock()

    # Stage 4: aliens are no longer hand-placed — ``SpawnDirector``
    # creates one each timer tick. The group starts empty; we kick off
    # one immediate spawn after construction so the screen isn't blank
    # for the first SPAWN_RATE ms after boot, and so the Stage 4 smoke
    # test ("aliens appear at the top every couple seconds") sees an
    # alien within the first frame instead of after the first interval.
    aliens = pygame.sprite.Group()

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
    # Stage 4: the same manager also owns the loaded word pool (from
    # ``WordSettings.WORDLIST_PATH``) and serves the next word to the
    # spawner via ``pick_word``.
    word_manager = WordManager(WordSettings.WORDLIST_PATH)
    spawn_director = SpawnDirector()
    # First-frame spawn so the player sees something immediately rather
    # than waiting out the full timer interval at boot.
    spawn_director.spawn(aliens, word_manager)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == spawn_director.spawn_event:
                # Timer tick: one new alien with a fresh word. The
                # director silently no-ops if the word pool is fully
                # in-use, so this branch is safe to hit every tick
                # regardless of how many aliens are already on screen.
                spawn_director.spawn(aliens, word_manager)
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

        # Stage 5: advance every alien one frame of vertical motion
        # before the render pass. Group.update() forwards to each
        # sprite's update(), which mutates rect.y from the float
        # position accumulator on Alien. Done before the off-screen
        # scan so an alien that crosses the bottom this frame is
        # caught (and missed) on the same frame it would have first
        # rendered fully off-screen.
        aliens.update()

        # Stage 5: miss detection. Iterate a snapshot of the group
        # (``list(aliens)``) because alien.kill() mutates the group
        # mid-iteration. ``rect.top > HEIGHT`` is the "fully past the
        # bottom edge" condition from TODO §5 step 2 — we wait until
        # the whole sprite has cleared the screen so a player who
        # finishes typing the word at the very last frame still gets
        # the kill, not a miss. Lock-clear runs before kill() so the
        # WordManager is never left holding a dead reference (it
        # checks identity in handle_letter / draw paths).
        for alien in list(aliens):
            if alien.rect.top > ScreenSettings.HEIGHT:
                if alien is word_manager.targeted_alien:
                    word_manager.clear_lock()
                alien.kill()
                print("miss")

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
