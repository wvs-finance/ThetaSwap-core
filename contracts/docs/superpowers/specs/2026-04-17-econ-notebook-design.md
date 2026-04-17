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
├── README.md                          exec layer — gate verdict, β̂ table, reconciliation status, links
├── references.bib                     single source of truth for all citations
├── cleaning.py                        applies NB1-documented cleaning decisions on top of econ_query_api
├── env.py                             DUCKDB_PATH, seed helpers, path constants
├── 01_data_eda.ipynb                  NB1
├── 02_estimation.ipynb                NB2
├── 03_tests_and_sensitivity.ipynb     NB3
├── estimates/
│   ├── nb2_params_point.json          Layer 1 → Layer 2 handoff contract (version-controlled)
│   ├── nb2_params_full.pkl            full fit objects (gitignored, reproducible on `make notebooks`)
│   └── gate_verdict.json              NB3 output for exec-layer README
├── figures/                           PNGs for README embedding
├── pdf/                               nbconvert exports (gitignored)
└── _nbconvert_template/               custom LaTeX template enforcing remove-input cell tags
```

`Colombia/` subpath future-proofs for Mexico/Peru/Chile replications of the same hedge thesis.

## 4. Artifact Contracts

### 4.1 `cleaning.py`

Pure Python module, no notebook state. Exposes deterministic functions that take a DuckDB connection and return cleaned pandas DataFrames. Honors the project's "query API is the only interface" rule (memory: Econ notebook handoff) by wrapping `econ_query_api` calls and applying NB1-ledger cleaning decisions. No randomness, no today-relative filters, no network I/O.

### 4.2 `references.bib`

BibTeX bibliography cited by every citation block in NB1/NB2/NB3. Rendered into PDFs via the nbconvert LaTeX template. Entries added incrementally as Analytics Reporter authors each section.

### 4.3 `env.py`

Path constants (DuckDB, estimates directory, figures directory), reproducibility seed helper, Python + library version pins documented alongside.

### 4.4 `nb2_params_point.json` (Layer 1 → Layer 2 handoff contract)

Version-controlled JSON. Contains:

- `ols_primary`: point estimates (β̂ on CPI surprise + 5 controls), HAC(4) covariance matrix Σ̂, n, R², adj-R²
- `garch_x`: {ω, α₁, β₁, δ, ν} point estimates + QMLE covariance matrix + log-likelihood + persistence
- `decomposition`: β₁ (CPI) and β₂ (standardized PPI) + covariance
- `subsamples`: per-regime (pre-2015-01-05, 2015-01-05 to 2021-01-04, post-2021-01-04) β̂, Σ̂, Wald-test p-value against pooling
- `reconciliation`: `"AGREE"` or `"DISAGREE"` per Rev 4 protocol (OLS ↔ GARCH-X within ±1 SE)
- `t3b_pass`: bool — OLS primary only
- `gate_verdict`: `"PASS"` | `"FAIL"`
- `spec_hash`: sha256 of upstream spec Rev 4 — NB3 asserts match on load

Format choice per research report §2: plug-in point estimates + full covariance matrix is the dominant convention in applied GARCH-option-pricing handoffs (Heston-Nandi, Duan, Hansen-Lunde 2005 JAE); no MCMC posterior required.

### 4.5 `nb2_params_full.pkl`

Convenience companion. Full `statsmodels.RegressionResults` for OLS + ladder + subsamples and `arch.ARCHModelResult` for GARCH-X. Gitignored. NB3 loads this for T4/T5 residual diagnostics.

### 4.6 `gate_verdict.json`

NB3 output. Aggregates per-test outcomes (T1–T7), material-mover count, reconciliation status, and final PASS/FAIL. Consumed by `README.md` at notebooks root.

## 5. Cross-Cutting Rules (NON-NEGOTIABLE)

### 5.1 Citation block before every decision, test, and spec choice

Every decision cell, test cell, and specification-choice cell in NB1/NB2/NB3 is preceded by a dedicated markdown cell with exactly four parts:

1. **Reference** — paper, URL, section/equation
2. **Why used** — what question this answers
3. **Relevance to our results** — how outcome modifies β̂, CI, or gate verdict
4. **Connection to simulator (Layer 2)** — how this output feeds RAN payoff; or "Does not feed Layer 2" with justification

Enforced by Analytics Reporter during authoring; reviewers reject any unreferenced decision.

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
8. **Decision Ledger + `cleaning.py` emission** — 12-row table; validation assertions against `load_clean_weekly_panel(conn)`

Total: 12 ledger decisions per Conrad et al. 2025 granularity precedent (23 decisions for 15 input series → scale to 12 for our 7 input series).

Plot convention: standalone per-variable, no 3×2 grid (Kevin Sheppard `arch` examples + Conrad 2025 replication precedent).

## 7. NB2 Design — Estimation (Pre-Committed Primary + Co-Primaries)

**Purpose:** Produce pre-committed primary β̂, GARCH-X co-primary δ̂, decomposition β₁/β₂, subsample regime estimates, reconciliation verdict; serialize Layer 2 handoff artifacts.

Sections:

1. **Setup + Spec Hash Check + Verdict Box** — assert spec_hash matches Rev 4; verdict box placeholder
2. **Descriptive Statistics** — full-sample mean/SD/skew/kurtosis, no conditioning on release weeks
3. **OLS Primary — Coefficient Ladder** — Columns 1–6 nested controls; Column 6 = pre-committed primary highlighted; Newey-West HAC(4)
4. **OLS Diagnostics (displayed, not branching)** — JB, Breusch-Pagan, Durbin-Watson, Ljung-Box Q(1..8)
5. **Student-t OLS Alternative (displayed)** — refit primary with Student-t likelihood regardless of JB outcome; side-by-side with Gaussian
6. **GARCH(1,1)-X Co-Primary** — `|s_t^CPI|` in variance equation (Han-Kristensen 2014); convergence guard (BFGS, 500-iter ceiling, Hessian PD check)
7. **CPI-vs-PPI Decomposition Co-Primary** — re-estimate primary with standardized ΔIPP_t added; report β₁ and β₂
8. **Subsample Estimates (Regime Check)** — OLS primary on each of three regimes from `SUBSAMPLE_SPLITS` API constant; Wald test for pooling; feeds Layer 2 regime-switching
9. **T3b Gate Evaluation (OLS primary only)** — β̂ − 1.28·SE > 0; adj-R² ≥ 0.15; explicit note that GARCH-X cannot override
10. **Reconciliation Dashboard** — OLS / GARCH-X / decomposition side-by-side; AGREE if within ±1 SE, else DISAGREE; Layer 2 consumes both bands on disagreement
11. **Serialization** — write `nb2_params_point.json` + `nb2_params_full.pkl`; full covariance matrices (not just SE vectors) for Layer 2 bootstrap draws
12. **Economic Magnitude (one-liners)** — β̂ → bp per 1-σ CPI surprise; full RAN-payoff translation deferred to Layer 2

Bootstrap sleeve for Layer 2: K=500 parameter vectors drawn from N(θ̂, Σ̂) in Layer 2 itself, not pre-drawn in NB2. Matches filtered-historical-simulation convention (Barone-Adesi et al. 2008 JBF).

## 8. NB3 Design — Specification Tests + Sensitivity + Gate Verdict

**Purpose:** Run T1–T7 spec tests with both economic and statistical interpretation, run A1–A9 sensitivities with forest plot + spotlight, deliver final gate verdict to exec-layer README.

Grouping rule: by diagnostic target (I4R 2024 + Simonsohn 2020 convention), not statistical attack-surface jargon. Numeric T-IDs preserved in subsection titles.

Sections:

1. **Setup + Gate Prerequisite Check** — load `nb2_params_point.json`; assert spec_hash
2. **Residual Diagnostics** — T4 Ljung-Box Q, T5 Jarque-Bera
3. **Stability & Regime** — T6 Chow/Bai-Perron, T7 intervention-control adequacy
4. **Effect Sign & Heterogeneity** — T3a (re-reference T3b from NB2)
5. **Variance Heterogeneity** — T2 Levene release vs non-release
6. **Exogeneity of Forecast Construction** — T1 consensus rationality F-test
7. **Sensitivity Forest Plot** — 12 rows; primary anchored at row 1 with horizontal divider; remaining sorted by |β̂| descending (Simonsohn 2020 convention); via `aeturrell/specification_curve` or manual matplotlib. Rows included: primary, GARCH-X (NB2), decomposition-CPI (NB2), decomposition-PPI (NB2), three subsamples (NB2), A1 monthly, A4 release-day-excl, A5 lagged-RV, A6 bivariate, A8 oil-level. A2/A3/A7 annotated as "see NB2" in dashboard panel
8. **Material-Mover Spotlight Tables** — full regression tables only for sensitivities where β̂ exits primary's 90% CI (I4R 2024 dashboard rule collapsed under pre-committed one-sided framing)
9. **Final Gate Verdict** — aggregate T3b (NB2) + T1/T2/T4/T5/T6/T7 + material-mover count; write `gate_verdict.json`; update exec-layer `README.md`

Appendix: coefficient matrix for all 12 specifications (not just material movers).

Material-mover rule (locked): β̂ outside primary's 90% CI. Rationale per research report §3: I4R 2024 two-pronged rule (sign + significance agreement) collapses to a single CI-containment check under one-sided pre-commitment.

## 9. Handoff Contracts Between Notebooks

| Producer | Consumer | Artifact | Format |
|---|---|---|---|
| NB1 | NB2, NB3 | `cleaning.load_clean_weekly_panel(conn)` + `load_clean_daily_panel(conn)` | Python module |
| NB1 | NB2, NB3 | Decision ledger (12 rows) | Markdown table in NB1 §8; documented in `cleaning.py` docstrings |
| NB2 | NB3 | `estimates/nb2_params_point.json` | JSON contract |
| NB2 | NB3 | `estimates/nb2_params_full.pkl` | Pickle (gitignored) |
| NB2 | Layer 2 simulator | `estimates/nb2_params_point.json` | JSON contract (same file, dual consumer) |
| NB3 | README exec layer | `estimates/gate_verdict.json` | JSON |
| NB3 | Layer 2 simulator (future) | Material-mover list + regime-specific dual bands flag | Section reference only; Layer 2 design will define the consumption contract |

Pickle version guard: NB2 records Python + statsmodels + arch version strings in `nb2_params_point.json`; NB3 asserts compatibility on load.

## 10. Cell Count and Scope Estimates

| Notebook | Sections | Estimated cells |
|---|---|---|
| NB1 | 8 | ~38 (12 decisions × 2 cells each + 6 variable blocks × 2 cells each + setup/footer) |
| NB2 | 12 | ~55 (each section has 3–5 cells including citation block) |
| NB3 | 9 | ~50 (7 tests × 3 cells + forest plot + spotlight loop + gate aggregation) |

Total: ~143 cells across the three notebooks. Approximate; citation-block requirement adds ~50% markdown overhead to a minimal-markdown draft.

## 11. Quality Gates

Per memory rule (Three-way spec/plan review): this design itself requires Code Reviewer + Reality Checker + Technical Writer review before implementation planning begins.

Post-implementation: each notebook reviewed by Reality Checker (numbers match expected ranges), Model QA (econometric correctness), Technical Writer (narrative clarity) per memory rule (Econ notebook handoff).

## 12. Open Questions / Deferred Items

- **Bai-Perron implementation package** — `ruptures` vs statsmodels `breaks_cusumolsresid`; decision deferred to implementation plan
- **Forest-plot library** — `aeturrell/specification_curve` vs manual matplotlib; first-preference the package, fallback to matplotlib if pip install blocked
- **A9 asymmetric surprise rendering** — single row in forest plot with combined β̂ or two rows (β⁺, β⁻); decision deferred; favoring two rows for transparency
- **Exec-layer README auto-generation** — regenerated on `make notebooks` or manually curated; decision deferred; favoring auto-generation from `gate_verdict.json` for reproducibility
- **Layer 2 design** — separate design doc; depends on NB2 `nb2_params_point.json` existing and this design passing quality gates

## 13. Non-Goals

- No Layer 2 simulator construction
- No pool parameterization
- No tick-concentration analysis (spec §4.5 mapping gap stays deferred)
- No new econometric tests beyond Rev 4's T1–T7 + A1–A9
- No departure from the pre-committed primary — the ladder and displayed alternatives are robustness checks, not candidate gate tests

## 14. References (external, evidence-backing)

- Andersen, Bollerslev, Diebold, Vega (2003, AER) — event-study framework
- Bai, Perron (1998; 2003, JAE) — structural breaks
- Balduzzi, Elton, Green (2001, JFQA) — consensus rationality
- Barone-Adesi et al. (2008, JBF) — filtered historical simulation
- Bollerslev (1986, JE) + Han-Kristensen (2014, JE) — GARCH(1,1)-X with absolute regressor
- Campbell-Lo-MacKinlay (1997) — CLM econometrics framework
- Chow (1960, Econometrica) — structural break test
- Conrad, Schoelkopf, Tushteva (2025) — replication-bundle convention baseline
- Engle, Rangel (2008, RFS) — Spline-GARCH
- Hansen, Lunde (2005, JAE) — GARCH-family handoff convention
- Jarque, Bera (1987, IntStatRev) — normality test
- Levene (1960); Conover et al. (1981) — variance heterogeneity
- Ljung, Box (1978, Biometrika) — serial correlation
- Mincer, Zarnowitz (1969) — forecast rationality
- Newey, West (1987, Econometrica) — HAC covariance
- Rincón-Torres, Rojas-Silva, Julio-Román (2021, BanRep be_1171) — Colombian FX-TES interdependence
- Simonsohn, Simmons, Nelson (2020, Nature Human Behaviour) — specification curve
- Ankel-Peters, Brodeur et al. (2024, Q Open) — I4R robustness dashboard
- Wilson, Hilferty (1931, PNAS) — cube-root normal approximation

Full BibTeX entries in `references.bib` to be authored during NB1 implementation.
