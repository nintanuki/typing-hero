"""Typing input, prefix-locking state machine, and word pool."""

import random

from settings import ScoreSettings, WordSettings


class WordManager:
    """Owns the active typing prefix, the locked alien, and the word pool.

    Never touches pygame or the screen. ``main.py`` feeds KEYDOWN events
    and reads state for rendering; ``SpawnDirector`` calls ``pick_word``
    at each spawn tick.
    """

    def __init__(self, wordlist_path=None):
        # Prefix stored uppercase so it can be blitted directly and compared
        # against alien.word.upper() without re-casing on every keystroke.
        self.current_prefix = ""
        self.targeted_alien = None
        self.candidate_aliens = []
        self._word_bands = self._load_bands(wordlist_path)
        self._all_words = self._dedupe_words_in_order(self._word_bands)

    def handle_letter(self, char, aliens):
        """Append ``char`` if it keeps at least one matching alien candidate."""
        if len(char) != 1 or not char.isalpha():
            return
        char_upper = char.upper()

        candidate_prefix = self.current_prefix + char_upper
        matches = self._matching_aliens(candidate_prefix, aliens)
        if not matches:
            return

        self.current_prefix = candidate_prefix
        self._update_candidates(matches)

    def handle_backspace(self, aliens):
        """Drop one typed letter and recompute candidates for the new prefix."""
        if not self.current_prefix:
            return
        self.current_prefix = self.current_prefix[:-1]
        if not self.current_prefix:
            self.candidate_aliens = []
            self.targeted_alien = None
            return

        self._update_candidates(self._matching_aliens(self.current_prefix, aliens))

    def handle_enter(self):
        """Commit the current prefix.

        Returns the locked alien if its word was just completed, otherwise
        ``None``. State clears either way.
        """
        killed = None
        if (
            self.targeted_alien is not None
            and self.current_prefix == self.targeted_alien.word.upper()
        ):
            killed = self.targeted_alien
        self.current_prefix = ""
        self.candidate_aliens = []
        self.targeted_alien = None
        return killed

    def clear_lock(self):
        """Drop both prefix and target without firing. Idempotent."""
        self.current_prefix = ""
        self.candidate_aliens = []
        self.targeted_alien = None

    def pick_word(self, in_use, level=1):
        """Return a random unused word from the active level band.

        If the active band is fully consumed by on-screen words, this
        falls back to any other loaded band before returning ``None``.
        """
        in_use_set = set(in_use)
        band = self._band_for_level(level)
        primary_pool = self._word_bands.get(band, ())
        available = [word for word in primary_pool if word not in in_use_set]
        if not available:
            available = [word for word in self._all_words if word not in in_use_set]
        if not available:
            return None
        return random.choice(available)

    @staticmethod
    def _load_words(path):
        """Read a one-word-per-line UTF-8 file; return a lowercase alpha-only list."""
        words = []
        try:
            with open(path, 'r', encoding='utf-8') as source:
                for line in source:
                    stripped = line.strip().lower()
                    if stripped.isalpha():
                        words.append(stripped)
        except OSError:
            return []
        return words

    def _load_bands(self, fallback_wordlist_path):
        """Load level difficulty bands from settings, with fallback to one flat list."""
        bands = {}
        for band, path in WordSettings.WORD_BANK_PATHS.items():
            bands[band] = self._load_words(path)

        if any(bands.values()):
            return bands

        # Backward-compatible fallback if band files are missing.
        fallback_words = self._load_words(fallback_wordlist_path) if fallback_wordlist_path else []
        return {band: fallback_words[:] for band in WordSettings.WORD_BANK_PATHS}

    @staticmethod
    def _dedupe_words_in_order(word_bands):
        """Flatten all bands while preserving first-seen order and uniqueness."""
        merged = []
        seen = set()
        for _, words in sorted(word_bands.items()):
            for word in words:
                if word in seen:
                    continue
                seen.add(word)
                merged.append(word)
        return merged

    @staticmethod
    def _clamp_level(level):
        """Clamp an arbitrary level value to [1, MAX_LEVEL]."""
        return max(1, min(ScoreSettings.MAX_LEVEL, int(level)))

    def _band_for_level(self, level):
        """Map current level to configured word band index."""
        clamped_level = self._clamp_level(level)
        return WordSettings.LEVEL_WORD_BAND[clamped_level - 1]

    @staticmethod
    def _matching_aliens(prefix, aliens):
        """Return all alive aliens whose word starts with ``prefix``."""
        return [
            alien for alien in aliens
            if alien.word.upper().startswith(prefix)
        ]

    def _update_candidates(self, candidates):
        """Update candidate set and choose the provisional focused alien."""
        self.candidate_aliens = list(candidates)
        if not self.candidate_aliens:
            self.targeted_alien = None
            return

        # While ambiguous, bias focus to the lowest alien (most urgent).
        self.candidate_aliens.sort(key=lambda alien: alien.rect.top, reverse=True)
        self.targeted_alien = self.candidate_aliens[0]

    @property
    def prefix_length(self):
        """Number of letters currently typed."""
        return len(self.current_prefix)
