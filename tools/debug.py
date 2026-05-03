import pygame
from settings import *

pygame.init()
font = pygame.font.Font(None,30)

def debug(info, y=ScreenSettings.HEIGHT - 20, x=10):
    """Renders a debug string directly onto the active display surface.

    Draws a black background rect behind the text to keep it readable over
    any background. Useful for quick in-game value inspection during development.

    Args:
        info: Any value; converted to a string via str() before rendering.
        y (int): Vertical position of the debug text. Defaults to near the
            bottom of the screen.
        x (int): Horizontal position of the debug text. Defaults to 10.
    """
    display_surf = pygame.display.get_surface()
    debug_surf = font.render(str(info),True,'White')
    debug_rect = debug_surf.get_rect(topleft = (x,y))
    pygame.draw.rect(display_surf,'Black',debug_rect)
    display_surf.blit(debug_surf,debug_rect)