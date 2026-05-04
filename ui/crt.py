import pygame
import random
from settings import *

class CRT:
    """CRT scanline overlay composited on top of each rendered frame."""
    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.tv = pygame.image.load(AssetPaths.TV).convert_alpha()
        self.tv = pygame.transform.scale(self.tv,(ScreenSettings.RESOLUTION))

    def create_crt_lines(self):
        line_height = ScreenSettings.CRT_SCANLINE_HEIGHT
        line_amount = int(ScreenSettings.HEIGHT / line_height)
        for line in range(line_amount):
            y_pos = line * line_height
            pygame.draw.line(self.tv,'black',(0,y_pos),(ScreenSettings.WIDTH,y_pos),1)

    def draw(self):
        """Composite the scanline overlay onto the screen with a randomized alpha flicker."""
        self.tv.set_alpha(random.randint(*ScreenSettings.CRT_ALPHA_RANGE))
        self.create_crt_lines()
        self.screen.blit(self.tv,(0,0))
