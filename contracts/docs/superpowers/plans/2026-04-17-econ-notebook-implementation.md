# Structural Econometrics Notebook Implementation Plan (rev 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the three-notebook Jupyter pipeline (NB1 EDA, NB2 estimation, NB3 tests+sensitivity) specified in `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` (rev 2), producing the Layer 1 → Layer 2 handoff JSON, the gate verdict, and the auto-generated exec-layer README.

**Architecture:** Three notebooks backed by a thin `cleaning.py` wrapper over `econ_query_api`, with CI-enforced purity and citation-block linting. NB1 emits a panel fingerprint and decision ledger; NB2 emits JSON + pickle handoff artifacts with full covariance matrices and bootstrap-residuals; NB3 consumes both and writes the gate verdict consumed by a Jinja2-rendered README. No code in this plan — every task dispatches a specialized subagent with a prose specification.

**Tech Stack:** Python 3.12+, DuckDB 1.5+, statsmodels, arch, scipy, pandas, numpy, matplotlib, specification_curve, Jinja2, jupyter + nbconvert, bibtexparser, ruptures (fallback: statsmodels breaks_cusumolsresid), just (existing worktree justfile).

**Revision history:** Rev 2 (2026-04-17) — applied fixes from three-way plan review (Senior PM + Reality Checker + Code Reviewer): split Tasks 1/13/18/26 into sub-tasks; added X-trio checkpoint protocol per new memory rule; fixed Task 4 failing-test logic; locked Task 16 ladder highlight; redefined Task 20 reconciliation rule; raised nbconvert timeout; added pre-commit install + shared conftest + null-policy manifest + determinism assertion + strict-agnosticism grep test; reassigned Task 5 subagent; swapped Task 21 (now 23) reviewer trio; added 5 papers (AHXZ 2006, Ederer-Nordhaus 2020, Belsley-Kuh-Welsch 1980, Elliott-Rothenberg-Stock 1996, Kwiatkowski 1992) to references.bib; locked test-file naming convention; approved worktree-root `justfile` scope expansion.

---

## Non-Negotiable Rules (enforced on every task)

1. **Strict TDD.** Every task writes a failing test first, verifies the failure, implements minimally, verifies the pass, then commits. Never write implementation before an observably failing test.
2. **Specialized subagent per task.** Foreground orchestrates and verifies; never authors. Each task below names exactly one subagent.
3. **X-trio checkpoint for notebook authoring.** Every task that dispatches a subagent to write notebook cells follows the Notebook Authoring Protocol below. Bulk authoring forbidden.
4. **Scripts-only scope (with worktree-root `justfile` exception).** Pipeline work touches `contracts/notebooks/`, `contracts/scripts/`, `contracts/data/`, `contracts/.gitignore`, and the worktree-root `justfile` (for the `notebooks:` recipe only — user-approved scope expansion). Never `src/`, `test/*.sol`, `foundry.toml`, or any Solidity.
5. **Query API is the only data interface.** All notebook data access flows through `cleaning.py`, which itself calls only `econ_query_api.py`. Raw SQL in notebook cells forbidden.
6. **Citation block before every decision/test/fit.** Four parts: reference, why used, relevance to results, connection to Layer 2. Enforced by the pre-commit lint from Task 5.
7. **Chasing-offline rule.** Spec searching, model comparison, and rejected alternatives live in the Analytics Reporter's private scratch — never in the committed notebook. Every three-way review charter (Tasks 15, 23, 31) includes an explicit reviewer checklist item asserting the notebook contains no forbidden phrases ("we tried", "rejected in favor of", "we chose … over", "this didn't work"); the pre-commit citation lint from Task 5 ALSO greps NB1/NB2/NB3 markdown cells for these substrings and fails the commit on match.
8. **Push origin, not upstream.** `origin` = JMSBPP. Never push to `upstream` (wvs-finance).
9. **Real data over mocks.** Tests hit real DuckDB and real fixtures; mocks allowed only for HTTP errors that cannot be reproduced or mid-execution hooks (e.g., atomic-emit exception injection).
10. **Test-file naming convention.** `contracts/scripts/tests/test_nb{N}_section{FIRST}[_{LAST}].py` for notebook section tests; `contracts/scripts/tests/test_<module>.py` for module tests.
11. **Artifact path constants.** All inter-task artifact paths reference constants exported from `env.py` (`DUCKDB_PATH`, `ESTIMATES_DIR`, `FIGURES_DIR`, `PDF_DIR`, `FINGERPRINT_PATH`, `POINT_JSON_PATH`, `FULL_PKL_PATH`, `GATE_VERDICT_PATH`, `READMEPath`). No bare string paths in notebooks or tests.

---

## Notebook Authoring Protocol (X-trio checkpoint)

Every task that dispatches a subagent to author notebook cells proceeds trio by trio:

**Trio = (why-markdown cell) + (code cell) + (interpretation-markdown cell)**

1. The subagent writes one markdown cell containing the four-part citation block. The "Why used" part explains WHY the next code cell runs and satisfies the why-markdown requirement.
2. The subagent writes the code cell.
3. The subagent executes the code cell and verifies it runs without error.
4. The subagent writes one markdown cell interpreting the specific results the code cell just produced.
5. The subagent HALTS and requests human review before authoring the next trio.

Bulk authoring of multiple trios in a single dispatch is forbidden. Each task may contain many trios; the subagent reports trio-by-trio and waits for approval to proceed.

Infrastructure tasks (scaffold, lint scripts, env.py, references.bib, justfile recipe, templates, CI tests) are exempt — they are not notebook-authoring tasks.

---

## Phase 0 — Shared Infrastructure

### Task 1a: Notebook folder scaffold + `.gitignore` scoped rules

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/.gitkeep`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/figures/.gitkeep`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/pdf/.gitkeep`
- Modify: `contracts/.gitignore`

- [ ] **Step 1: Write the failing test.** `contracts/scripts/tests/test_scaffold.py` asserts: the five folders exist under `contracts/notebooks/fx_vol_cpi_surprise/Colombia/`; `contracts/.gitignore` contains scoped rules for `contracts/notebooks/fx_vol_cpi_surprise/**/estimates/*.pkl`, `contracts/notebooks/fx_vol_cpi_surprise/**/pdf/`, and `contracts/notebooks/fx_vol_cpi_surprise/**/_nbconvert_template/**/*.aux` (not global `*.pkl`).
- [ ] **Step 2: Run the test and confirm failure.** Expected: folders missing, ignore rules absent.
- [ ] **Step 3: Create the folders + gitkeeps; extend `.gitignore` with the three scoped rules.**
- [ ] **Step 4: Run the test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): notebook folder scaffold + scoped gitignore`.

### Task 1b: `env.py` — path constants + required packages + seed helper + nbconvert timeout

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py`
- Create: `contracts/scripts/tests/conftest.py` (shared DuckDB `conn` fixture)
- Create: `contracts/scripts/nb2_serialize.py` (stub — full implementation arrives in Task 22)
- Test: `contracts/scripts/tests/test_env.py`

- [ ] **Step 1: Write the failing test.** Assert `env` exposes: `DUCKDB_PATH` (absolute path string to `contracts/data/structural_econ.duckdb`), `ESTIMATES_DIR`, `FIGURES_DIR`, `PDF_DIR`, `FINGERPRINT_PATH`, `POINT_JSON_PATH`, `FULL_PKL_PATH`, `GATE_VERDICT_PATH`, `READMEPath`, `NBCONVERT_TIMEOUT` (default 1800), `REQUIRED_PACKAGES` dict containing at minimum the keys `statsmodels`, `arch`, `numpy`, `pandas`, `duckdb`, `scipy`, `jinja2`, `bibtexparser`, `specification_curve`, `ruptures`, `nbformat`, `jupyter`, `matplotlib`, each with a semantic-version-pin string (major.minor form). Assert `pin_seed(seed:int)` sets `numpy.random`, `random`, and `PYTHONHASHSEED` deterministically. Assert that version pins match exactly what `pip freeze` reports in the current venv (the test reads `pip freeze` and compares). Assert the shared `conn` fixture in `conftest.py` yields a DuckDB connection pointing at `DUCKDB_PATH` and cleans up after each test.
- [ ] **Step 2: Run the test and confirm failure.** Expected: module not found.
- [ ] **Step 3: Implement `env.py`.** Version pins are derived from `pip freeze` in the current venv at authoring time and written in exactly that major.minor form; the versions-must-match assertion in the test guards against drift.
- [ ] **Step 4: Implement `conftest.py`** with a session-scoped `conn` fixture yielding a fresh DuckDB connection each test session.
- [ ] **Step 5: Create the `nb2_serialize.py` stub** — a single module docstring pointing to Task 22 for implementation; no executable code yet. This reserves the import path so later tasks can reference it without a new Phase 0 task.
- [ ] **Step 6: Run the test and confirm pass.**
- [ ] **Step 7: Commit** with message `feat(fx-vol-econ): env.py + conftest + nb2_serialize stub`.

### Task 1c: Empty `.ipynb` skeletons

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/README.md` (placeholder text, overwritten by Task 30)
- Test: `contracts/scripts/tests/test_notebook_skeletons.py`

- [ ] **Step 1: Write the failing test.** Asserts each `.ipynb` is valid `nbformat.v4` with: (a) a title markdown cell naming the notebook; (b) a "Gate Verdict" admonition-style markdown cell with placeholder text "populated after NB2 and NB3"; (c) zero code cells; (d) the placeholder README contains a single line pointing to Task 30 for auto-render.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author skeletons using `nbformat`.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): notebook skeletons + placeholder README`.

### Task 1d: `justfile` `notebooks` recipe

**Subagent:** Data Engineer

**Files:**
- Modify: `justfile` (worktree root — approved scope expansion per Non-Negotiable Rule 4)
- Test: `contracts/scripts/tests/test_just_notebooks_recipe.py`

- [ ] **Step 1: Write the failing test.** Asserts `just --list` from the worktree root includes a `notebooks` entry; asserts `just notebooks --dry-run` (or the runner's equivalent) prints a command sequence that runs `jupyter nbconvert --execute --to notebook --inplace` on NB1 → NB2 → NB3 in order, then `--to pdf` for each, using the `NBCONVERT_TIMEOUT` from `env.py`.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Add the recipe to the worktree-root `justfile`.** Comment the recipe explaining the scope expansion rationale (references this plan's Rule 4).
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): just notebooks recipe with 1800s timeout`.

### Task 2: references.bib scaffold

**Subagent:** Technical Writer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/references.bib`
- Test: `contracts/scripts/tests/test_references_bib.py`

- [ ] **Step 1: Write the failing test.** The test parses `references.bib` with `bibtexparser` and asserts presence of entries for every reference listed in design spec §14 PLUS the five papers cited by downstream tasks that the design spec §14 does not yet list: Andersen-Bollerslev-Diebold-Ebens 2001 JFE, Andersen-Bollerslev-Diebold-Vega 2003 AER, Ang-Hodrick-Xing-Zhang 2006 JFE (VIX as global risk), Ankel-Peters-Brodeur 2024 Q Open, Bai-Perron 1998 Econometrica, Bai-Perron 2003 JAE, Balduzzi-Elton-Green 2001 JFQA, Barone-Adesi 2008 JBF, Belsley-Kuh-Welsch 1980 (VIF diagnostics), Bollerslev 1986 JE, Bollerslev-Wooldridge 1992 (QMLE), Breusch-Pagan 1979 Econometrica, Campbell-Lo-MacKinlay 1997, Chow 1960 Econometrica, Conover-Johnson-Johnson 1981 Technometrics, Conrad-Schoelkopf-Tushteva 2025, Durbin-Watson 1951 Biometrika, Ederer-Nordhaus 2020 Energy Economics (WTI negative price), Elliott-Rothenberg-Stock 1996 Econometrica (DF-GLS), Engle-Rangel 2008 RFS, Fuentes-Pincheira-Julio-Rincón 2014 BIS 462, Han-Kristensen 2014 JBES, Hansen-Lunde 2005 JAE, Heston-Nandi 2000 RFS, Jarque-Bera 1987 Int Stat Rev, Kwiatkowski-Phillips-Schmidt-Shin 1992 JE (KPSS), Levene 1960, Ljung-Box 1978 Biometrika, Mincer-Zarnowitz 1969, Newey-West 1987 Econometrica, Politis-Romano 1994 JASA, Rincón-Torres-Rojas-Silva-Julio-Román 2021 (BanRep Borrador 1171), Simonsohn-Simmons-Nelson 2020 Nature Human Behaviour, Wilson-Hilferty 1931 PNAS. For Han-Kristensen the test also asserts `journal = {Journal of Business & Economic Statistics}`.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Populate `references.bib`** with BibTeX entries for all 34 references. DOIs where available; URLs as fallback. Unique keys following `authorYEARkeyword` convention.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): references.bib — 34 entries`.

### Task 3: Panel fingerprint utility

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/panel_fingerprint.py`
- Test: `contracts/scripts/tests/test_panel_fingerprint.py`

- [ ] **Step 1: Write the failing test.** Three cases: (a) deterministic fingerprint — calling twice on the same DataFrame returns byte-identical output; (b) order-invariance — two DataFrames with identical content but shuffled row order produce identical fingerprints (function sorts by the named date column internally); (c) drift detection — changing a single value changes the sha256 field.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement `panel_fingerprint.py`.** Pure function; takes DataFrame + date-column name; returns a dict with: row count, column count, column-dtype mapping (sorted), min and max date as ISO strings, sha256 of the DataFrame serialized as CSV sorted by the date column. No I/O.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): panel fingerprint utility`.

### Task 4: `cleaning.py` purity CI lint

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/tests/test_cleaning_purity.py`
- Create: `contracts/scripts/tests/fixtures/cleaning_violator.py` (synthetic violator for self-test)
- Create: `contracts/scripts/tests/fixtures/cleaning_clean.py` (synthetic pure module for self-test)

- [ ] **Step 1: Write the failing test.** Against the TWO synthetic fixtures (not the real cleaning.py, which doesn't yet exist): assert the lint logic classifies the violator fixture as a violation (it contains `conn.execute(...)`) AND classifies the clean fixture as pure (it only calls `econ_query_api` functions). Use `importlib` to load the fixtures and source-text grep for the forbidden patterns: DuckDB execute calls, SQL-string invocation, pandas read-SQL, direct DuckDB connection construction. The test does NOT yet assert anything about the real `cleaning.py`.
- [ ] **Step 2: Run the test and confirm failure.** Expected: either fixtures missing, or the lint logic does not correctly distinguish the two cases.
- [ ] **Step 3: Create the two synthetic fixtures + implement the lint logic inside the test.** The violator fixture must import from `econ_query_api` and also call `conn.execute(...)` directly. The clean fixture only wraps `econ_query_api`.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): cleaning.py purity lint with two synthetic fixtures`.

Task 14 (NB1 cleaning.py implementation) adds a new assertion block to this test that activates against the real `cleaning.py`; re-running this test suite is a step in Task 14.

### Task 5: Citation-block pre-commit lint + chasing-offline grep

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/lint_notebook_citations.py`
- Create: `contracts/scripts/tests/test_lint_notebook_citations.py`
- Create: `contracts/scripts/tests/fixtures/nb_citation_valid.ipynb`
- Create: `contracts/scripts/tests/fixtures/nb_citation_missing_connection.ipynb`
- Create: `contracts/scripts/tests/fixtures/nb_no_gated_cells.ipynb`
- Create: `contracts/scripts/tests/fixtures/nb_chasing_offline_violation.ipynb`
- Modify: `contracts/.pre-commit-config.yaml` (create if absent)
- Modify: `contracts/requirements.txt` (add `pre-commit` if absent)

- [ ] **Step 1: Write the failing test.** Six cases: (a) valid fixture with all four citation-block parts → exit 0; (b) missing "Connection to simulator" → exit 1 with a specific error string; (c) no gated cells → exit 0 (nothing to gate); (d) gated cell not preceded by any markdown within 2 cells → exit 1; (e) fixture containing a forbidden chasing-offline phrase ("we tried X", "rejected in favor of Y") in a markdown cell → exit 1 with a distinct error code; (f) running `pre-commit run --all-files` on a staging copy of the repo invokes the lint via the pre-commit hook configuration.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement `lint_notebook_citations.py`** as a CLI that parses `.ipynb` files with `nbformat`, identifies gated code cells (containing fit patterns matching `OLS(`, `arch_model(`, `scipy.stats.levene`, `scipy.stats.jarque_bera`, `scipy.stats.shapiro`, `TLinearModel`, `arch_bootstrap`, or a cell-tag marker `Decision #N`), walks back up to two markdown cells for the four required headers, AND greps every markdown cell (regardless of gating) for the chasing-offline forbidden substrings. Exit non-zero on any violation.
- [ ] **Step 4: Add the pre-commit hook configuration** scoped to `.ipynb` under `contracts/notebooks/fx_vol_cpi_surprise/`. Add `pre-commit` to requirements.txt.
- [ ] **Step 5: Add an explicit activation step to this task** — after the tests pass, run `pre-commit install` in the repo so subsequent commits auto-run the hook. The test asserts the `.git/hooks/pre-commit` symlink exists.
- [ ] **Step 6: Run and confirm pass.**
- [ ] **Step 7: Commit** with message `feat(fx-vol-econ): citation-block + chasing-offline pre-commit lint`.

### Task 6: nbconvert LaTeX template enforcing `remove-input` tags

**Subagent:** Technical Writer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/_nbconvert_template/article.tex.j2`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/_nbconvert_template/jupyter_nbconvert_config.py`
- Test: `contracts/scripts/tests/test_nbconvert_template.py`

- [ ] **Step 1: Write the failing test.** The test constructs a minimal `.ipynb` with one code cell tagged `remove-input`, one code cell without the tag, one markdown cell. It runs `jupyter nbconvert --to latex --template <path>` against the template. Asserts the LaTeX output contains the markdown text, contains the output of the un-tagged cell, but does NOT contain the source text of the tagged cell. Asserts the config pins `ExecutePreprocessor.timeout` to the value of `env.NBCONVERT_TIMEOUT` (1800).
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Create the LaTeX template** by extending jupyter's default `article` template with a Jinja2 override that suppresses cell input for cells tagged `remove-input`, keeping outputs visible. Companion `jupyter_nbconvert_config.py` pins the timeout by reading `env.NBCONVERT_TIMEOUT`.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): nbconvert template — hide utility cells, 1800s timeout`.

---

## Phase 1 — NB1 Data EDA

Every NB1 task dispatches **Analytics Reporter** and follows the X-trio checkpoint protocol: the subagent produces one trio (why-markdown + code + interpretation), executes, then HALTS for human review before the next trio.

### Task 7: NB1 §1 Setup + Data Availability Statement

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section1.py`

- [ ] **Step 1: Write the failing test.** Executes the notebook headless up through §1 only (via a cell tag filter `section:1`) using `nbformat` + `nbclient`. Asserts via `nb.cells[i].outputs` and `nb.cells[i].source` that the executed output contains: (a) a manifest table with one row per raw source (TRM, IBR, intervention, FRED daily, FRED monthly, DANE IPC, DANE IPP, DANE calendar, BLS calendar); (b) a date-coverage table per `econ_query_api._DATE_TABLES`; (c) a Data Availability Statement markdown block following the Social Science Data Editors template; (d) a "Gate Verdict" admonition with placeholder text.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §1 per the X-trio protocol.** Trio 1 covers manifest + DAS; trio 2 covers date coverage; Analytics Reporter HALTS after each for human review. Citation blocks reference the Social Science Data Editors template and Ankel-Peters-Brodeur 2024.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §1 setup + DAS + coverage`.

### Task 8: NB1 §2 Panel Construction Audit + Decision #1

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section2.py`

- [ ] **Step 1: Write the failing test.** Via nbformat on cells tagged `section:2`. Asserts: (a) a panel-completeness DataFrame for weekly_panel and daily_panel (`get_panel_completeness()`); (b) an empirical sample-start determination from coverage overlap of TRM, IBR, IPC, IPP, FRED; (c) a Decision #1 markdown cell with the four-part citation block, citing Rincón-Torres-Rojas-Silva-Julio-Román 2021 for Colombian FX sample conventions, locking the sample window.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §2 per the X-trio protocol.** One trio per substantive output (completeness table, coverage overlap, decision anchor). Halt per trio.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §2 panel audit + Decision #1`.

### Task 9: NB1 §3 LHS EDA + Decisions #2-3 (+ strict-agnosticism test)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section3.py`

- [ ] **Step 1: Write the failing test.** Via nbformat on cells tagged `section:3`. Asserts: (a) three standalone figure blocks for raw RV, log(RV), RV^{1/3} — each figure must contain axis labels (x-axis `week_start`, y-axis named for the transform with units), a title naming the transform, a descriptive caption citing the bibliography keys for Wilson-Hilferty 1931 and Andersen-Bollerslev-Diebold-Ebens 2001; (b) three subplots per figure: time-series, ACF (lags 1–12), distribution histogram; (c) a skew/kurtosis comparison table covering all three transforms; (d) Decision #2 citation block locking LHS = RV^{1/3} citing Wilson-Hilferty and ABDE; (e) Decision #3 citation block specifying the RV outlier policy citing Newey-West 1987 and Barone-Adesi 2008. Strict-agnosticism grep assertion: scan every markdown cell in §3 and assert zero occurrences of "release week", "non-release", "release day", "episode" substrings. No release-week comparisons, no episode tagging.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §3 per the X-trio protocol.** One trio per transform (raw RV, log RV, RV^{1/3}), one trio for the skew/kurtosis comparison, one trio per Decision.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §3 LHS EDA + Decisions #2-3`.

### Task 10: NB1 §4a-4c RHS EDA — CPI, US CPI, BanRep rate surprises

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section4a_4c.py`

- [ ] **Step 1: Write the failing test.** For each of the three subsections: a standalone time-series + ACF + distribution block with axes, labels, units, captions; a release-date alignment audit (CPI + US CPI: counts of imputed flags); a decision with four-part citation. Decision #4 (CPI surprise, Andersen-Bollerslev-Diebold-Vega 2003 AR(1) expanding-window); Decision #5 (US CPI warmup); Decision #6 (BanRep rate surprise imputation). Each citation block's "Connection to simulator" references Rev 4 spec §3.3 S1 consensus-bias.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §4a-4c per the X-trio protocol.** Three trios per subsection (plot, audit, decision). Halt per trio.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §4a-4c surprises + Decisions #4-6`.

### Task 11: NB1 §4d-4f RHS EDA — VIX, oil return, intervention dummy

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section4d_4f.py`

- [ ] **Step 1: Write the failing test.** Per subsection: standalone block + decision. Decision #7 (VIX NA handling, citing Ang-Hodrick-Xing-Zhang 2006 on VIX as global-risk proxy). Decision #8 (oil return 2020-04-20 negative-price policy, citing Ederer-Nordhaus 2020 + the `CASE WHEN value > 0` guard in econ_query_api). Decision #9 (intervention-dummy missing-date policy, citing Fuentes-Pincheira-Julio-Rincón 2014 BIS 462 + Rincón-Torres 2021).
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §4d-4f per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §4d-4f VIX/oil/intervention + Decisions #7-9`.

### Task 12: NB1 §5-7 Joint behavior + stationarity + merge + Decisions #10-12

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section5_7.py`

- [ ] **Step 1: Write the failing test.** §5 asserts: correlation heatmap of RV^{1/3} + six RHS variables; VIF table for the pre-committed RHS set (cites Belsley-Kuh-Welsch 1980); Decision #10 collinearity-resolution policy. §6 asserts: ADF + KPSS table per series citing Elliott-Rothenberg-Stock 1996 (DF-GLS) and Kwiatkowski-Phillips-Schmidt-Shin 1992 (KPSS); Decision #11 stationarity-trim policy. §7 asserts: Decision #12 merge-alignment policy citing Conrad-Schoelkopf-Tushteva 2025.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §5-7 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §5-7 joint/stationarity/merge + Decisions #10-12`.

### Task 13: NB1 §8a `cleaning.py` implementation + null-policy manifest

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/cleaning.py`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/null_policy.yaml` (machine-readable per-column null contract)
- Test: `contracts/scripts/tests/test_cleaning_module.py`
- Modify: `contracts/scripts/tests/test_cleaning_purity.py` (activate real-file assertions — the Task 4 pointer correction: this is the task where real-file lint activates, NOT Task 12)

- [ ] **Step 1: Write the failing test.** `test_cleaning_module.py` asserts: (a) `cleaning.load_clean_weekly_panel(conn)` returns a DataFrame with the exact column set expected by NB2, sorted by `week_start`, with row count matching Decision #1's sample window, and with null counts conforming to `null_policy.yaml` (every column has an explicit "allowed-null" or "no-null" rule; test reads the YAML and asserts per-column); (b) `cleaning.load_clean_daily_panel(conn)` analogous for daily panel; (c) **determinism byte-equality** — two consecutive calls produce byte-identical DataFrames (`pd.testing.assert_frame_equal(df1, df2, check_dtype=True)` + identical CSV bytes); (d) Task 4 purity lint's real-file assertions now activate and pass against the real `cleaning.py`.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement `cleaning.py`** as pure functions wrapping `econ_query_api` per Decisions #1-#12. Every function has a docstring copying the decision rationale. No randomness, no today-relative filters.
- [ ] **Step 4: Implement `null_policy.yaml`** — one row per column declaring null-policy (`"no_null"` or `"allowed_null: <reason>"`).
- [ ] **Step 5: Run all tests (including re-run of `test_cleaning_purity.py`) and confirm pass.**
- [ ] **Step 6: Commit** with message `feat(fx-vol-econ nb1): §8a cleaning.py + null policy + determinism test`.

### Task 14: NB1 §8b Decision ledger + panel fingerprint emission

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json`
- Test: `contracts/scripts/tests/test_nb1_ledger.py`

- [ ] **Step 1: Write the failing test.** Executes the full NB1 headless. Asserts: (a) §8b contains a 12-row markdown ledger table with columns (#, Question, Choice, Rationale, cleaning.py anchor, Alternative considered) with exactly 12 `Decision #N` anchors matching #1–#12; (b) `estimates/nb1_panel_fingerprint.json` exists at `env.FINGERPRINT_PATH`, was written by the notebook, and matches the fingerprint of `cleaning.load_clean_weekly_panel(conn)` computed independently by the test via `panel_fingerprint` from Task 3.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §8b per the X-trio protocol.** Trio 1: ledger markdown. Trio 2: fingerprint emission code cell + interpretation.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §8b ledger + panel fingerprint`.

### Task 15: NB1 three-way review gate

**Subagents (dispatched in parallel):** Model QA Specialist, Reality Checker, Technical Writer

Each told: Codex will review the output; NOT told about other reviewers; NOT told this is a review round. Each has a charter that explicitly includes a **chasing-offline checklist item**: "scan NB1 markdown cells for forbidden phrases ('we tried', 'rejected in favor of', 'we chose … over', 'this didn't work'); flag any occurrence."

- [ ] **Step 1:** Dispatch three reviewers in parallel.
- [ ] **Step 2:** Consolidate findings; identify BLOCKERs vs fixes.
- [ ] **Step 3:** Apply fixes via the appropriate specialist (Analytics Reporter for notebook cells; Data Engineer for `cleaning.py` or `null_policy.yaml`).
- [ ] **Step 4:** Re-dispatch reviewers on the revised NB1 until all three return APPROVED.
- [ ] **Step 5:** Commit the review reports + revisions with messages following the `fix(fx-vol-econ nb1): <specific>` pattern.

---

## Phase 2 — NB2 Estimation

### Task 16: NB2 §1-2 Setup + spec-hash + panel fingerprint verification + descriptive stats

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section1_2.py`

- [ ] **Step 1: Write the failing test.** Asserts: (a) §1 computes sha256 of spec Rev 4 and asserts match against the embedded hex string; (b) §1 re-computes the panel fingerprint from `cleaning.load_clean_weekly_panel(conn)` and asserts equality with the JSON at `env.FINGERPRINT_PATH`; (c) §1 contains the gate-verdict admonition in placeholder state; (d) §2 emits mean/SD/skew/kurtosis for RV^{1/3} and six RHS variables — full-sample only, no release-week conditioning.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §1-2 per the X-trio protocol.** Citation block for §1 references Rev 4 §1 anti-fishing; §2 references Conrad-Schoelkopf-Tushteva 2025 Table 1 descriptive-only convention.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §1-2 setup + descriptive stats`.

### Task 17: NB2 §3 Coefficient ladder + §3.5 block-bootstrap HAC sanity check

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section3.py`

- [ ] **Step 1: Write the failing test.** Asserts: (a) six-column nested-control ladder (bivariate → add US CPI → BanRep rate → VIX → intervention → oil); every column uses Newey-West HAC(4); Column 6 is visually highlighted using `\cellcolor{gray!15}` on the Column 6 header row of the LaTeX-exported table (the mechanism is locked — no alternative); sample size and adj-R² per column. (b) §3.5 runs Politis-Romano stationary bootstrap with a 4-week mean block length and B=1000, computes a 90% percentile CI on β̂_CPI from Column 6, and reports AGREEMENT or DIVERGENCE with the HAC 90% CI (agreement = the two intervals overlap by ≥50% of the HAC interval length). (c) Citation blocks precede §3 (Newey-West 1987, Andersen-Bollerslev-Diebold-Vega 2003) and §3.5 (Politis-Romano 1994). (d) Column 6 fit object is stored in a notebook variable documented for downstream tasks.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §3 and §3.5 per the X-trio protocol.** Ladder via `statsmodels.iolib.summary2.summary_col` or `stargazer`; block-bootstrap via `arch.bootstrap.StationaryBootstrap`.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §3 ladder + §3.5 block-bootstrap HAC`.

### Task 18: NB2 §4-5 OLS diagnostics + Student-t OLS alternative

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section4_5.py`

- [ ] **Step 1: Write the failing test.** §4 asserts Jarque-Bera + Breusch-Pagan + Durbin-Watson + Ljung-Box Q(1..8) on Column 6 residuals, rendered in a summary table, no auto-branching. §5 asserts a Student-t likelihood fit using `statsmodels.miscmodels.tmodel.TLinearModel` (locked API per plan rev 2), reporting the estimated ν̂ and a side-by-side coefficient table vs Gaussian OLS; the refit runs regardless of §4 outcomes. Citation blocks reference Jarque-Bera 1987, Breusch-Pagan 1979, Durbin-Watson 1951, Ljung-Box 1978, Campbell-Lo-MacKinlay 1997.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §4-5 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §4-5 diagnostics + Student-t via TLinearModel`.

### Task 19: NB2 §6 GARCH(1,1)-X co-primary

**Subagent:** Analytics Reporter (with Model QA review after Step 3)

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section6.py`

- [ ] **Step 1: Write the failing test.** Asserts: GARCH(1,1)-X fit via `arch.arch_model` on daily COP/USD returns with `|s_t^CPI|` in the variance equation (absolute value, per Han-Kristensen 2014 JBES); BFGS optimizer with 500-iter ceiling + Hessian PD check; output includes ω, α₁, β₁, δ, ν (if Student-t), log-likelihood, persistence α₁+β₁, standardized residual series, conditional volatility series, iterations used, Hessian PD status; Jarque-Bera on standardized residuals with an explicit QMLE-SE fallback surfaced in the notebook cell (not scratch) if JB rejects. Citation block references Bollerslev 1986, Han-Kristensen 2014 JBES, Bollerslev-Wooldridge 1992.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §6 per the X-trio protocol.**
- [ ] **Step 3.5: Dispatch Model QA Specialist** to review §6 for `|s_t|` enforcement, convergence guard, QMLE surfacing. Apply any fixes before Step 4.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §6 GARCH-X co-primary`.

### Task 20: NB2 §7 CPI/PPI decomposition co-primary

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section7.py`

- [ ] **Step 1: Write the failing test.** Asserts: primary refit with standardized ΔIPP added alongside CPI surprise; joint β_CPI, β_PPI point estimates + joint covariance block; interpretation markdown branches on channel dominance (|β_CPI| > |β_PPI| → inflation-channel; else producer-cost-channel). Citation block references Rev 4 §4.1 decomposition + Conrad-Schoelkopf-Tushteva 2025 for decomposition convention.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §7 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §7 CPI/PPI decomposition`.

### Task 21: NB2 §8-9 Subsample regimes + T3b gate evaluation

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section8_9.py`

- [ ] **Step 1: Write the failing test.** §8 asserts: Column 6 primary re-fit on three regimes from the query API's subsample-split constants (pre 2015-01-05, 2015-01-05 through 2021-01-04, post 2021-01-04); per-regime β̂, Σ̂, n, sample date range; Wald χ² test AND small-sample F-test for pooling (both p-values reported); Bai-Perron caveat markdown on HAC over-rejection. §9 asserts: β̂_CPI − 1.28·SE(β̂_CPI) > 0 → PASS or FAIL; adj-R² ≥ 0.15 → PASS or FAIL; explicit markdown "Gate is OLS-primary-only per Rev 4 §1; GARCH-X cannot override." Citation blocks reference Bai-Perron 1998 + Rev 4 §6.1 S3; Rev 4 §5 T3b + Balduzzi-Elton-Green 2001.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §8-9 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §8-9 regimes + T3b gate`.

### Task 22: NB2 §10-11 Reconciliation dashboard + atomic serialization

**Subagent:** Data Engineer

**Files:**
- Modify: `02_estimation.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb2_params_point.schema.json`
- Modify: `contracts/scripts/nb2_serialize.py` (full implementation replaces Task 1b stub)
- Test: `contracts/scripts/tests/test_nb2_serialization.py`

- [ ] **Step 1: Write the failing test.** Three sub-tests. (a) **Schema validation:** `nb2_params_point.schema.json` is a valid JSON Schema Draft 2020-12 with every block named in design spec §4.4 (ols_primary, ols_student_t, ols_ladder, garch_x with residual and conditional-volatility series, decomposition, subsamples three regimes with full Σ̂, reconciliation, t3b_pass, gate_verdict, spec_hash, panel_fingerprint, intervention_coverage, handoff_metadata). Every covariance uses the `{param_names, matrix}` layout. (b) **Reconciliation rule (locked per plan rev 2):** AGREE iff (i) sign(β̂_CPI) = sign(δ̂), (ii) overlap of β̂_CPI's 90% HAC CI with δ̂'s 90% QMLE CI is non-empty (directional concordance — the two parameters are not numerically comparable but their signs and significance classifications are), (iii) significance at 10% concordant (both reject null OR both fail to reject). DISAGREE otherwise. Test with synthetic fits exhibiting each failure mode. (c) **Atomic emit:** injecting an exception after JSON write but before PKL write leaves NEITHER file on disk. (d) The bootstrap-HAC agreement flag from §3.5 (Task 17) is surfaced in the reconciliation dashboard.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §10 dashboard per the X-trio protocol.** Side-by-side coefficient + CI block for OLS / GARCH-X / decomposition. The Verdict Box in §1 is programmatically updated.
- [ ] **Step 4: Implement full `nb2_serialize.py`.** Single function taking all fit objects + verdict, writes JSON and PKL atomically (stage to temp → fsync → rename both). JSON validated against schema before write. Handoff-metadata block includes Python + statsmodels + arch + numpy + pandas versions + bootstrap-distribution description (parametric-bootstrap from fitted residuals for GARCH-X; multivariate normal for OLS) + recommended random seed.
- [ ] **Step 5: Author §11 serialization code cell** that calls `nb2_serialize.write_all(...)`.
- [ ] **Step 6: Run and confirm pass.**
- [ ] **Step 7: Commit** with message `feat(fx-vol-econ nb2): §10 reconciliation + §11 atomic serialization + schema`.

### Task 23: NB2 §12 Economic magnitude + NB2 three-way review gate

**Subagents:**
- §12 authoring: Analytics Reporter
- Review (parallel, Codex-will-review framing): Model QA Specialist, Reality Checker, Technical Writer (swap per plan rev 2 — Code Reviewer's serialization concerns already covered by Task 22's schema + atomic tests; Technical Writer is the missing lens for NB2 PDF readability: ladder layout, GARCH convergence rendering, Student-t side-by-side)

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section12.py`

- [ ] **Step 1: Write the failing test.** Asserts single-line prints "β̂ = X ⇒ Y bp per 1-σ CPI surprise" and parallel for δ̂ → conditional-variance impact per 1-σ |surprise|. No RAN-payoff translation. Citation references Conrad-Schoelkopf-Tushteva 2025 for in-estimation magnitude convention.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §12 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Dispatch the three reviewers** with Codex-will-review framing. Each charter includes the chasing-offline checklist item.
- [ ] **Step 6: Consolidate fixes; dispatch specialists; re-review until all three APPROVE.**
- [ ] **Step 7: Commit** with message `feat(fx-vol-econ nb2): §12 economic magnitude + 3-way review pass`.

---

## Phase 3 — NB3 Tests + Sensitivity + Gate Verdict

### Task 24: NB3 §1 Setup + §2 T1 exogeneity

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section1_2.py`

- [ ] **Step 1: Write the failing test.** §1 asserts: loads `env.POINT_JSON_PATH` and `env.FULL_PKL_PATH`; enforces spec_hash match; re-computes and asserts panel fingerprint; version-mismatch degraded mode (library versions in handoff metadata don't match runtime → WARNING, skip pickle-dependent cells, record `pkl_degraded: true`). §2 asserts T1 consensus-rationality F-test: regress `s_t^CPI` on {`s_{t-1}^CPI`, `RV_{t-1}`, `VIX_{t-1}`}, report F-stat, p-value, joint-null-rejection at 5%. Citation block references Mincer-Zarnowitz 1969, Balduzzi-Elton-Green 2001.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §1-2 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §1 setup + §2 T1 exogeneity`.

### Task 25: NB3 §3 T2 Levene + §4 T4/T5 residual diagnostics

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section3_4.py`

- [ ] **Step 1: Write the failing test.** §3 asserts Levene (median-centered Brown-Forsythe variant) on RV^{1/3} release vs non-release — F-stat, p-value, announcement-channel claim at 10%. §4 asserts Ljung-Box Q(1..8) on primary residuals from PKL and Jarque-Bera on same. Citations: §3 Levene 1960, Conover-Johnson-Johnson 1981; §4 Ljung-Box 1978, Jarque-Bera 1987.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §3-4 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §3 Levene + §4 residuals`.

### Task 26: NB3 §5 T6 Bai-Perron + §6 T7 intervention adequacy

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section5_6.py`

- [ ] **Step 1: Write the failing test.** §5 asserts Bai-Perron endogenous break estimation via `ruptures` (first preference) or `statsmodels.stats.diagnostic.breaks_cusumolsresid` (fallback); reports estimated break dates; compares to NB2 subsample boundaries; flags unaligned breaks. §6 asserts T7 re-fit without intervention dummy, compare β̂ with vs without, stability threshold ±1 SE, PASS/FAIL for adequacy. Citations: §5 Chow 1960 + Bai-Perron 1998/2003; §6 Fuentes-Pincheira-Julio-Rincón 2014 + Rincón-Torres 2021.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §5-6 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §5 Bai-Perron + §6 T7 intervention`.

### Task 27: NB3 §7 T3a effect sign + §8 sensitivity forest plot

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section7_8.py`

- [ ] **Step 1: Write the failing test.** §7: T3a two-sided β ≠ 0 with primary HAC SE — t-stat, p-value, 95% two-sided CI; cross-reference T3b from NB2. §8: forest plot contains primary (row 1, anchor, horizontal divider below), GARCH-X (NB2), decomposition-CPI (NB2), decomposition-PPI (NB2), three subsamples (NB2), A1 monthly (fit on `get_monthly_panel`), A4 release-day-excluded (fit on `get_rv_excluding_release_day`), A5 lagged-RV, A6 bivariate, A8 oil-level, A9⁺ and A9⁻ (two rows); rows 2+ sorted by |β̂| descending; A2/A3/A7 annotated "see NB2"; rendered via `specification_curve` or matplotlib fallback. Citations: §7 Andersen-Bollerslev-Diebold-Vega 2003; §8 Simonsohn-Simmons-Nelson 2020.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §7-8 per the X-trio protocol.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §7 T3a + §8 forest plot (13 rows with A9 two-row)`.

### Task 28: NB3 §9 Material-mover spotlight tables

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section9.py`

- [ ] **Step 1: Write the failing test.** Two-pronged material-mover rule: a sensitivity is material iff β̂ falls outside the primary's 90% CI AND the T3b sign/significance classification changes. Synthetic fits exercise both prongs. Also asserts: if upstream T3b FAILed, NB3 halts before §9 with an explicit "gate failed, halting" message and zero spotlight tables produced. Citation references Leamer 1983/1985 + Ankel-Peters-Brodeur 2024.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §9 per the X-trio protocol.** Iterate over sensitivity fits from Task 27, apply two-pronged rule, emit regression tables only for material movers. Appendix accumulates every sensitivity's coefficient row regardless.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §9 spotlight + two-pronged material-mover rule`.

### Task 29: NB3 §10 Gate aggregation + `gate_verdict.json` atomic emission

**Subagent:** Data Engineer

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json` (written by notebook)
- Create: `contracts/scripts/gate_aggregate.py` (pure function building the verdict dict)
- Test: `contracts/scripts/tests/test_nb3_section10_gate.py`

- [ ] **Step 1: Write the failing test.** Asserts the `gate_verdict.json` schema includes per-test PASS/FAIL (T1, T2, T4, T5, T6, T7), re-referenced T3b from NB2, material-mover count, reconciliation status from NB2, bootstrap-HAC agreement flag from NB2 §3.5, `pkl_degraded` status from §1, final `gate_verdict` PASS or FAIL. The file is written atomically (stage → fsync → rename). `gate_aggregate.py` is a pure function taking the inputs and returning the dict.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement `gate_aggregate.py` + author §10 cell that calls it and emits the JSON.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §10 gate aggregation + atomic gate_verdict.json`.

### Task 30: NB3 README auto-render via Jinja2 + CI diff check

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/_readme_template.md.j2`
- Modify: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/README.md` (rendered by notebook execution)
- Create: `contracts/scripts/render_readme.py` (pure function consuming JSON artifacts)
- Test: `contracts/scripts/tests/test_readme_render.py`

- [ ] **Step 1: Write the failing test.** The Jinja2 template must contain, in order: (1) a one-line gate-verdict headline (PASS or FAIL with β̂ and 90% CI); (2) a β̂ results table with primary / GARCH-X / decomposition rows; (3) a reconciliation row (AGREE / DISAGREE + bootstrap-HAC agreement flag); (4) an embedded or linked forest-plot PNG; (5) a per-test pass/fail table for T1/T2/T4/T5/T6/T7; (6) links to three PDF exports; (7) a spec-hash footer. Given synthetic `gate_verdict.json` + `nb2_params_point.json` inputs, the renderer produces a deterministic byte-identical README. CI diff check: `render_readme.py <gate_verdict.json> <nb2_params_point.json>` against the committed inputs must match the committed README byte-for-byte; any drift fails the test.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author the template + `render_readme.py` + the final notebook cell that calls the renderer and writes README.md.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): Jinja2 README auto-render + CI diff check`.

### Task 31: NB3 three-way review gate

**Subagents (parallel):** Model QA Specialist, Reality Checker, Technical Writer

Each charter includes the chasing-offline checklist item. Same pattern as Tasks 15 and 23.

- [ ] **Step 1:** Dispatch parallel.
- [ ] **Step 2:** Consolidate.
- [ ] **Step 3:** Apply fixes.
- [ ] **Step 4:** Re-review until APPROVED.
- [ ] **Step 5:** Commit review reports + revisions.

---

## Phase 4 — Integration

### Task 32: End-to-end `just notebooks` validation + idempotency

**Subagent:** Reality Checker

**Files:**
- Test: `contracts/scripts/tests/test_end_to_end.py`

- [ ] **Step 1: Write the failing test.** Runs `just notebooks` twice in sequence from a clean state. Asserts: (a) first run — all three `.ipynb` execute without errors (exit 0 per notebook); all three PDFs produced at `env.PDF_DIR` and each is larger than 50 KB; `env.POINT_JSON_PATH` and `env.GATE_VERDICT_PATH` exist; the committed README matches a fresh render from the committed JSON artifacts (via Task 30's CI diff check); `gate_verdict.json` parses successfully and its `gate_verdict` field is `"PASS"` or `"FAIL"` (not null). (b) Second run — `nb1_panel_fingerprint.json`, `nb2_params_point.json`, and `gate_verdict.json` are byte-identical to the first run (determinism guarantee from §4.1 — idempotency check). The test does NOT assert PASS or FAIL on the gate; it asserts the pipeline runs twice deterministically and produces a verdict.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Fix runtime errors** by dispatching appropriate specialists.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `test(fx-vol-econ): end-to-end pipeline + determinism check`.

### Task 33: Final documentation + memory update

**Subagent:** Technical Writer + foreground memory update

**Files:**
- Modify: `contracts/CLAUDE.md` or worktree-root `CLAUDE.md`
- Memory: create `project_fx_vol_cpi_notebook_complete.md` with gate verdict, links, four-artifact pointers
- Memory: update `project_econ_notebook_handoff.md` to reflect completion

- [ ] **Step 1: Document the pipeline** in CLAUDE.md (single paragraph + links).
- [ ] **Step 2: Update memory** with completion record.
- [ ] **Step 3: Commit** with message `docs(fx-vol-econ): completion record + memory update`.

---

## Total Task Count and Phase Summary

**36 tasks across 4 phases.**

- Phase 0 (1a, 1b, 1c, 1d, 2, 3, 4, 5, 6): 9 infrastructure tasks
- Phase 1 (7, 8, 9, 10, 11, 12, 13, 14, 15): 8 NB1 authoring tasks + 1 three-way review gate
- Phase 2 (16, 17, 18, 19, 20, 21, 22, 23): 7 NB2 authoring tasks + 1 three-way review gate (merged into Task 23 with §12)
- Phase 3 (24, 25, 26, 27, 28, 29, 30, 31): 7 NB3 authoring tasks + 1 three-way review gate
- Phase 4 (32, 33): end-to-end validation + closure

## Dependency Graph

- Phase 0 tasks: 1a → {1b, 1c, 1d, 2, 3, 4, 5, 6} (1b-6 parallelizable once 1a done)
- Task 5's `pre-commit install` step must complete before Task 7 begins (first citation block authored)
- Phase 1: 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 (sequential; 13 activates Task 4's real-file lint assertions; 14 uses Task 3's fingerprint utility)
- Phase 2: depends on Phase 1 APPROVED; 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23
- Phase 3: depends on Phase 2 APPROVED (NB3 loads NB2 handoff); 24 → 25 → 26 → 27 → 28 → 29 → 30 → 31
- Phase 4: depends on Phase 3 APPROVED; 32 → 33

Review gates (Tasks 15, 23, 31) are mandatory; no phase advances until all three reviewers return APPROVED.
