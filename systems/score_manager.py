"""Run score and persisted high-score storage."""

import json
import os

from settings import AlienSettings, FontSettings, ScoreSettings


class ScoreManager:
    """Owns the run score, on-disk high-score payload, and initials-entry state.

    Never touches pygame or renders. ``ScoreHUD`` reads ``score`` and
    ``high_score``; ``main.py`` calls ``add_for_color`` on each kill
    and ``finalize_game_over`` when the game ends.
    """

    def __init__(self, save_path=None):
        self._save_path = save_path or ScoreSettings.SAVE_PATH
        self.score = 0
        self.save_data = {
            'high_score': 0,
            'leaderboard': [],
        }
        self._load_from_disk()

        # Initials-entry state — only active when the run score qualifies.
        self.entering_initials = False
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

    def add_for_color(self, color):
        """Award points for one alien kill. Returns the points awarded."""
        points = AlienSettings.POINTS[color]
        self.score += points
        return points

    def reset(self):
        """Zero the run score and clear initials state; leave persisted save intact."""
        self.score = 0
        self.entering_initials = False
        self.initials = FontSettings.DEFAULT_INITIALS
        self.initials_index = 0
        self.pending_score = None
        self.score_processed = False

    def finalize_game_over(self):
        """On game over, route to initials entry or persist the score directly."""
        if self.score_processed:
            return
        if self.qualifies_for_leaderboard(self.score):
            self.entering_initials = True
            self.initials = FontSettings.DEFAULT_INITIALS
            self.initials_index = 0
            self.pending_score = self.score
        else:
            self._update_high_score()
            self._write_to_disk()
            self.score_processed = True

    def qualifies_for_leaderboard(self, score):
        """Return True if ``score`` earns a leaderboard slot."""
        lb = self.save_data.get('leaderboard', [])
        if len(lb) < 10:
            return score > 0
        return score > lb[-1]['score']

    def submit_initials(self):
        """Commit the entered initials to the leaderboard and persist."""
        lb = self.save_data.get('leaderboard', [])
        existing = next((e for e in lb if e['name'] == self.initials), None)
        if existing:
            if self.pending_score > existing['score']:
                existing['score'] = self.pending_score
        else:
            lb.append({'name': self.initials, 'score': self.pending_score})
        self.save_data['leaderboard'] = sorted(
            lb, key=lambda e: e['score'], reverse=True
        )[:10]
        if self.save_data['leaderboard']:
            self.save_data['high_score'] = self.save_data['leaderboard'][0]['score']
        self._write_to_disk()
        self.entering_initials = False
        self.pending_score = None
        self.score_processed = True

    def move_cursor(self, step):
        """Move the initials cursor left (step=-1) or right (step=1)."""
        self.initials_index = max(0, min(2, self.initials_index + step))

    def cycle_char(self, step):
        """Rotate the highlighted letter forward (step=1) or backward (step=-1)."""
        chars = list(self.initials)
        c = chars[self.initials_index]
        if step > 0:
            chars[self.initials_index] = 'A' if c == 'Z' else chr(ord(c) + 1)
        else:
            chars[self.initials_index] = 'Z' if c == 'A' else chr(ord(c) - 1)
        self.initials = ''.join(chars)

    @property
    def high_score(self):
        """Highest score persisted across runs."""
        return self.save_data.get('high_score', 0)

    def _update_high_score(self):
        """Update high_score in save_data if current score beats it."""
        if self.score > self.save_data.get('high_score', 0):
            self.save_data['high_score'] = self.score

    def _write_to_disk(self):
        """Write save_data to disk."""
        with open(self._save_path, 'w', encoding='utf-8') as save_file:
            json.dump(self.save_data, save_file)

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
