"""Typing input + prefix-locking state machine + word pool.

Stage 3 introduced ``WordManager`` — the small piece of game state that
turns a stream of letter keypresses into "which alien is the player
currently typing at, and how far into its word are they?" Stage 4
extends the same class to also own the word pool: at boot it loads
``WordSettings.WORDLIST_PATH`` and exposes ``pick_word(in_use)`` so
``SpawnDirector`` can hand each new alien a unique word.

The model: at most one alien is locked at a time. When no alien is
locked, the next letter the player types tries to acquire a target by
finding an alien whose word starts with that letter (case-insensitive).
Once locked, further letters extend the prefix only if they continue to
match the target's word; letters that would diverge from the target are
ignored — Q3 in ``docs/TODO.md`` is resolved as "ignore wrong-letter
keystrokes; the lock survives." Backspace shrinks the prefix and
releases the lock when the prefix empties. Enter commits the buffer:
on a complete match the manager reports the kill back to the caller, on
a partial or empty buffer it just clears state.

All comparisons are case-insensitive; the manager stores the prefix in
uppercase so the typing-buffer render and the ``draw_word`` two-color
split read from the same string without re-uppercasing per frame. The
on-disk word list stays lowercase (per Q7's "store lowercase, uppercase
at render/compare time" rule) and is exposed to spawning code as-is.
"""

import random


class WordManager:
    """Owns the active typing prefix, the locked alien, and the word pool.

    The manager is intentionally storage-only — it never touches pygame
    or the screen. ``main.py`` feeds it KEYDOWN events and asks it for
    its current state when rendering; ``SpawnDirector`` asks it for the
    next word at spawn time. That keeps the input/state separation
    that the Refactoring Rules in ``docs/TESTING.md`` ask for, and
    makes the manager unit-testable without spinning up a display.
    """

    def __init__(self, wordlist_path=None):
        """Initialize an empty manager and (optionally) load the word pool.

        Args:
            wordlist_path (str | None): Path to a UTF-8 text file with
                one word per line. If ``None``, the pool stays empty
                and ``pick_word`` always returns ``None`` — useful for
                Stage 1–3 unit tests that only exercise prefix-locking.
                Lines are lowercased and stripped; non-alphabetic lines
                (blank lines, comments, words with digits/punctuation)
                are silently dropped so the file format can stay
                hand-edited without breaking the loader.
        """
        # ``current_prefix`` is stored uppercase so callers can blit it
        # directly (per Q7's project-wide uppercase rule) and so prefix
        # comparisons against ``alien.word.upper()`` don't have to
        # re-case on every keystroke.
        self.current_prefix = ""
        self.targeted_alien = None
        # The pool stays lowercase on disk and in memory; rendering
        # and prefix-matching both uppercase at the boundary so this
        # list is the authoritative storage form.
        self._words = self._load_words(wordlist_path) if wordlist_path else []

    def handle_letter(self, char, aliens):
        """Append ``char`` to the prefix, acquiring a lock if needed.

        Behavior depends on whether a target is currently locked:
          * No target locked: scan ``aliens`` for one whose word starts
            with ``char`` (case-insensitive). If found, set it as the
            target and start the prefix with ``char``. If multiple
            aliens share that starting letter, the lowest-y alien wins
            — that's the most urgent target on screen and matches the
            tie-break rule called out in ``docs/TODO.md`` §6. If no
            alien matches, the keystroke is silently ignored.
          * Target locked: append ``char`` to the prefix only if the
            new prefix is still a prefix of the target's word. Wrong
            letters mid-word are ignored without breaking the lock
            (Q3, v1 default).

        Args:
            char (str): Single character from ``event.unicode`` (any
                case). Empty / multi-character / non-letter strings are
                rejected — main.py is expected to filter via
                ``event.unicode.isalpha()`` before calling, but the
                guard is here too so a misuse from a future caller can
                never advance the prefix.
            aliens (Iterable): On-screen aliens to scan for a lock.
                Typically a ``pygame.sprite.Group``; any iterable of
                objects exposing ``.word`` and ``.rect.top`` works,
                which keeps the manager testable without pygame.

        Returns:
            None. The manager mutates its own state; the caller reads
            ``self.current_prefix`` and ``self.targeted_alien`` for
            rendering.
        """
        # Reject anything that isn't a single letter so a stray
        # ``event.unicode == ''`` (modifier-only key) or a multi-char
        # string from a future input path can't pollute the prefix.
        if len(char) != 1 or not char.isalpha():
            return
        char_upper = char.upper()

        if self.targeted_alien is None:
            self._acquire_target(char_upper, aliens)
            return

        # Locked: extend only if the new prefix still matches.
        candidate = self.current_prefix + char_upper
        if self.targeted_alien.word.upper().startswith(candidate):
            self.current_prefix = candidate

    def handle_backspace(self):
        """Drop the most recent letter from the prefix.

        If the prefix empties out, the lock releases — the next letter
        will re-acquire from scratch. Calling backspace with no prefix
        is a no-op (no exception, no spurious lock-clear).

        Returns:
            None.
        """
        if not self.current_prefix:
            return
        self.current_prefix = self.current_prefix[:-1]
        if not self.current_prefix:
            self.targeted_alien = None

    def handle_enter(self):
        """Commit the current prefix.

        On a complete match against the locked target's word, return
        the alien so the caller can ``alien.kill()`` it (and play any
        Stage 8 explosion / SFX, when those land). State clears either
        way: a successful kill clears the lock; a partial or empty
        buffer also clears, mirroring Stage 2's "Enter always resets
        the buffer" feel.

        Returns:
            Alien | None: The alien to remove if its word was just
            completed, otherwise ``None``.
        """
        killed = None
        if (
            self.targeted_alien is not None
            and self.current_prefix == self.targeted_alien.word.upper()
        ):
            killed = self.targeted_alien
        self.current_prefix = ""
        self.targeted_alien = None
        return killed

    def clear_lock(self):
        """Drop both prefix and target without firing.

        Use when the locked alien is removed for a non-typing reason —
        e.g. it falls off the bottom of the screen in Stage 5, or
        external code wants to cancel input. Idempotent.

        Returns:
            None.
        """
        self.current_prefix = ""
        self.targeted_alien = None

    def pick_word(self, in_use):
        """Return a random word not currently held by any on-screen alien.

        Stage 4: ``SpawnDirector`` calls this at every spawn tick to
        pull the next alien's word. Excluding ``in_use`` words keeps
        prefix-locking unambiguous — two aliens carrying the same word
        would force the player to type it twice while only the lowest
        one resolves, which reads as a bug. Duplicate *first letters*
        across aliens are still allowed (the lowest-y tie-break in
        ``_acquire_target`` resolves those) — only full duplicate words
        are filtered.

        Args:
            in_use (Iterable[str]): Words currently displayed on
                screen. Typically built as ``{a.word for a in aliens}``
                at the call site so the manager never has to know
                about the sprite group.

        Returns:
            str | None: A word from the pool not in ``in_use``, or
            ``None`` if every loaded word is currently on screen (or
            the pool is empty). The caller treats ``None`` as "skip
            this spawn tick" rather than as an error.
        """
        in_use_set = set(in_use)
        available = [word for word in self._words if word not in in_use_set]
        if not available:
            return None
        return random.choice(available)

    @staticmethod
    def _load_words(path):
        """Read a one-word-per-line UTF-8 file into a lowercase list.

        Splitting this into a static method keeps ``__init__`` short
        and makes the parsing rule ("alphabetic lines only, lowercased,
        whitespace stripped") testable in isolation. Non-alphabetic
        lines are silently dropped so blank lines and the occasional
        stray punctuation in the source file don't bring down boot —
        the only way a word gets into the pool is by passing
        ``str.isalpha``.

        Args:
            path (str): Filesystem path to the word list.

        Returns:
            list[str]: The lowercased, alpha-only words from the file
            in source order. Order doesn't matter for ``pick_word``
            (it shuffles), but preserving it makes diffs of the file
            easier to reason about during development.
        """
        words = []
        with open(path, 'r', encoding='utf-8') as source:
            for line in source:
                stripped = line.strip().lower()
                if stripped.isalpha():
                    words.append(stripped)
        return words

    def _acquire_target(self, char_upper, aliens):
        """Pick a target whose word starts with ``char_upper``, lowest-y wins.

        Internal helper for ``handle_letter`` only. Splitting it out
        keeps the public method readable and makes the tie-break rule
        a single place to change later.

        Args:
            char_upper (str): Already-uppercased single character.
            aliens (Iterable): Same group passed into ``handle_letter``.

        Returns:
            None. Mutates ``self.targeted_alien`` and
            ``self.current_prefix`` directly.
        """
        # Sort by ``rect.top`` so on a tie (two aliens starting with
        # the same letter, which Stage 3 deliberately avoids but Stage
        # 4+ will produce) the alien further down the screen — the one
        # most about to be missed — is picked. ``rect.top`` is fine for
        # a tie-break key; centery would also work.
        candidates = [
            alien for alien in aliens
            if alien.word.upper().startswith(char_upper)
        ]
        if not candidates:
            return
        candidates.sort(key=lambda a: a.rect.top, reverse=True)
        self.targeted_alien = candidates[0]
        self.current_prefix = char_upper

    @property
    def prefix_length(self):
        """Number of typed letters currently locking the target.

        Sugar for the rendering side of the house — main.py passes
        this into ``Alien.draw_word`` so the targeted alien splits its
        word into typed-prefix (cyan) + untyped-suffix (white) without
        having to know about the manager's internals.

        Returns:
            int: ``len(self.current_prefix)``.
        """
        return len(self.current_prefix)
