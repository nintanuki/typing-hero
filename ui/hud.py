"""HUD overlays: hearts row + score readout + the Stage 6 game-over banner.

Stage 6 ported the bare minimum HUD pieces. Stage 7 adds the top-left
score readout (current score + persistent high score) so the player
sees their progress as they kill aliens. All three pieces are pure
render helpers — state (current heart count, ``game_active`` flag,
``ScoreManager``) lives in ``main.py`` (or its managers) and gets
passed in each frame.

The richer intro/game-over screens (final score, high-score, initials
entry, pause overlay) land in Stage 9 alongside the
``SessionStateManager`` port — at which point this module likely splits
into ``hud.py`` (in-game) and ``menus.py`` (overlays). Stage 6/7 keep
all pieces co-located so the file count stays small while only a few
HUD elements exist.
"""

import pygame

from settings import (
    AssetPaths,
    FontSettings,
    GameOverSettings,
    HeartSettings,
    ScoreSettings,
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


class ScoreHUD:
    """Renders the current score + persistent high score in the top-left.

    Mirrors the legacy ``display_in_game_score`` rhythm in
    ``legacy/ui/style.py``: small high-score row at the very top,
    medium current-score row directly below. The two-row stack is part
    of the "be faithful to the scoreboard" piece of ``docs/TODO.md`` §8
    O1 — Star Hero players will recognize the layout from across the
    arcade. Fonts are loaded once at construction so per-frame draws
    only call ``font.render`` for the two integer values that change.
    """

    def __init__(self):
        """Pre-load the small + medium fonts used by the two score rows."""
        # Font instances are reused across frames — Pygame recreates
        # the font face every ``Font(...)`` call, so caching the two
        # objects here saves the per-frame allocation. This mirrors
        # the same pattern ``ScoreHUD``'s sibling classes follow.
        self._high_score_font = pygame.font.Font(
            FontSettings.FONT, ScoreSettings.HIGH_SCORE_SIZE
        )
        self._score_font = pygame.font.Font(
            FontSettings.FONT, ScoreSettings.SCORE_SIZE
        )

    def draw(self, surface, score, high_score):
        """Render the high-score row and the current-score row.

        Both rows are uppercase per the project-wide rule (Q7 in
        ``docs/TODO.md``). The strings include a colon + value so the
        player can distinguish the two readouts at a glance even when
        both values are similar (e.g. on a near-record run).

        Args:
            surface (pygame.Surface): Destination surface, typically
                the main game screen. Drawn early in the HUD pass so
                the hearts row and the typing buffer can sit beside
                / below it without overlap concerns.
            score (int): Current run score. Read from
                ``ScoreManager.score`` at the call site.
            high_score (int): Persistent high score across runs. Read
                from ``ScoreManager.high_score`` (the property
                wrapping ``save_data['high_score']``).
        """
        # Render in two passes — the high-score sits a few pixels
        # above the score so the larger SCORE row reads as the
        # primary readout and the smaller HIGH SCORE row as the
        # contextual reference. Both topleft-anchored so the row
        # widths don't have to match.
        high_surf = self._high_score_font.render(
            f'HIGH SCORE: {high_score}', True, ScoreSettings.COLOR
        )
        surface.blit(high_surf, ScoreSettings.HIGH_SCORE_TOPLEFT)

        score_surf = self._score_font.render(
            f'SCORE: {score}', True, ScoreSettings.COLOR
        )
        surface.blit(score_surf, ScoreSettings.SCORE_TOPLEFT)


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
