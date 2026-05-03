import pygame
from settings import *

# see https://www.youtube.com/watch?v=VUFvY349ess for more details
class Background(pygame.sprite.Sprite):
    """Creates a scrolling space themed background"""
    def __init__(self, groups):
        """
        Initializes the background by loading a space-themed image,
        creating a surface that is twice the height of the original image for seamless scrolling,
        and setting the initial position of the background.

        Args:
            groups: The sprite group(s) this background should be added to.
        """
        super().__init__(groups)
        bg_image = pygame.image.load(AssetPaths.BACKGROUND).convert()
        full_height = bg_image.get_height()
        full_width = bg_image.get_width()
        self.image = pygame.Surface((full_width,full_height * 2))

        self.image.blit(bg_image,(0,0))
        self.image.blit(bg_image,(0,full_height))

        self.rect = self.image.get_rect(bottomleft = (0,ScreenSettings.HEIGHT))
        self.pos = pygame.math.Vector2(self.rect.bottomleft)

        self.scroll_speed = ScreenSettings.DEFAULT_BG_SCROLL_SPEED

    def update(self, delta_time, speed_multiplier=1.0):
        """
        Updates the position of the background to create a scrolling effect
        by moving it downwards based on the defined scroll speed and the time elapsed
        since the last update, and resets its position when it has scrolled completely.

        Args:
            delta_time (float): Time in seconds elapsed since the last frame, used
                to ensure scroll speed is frame-rate independent.
            speed_multiplier (float): A scalar applied to the scroll speed each
                frame. Values below 1.0 slow the background (e.g. when brake is
                active); values above 1.0 speed it up.
        """
        self.pos.y += self.scroll_speed * delta_time * speed_multiplier
        if self.rect.top >= 0:
            self.pos.y = -self.image.get_height() / 2
        self.rect.y = round(self.pos.y)

class Explosion(pygame.sprite.Sprite):
    """Creates an explosion animation"""
    def __init__(self, pos_x, pos_y):
        """
        Initializes the explosion animation by loading a sprite sheet,
        extracting individual frames, and setting the initial position of the explosion.

        Args:
            pos_x (int): The x-coordinate of the explosion's center.
            pos_y (int): The y-coordinate of the explosion's center.
        """
        super().__init__()
        self.is_animating = False

        # sprite sheet from https://www.pngwing.com/en/free-png-xiyem/
        sprite_sheet = pygame.image.load(AssetPaths.EXPLOSION).convert_alpha()

        # Using list comprehension to build the explosion animation fromt he sprite sheet
        self.sprites = [self.get_image(sprite_sheet, frame, ExplosionSettings.SIZE, ExplosionSettings.SIZE, ExplosionSettings.SCALE) for frame in range(ExplosionSettings.FRAMES)]

        self.current_sprite = 0
        self.image = self.sprites[self.current_sprite]

        self.rect = self.image.get_rect(center = (pos_x, pos_y))

    # see sprite sheet tutorials by Coding With Russ:
    # https://www.youtube.com/watch?v=M6e3_8LHc7A
    # https://www.youtube.com/watch?v=M6e3_8LHc7A
    @staticmethod # use static method because it does not use the self argument
    def get_image(sheet, frame, width, height, scale):
        """Extracts a single frame from a sprite sheet and scales it to the desired size.

        Args:
            sheet (pygame.Surface): The full sprite sheet surface.
            frame (int): Zero-based index of the frame to extract.
            width (int): Width in pixels of a single frame on the sprite sheet.
            height (int): Height in pixels of a single frame on the sprite sheet.
            scale (float): Scale factor applied to the extracted frame.

        Returns:
            pygame.Surface: A scaled surface containing the requested frame.
        """
        surf = pygame.Surface((width,height), pygame.SRCALPHA) # pygame.SRCALPHA gives the surface per-pixel-transparency
        surf.blit(sheet,(0,0),((frame*width),0,width,height))
        surf = pygame.transform.scale(surf, (width * scale, height * scale))
        return surf

    def explode(self):
        """Starts the explosion animation by setting the is_animating flag to True.

        Must be called after the sprite is added to a group; the animation
        advances each frame via update().
        """
        self.is_animating = True

    def update(self, speed):
        """
        Advances the explosion animation frame and removes the sprite when complete.

        Args:
            speed (float): How much to advance the frame index each call.
                Larger values play the animation faster. Typically supplied
                from ExplosionSettings.ANIMATION_SPEED.
        """
        if self.is_animating:
            self.current_sprite += speed
            if int(self.current_sprite) >= len(self.sprites):
                self.kill()
            else:
                self.image = self.sprites[int(self.current_sprite)]
