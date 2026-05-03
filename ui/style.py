import pygame
from settings import *

class Style():
    """Render all HUD, menu, pause, and game-over UI layers for Star Hero."""

    def __init__(self, screen: pygame.Surface, audio) -> None:
        """Initialize fonts, shared screen/audio references, hearts, and title art.

        Args:
            screen (pygame.Surface): The active display surface used for all UI blits.
            audio (Audio): Audio manager instance used for reading current volume.
        """
        self.screen = screen
        self.small_font = pygame.font.Font(FontSettings.FONT,FontSettings.SMALL)
        self.medium_font = pygame.font.Font(FontSettings.FONT,FontSettings.MEDIUM)
        self.large_font = pygame.font.Font(FontSettings.FONT,FontSettings.LARGE)
        self.micro_font = pygame.font.Font(FontSettings.FONT, 6)

        self.audio = audio # Audio reference used to read and display the current volume

        # Heart icon used by the in-game HUD. Loading once here means
        # display_hearts can stay a pure rendering call with no I/O.
        self.heart_surf = pygame.image.load(AssetPaths.HEART).convert_alpha()
        heart_width = self.heart_surf.get_size()[0]
        self.heart_x_start_pos = ScreenSettings.WIDTH - (
            heart_width * PlayerSettings.MAX_HEALTH + UISettings.HEART_RIGHT_MARGIN
        )

        # Load image of ship for intro and game over screens
        self.player_ship = pygame.image.load(AssetPaths.PLAYER).convert_alpha()
        self.player_ship = pygame.transform.rotozoom(self.player_ship,0,0.2)
        self.player_ship_rect = self.player_ship.get_rect(center = (ScreenSettings.CENTER))

    def display_hearts(self, hearts: int) -> None:
        """Draw the player's remaining hearts in the top-right HUD.

        Args:
            hearts (int): Current heart count to render.
        """
        heart_width = self.heart_surf.get_size()[0]
        for heart_index in range(hearts):
            # Step right by (icon width + spacing) for each successive heart.
            x = self.heart_x_start_pos + (heart_index * (heart_width + UISettings.HEART_SPACING))
            self.screen.blit(self.heart_surf, (x, UISettings.HEART_TOP_MARGIN))

    def display_title(self):
        """Draw the game title on the intro screen."""
        title = self.large_font.render('STAR HERO', False, FontSettings.COLOR)
        title_rect = title.get_rect(center=(ScreenSettings.WIDTH / 2, 70))
        self.screen.blit(title, title_rect)

    def display_game_over(self):
        """Draw the game-over heading."""
        game_over_message = self.large_font.render('GAME OVER', False, FontSettings.COLOR)
        game_over_message_rect = game_over_message.get_rect(center=(ScreenSettings.WIDTH / 2, 70))
        self.screen.blit(game_over_message, game_over_message_rect)

    def display_player_ship(self, y_pos=None):
        """Draw the player ship image centered on intro/game-over screens.

        Args:
            y_pos (int | None): Optional y-coordinate for custom vertical placement.
                When None, the ship is drawn at full screen center.
        """
        if y_pos is None:
            rect = self.player_ship.get_rect(center=ScreenSettings.CENTER)
        else:
            rect = self.player_ship.get_rect(center=(ScreenSettings.WIDTH / 2, y_pos))
        self.screen.blit(self.player_ship, rect)

    def display_intro_message(self):
        """Draw the intro prompt instructing the player to start the game."""
        intro_message = self.medium_font.render('PRESS START TO PLAY', False, FontSettings.COLOR)
        intro_message_rect = intro_message.get_rect(center=(ScreenSettings.WIDTH / 2, ScreenSettings.HEIGHT - 70))
        self.screen.blit(intro_message, intro_message_rect)

    def display_high_score(self, save_data: dict) -> None:
        """Draw the persistent high score label.

        Args:
            save_data (dict): Save payload containing at least a high_score key.
        """
        high_score_message = self.medium_font.render(
            f'HIGH SCORE: {save_data["high_score"]}',
            False,
            FontSettings.COLOR
        )
        high_score_message_rect = high_score_message.get_rect(center=(ScreenSettings.WIDTH / 2, 520))
        self.screen.blit(high_score_message, high_score_message_rect)

    def display_in_game_score(self, save_data: dict, score: int) -> None:
        """Draw gameplay HUD score fields in the top-left corner.

        Args:
            save_data (dict): Save payload containing leaderboard and high-score data.
            score (int): Current run score.
        """
        high_score_surf = self.small_font.render(f'HIGH SCORE: {save_data["high_score"]}', False, FontSettings.COLOR)
        high_score_rect = high_score_surf.get_rect(topleft=(10, 5))
        self.screen.blit(high_score_surf, high_score_rect)

        score_surf = self.medium_font.render(f'SCORE: {score}', False, FontSettings.COLOR)
        score_rect = score_surf.get_rect(topleft=(10, 20))
        self.screen.blit(score_surf, score_rect)

    def display_game_over_score(self, score: int) -> None:
        """Draw the final run score on the game-over screen.

        Args:
            score (int): Final score earned in the just-finished run.
        """
        score_message = self.medium_font.render(f'YOUR SCORE: {score}', False, FontSettings.COLOR)
        score_message_rect = score_message.get_rect(center=(ScreenSettings.WIDTH / 2, 560))
        self.screen.blit(score_message, score_message_rect)

    def display_pause_text(self) -> None:
        """Draw the pause banner while gameplay is halted."""
        pause_text = self.medium_font.render('PAUSED', False, (FontSettings.COLOR))
        pause_text_rect = pause_text.get_rect(center = (ScreenSettings.CENTER))
        self.screen.blit(pause_text,pause_text_rect)

    def display_volume(self) -> None:
        """Draw the temporary volume HUD with both numeric value and meter bar."""

        # Volume Number
        volume_message = self.small_font.render(f'VOLUME: {round(self.audio.master_volume * 10)}',False,(FontSettings.COLOR))
        volume_message_rect = volume_message.get_rect(bottomleft = (10,ScreenSettings.HEIGHT - 20))
        self.screen.blit(volume_message,volume_message_rect)
        
        # Volume Bar
        pygame.draw.rect(self.screen,'green',(10,ScreenSettings.HEIGHT - 20,(self.audio.master_volume*1000)/UISettings.VOLUME_BAR_RATIO,10))

    def display_leaderboard(self, leaderboard: list[dict], title: str = "TOP 10", start_y: int = 300) -> None:
        """Draw a centered leaderboard block.

        Args:
            leaderboard (list[dict]): Ranked score entries with name and score fields.
            title (str): Heading label displayed above leaderboard rows.
            start_y (int): Vertical anchor where the title row starts.
        """
        screen_center_x = ScreenSettings.WIDTH // 2

        title_surf = self.small_font.render(title, False, FontSettings.COLOR)
        title_rect = title_surf.get_rect(center=(screen_center_x, start_y))
        self.screen.blit(title_surf, title_rect)

        y = start_y + 30
        for i, entry in enumerate(leaderboard, start=1):
            text = f"{i:>2}. {entry['name']}  {entry['score']}"
            surf = self.small_font.render(text, False, FontSettings.COLOR)
            rect = surf.get_rect(center=(screen_center_x, y))
            self.screen.blit(surf, rect)
            y += 22

    def display_level(self, score: int) -> None:
        """Draw the computed difficulty level in the bottom-left HUD.

        Args:
            score (int): Current score used to derive the level index.
        """
        # Level starts at 1 and increases every DIFFICULTY_STEP points (max 20)
        level = min(20, (score // AlienSettings.DIFFICULTY_STEP) + 1)
        level_surf = self.small_font.render(f'LEVEL: {level}', False, FontSettings.COLOR)
        # Keep level text clear of the temporary volume overlay.
        level_rect = level_surf.get_rect(bottomleft=(10, ScreenSettings.HEIGHT - 36))
        self.screen.blit(level_surf, level_rect)

    def _draw_bomb_icons(self, bomb_count: int, top_right: tuple[int, int], spacing: int = 4) -> None:
        """Draw bomb icons showing count up to 6; for 7+, show single icon with 'x#' label.
        
        For 1-6 bombs: display individual icons right-aligned.
        For 7+ bombs: display single icon followed by 'x#' text to the right, both centered vertically.

        Args:
            bomb_count (int): Number of bombs to represent.
            top_right (tuple[int, int]): Top-right anchor for the display.
            spacing (int): Horizontal space between elements.
        """
        icon_width = 16
        icon_height = 14

        # For 7+ bombs, show icon + x# indicator
        if bomb_count > 6:
            top_y = top_right[1]
            center_y = top_y + (icon_height // 2)
            
            # Calculate icon position (to the left of text)
            indicator_text = f'x{bomb_count}'
            indicator_surf = self.small_font.render(indicator_text, False, 'white')
            icon_x = top_right[0] - indicator_surf.get_width() - spacing - icon_width
            center_x = icon_x + (icon_width // 2)
            
            # Draw single bomb icon
            points = [
                (icon_x + 3, top_y),
                (icon_x + icon_width - 3, top_y),
                (icon_x + icon_width, center_y),
                (icon_x + icon_width - 3, top_y + icon_height),
                (icon_x + 3, top_y + icon_height),
                (icon_x, center_y),
            ]

            pygame.draw.polygon(self.screen, 'black', points)
            pygame.draw.polygon(self.screen, 'red', points, 1)

            bomb_letter = self.micro_font.render('B', False, 'white')
            bomb_rect = bomb_letter.get_rect(center=(center_x, center_y - 1))
            self.screen.blit(bomb_letter, bomb_rect)

            # Draw x# indicator, centered vertically with the icon
            indicator_rect = indicator_surf.get_rect(midright=(top_right[0], center_y))
            self.screen.blit(indicator_surf, indicator_rect)
        else:
            # Draw individual bomb icons (1-6)
            total_width = (bomb_count * icon_width) + (max(0, bomb_count - 1) * spacing)
            start_x = top_right[0] - total_width
            top_y = top_right[1]

            for index in range(bomb_count):
                left = start_x + (index * (icon_width + spacing))
                center_x = left + (icon_width // 2)
                center_y = top_y + (icon_height // 2)
                points = [
                    (left + 3, top_y),
                    (left + icon_width - 3, top_y),
                    (left + icon_width, center_y),
                    (left + icon_width - 3, top_y + icon_height),
                    (left + 3, top_y + icon_height),
                    (left, center_y),
                ]

                pygame.draw.polygon(self.screen, 'black', points)
                pygame.draw.polygon(self.screen, 'red', points, 1)

                bomb_letter = self.micro_font.render('B', False, 'white')
                bomb_rect = bomb_letter.get_rect(center=(center_x, center_y - 1))
                self.screen.blit(bomb_letter, bomb_rect)

    def display_player_status(self, player) -> None:
        """Draw right-aligned status rows for ship state, weapon mode, power, bombs, and boost meter.

        Args:
            player (Player): Active player sprite providing status and meter values.
        """
        
        # --- 1. Determine Values and Colors ---
        # Status
        if player.confused:
            status_val = "CONFUSION"
            status_color = 'magenta'
        elif player.shield_active:
            status_val = "SHIELD"
            status_color = 'cyan'
        else:
            status_val = "OKAY"
            status_color = 'white'
        
        # Laser
        if player.laser_level == 4:
            laser_val = "HYPER"
            laser_color = 'cyan'
        elif player.laser_level == 3:
            laser_val = "BURST"
            laser_color = 'cyan'
        elif player.laser_level == 2:
            laser_val = "TWIN"
            laser_color = 'green'
        else:
            laser_val = "SINGLE"
            laser_color = 'white'

        # Mode (yellow upgrades)
        if player.rapid_fire_level == 3:
            mode_val = "AUTO"
            mode_color = 'yellow'
        elif player.rapid_fire_level == 2:
            mode_val = "TURBO"
            mode_color = 'yellow'
        elif player.rapid_fire_level == 1:
            mode_val = "RAPID"
            mode_color = 'yellow'
        else:
            mode_val = "NORMAL"
            mode_color = 'white'
        
        # Power
        power_val = "NONE"
        power_color = 'white'
        if player.rainbow_beam_active:
            power_val = "RAINBOW BEAM"
            # Create rainbow effect using HSV conversion
            hue = (pygame.time.get_ticks() // 4) % 360
            power_color = pygame.Color(0)
            power_color.hsva = (hue, 100, 100, 100)

        # --- 2. Define Rows ---
        # Format: (Label, Value, Value Color)
        rows = [
            ("STATUS: ", [(status_val, status_color)]),
            ("LASER: ", [(laser_val, laser_color)]),
            ("MODE: ", [(mode_val, mode_color)]),
            ("POWER: ", [(power_val, power_color)])
        ]

        # --- 3. Layout Anchors ---
        right_margin = UISettings.STATUS_RIGHT_MARGIN
        row_spacing = UISettings.STATUS_ROW_SPACING

        # Meter sits directly below the hearts row in the top-right HUD.
        meter_width = UISettings.BOOST_METER_WIDTH
        meter_height = UISettings.BOOST_METER_HEIGHT
        meter_x = ScreenSettings.WIDTH - right_margin - meter_width
        meter_y = UISettings.HEART_TOP_MARGIN + UISettings.HEART_SPRITE_SIZE[1] + UISettings.BOOST_METER_TOP_GAP

        # Push text rows below the meter so there is clear separation.
        start_y = meter_y + meter_height + UISettings.BOOST_METER_BOTTOM_GAP

        for i, (label, value_segments) in enumerate(rows):
            # Render the white label
            label_surf = self.small_font.render(label, False, 'white')
            value_surfaces = [self.small_font.render(text, False, color) for text, color in value_segments]
            
            # Calculate positions to align the entire line to the right
            value_width = sum(surf.get_width() for surf in value_surfaces)
            total_width = label_surf.get_width() + value_width
            x_pos = ScreenSettings.WIDTH - right_margin - total_width
            y_pos = start_y + (i * row_spacing)
            
            self.screen.blit(label_surf, (x_pos, y_pos))
            value_x = x_pos + label_surf.get_width()
            for surf in value_surfaces:
                self.screen.blit(surf, (value_x, y_pos))
                value_x += surf.get_width()

        bombs_top_right = (
            ScreenSettings.WIDTH - right_margin,
            start_y + (len(rows) * row_spacing) + UISettings.BOMBS_ROW_TOP_GAP,
        )
        self._draw_bomb_icons(player.bombs, bombs_top_right)

        # --- 4. Boost/Brake Meter ---
        ratio, boost_state = player.get_boost_meter()

        if boost_state == 'boost':
            fill_color = 'orange'
        elif boost_state == 'brake':
            fill_color = 'gold'
        elif boost_state == 'cooldown':
            fill_color = 'red'
        else:
            fill_color = 'deepskyblue'

        pygame.draw.rect(self.screen, (60, 60, 60), (meter_x, meter_y, meter_width, meter_height), border_radius=3)
        pygame.draw.rect(
            self.screen,
            fill_color,
            (meter_x, meter_y, int(meter_width * ratio), meter_height),
            border_radius=3
        )
        pygame.draw.rect(self.screen, 'white', (meter_x, meter_y, meter_width, meter_height), 1, border_radius=3)

    def update(
        self,
        game_state: str,
        save_data: dict,
        score: int,
        entering_initials: bool = False,
        initials: str = "AAA",
        initials_index: int = 0,
    ) -> None:
        """Render the correct UI screen for the current game state.

        Args:
            game_state (str): One of intro, game_active, game_over, or pause.
            save_data (dict): Save payload containing leaderboard/high-score data.
            score (int): Current run score.
            entering_initials (bool): Whether the game-over initials-entry UI is active.
            initials (str): Current three-letter initials buffer.
            initials_index (int): Active cursor position within initials buffer.
        """

        screen_center_x = ScreenSettings.WIDTH // 2
        leaderboard = save_data.get('leaderboard', [])

        if game_state == 'intro':
            self.display_title()
            self.display_player_ship(170)
            self.display_leaderboard(leaderboard, title="TOP 10", start_y=260)
            self.display_intro_message()

        elif game_state == 'game_active':
            self.display_in_game_score(save_data, score)
            self.display_level(score)

        elif game_state == 'game_over':
            self.display_game_over()
            self.display_high_score(save_data)
            self.display_game_over_score(score)

            if entering_initials:
                prompt = self.small_font.render("NEW HIGH SCORE! ENTER YOUR INITIALS", False, 'yellow')
                prompt_rect = prompt.get_rect(center=(screen_center_x, 125))
                self.screen.blit(prompt, prompt_rect)

                initials_text = ""
                for i, ch in enumerate(initials):
                    if i == initials_index:
                        initials_text += f"[{ch}] "
                    else:
                        initials_text += f" {ch}  "

                initials_surf = self.large_font.render(initials_text.strip(), False, FontSettings.COLOR)
                initials_rect = initials_surf.get_rect(center=(screen_center_x, 165))
                self.screen.blit(initials_surf, initials_rect)

                leaderboard_title_y = 220
            else:
                restart_surf = self.medium_font.render("PRESS ENTER TO PLAY AGAIN", False, FontSettings.COLOR)
                restart_rect = restart_surf.get_rect(center=(screen_center_x, ScreenSettings.HEIGHT - 70))
                self.screen.blit(restart_surf, restart_rect)

                leaderboard_title_y = 130

            self.display_leaderboard(
            leaderboard,
            title="TOP 10",
            start_y=leaderboard_title_y
            )

        elif game_state == 'pause':
            self.display_pause_text()
