# Copilot Instructions for Typing Hero

These rules apply to **every** editor of this codebase, human or AI. They are not suggestions. Read this file before each session.

---

## Required reading order (before any change)

1. [README.md](../README.md) — what the project is and how to run it.
2. [docs/TODO.md](../docs/TODO.md) — current phase and roadmap.
3. [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — how the code actually works.
4. [docs/TESTING.md](../docs/TESTING.md) — per-stage smoke tests + cross-cutting checks.
5. [docs/CHANGELOG.md](../docs/CHANGELOG.md) — most recent entries, so you know the current state.
6. The source files relevant to your task.

If a question is asked about *why* code was written a certain way, that is a request for an **explanation**, not a request for a code change. Do not modify code unless the user explicitly asks for a change.

---

## Required actions (after any change)

- **Append an entry to [docs/CHANGELOG.md](../docs/CHANGELOG.md)** following the format defined at the top of that file (ISO 8601 timestamp with timezone, per-file timestamp, file path, line numbers at time of edit, before/after blocks, why, and editor name including the AI model used). Do not duplicate the format spec here — the changelog itself is the single source of truth for its own format.
- **If the change altered how a system works, update the matching section of [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).** Out-of-date architecture docs are worse than none.
- **If the change completes or advances a roadmap item, update [docs/TODO.md](../docs/TODO.md)** (mark `[x]`, do not delete — leave as a record).
- **Run the relevant section of [docs/TESTING.md](../docs/TESTING.md) mentally** before claiming the change is done.

---

## Code style

- All Python code must be PEP-8 compliant.
- Less code is better; clean and readable is best.
- Prefer clear names over short ones. New class and function names must clearly describe their purpose.
- Do not change function or variable names unless the role has *completely* changed.
- Keep code free of dead imports, unused variables, unused functions, and legacy code.

## Architecture rules

- `GameManager` (in `main.py`) must stay thin. Its job is to own the display, drain events, route them to handlers, and call `_update` / `_draw` on the systems it owns. Offload everything else to dedicated classes.
- Classes communicate through `GameManager` where possible. Avoid systems reaching directly into each other.
- Keep middlemen minimal: if A calls B and B only calls C, have A call C directly.
- All constants live in `settings.py`. **No magic numbers anywhere else.** When adding a constant, include a comment explaining its units and effect.

## File and function layout

- Inside a class, group functions by role (boot/lifecycle, gameplay actions, audio, event handling, per-frame update/render, etc.).
- `update`, `_update`, and `run` go **last** and should only call other functions on the class — they are coordinators, not implementations.
- Separate logical sections inside a file with an all-caps banner comment, exactly this style:

  ```python
      # -------------------------
      # SECTION NAME
      # -------------------------
  ```

  Match the leading indentation of the surrounding class body. Keep the dashes the same length and the name in ALL CAPS. Existing files (e.g. `main.py`) already use this style. New code must follow it; existing code need not be retrofitted in a single pass — update banners as you touch the surrounding section.

## Comments and docstrings

- Every class and function must have a docstring with a one-line summary, plus `Args:` / `Returns:` blocks when applicable.
- Do not remove docstrings. Update them in place if behavior changes.
- Do not remove comments unless they are inaccurate; prefer updating them.
- Comments must explain **why**, not just what.
- Do not leave comments noting that a change was made, unless they explain a non-obvious bug fix or unconventional code.

## UI text

- **ALL text displayed to the user must be ALL CAPS.** Every string passed to `font.render` (or to a HUD class that renders it) must be `.upper()`'d before it hits the screen — alien words, typing buffer, score row, initials, menu prompts, all of it. A bare `font.render(some_string, ...)` without `.upper()` is a bug.

## Working with `legacy/`

- Treat `legacy/` as **read-only reference**. Anything inside it is the frozen Star Hero codebase that Typing Hero grew out of. Do not edit files there.
- When porting a subsystem, read specific classes with grep + read at a line range — never load a full legacy file into context.
- The `legacy/` folder will be deleted once it has no more reference value.

---

## Mental smoke-test checklist (run after any meaningful change)

This is the fast gut-check. The full per-stage playbook lives in [docs/TESTING.md](../docs/TESTING.md).

- Game boots to the title screen without tracebacks.
- `Enter` starts a run, `ESC` exits cleanly, `F11` toggles fullscreen.
- Typing updates the buffer and uses soft-lock targeting for ambiguous prefixes (lowest matching alien gets provisional focus).
- Completing a word destroys the correct alien and increments score by color (red 100 / green 200 / yellow 300 / blue 500 — verify by `AlienSettings.POINTS`).
- Misses reduce hearts (or strip powerups first when active); zero hearts transitions to game-over.
- If the score qualifies, initials entry works with arrow keys + `Enter`.
- `Enter` toggles pause during gameplay; the active music channel pauses/resumes with it.
- Intro / BGM / game-over music and core SFX (`laser`, `explosion`, `hyper`, alarms) still fire at the expected events.
- No new magic numbers leaked outside `settings.py`.
