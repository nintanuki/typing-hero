# Testing Checklist

Run this after major changes to ensure nothing broke:

* Start game successfully

# Refactoring Rules
* Update CHANGELOG.md for every code change (timestamp, file, line numbers, before/after, why) including which AI model made the change. Read it first before making changes so you know the current state.
* All code must be PEP-8 compliant.
* Less code is better than more code, but clean and readable code is the best.
* Keep "middlemen" minimal, if A calls B, and all B does is call C, A should just call C
* Keep code clean of dead imports, unused variables and functions, and legacy code.
* GameManager must be light, offload responsibilities to other classes
* When possible classes should comminicate to eachother through GameManager.
* Any new names for classes and functions must be clear regarding it's function
* Keep all constants declared in settings.py, avoid magic numbers
* All classes and functions must have a docstring.
* All docstrings must have a summary, Args (if applicable) and Returns (if applicable)
* Do not change function names (unless their role is now completely different)
* Keep functions organized and grouped by role. The update and run functions in classes should be the last function, and do as little as possible. Only call other functions if possible.
* Do not change variable names if not necessary.
* Function names and variable names must be descriptive.
* Do not remove comments.
* Comments must explain why, not just what.
* When making a change, do not leave a comment that a change was made, unless it was to fix a bug that wasn't obvious and to explain why something was done in an unconventional way.