"""Typing Hero — main entry point."""

import sys

import pygame

from core.animations import Background
from core.sprites import KillLaser
from settings import (
    FontSettings,
    HeartSettings,
    ScreenSettings,
    TypingSettings,
    WordSettings,
)
from systems.score_manager import ScoreManager
from systems.spawn_director import SpawnDirector
from systems.word_manager import WordManager
from systems.audio import Audio
from ui.hud import GameOverScreen, HeartsHUD, ScoreHUD
from ui.crt import CRT


def run() -> None:
    """Initialize pygame and run the main loop until the user quits."""
    pygame.init()
    screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
    crt = CRT(screen)
    pygame.display.set_caption(ScreenSettings.TITLE)
    clock = pygame.time.Clock()

    bg_group = pygame.sprite.GroupSingle()
    background = Background(bg_group)
    
    aliens = pygame.sprite.Group()
    lasers = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    word_font = pygame.font.Font(FontSettings.FONT, WordSettings.SIZE)
    typing_font = pygame.font.Font(FontSettings.FONT, TypingSettings.SIZE)

    word_manager = WordManager(WordSettings.WORDLIST_PATH)
    spawn_director = SpawnDirector()
    # Spawn immediately so the screen isn't blank until the first timer tick.
    spawn_director.spawn(aliens, word_manager)

    audio = Audio()

    hearts_hud = HeartsHUD()
    score_hud = ScoreHUD()
    game_over_screen = GameOverScreen()

    scores = ScoreManager()

    hearts = HeartSettings.MAX
    game_active = True

    audio.ensure_bgm_playing()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == spawn_director.spawn_event:
                if game_active:
                    spawn_director.spawn(aliens, word_manager)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif game_active:
                    if event.key == pygame.K_RETURN:
                        killed = word_manager.handle_enter()
                        if killed is not None:
                            scores.add_for_color(killed.color)
                            spawn_director.adjust_difficulty(scores.score)
                            audio.play('laser')
                            new_laser = KillLaser(killed, explosions, audio)
                            lasers.add(new_laser)
                            killed.is_dying = True
                    elif event.key == pygame.K_BACKSPACE:
                        word_manager.handle_backspace()
                    elif event.unicode.isalpha():
                        if word_manager.prefix_length < TypingSettings.MAX_LENGTH:
                            word_manager.handle_letter(event.unicode, aliens)
                else:
                    # Game-over: only Enter does anything. Restart clears aliens,
                    # resets state, and spawns the first alien of the new run.
                    if event.key == pygame.K_RETURN:
                        for alien in list(aliens):
                            alien.kill()
                        word_manager.clear_lock()
                        hearts = HeartSettings.MAX
                        scores.reset()
                        spawn_director.adjust_difficulty(scores.score)
                        spawn_director.spawn(aliens, word_manager)
                        audio.ensure_bgm_playing()
                        game_active = True

        if game_active:
            dt = clock.get_time() / 1000.0

            bg_group.update(dt, 1.0)
            aliens.update()
            lasers.update()
            explosions.update()

            for alien in list(aliens):
                if alien.rect.top > ScreenSettings.HEIGHT:
                    if alien is word_manager.targeted_alien:
                        word_manager.clear_lock()
                    alien.kill()
                    hearts -= 1
                    if hearts <= 0:
                        word_manager.clear_lock()
                        scores.persist()
                        audio.stop_bgm()
                        game_active = False
                        break

        screen.fill(ScreenSettings.BG_COLOR)
        bg_group.draw(screen)
        aliens.draw(screen)
        lasers.draw(screen)
        explosions.draw(screen)
        for alien in aliens:
            if alien is word_manager.targeted_alien:
                alien.draw_word(screen, word_font, word_manager.prefix_length)
            else:
                alien.draw_word(screen, word_font)

        if game_active:
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
            hearts_hud.draw(screen, hearts)
            score_hud.draw(screen, scores.score, scores.high_score)
        else:
            score_hud.draw(screen, scores.score, scores.high_score)
            game_over_screen.draw(screen)

        crt.draw()
        pygame.display.flip()
        clock.tick(ScreenSettings.FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
    sys.exit(0)
