import os
import json
import random
import pygame

from settings import *
from core.sprites import Laser, Alien, PowerUp


class CollisionManager:
    """Resolves all per-frame sprite-to-sprite collisions in one place."""

    def __init__(self, game):
        """Store the shared game reference used by every collision check.

        Args:
            game (GameManager): The main game manager instance.
        """
        self.game = game

    def _player_lasers(self):
        """Destroy aliens hit by player lasers and dispatch the kill effect."""
        if not self.game.player.sprite.lasers:
            return
        for laser in self.game.player.sprite.lasers:
            aliens_hit = pygame.sprite.spritecollide(laser, self.game.aliens, True)
            if aliens_hit:
                # Piercing lasers continue through enemies, otherwise the laser dies on impact.
                if not laser.is_piercing:
                    laser.kill()

                for alien in aliens_hit:
                    self.game.handle_alien_destroyed(alien)

    def _player_bombs(self):
        """Detonate any bomb projectile that strikes an alien and start a blast."""
        player = self.game.player.sprite
        for bomb in player.bomb_projectiles.sprites():
            aliens_hit = pygame.sprite.spritecollide(bomb, self.game.aliens, True)
            if not aliens_hit:
                continue

            for alien in aliens_hit:
                self.game.handle_alien_destroyed(alien)

            blast_center = bomb.rect.center
            bomb.kill()
            self.game.trigger_bomb_blast(blast_center)

    def _bomb_blasts(self):
        """Apply expanding-blast damage to aliens caught inside the radius."""
        for blast in self.game.bomb_blasts:
            nearby_aliens = pygame.sprite.spritecollide(blast, self.game.aliens, False)
            for alien in nearby_aliens:
                if id(alien) in blast.hit_aliens:
                    continue

                dx = alien.rect.centerx - blast.center[0]
                dy = alien.rect.centery - blast.center[1]
                # Compare squared distances to avoid a costly sqrt call.
                # Equivalent to: distance(alien, blast_center) <= blast.radius
                if (dx * dx) + (dy * dy) <= (blast.radius * blast.radius):
                    blast.hit_aliens.add(id(alien))
                    alien.kill()
                    self.game.handle_alien_destroyed(alien)

    def _alien_lasers(self):
        """Damage the player when an alien laser overlaps the ship."""
        player = self.game.player.sprite
        for laser in self.game.alien_lasers:
            if pygame.sprite.spritecollide(laser, self.game.player, False):
                laser.kill() # Lasers always stop on player contact.
                if not player.is_invulnerable():
                    self.game.session.player_damage()

    def _ship_collisions(self):
        """Damage the player and award score when a ship-to-alien collision occurs."""
        # Damage player if their ship collides with an alien.
        aliens_crash = pygame.sprite.spritecollide(self.game.player.sprite, self.game.aliens, True)
        for alien in aliens_crash:
            self.game.scores.score += alien.value
            if self.game.hearts > 1:
                self.game.explode(alien.rect.centerx, alien.rect.centery)
        if aliens_crash and not self.game.player.sprite.is_invulnerable():
            self.game.session.player_damage()

    def _powerups(self):
        """Apply the effects of powerups the player has just walked over."""
        powerups_collected = pygame.sprite.spritecollide(self.game.player.sprite, self.game.powerups, True)
        for powerup in powerups_collected:
            if powerup.powerup_type == 'heal' and self.game.hearts < PlayerSettings.MAX_HEALTH: # Only heal if player isn't at full health
                self.game.audio.play('powerup_heart')
                self.game.hearts += 1
            else:
                # Only play sound if it's a new powerup activation, not if player already has it active
                if powerup.powerup_type == 'laser_upgrade':
                    if self.game.player.sprite.laser_level < 4:
                        self.game.audio.play('powerup_twin')
                elif powerup.powerup_type in ['rapid_fire', 'rainbow_beam', 'shield', 'bomb']:
                    self.game.audio.play('powerup_weapon')

                self.game.player.sprite.activate_powerup(powerup)

    def _confusion_beams(self):
        """Confuse the player when any blue-alien beam mask overlaps the ship.

        Each ``Alien`` reports its own current beam mask via
        ``get_confusion_beam_mask``. Doing the overlap test here keeps
        gameplay-only state changes (shield strip, confusion timer) out of
        the rendering path in ``main.py``. The shield is stripped on every
        contact so picking up a fresh shield mid-beam still gets melted
        immediately, matching pre-refactor behavior.
        """
        player = self.game.player.sprite
        for alien in self.game.aliens:
            beam_mask = alien.get_confusion_beam_mask()
            if beam_mask is None:
                continue
            if beam_mask.overlap(player.mask, player.rect.topleft):
                player.shield_active = False
                if not player.confused:
                    player.confused = True
                    player.confusion_timer = pygame.time.get_ticks()

    def update(self):
        """Run every collision check for the current frame."""
        self._player_lasers()
        self._player_bombs()
        self._bomb_blasts()
        self._alien_lasers()
        self._ship_collisions()
        self._powerups()
        self._confusion_beams()


class ScoreManager:
    """Manages score, high score, leaderboard I/O, and initials entry state."""

    def __init__(self, game):
        """Initialize score, leaderboard cache, and initials-entry state.

        Args:
            game (GameManager): The main game manager instance.
        """
        self.game = game
        self.score = 0
        self.save_data = {
            'high_score': 0,
            'leaderboard': []
        }

        # Leaderboard / initials entry state
        self.entering_initials = False
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

        # Load saved high score and leaderboard data if available.
        # AssetPaths.BASE_DIR keeps the save anchored to the game root rather
        # than this module's folder, so the file does not move when this code
        # is relocated under systems/.
        try:
            score_file_path = os.path.join(AssetPaths.BASE_DIR, 'high_score.txt')
            with open(score_file_path) as high_score_file:
                self.save_data = json.load(high_score_file)
        except (OSError, json.JSONDecodeError):
            print('No file created yet')

    def reset(self) -> None:
        """Reset score and initials-entry state in preparation for a new run."""
        self.score = 0
        self.entering_initials = False
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

    def _sort_and_trim_leaderboard(self) -> None:
        """Sort the leaderboard descending, keep top 10, and refresh the high score."""
        # Sort descending by score and keep only the top 10 entries.
        self.save_data['leaderboard'] = sorted(
            self.save_data.get('leaderboard', []),
            key=lambda entry: entry['score'],
            reverse=True
        )[:10]

        if self.save_data['leaderboard']:
            self.save_data['high_score'] = self.save_data['leaderboard'][0]['score']
        else:
            self.save_data['high_score'] = 0

    def save_scores(self) -> None:
        """Write the leaderboard and high score to disk."""
        self._sort_and_trim_leaderboard()
        score_file_path = os.path.join(AssetPaths.BASE_DIR, 'high_score.txt')
        with open(score_file_path, 'w') as high_score_file:
            json.dump(self.save_data, high_score_file)

    def qualifies_for_leaderboard(self, score: int) -> bool:
        """Return True if ``score`` would earn a leaderboard slot.

        Args:
            score (int): The player's final score to check.

        Returns:
            bool: True if the score earns a leaderboard spot, False otherwise.
        """
        leaderboard = self.save_data.get('leaderboard', [])
        if len(leaderboard) < 10:
            return score > 0
        return score > leaderboard[-1]['score']

    def start_initial_entry(self) -> None:
        """Begin the initials-entry flow for a qualifying high-score run."""
        self.entering_initials = True
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = self.score

    def submit_initials(self) -> None:
        """Commit the entered initials/score to the leaderboard and persist."""
        leaderboard = self.save_data.get('leaderboard', [])
        # If this name already exists on the board, update it only if the new score is higher.
        # Otherwise add a fresh entry so duplicate names don't bloat the leaderboard.
        existing_entry = next((item for item in leaderboard if item["name"] == self.initials), None)

        if existing_entry:
            if self.pending_score > existing_entry['score']:
                existing_entry['score'] = self.pending_score
        else:
            leaderboard.append({'name': self.initials, 'score': self.pending_score})

        self.save_data['leaderboard'] = leaderboard
        self._sort_and_trim_leaderboard()
        self.save_scores()

        self.entering_initials = False
        self.pending_score = None
        self.score_processed = True

    def finalize_game_over_score(self) -> None:
        """On game over, route to initials entry or persist the score directly."""
        if self.score_processed:
            return
        if self.qualifies_for_leaderboard(self.score):
            self.start_initial_entry()
        else:
            self._sort_and_trim_leaderboard()
            self.save_scores()
            self.score_processed = True

    def _move_initials_cursor(self, step: int) -> None:
        """Move the initials-entry cursor and clamp to the valid range.

        Args:
            step (int): Direction to move (-1 for left, 1 for right).
        """
        self.initials_index = max(0, min(2, self.initials_index + step))

    def _cycle_initials_char(self, step: int) -> None:
        """Rotate the highlighted initials character by one alphabet step.

        Args:
            step (int): Direction to cycle (1 for forward, -1 for backward).
        """
        chars = list(self.initials)
        current = chars[self.initials_index]
        # Use ord/chr arithmetic to step through ASCII letters, wrapping Z→A and A→Z.
        if step > 0:
            chars[self.initials_index] = 'A' if current == 'Z' else chr(ord(current) + 1)
        else:
            chars[self.initials_index] = 'Z' if current == 'A' else chr(ord(current) - 1)
        self.initials = ''.join(chars)


class SessionStateManager:
    """Tracks active/paused/alive state, run resets, the pause loop, and player damage."""

    def __init__(self, game):
        """Store the shared game reference and seed session-state flags.

        Args:
            game (GameManager): The main game manager instance.
        """
        self.game = game
        self.game_active = False
        self.paused = False
        self.player_alive = True
        self.play_intro_music = True

    def reset_for_new_game(self) -> None:
        """Reset every per-run game-state field so a fresh run can start."""
        game = self.game
        game.scores.reset()
        game.hearts = PlayerSettings.MAX_HEALTH
        self.player_alive = True
        self.game_active = True

        # Reset player position
        game.player.sprite.rect.center = ScreenSettings.CENTER

        # Clear all sprite groups from previous run
        game.aliens.empty()
        game.alien_lasers.empty()
        game.powerups.empty()
        game.exploding_sprites.empty()
        game.bomb_blasts.empty()
        game.player.sprite.lasers.empty()
        game.player.sprite.bomb_projectiles.empty()

        # Reset player state
        player = game.player.sprite
        player.ready = True
        player.laser_time = 0
        player.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN
        player.laser_level = 1
        player.rapid_fire_level = 0
        player.rainbow_beam_active = False
        player.rainbow_beam_start_time = 0
        player.shield_active = False
        player.shield_start_time = 0
        player.bombs = BombSettings.START_COUNT

        player.boost_meter = 1.0
        player.boost_active = False
        player.brake_active = False
        player.boost_locked_until_full = False
        player.world_speed_multiplier = 1.0

        player.confused = False
        player.confusion_timer = 0

        player.is_flashing = False
        player.flash_timer = 0
        player.last_flash_time = 0
        player.is_red = False
        player.image = player.original_image.copy()

        # Reset background speed
        for bg in game.background.sprites():
            bg.scroll_speed = ScreenSettings.DEFAULT_BG_SCROLL_SPEED

        # Stop any lingering audio/effects from previous game
        game.audio.stop_alarms()

        # Make sure death timer isn't still hanging around
        pygame.time.set_timer(game.spawner.player_death_timer, 0)

    def pause(self) -> None:
        """Toggle pause, then drain events on a tight inner loop while paused."""
        game = self.game
        self.paused = not self.paused
        while self.paused:
            if game.quit_combo_pressed():
                game.close_game()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.close_game()

                if game.handle_joystick_hotplug(event):
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    if event.key == pygame.K_ESCAPE:
                        # ESC always exits the game and returns to the launcher,
                        # matching the L1+R1+START+SELECT controller combo.
                        game.close_game()
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.unpause_game()
                    if event.key == pygame.K_m:
                        game.toggle_debug_mute()

                if event.type == pygame.JOYBUTTONDOWN:
                    if game.quit_combo_pressed():
                        game.close_game()
                    if event.button == ControllerSettings.START_BUTTON:
                        self.unpause_game()
                    if event.button == ControllerSettings.BACK_BUTTON:
                        pygame.display.toggle_fullscreen()

            game.screen.fill((0, 0, 0))
            game.style.update('pause', game.scores.save_data, game.scores.score)
            pygame.display.update()

    def unpause_game(self) -> None:
        """Resume music channels and play the unpause SFX."""
        game = self.game
        game.audio.unpause_music()
        game.audio.play('unpause')
        self.paused = False

    def player_damage(self) -> None:
        """Apply a hit: strip an active upgrade if any, otherwise lose a heart."""
        game = self.game
        player = game.player.sprite
        if player and player.shield_active:
            return

        # If the player has any active upgrade, strip it instead of removing a heart.
        # This gives the player a second chance before actually taking damage.
        has_upgrade = player and (
            player.laser_level > 1 or
            player.rapid_fire_level > 0 or
            player.rainbow_beam_active
        )

        if has_upgrade:
            # Play the same alarm as losing the first heart
            game.audio.play('alarm_med')
            player.trigger_damage_effect()
            return

        game.hearts -= 1

        if player:
            player.trigger_damage_effect()

        if game.hearts == 2:
            game.audio.play('alarm_med')
        elif game.hearts == 1:
            game.audio.play('alarm_low')

        if game.hearts <= 0:
            game.explode(player.rect.centerx, player.rect.centery)
            game.audio.channels['bg_music'].pause()
            self.player_alive = False
            player.ready = False
            player.shoot_button_held = True
            pygame.time.set_timer(game.spawner.player_death_timer, PlayerSettings.DEATH_DELAY)


class SpawnDirector:
    """Owns spawn timers, alien/powerup spawning, alien shooting, and adaptive difficulty."""

    def __init__(self, game):
        """Allocate timers and store the shared game reference.

        Args:
            game (GameManager): The main game manager instance.
        """
        self.game = game

        self.alien_spawn_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_spawn_timer, AlienSettings.SPAWN_RATE)

        self.alien_laser_timer = pygame.event.custom_type()
        pygame.time.set_timer(self.alien_laser_timer, AlienSettings.LASER_RATE)

        # Custom timer for player death delay before showing game over screen.
        self.player_death_timer = pygame.event.custom_type()

    def spawn_aliens(self, alien_color: str) -> None:
        """Spawn one alien of the requested color and play its arrival cue.

        Args:
            alien_color (str): The color of the alien, which determines its behavior and point value.
        """
        self.game.aliens.add(Alien(alien_color, *ScreenSettings.RESOLUTION))
        if alien_color == 'blue':
            self.game.audio.play('ufo')

    def spawn_powerup(self, pos: tuple[int, int], color: str) -> None:
        """Spawn one powerup at the given position.

        Args:
            pos (tuple[int, int]): The (x, y) position to spawn the powerup.
            color (str): The color of the powerup, which determines its type and effect.
        """
        self.game.powerups.add(PowerUp(pos, color))

    def alien_shoot(self) -> None:
        """Pick one non-blue alien at random and have it fire a laser.

        Green aliens fire a paired left/right shot; everything else fires a
        single laser from the alien's center.
        """
        game = self.game
        if not game.aliens.sprites():
            return
        attacking_aliens = [alien for alien in game.aliens.sprites() if alien.color != 'blue']
        if not attacking_aliens:
            return
        random_alien = random.choice(attacking_aliens)

        if random_alien.color == 'green':
            # Green aliens fire a double shot — two lasers spread either side of center.
            offset = 10
            game.alien_lasers.add(
                Laser(
                    pos=(random_alien.rect.centerx - offset, random_alien.rect.centery),
                    speed=LaserSettings.ALIEN_LASER_SPEED,
                    colors=LaserSettings.COLORS['alien'],
                    width=LaserSettings.DEFAULT_WIDTH,
                )
            )
            game.alien_lasers.add(
                Laser(
                    pos=(random_alien.rect.centerx + offset, random_alien.rect.centery),
                    speed=LaserSettings.ALIEN_LASER_SPEED,
                    colors=LaserSettings.COLORS['alien'],
                    width=LaserSettings.DEFAULT_WIDTH,
                )
            )
        else:
            game.alien_lasers.add(
                Laser(
                    random_alien.rect.center,
                    LaserSettings.ALIEN_LASER_SPEED,
                    LaserSettings.COLORS['alien'],
                    LaserSettings.DEFAULT_WIDTH,
                )
            )

    def adjust_difficulty(self) -> None:
        """Tighten spawn/laser timers and speed up the background as score climbs."""
        game = self.game
        # Each full DIFFICULTY_STEP points earned unlocks one more level of difficulty.
        steps = game.scores.score // AlienSettings.DIFFICULTY_STEP

        # Reduce alien spawn interval by 25 ms per step, capped at the minimum.
        new_spawn_rate = max(
            AlienSettings.MIN_SPAWN_RATE,
            AlienSettings.SPAWN_RATE - (steps * 25)
        )
        pygame.time.set_timer(self.alien_spawn_timer, new_spawn_rate)

        # Reduce alien laser interval by 15 ms per step, capped at the minimum.
        new_laser_rate = max(
            AlienSettings.MIN_LASER_RATE,
            AlienSettings.LASER_RATE - (steps * 15)
        )
        pygame.time.set_timer(self.alien_laser_timer, new_laser_rate)

        # Speed up background scroll to reinforce the sense of increasing pace.
        new_bg_speed = min(
            ScreenSettings.BG_SCROLL_MAX,
            ScreenSettings.DEFAULT_BG_SCROLL_SPEED + (steps * ScreenSettings.BG_SCROLL_STEP)
        )
        for bg in game.background.sprites():
            bg.scroll_speed = new_bg_speed

    def try_spawn_alien_drop(self, alien: Alien) -> None:
        """Roll the destroyed alien's drop table and spawn a powerup if it hits.

        Args:
            alien (Alien): The alien that was destroyed, used to determine drop chances and type.
        """
        game = self.game
        player = game.player.sprite

        if alien.color == 'red':
            if random.random() < AlienSettings.DROP_CHANCE['red']:
                eligible_drops = []
                weights = []
                # Heart drop
                if game.hearts < PlayerSettings.MAX_HEALTH: # Only drop hearts if player isn't at full health
                    eligible_drops.append('red')
                    weights.append(1.0)
                # Bomb drop
                eligible_drops.append('bomb')
                weights.append(1.0)
                # Shield drop
                if not player.shield_active: # Only drop shield if player doesn't already have one active
                    eligible_drops.append('red_shield')
                    weights.append(0.5)  # Shields are half as likely as hearts or bombs

                if eligible_drops:
                    chosen = random.choices(eligible_drops, weights=weights, k=1)[0]
                    self.spawn_powerup(alien.rect.center, chosen)
        else:
            can_drop_color_powerup = True
            if alien.color == 'green':
                can_drop_color_powerup = player.laser_level < 4
            elif alien.color == 'yellow':
                can_drop_color_powerup = player.rapid_fire_level < 3

            if can_drop_color_powerup and random.random() < AlienSettings.DROP_CHANCE[alien.color]:
                self.spawn_powerup(alien.rect.center, alien.color)
