"""Run score and persisted high-score storage."""

import json
import os

from settings import AlienSettings, ScoreSettings


class ScoreManager:
    """Owns the run score and the on-disk high-score payload.

    Never touches pygame or renders. ``ScoreHUD`` reads ``score`` and
    ``high_score``; ``main.py`` calls ``add_for_color`` on each kill
    and ``persist`` on game-over.
    """

    def __init__(self, save_path=None):
        self._save_path = save_path or ScoreSettings.SAVE_PATH
        self.score = 0
        self.save_data = {
            'high_score': 0,
            'leaderboard': [],
        }
        self._load_from_disk()

    def add_for_color(self, color):
        """Award points for one alien kill. Returns the points awarded."""
        points = AlienSettings.POINTS[color]
        self.score += points
        return points

    def reset(self):
        """Zero the run score; leave the persisted save intact."""
        self.score = 0

    def persist(self):
        """Write the high-score payload to disk. Updates the record if beaten."""
        if self.score > self.save_data.get('high_score', 0):
            self.save_data['high_score'] = self.score
        with open(self._save_path, 'w', encoding='utf-8') as save_file:
            json.dump(self.save_data, save_file)

    @property
    def high_score(self):
        """Highest score persisted across runs."""
        return self.save_data.get('high_score', 0)

    def _load_from_disk(self):
        """Load the persisted save payload into ``self.save_data``, if it exists."""
        if not os.path.isfile(self._save_path):
            return
        try:
            with open(self._save_path, 'r', encoding='utf-8') as save_file:
                payload = json.load(save_file)
        except (OSError, json.JSONDecodeError):
            print(f'ScoreManager: ignoring corrupt save at {self._save_path}')
            return
        self.save_data['high_score'] = int(payload.get('high_score', 0))
        self.save_data['leaderboard'] = list(payload.get('leaderboard', []))
