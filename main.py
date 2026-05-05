"""Typing Hero — main entry point."""

import random
import sys

import pygame

from core.animations import Background
from core.sprites import KillLaser, PowerUp
from settings import (
    AlienSettings,
    FontSettings,
    HeartSettings,
    PowerupSettings,
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
    powerups = pygame.sprite.Group()

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
    laser_level = 1

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
                            aliens, word_manager, spawn_director, audio, bg_group, powerups
                        )
                        hearts = HeartSettings.MAX
                        laser_level = 1
                        state = 'playing'

                elif state == 'playing':
                    if event.key == pygame.K_SPACE:
                        _handle_spacebar_playing()
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
                            if (
                                word_manager.targeted_alien is not None
                                and word_manager.current_prefix
                                == word_manager.targeted_alien.word.upper()
                            ):
                                hearts, laser_level = _resolve_shot_outcome(
                                    word_manager,
                                    scores,
                                    spawn_director,
                                    audio,
                                    aliens,
                                    lasers,
                                    explosions,
                                    powerups,
                                    bg_group,
                                    hearts,
                                    laser_level,
                                )

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
                                aliens, lasers, explosions, powerups,
                                word_manager, spawn_director, scores, audio, bg_group
                            )
                            hearts = HeartSettings.MAX
                            laser_level = 1
                            state = 'playing'

            elif event.type == spawn_director.spawn_event:
                if state == 'playing':
                    spawn_director.spawn(aliens, word_manager, scores.score)

        # --- Update ---
        current_level = spawn_director.level(scores.score)

        if state in ('intro', 'playing', 'game_over'):
            bg_group.update(dt)

        if state == 'playing':
            audio.ensure_bgm_playing()
            aliens.update()
            lasers.update()
            explosions.update()
            powerups.update()

            hearts, laser_level = _resolve_powerups_at_bottom(
                powerups, hearts, laser_level, audio
            )

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
            powerups.draw(screen)
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


def _start_game(aliens, word_manager, spawn_director, audio, bg_group, powerups):
    """Transition from intro to playing: stop intro music, start BGM, first spawn."""
    audio.stop_intro_music()
    audio.stop_bgm()
    audio.stop_alarms()
    audio.ensure_bgm_playing()
    powerups.empty()
    spawn_director.adjust_difficulty(0)
    spawn_director.sync_background_speed(bg_group, 0)
    spawn_director.spawn(aliens, word_manager, 0)


def _handle_spacebar_playing():
    """Reserved hook for future in-game spacebar behavior."""
    pass


def _resolve_shot_outcome(
    word_manager,
    scores,
    spawn_director,
    audio,
    aliens,
    lasers,
    explosions,
    powerups,
    bg_group,
    hearts,
    laser_level,
):
    """Resolve one completed word into kills, drops, and shot visuals."""
    targeted_alien = word_manager.handle_enter()
    if targeted_alien is None:
        return hearts, laser_level

    victims = _resolve_shot_targets(targeted_alien, aliens, laser_level)
    if not victims:
        return hearts, laser_level

    for victim in victims:
        if victim.is_dying:
            continue
        scores.add_for_color(victim.color)
        _try_spawn_powerup_drop(victim, powerups, hearts, laser_level)
        victim.is_dying = True
        lasers.add(KillLaser(victim, explosions, audio))

    spawn_director.adjust_difficulty(scores.score)
    spawn_director.sync_background_speed(bg_group, scores.score)
    if laser_level >= PowerupSettings.MAX_LASER_LEVEL:
        audio.play('hyper')
    else:
        audio.play('laser')
    return hearts, laser_level


def _resolve_shot_targets(targeted_alien, aliens, laser_level):
    """Return aliens hit by the current laser mode for one successful word."""
    if targeted_alien not in aliens:
        return []

    if laser_level <= 1:
        return [targeted_alien]

    if laser_level == 2:
        victims = [targeted_alien]
        beam_offsets = (-18, 18)
        for offset in beam_offsets:
            beam_x = targeted_alien.rect.centerx + offset
            beam_targets = [
                alien
                for alien in aliens
                if alien not in victims and alien.rect.left <= beam_x <= alien.rect.right
            ]
            if not beam_targets:
                continue
            beam_targets.sort(key=lambda alien: alien.rect.centery, reverse=True)
            victims.append(beam_targets[0])
        return victims

    beam_x = targeted_alien.rect.centerx
    victims = [
        alien for alien in aliens
        if alien.rect.left <= beam_x <= alien.rect.right
    ]
    victims.sort(key=lambda alien: alien.rect.centery, reverse=True)
    return victims


def _try_spawn_powerup_drop(alien, powerups, hearts, laser_level):
    """Roll minimal drop table: red hearts and green laser-upgrade tokens."""
    if alien.color == 'red':
        if hearts >= HeartSettings.MAX:
            return
        if random.random() < AlienSettings.DROP_CHANCE['red']:
            powerups.add(PowerUp(alien.rect.center, PowerupSettings.HEART_TYPE))
        return

    if alien.color == 'green':
        if laser_level >= PowerupSettings.MAX_LASER_LEVEL:
            return
        if random.random() < AlienSettings.DROP_CHANCE['green']:
            powerups.add(PowerUp(alien.rect.center, PowerupSettings.LASER_UPGRADE_TYPE))


def _resolve_powerups_at_bottom(powerups, hearts, laser_level, audio):
    """Apply powerup effects once drops reach the bottom edge."""
    for powerup in list(powerups):
        if not powerup.reached_bottom():
            continue

        if powerup.kind == PowerupSettings.HEART_TYPE:
            if hearts < HeartSettings.MAX:
                hearts += 1
                audio.play('powerup_heart')
        elif powerup.kind == PowerupSettings.LASER_UPGRADE_TYPE:
            if laser_level < PowerupSettings.MAX_LASER_LEVEL:
                laser_level += 1
                if laser_level >= PowerupSettings.MAX_LASER_LEVEL:
                    audio.play('hyper')
                else:
                    audio.play('powerup_twin')

        powerup.kill()

    return hearts, laser_level


def _restart_game(
    aliens,
    lasers,
    explosions,
    powerups,
    word_manager,
    spawn_director,
    scores,
    audio,
    bg_group,
):
    """Reset all per-run state and begin a new run."""
    for alien in list(aliens):
        alien.kill()
    lasers.empty()
    explosions.empty()
    powerups.empty()
    word_manager.clear_lock()
    scores.reset()
    audio.stop_alarms()
    audio.stop_bgm()
    spawn_director.adjust_difficulty(0)
    spawn_director.sync_background_speed(bg_group, 0)
    spawn_director.spawn(aliens, word_manager, 0)
    audio.ensure_bgm_playing()


if __name__ == "__main__":
    run()
    sys.exit(0)

