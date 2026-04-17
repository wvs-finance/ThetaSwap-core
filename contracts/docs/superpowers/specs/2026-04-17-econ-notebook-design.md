# Design: Structural Econometrics Estimation Notebook Pipeline

**Date:** 2026-04-17
**Status:** Draft, pending user review
**Upstream:** `contracts/notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)
**Data interface:** `contracts/scripts/econ_query_api.py` (17 endpoints, 27 tests)
**Downstream:** Layer 2 RAN payoff simulator (separate design, deferred)
**Research reports** (evidence backing this design):
- `contracts/.scratch/2026-04-17-notebook-structure-research.md` — top-level structure conventions
- `contracts/.scratch/2026-04-17-nb1-eda-conventions-research.md` — EDA + decision-ledger conventions
- `contracts/.scratch/2026-04-17-nb2-estimation-and-handoff-research.md` — estimation + Layer 2 handoff contract
- `contracts/.scratch/2026-04-17-nb3-tests-sensitivity-research.md` — spec-test grouping + forest plot + material-mover threshold

---

## 1. Purpose and Scope

Deliver a three-notebook Jupyter pipeline that estimates the pre-committed structural econometric model in Rev 4 of the upstream spec, produces the gate verdict, and serializes Layer-2-ready parameter artifacts. The pipeline is a research deliverable: reviewers (internal, academic, product-facing) must be able to trace every choice to a published precedent and understand how each output connects to the downstream RAN payoff simulator.

Scope excludes: the simulator itself, pool-parameterization logic, tick-concentration analysis (spec §4.5 Layer 1 → Layer 2 mapping gap remains deferred).

## 2. Audience and Format Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Audience | Hybrid layered: exec summary / technical body / appendix | One deliverable serves internal research, academic referee, and product-decision reviewers without duplication |
| Output format | `.ipynb` source + nbconvert LaTeX/PDF export per notebook | Matches spec Rev 4 LaTeX-heavy notation; portable for sharing |
| Scope | Three notebooks (EDA + estimation + tests/sensitivity) | Conrad et al. 2025 replication + Cookiecutter Data Science phase-numbered convention; T1–T7 + A1–A9 is ~16 procedures, justifying separation of estimation from sensitivity |
| Estimation presentation | Coefficient ladder with pre-committed primary named upfront; private spec-chasing in Analytics Reporter scratch | Honors Rev 4 anti-fishing commitment; ladder matches Conrad et al. 2025 `eststo`/`esttab` convention |
| Code visibility in PDF | Hide utility cells (imports, data loads, plot helpers) via `remove-input` tag; show all modeling calls | Reader sees what was estimated without pandas mechanics; reviewer can always open `.ipynb` for full audit |
| Sensitivity presentation | Forest plot of β̂ ± 90% CI across 12 rows + spotlight tables for material movers + appendix coefficient matrix | Specification curve convention (Simonsohn–Simmons–Nelson 2020); every sensitivity visible, detail where it matters |
| Gate verdict placement | Exec-layer `README.md` at notebooks root + repeated verdict box at top of each of the three notebooks | Single source of truth for product decisions; each PDF standalone-shareable |

## 3. Folder Layout

```
contracts/notebooks/fx_vol_cpi_surprise/Colombia/
├── README.md                             auto-rendered exec layer (Jinja2; see §4.6)
├── references.bib                        single source of truth for all citations
├── cleaning.py                           applies NB1-documented cleaning decisions on top of econ_query_api
├── env.py                                version pins + seed helpers + path constants
├── 01_data_eda.ipynb                     NB1
├── 02_estimation.ipynb                   NB2
├── 03_tests_and_sensitivity.ipynb        NB3
├── estimates/
│   ├── nb1_panel_fingerprint.json        NB1 panel audit record (§4.7)
│   ├── nb2_params_point.json             Layer 1 → Layer 2 handoff contract (version-controlled)
│   ├── nb2_params_point.schema.json      JSON Schema validating the contract on every emission
│   ├── nb2_params_full.pkl               full fit objects (gitignored, reproducible on `just notebooks`)
│   └── gate_verdict.json                 NB3 output, consumed by README render
├── figures/                              PNGs for README embedding
├── pdf/                                  nbconvert exports (gitignored)
└── _nbconvert_template/                  custom LaTeX template enforcing remove-input cell tags
```

`Colombia/` subpath future-proofs for Mexico/Peru/Chile replications of the same hedge thesis.

Runner: the existing angstrom-worktree `justfile` gains a `notebooks:` recipe that runs `jupyter nbconvert --execute --to notebook --inplace` on the three notebooks in order (NB1 → NB2 → NB3) and then `--to pdf` for PDF exports. No new Makefile is introduced.

`.gitignore` additions (scoped, not global): the pickle companion, the `pdf/` folder, and any LaTeX build artifacts under `_nbconvert_template/`. The rules are rooted at `contracts/notebooks/fx_vol_cpi_surprise/**/` so future intentional pickle fixtures elsewhere in the repo remain tracked.

## 4. Artifact Contracts

### 4.1 `cleaning.py`

Pure Python module, no notebook state. Exposes deterministic functions that take a DuckDB connection and return cleaned pandas DataFrames. Honors the project's "query API is the only interface" rule (memory: Econ notebook handoff) by wrapping `econ_query_api` calls and applying NB1-ledger cleaning decisions. No randomness, no today-relative filters, no network I/O.

Determinism guarantee: for a fixed connection, every public function returns a byte-identical DataFrame across runs — same dtypes, same row ordering (sorted by `week_start` or `date`), no NaN-vs-NaT drift.

Purity enforcement: a companion test module (`contracts/scripts/tests/test_cleaning_purity.py`) asserts via source-text grep that `cleaning.py` contains zero occurrences of raw-query call patterns (DuckDB execute, SQL-string invocation, pandas read-SQL, or direct DuckDB connection construction), and that every public function flows through at least one `econ_query_api` call before any pandas post-processing. CI fails on violation.

### 4.2 `references.bib`

BibTeX bibliography cited by every citation block in NB1/NB2/NB3. Rendered into PDFs via the nbconvert LaTeX template. Entries added incrementally as Analytics Reporter authors each section.

### 4.3 `env.py`

Path constants (DuckDB, estimates directory, figures directory) and a reproducibility seed helper. Exports an explicit required-versions tuple for Python and each third-party library (statsmodels, arch, numpy, pandas, duckdb, specification_curve or the forest-plot substitute). Versions mirrored in `contracts/requirements.txt` (already exists). Asserted on module import: mismatch raises immediately, preventing silent drift. A seeded-nbconvert execution timeout (600 s) is pinned in the nbconvert template so cold-start execution is deterministic.

### 4.4 `nb2_params_point.json` (Layer 1 → Layer 2 handoff contract)

Version-controlled JSON. The schema is described below in prose; an authoritative JSON-Schema file is written to `estimates/nb2_params_point.schema.json` during implementation and validated on every emission.

Top-level blocks:

- **Primary OLS block** — point estimates (β̂ on CPI surprise and the five controls: US CPI surprise, BanRep rate surprise, VIX, intervention dummy, oil return), the HAC(4) covariance matrix, the HAC lag explicitly recorded as an integer, sample size, R², adjusted R², and the sample date range (inclusive start and end).
- **Primary OLS with Student-t likelihood block** — the displayed alternative from NB2 §5; same fields as the primary block plus the estimated Student-t degrees-of-freedom ν.
- **OLS ladder block** — Columns 1 through 6 (nested-control robustness); each column carries point estimates, standard errors, and the sample date range, but does not require the full covariance matrix (Layer 2 does not consume the ladder).
- **GARCH(1,1)-X block** — point estimates {ω, α₁, β₁, δ, ν if Student-t}, the QMLE covariance matrix, the log-likelihood, the persistence α₁+β₁, the standardized residual series {ẑ_t} keyed by date (required for Barone-Adesi filtered historical simulation in Layer 2), the conditional volatility series {σ̂_t} keyed by date (required for Layer 2 to initialize simulation from the last in-sample σ̂_T), the sample date range, and the convergence diagnostics (iterations used, Hessian PD status).
- **Decomposition block** — β₁ (CPI) and β₂ (standardized PPI) with their joint covariance matrix, sample date range.
- **Subsample block** — three regimes (pre 2015-01-05, 2015-01-05 through 2021-01-04, post 2021-01-04); each regime carries point estimates, a full covariance matrix, sample size, and its date range. Pooling tests reported as both a Wald χ² p-value and the equivalent small-sample F-test p-value; small-sample HAC Wald tests can over-reject, so both statistics are surfaced.
- **Reconciliation field** — the string `"AGREE"` or `"DISAGREE"` per Rev 4 protocol (OLS primary and GARCH-X agree within ±1 SE on sign and significance).
- **Gate-verdict fields** — the boolean `t3b_pass` (OLS primary only) and the string `gate_verdict` with value `"PASS"` or `"FAIL"`.
- **Spec and panel integrity fields** — the sha256 of the upstream spec Rev 4 (NB3 asserts match on load) and the sha256 fingerprint of the cleaned weekly panel NB1 produced (see §4.7).
- **Intervention coverage field** — the count of weeks in the primary sample with the intervention dummy equal to one; T7 validity depends on this count being bounded away from both zero and the sample size.
- **Handoff metadata** — the library version strings for Python, statsmodels, arch, numpy, and pandas (used by the pickle version guard in §4.5); a description of the bootstrap-draw distribution Layer 2 is expected to use (for the OLS block, multivariate normal from the HAC-robust covariance; for the GARCH-X block, parametric bootstrap from the fitted standardized residuals rather than Gaussian draws, because Gaussian draws violate the α₁+β₁<1 stationarity constraint with non-trivial probability at the realistic Colombian persistence of ~0.97); and a recommended random seed so Layer 2 consumers have a canonical default.

Every covariance matrix in the JSON is stored as an explicit two-field block: an ordered list of parameter names and a row-major matrix whose rows and columns align with that list. This forbids implicit parameter ordering (which breaks silently on library upgrades).

Format choice per research report §2: plug-in point estimates plus the full covariance matrix is the dominant convention in applied GARCH option-pricing handoffs; the covariance-propagation precedent is Heston-Nandi (the edoberton implementation keeps `hess_inv.todense()` for the inverse Hessian); Hansen-Lunde 2005 JAE established the plug-in-point-estimate convention but does NOT propagate covariance matrices downstream, so the covariance half of the contract does not rest on Hansen-Lunde. No MCMC posterior is required.

### 4.5 `nb2_params_full.pkl`

Convenience companion. Full `statsmodels.RegressionResults` objects for the primary OLS, the ladder, the Student-t alternative, and each subsample; full `arch.ARCHModelResult` for GARCH-X. Gitignored. NB3 loads this for T4/T5 residual diagnostics. Both JSON and pickle are written atomically in the same serialization function to prevent drift: the function takes all fit objects and emits both files or raises.

Version guard: NB3 compares the Python, statsmodels, arch, numpy, and pandas major.minor version strings against the handoff-metadata block in `nb2_params_point.json`. On mismatch, NB3 emits a console WARNING, skips all PKL-dependent cells (the T4 and T5 residual diagnostics fall through to an "unavailable — rerun NB2 under matching versions" message), and the final `gate_verdict.json` records `"pkl_degraded": true`. The gate verdict itself remains valid from the JSON contract alone; only residual-level diagnostics are lost.

### 4.6 `gate_verdict.json`

NB3 output. Aggregates per-test outcomes (T1–T7), material-mover count, reconciliation status, and final PASS/FAIL. Consumed by `README.md` at notebooks root.

The exec-layer `README.md` is auto-generated from a Jinja2 template that consumes `gate_verdict.json` and `nb2_params_point.json`; NB3's final cell performs the render and writes the file in place. CI diff-checks the committed README against a fresh render from the committed JSON artifacts: any drift fails CI, preventing manual divergence.

### 4.7 `nb1_panel_fingerprint.json`

NB1 output. A lightweight audit record of the cleaned weekly and daily panels: row and column counts, date range bounds, column dtypes, and the sha256 of the panel serialized as a sorted CSV. NB2 and NB3 assert the fingerprint matches at load time by re-computing it from `cleaning.load_clean_weekly_panel(conn)` and `cleaning.load_clean_daily_panel(conn)`. Mismatch halts execution with an explicit message identifying which field diverged. This closes the cross-notebook panel-version audit gap without requiring a materialized parquet in version control.

## 5. Cross-Cutting Rules (NON-NEGOTIABLE)

### 5.1 Citation block before every decision, test, and spec choice

Every decision cell, test cell, and specification-choice cell in NB1/NB2/NB3 is preceded by a dedicated markdown cell with exactly four parts:

1. **Reference** — paper, URL, section/equation
2. **Why used** — what question this answers
3. **Relevance to our results** — how outcome modifies β̂, CI, or gate verdict
4. **Connection to simulator (Layer 2)** — how this output feeds RAN payoff; or "Does not feed Layer 2" with justification

Enforced by Analytics Reporter during authoring and by a pre-commit lint script (`contracts/scripts/lint_notebook_citations.py`) that scans each `.ipynb` under `contracts/notebooks/fx_vol_cpi_surprise/` and fails the commit if any decision cell, test cell, or fit call in NB1/NB2/NB3 is not preceded within the prior two markdown cells by the four-part block signature ("Reference", "Why used", "Relevance to our results", "Connection to simulator"). Reviewers reject any cell the linter does not gate.

### 5.2 Code visibility

Imports, data loads, plotting helpers: tag cells `remove-input` — hidden in PDF, visible in `.ipynb`. Modeling calls (regression fits, test invocations): shown in PDF. Rationale: reader sees what was estimated without mechanics.

### 5.3 Chasing-happens-offline rule

Spec searching, model comparison, JB-fallback trials happen in Analytics Reporter's private scratch. Only the committed primary, displayed alternatives (Student-t OLS, GARCH-X), and pre-committed co-primaries appear in the published notebooks. No cell demonstrates "we tried X and picked Y."

### 5.4 Strict EDA agnosticism in NB1

NB1 shows only unconditional distributions and coverage. No release-vs-non-release comparisons, no episode-tagged outlier narratives, no foreshadowing of T1–T7. Conrad et al. 2025 precedent.

### 5.5 Query API is the only data interface

All notebook data access flows through `cleaning.py`, which itself calls only `econ_query_api.py`. Raw SQL in notebook cells and direct DuckDB table access from notebooks are forbidden.

## 6. NB1 Design — Data EDA + Provenance Log

**Purpose:** Justify every cleaning choice with evidence, emit `cleaning.py`, and hand off documented panels to NB2/NB3 via the query API wrapper.

Sections:

1. **Setup + Data Availability Statement** — manifest, coverage, SSDE-template DAS block
2. **Panel Construction Audit** — sample-period empirical defense, completeness report; Decision #1 (sample window)
3. **LHS EDA — COP/USD Realized Volatility** — raw RV, log(RV), RV^{1/3} distributions; Decision #2 (LHS transform = RV^{1/3}) and Decision #3 (RV outlier policy)
4. **RHS Variable Inspection** — one standalone block (time series + ACF + distribution) per variable, six subsections (CPI surprise, US CPI surprise, BanRep rate surprise, VIX, oil return, intervention dummy); Decisions #4–#9, one per regressor
5. **Joint Behavior** — correlation heatmap + VIF; Decision #10 (collinearity resolution)
6. **Stationarity Pre-Checks** — ADF + KPSS per series; Decision #11 (stationarity trim)
7. **Sample Window + Merge-Alignment** — Decision #12 (merge policy for single-variable missingness)
8. **Decision Ledger + `cleaning.py` emission** — 12-row table; validation assertions against the cleaning module's weekly-panel and daily-panel loaders; emit `nb1_panel_fingerprint.json` (§4.7) so downstream notebooks audit panel integrity on load

Total: 12 ledger decisions per Conrad et al. 2025 granularity precedent (23 decisions for 15 input series → scale to 12 for our 7 input series).

Plot convention: standalone per-variable, no 3×2 grid (Kevin Sheppard `arch` examples + Conrad 2025 replication precedent).

## 7. NB2 Design — Estimation (Pre-Committed Primary + Co-Primaries)

**Purpose:** Produce pre-committed primary β̂, GARCH-X co-primary δ̂, decomposition β₁/β₂, subsample regime estimates, reconciliation verdict; serialize Layer 2 handoff artifacts.

Sections:

1. **Setup + Spec Hash Check + Panel Fingerprint Check + Verdict Box** — assert the spec hash matches Rev 4; re-compute the panel fingerprint from the cleaning module's weekly-panel loader and assert match against `nb1_panel_fingerprint.json`; verdict box placeholder
2. **Descriptive Statistics** — full-sample mean/SD/skew/kurtosis, no conditioning on release weeks
3. **OLS Primary — Coefficient Ladder** — Columns 1–6 nested controls; Column 6 = pre-committed primary highlighted; Newey-West HAC(4)
3.5. **Block-bootstrap HAC sanity check** — Politis-Romano stationary bootstrap with a 4-week mean block length and B=1000 replications; compute a 90% percentile CI on β̂ and compare against the HAC 90% CI. Agreement reinforces the plug-in headline; divergence raises a flag recorded in the reconciliation dashboard (§10) and carried into the final gate verdict. Does not change the headline point estimate.
4. **OLS Diagnostics (displayed, not branching)** — Jarque-Bera on residuals, Breusch-Pagan, Durbin-Watson, Ljung-Box Q at lags 1 through 8
5. **Student-t OLS Alternative (displayed)** — refit primary with Student-t likelihood regardless of JB outcome; side-by-side with Gaussian; ν̂ recorded
6. **GARCH(1,1)-X Co-Primary** — |s_t^CPI| (absolute value) in the variance equation per Han-Kristensen (2014, JBES); convergence guard (BFGS, 500-iteration ceiling, Hessian positive-definite check); QMLE standard errors (Bollerslev-Wooldridge 1992) are reported if a Jarque-Bera test on standardized residuals rejects normality — this fallback is explicit in the published cell, not hidden in scratch
7. **CPI-vs-PPI Decomposition Co-Primary** — re-estimate primary with standardized ΔIPP_t added; report β₁ and β₂
8. **Subsample Estimates (Regime Check)** — OLS primary on each of three regimes from the query API's subsample-split constants (pre 2015-01-05, 2015-01-05 through 2021-01-04, post 2021-01-04); Wald χ² test and small-sample F-test for pooling (both reported because small-sample HAC Wald tests can over-reject); feeds Layer 2 regime-switching
9. **T3b Gate Evaluation (OLS primary only)** — β̂ − 1.28·SE > 0; adj-R² ≥ 0.15; explicit note that GARCH-X cannot override
10. **Reconciliation Dashboard** — OLS primary / GARCH-X / decomposition side-by-side; AGREE if within ±1 SE on sign and significance, else DISAGREE; Layer 2 consumes both bands on disagreement; the bootstrap-HAC agreement flag from §3.5 is surfaced here
11. **Serialization** — write `nb2_params_point.json` and `nb2_params_full.pkl` atomically; full covariance matrices (param-name-aligned, not just SE vectors) for every block; Student-t OLS block, GARCH-X residuals and conditional-volatility series, and intervention coverage all serialized for Layer 2 consumption per §4.4
12. **Economic Magnitude (one-liners)** — β̂ → bp per 1-σ CPI surprise; full RAN-payoff translation deferred to Layer 2

Bootstrap sleeve for Layer 2: K=500 parameter vectors drawn in Layer 2 itself, not pre-drawn in NB2. For the OLS block, Gaussian draws from the HAC-robust covariance are sound (asymptotic normality holds under HAC). For the GARCH-X block, Gaussian draws from N(θ̂, Σ̂) are **not** used because they violate the α₁+β₁<1 stationarity constraint and the positivity constraints on ω/α/β/δ with non-trivial probability at realistic Colombian persistence (~0.97); instead Layer 2 runs a parametric bootstrap from the fitted standardized residuals {ẑ_t} (Bollerslev-Wooldridge 1992 style), which produces K parameter vectors respecting the constraint by construction. The covariance matrix across the two blocks is block-diagonal (the OLS and GARCH-X fits are estimated independently), explicitly documented in the handoff. The approach matches the filtered-historical-simulation convention (Barone-Adesi et al. 2008 JBF).

## 8. NB3 Design — Specification Tests + Sensitivity + Gate Verdict

**Purpose:** Run T1–T7 spec tests with both economic and statistical interpretation, run A1–A9 sensitivities with forest plot + spotlight, deliver final gate verdict to exec-layer README.

Grouping rule: by diagnostic target (I4R 2024 + Simonsohn 2020 convention), not statistical attack-surface jargon. Numeric T-IDs preserved in subsection titles.

Sections (reordered so identification precedes dynamics — T1 runs first because consensus irrationality would bias every downstream estimate):

1. **Setup + Gate Prerequisite Check** — load `nb2_params_point.json`, assert `spec_hash` matches Rev 4, re-compute and assert panel fingerprint against `nb1_panel_fingerprint.json`
2. **Exogeneity of Forecast Construction** — T1 consensus rationality F-test (runs first because failure biases β̂ regardless of downstream diagnostics)
3. **Variance Heterogeneity** — T2 Levene test (release vs non-release) — establishes the announcement channel exists
4. **Residual Diagnostics** — T4 Ljung-Box Q at lags 1 through 8, T5 Jarque-Bera on residuals
5. **Stability** — T6 Chow / Bai-Perron structural break (regime stability)
6. **Control Adequacy** — T7 intervention-control adequacy (separate from stability; tests whether `I_t` absorbs the intervention signal, an omitted-variable-style diagnostic)
7. **Effect Sign** — T3a two-sided β ≠ 0 test; re-reference T3b from NB2 (T3b is OLS-primary-only gate)
8. **Sensitivity Forest Plot** — primary anchored at row 1 with a horizontal divider; remaining rows sorted by |β̂| descending (Simonsohn 2020 convention); rendered via `aeturrell/specification_curve` (Python, MIT, OLS-regression-based) or a manual matplotlib fallback. Rows included: primary, GARCH-X (NB2), decomposition-CPI (NB2), decomposition-PPI (NB2), three subsamples (NB2), A1 monthly, A4 release-day-excl, A5 lagged-RV, A6 bivariate, A8 oil-level, and A9 asymmetric rendered as two rows (β⁺, β⁻) for transparency. A2/A3/A7 annotated as "see NB2" in the dashboard panel. Row count depends on A9 rendering (13 rows under two-row A9, fewer if A9 is collapsed to a single row); exact count locked during implementation.
9. **Material-Mover Spotlight Tables** — full regression tables only for sensitivities whose β̂ both (a) falls outside the primary's 90% CI and (b) disagrees on the T3b sign/significance classification (the two-pronged I4R 2024 rule). This replaces the earlier collapsed single-rule version: when the primary T3b has PASSed (its CI excludes zero), the two prongs coincide in most cases, but the conjunction prevents false-positive flagging when primary CI is narrow and a sensitivity is merely a large-but-concordant estimate. The collapse is valid only under T3b PASS; if T3b fails, NB3 halts before this section and the question is moot.
10. **Final Gate Verdict** — aggregate T3b (NB2), T1, T2, T4, T5, T6, T7, material-mover count, and the bootstrap-HAC agreement flag from NB2 §3.5; write `gate_verdict.json`; trigger Jinja2 render of exec-layer `README.md` from committed JSON artifacts

Appendix: coefficient matrix for every specification evaluated, not only material movers.

Material-mover rule: two-pronged conjunction — β̂ exits the primary's 90% CI AND the T3b sign/significance classification changes. Condition: collapse to the single-prong form is valid only under T3b PASS; NB3 halts before §9 if T3b has FAILed upstream.

## 9. Handoff Contracts Between Notebooks

The pipeline has seven documented handoffs. Each is described in prose (no code shapes or function signatures).

NB1 hands off two things to both NB2 and NB3: a cleaning module that exposes two deterministic loader functions (one for the weekly panel, one for the daily panel), and a lightweight fingerprint artifact capturing row/column/date/checksum metadata of the cleaned panels. Downstream notebooks re-compute the fingerprint at load time and assert match before proceeding. NB1 also emits its decision ledger in-line as a markdown table and again as docstrings on each cleaning function, so the rationale travels with the code.

NB2 hands off two files to NB3 and Layer 2: a version-controlled JSON contract (the full specification of which is §4.4) and a gitignored pickle companion (§4.5). Both are written atomically in a single serialization routine. The JSON is the authoritative contract; the pickle is a convenience that preserves fit objects for richer residual diagnostics. Layer 2 consumes the JSON only.

NB3 hands off two things: a gate-verdict JSON file that aggregates test outcomes, material-mover count, reconciliation status, and the final PASS or FAIL; and an auto-rendered README at the notebooks root, generated from a Jinja2 template that reads both the gate-verdict JSON and the NB2 parameter JSON. A future Layer 2 design will consume NB3's material-mover list and the regime-dual-bands flag; that consumption contract is deferred to the Layer 2 design document.

Pickle version guard: NB2 records Python, statsmodels, arch, numpy, and pandas version strings in the JSON contract. NB3 asserts an exact major.minor match on load. On mismatch NB3 emits a WARNING, skips pickle-dependent cells (the T4 and T5 residual diagnostics become unavailable), and records `pkl_degraded: true` in the gate verdict. The gate verdict itself remains valid from the JSON contract alone.

## 10. Cell Count and Scope Estimates

| Notebook | Sections | Estimated cells |
|---|---|---|
| NB1 | 8 | ~38 (12 decisions × 2 cells each + 6 variable blocks × 2 cells each + setup/footer) |
| NB2 | 13 (incl. §3.5 block-bootstrap) | ~58 (each section has 3–5 cells including citation block) |
| NB3 | 9 | ~50 (7 tests × 3 cells + forest plot + spotlight loop + gate aggregation) |

Total: ~146 cells across the three notebooks. Approximate; citation-block requirement adds ~50% markdown overhead to a minimal-markdown draft.

## 11. Quality Gates

Per memory rule (Three-way spec/plan review): this design itself requires Code Reviewer + Reality Checker + Technical Writer review before implementation planning begins.

Post-implementation: each notebook reviewed by Reality Checker (numbers match expected ranges), Model QA (econometric correctness), Technical Writer (narrative clarity) per memory rule (Econ notebook handoff).

## 12. Open Questions / Deferred Items

- **Bai-Perron implementation package** — `ruptures` vs statsmodels `breaks_cusumolsresid`; decision deferred to implementation plan
- **Forest-plot library** — `aeturrell/specification_curve` vs manual matplotlib; first-preference the package, fallback to matplotlib if pip install blocked
- **A9 asymmetric surprise rendering** — resolved: two rows (β⁺, β⁻) in the forest plot for transparency; see NB3 §8
- **Exec-layer README auto-generation** — resolved: Jinja2 render from `gate_verdict.json` and `nb2_params_point.json`, committed to git, CI diff-checked against a fresh render; see §4.6
- **Layer 2 design** — separate design doc; depends on NB2 `nb2_params_point.json` existing and this design passing quality gates
- **`just notebooks` recipe** — the angstrom worktree already uses a `justfile`; the implementation plan adds a `notebooks:` recipe that runs nbconvert --execute on all three notebooks in order, rather than introducing a new Makefile

## 13. Non-Goals

- No Layer 2 simulator construction
- No pool parameterization
- No tick-concentration analysis (spec §4.5 mapping gap stays deferred)
- No new econometric tests beyond Rev 4's T1–T7 + A1–A9
- No departure from the pre-committed primary — the ladder and displayed alternatives are robustness checks, not candidate gate tests

## 14. References (external, evidence-backing)

- Andersen, Bollerslev, Diebold, Vega (2003, *AER*) — event-study framework
- Ankel-Peters, Brodeur et al. (2024, *Q Open*) — I4R robustness dashboard
- Bai, Perron (1998, *Econometrica*; 2003, *JAE*) — structural breaks
- Balduzzi, Elton, Green (2001, *JFQA*) — consensus rationality
- Barone-Adesi et al. (2008, *JBF*) — filtered historical simulation
- Bollerslev (1986, *JE*) — GARCH(1,1) baseline
- Bollerslev, Wooldridge (1992) — QMLE for ARCH models with misspecified likelihood
- Campbell, Lo, MacKinlay (1997) — CLM econometrics framework
- Chow (1960, *Econometrica*) — structural break test
- Conrad, Schoelkopf, Tushteva (2025, forthcoming *JE*) — replication-bundle convention baseline
- Engle, Rangel (2008, *RFS*) — Spline-GARCH
- Han, Kristensen (2014, *JBES*) — GARCH(1,1)-X with absolute-valued exogenous regressor (variance equation identification)
- Hansen, Lunde (2005, *JAE*) — GARCH-family point-estimate handoff convention (plug-in of fitted series; does NOT propagate covariance matrices)
- Heston, Nandi (2000, *RFS*) — GARCH-family covariance propagation via inverse Hessian in option pricing
- Jarque, Bera (1987, *Int. Statistical Review*) — normality test
- Levene (1960); Conover, Johnson, Johnson (1981, *Technometrics*) — variance heterogeneity (robust Brown-Forsythe variant)
- Ljung, Box (1978, *Biometrika*) — serial correlation
- Mincer, Zarnowitz (1969) — forecast rationality
- Newey, West (1987, *Econometrica*) — HAC covariance
- Politis, Romano (1994, *JASA*) — stationary bootstrap for time series (block-bootstrap baseline for NB2 §3.5)
- Rincón-Torres, Rojas-Silva, Julio-Román (2021, BanRep Borrador 1171) — Colombian FX-TES interdependence
- Simonsohn, Simmons, Nelson (2020, *Nature Human Behaviour*) — specification curve
- Wilson, Hilferty (1931, *PNAS*) — cube-root normal approximation

Full BibTeX entries in `references.bib` are authored during NB1 implementation.
