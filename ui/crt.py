import pygame
import random
from settings import *

class CRT:
    """Creates a CRT monitor effect"""
    def __init__(self, screen):
        """
        Initializes the CRT effect by loading a TV overlay image,
        scaling it to fit the screen,
        and storing a reference to the screen for drawing.

        Args:
            screen (pygame.Surface): The main display surface that the CRT
                overlay will be composited onto each frame.
        """
        super().__init__()
        self.screen = screen
        self.tv = pygame.image.load(AssetPaths.TV).convert_alpha()
        self.tv = pygame.transform.scale(self.tv,(ScreenSettings.RESOLUTION))

    def create_crt_lines(self):
        """Draws evenly-spaced horizontal scanlines onto the TV overlay surface to simulate a CRT monitor."""
        line_height = ScreenSettings.CRT_SCANLINE_HEIGHT
        line_amount = int(ScreenSettings.HEIGHT / line_height)
        for line in range(line_amount):
            y_pos = line * line_height
            pygame.draw.line(self.tv,'black',(0,y_pos),(ScreenSettings.WIDTH,y_pos),1)

    def draw(self):
        """
        Composites the CRT overlay onto the screen.

        Randomizes the TV overlay's alpha each frame within CRT_ALPHA_RANGE to
        simulate the subtle flicker of a real CRT monitor, then draws scanlines
        and blits the overlay on top of the rendered game scene.
        """
        self.tv.set_alpha(random.randint(*ScreenSettings.CRT_ALPHA_RANGE))
        self.create_crt_lines()
        self.screen.blit(self.tv,(0,0))
