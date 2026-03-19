# Gitignore Cleanup for Judge/Cloner Readiness

**Date:** 2026-03-18
**Branch:** 008-uniswap-v3-reactive-integration
**Goal:** Remove noise from the tracked repo so judges and developers cloning see a clean, professional project.

## Audience

Both hackathon/competition judges (evaluating, may not build) and developers who will clone and run `forge build && forge test`.

## Constraints

- Gitignore only — no file deletion. Files remain on disk.
- `app/`, `.planning/`, `skills/`, `kitty-specs/`, `docs/superpowers/` all stay tracked (transparency).
- Research PDFs stay tracked; LaTeX build intermediates get ignored.
- `foundry.lock` stays tracked (reproducible submodule pinning).

## Section 1: Files to Untrack (`git rm --cached`)

| Path | Reason |
|------|--------|
| `notes/SCRATCH.md` | Personal scratch |
| `notes/SCRATCH.md~` | Backup file |
| `docs/usage.md~` | Backup file |
| `specs/notes/DRAFT.md~` | Backup file |
| `specs/notes/DraftEntryIndex.md~` | Backup file |
| `research/model/main.log` | LaTeX build artifact |
| `research/slides/presentation.log` | LaTeX build artifact |

Note: `research/slides/presentation.vrb` is already untracked and will be covered by the new `*.vrb` gitignore pattern.

## Section 2: `.gitignore` Changes

### Fix: Remove stale `docs/` ignore rule

The current `.gitignore` line 11 has `docs/` which blocks new files under `docs/` from being tracked. Since `docs/` is heavily tracked (102 files) and should remain visible, **remove the `docs/` line entirely**. The original `docs/` rule was from the Forge default `.gitignore` (for `forge doc` output) and is no longer appropriate.

### Fix: Remove `!research/**/*.log` exception

Remove this negation so LaTeX `.log` files in `research/` are caught by the existing global `*.log` pattern (line 112).

### New entries to add

The following patterns are genuinely new (not already covered by existing global patterns):

```gitignore
# Personal scratch
notes/

# LaTeX .vrb artifacts (not covered by existing global patterns)
*.vrb

# Python egg-info
*.egg-info/

# Stray venvs
list/
```

Note: `scripts/.env` is already covered by the existing global `.env` rule (line 78). The existing global patterns `*.aux`, `*.bbl`, `*.blg`, `*.toc`, `*.nav`, `*.snm`, `*.out` already cover those LaTeX intermediates — no additional `research/**/*.xxx` entries needed. The existing `notes.md` rule (line 81) covers the file; the new `notes/` rule covers the directory.

## Section 3: Post-Cleanup Repo Structure

```
src/                    # Core Solidity contracts (72 files)
test/                   # Forge tests (49 files)
research/               # Python pipeline + LaTeX .tex + .pdf outputs
specs/                  # Contract specifications
docs/                   # Architecture, diagrams, plans
app/                    # Frontend application
foundry-script/         # Deployment scripts
scripts/                # Shell scripts + .env.example
.planning/              # GSD roadmap/phases
skills/                 # Claude skill definitions
kitty-specs/            # Kittify specs
assets/                 # Logo SVGs
lib/                    # Git submodules
.github/                # CI workflow
```

Root files: `README.md`, `CLAUDE.md`, `Makefile`, `foundry.toml`, `foundry.lock`, `remappings.txt`, `pyproject.toml`, `uv.lock`, `conftest.py`, `.gitignore`, `.gitmodules`

## Impact

- 7 files removed from tracking
- 0 files deleted from disk
- Future noise (LaTeX intermediates, egg-info, stray venvs, secrets) prevented
