import pygame
import sys
import time
import random

from settings import *
from core.animations import Background, Explosion
from core.sprites import Player, BombBlast
from ui.style import Style
from ui.crt import CRT
from systems.audio import Audio
from systems.managers import (
    CollisionManager,
    ScoreManager,
    SessionStateManager,
    SpawnDirector,
)


class GameManager:
    """Coordinates Star Hero's display, audio, sprite groups, sub-managers, and main loop."""

    def __init__(self):
        """Initialize pygame, the display, audio, sprite groups, and sub-managers."""
        # -------- Pygame core --------
        pygame.init()

        # Keep joystick objects alive so button events remain reliable on all backends.
        pygame.joystick.init()
        self.joysticks = []
        self.refresh_joysticks()

        # -------- Display --------
        self.screen = pygame.display.set_mode((ScreenSettings.RESOLUTION), pygame.SCALED)
        pygame.display.set_caption(ScreenSettings.TITLE)
        self.clock = pygame.time.Clock()
        self._show_loading_screen()

        # -------- Subsystems --------
        self.crt = CRT(self.screen)
        self.audio = Audio()
        self.style = Style(self.screen, self.audio)

        # Volume display state. The timer fires once after VOLUME_DISPLAY_TIME
        # to hide the bar; before this lived on SpawnDirector, which had
        # nothing to do with UI.
        self.show_volume = False
        self.volume_display_timer = pygame.event.custom_type()

        # -------- Managers --------
        self.collisions = CollisionManager(self)
        self.scores = ScoreManager(self)
        self.session = SessionStateManager(self)
        self.spawner = SpawnDirector(self)

        # -------- Player health --------
        self.hearts = PlayerSettings.MAX_HEALTH

        # -------- Sprite groups --------
        self.background = pygame.sprite.Group()
        Background(self.background)

        player_sprite = Player((ScreenSettings.CENTER), self.audio)
        self.player = pygame.sprite.GroupSingle(player_sprite)  # type: ignore[arg-type]
        self.player.sprite.bombs = BombSettings.START_COUNT

        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.exploding_sprites = pygame.sprite.Group()
        self.bomb_blasts = pygame.sprite.Group()

    # -------------------------
    # BOOT / LIFECYCLE
    # -------------------------

    def _show_loading_screen(self) -> None:
        """Paint a "LOADING..." card before audio loading freezes the UI thread.

        Audio pre-loading can take a noticeable beat on slower hardware. We
        cannot funnel this through Style because Audio is not constructed
        yet, so the loading screen renders directly here.
        """
        self.screen.fill(ColorSettings.COLORS['BLACK'])
        loading_font = pygame.font.Font(FontSettings.FONT, FontSettings.MEDIUM)
        loading_text = loading_font.render("LOADING...", False, FontSettings.COLOR)
        loading_rect = loading_text.get_rect(center=(ScreenSettings.WIDTH // 2, ScreenSettings.HEIGHT // 2))
        self.screen.blit(loading_text, loading_rect)
        pygame.display.flip()

    def close_game(self):
        """Save scores, then close the game process cleanly."""
        self.scores.save_scores()
        pygame.quit()
        sys.exit()

    def refresh_joysticks(self) -> None:
        """Rebuild the active joystick list to support controller hot-plugging."""
        self.joysticks = []
        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            if not joystick.get_init():
                joystick.init()
            self.joysticks.append(joystick)

    def quit_combo_pressed(self):
        """Return True if the START + SELECT + L1 + R1 quit chord is held on any controller."""
        if len(self.joysticks) != pygame.joystick.get_count():
            self.refresh_joysticks()

        for joystick in self.joysticks:
            try:
                if all(joystick.get_button(button) for button in ControllerSettings.QUIT_COMBO):
                    return True
            except pygame.error:
                # Device may have disconnected between frames.
                continue
        return False

    def handle_joystick_hotplug(self, event: pygame.event.Event) -> bool:
        """Refresh the joystick cache when a controller add/remove event arrives.

        Args:
            event (pygame.event.Event): The event to inspect.

        Returns:
            bool: True if the event was a hotplug event and was handled.
        """
        joystick_event_types = {
            getattr(pygame, 'JOYDEVICEADDED', None),
            getattr(pygame, 'JOYDEVICEREMOVED', None),
        }
        if event.type in joystick_event_types:
            self.refresh_joysticks()
            return True
        return False

    # -------------------------
    # GAMEPLAY ACTIONS
    # -------------------------

    def handle_alien_destroyed(self, alien) -> None:
        """Award score, ramp difficulty, explode, and roll for a powerup drop.

        Args:
            alien (Alien): The alien that was destroyed.
        """
        self.scores.score += alien.value
        self.spawner.adjust_difficulty()
        self.explode(alien.rect.centerx, alien.rect.centery)
        self.spawner.try_spawn_alien_drop(alien)

    def trigger_bomb_blast(self, center: tuple[int, int]) -> None:
        """Spawn an expanding bomb blast at the given center position.

        Args:
            center (tuple[int, int]): The (x, y) origin of the blast.
        """
        self.bomb_blasts.add(BombBlast(center))

    def handle_bomb_input(self) -> None:
        """Detonate the active bomb if one is airborne, otherwise launch a fresh one."""
        detonation_center = self.player.sprite.detonate_air_bomb()
        if detonation_center:
            self.trigger_bomb_blast(detonation_center)
            return

        self.player.sprite.launch_bomb()

    def explode(self, x_pos: int, y_pos: int) -> None:
        """Spawn an explosion sprite at the given position and play the SFX.

        Args:
            x_pos (int): The x-coordinate of the explosion's center.
            y_pos (int): The y-coordinate of the explosion's center.
        """
        self.audio.play('explosion')
        explosion = Explosion(x_pos, y_pos)
        self.exploding_sprites.add(explosion)
        explosion.explode()

    # -------------------------
    # AUDIO / VOLUME ACTIONS
    # -------------------------

    def toggle_debug_mute(self) -> None:
        """Flip the debug mute flag and immediately reapply audio volumes."""
        AudioSettings.DEBUG_MUTE = not AudioSettings.DEBUG_MUTE
        self.audio.update()

    def adjust_master_volume(self, delta: float, show_overlay: bool = False) -> None:
        """Step master volume by ``delta`` (clamped to [0, 1]) and optionally show the bar.

        Args:
            delta (float): Amount to add to the current volume (can be negative).
            show_overlay (bool): If True, displays the volume bar HUD.
        """
        self.audio.master_volume = max(0.0, min(1.0, self.audio.master_volume + delta))
        self.audio.update()

        if show_overlay:
            pygame.time.set_timer(self.volume_display_timer, UISettings.VOLUME_DISPLAY_TIME)
            self.show_volume = True

    def pause_game(self) -> None:
        """Pause music, play the pause SFX, and enter the pause loop."""
        self.audio.pause_music()
        self.audio.play('pause')
        self.session.pause()

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def _process_events(self, delta_time: float) -> None:
        """Drain pygame's event queue and dispatch by event type."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()

            if self.handle_joystick_hotplug(event):
                continue

            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_joybuttondown(event)
            elif event.type == pygame.JOYHATMOTION:
                self._handle_joyhatmotion(event)
            elif event.type == self.volume_display_timer:
                # Volume bar HUD timed out. Disarm the timer so the next
                # adjustment can re-arm it without a stale carry-over.
                self.show_volume = False
                pygame.time.set_timer(self.volume_display_timer, 0)
            elif self.session.game_active:
                self._handle_active_gameplay_timer(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Route a single keyboard press."""
        # Global keys (always honored regardless of run state).
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        if event.key == pygame.K_ESCAPE:
            # ESC always exits the game and returns to the launcher,
            # matching the L1+R1+START+SELECT controller combo.
            self.close_game()
        if event.key == pygame.K_m:
            self.toggle_debug_mute()
        if event.key in (pygame.K_KP_PLUS, pygame.K_EQUALS):
            self.adjust_master_volume(0.1, show_overlay=True)
        elif event.key in (pygame.K_KP_MINUS, pygame.K_MINUS):
            self.adjust_master_volume(-0.1, show_overlay=True)

        # Active gameplay keys.
        if self.session.game_active:
            if event.key == pygame.K_b:
                self.handle_bomb_input()
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # ENTER pauses an active run. On the title/game-over screens
                # the same key restarts or submits initials (handled below).
                self.pause_game()
            return

        # Title / game-over keys.
        if self.scores.entering_initials:
            if event.key == pygame.K_LEFT:
                self.scores._move_initials_cursor(-1)
            elif event.key == pygame.K_RIGHT:
                self.scores._move_initials_cursor(1)
            elif event.key == pygame.K_UP:
                self.scores._cycle_initials_char(1)
            elif event.key == pygame.K_DOWN:
                self.scores._cycle_initials_char(-1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.scores.submit_initials()
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.session.reset_for_new_game()

    def _handle_joybuttondown(self, event: pygame.event.Event) -> None:
        """Route a single controller button press."""
        if self.quit_combo_pressed():
            self.close_game()

        # BACK is the global fullscreen toggle.
        if event.button == ControllerSettings.BACK_BUTTON:
            pygame.display.toggle_fullscreen()

        # Active gameplay buttons.
        if self.session.game_active:
            if event.button == ControllerSettings.START_BUTTON:
                self.pause_game()
            elif event.button == ControllerSettings.B_BUTTON:
                self.handle_bomb_input()
            return

        # Title / game-over buttons. START or A both serve as
        # confirm/restart and as initials-submit, mirroring the keyboard
        # mapping where RETURN handles both jobs.
        if event.button in (ControllerSettings.A_BUTTON, ControllerSettings.START_BUTTON):
            if self.scores.entering_initials:
                self.scores.submit_initials()
            else:
                self.session.reset_for_new_game()

    def _handle_joyhatmotion(self, event: pygame.event.Event) -> None:
        """Route a D-pad direction event for volume + initials navigation."""
        # Volume up/down lives on the D-pad outside initials entry. During
        # initials entry the same hat directions cycle characters.
        if not self.scores.entering_initials:
            if event.value[1] == 1:
                self.adjust_master_volume(0.1, show_overlay=True)
            elif event.value[1] == -1:
                self.adjust_master_volume(-0.1, show_overlay=True)
            return

        hat_x, hat_y = event.value
        if hat_x == -1:
            self.scores._move_initials_cursor(-1)
        elif hat_x == 1:
            self.scores._move_initials_cursor(1)
        if hat_y == 1:
            self.scores._cycle_initials_char(1)
        elif hat_y == -1:
            self.scores._cycle_initials_char(-1)

    def _handle_active_gameplay_timer(self, event: pygame.event.Event) -> None:
        """Dispatch alien spawn / shoot / death timer events while the game is active."""
        if event.type == self.spawner.alien_spawn_timer:
            alien_color = random.choices(AlienSettings.COLOR, weights=AlienSettings.SPAWN_CHANCE)[0]
            self.spawner.spawn_aliens(alien_color)
        elif event.type == self.spawner.alien_laser_timer:
            self.spawner.alien_shoot()
        elif event.type == self.spawner.player_death_timer:
            self._on_player_death_timer()

    def _on_player_death_timer(self) -> None:
        """Tear down the active run when the post-death delay expires."""
        self.audio.player_down.play()
        self.aliens.empty()
        self.powerups.empty()

        for bg in self.background.sprites():
            bg.scroll_speed = ScreenSettings.DEFAULT_BG_SCROLL_SPEED

        self.session.game_active = False
        pygame.time.set_timer(self.spawner.player_death_timer, 0)
        self.scores.finalize_game_over_score()

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _world_speed_multiplier(self) -> float:
        """Return the current world-speed scalar derived from the player's boost state."""
        if self.session.game_active and self.player.sprite:
            return self.player.sprite.get_world_speed_multiplier()
        return 1.0

    def _update_world(self, delta_time: float, world_speed_multiplier: float) -> None:
        """Advance every gameplay sprite group + run collision checks for the frame."""
        if not self.session.game_active:
            return

        self.player.sprite.world_speed_multiplier = world_speed_multiplier
        if self.session.player_alive:
            self.player.update()
        self.alien_lasers.update(world_speed_multiplier)
        self.aliens.update(world_speed_multiplier)
        self.powerups.update()
        self.bomb_blasts.update()
        self.collisions.update()
        self.exploding_sprites.update(ExplosionSettings.ANIMATION_SPEED)

    def _draw_active_gameplay(self) -> None:
        """Composite gameplay sprites, HUD, and confusion beams while a run is in progress."""
        # Player projectiles
        self.player.sprite.lasers.draw(self.screen)
        self.player.sprite.bomb_projectiles.draw(self.screen)

        # Player ship + shield orb (only while alive)
        if self.session.player_alive:
            self.player.draw(self.screen)
            self.player.sprite.draw_shield_orb(self.screen)

        # Explosions on top of the player but under the aliens for readability.
        self.exploding_sprites.draw(self.screen)

        # Confusion beams sit between aliens and ships visually; drawn before
        # the aliens themselves so the alien sprite occludes the beam origin.
        for alien in self.aliens:
            alien.draw_confusion_beam(self.screen)

        self.aliens.draw(self.screen)
        self.alien_lasers.draw(self.screen)
        self.powerups.draw(self.screen)
        self.bomb_blasts.draw(self.screen)

        self.style.update('game_active', self.scores.save_data, self.scores.score)
        self.style.display_player_status(self.player.sprite)
        self.style.display_hearts(self.hearts)

    def _draw_inactive_screen(self) -> None:
        """Composite the intro or game-over screen depending on whether a run has happened."""
        # Show intro screen if score is 0, otherwise show game over screen.
        if self.scores.score == 0:
            self.style.update('intro', self.scores.save_data, self.scores.score)
        else:
            self.style.update(
                'game_over',
                self.scores.save_data,
                self.scores.score,
                entering_initials=self.scores.entering_initials,
                initials=self.scores.initials,
                initials_index=self.scores.initials_index,
            )

    def _update_music(self) -> None:
        """Drive intro/BGM playback based on whether a run is currently active."""
        if self.session.game_active:
            self.audio.stop_intro_music()
            self.session.play_intro_music = False
            self.audio.ensure_bgm_playing()
        else:
            self.audio.stop_bgm()
            if self.session.play_intro_music:
                self.audio.play_intro_music()

    def _render_frame(self, delta_time: float, world_speed_multiplier: float) -> None:
        """Draw one full frame: background, gameplay or menus, volume HUD, CRT pass."""
        self.screen.fill(ScreenSettings.BG_COLOR)

        self.background.update(delta_time, world_speed_multiplier)
        self.background.draw(self.screen)

        if self.show_volume:
            self.style.display_volume()

        if self.session.game_active:
            self._draw_active_gameplay()
        else:
            self._draw_inactive_screen()

        self.crt.draw()

    def run(self) -> None:
        """Main game loop: pump events, advance world, render, repeat."""
        last_time = time.time()  # Track time for delta_time so animations are frame-rate independent.
        while True:
            delta_time = time.time() - last_time
            last_time = time.time()

            if self.quit_combo_pressed():
                self.close_game()

            self._process_events(delta_time)
            world_speed_multiplier = self._world_speed_multiplier()
            self._update_music()
            self._update_world(delta_time, world_speed_multiplier)
            self._render_frame(delta_time, world_speed_multiplier)
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)


# Main execution
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()
