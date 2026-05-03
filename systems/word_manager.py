"""Typing input + prefix-locking state machine.

Stage 3 introduces ``WordManager`` — the small piece of game state that
turns a stream of letter keypresses into "which alien is the player
currently typing at, and how far into its word are they?" This replaces
the inline ``current_input`` string main.py used in Stage 2.

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
split read from the same string without re-uppercasing per frame.
"""


class WordManager:
    """Owns the active typing prefix and the locked alien (if any).

    The manager is intentionally storage-only — it never touches pygame
    or the screen. ``main.py`` feeds it KEYDOWN events and asks it for
    its current state when rendering. That keeps the input/state
    separation that the Refactoring Rules in ``docs/TESTING.md`` ask
    for, and makes the manager unit-testable without spinning up a
    display.
    """

    def __init__(self):
        """Initialize an empty manager: no prefix, no target."""
        # ``current_prefix`` is stored uppercase so callers can blit it
        # directly (per Q7's project-wide uppercase rule) and so prefix
        # comparisons against ``alien.word.upper()`` don't have to
        # re-case on every keystroke.
        self.current_prefix = ""
        self.targeted_alien = None

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
