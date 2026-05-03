"""HUD overlays: hearts row + the Stage 6 game-over banner.

Stage 6 ports the bare minimum HUD pieces. The hearts row in the top-
right mirrors player health; the centered "GAME OVER — press Enter to
restart" overlay shows when a run ends. Both are pure render helpers —
state (the current heart count, the ``game_active`` flag) lives in
``main.py`` and gets passed in each frame.

The richer intro/game-over screens (final score, high-score, initials
entry, pause overlay) land in Stage 9 alongside the
``SessionStateManager`` port — at which point this module likely splits
into ``hud.py`` (in-game) and ``menus.py`` (overlays). Stage 6 keeps
both pieces co-located so the file count stays small while only two HUD
elements exist.
"""

import pygame

from settings import (
    AssetPaths,
    FontSettings,
    GameOverSettings,
    HeartSettings,
    ScreenSettings,
)


class HeartsHUD:
    """Renders the player-health row in the top-right corner.

    Mirrors the legacy ``display_hearts`` rhythm in ``legacy/ui/style.py``:
    load the heart sprite once at construction (so per-frame draws never
    touch disk), pre-compute the row's leftmost x from the sprite's
    actual pixel width (so the row pins to the right edge regardless of
    the asset's size), and on each draw blit one icon per remaining
    heart left-to-right. The leftmost slot empties first as the player
    takes damage; the rightmost icon is the last to disappear.
    """

    def __init__(self):
        """Load the heart sprite and pre-compute the row's leftmost x."""
        # ``convert_alpha`` matches how every other sprite in this code
        # base is loaded (see ``Alien.__init__``) — keeps the alpha
        # channel cheap to blit each frame.
        self.heart_surf = pygame.image.load(AssetPaths.HEART).convert_alpha()
        self._heart_width = self.heart_surf.get_width()
        # Leftmost x for the row: pin the rightmost heart to
        # ``WIDTH - RIGHT_MARGIN``, then walk back ``MAX`` icon-widths
        # plus inter-icon spacing. Computing this once at init keeps the
        # per-frame draw a tight loop with no arithmetic per heart.
        self._row_left_x = ScreenSettings.WIDTH - (
            self._heart_width * HeartSettings.MAX
            + HeartSettings.RIGHT_MARGIN
        )

    def draw(self, surface, hearts):
        """Blit ``hearts`` heart icons starting at the row's left.

        Args:
            surface (pygame.Surface): Destination surface, typically the
                main game screen.
            hearts (int): Number of icons to draw. Clamped to
                ``[0, HeartSettings.MAX]`` defensively so a caller mis-
                count can't draw a negative or wraparound row.
        """
        # Defensive clamp — if main.py ever subtracts past zero before
        # the game-over branch fires, we render an empty row instead of
        # blowing the loop bounds out into infinity.
        hearts = max(0, min(hearts, HeartSettings.MAX))
        for index in range(hearts):
            x = self._row_left_x + index * (
                self._heart_width + HeartSettings.SPACING
            )
            surface.blit(self.heart_surf, (x, HeartSettings.TOP_MARGIN))


class GameOverScreen:
    """Renders the Stage 6 minimal game-over banner + restart prompt.

    Intentionally not a state machine and not a sprite — just two
    pre-rasterized text surfaces blitted in the center of the screen
    when the main loop's ``game_active`` flag flips to ``False``.
    Stage 9 replaces this with the full intro/game-over flow (final
    score, high-score, initials entry).
    """

    def __init__(self):
        """Pre-rasterize banner + prompt so per-frame draws are pure blits.

        The text never changes between frames, so paying the
        ``font.render`` cost once at construction is strictly better
        than re-rendering each frame. Both surfaces uppercase per the
        project-wide rule (``docs/TODO.md`` Q7).
        """
        banner_font = pygame.font.Font(
            FontSettings.FONT, GameOverSettings.BANNER_SIZE
        )
        prompt_font = pygame.font.Font(
            FontSettings.FONT, GameOverSettings.PROMPT_SIZE
        )
        # ``.upper()`` here is belt-and-suspenders — the source strings
        # in ``GameOverSettings`` are already uppercase, but threading
        # ``.upper()`` through every font.render call site keeps the
        # rule visible at the boundary so a future edit to the source
        # text in lower-case can't accidentally render mixed-case.
        self._banner_surf = banner_font.render(
            GameOverSettings.BANNER_TEXT.upper(),
            True,
            GameOverSettings.COLOR,
        )
        self._prompt_surf = prompt_font.render(
            GameOverSettings.PROMPT_TEXT.upper(),
            True,
            GameOverSettings.COLOR,
        )
        # Pre-compute rects too; both layout and rasterization are
        # frame-invariant.
        cx, cy = ScreenSettings.CENTER
        self._banner_rect = self._banner_surf.get_rect(
            center=(cx, cy - GameOverSettings.BANNER_OFFSET)
        )
        self._prompt_rect = self._prompt_surf.get_rect(
            center=(cx, cy + GameOverSettings.PROMPT_OFFSET)
        )

    def draw(self, surface):
        """Blit the banner above center and the prompt below it.

        Args:
            surface (pygame.Surface): Destination surface, typically the
                main game screen. Drawn last in the frame so the overlay
                sits on top of any frozen aliens still on the playfield.
        """
        surface.blit(self._banner_surf, self._banner_rect)
        surface.blit(self._prompt_surf, self._prompt_rect)
