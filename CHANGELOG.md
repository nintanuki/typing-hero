# Change Log

This file is an append-only record of every code change made to Dungeon Digger
by a human, AI assistant, or copilot tool. Read it before making changes so you
know the current state of the codebase.

## Format

Each entry covers one logical change (which may touch multiple files). Use the
template below, with one `**File:** ... **Why:** ...` block per file touched.

    ## YYYY-MM-DD HH:MM — short summary

    **File:** path/to/file.py
    **Lines (at time of edit):** 38-52 (modified)
    **Before:**
        [old code]
    **After:**
        [new code]
    **Why:** explanation

## Conventions

* Line numbers reflect the file as it existed at the moment of the edit. Edits
  above shift line numbers below, so older entries will not match the current
  file. Never go back and "fix" old line numbers.
* Entries are append-only. Never delete history. If a later edit reverts an
  earlier one, write a new entry that references the original.
* For new files, write `(new file)` instead of a line range. The "Before"
  block can be omitted or marked `(file did not exist)`.
* For deletes, write `(deleted)` and put the removed code in "Before" with no
  "After" block.
* Keep "Before" / "After" blocks short. If a change is huge, summarize with a
  diff-style excerpt of the most important lines plus a sentence describing the
  rest, instead of pasting the entire file.
  
## 2026-05-02 23:18 UTC — Date+time format and TODO restructure

**File:** docs/CHANGELOG.md
**Date and Time:** 2026-05-02 23:18 UTC
**Lines (at time of edit):** 716-746 (Format + Conventions sections rewritten)
**Before:**
    ## Format
    ...
        ## YYYY-MM-DD HH:MM — short summary
        **File:** path/to/file.py
        **Date and Time* e.g. 5/2/2026 @ 3:43PM
        ...
    ## Conventions
    [no rule about timezones; older entries use date-only headers and a mix
     of `5/2/2026` US-style values for the per-file `Date and Time` field —
     no entry to date has ever included an actual clock time]
**After:**
    ## Format
    ...
        ## YYYY-MM-DD HH:MM TZ — short summary
        **File:** path/to/file.py
        **Date and Time:** YYYY-MM-DD HH:MM TZ
        ...
    ### Date and time format
    [requires ISO 8601 date + 24-hour clock + timezone abbreviation, e.g.
     `2026-05-02 16:18 PDT`, on BOTH the section header and per-file field]
    ## Conventions
    [+ rule: pre-2026-05-02 entries are not retroactively edited]
**Why:** The old template promised "Date and Time" but every real entry
filled it with a date-only `5/2/2026` value (US-style, ambiguous, not
sortable as text), and the section header was inconsistent — sometimes
ISO date, never a clock time. Two problems compound: (1) collaborators
in different timezones can't sort the file deterministically; (2) within
a single working session several entries land within minutes of each
other and the day-only stamp can't tell them apart. ISO 8601 with a
24-hour clock and timezone abbreviation fixes both, and is the format
most engineering teams settle on for this exact reason. Per-file field
stays alongside the header on purpose — a single logical change can span
hours when it touches three files, and the per-file timestamp pinpoints
when each landed. Old entries are explicitly grandfathered: backfilling
guesses would be worse than leaving the gap visible.
**Editor:** Claude (Opus 4.7, via Cowork)