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
from systems.audio import Audio
from systems.score_manager import ScoreManager
from systems.spawn_director import SpawnDirector
from systems.word_manager import WordManager
from ui.crt import CRT
from ui.hud import GameOverScreen, HeartsHUD, IntroScreen, PauseScreen, ScoreHUD


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

    audio = Audio()

    hearts_hud = HeartsHUD()
    score_hud = ScoreHUD()
    game_over_screen = GameOverScreen()
    intro_screen = IntroScreen()
    pause_screen = PauseScreen()

    scores = ScoreManager()

    hearts = HeartSettings.MAX

    # state: 'intro' | 'playing' | 'paused' | 'game_over'
    state = 'intro'
    audio.play_intro_music()

    running = True
    while running:
        dt = clock.get_time() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

                elif state == 'intro':
                    if event.key == pygame.K_RETURN:
                        _start_game(
                            aliens, word_manager, spawn_director, audio, bg_group
                        )
                        hearts = HeartSettings.MAX
                        state = 'playing'

                elif state == 'playing':
                    if event.key == pygame.K_SPACE:
                        if word_manager.current_prefix:
                            # Mid-word: try to fire.
                            killed = word_manager.handle_enter()
                            if killed is not None:
                                scores.add_for_color(killed.color)
                                spawn_director.adjust_difficulty(scores.score)
                                spawn_director.sync_background_speed(bg_group, scores.score)
                                audio.play('laser')
                                lasers.add(KillLaser(killed, explosions, audio))
                                killed.is_dying = True
                    elif event.key == pygame.K_RETURN:
                        # Enter toggles pause.
                        audio.play('pause')
                        audio.pause_music()
                        state = 'paused'
                    elif event.key == pygame.K_BACKSPACE:
                        word_manager.handle_backspace()
                    elif event.unicode.isalpha():
                        if word_manager.prefix_length < TypingSettings.MAX_LENGTH:
                            word_manager.handle_letter(event.unicode, aliens)

                elif state == 'paused':
                    if event.key == pygame.K_RETURN:
                        audio.play('unpause')
                        audio.unpause_music()
                        state = 'playing'

                elif state == 'game_over':
                    if scores.entering_initials:
                        if event.key == pygame.K_UP:
                            scores.cycle_char(1)
                        elif event.key == pygame.K_DOWN:
                            scores.cycle_char(-1)
                        elif event.key == pygame.K_LEFT:
                            scores.move_cursor(-1)
                        elif event.key == pygame.K_RIGHT:
                            scores.move_cursor(1)
                        elif event.key == pygame.K_RETURN:
                            scores.submit_initials()
                    else:
                        if event.key == pygame.K_RETURN:
                            _restart_game(
                                aliens, lasers, explosions,
                                word_manager, spawn_director, scores, audio, bg_group
                            )
                            hearts = HeartSettings.MAX
                            state = 'playing'

            elif event.type == spawn_director.spawn_event:
                if state == 'playing':
                    spawn_director.spawn(aliens, word_manager)

        # --- Update ---
        current_level = spawn_director.level(scores.score)

        if state in ('intro', 'playing', 'game_over'):
            bg_group.update(dt)

        if state == 'playing':
            audio.ensure_bgm_playing()
            aliens.update()
            lasers.update()
            explosions.update()

            for alien in list(aliens):
                if alien.rect.top > ScreenSettings.HEIGHT:
                    if alien is word_manager.targeted_alien:
                        word_manager.clear_lock()
                    alien.kill()
                    hearts -= 1
                    if hearts == 2:
                        audio.play('alarm_med')
                    elif hearts == 1:
                        audio.play('alarm_low')
                    if hearts <= 0:
                        hearts = 0
                        word_manager.clear_lock()
                        scores.finalize_game_over()
                        audio.stop_alarms()
                        audio.play_game_over_music()
                        state = 'game_over'
                        break

        # --- Draw ---
        screen.fill(ScreenSettings.BG_COLOR)
        bg_group.draw(screen)

        if state == 'intro':
            intro_screen.draw(screen, scores)

        elif state in ('playing', 'paused'):
            aliens.draw(screen)
            lasers.draw(screen)
            explosions.draw(screen)
            for alien in aliens:
                if alien is word_manager.targeted_alien:
                    alien.draw_word(screen, word_font, word_manager.prefix_length)
                else:
                    alien.draw_word(screen, word_font)

            if state == 'playing':
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
                score_hud.draw(screen, scores.score, scores.high_score, current_level)

            elif state == 'paused':
                hearts_hud.draw(screen, hearts)
                score_hud.draw(screen, scores.score, scores.high_score, current_level)
                pause_screen.draw(screen)

        elif state == 'game_over':
            game_over_screen.draw(screen, scores.score, scores)

        crt.draw()
        pygame.display.flip()
        clock.tick(ScreenSettings.FPS)

    pygame.quit()


def _start_game(aliens, word_manager, spawn_director, audio, bg_group):
    """Transition from intro to playing: stop intro music, start BGM, first spawn."""
    audio.stop_intro_music()
    audio.stop_bgm()
    audio.stop_alarms()
    audio.ensure_bgm_playing()
    spawn_director.adjust_difficulty(0)
    spawn_director.sync_background_speed(bg_group, 0)
    spawn_director.spawn(aliens, word_manager)


def _restart_game(aliens, lasers, explosions, word_manager, spawn_director, scores, audio, bg_group):
    """Reset all per-run state and begin a new run."""
    for alien in list(aliens):
        alien.kill()
    lasers.empty()
    explosions.empty()
    word_manager.clear_lock()
    scores.reset()
    audio.stop_alarms()
    audio.stop_bgm()
    spawn_director.adjust_difficulty(0)
    spawn_director.sync_background_speed(bg_group, 0)
    spawn_director.spawn(aliens, word_manager)
    audio.ensure_bgm_playing()


if __name__ == "__main__":
    run()
    sys.exit(0)

