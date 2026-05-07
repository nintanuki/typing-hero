"""Typing Hero main entry point and runtime orchestration."""

from __future__ import annotations

import random
import sys
from typing import Literal

import pygame

from core.animations import Background, Explosion
from core.sprites import Alien, KillLaser, PowerUp, RainbowLaser
from settings import (
    AlienSettings,
    DamageSettings,
    FontSettings,
    HeartSettings,
    LaserSettings,
    PowerupSettings,
    ScreenSettings,
    ShieldSettings,
    TypingSettings,
    WordSettings,
)
from systems.audio import Audio
from systems.score_manager import ScoreManager
from systems.spawn_director import SpawnDirector
from systems.word_manager import WordManager
from ui.crt import CRT
from ui.hud import GameOverScreen, HeartsHUD, IntroScreen, PauseScreen, ScoreHUD

class GameManager:
    """Coordinate the Typing Hero runtime loop and high-level game state."""

    # -------------------------
    # BOOT / LIFECYCLE
    # -------------------------

    def __init__(self) -> None:
        """Initialize pygame, runtime services, and per-session state."""
        pygame.init()
        self.screen = pygame.display.set_mode(
            ScreenSettings.RESOLUTION,
            pygame.SCALED,
        )
        pygame.display.set_caption(ScreenSettings.TITLE)
        self.clock = pygame.time.Clock()
        self.crt = CRT(self.screen)

        self.bg_group = pygame.sprite.GroupSingle()
        Background(self.bg_group)

        self.aliens = pygame.sprite.Group()
        self.lasers = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        self.word_font = pygame.font.Font(FontSettings.FONT, WordSettings.SIZE)
        self.typing_font = pygame.font.Font(FontSettings.FONT, TypingSettings.SIZE)

        self.word_manager = WordManager(WordSettings.WORDLIST_PATH)
        self.spawn_director = SpawnDirector()
        self.audio = Audio()
        self.hearts_hud = HeartsHUD()
        self.score_hud = ScoreHUD()
        self.game_over_screen = GameOverScreen()
        self.intro_screen = IntroScreen()
        self.pause_screen = PauseScreen()
        self.scores = ScoreManager()

        self.hearts = HeartSettings.MAX
        self.laser_level = 1
        self.burst_tier = 0
        self._pending_follow_ups: list = []  # (fire_at_ticks, alien_ref)
        self._rainbow_beam_until = 0  # ticks when the active rainbow beam expires
        self.current_level = 1
        self._invincible_until = 0   # ticks when invincibility expires
        self._flash_start = 0        # ticks when the current damage flash began
        self._flash_end = 0          # ticks when the current damage flash expires
        self._shield_until = 0       # ticks when the shield powerup expires
        self.state: Literal['intro', 'playing', 'paused', 'game_over'] = 'intro'
        self.running = True

        self.audio.play_intro_music()

    def close_game(self) -> None:
        """Close pygame and exit the process cleanly."""
        pygame.quit()
        sys.exit()

    # -------------------------
    # GAMEPLAY ACTIONS
    # -------------------------

    def _start_game(self) -> None:
        """Transition from the intro screen into an active run."""
        self.audio.stop_intro_music()
        self._reset_run_state()
        self.state = 'playing'

    def _restart_game(self) -> None:
        """Reset all per-run state and begin a fresh gameplay run."""
        self._reset_run_state()
        self.state = 'playing'

    def _reset_run_state(self) -> None:
        """Reset sprite groups, score state, and difficulty for a new run."""
        self.aliens.empty()
        self.lasers.empty()
        self.explosions.empty()
        self.powerups.empty()
        self.word_manager.clear_lock()
        self.scores.reset()
        self.hearts = HeartSettings.MAX
        self.laser_level = 1
        self.burst_tier = 0
        self._pending_follow_ups = []
        self._rainbow_beam_until = 0
        self.current_level = 1
        self._invincible_until = 0
        self._flash_start = 0
        self._flash_end = 0
        self._shield_until = 0

        self.audio.stop_alarms()
        self.audio.stop_bgm()
        self.spawn_director.adjust_difficulty(0)
        self.spawn_director.sync_background_speed(self.bg_group, 0)
        spawned = self.spawn_director.spawn(self.aliens, self.word_manager, 0)
        if spawned is not None and spawned.color == 'blue':
            self.audio.play('ufo')
        self.audio.ensure_bgm_playing()

    def _handle_spacebar_playing(self) -> None:
        """Reserve spacebar behavior for a future gameplay action."""

    def _resolve_completed_word(self) -> None:
        """Turn a completed word into live laser projectiles and audio feedback."""
        targeted_alien = self.word_manager.handle_enter()
        if targeted_alien is None or targeted_alien not in self.aliens:
            return

        self._spawn_shot_lasers(targeted_alien)
        self._play_shot_sound()

        if self.burst_tier >= 1:
            now = pygame.time.get_ticks()
            delays = (
                PowerupSettings.BURST_TIER2_DELAYS_MS
                if self.burst_tier >= 2
                else (PowerupSettings.BURST_TIER1_DELAY_MS,)
            )
            for delay in delays:
                self._pending_follow_ups.append((now + delay, targeted_alien))

    def _play_shot_sound(self) -> None:
        """Play the shot SFX that matches the current laser tier."""
        if self.laser_level >= PowerupSettings.MAX_LASER_LEVEL:
            self.audio.play('hyper')
            return
        self.audio.play('laser')

    def _spawn_shot_lasers(self, targeted_alien: Alien) -> None:
        """Spawn the current laser loadout aimed at the resolved alien.

        For zig-zagging aliens (yellow, blue) the laser is fired at the alien's
        predicted position rather than its current center, so the shot leads the
        target and connects mid-flight.

        Args:
            targeted_alien: The alien whose completed word triggered the shot.
        """
        # --- Predictive intercept ---
        # The laser travels from y=HEIGHT upward at |LaserSettings.SPEED| px/frame.
        # Time to reach the alien = distance / speed, where distance is how far
        # the laser must climb from the bottom edge to the alien's current y.
        # The alien moves horizontally at zigzag_direction * ZIGZAG_HORIZONTAL_SPEED
        # per frame, so multiplying by travel_frames gives the horizontal offset
        # by the time of impact.
        # For non-zigzag aliens (red, green) zigzag_direction == 0, so aim_x equals
        # the alien's current center with no change in behavior.
        # Yellow can flip direction mid-flight (counter-based), so the intercept is
        # an approximation — it still leads the target rather than firing behind it.
        distance = ScreenSettings.HEIGHT - targeted_alien.rect.centery
        travel_frames = distance / abs(LaserSettings.SPEED)
        aim_x = round(
            targeted_alien.rect.centerx
            + targeted_alien.zigzag_direction
            * AlienSettings.ZIGZAG_HORIZONTAL_SPEED
            * targeted_alien.level_speed_multiplier
            * travel_frames
        )
        # Clamp so the laser can't spawn off-screen.
        aim_x = max(0, min(ScreenSettings.WIDTH, aim_x))

        if self.laser_level <= 1:
            self.lasers.add(
                KillLaser(aim_x, LaserSettings.COLORS['single'])
            )
            return

        twin_colors = (
            LaserSettings.COLORS['piercing']
            if self.laser_level >= PowerupSettings.MAX_LASER_LEVEL
            else LaserSettings.COLORS['twin']
        )
        is_piercing = self.laser_level >= PowerupSettings.MAX_LASER_LEVEL
        for offset in (
            -PowerupSettings.TWIN_BEAM_OFFSET,
            PowerupSettings.TWIN_BEAM_OFFSET,
        ):
            self.lasers.add(
                KillLaser(
                    aim_x + offset,
                    twin_colors,
                    is_piercing=is_piercing,
                )
            )

    def _resolve_laser_collisions(self) -> None:
        """Resolve projectile hits, score gain, drops, and difficulty changes."""
        score_changed = False
        for laser in list(self.lasers):
            hit_aliens = [
                alien for alien in self.aliens
                if alien not in laser.hit_aliens and laser.rect.colliderect(alien.rect)
            ]
            if not hit_aliens:
                continue

            # Lowest alien is physically closest to the laser origin at the bottom.
            hit_aliens.sort(key=lambda alien: alien.rect.centery, reverse=True)
            for alien in hit_aliens:
                if alien not in self.aliens:
                    continue

                laser.hit_aliens.add(alien)
                self.explosions.add(Explosion(alien.rect.centerx, alien.rect.centery))
                self.audio.play('explosion')
                self.scores.add_for_color(alien.color)
                self._try_spawn_powerup_drop(alien)
                alien.kill()
                score_changed = True

                if not laser.is_piercing:
                    laser.kill()
                    break

        if score_changed:
            self.spawn_director.adjust_difficulty(self.scores.score)
            self.spawn_director.sync_background_speed(
                self.bg_group,
                self.scores.score,
            )

    def _try_spawn_powerup_drop(self, alien: Alien) -> None:
        """Roll the drop table for a killed alien.

        Args:
            alien: The alien that was just destroyed.
        """
        if alien.color == 'red':
            if (
                not self._shield_is_active()
                and random.random() < PowerupSettings.SHIELD_DROP_CHANCE
            ):
                self.powerups.add(
                    PowerUp(alien.rect.center, PowerupSettings.SHIELD_TYPE)
                )
                return

            if self.hearts < HeartSettings.MAX and random.random() < AlienSettings.DROP_CHANCE['red']:
                self.powerups.add(PowerUp(alien.rect.center, PowerupSettings.HEART_TYPE))
            return

        if alien.color == 'green':
            if self.laser_level >= PowerupSettings.MAX_LASER_LEVEL:
                return
            if random.random() < AlienSettings.DROP_CHANCE['green']:
                self.powerups.add(
                    PowerUp(
                        alien.rect.center,
                        PowerupSettings.LASER_UPGRADE_TYPE,
                    )
                )
            return

        if alien.color == 'yellow':
            if self.burst_tier >= PowerupSettings.MAX_BURST_TIER:
                return
            if random.random() < AlienSettings.DROP_CHANCE['yellow']:
                self.powerups.add(
                    PowerUp(alien.rect.center, PowerupSettings.BURST_TYPE)
                )
            return

        if alien.color == 'blue':
            if random.random() < AlienSettings.DROP_CHANCE['blue']:
                self.powerups.add(
                    PowerUp(alien.rect.center, PowerupSettings.RAINBOW_BEAM_TYPE)
                )

    def _resolve_powerups_at_bottom(self) -> None:
        """Apply powerup effects once drops reach the bottom edge."""
        for powerup in list(self.powerups):
            if not powerup.reached_bottom():
                continue

            if powerup.kind == PowerupSettings.HEART_TYPE:
                if self.hearts < HeartSettings.MAX:
                    self.hearts += 1
                    self.audio.play('powerup_heart')
            elif powerup.kind == PowerupSettings.SHIELD_TYPE:
                self._shield_until = pygame.time.get_ticks() + ShieldSettings.DURATION_MS
                self.audio.play('powerup_weapon')
            elif powerup.kind == PowerupSettings.LASER_UPGRADE_TYPE:
                if self.laser_level < PowerupSettings.MAX_LASER_LEVEL:
                    self.laser_level += 1
                    self.audio.play('powerup_twin')
            elif powerup.kind == PowerupSettings.BURST_TYPE:
                if self.burst_tier < PowerupSettings.MAX_BURST_TIER:
                    self.burst_tier += 1
                    self.audio.play('powerup_twin')
            elif powerup.kind == PowerupSettings.RAINBOW_BEAM_TYPE:
                self._rainbow_beam_until = (
                    pygame.time.get_ticks() + PowerupSettings.RAINBOW_BEAM_DURATION
                )
                self.audio.play('powerup_weapon')

            powerup.kill()

    def _shield_is_active(self) -> bool:
        """Return True while the temporary shield should block miss penalties."""
        return pygame.time.get_ticks() < self._shield_until

    def _apply_shield_bottom_kill(self, alien: Alien) -> None:
        """Treat a bottom collision as a kill while the shield is active.

        Args:
            alien: The alien that reached the bottom edge while shielded.
        """
        self.explosions.add(Explosion(alien.rect.centerx, alien.rect.centery))
        self.audio.play('explosion')
        self.scores.add_for_color(alien.color)
        self._try_spawn_powerup_drop(alien)
        alien.kill()

        self.spawn_director.adjust_difficulty(self.scores.score)
        self.spawn_director.sync_background_speed(self.bg_group, self.scores.score)

    def _trigger_damage_flash(self) -> None:
        """Start the invincibility window and schedule the red/white screen flash."""
        now = pygame.time.get_ticks()
        self._invincible_until = now + DamageSettings.INVINCIBILITY_MS
        self._flash_start = now
        self._flash_end = now + DamageSettings.FLASH_DURATION

    def _apply_miss_penalty(self, alien_color: str) -> None:
        """Apply the bottom-hit penalty for a missed alien.

        Blue aliens deal no damage — escaping them is a missed score opportunity
        only. Without shield protection, a hit strips laser and burst powerups
        first; once both are gone, hearts are deducted. Invincibility frames
        block all damage during the post-hit recovery window.

        Args:
            alien_color: The color of the alien that reached the bottom.
        """
        if alien_color == 'blue':
            return

        if self._shield_is_active():
            return

        if pygame.time.get_ticks() < self._invincible_until:
            return  # Still inside the invincibility window from a recent hit.

        self._trigger_damage_flash()

        if self.laser_level > 1 or self.burst_tier > 0:
            self.laser_level = 1
            self.burst_tier = 0
            self._pending_follow_ups = []
            self.audio.play('alarm_med')
            return

        self.hearts -= 1
        if self.hearts == 2:
            self.audio.play('alarm_med')
        elif self.hearts == 1:
            self.audio.play('alarm_low')

    # -------------------------
    # AUDIO / VOLUME ACTIONS
    # -------------------------

    def _pause_game(self) -> None:
        """Pause gameplay and suspend the active music channel."""
        self.audio.play('pause')
        self.audio.pause_music()
        self.state = 'paused'

    def _resume_game(self) -> None:
        """Resume gameplay and unpause the active music channel."""
        self.audio.play('unpause')
        self.audio.unpause_music()
        self.state = 'playing'

    def _enter_game_over(self) -> None:
        """Finalize the run and transition into the game-over state."""
        self.hearts = 0
        self.word_manager.clear_lock()
        self.scores.finalize_game_over()
        self.audio.stop_alarms()
        self.audio.play_game_over_music()
        self.state = 'game_over'

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def _handle_events(self) -> None:
        """Dispatch the current frame's pygame events."""
        for event in pygame.event.get():
            self._handle_event(event)

    def _handle_event(self, event: pygame.event.Event) -> None:
        """Route a single pygame event to the correct handler.

        Args:
            event: The pygame event raised during the current frame.
        """
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event)
            return

        if event.type == self.spawn_director.spawn_event:
            self._handle_spawn_event()

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle one keyboard event based on the active game state.

        Args:
            event: The keyboard event to process.
        """
        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            return

        if self.state == 'intro':
            self._handle_intro_keydown(event)
        elif self.state == 'playing':
            self._handle_playing_keydown(event)
        elif self.state == 'paused':
            self._handle_paused_keydown(event)
        elif self.state == 'game_over':
            self._handle_game_over_keydown(event)

    def _handle_intro_keydown(self, event: pygame.event.Event) -> None:
        """Handle intro-screen keyboard input.

        Args:
            event: The keyboard event to process.
        """
        if event.key == pygame.K_RETURN:
            self._start_game()

    def _handle_playing_keydown(self, event: pygame.event.Event) -> None:
        """Handle live gameplay keyboard input.

        Args:
            event: The keyboard event to process.
        """
        if event.key == pygame.K_SPACE:
            self._handle_spacebar_playing()
            return

        if event.key == pygame.K_RETURN:
            # Enter toggles pause during active gameplay.
            self._pause_game()
            return

        if event.key == pygame.K_BACKSPACE:
            self.word_manager.handle_backspace(self.aliens)
            return

        if not event.unicode.isalpha():
            return

        if self.word_manager.prefix_length >= TypingSettings.MAX_LENGTH:
            return

        self.word_manager.handle_letter(event.unicode, self.aliens)
        targeted_alien = self.word_manager.targeted_alien
        if (
            targeted_alien is not None
            and self.word_manager.current_prefix == targeted_alien.word.upper()
        ):
            self._resolve_completed_word()

    def _handle_paused_keydown(self, event: pygame.event.Event) -> None:
        """Handle paused-state keyboard input.

        Args:
            event: The keyboard event to process.
        """
        if event.key == pygame.K_RETURN:
            self._resume_game()

    def _handle_game_over_keydown(self, event: pygame.event.Event) -> None:
        """Handle game-over keyboard input or initials entry.

        Args:
            event: The keyboard event to process.
        """
        if self.scores.entering_initials:
            self._handle_initials_entry_keydown(event)
            return

        if event.key == pygame.K_RETURN:
            self._restart_game()

    def _handle_initials_entry_keydown(self, event: pygame.event.Event) -> None:
        """Handle leaderboard initials-entry controls.

        Args:
            event: The keyboard event to process.
        """
        if event.key == pygame.K_UP:
            self.scores.cycle_char(1)
        elif event.key == pygame.K_DOWN:
            self.scores.cycle_char(-1)
        elif event.key == pygame.K_LEFT:
            self.scores.move_cursor(-1)
        elif event.key == pygame.K_RIGHT:
            self.scores.move_cursor(1)
        elif event.key == pygame.K_RETURN:
            self.scores.submit_initials()

    def _handle_spawn_event(self) -> None:
        """Spawn a new alien when the gameplay timer fires."""
        if self.state == 'playing':
            spawned = self.spawn_director.spawn(
                self.aliens,
                self.word_manager,
                self.scores.score,
            )
            if spawned is not None and spawned.color == 'blue':
                self.audio.play('ufo')

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _update_rainbow_beam(self) -> None:
        """Spawn a fresh RainbowLaser slice every frame while the beam is active.

        The cone effect emerges from the stacking — older slices have grown wider
        and traveled further, so a stack forms an upside-down triangle.  The
        'hyper' SFX replays each frame on the same channel; the channel auto-cuts
        the previous play so the effect is a sustained hum, not a stutter.
        """
        if pygame.time.get_ticks() >= self._rainbow_beam_until:
            return
        self.lasers.add(RainbowLaser())
        self.audio.play('hyper')

    def _update_follow_up_shots(self) -> None:
        """Fire any burst follow-up shots whose delay has elapsed.

        Each queued shot fires at the alien's predicted position at the
        moment it fires (fresh calculation), so it acts as a genuine
        backup if the primary shot missed.  If the alien is already dead
        the follow-up is silently dropped.
        """
        if not self._pending_follow_ups:
            return
        now = pygame.time.get_ticks()
        remaining = []
        for fire_at, alien in self._pending_follow_ups:
            if now < fire_at:
                remaining.append((fire_at, alien))
                continue
            if alien in self.aliens:
                self._spawn_shot_lasers(alien)
                self._play_shot_sound()
        self._pending_follow_ups = remaining

    def _update_playing(self) -> None:
        """Advance gameplay-only sprite state and resolve gameplay outcomes."""
        self.audio.ensure_bgm_playing()
        self.aliens.update()
        self.lasers.update()
        self._update_rainbow_beam()
        self._update_follow_up_shots()
        self._resolve_laser_collisions()
        self.explosions.update()
        self.powerups.update()
        self._resolve_powerups_at_bottom()

        for alien in list(self.aliens):
            if alien.rect.top <= ScreenSettings.HEIGHT:
                continue

            if alien is self.word_manager.targeted_alien:
                self.word_manager.clear_lock()

            if self._shield_is_active():
                self._apply_shield_bottom_kill(alien)
                continue

            alien.kill()
            self._apply_miss_penalty(alien.color)
            if self.hearts <= 0:
                self._enter_game_over()
                break

    def _update(self, delta_time: float) -> None:
        """Advance one frame of game state.

        Args:
            delta_time: Elapsed seconds since the previous rendered frame.
        """
        self.current_level = self.spawn_director.level(self.scores.score)

        if self.state in ('intro', 'playing', 'game_over'):
            self.bg_group.update(delta_time)

        if self.state == 'playing':
            self._update_playing()

    def _draw_typing_buffer(self) -> None:
        """Render the current typing prefix at the bottom of the playfield."""
        if not self.word_manager.current_prefix:
            return

        buffer_surf = self.typing_font.render(
            self.word_manager.current_prefix,
            True,
            TypingSettings.COLOR,
        )
        buffer_rect = buffer_surf.get_rect(
            midbottom=(
                ScreenSettings.WIDTH / 2,
                ScreenSettings.HEIGHT - TypingSettings.OFFSET_FROM_BOTTOM,
            )
        )
        self.screen.blit(buffer_surf, buffer_rect)

    def _draw_playfield(self) -> None:
        """Render the shared gameplay playfield layers and alien words."""
        self.aliens.draw(self.screen)
        self.lasers.draw(self.screen)
        self.explosions.draw(self.screen)
        self.powerups.draw(self.screen)

        for alien in self.aliens:
            if alien is self.word_manager.targeted_alien:
                alien.draw_word(
                    self.screen,
                    self.word_font,
                    self.word_manager.prefix_length,
                )
            else:
                alien.draw_word(self.screen, self.word_font)

    def _draw_hud(self) -> None:
        """Render the gameplay HUD for the current score, hearts, and level."""
        self.hearts_hud.draw(self.screen, self.hearts)
        self.score_hud.draw(
            self.screen,
            self.scores.score,
            self.scores.high_score,
            self.current_level,
        )

    def _draw(self) -> None:
        """Render the current frame for the active game state."""
        self.screen.fill(ScreenSettings.BG_COLOR)
        self.bg_group.draw(self.screen)

        if self.state == 'intro':
            self.intro_screen.draw(self.screen, self.scores)
        elif self.state in ('playing', 'paused'):
            self._draw_playfield()
            self._draw_hud()
            if self.state == 'playing':
                self._draw_typing_buffer()
            else:
                self.pause_screen.draw(self.screen)
        elif self.state == 'game_over':
            self.game_over_screen.draw(self.screen, self.scores.score, self.scores)

        self.crt.draw()
        if self.state == 'playing' and self._shield_is_active():
            shield_time_left = self._shield_until - pygame.time.get_ticks()
            if shield_time_left <= ShieldSettings.WARNING_MS:
                show_blue = (
                    (shield_time_left // ShieldSettings.WARNING_FLASH_INTERVAL) % 2
                ) == 0
            else:
                show_blue = True
            self.crt.draw_shield_flash(show_blue)

        # Damage flash is drawn after the CRT so it sits on top of everything.
        # It's separate from crt.draw() so a future CRT-disable toggle won't hide it.
        if self.state == 'playing' and pygame.time.get_ticks() < self._flash_end:
            elapsed = pygame.time.get_ticks() - self._flash_start
            show_red = (elapsed // DamageSettings.FLASH_INTERVAL) % 2 == 0
            self.crt.draw_damage_flash(show_red)
        pygame.display.flip()

    def run(self) -> None:
        """Run the main game loop until the user quits."""
        while self.running:
            delta_time = self.clock.get_time() / 1000.0
            self._handle_events()
            self._update(delta_time)
            self._draw()
            self.clock.tick(ScreenSettings.FPS)

        self.close_game()

# Main execution
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()

