"""Typing Hero entry point.

Stage 6 scaffold: runs now *end*. The player has ``HeartSettings.MAX``
hearts; each missed alien costs one. When the count hits zero, the
loop flips into a game-over state — alien motion, miss-detection, the
spawn timer, and typing input all gate off, the active typing lock
clears, and a centered "GAME OVER — press Enter to restart" overlay
draws on top of the frozen playfield. Pressing Enter from that state
clears the alien group, resets the heart counter, kicks a fresh first-
frame spawn, and the run resumes.

Stage 5's falling motion + miss callback (the ``aliens.update()`` and
``rect.top > HEIGHT`` scan) is preserved verbatim except that the miss
callback now decrements ``hearts`` and ends the run at zero. Stage 4's
``SpawnDirector`` + first-frame spawn is unchanged. Stage 3's
``WordManager`` is unchanged. Hearts render in the top-right via the
new ``HeartsHUD``; the game-over overlay renders via ``GameOverScreen``
— both ported from ``legacy/ui/style.py`` with the boost-meter / status-
row / bombs-row fluff cut out.

ESC and the OS close button still quit the window cleanly. All text
that reaches the screen is rendered uppercase per the project-wide
capitalization rule (see ``docs/TODO.md`` Q7).
"""

import sys

import pygame

from settings import (
    FontSettings,
    HeartSettings,
    ScreenSettings,
    TypingSettings,
    WordSettings,
)
from systems.spawn_director import SpawnDirector
from systems.word_manager import WordManager
from ui.hud import GameOverScreen, HeartsHUD
from ui.crt import CRT


def run() -> None:
    """Initialize pygame and run the main loop until the user quits."""
    pygame.init()
    screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
    crt = CRT(screen)
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

    # Stage 6: HUD + game-over overlay. Both pre-rasterize their assets
    # at construction so the per-frame draw is just blits. ``HeartsHUD``
    # owns the heart sprite and the row geometry; ``GameOverScreen``
    # owns the banner + prompt surfaces and their pre-computed rects.
    hearts_hud = HeartsHUD()
    game_over_screen = GameOverScreen()

    # Stage 6: hearts counter + game_active flag. Hearts decrement on
    # miss; at zero, ``game_active`` flips to False and the run ends.
    # Both pieces of state live here in main.py rather than on a
    # separate manager — Stage 9's ``SessionStateManager`` port will
    # take ownership of ``game_active`` (intro / game_active / pause /
    # game_over) and pull this flag in then.
    hearts = HeartSettings.MAX
    game_active = True

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
                # Stage 6: gated on ``game_active`` so the spawn timer
                # keeps ticking on the game-over screen but no aliens
                # appear behind the banner. The timer itself stays
                # armed — restarting a run picks up the same cadence
                # without re-arming, and the next on-game-over tick is
                # silently dropped here.
                if game_active:
                    spawn_director.spawn(aliens, word_manager)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game_active:
                    if event.key == pygame.K_RETURN:
                        # Enter commits the buffer. The manager returns
                        # the alien to remove if the prefix matched its
                        # word, otherwise None — and clears its own
                        # state in either case (mirroring Stage 2's
                        # "Enter always resets the buffer" feel).
                        killed = word_manager.handle_enter()
                        if killed is not None:
                            killed.kill()
                            print("kill")
                    elif event.key == pygame.K_BACKSPACE:
                        word_manager.handle_backspace()
                    elif event.unicode.isalpha():
                        # Only accept letters in v1 — no punctuation, no
                        # digits (Q7 in docs/TODO.md). The MAX_LENGTH
                        # guard protects against keyboard repeat / paste
                        # growing the rendered buffer surface unbounded;
                        # the manager itself is silent on length so the
                        # cap lives here at the input boundary.
                        if word_manager.prefix_length < TypingSettings.MAX_LENGTH:
                            word_manager.handle_letter(event.unicode, aliens)
                else:
                    # Game-over state: only Enter does anything. Other
                    # keys drop silently so a player still tapping at
                    # the keyboard when they died doesn't accidentally
                    # plant a half-typed prefix that'd carry over into
                    # the next run. Restart order: clear the alien
                    # group (so the playfield reads fresh), clear any
                    # leftover lock (already cleared at game-over but
                    # idempotent), refill hearts, kick the first-frame
                    # spawn so the new run isn't blank for SPAWN_RATE
                    # ms, then flip ``game_active`` back on.
                    if event.key == pygame.K_RETURN:
                        for alien in list(aliens):
                            alien.kill()
                        word_manager.clear_lock()
                        hearts = HeartSettings.MAX
                        spawn_director.spawn(aliens, word_manager)
                        game_active = True

        # Stage 6: motion + miss-detection only run while the game is
        # active. On the game-over screen the previously-on-screen
        # aliens freeze in place (rendered without ``update`` advancing
        # them), which keeps the playfield as a backdrop for the banner
        # without continuing to take damage from below.
        if game_active:
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
            # mid-iteration. ``rect.top > HEIGHT`` is the "fully past
            # the bottom edge" condition from TODO §5 step 2 — we wait
            # until the whole sprite has cleared the screen so a player
            # who finishes typing the word at the very last frame still
            # gets the kill, not a miss. Lock-clear runs before kill()
            # so the WordManager is never left holding a dead reference
            # (it checks identity in handle_letter / draw paths).
            # Stage 6: each miss decrements ``hearts``. At zero the run
            # ends — clear any stale typing state so the game-over
            # screen reads clean, then flip ``game_active``. The
            # ``print("miss")`` placeholder from Stage 5 stays for
            # parity with the smoke test until a Stage 8 SFX hook
            # replaces it.
            for alien in list(aliens):
                if alien.rect.top > ScreenSettings.HEIGHT:
                    if alien is word_manager.targeted_alien:
                        word_manager.clear_lock()
                    alien.kill()
                    hearts -= 1
                    print("miss")
                    if hearts <= 0:
                        # Game over. Clear the lock (idempotent if
                        # already empty) and flip the active flag.
                        # ``break`` so we don't continue logging misses
                        # for any other aliens that crossed the bottom
                        # in the same frame — once the run is over,
                        # additional misses don't matter.
                        word_manager.clear_lock()
                        game_active = False
                        break

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

        if game_active:
            # Render the typing buffer at the bottom-center of the
            # screen. Already uppercase coming out of the manager; if
            # the buffer is empty we skip the blit so we don't waste a
            # render on an empty surface.
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
            # Hearts row sits in the top-right; only drawn during a
            # live run because at zero hearts the row is empty space
            # anyway and the game-over banner is the focus.
            hearts_hud.draw(screen, hearts)
        else:
            # Drawn last so the banner + prompt sit on top of any
            # frozen aliens still on the playfield. The frozen scene
            # behind the banner reads as "this is the run you just
            # finished," which is more informative than a black screen.
            game_over_screen.draw(screen)

        crt.draw()
        pygame.display.flip()
        clock.tick(ScreenSettings.FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
    sys.exit(0)
