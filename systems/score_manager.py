"""Run score + persisted high-score / leaderboard storage.

Stage 7 ports the storage half of the legacy ``ScoreManager``
(``legacy/systems/managers.py``): the ``score`` field, the JSON-on-
disk save payload (``high_score`` + ``leaderboard``), the load-at-boot
flow, and ``reset()`` for new runs. The initials-entry flow
(``entering_initials`` / ``qualifies_for_leaderboard`` /
``submit_initials``) is intentionally left out at this stage —
``docs/TODO.md`` §5 Stage 9 specifically owns "if keeping leaderboards,
port `ScoreManager` initials entry path." Stage 7 only needs scoring +
high-score persistence; the input flow that fills in the player's
three-letter name lives with the other menu work.

The legacy class stored a reference to the ``GameManager`` and read
``game.scores.score`` from sibling code; Typing Hero's version owns its
state and exposes ``add_for_color`` / ``persist`` / ``reset`` as the
public surface so ``main.py`` (which still doesn't have a real central
coordinator yet — Stage 9's ``SessionStateManager`` port introduces one)
can wire it up with no shared-mutable-game-object pattern.
"""

import json
import os

from settings import AlienSettings, ScoreSettings


class ScoreManager:
    """Owns the run score and the on-disk high-score / leaderboard payload.

    The manager is pure storage — it never touches pygame and never
    renders. ``ScoreHUD`` reads ``score`` and ``high_score`` for the
    top-left HUD; ``main.py`` calls ``add_for_color(color)`` on each
    successful kill and ``persist()`` on game-over. Same separation
    of concerns as ``WordManager``: state lives here, rendering and
    event-routing live elsewhere, the Refactoring Rules in
    ``docs/TESTING.md`` are honored.
    """

    def __init__(self, save_path=None):
        """Initialize a zero score and load any persisted save payload.

        Args:
            save_path (str | None): Override the on-disk save location
                used in tests. ``None`` falls through to
                ``ScoreSettings.SAVE_PATH`` — the project-root
                ``high_score.txt`` path that mirrors the legacy
                location, so an existing Star Hero save lands in the
                same slot Typing Hero reads from on first boot.
        """
        self._save_path = save_path or ScoreSettings.SAVE_PATH
        self.score = 0
        # Same payload shape as legacy: a dict with a top-level
        # ``high_score`` int and a ``leaderboard`` list of
        # ``{'name': 'AAA', 'score': 1234}`` dicts. The leaderboard
        # is empty in the Stage 7 flow (no initials entry yet) but
        # the field is allocated so Stage 9 can drop initials in
        # without a schema migration on the save file.
        self.save_data = {
            'high_score': 0,
            'leaderboard': [],
        }
        self._load_from_disk()

    def add_for_color(self, color):
        """Award the per-color point value for one alien kill.

        Args:
            color (str): One of the keys in ``AlienSettings.POINTS`` —
                ``'red'``, ``'green'``, ``'yellow'``, ``'blue'``. The
                color string is stored on each ``Alien`` instance so
                ``main.py`` can pass ``alien.color`` directly without
                a lookup table.

        Returns:
            int: The number of points awarded — useful if the caller
            wants to render a "+200" floater later (Stage 10 polish).
        """
        # ``KeyError`` on an unknown color is intentional — that's a
        # bug at the caller (a new color was added without a POINTS
        # entry), and we'd rather know loudly than silently award 0.
        points = AlienSettings.POINTS[color]
        self.score += points
        return points

    def reset(self):
        """Zero the score for a fresh run; leave the persisted save alone.

        ``main.py``'s game-over → restart path calls this so the new
        run starts at 0 without losing the high score the player just
        beat. ``self.save_data`` is preserved on purpose — it's the
        durable record that survives the run boundary.

        Returns:
            None.
        """
        self.score = 0

    def persist(self):
        """Write the high-score payload to disk.

        Called from ``main.py`` at game-over. Updates ``high_score``
        in the payload if the just-finished run beat the previous
        record, then dumps the dict to JSON at ``self._save_path``.
        Stage 9's initials-entry port will add a leaderboard write
        here too; for now we only touch the scalar high-score field
        so the save file stays compatible with both stages.

        Returns:
            None.
        """
        # Promote the run's score into the high-score field if it's
        # the new record. Reading from ``save_data`` rather than a
        # cached attr means a Stage 9 leaderboard write can mutate
        # ``high_score`` (e.g. via ``submit_initials``) and this
        # path still does the right thing.
        if self.score > self.save_data.get('high_score', 0):
            self.save_data['high_score'] = self.score
        # Open in 'w' mode (truncate) — the file is small and
        # rewritten in full each game-over, no append semantics.
        # ``OSError`` from a missing/unwritable path bubbles up: the
        # game can run fine without persistence (high score just
        # won't survive), but the loud error tells the player /
        # developer their save isn't landing.
        with open(self._save_path, 'w', encoding='utf-8') as save_file:
            json.dump(self.save_data, save_file)

    @property
    def high_score(self):
        """Highest score persisted across runs.

        Sugar over ``self.save_data['high_score']`` so the HUD render
        path doesn't have to know about the dict layout. Defaults to
        0 if the save file was missing or corrupt at boot — fresh
        installs read as "no record yet" rather than crashing.

        Returns:
            int: The highest score in the persisted save payload.
        """
        return self.save_data.get('high_score', 0)

    def _load_from_disk(self):
        """Read the persisted save payload, if any, into ``self.save_data``.

        Internal helper for ``__init__`` only. Splitting it out keeps
        ``__init__`` short and isolates the "tolerate missing /
        corrupt file" branch so a future test can override behavior
        by patching this single method. A missing file is the normal
        first-boot case; a corrupt file logs and falls back to the
        empty default so a single bad save never breaks startup.

        Returns:
            None. Mutates ``self.save_data`` in place if the load
            succeeds; leaves the empty default in place otherwise.
        """
        # Skip cleanly if the file doesn't exist yet — first boot or
        # a fresh install. ``os.path.isfile`` (vs catching the
        # ``FileNotFoundError``) keeps the happy path explicit.
        if not os.path.isfile(self._save_path):
            return
        try:
            with open(self._save_path, 'r', encoding='utf-8') as save_file:
                payload = json.load(save_file)
        except (OSError, json.JSONDecodeError):
            # Corrupt or unreadable — print so Frankie sees it during
            # development, then fall through to the empty default. A
            # later boot can still recover by writing a fresh save.
            print(f'ScoreManager: ignoring corrupt save at {self._save_path}')
            return
        # Defensive merge: only adopt keys we expect, in case a
        # future schema change leaves stale fields lying around.
        self.save_data['high_score'] = int(payload.get('high_score', 0))
        self.save_data['leaderboard'] = list(payload.get('leaderboard', []))
