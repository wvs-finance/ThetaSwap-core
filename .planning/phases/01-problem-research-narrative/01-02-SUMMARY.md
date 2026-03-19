---
phase: 01-problem-research-narrative
plan: 02
subsystem: research
tags: [matplotlib, publication-plots, backtest, notebooks, beamer]

# Dependency graph
requires:
  - phase: 01-problem-research-narrative
    provides: narrative markdown files (01-01)
provides:
  - set_publication_style() function in research/backtest/plotting.py
  - 4 publication-style PNGs in research/figures/ at 300 DPI
  - backtest/sweep.py trigger-based insurance module
affects: [03-root-readme-research-readme-demo, 04-beamer-slides]

# Tech tracking
tech-stack:
  added: []
  patterns: [publication rcParams module, figure export cells in notebooks]

key-files:
  created:
    - research/figures/dose-response.png
    - research/figures/trigger-days.png
    - research/figures/alpha-sweep.png
    - research/figures/reserve-dynamics.png
    - research/backtest/sweep.py
  modified:
    - research/backtest/plotting.py
    - research/notebooks/eth-usdc-insurance-demand-identification.ipynb
    - research/notebooks/eth-usdc-backtest.ipynb

key-decisions:
  - "usetex disabled: system lacks type1ec.sty (cm-super); serif font fallback provides consistent typography"
  - "Created backtest/sweep.py to restore missing trigger-based insurance API referenced by notebook"

patterns-established:
  - "Publication rcParams: call set_publication_style() at notebook top before any plotting"
  - "Figure export: save PNGs to research/figures/ via Path('..') / 'figures' from notebooks"

requirements-completed: [PROB-01, PROB-02, PROB-03]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 1 Plan 02: Publication Plots Summary

**4 publication-style PNGs (dose-response, trigger-days, alpha-sweep, reserve-dynamics) generated at 300 DPI with serif fonts, plus set_publication_style() rcParams module for Beamer-compatible typography**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T21:56:16Z
- **Completed:** 2026-03-18T22:01:16Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added `set_publication_style()` and `PUBLICATION_RCPARAMS` dict to `research/backtest/plotting.py`
- Updated both notebooks with figure export cells that save PNGs to `research/figures/`
- Generated all 4 required PNGs: dose-response (133K), trigger-days (90K), alpha-sweep (243K), reserve-dynamics (205K)
- Created `backtest/sweep.py` restoring the trigger-based insurance API (Rule 3 auto-fix)
- All 78 existing backtest tests pass unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Add publication rcParams and figure export cells** - `88ea2d8` (feat)
2. **Task 1 fix: Fix import order and add missing sweep module** - `fe41ab5` (fix)
3. **Task 2: Generate 4 publication PNGs** - `ef91c3d` (feat)

## Files Created/Modified
- `research/backtest/plotting.py` - Added PUBLICATION_RCPARAMS dict and set_publication_style() function
- `research/backtest/sweep.py` - Trigger-based insurance backtest (run_single_backtest, run_gamma_sweep)
- `research/notebooks/eth-usdc-insurance-demand-identification.ipynb` - Added pub style import + dose-response export cell
- `research/notebooks/eth-usdc-backtest.ipynb` - Added pub style import + 3 figure export cells
- `research/figures/dose-response.png` - Q1-Q4 exit rates by deviation quartile showing inverted-U
- `research/figures/trigger-days.png` - Daily delta-plus bar chart with threshold line at 0.09
- `research/figures/alpha-sweep.png` - % better off and mean HV vs tail exponent, HV distribution at alpha=2
- `research/figures/reserve-dynamics.png` - Seeded reserve trajectories at calibrated gamma

## Decisions Made
- usetex disabled due to missing type1ec.sty (cm-super package); serif font fallback used instead. Enable usetex when cm-super is installed for exact Computer Modern typography matching Beamer.
- Created `backtest/sweep.py` as a new module (not a shim) implementing trigger-based INS-05 insurance mechanism. The notebook referenced `backtest.sweep` which was removed during a prior API refactor; the notebook had stale cached outputs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing backtest.sweep module**
- **Found during:** Task 2 (notebook execution)
- **Issue:** Backtest notebook imports `from backtest.sweep import run_single_backtest, run_gamma_sweep` but no `sweep.py` module exists. The API was removed during a prior refactor; notebook had stale cached outputs.
- **Fix:** Created `research/backtest/sweep.py` implementing the trigger-based insurance mechanism (INS-05) using existing `pnl.py` and `types.py` infrastructure.
- **Files modified:** research/backtest/sweep.py (new)
- **Verification:** `PYTHONPATH=research uhi8/bin/python -c "from backtest.sweep import run_single_backtest, run_gamma_sweep"` succeeds; notebook executes headless without errors.
- **Committed in:** fe41ab5

**2. [Rule 1 - Bug] Notebook import order**
- **Found during:** Task 2 (notebook execution)
- **Issue:** `set_publication_style()` import was placed before `sys.path.insert(0, "..")` in both notebooks, causing ModuleNotFoundError during headless execution.
- **Fix:** Moved publication style import after sys.path setup.
- **Files modified:** Both notebooks
- **Verification:** Both notebooks execute headless via nbconvert without errors.
- **Committed in:** fe41ab5

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for notebook execution. No scope creep.

## Issues Encountered
- usetex rendering fails with `RuntimeError: latex was not able to process string` due to missing `type1ec.sty`. Fell back to serif fonts as specified in the plan's fallback path. PNGs still have clean publication style.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 PNGs ready for Phase 3 (README) consumption via `\includegraphics` or markdown `![](research/figures/...)`
- All 4 PNGs ready for Phase 4 (Beamer) consumption via `\graphicspath`
- To enable exact Computer Modern typography: install `texlive-fontsextra` (provides cm-super/type1ec.sty) and set `PUBLICATION_RCPARAMS["text.usetex"] = True`

---
*Phase: 01-problem-research-narrative*
*Completed: 2026-03-18*
