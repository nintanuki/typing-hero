import pygame
import random
import math
import os
from settings import *

class Laser(pygame.sprite.Sprite):
    """Represents a laser shot by either the player or an alien. Handles movement, animation, and self-destruction when off-screen."""
    def __init__(self, pos, speed, colors, width, should_grow=False, is_piercing=False):
        """
        Initializes the laser with position, speed, colors for flickering, width, and growth behavior (for beams).

        Args:
            pos (tuple): The initial (x, y) position of the laser.
            speed (int): The vertical speed of the laser (negative for player lasers, positive for alien lasers).
            colors (tuple): A pair of colors to alternate between for flickering effect.
            width (int): The width of the laser beam.
            should_grow (bool): If True, the laser will start thin and grow to the target width (used for beams).
            is_piercing (bool): If True, the laser will pierce through enemies.
        """
        super().__init__()
        self.colors = colors
        self.color_index = 0
        self.hue = 0  # Start at red in the HSV spectrum

        self.is_piercing = is_piercing

        # Beam Growth Logic
        self.target_width = width
        self.current_width = 1 if should_grow else width# Start as a thin line

        self.image = pygame.Surface((self.current_width, LaserSettings.HEIGHT))
        
        if self.colors == "rainbow":
            # Start with white as a default color so it doesn't crash before update() runs
            self.image.fill((255, 255, 255)) 
        else:
            self.image.fill(self.colors[self.color_index])

        self.rect = self.image.get_rect(center = pos)
        self.pos_y = float(self.rect.y)
        self.speed = speed
        self.should_grow = should_grow

    def move(self, speed_multiplier=1.0):
        """Moves the laser vertically based on its speed. Called every frame in update()."""
        self.pos_y += self.speed * speed_multiplier
        self.rect.y = round(self.pos_y)

    def rebuild_surface(self):
        """
        Rebuilds the laser's surface when its width changes (used for beams).
        Called during update() when should_grow is True.
        """
        old_center = self.rect.center
        self.image = pygame.Surface((self.current_width, LaserSettings.HEIGHT))
        self.rect = self.image.get_rect(center = old_center)
        self.pos_y = float(self.rect.y)

    def animate_rainbow(self):
        """
        Handles the rainbow animation for beam lasers by updating the hue and filling the laser surface with segmented colors.
        Called every frame in update() when the laser is a beam.
        """
        self.hue = (self.hue + LaserSettings.RAINBOW_HUE_STEP) % 360
        
        # To create a flowing rainbow effect, we divide the beam into segments and assign
        # a slightly different hue to each segment based on its position and the current hue value.
        # This creates the illusion of colors moving along the beam as it grows.
        for segment_index in range(LaserSettings.RAINBOW_SEGMENTS):
            # Offset the hue for each segment based on its position
            # Adding 'i * 20' creates the color shift along the beam
            seg_hue = (self.hue + (segment_index * LaserSettings.RAINBOW_SEGMENT_SHIFT)) % 360
            
            color = pygame.Color(0)
            color.hsva = (seg_hue, 100, 100, 100)
            
            # Draw the segment onto the image
            segment_rect = pygame.Rect(
                0,
                segment_index * LaserSettings.SEGMENT_HEIGHT,
                self.current_width,
                LaserSettings.SEGMENT_HEIGHT
                )
            self.image.fill(color, segment_rect)

    def animate_flicker(self):
        """
        Handles the flickering animation by alternating between two colors.
        Called every frame in update() for non-beam lasers.
        """
        self.color_index = 1 - self.color_index # Toggles between 0 and 1 every frame
        self.image.fill(self.colors[self.color_index])

    def update_color(self):
        """Updates the laser's color based on whether it's a beam (rainbow animation)
        or a standard laser (flicker animation).
        Called every frame in update()."""
        
        # Color  Logic for Beam
        if self.colors == "rainbow":
            self.animate_rainbow()
        else:
            # Standard flickering for non-beam lasers
            self.animate_flicker()

    def update_size(self):
        """
        Handles the growth of beam lasers by increasing their width until they reach the target width.
        Called every frame in update() when should_grow is True.
        """

        # Rapidly grow width of beam until target is reached
        # Only grow if the flag is set and we haven't hit the target yet
        if self.should_grow and self.current_width < self.target_width:
            self.current_width = min(self.target_width, self.current_width + LaserSettings.RAINBOW_BEAM_GROWTH_SPEED)
            # Re-create the surface and re-center the rect
            self.rebuild_surface()

    def destroy_if_offscreen(self):
        """Destroys the laser if it goes off the top or bottom of the screen. Called every frame in update()."""
        if self.rect.bottom < 0 or self.rect.top > ScreenSettings.HEIGHT:
            self.kill()

    def update(self, speed_multiplier=1.0):
        """
        Handles laser movement, growth (for beams),
        color flickering, and self-destruction when off-screen.
        Called every frame.
        """
        self.move(speed_multiplier)
        self.update_size()
        self.update_color()
        self.destroy_if_offscreen()

class BombProjectile(pygame.sprite.Sprite):
    """Represents a launched bomb that travels upward and can be detonated."""

    def __init__(self, pos):
        """Initialize bomb projectile sprite state.

        Args:
            pos (tuple[int, int]): Spawn position, typically at the player's ship nose.
        """
        super().__init__()
        size = BombSettings.PROJECTILE_RADIUS * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.pos_y = float(self.rect.y)
        self.speed = BombSettings.PROJECTILE_SPEED
        self.flash_timer = 0
        self.base_color = BombSettings.PROJECTILE_BASE_COLOR
        self.flash_color = BombSettings.PROJECTILE_FLASH_COLOR
        self.current_color = self.base_color
        self.outline_color = BombSettings.PROJECTILE_OUTLINE_COLOR
        self._redraw()

    def _redraw(self):
        """Rebuild the projectile surface with the current flash color."""
        self.image.fill((0, 0, 0, 0))
        radius = BombSettings.PROJECTILE_RADIUS
        center = (radius, radius)
        hex_points = []
        for i in range(6):
            angle = math.radians((i * 60) - 30)
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            hex_points.append((round(x), round(y)))

        pygame.draw.polygon(self.image, self.current_color, hex_points)
        pygame.draw.polygon(self.image, self.outline_color, hex_points, BombSettings.PROJECTILE_OUTLINE_WIDTH)

    def move(self, speed_multiplier=1.0):
        """Advance projectile upward with frame-scaled world speed.

        Args:
            speed_multiplier (float): World-speed scalar from boost/brake state.
        """
        self.pos_y += self.speed * speed_multiplier
        self.rect.y = round(self.pos_y)

    def animate(self):
        """Toggle bomb color at fixed intervals to create a flashing warning effect."""
        current_time = pygame.time.get_ticks()
        if current_time - self.flash_timer >= BombSettings.FLASH_SPEED:
            self.flash_timer = current_time
            if self.current_color == self.base_color:
                self.current_color = self.flash_color
            else:
                self.current_color = self.base_color
            self._redraw()

    def destroy_if_offscreen(self):
        """Remove projectile once it leaves the top edge of the screen."""
        if self.rect.bottom < 0:
            self.kill()

    def update(self, speed_multiplier=1.0):
        """Run bomb projectile movement, flash animation, and cleanup.

        Args:
            speed_multiplier (float): World-speed scalar from boost/brake state.
        """
        self.move(speed_multiplier)
        self.animate()
        self.destroy_if_offscreen()

class BombBlast(pygame.sprite.Sprite):
    """Represents the expanding area-of-effect ring created by a bomb detonation."""

    def __init__(self, center):
        """Initialize a blast pulse at the detonation center.

        Args:
            center (tuple[int, int]): Screen-space center position of detonation.
        """
        super().__init__()
        self.center = center
        self.radius = BombSettings.BLAST_START_RADIUS
        self.max_radius = BombSettings.BLAST_MAX_RADIUS
        self.hit_aliens = set()
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self._redraw()

    def _redraw(self):
        """Rebuild blast surface to match the current radius."""
        diameter = max(2, self.radius * 2)
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (diameter // 2, diameter // 2)
        fill_rgb = BombSettings.BLAST_FILL_COLOR
        pygame.draw.circle(self.image, (*fill_rgb, BombSettings.BLAST_ALPHA), center, self.radius)
        pygame.draw.circle(
            self.image,
            (*fill_rgb, BombSettings.BLAST_RING_ALPHA),
            center,
            self.radius,
            BombSettings.BLAST_RING_WIDTH,
        )
        self.rect = self.image.get_rect(center=self.center)

    def update(self):
        """Expand the blast radius each frame and destroy once max size is reached."""
        self.radius += BombSettings.BLAST_GROWTH
        if self.radius >= self.max_radius:
            self.kill()
            return
        self._redraw()

class Player(pygame.sprite.Sprite):
    """
    Represents the player's ship. Handles movement, shooting, powerup effects,
    damage flashing, and constraints within the screen.
    """
    def __init__(self,pos,audio):
        """
        Initializes the player with position,
        audio for sound effects,
        and sets up all necessary attributes
        for movement, shooting, powerups, and damage effects.

        Args:
            pos (tuple): The initial (x, y) position of the player ship.
            audio (AudioManager): An instance of the AudioManager class to handle sound effects.
        """
        super().__init__()
        # Store original image to revert back after flashing
        self.original_image = pygame.image.load(AssetPaths.PLAYER).convert_alpha()
        self.original_image = pygame.transform.rotozoom(self.original_image, 0, PlayerSettings.SCALE)
        self.image = self.original_image.copy()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center = (pos)) # make pos = 400,500?

        # Damage Flash Logic
        self.is_flashing = False
        self.flash_timer = 0
        self.last_flash_time = 0
        self.is_red = False

        self.ready = True
        self.shoot_button_held = False
        
        self.laser_time = 0
        self.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN

        # Powerup States
        self.laser_level = 1 # Tier 1 start
        self.rapid_fire_level = 0 # 0 = normal, 1 = rapid, 2 = turbo, 3 = auto
        self.rainbow_beam_active = False
        self.rainbow_beam_start_time = 0
        self.shield_active = False
        self.shield_start_time = 0
        self.bombs = BombSettings.START_COUNT
        self.bomb_projectiles = pygame.sprite.Group()

        self.lasers = pygame.sprite.Group()

        self.audio = audio

        # Confusion state for when hit by blue alien attack
        self.confused = False
        self.confusion_timer = 0

        # Boost meter state
        self.boost_meter = 1.0
        self.boost_active = False
        self.brake_active = False
        self.boost_locked_until_full = False
        self.world_speed_multiplier = 1.0

    def launch_bomb(self):
        """Launch a bomb if inventory is available and no bomb is currently airborne.

        Returns:
            bool: True when a bomb was launched; otherwise False.
        """
        if self.bombs <= 0:
            return False
        if self.bomb_projectiles:
            return False

        self.bomb_projectiles.add(BombProjectile(self.rect.midtop))
        self.bombs -= 1
        return True

    def detonate_air_bomb(self):
        """Detonate the active in-flight bomb, if present.

        Returns:
            tuple[int, int] | None: Detonation center when a bomb is active;
                otherwise None.
        """
        if not self.bomb_projectiles:
            return None

        bomb = self.bomb_projectiles.sprites()[0]
        detonation_center = bomb.rect.center
        bomb.kill()
        return detonation_center

    def update_meter_state(self, boost_pressed, brake_pressed):
        """Update boost/brake state machine and shared energy meter.

        Args:
            boost_pressed (bool): Whether boost input is currently held.
            brake_pressed (bool): Whether brake input is currently held.
        """
        dt = 1 / ScreenSettings.FPS

        # While depleted, prevent using boost or brake until the meter fully refills.
        if self.boost_locked_until_full:
            self.boost_active = False
            self.brake_active = False
        elif boost_pressed and self.boost_meter > 0:
            self.boost_active = True
            self.brake_active = False
        elif brake_pressed and self.boost_meter > 0:
            self.boost_active = False
            self.brake_active = True
        else:
            self.boost_active = False
            self.brake_active = False

        if self.boost_active or self.brake_active:
            self.boost_meter -= PlayerSettings.BOOST_DRAIN_PER_SECOND * dt
            if self.boost_meter <= 0:
                self.boost_meter = 0
                self.boost_active = False
                self.brake_active = False
                self.boost_locked_until_full = True
        else:
            self.boost_meter += PlayerSettings.BOOST_RECHARGE_PER_SECOND * dt
            if self.boost_meter >= 1:
                self.boost_meter = 1
                self.boost_locked_until_full = False

    def get_boost_meter(self):
        """Return current boost meter ratio and semantic state for HUD rendering.

        Returns:
            tuple[float, str]: Meter ratio in [0, 1] and one of boost/brake/cooldown/ready.
        """
        if self.boost_active:
            return self.boost_meter, 'boost'

        if self.brake_active:
            return self.boost_meter, 'brake'

        if self.boost_locked_until_full:
            return self.boost_meter, 'cooldown'

        return self.boost_meter, 'ready'

    def get_world_speed_multiplier(self):
        """Return current world-speed scalar used by non-player entities.

        Returns:
            float: Brake multiplier while braking, otherwise 1.0.
        """
        if self.brake_active:
            return PlayerSettings.BRAKE_WORLD_SPEED_MULT
        return 1.0

    def trigger_damage_effect(self):
        """Called when the player takes damage"""
        self.is_flashing = True
        self.flash_timer = pygame.time.get_ticks()

        # Reset all powerups upon taking damage
        self.laser_level = 1 # Reset to Tier 1
        self.rapid_fire_level = 0
        self.rainbow_beam_active = False
        self.shield_active = False
        self.update_laser_cooldown()

    def update_laser_cooldown(self):
        """Sets the active cooldown from the current powerup state."""
        self.rapid_fire_level = max(0, min(3, self.rapid_fire_level))

        if self.rainbow_beam_active:
            self.laser_cooldown = 0
        elif self.rapid_fire_level == 3:
            self.laser_cooldown = PlayerSettings.RAPID_FIRE_TIER_2_COOLDOWN
        elif self.rapid_fire_level == 2:
            self.laser_cooldown = PlayerSettings.RAPID_FIRE_TIER_2_COOLDOWN
        elif self.rapid_fire_level == 1:
            self.laser_cooldown = PlayerSettings.RAPID_FIRE_TIER_1_COOLDOWN
        else:
            self.laser_cooldown = PlayerSettings.DEFAULT_LASER_COOLDOWN

    def is_invulnerable(self):
        """Check whether damage should currently be ignored for the player.

        Returns:
            bool: True when flashing, shielded, or rainbow-beam invulnerable.
        """
        return self.is_flashing or self.rainbow_beam_active or self.shield_active

    def animate_damage(self):
        """Toggles the ship color between original and red tint"""
        if self.is_flashing:
            current_time = pygame.time.get_ticks()
            
            # Check if total duration has passed
            if current_time - self.flash_timer >= PlayerSettings.FLASH_DURATION:
                self.is_flashing = False
                self.image = self.original_image.copy() # Reset to normal
                return

            # Toggle flash state based on interval
            if current_time - self.last_flash_time >= PlayerSettings.FLASH_INTERVAL:
                self.last_flash_time = current_time
                self.is_red = not self.is_red

                if self.is_red:
                    # Create a red version of the ship
                    red_surf = self.original_image.copy()
                    # BLIT_RGBA_MULT multiplies the image by the color (R, G, B, A)
                    # This keeps the transparency but turns the pixels red
                    red_surf.fill((255, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
                    self.image = red_surf
                else:
                    self.image = self.original_image.copy()

    def get_input(self):
        """Handles player input for movement and shooting. Called every frame in update()"""
        keys = pygame.key.get_pressed() # Get keyboard state once to avoid multiple calls per frame
        base_speed = PlayerSettings.SPEED # Base speed before any boosts or brakes
        direction = -1 if self.confused else 1  # Confusion inverts all movement

        # --- Collect all controller state in a single pass ---
        # Rather than looping over joysticks multiple times, we gather everything here.
        left_boost_held = right_boost_held = forward_boost_held = False
        brake_held = shoot_held = False
        joystick_x = joystick_y = 0.0

        # We loop through all connected joysticks and check the relevant buttons and axes.
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            left_boost_held    |= joy.get_button(ControllerSettings.L1_BUTTON)
            right_boost_held   |= joy.get_button(ControllerSettings.R1_BUTTON)
            forward_boost_held |= joy.get_button(ControllerSettings.Y_BUTTON)
            brake_held         |= joy.get_button(ControllerSettings.X_BUTTON)
            shoot_held         |= joy.get_button(ControllerSettings.A_BUTTON)
            x, y = joy.get_axis(ControllerSettings.LEFT_STICK_X), joy.get_axis(ControllerSettings.LEFT_STICK_Y)
            if abs(x) > PlayerSettings.JOYSTICK_DEADZONE: joystick_x = x
            if abs(y) > PlayerSettings.JOYSTICK_DEADZONE: joystick_y = y

        # --- Update the boost/brake meter based on what's being held ---
        keyboard_boost_held = keys[pygame.K_f]

        # Check if the player is actually moving in a boostable direction.
        # Boost should only drain the meter if it's doing something useful.
        moving_left    = keys[pygame.K_a] or keys[pygame.K_LEFT]  or joystick_x < -PlayerSettings.JOYSTICK_DEADZONE
        moving_right   = keys[pygame.K_d] or keys[pygame.K_RIGHT] or joystick_x >  PlayerSettings.JOYSTICK_DEADZONE
        moving_forward = keys[pygame.K_w] or keys[pygame.K_UP]    or joystick_y < -PlayerSettings.JOYSTICK_DEADZONE

        # Boost only counts if a boost button matches the direction being moved
        left_boost_active    = left_boost_held    and moving_left
        right_boost_active   = right_boost_held   and moving_right
        forward_boost_active = forward_boost_held and moving_forward
        keyboard_boost_active = keyboard_boost_held and (moving_left or moving_right or moving_forward)

        any_boost_held = left_boost_active or right_boost_active or forward_boost_active or keyboard_boost_active
        self.update_meter_state(any_boost_held, keys[pygame.K_g] or brake_held)
        self.world_speed_multiplier = self.get_world_speed_multiplier()

        # Boost only applies if the meter has charge and the system is active
        boost_available = self.boost_active and self.boost_meter > 0

        # --- Helper: returns boosted or base speed depending on whether the condition is met ---
        def boosted_speed(boost_condition):
            if boost_available and boost_condition:
                return base_speed * PlayerSettings.SPEED_BOOST
            return base_speed

        # --- Keyboard movement (WASD / Arrow Keys) ---
        # Vertical movement has no boost, so we always use base_speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.rect.y -= boosted_speed(forward_boost_held or keyboard_boost_held) * direction
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.rect.y += base_speed * direction

        # Horizontal movement can be boosted per-direction via L1/R1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= boosted_speed(left_boost_held or keyboard_boost_held) * direction
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += boosted_speed(right_boost_held or keyboard_boost_held) * direction

        # --- Controller left stick movement ---
        # Boost applies to horizontal left/right based on stick direction + button held
        if joystick_x:
            moving_left  = joystick_x < 0 and left_boost_held
            moving_right = joystick_x > 0 and right_boost_held
            self.rect.x += joystick_x * boosted_speed(moving_left or moving_right) * direction

        # Boost applies to forward (upward) stick movement via Y button
        if joystick_y:
            moving_forward = forward_boost_held and joystick_y < 0
            self.rect.y += joystick_y * boosted_speed(moving_forward) * direction

        # --- Shooting ---
        # Space bar or controller A button both trigger shooting
        shoot_pressed = keys[pygame.K_SPACE] or shoot_held

        # Rainbow beam fires automatically via handle_auto_shooting(), so we just
        # track the button state here and skip manual fire logic entirely
        if self.rainbow_beam_active:
            self.shoot_button_held = shoot_pressed
            return

        # Auto fire (rapid_fire level 3) allows holding the button
        if self.rapid_fire_level == 3:
            if shoot_pressed and self.ready:
                self.trigger_shot()
        # All other modes require a fresh press (no holding)
        else:
            if shoot_pressed and not self.shoot_button_held and self.ready:
                self.trigger_shot()

        self.shoot_button_held = shoot_pressed

    def recharge(self):
        """Recharges the player's laser based on cooldown. Called every frame in update()"""
        if not self.ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_time >= self.laser_cooldown:
                self.ready = True

    def constraint(self):
        """Constrains the player within the screen. Called every frame in update()"""
        if self.rect.left <= 0:
            self.rect.left = 0
        if self.rect.right >= ScreenSettings.WIDTH:
            self.rect.right = ScreenSettings.WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= ScreenSettings.HEIGHT:
            self.rect.bottom = ScreenSettings.HEIGHT

    def shoot_laser(self):
        """Spawns lasers based on current powerup state. Handles twin lasers, rapid fire, and beam logic."""
        is_rainbow_beam = self.rainbow_beam_active
        is_hyper = (self.laser_level == 4)
        is_piercing = self.laser_level >= 3
        has_rapid = self.rapid_fire_level > 0
        laser_speed = LaserSettings.PLAYER_LASER_SPEED * 2 if is_hyper else LaserSettings.PLAYER_LASER_SPEED
        
        # 1. Determine the behavior and growth of the rainbow beam
        width = LaserSettings.RAINBOW_BEAM_WIDTH if is_rainbow_beam else LaserSettings.DEFAULT_WIDTH
        offset = 20 if is_rainbow_beam else 12

        # 2. Assign colors based on priority
        if self.rainbow_beam_active:
            colors = "rainbow"
        elif has_rapid and is_piercing:
            colors = LaserSettings.COLORS['hyper_rapid']
        elif has_rapid:
            colors = LaserSettings.COLORS['rapid']
        elif is_hyper:
            colors = LaserSettings.COLORS['hyper']
        elif self.laser_level == 3:
            colors = LaserSettings.COLORS['burst']
        elif self.laser_level >= 2:
            colors = LaserSettings.COLORS['twin']
        else:
            colors = LaserSettings.COLORS['single']

        # 3. Spawn the lasers
        if self.laser_level >= 2:
            # Left laser
            self.lasers.add(Laser((self.rect.centerx - offset, self.rect.centery), 
                                laser_speed, colors, width, 
                                should_grow=is_rainbow_beam, is_piercing=is_piercing))
            # Right laser
            self.lasers.add(Laser((self.rect.centerx + offset, self.rect.centery), 
                                laser_speed, colors, width, 
                                should_grow=is_rainbow_beam, is_piercing=is_piercing))
        else:
            # Level 1: Single laser
            self.lasers.add(Laser(self.rect.center, laser_speed, 
                                colors, width, should_grow=is_rainbow_beam, is_piercing=is_piercing))
            
        
        if self.laser_level >= 3 or self.rainbow_beam_active:
            self.audio.play('hyper')
        else:
            self.audio.play('laser')

    def activate_powerup(self, powerup):
        """
        Activates the given powerup's effect on the player. Called when player collects a powerup.

        Args:
            powerup (PowerUp): The powerup object that was collected, which contains information about the type and any cooldown bonuses.
        """
        current_time = pygame.time.get_ticks()

        if powerup.powerup_type == 'laser_upgrade':
            if self.laser_level < 4:
                self.laser_level += 1
                
        elif powerup.powerup_type == 'rapid_fire':
            # Only activate rapid fire if the rainbow beam isn't already active
            if not self.rainbow_beam_active:
                if self.rapid_fire_level < 3:
                    self.rapid_fire_level += 1
                self.update_laser_cooldown()

        elif powerup.powerup_type == 'shield':
            self.shield_active = True
            self.shield_start_time = current_time
            
        elif powerup.powerup_type == 'rainbow_beam':
            self.rainbow_beam_active = True
            self.rainbow_beam_start_time = current_time
            self.update_laser_cooldown()
        elif powerup.powerup_type == 'bomb':
            self.bombs += 1

    def check_powerup_timeout(self):
        """Checks if any time-limited powerups have expired and deactivates them. Called every frame in update()"""
        current_time = pygame.time.get_ticks()

        if self.rainbow_beam_active:
            if current_time - self.rainbow_beam_start_time >= PlayerSettings.RAINBOW_BEAM_DURATION:
                self.rainbow_beam_active = False
                self.update_laser_cooldown()

        if self.shield_active:
            if current_time - self.shield_start_time >= PlayerSettings.SHIELD_DURATION:
                self.shield_active = False

    def trigger_shot(self):
        """Helper to handle the act of shooting"""
        self.shoot_laser()
        self.ready = False
        self.laser_time = pygame.time.get_ticks()

    def handle_auto_shooting(self):
        """
        Handles automatic shooting for powerups that require it (like rapid fire and beam).
        Called every frame in update().
        """
        if self.rainbow_beam_active and self.ready:
            self.trigger_shot()

    def draw_shield_orb(self, screen):
        """Draw a pulsing shield orb around the player's ship while shield is active.

        Args:
            screen (pygame.Surface): Destination surface for shield rendering.
        """
        if not self.shield_active:
            return

        current_time = pygame.time.get_ticks()
        time_left = PlayerSettings.SHIELD_DURATION - (current_time - self.shield_start_time)
        # If shield is in last 1 second, flash rapidly
        if time_left <= 1000:
            pulse = (current_time // 50) % 2  # Faster flash
        else:
            pulse = (current_time // 100) % 2
        alpha = 150 if pulse == 0 else 70
        radius = max(self.rect.width, self.rect.height) // 2 + 12

        orb_size = radius * 2 + 6
        orb = pygame.Surface((orb_size, orb_size), pygame.SRCALPHA)
        center = (orb_size // 2, orb_size // 2)

        pygame.draw.circle(orb, (80, 255, 255, alpha), center, radius, 3)
        pygame.draw.circle(orb, (120, 255, 255, alpha // 2), center, radius - 4, 2)

        orb_rect = orb.get_rect(center=self.rect.center)
        screen.blit(orb, orb_rect)

    def update_lasers(self):
        """Updates all lasers fired by the player. Called every frame in update()"""
        self.lasers.update(self.world_speed_multiplier)

    def update_bombs(self):
        """Updates any active in-flight bomb."""
        self.bomb_projectiles.update(self.world_speed_multiplier)
    
    def update(self):
        """Handles player input for movement and shooting,
        applies constraints, manages powerup effects and durations,
        animates damage flashing, and updates lasers.
        Called every frame."""
        self.get_input()
        self.handle_auto_shooting()
        self.constraint()
        self.recharge()
        self.check_powerup_timeout()
        self.animate_damage()
        self.update_lasers()
        self.update_bombs()

        if self.confused:
            if pygame.time.get_ticks() - self.confusion_timer >= PlayerSettings.CONFUSION_TIMEOUT:
                self.confused = False
                self.image = self.original_image # Reset to original colors
            else:
                # Tint the ship by multiplying its pixels with the configured
                # purple/magenta. BLEND_RGBA_MULT preserves alpha so the
                # silhouette stays correct.
                tinted_surf = self.original_image.copy()
                tinted_surf.fill(AlienSettings.CONFUSION_PLAYER_TINT, special_flags=pygame.BLEND_RGBA_MULT)
                self.image = tinted_surf

class Alien(pygame.sprite.Sprite):
    """Represents an alien enemy. Handles movement patterns, zigzag behavior for certain types, and self-destruction when off-screen."""
    def __init__(self,color,screen_width,screen_height):
        """Initializes the alien with a color
        (which determines its behavior and points),
        screen dimensions for spawning and movement constraints,
        and sets up its sprite and movement attributes.
        
        Args:
            color (str): The color/type of the alien, which affects its speed, points, and behavior.
            screen_width (int): The width of the game screen, used for spawning and movement constraints
            screen_height (int): The height of the game screen, used for spawning and movement constraints
        """
        super().__init__()
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 1. Load the frames
        self.frames = []
        path1 = os.path.join(AssetPaths.GRAPHICS_DIR, f'{self.color}1.png')
        path2 = os.path.join(AssetPaths.GRAPHICS_DIR, f'{self.color}2.png')

        # Load frame 1
        self.frames.append(pygame.image.load(path1).convert_alpha())

        # Load frame 2 (if not blue)
        if color in ['red', 'green', 'yellow']:
            try:
                self.frames.append(pygame.image.load(path2).convert_alpha())
            except pygame.error:
                # Fallback if the file is missing
                self.frames.append(self.frames[0])

        self.frame_index = 0
        self.image = self.frames[self.frame_index]

        # Position setup
        x_pos  = random.randint(20,self.screen_width - 20)
        self.rect = self.image.get_rect(center = (x_pos,random.randint(*AlienSettings.SPAWN_OFFSET)))
        self.position = pygame.math.Vector2(self.rect.topleft)

        # Movement logic
        # Yellow aliens zigzag
        self.yellow_zigzag_direction = random.choice([-1,1]) # 1 for right, -1 for left
        self.yellow_zigzag_counter = 0 
        # Blue aliens zigzag
        self.blue_zigzag_direction = random.choice([-1,1]) # 1 for right, -1 for left

        # Point value based on color
        self.value = AlienSettings.POINTS.get(color, 0)

        # Confusion attack attributes (for blue aliens)
        self.is_confusing = False
        self.confusion_start_time = 0
        self.has_projected = False
        # Only blue aliens have a chance to cause confusion
        self.can_confuse = (color == 'blue' and random.random() < AlienSettings.CONFUSION_CHANCE)

        self.confusion_growth = 0  # Starts at 0, will increase to ScreenSettings.HEIGHT
        # Cache for the per-frame beam surface so draw and collision can both
        # consume the exact same pixels without rebuilding (or double-stepping
        # confusion_growth).
        self.confusion_beam_surf = None

    def apply_movement(self, delta_x, delta_y):
        """Apply sub-pixel deltas and keep rect coordinates synchronized.

        Args:
            delta_x (float): Horizontal movement delta in pixels.
            delta_y (float): Vertical movement delta in pixels.
        """
        self.position.x += delta_x
        self.position.y += delta_y
        self.rect.x = round(self.position.x)
        self.rect.y = round(self.position.y)

    def calculate_movement(self, speed_multiplier=1.0):
        """
        Calculates the movement of the alien based on its color and behavior patterns.

        Args:
            speed_multiplier (float): World-speed scalar applied to alien motion.
        """
        # Check for confusion attack trigger (only for blue aliens with the ability)
        if self.can_confuse and not self.has_projected:
            if self.rect.centery >= AlienSettings.CONFUSION_STOP_Y:
                self.is_confusing = True
                self.has_projected = True
                self.confusion_start_time = pygame.time.get_ticks()

        if self.is_confusing:
            # Check if the projection time is over
            if pygame.time.get_ticks() - self.confusion_start_time >= AlienSettings.CONFUSION_DURATION:
                self.is_confusing = False
            return # Stop moving while confusing the player
        
        # numbers round down if decimals are used? .05 doesn't move and 1 is the same as 1.5, etc
        if self.color == 'red':
            self.apply_movement(0, AlienSettings.SPEED['red'] * speed_multiplier)
        elif self.color == 'green':
            self.apply_movement(0, AlienSettings.SPEED['green'] * speed_multiplier)
        elif self.color == 'yellow':
            self.apply_movement(self.yellow_zigzag_direction * 2 * speed_multiplier, AlienSettings.SPEED['yellow'] * speed_multiplier)
            self.yellow_zigzag_counter += 1
            if self.yellow_zigzag_counter >= AlienSettings.ZIGZAG_THRESHOLD:
                self.yellow_zigzag_counter = 0
                self.yellow_zigzag_direction *= -1
            if self.rect.left < 0 or self.rect.right > self.screen_width:
                self.yellow_zigzag_direction *= -1
        else: # color is blue
            self.apply_movement(self.blue_zigzag_direction * 2 * speed_multiplier, AlienSettings.SPEED['blue'] * speed_multiplier)
            if self.rect.left < 0 or self.rect.right > self.screen_width:
                self.blue_zigzag_direction *= -1

    def animate(self):
        """Cycles through the frames"""
        if len(self.frames) > 1:
            self.frame_index += AlienSettings.ANIMATION_SPEED
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]

    def update_confusion_beam(self):
        """Grow this frame's confusion beam and cache the resulting surface.

        Called once per frame from update(); both rendering and collision
        read the same cached surface to keep growth advancing exactly once
        per frame. The cached surface is None when the alien is not
        currently projecting the beam.
        """
        if not self.is_confusing:
            self.confusion_beam_surf = None
            return

        # Grow the beam toward the bottom of the screen, capped to screen
        # height so it cannot extend forever.
        if self.confusion_growth < ScreenSettings.HEIGHT:
            self.confusion_growth += AlienSettings.CONFUSION_BEAM_GROWTH_PER_FRAME

        # Trapezoid: narrow at the alien's belly, fans out by a fraction of
        # the current beam length so longer beams look more menacing.
        top_width = AlienSettings.CONFUSION_BEAM_TOP_WIDTH
        bottom_width = top_width + (self.confusion_growth * AlienSettings.CONFUSION_BEAM_WIDEN_RATIO)

        beam_polygon = [
            (self.rect.centerx - top_width // 2, self.rect.bottom),
            (self.rect.centerx + top_width // 2, self.rect.bottom),
            (self.rect.centerx + bottom_width // 2, self.rect.bottom + self.confusion_growth),
            (self.rect.centerx - bottom_width // 2, self.rect.bottom + self.confusion_growth),
        ]

        field_surf = pygame.Surface((ScreenSettings.WIDTH, ScreenSettings.HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(field_surf, AlienSettings.CONFUSION_BEAM_COLOR, beam_polygon)
        self.confusion_beam_surf = field_surf

    def draw_confusion_beam(self, screen):
        """Blit this frame's cached confusion-beam surface onto ``screen``.

        Args:
            screen (pygame.Surface): Destination surface for the beam blit.
        """
        if self.confusion_beam_surf is not None:
            screen.blit(self.confusion_beam_surf, (0, 0))

    def get_confusion_beam_mask(self):
        """Return a pixel-perfect mask of this frame's confusion beam, or None.

        Used by ``CollisionManager`` to detect player overlap with the beam.

        Returns:
            pygame.mask.Mask | None: Beam mask anchored at screen origin, or None.
        """
        if self.confusion_beam_surf is None:
            return None
        return pygame.mask.from_surface(self.confusion_beam_surf, threshold=1)

    def destroy(self):
        """Destroys the alien once it falls past the configured bottom margin."""
        if self.rect.y >= self.screen_height + AlienSettings.OFFSCREEN_MARGIN:
            self.kill()

    def update(self, speed_multiplier=1.0):
        """Update alien behavior for one frame.

        Args:
            speed_multiplier (float): World-speed scalar applied to movement.
        """
        self.calculate_movement(speed_multiplier)
        self.animate()
        self.update_confusion_beam()
        self.destroy()

class PowerUp(pygame.sprite.Sprite):
    """Represents a powerup that the player can collect. Handles movement, animation (flashing), and self-destruction when off-screen."""
    def __init__(self, pos, color):
        """Initializes the powerup with a position and color (which determines its type and appearance),
        and sets up attributes for movement, flashing animation, and self-destruction.
        
        Args:
            pos (tuple): The initial (x, y) position of the powerup when it spawns.
            color (str): The color/type of the powerup, which determines its effect on the player and its appearance.
        """
        super().__init__()
        self.shape = PowerupSettings.DATA[color].get('shape', 'circle')

        self.draw_color = PowerupSettings.DATA[color]['draw_color']
        self.powerup_type = PowerupSettings.DATA[color]['type']
        self.cooldown_bonus = PowerupSettings.DATA[color].get('cooldown', None)

        self.flash_color = (255, 255, 255)
        self.current_color = self.draw_color

        if self.shape == 'heart':
            self.image = pygame.image.load(AssetPaths.HEART).convert_alpha()
            self.image = pygame.transform.scale(self.image, UISettings.HEART_SPRITE_SIZE)
            self.rect = self.image.get_rect(center=pos)
        else:
            self.image = pygame.Surface((PowerupSettings.RADIUS * 2, PowerupSettings.RADIUS * 2), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=pos)

        self.flash_timer = 0
        self.flash_speed = PowerupSettings.FLASH_SPEED

    def move(self):
        """Moves the powerup downward based on its speed. Called every frame in update()."""
        self.rect.y += PowerupSettings.SPEED

    def animate(self):
        """
        Handles the flashing animation of the powerup by toggling its color between the base color and white at a set interval.
        Called every frame in update().
        """
        if self.shape == 'heart':
            return  # skip animation, keep sprite static

        current_time = pygame.time.get_ticks()

        if self.powerup_type == 'rainbow_beam':
            hue = (current_time // PowerupSettings.RAINBOW_STAR_HUE_DIVISOR) % 360
            rainbow_color = pygame.Color(0)
            rainbow_color.hsva = (hue, 100, 100, 100)
            self.current_color = rainbow_color
        elif current_time - self.flash_timer >= self.flash_speed:
            self.flash_timer = current_time

            # toggle between the orb's color and white
            if self.current_color == self.draw_color:
                self.current_color = self.flash_color
            else:
                self.current_color = self.draw_color

        # Clear and redraw the shape every frame.
        self.image.fill((0, 0, 0, 0))

        if self.shape == 'star':
            center = (PowerupSettings.RADIUS, PowerupSettings.RADIUS)
            outer_radius = PowerupSettings.RADIUS
            inner_radius = max(4, int(outer_radius * 0.45))
            points = []

            # Build a 5-point star with alternating outer/inner vertices.
            for i in range(10):
                angle = math.radians((i * 36) - 90)
                radius = outer_radius if i % 2 == 0 else inner_radius
                x = center[0] + int(math.cos(angle) * radius)
                y = center[1] + int(math.sin(angle) * radius)
                points.append((x, y))

            pygame.draw.polygon(self.image, self.current_color, points)
        elif self.shape == 'diamond':
            points = [
                (PowerupSettings.RADIUS, 0),                    # top
                (PowerupSettings.RADIUS * 2, PowerupSettings.RADIUS),      # right
                (PowerupSettings.RADIUS, PowerupSettings.RADIUS * 2),      # bottom
                (0, PowerupSettings.RADIUS)                     # left
            ]
            pygame.draw.polygon(self.image, self.current_color, points)
        else:
            pygame.draw.circle(
                self.image,
                self.current_color,
                (PowerupSettings.RADIUS, PowerupSettings.RADIUS),
                PowerupSettings.RADIUS
            )

    def destroy(self):
        """Destroys the powerup if it moves off the bottom of the screen. Called every frame in update()."""
        if self.rect.top > ScreenSettings.HEIGHT:
            self.kill()

    def update(self):
        """
        Handles the downward movement of the powerup,
        its flashing animation, and checks for self-destruction when off-screen.
        Called every frame in the game loop.
        """
        self.move()
        self.animate()
        self.destroy()
