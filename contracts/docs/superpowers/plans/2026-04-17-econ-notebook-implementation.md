# Structural Econometrics Notebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the three-notebook Jupyter pipeline (NB1 EDA, NB2 estimation, NB3 tests+sensitivity) specified in `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` (rev 2), producing the Layer 1 → Layer 2 handoff JSON, the gate verdict, and the auto-generated exec-layer README.

**Architecture:** Three notebooks backed by a thin `cleaning.py` wrapper over `econ_query_api`, with CI-enforced purity and citation-block linting. NB1 emits a panel fingerprint and decision ledger; NB2 emits JSON + pickle handoff artifacts with full covariance matrices and bootstrap-residuals; NB3 consumes both and writes the gate verdict consumed by a Jinja2-rendered README. No code in this plan — every task dispatches a specialized subagent with a prose specification.

**Tech Stack:** Python 3.12+, DuckDB 1.5+, statsmodels, arch, scipy, pandas, numpy, matplotlib, specification_curve (or matplotlib fallback), Jinja2, jupyter + nbconvert, just (existing worktree justfile).

---

## Non-Negotiable Rules (enforced on every task)

1. **Strict TDD.** Every task writes a failing test first, verifies the failure, implements minimally, verifies the pass, then commits. Never write implementation before an observably failing test.
2. **Specialized subagent per task.** Foreground orchestrates and verifies; never authors. Each task below names the subagent.
3. **Scripts-only scope.** Pipeline work touches ONLY `contracts/notebooks/`, `contracts/scripts/`, `contracts/data/`, `contracts/.gitignore`. Never `src/`, `test/*.sol`, `foundry.toml`, or any Solidity.
4. **Query API is the only data interface.** All data access flows through `cleaning.py`, which itself calls only `econ_query_api.py`. Raw SQL in notebook cells forbidden.
5. **Citation block before every decision/test/fit.** Four parts: reference, why used, relevance to results, connection to Layer 2. Enforced by pre-commit lint from Task 5.
6. **Push origin, not upstream.** `origin` = JMSBPP. Never push to `upstream` (wvs-finance).
7. **Real data over mocks.** Tests hit real DuckDB and real fixtures; mocks allowed only for HTTP errors that cannot be reproduced.

---

## Phase 0 — Shared Infrastructure

### Task 1: Notebook folder scaffold + justfile recipe + env.py

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/README.md` (placeholder; Jinja2-rendered later)
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb` (empty skeleton)
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/02_estimation.ipynb` (empty skeleton)
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/03_tests_and_sensitivity.ipynb` (empty skeleton)
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/.gitkeep`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/figures/.gitkeep`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/pdf/.gitkeep`
- Modify: `justfile` (worktree root) — add `notebooks:` recipe
- Modify: `contracts/.gitignore` — add scoped rules for `fx_vol_cpi_surprise/**/estimates/*.pkl`, `fx_vol_cpi_surprise/**/pdf/`, `fx_vol_cpi_surprise/**/_nbconvert_template/**/*.aux`
- Test: `contracts/scripts/tests/test_nb_env.py`

- [ ] **Step 1: Write the failing test.** The test imports `env` from the notebook package path and asserts that the module exports `DUCKDB_PATH` (str path to `contracts/data/structural_econ.duckdb`), `ESTIMATES_DIR`, `FIGURES_DIR`, and a `REQUIRED_PACKAGES` dict containing at least `statsmodels`, `arch`, `numpy`, `pandas`, `duckdb`, `scipy`, and `jinja2` keys with semantic-version-pin strings. Also assert that importing `env` raises a clear error when a required package is missing.
- [ ] **Step 2: Run the test and confirm failure.** Expected: ImportError or AttributeError because `env.py` does not yet exist.
- [ ] **Step 3: Create empty notebook skeletons.** Each notebook is a minimal valid `.ipynb` with one markdown cell containing the notebook title and a second markdown cell reading "Placeholder — implemented in Phase N". Use `nbformat` to construct the JSON.
- [ ] **Step 4: Implement env.py** with the required constants, version-pin tuples asserted on import, and a `pin_seed()` helper that sets numpy/random/python-hash seeds deterministically.
- [ ] **Step 5: Add the `notebooks` recipe to the worktree `justfile`.** The recipe runs `jupyter nbconvert --execute --to notebook --inplace` on NB1 → NB2 → NB3 in order, then `--to pdf` for each. It fails fast if any notebook errors. Document the recipe with a comment referencing the design spec §3.
- [ ] **Step 6: Extend `contracts/.gitignore`** with the three scoped rules above.
- [ ] **Step 7: Run the test and confirm pass.** Expected: all env.py assertions pass; import is clean.
- [ ] **Step 8: Commit** with message `feat(fx-vol-econ): notebook scaffold + env.py + just notebooks recipe`.

### Task 2: references.bib scaffold

**Subagent:** Technical Writer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/references.bib`
- Test: `contracts/scripts/tests/test_references_bib.py`

- [ ] **Step 1: Write the failing test.** The test parses `references.bib` with `bibtexparser` (add to requirements if absent) and asserts the presence of entries for every reference listed in design spec §14: Andersen-Bollerslev-Diebold-Vega 2003, Ankel-Peters-Brodeur 2024, Bai-Perron 1998 & 2003, Balduzzi-Elton-Green 2001, Barone-Adesi 2008, Bollerslev 1986, Bollerslev-Wooldridge 1992, Campbell-Lo-MacKinlay 1997, Chow 1960, Conrad-Schoelkopf-Tushteva 2025, Engle-Rangel 2008, Han-Kristensen 2014 (journal = JBES), Hansen-Lunde 2005, Heston-Nandi 2000, Jarque-Bera 1987, Levene 1960, Conover-Johnson-Johnson 1981, Ljung-Box 1978, Mincer-Zarnowitz 1969, Newey-West 1987, Politis-Romano 1994, Rincón-Torres et al. 2021 (BanRep Borrador 1171), Simonsohn-Simmons-Nelson 2020, Wilson-Hilferty 1931. For each entry assert the `journal` or `booktitle` field is present and non-empty. For Han-Kristensen specifically assert `journal = {Journal of Business & Economic Statistics}` (catches the earlier JE → JBES correction).
- [ ] **Step 2: Run the test and confirm failure.** Expected: file not found, or missing entries.
- [ ] **Step 3: Populate `references.bib`** with BibTeX entries for every listed reference. Use DOIs where available; URLs as fallback. Every entry has a unique key following `authorYEARkeyword` convention (e.g., `andersen2003micro`, `hanKristensen2014garch`).
- [ ] **Step 4: Run the test and confirm pass.** Expected: all 24 entries present, Han-Kristensen journal is JBES.
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): references.bib — 24 entries covering design §14`.

### Task 3: Panel fingerprint utility

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/panel_fingerprint.py`
- Test: `contracts/scripts/tests/test_panel_fingerprint.py`

- [ ] **Step 1: Write the failing test.** Three test cases: (a) a deterministic-fingerprint test — calling the fingerprint function twice on the same DataFrame produces byte-identical JSON; (b) an order-invariance test — two DataFrames with identical content but different row order produce identical fingerprints (function sorts by date column internally); (c) a drift-detection test — changing a single value in the DataFrame changes the sha256 field.
- [ ] **Step 2: Run tests and confirm failure.** Expected: module not found.
- [ ] **Step 3: Implement `panel_fingerprint.py`** exposing a pure function that takes a pandas DataFrame and a date-column name and returns a dict with: row count, column count, column-dtype mapping (sorted), min and max of the date column as ISO strings, and the sha256 of the DataFrame serialized as a CSV sorted by the date column. The function has no I/O; callers write the dict to JSON.
- [ ] **Step 4: Run tests and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): panel fingerprint utility with drift + order tests`.

### Task 4: cleaning.py purity CI lint

**Subagent:** Data Engineer

**Files:**
- Create: `contracts/scripts/tests/test_cleaning_purity.py`

- [ ] **Step 1: Write the failing test.** The test reads the source text of `contracts/notebooks/fx_vol_cpi_surprise/Colombia/cleaning.py` and asserts: zero substring matches for raw-query patterns (`.execute(`, `.sql(`, `.read_sql(`, `duckdb.connect(`); every public function (functions whose name does not start with underscore) contains at least one reference to an `econ_query_api` function name. The test also runs against a synthetic fixture in `tests/fixtures/cleaning_violator.py` that violates the rule and asserts the lint detects the violation.
- [ ] **Step 2: Run the test and confirm failure.** Expected: `cleaning.py` does not exist yet (skip the real-file assertions with `pytest.skip` if file missing) but the synthetic-violator assertion must pass immediately once the lint logic exists.
- [ ] **Step 3: Implement the lint.** Since this is a test module, the "implementation" is the lint logic inside the test itself. The test passes by correctly detecting the synthetic violator; the real-file assertions skip gracefully until Task 12 creates `cleaning.py`.
- [ ] **Step 4: Create the synthetic-violator fixture.** A 3-line Python file that calls `conn.execute(...)` directly, used by the lint test to self-verify.
- [ ] **Step 5: Run tests and confirm pass.** Expected: synthetic-violator detected; real-file assertions skipped.
- [ ] **Step 6: Commit** with message `feat(fx-vol-econ): CI lint asserting cleaning.py purity`.

### Task 5: Citation-block pre-commit lint

**Subagent:** AI Engineer

**Files:**
- Create: `contracts/scripts/lint_notebook_citations.py`
- Create: `contracts/scripts/tests/test_lint_notebook_citations.py`
- Modify: `contracts/.pre-commit-config.yaml` (create if absent) — add the lint hook

- [ ] **Step 1: Write the failing test.** Four cases, each using a minimal synthetic `.ipynb` fixture: (a) a notebook with a code cell that calls `sm.OLS(...)` preceded by a markdown cell containing all four required headers ("Reference", "Why used", "Relevance to our results", "Connection to simulator") — lint exits 0; (b) same code cell preceded by a markdown cell missing the "Connection to simulator" header — lint exits 1 and reports the missing part; (c) a notebook with a code cell not preceded by any markdown within two cells — lint exits 1; (d) a notebook whose only code cells are imports or pandas mechanics (no fit calls, no test calls, no decision markers) — lint exits 0 (nothing to gate).
- [ ] **Step 2: Run tests and confirm failure.** Expected: script does not exist.
- [ ] **Step 3: Implement `lint_notebook_citations.py`** as a CLI script that takes a list of `.ipynb` paths, parses each notebook with `nbformat`, identifies "gated" code cells (cells containing regex matches for fit patterns — OLS/GLS, `arch_model`, `scipy.stats.levene`, `scipy.stats.jarque_bera`, or a cell-tag marker `# Decision #N`), walks back up to two markdown cells looking for the four required headers, and exits non-zero if any gated cell is missing any part of the block.
- [ ] **Step 4: Add the pre-commit hook configuration** that runs the script against `.ipynb` files under `contracts/notebooks/fx_vol_cpi_surprise/`.
- [ ] **Step 5: Run tests and confirm pass.**
- [ ] **Step 6: Commit** with message `feat(fx-vol-econ): citation-block pre-commit lint with 4 fixture cases`.

### Task 6: nbconvert template enforcing remove-input tags

**Subagent:** Technical Writer

**Files:**
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/_nbconvert_template/article.tex.j2`
- Test: `contracts/scripts/tests/test_nbconvert_template.py`

- [ ] **Step 1: Write the failing test.** The test constructs a minimal `.ipynb` with (a) one code cell tagged `remove-input`, (b) one code cell without the tag, (c) one markdown cell. It runs `jupyter nbconvert --to latex --template <path>` and asserts the resulting LaTeX source contains the markdown text, contains the output of cell (b), but does NOT contain the source text of cell (a). Also asserts the template sets a timeout of 600 seconds.
- [ ] **Step 2: Run the test and confirm failure.** Expected: template file not found.
- [ ] **Step 3: Create the LaTeX template** based on `article` (jupyter's default article template) with a Jinja2 override that suppresses cell input for cells tagged `remove-input`, while keeping outputs visible. Pin `ExecutePreprocessor.timeout=600` via a companion `jupyter_nbconvert_config.py`.
- [ ] **Step 4: Run the test and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ): nbconvert LaTeX template — hide utility cells, pin timeout`.

---

## Phase 1 — NB1 Data EDA

Every NB1 task is authored by **Analytics Reporter** and reviewed between tasks. Each task adds specific cells to `01_data_eda.ipynb` with citation blocks preceding every decision. Every decision cell also appends to a running `cleaning.py` skeleton that Task 12 finalizes.

### Task 7: NB1 §1 Setup + Data Availability Statement

**Subagent:** Analytics Reporter

**Files:**
- Modify: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section1.py`

- [ ] **Step 1: Write the failing test.** The test executes the notebook headless via `nbclient` up through §1 only (via a cell tag filter `section:1`). Asserts the executed output contains: (a) a manifest table with the six source rows (TRM, IBR, intervention, FRED daily, FRED monthly, DANE IPC, DANE IPP, DANE calendar, BLS calendar); (b) a date-coverage table with rows for every table named in `econ_query_api._DATE_TABLES`; (c) a Data Availability Statement markdown block following the Social Science Data Editors template; (d) a "Gate Verdict" admonition block with placeholder text "populated after NB2".
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §1 cells.** Citation block references the Social Science Data Editors README template (Ankel-Peters et al. 2024). The code cells call `get_manifest()` and `get_date_coverage()` from the query API.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §1 setup + DAS + coverage table`.

### Task 8: NB1 §2 Panel Construction Audit + Decision #1

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section2.py`

- [ ] **Step 1: Write the failing test.** Executes cells tagged `section:2`. Asserts: (a) a panel-completeness DataFrame with rows for every column of weekly_panel and daily_panel (call `get_panel_completeness()`); (b) an empirical sample-start determination showing the overlap of TRM, IBR, IPC, IPP, and FRED coverage with a table naming the binding constraint series and its min date; (c) Decision #1 markdown cell containing the sample window (start and end dates) with the four-part citation block referencing Rincón-Torres et al. 2021 (be_1171) for Colombian FX sample conventions.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §2 cells.** The binding-constraint table is computed from `get_date_coverage()`; the sample-start empirically defends the earliest weekly observation whose full RHS set is available.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §2 panel audit + Decision #1 sample window`.

### Task 9: NB1 §3 LHS EDA + Decisions #2-3

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section3.py`

- [ ] **Step 1: Write the failing test.** Executes cells tagged `section:3`. Asserts: (a) three standalone figure blocks for raw RV, log(RV), RV^{1/3} — each with a time-series subplot, an ACF subplot (lags 1–12), and a distribution subplot; (b) a skew/kurtosis comparison table showing all three transforms; (c) Decision #2 markdown cell locking LHS = RV^{1/3} with citation block referencing Wilson-Hilferty 1931 and Andersen-Bollerslev-Diebold-Ebens 2001; (d) Decision #3 markdown cell specifying the RV outlier policy (keep all + HAC, or winsorize, or indicator dummy — whichever the analyst justifies from the data) with a citation block referencing Newey-West 1987 for HAC and Barone-Adesi et al. 2008 for filtered treatment. Strict agnosticism: NO release-week comparisons, NO episode-tagged outlier narratives.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §3 cells.** Decisions #2 and #3 both cite the Layer 2 connection: RV^{1/3} is what β̂ predicts; outlier policy propagates into HAC Σ̂ and the Layer 2 bootstrap sleeve.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §3 LHS EDA + Decisions #2-3 (RV^{1/3} + outlier policy)`.

### Task 10: NB1 §4a-4c RHS EDA (CPI surprise, US CPI surprise, BanRep rate surprise)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section4a_4c.py`

- [ ] **Step 1: Write the failing test.** For each of the three subsections, assert: a standalone time-series + ACF + distribution block; a release-date alignment audit (for CPI/US CPI — count of imputed flags from the calendar tables); a decision markdown cell with the four-part citation block. Decision #4 = CPI surprise imputation/warmup policy (citation: Andersen-Bollerslev-Diebold-Vega 2003 on AR(1) expanding-window surprises when survey data is unavailable); Decision #5 = US CPI surprise warmup; Decision #6 = BanRep rate surprise imputation policy.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §4a-4c cells.** Each subsection pulls from `get_surprise_series(series=...)`. Decisions reference Rev 4 spec §3.3 on consensus bias (S1) for their Layer 2 connection.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §4a-4c CPI/US CPI/BanRep surprises + Decisions #4-6`.

### Task 11: NB1 §4d-4f RHS EDA (VIX, oil return, intervention dummy)

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section4d_4f.py`

- [ ] **Step 1: Write the failing test.** For each subsection: standalone block + decision with citation. Decision #7 = VIX NA handling (holidays, weekends; citation: CBOE methodology documentation + Ang-Hodrick-Xing-Zhang 2006 on VIX as global-risk proxy). Decision #8 = oil return 2020-04-20 negative-price policy (citation: the DuckDB `CASE WHEN value > 0` guard already in `econ_query_api.get_monthly_panel` plus Ederer-Nordhaus 2020 on the negative-price episode). Decision #9 = intervention dummy missing-date policy (citation: Rincón-Torres et al. 2021 be_1171 §3 + BIS 462 on SUAMECA methodology).
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §4d-4f cells.** Intervention subsection shows the discretionary-vs-rule-based breakdown from `get_intervention_details`.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §4d-4f VIX/oil/intervention + Decisions #7-9`.

### Task 12: NB1 §5-7 Joint behavior + stationarity + merge policy + Decisions #10-12

**Subagent:** Analytics Reporter

**Files:**
- Modify: `01_data_eda.ipynb`
- Test: `contracts/scripts/tests/test_nb1_section5_7.py`

- [ ] **Step 1: Write the failing test.** Three sub-parts. (§5) asserts: a correlation heatmap of RV^{1/3} plus all six RHS variables; a VIF table for the pre-committed RHS set; Decision #10 markdown with collinearity-resolution policy and a citation referencing Belsley-Kuh-Welsch 1980 on VIF thresholds. (§6) asserts: an ADF + KPSS table for every series (RV^{1/3}, CPI surprise, US CPI surprise, BanRep rate surprise, VIX, oil return); Decision #11 with stationarity-based trim/differencing policy (citation: Elliott-Rothenberg-Stock 1996 + Kwiatkowski et al. 1992). (§7) asserts: Decision #12 with merge-alignment policy for single-variable missingness (citation: Conrad-Schoelkopf-Tushteva 2025 `2_Import_Dataset.do` for per-series drop rules).
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §5-7 cells.** VIF computed on the primary RHS set; ADF and KPSS from `statsmodels.tsa.stattools`.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb1): §5-7 joint/stationarity/merge + Decisions #10-12`.

### Task 13: NB1 §8 Decision ledger + `cleaning.py` emission + panel fingerprint

**Subagent:** Data Engineer

**Files:**
- Modify: `01_data_eda.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/cleaning.py`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json`
- Test: `contracts/scripts/tests/test_cleaning_module.py`
- Test: `contracts/scripts/tests/test_nb1_ledger.py`

- [ ] **Step 1: Write failing tests.** Test A (`test_cleaning_module.py`): asserts `cleaning.load_clean_weekly_panel(conn)` returns a pandas DataFrame with the exact column set expected by NB2, with no nulls in columns the ledger commits to clean, sorted by `week_start`, and with row count matching the ledger's Decision #1 sample window. Similar for `load_clean_daily_panel`. Test B (`test_nb1_ledger.py`): executes the entire NB1 headless and asserts the rendered ledger in §8 is a 12-row markdown table with exactly 12 Decision anchors matching Decisions #1–#12 as defined by the preceding section tests; asserts `estimates/nb1_panel_fingerprint.json` exists and matches the fingerprint of the freshly-loaded panel. Test C: re-run `test_cleaning_purity.py` from Task 4 — now the real-file assertions must execute (no skips) and pass.
- [ ] **Step 2: Run all three tests and confirm failure.**
- [ ] **Step 3: Implement `cleaning.py`.** Pure functions only; every function wraps an `econ_query_api` call and applies exactly the transformations Decisions #1–#12 specify. No random, no today-relative, no I/O except reading from the conn. Document each function with a docstring that copies the relevant decision rationale from the ledger.
- [ ] **Step 4: Author §8 ledger cell.** 12-row markdown table: #, Question, Choice, Rationale, cleaning.py anchor, Alternative considered. The final code cell imports `panel_fingerprint` (Task 3), computes the fingerprint on `load_clean_weekly_panel(conn)` and `load_clean_daily_panel(conn)`, writes `nb1_panel_fingerprint.json`.
- [ ] **Step 5: Run all three tests and confirm pass.**
- [ ] **Step 6: Commit** with message `feat(fx-vol-econ nb1): §8 ledger + cleaning.py + panel fingerprint`.

### Task 14: NB1 three-way review

**Subagents dispatched in parallel** (each told Codex will review its output; none told about the others or that this is a review round):

- **Model QA Specialist** — audits decisions #1-12 for econometric defensibility
- **Reality Checker** — verifies every citation block has a real reference, every decision maps to a named precedent, and strict agnosticism is upheld (no release-vs-non-release contrast)
- **Technical Writer** — narrative clarity, ledger completeness, PDF-export readiness

Each writes a report to `contracts/.scratch/2026-04-??-nb1-review-<role>.md`. Foreground consolidates fixes, dispatches Analytics Reporter + Data Engineer for any required revisions, re-runs Task 14 reviews until all three return APPROVED.

- [ ] **Step 1:** Dispatch three reviewers in parallel per the 3-way review memory pattern.
- [ ] **Step 2:** Consolidate findings into a fix matrix.
- [ ] **Step 3:** Apply fixes via specialized subagents (Analytics Reporter for notebook content, Data Engineer for cleaning.py logic).
- [ ] **Step 4:** Re-dispatch reviewers on the revised NB1 until all three return APPROVED.
- [ ] **Step 5:** Commit the review reports + any revision commits.

---

## Phase 2 — NB2 Estimation

### Task 15: NB2 §1-2 Setup + spec hash check + panel fingerprint verification + descriptive stats

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section1_2.py`

- [ ] **Step 1: Write the failing test.** Asserts: (a) §1 computes the sha256 of the upstream spec Rev 4 and asserts match against an embedded hex string; (b) §1 re-computes the panel fingerprint from `cleaning.load_clean_weekly_panel(conn)` and asserts match against `estimates/nb1_panel_fingerprint.json`; (c) §1 includes the gate verdict admonition box in placeholder state; (d) §2 emits a descriptive-stats table with mean/SD/skew/kurtosis for RV^{1/3} and all six RHS variables — full-sample only, no release-week conditioning.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §1-2 cells.** Citation block on §1 references the anti-fishing pre-commitment in Rev 4 §1; citation block on §2 references Conrad-Schoelkopf-Tushteva 2025 Table 1 for descriptive-only convention.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §1-2 setup + descriptive stats`.

### Task 16: NB2 §3 Coefficient ladder (Columns 1-6) + §3.5 block-bootstrap HAC sanity check

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section3.py`

- [ ] **Step 1: Write the failing test.** Asserts: (a) §3 emits a side-by-side coefficient table with Columns 1 through 6 (bivariate → add US CPI → add BanRep rate → add VIX → add intervention → add oil); Column 6 highlighted (bold-border or colored background in the LaTeX render) as the pre-committed primary; every column uses Newey-West HAC(4); sample size and adjusted R² reported per column. (b) §3.5 runs Politis-Romano stationary bootstrap with a 4-week mean block length and B=1000 replications on Column 6, computes a 90% percentile CI on β̂ for CPI surprise, and reports agreement-or-disagreement with the HAC 90% CI (agreement defined as the two CIs overlapping by at least 50% of the HAC interval length). (c) A citation block precedes both §3 (Newey-West 1987; Andersen-Bollerslev-Diebold-Vega 2003) and §3.5 (Politis-Romano 1994). (d) The primary Column 6 fit object is stored in a notebook-scoped variable whose name is documented for downstream tasks.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §3 and §3.5 cells.** Ladder presentation uses either `statsmodels.iolib.summary2.summary_col` or the `stargazer` package (if installed via requirements). §3.5 uses `arch.bootstrap.StationaryBootstrap` from the existing `arch` package.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §3 ladder + §3.5 block-bootstrap HAC check`.

### Task 17: NB2 §4-5 OLS diagnostics + Student-t alternative

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section4_5.py`

- [ ] **Step 1: Write the failing test.** Asserts: (§4) Jarque-Bera, Breusch-Pagan, Durbin-Watson, and Ljung-Box Q at lags 1 through 8 are computed on Column 6 residuals; all four test statistics and p-values are rendered in a summary table; no auto-branching based on any outcome. (§5) A second fit is emitted refitting Column 6 with a Student-t likelihood (via `statsmodels.regression.linear_model.OLS` re-fit or `arch.bootstrap` if required), reporting the estimated degrees-of-freedom ν̂ and a side-by-side coefficient comparison against Gaussian OLS. The refit runs regardless of §4 outcomes per design §7.5. Citation blocks reference Jarque-Bera 1987, Breusch-Pagan 1979, Durbin-Watson 1951, Ljung-Box 1978, and for §5 refer to Campbell-Lo-MacKinlay 1997 on Student-t modeling of asset-return tails.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §4-5 cells.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §4-5 OLS diagnostics + Student-t alternative`.

### Task 18: NB2 §6-7 GARCH(1,1)-X + CPI/PPI decomposition

**Subagent:** Analytics Reporter (with Model QA review after step 3)

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section6_7.py`

- [ ] **Step 1: Write the failing test.** (§6) Asserts: GARCH(1,1)-X fit via `arch.arch_model` on daily COP/USD returns with `|s_t^CPI|` in the variance equation; BFGS optimizer with 500-iteration ceiling and Hessian positive-definite check; output includes ω, α₁, β₁, δ, ν (if Student-t), log-likelihood, persistence α₁+β₁; a Jarque-Bera test on standardized residuals with an explicit QMLE-SE fallback surfaced in the notebook (not scratch) if JB rejects; a convergence-diagnostic block reporting iterations and Hessian status. (§7) Decomposition fit: re-estimate Column 6 with standardized ΔIPP added alongside CPI surprise; report β_CPI and β_PPI with a joint covariance block; interpretation markdown branch (which channel dominates based on |β_CPI| vs |β_PPI|). Citation blocks reference Han-Kristensen 2014 JBES, Bollerslev 1986, Bollerslev-Wooldridge 1992, and for decomposition the CPI vs PPI discussion in Rev 4 §4.1.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §6-7 cells.**
- [ ] **Step 3.5: Dispatch Model QA Specialist** to review §6 GARCH-X setup for correctness (`|s_t|` enforcement, convergence guard, QMLE surfacing). Apply any fixes before proceeding.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §6-7 GARCH-X + CPI/PPI decomposition`.

### Task 19: NB2 §8-9 Subsample regimes + T3b gate evaluation

**Subagent:** Analytics Reporter

**Files:**
- Modify: `02_estimation.ipynb`
- Test: `contracts/scripts/tests/test_nb2_section8_9.py`

- [ ] **Step 1: Write the failing test.** (§8) Asserts: Column 6 primary re-fit on each of the three subsamples defined by the `SUBSAMPLE_SPLITS` query-API constant; each regime reports β̂, Σ̂, n, sample date range; a pooled-vs-regime Wald χ² test and the equivalent small-sample F-test for coefficient pooling, both p-values reported (small-sample HAC Wald over-rejection caveat noted in a markdown cell). (§9) T3b evaluation: computes β̂_CPI − 1.28·SE(β̂_CPI) from Column 6, asserts one-sided-positive PASS or FAIL; adj-R² ≥ 0.15 asserted PASS or FAIL; an explicit markdown note stating "Gate is OLS-primary-only per Rev 4 §1. GARCH-X cannot override." Citation block for §8 references Bai-Perron 1998 + Rev 4 §6.1 S3 on regime chronology; §9 references Rev 4 §5 T3b and Balduzzi-Elton-Green 2001 on economic-magnitude interpretation.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §8-9 cells.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb2): §8-9 subsample regimes + T3b gate`.

### Task 20: NB2 §10-11 Reconciliation dashboard + atomic serialization

**Subagent:** Data Engineer

**Files:**
- Modify: `02_estimation.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb2_params_point.schema.json`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb2_params_point.json` (written by the notebook execution)
- Test: `contracts/scripts/tests/test_nb2_serialization.py`

- [ ] **Step 1: Write the failing test.** Three sub-tests. (a) Schema validation: `nb2_params_point.schema.json` is a valid JSON Schema (Draft 2020-12) with every block named in design spec §4.4: ols_primary, ols_student_t, ols_ladder (columns 1-6), garch_x (including residual series and conditional volatility series), decomposition, subsamples (three regimes each with full Σ̂), reconciliation field, t3b_pass, gate_verdict, spec_hash, panel_fingerprint, intervention_coverage, handoff_metadata (Python/library versions + recommended seed + bootstrap-distribution description). Every covariance matrix uses the `{param_names, matrix}` layout. (b) Atomic-emit test: an intentional exception mid-way through the serialization routine leaves NEITHER file on disk (atomic write-or-nothing); verified by inserting a hook that raises after JSON is written but before PKL — the test asserts JSON is also absent after the run. (c) Reconciliation logic: constructs synthetic OLS and GARCH-X fits where β̂ and δ̂ disagree by >1 SE, asserts the dashboard marks DISAGREE; separate case with agreement → AGREE.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §10 reconciliation dashboard.** Side-by-side coefficient + CI block for OLS primary / GARCH-X / decomposition. Agreement rule: ±1 SE on sign and significance at 10%; bootstrap-HAC agreement flag from §3.5 surfaced here. Verdict-box in §1 is programmatically updated.
- [ ] **Step 4: Author §11 serialization.** A single Python function (in `contracts/scripts/nb2_serialize.py`, imported by the notebook) takes all fit objects plus the verdict and writes JSON and PKL atomically (staging to temp paths, fsyncing, then renaming both). JSON is validated against the schema before write.
- [ ] **Step 5: Run and confirm pass.**
- [ ] **Step 6: Commit** with message `feat(fx-vol-econ nb2): §10 reconciliation + §11 atomic serialization + schema`.

### Task 21: NB2 §12 Economic magnitude + NB2 three-way review

**Subagents:**
- §12 authoring: Analytics Reporter
- Review (in parallel, with Codex-will-review framing): Model QA Specialist, Reality Checker, Code Reviewer

**Files:**
- Modify: `02_estimation.ipynb` (§12)
- Test: `contracts/scripts/tests/test_nb2_section12.py`

- [ ] **Step 1: Write the failing test for §12.** Asserts a single-line print/markdown "β̂ = X ⇒ Y bp per 1-σ CPI surprise" and a parallel line for δ̂ → conditional-variance impact per 1-σ |surprise|. No RAN payoff translation (deferred to Layer 2). Citation block references Conrad-Schoelkopf-Tushteva 2025 for in-estimation economic-magnitude convention.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §12.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Dispatch the three reviewers** on the complete NB2 (all §1-§12) with the standard Codex-will-review framing. Reports go to `contracts/.scratch/2026-04-??-nb2-review-<role>.md`.
- [ ] **Step 6: Consolidate fixes, dispatch specialists, re-review until all APPROVED.**
- [ ] **Step 7: Commit** the revision chain with message `feat(fx-vol-econ nb2): §12 economic magnitude + 3-way review pass`.

---

## Phase 3 — NB3 Tests + Sensitivity + Gate Verdict

### Task 22: NB3 §1 Setup + §2 T1 exogeneity

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section1_2.py`

- [ ] **Step 1: Write the failing test.** (§1) Asserts: loads `estimates/nb2_params_point.json` and `nb2_params_full.pkl`; enforces spec_hash match; re-computes and asserts panel fingerprint; handles the version-mismatch degraded mode by asserting that when library versions in the handoff metadata do not match the current runtime, the notebook logs a WARNING, skips pickle-dependent cells, and proceeds. (§2) Asserts T1 consensus-rationality F-test: regresses `s_t^CPI` on `s_{t-1}^CPI`, `RV_{t-1}`, and `VIX_{t-1}`; reports F-statistic, p-value, joint-null-rejection decision at 5%. Citation block references Mincer-Zarnowitz 1969 and Balduzzi-Elton-Green 2001.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §1-2 cells.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §1 setup + §2 T1 exogeneity`.

### Task 23: NB3 §3 T2 variance heterogeneity + §4 T4/T5 residual diagnostics

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section3_4.py`

- [ ] **Step 1: Write the failing test.** (§3) Asserts T2 Levene (or Brown-Forsythe median-centered variant) comparing RV^{1/3} variance between release weeks and non-release weeks; reports F-stat and p-value; announces announcement-channel existence if p < 0.10. (§4) Asserts T4 Ljung-Box Q on primary-fit residuals (retrieved from the pickle) at lags 1 through 8; T5 Jarque-Bera on the same residuals; p-values and reject/no-reject summaries. Citation blocks: §3 — Levene 1960, Conover-Johnson-Johnson 1981; §4 — Ljung-Box 1978, Jarque-Bera 1987.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §3-4 cells.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §3 T2 Levene + §4 T4/T5 residuals`.

### Task 24: NB3 §5 T6 structural break + §6 T7 intervention adequacy

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section5_6.py`

- [ ] **Step 1: Write the failing test.** (§5) Asserts Bai-Perron endogenous break estimation on the primary sample using `ruptures` (first preference) or `statsmodels.stats.diagnostic.breaks_cusumolsresid` (fallback); reports estimated break dates, compares against the NB2 subsample boundaries (2015-01-05, 2021-01-04); flags any break not aligned with those boundaries. (§6) Asserts T7: re-fit primary without intervention dummy, compare β̂ with intervention vs without, stability threshold = change within ±1 SE; reports the comparison table and a PASS/FAIL for control adequacy. Citation blocks: §5 — Chow 1960, Bai-Perron 1998 & 2003; §6 — Fuentes-Pincheira-Julio-Rincón 2014 BIS 462, Rincón-Torres et al. 2021 be_1171.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §5-6 cells.** Package selection (`ruptures` vs statsmodels) is decided in-task based on install availability and documented in the ledger.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §5 Bai-Perron break + §6 T7 intervention adequacy`.

### Task 25: NB3 §7 T3a effect sign + §8 sensitivity forest plot

**Subagent:** Analytics Reporter

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Test: `contracts/scripts/tests/test_nb3_section7_8.py`

- [ ] **Step 1: Write the failing test.** (§7) Asserts T3a two-sided β ≠ 0 test using the primary HAC SE: t-stat, p-value, 95% two-sided CI; references T3b verdict from NB2 handoff. (§8) Asserts: the forest plot contains the following rows — primary Column 6 (anchor, row 1, with horizontal divider below), GARCH-X, decomposition-CPI, decomposition-PPI, three subsamples (pre-2015, 2015-2021, post-2021), A1 monthly horizon (fitted on `get_monthly_panel(conn)`), A4 release-day-excluded (fitted on `get_rv_excluding_release_day`), A5 lagged RV (re-fit primary with RV_{t-1} added), A6 bivariate (no controls), A8 oil-level (re-fit primary with log(oil price) added), A9 asymmetric rendered as two rows (β⁺, β⁻). Rows 2+ are sorted by |β̂| descending. A2, A3, A7 annotated as "see NB2 §7, §8, §6" in the dashboard panel. The plot is rendered via `specification_curve` package if installed, else manual matplotlib. Citation blocks: §7 — Andersen-Bollerslev-Diebold-Vega 2003; §8 — Simonsohn-Simmons-Nelson 2020.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §7-8 cells.** Fit objects for A1/A4/A5/A6/A8/A9 are computed inline and persisted to a temporary dict for §9's spotlight step.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `feat(fx-vol-econ nb3): §7 T3a + §8 forest plot with A9 two-row`.

### Task 26: NB3 §9 Material-mover spotlight + §10 gate verdict + README auto-render

**Subagent:** Data Engineer (for serialization + Jinja2) + Analytics Reporter (for spotlight-table narrative)

**Files:**
- Modify: `03_tests_and_sensitivity.ipynb`
- Create: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/_readme_template.md.j2`
- Create (written by notebook execution): `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json`
- Modify (written by notebook execution): `contracts/notebooks/fx_vol_cpi_surprise/Colombia/README.md`
- Test: `contracts/scripts/tests/test_nb3_section9_10.py`
- Test: `contracts/scripts/tests/test_readme_render.py`

- [ ] **Step 1: Write failing tests.** Test A: the material-mover rule is two-pronged — a spec is flagged only when β̂ falls outside the primary 90% CI AND the T3b sign/significance classification changes. Synthetic fits verifying both prongs required. Test A also asserts NB3 halts before §9 if T3b has failed upstream (with an explicit "gate failed, halting" message and no spotlight tables produced). Test B: `gate_verdict.json` schema includes per-test PASS/FAIL (T1, T2, T4, T5, T6, T7), T3b re-reference from NB2, material-mover count, reconciliation status from NB2, bootstrap-HAC agreement flag from NB2 §3.5, and final gate_verdict PASS/FAIL. Test C: README Jinja2 render — given a synthetic `gate_verdict.json` + `nb2_params_point.json`, the rendered README contains the gate verdict, β̂ table, reconciliation status, a link or embed of the forest plot, and links to each notebook PDF. Test D: CI diff check — re-rendering the README from the committed JSON artifacts produces byte-identical output to the committed README.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Author §9 spotlight-table logic.** Iterate over the sensitivity fits from Task 25; apply the two-pronged rule; emit a regression table only for material movers; the appendix accumulates every sensitivity's coefficient row regardless of materiality.
- [ ] **Step 4: Author §10 gate aggregation.** Build the verdict dict, serialize to `gate_verdict.json` atomically.
- [ ] **Step 5: Author the README Jinja2 template** and the final cell that renders and writes README.md. The template is committed; the rendered README is also committed; the CI diff check runs in `test_readme_render.py`.
- [ ] **Step 6: Run all tests and confirm pass.**
- [ ] **Step 7: Commit** with message `feat(fx-vol-econ nb3): §9-10 spotlight + gate + README auto-render`.

### Task 27: NB3 three-way review

Same pattern as Task 14 / Task 21 — three reviewers in parallel with Codex-will-review framing:

- **Model QA Specialist** — spec-test econometric correctness, forest-plot validity, two-pronged rule implementation
- **Reality Checker** — every citation real, Layer 2 mapping-gap disclaimer intact in §10, no accidental claim to solve deferred questions
- **Technical Writer** — narrative clarity, PDF-export readiness, cross-reference consistency between README and notebooks

- [ ] **Step 1:** Dispatch three reviewers in parallel.
- [ ] **Step 2:** Consolidate fixes.
- [ ] **Step 3:** Apply via specialized subagents.
- [ ] **Step 4:** Re-dispatch until all APPROVED.
- [ ] **Step 5:** Commit review reports + revision chain.

---

## Phase 4 — Integration

### Task 28: End-to-end `just notebooks` validation

**Subagent:** Reality Checker

**Files:**
- No source changes. Produces: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/pdf/01_data_eda.pdf`, `02_estimation.pdf`, `03_tests_and_sensitivity.pdf` (gitignored)
- Test: `contracts/scripts/tests/test_end_to_end.py`

- [ ] **Step 1: Write the failing test.** Runs `just notebooks` from the worktree root. Asserts: all three `.ipynb` files execute without errors; all three PDF exports are produced in `pdf/`; the committed `README.md` matches a fresh render from the committed JSON artifacts (via Task 26's CI diff check); the final `gate_verdict.json` contains a non-null `gate_verdict` field. The test does not assert PASS or FAIL — it asserts the pipeline completes and produces a verdict.
- [ ] **Step 2: Run and confirm failure.** Expected on first run: some subset of notebooks may still have issues.
- [ ] **Step 3: Fix any runtime errors** by dispatching appropriate specialists.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** with message `test(fx-vol-econ): end-to-end pipeline validation`.

### Task 29: Final documentation + memory update

**Subagent:** Technical Writer + foreground memory update

**Files:**
- Modify: `contracts/CLAUDE.md` or worktree `CLAUDE.md` — add a pointer to the pipeline
- Memory: add a `project_fx_vol_cpi_notebook_complete.md` entry with gate verdict state and links to the four key artifacts (design spec rev 2, implementation plan, README, gate_verdict.json)
- Memory: update `project_econ_notebook_handoff.md` to reflect completion

- [ ] **Step 1: Document the pipeline** in the worktree-level CLAUDE.md (single paragraph + links).
- [ ] **Step 2: Update memory** with the completion record and artifact pointers.
- [ ] **Step 3: Commit** documentation changes with message `docs(fx-vol-econ): completion record + memory update`.

---

## Total Task Count

**29 tasks across 4 phases.** Every task has: a named specialized subagent, explicit files to create/modify, a failing test written first, an implementation step, a passing verification, and a commit. No code in any step (per code-agnostic plan rule); the dispatched subagent receives the detailed prose specification from the task description and implements under TDD discipline.

Phase 0 (1-6): shared infrastructure. Phase 1 (7-14): NB1 EDA. Phase 2 (15-21): NB2 estimation. Phase 3 (22-27): NB3 tests+sensitivity. Phase 4 (28-29): integration + closure.

## Dependency Graph

- Phase 0 tasks run sequentially: Task 1 → Task 2, 3, 4, 5, 6 can run in parallel once Task 1 is complete.
- Phase 1 depends on Phase 0 complete.
- Phase 2 depends on Phase 1 complete (NB2 imports the cleaning module emitted by Task 13).
- Phase 3 depends on Phase 2 complete (NB3 consumes the handoff JSON emitted by Task 20).
- Phase 4 depends on Phase 3 complete.

Review tasks (14, 21, 27) are mandatory gates; do not advance to the next phase until the three reviewers return APPROVED.
