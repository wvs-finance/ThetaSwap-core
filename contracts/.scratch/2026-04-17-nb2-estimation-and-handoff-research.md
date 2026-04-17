# NB2 Structure & Layer 1 → Layer 2 Handoff: Evidence-Based Research

Date: 2026-04-17
Scope: Answers three questions for the NB2 (estimation) notebook of the structural-econ FX-vol-on-CPI-surprise project, and for the downstream RAN structural-simulation notebook.

---

## Question 1 — NB2 structure in published replication bundles

### Precedent 1a: Conrad, Schoelkopf, Tushteva (2025) "Long-Term Volatility Shapes the Stock Market's Sensitivity to News"
- Repo: https://github.com/juliustheodor/long-term-volatility-news
- Main regression file: `code/3_Empirical Analysis.do` (~157 KB Stata do-file)
- GARCH estimation: separate `mf2garch estimation/MF2GARCH_estimation.m` (MATLAB), run FIRST; produces `MF2optimalBICinmean.dta` consumed by `3_Empirical Analysis.do`.

Conventions demonstrated (verified by reading the do-file):
- **Coefficient ladder: YES.** Nested specifications built via `eststo:` chain — baseline OLS, then volatility components added one at a time (`htau_mean_sqrt`, `tau_mean_sqrt`, `h_mean_sqrt`), then combined. Exported with `esttab ... using Table2.tex, ar2 replace se star` as a single multi-column table.
- **GARCH and OLS live in SEPARATE files.** MF2-GARCH output is serialized to `.dta`, then merged into the OLS pipeline via `merge m:1 ... using ".../MF2optimalBICinmean.dta"`.
- **JB / residual diagnostics: ABSENT from the main regression file.** Only `ar2` (adjusted R²) is reported; no Jarque-Bera, Ljung-Box, or normality tests.
- **Economic magnitude interpretation: embedded inline** with `summ`, percentile extraction, then `disp "Annualized: " sqrt(252*`taupercentileCC')` — alongside regression output, not deferred to a separate "interpretation" section.

### Precedent 1b: Kevin Sheppard `arch` package examples (github.com/bashtage/arch/tree/main/examples)
- `univariate_volatility_modeling.ipynb`: individual models demonstrated in isolation — no ladder; Student-t appears as a parallel distributional choice (its own titled section), not as a residual-diagnostic fallback.
- `univariate_forecasting_with_exogenous_variables.ipynb`: focuses on GARCH-X data-structure mechanics; **no JB, no normality testing, no ladder, no economic-magnitude translation.** Pattern = tutorial exposition, not applied-econ artifact.

### Verdict for the user's NB2 plan
- Coefficient ladder (Column 1–6 nested controls): **MATCHES published applied-econ precedent (Conrad et al. 2025).** Keep it.
- GARCH-X in the SAME notebook as OLS primary: **DEVIATES from Conrad (which separates them).** For NB2, co-locating is defensible because (a) it is a single author's notebook, not a two-person Stata/MATLAB pipeline, and (b) reconciliation requires both fits side-by-side. Recommend keeping co-located but with a clearly-headed second section.
- JB → Student-t fallback: **No strong precedent for auto-running in the estimation stage.** Conrad does not do it. `arch` presents Student-t as a parallel model, not a fallback. Recommendation: run JB in NB2 as part of the OLS primary's diagnostic cell (it is cheap), but make the Student-t fallback a DISPLAYED decision in the output — i.e., fit both, show both, let the reviewer see the choice. Don't auto-swap silently.
- Economic magnitude translation: **In-estimation (Conrad's convention) is fine for NB2.** A one-line "β̂ = X implies Y bp per 1-σ surprise" print alongside the coefficient is idiomatic. Reserve the full RAN-payoff translation for the downstream simulator notebook.

---

## Question 2 — Estimation → structural-simulation handoff convention

### Precedent 2a: `edoberton/heston_nandi_garch` (Python, Heston–Nandi GARCH(1,1))
- File: https://github.com/edoberton/heston_nandi_garch/blob/main/HNGarch.py
- Handoff pattern (direct quotes from source):
  - MLE returns 5 parameters stored as instance attributes: `self.omega`, `self.alpha`, `self.beta`, `self.gamma`, `self.p_lambda`.
  - **Covariance available**: `hess_inv = res.hess_inv.todense()`; `self.std_errors = np.sqrt(diag)`. Full Hessian inverse kept.
  - Simulator consumes them as a list: `params = [self.omega, self.alpha, self.beta, self.gamma_star, self.p_lambda]`.
  - Residual distribution hardcoded: `z_star = normal(0,1)` — Gaussian only.
  - **Point estimates only**; no parameter-draw sampling, no bootstrap.

### Precedent 2b: Conrad et al. 2025
- MF2-GARCH fitted in MATLAB; output serialized to Stata `.dta` → CSV-equivalent format. Only point estimates of the volatility components (`h_BIC`, `tau_BIC`, `htau_BIC`) are passed forward as fitted series — not the parameter covariance matrix.

### Precedent 2c: Hansen & Lunde (2005) JAE (330-model comparison)
- JAE data archive: http://qed.econ.queensu.ca/jae/datasets/hansen002/ — replication files in plain-text / CSV per JAE convention. Point estimates of each of the 330 fits passed forward; no posterior, no covariance.

### Verdict
- **Just point estimates is the dominant convention in applied GARCH-option-pricing code** (Heston-Nandi, Duan 1995 implementations, Conrad 2025). Covariance matrix is kept but rarely propagated.
- **No strong precedent for full MCMC posterior handoff** in the GARCH→option-pricing literature. Bayesian handoffs exist in DSGE (Dynare posterior .mat files), not here.
- **File format**: CSV/`.dta`/`.mat` for fitted series; raw Python attributes or pickled objects for parameter bundles. No single dominant format; the Conrad convention (tabular .dta/CSV for fitted series + parameters) is cleanest for non-Python downstream consumers.

### Recommended Layer 1 → Layer 2 serialization for the RAN project
Two artifacts, written by NB2 on completion:

1. `nb2_params_point.json` — human-readable, version-controlled:
   ```
   {
     "ols_primary":  {"beta_s": ..., "se_beta_s": ..., "controls": {...},
                      "hac_lag": 4, "n": ..., "r2": ...},
     "garch_x":      {"omega": ..., "alpha_1": ..., "beta_1": ...,
                      "delta_cpi_surprise": ..., "nu_student_t": ...,
                      "se_vector": [...], "loglik": ...},
     "decomposition": {"beta_cpi": ..., "beta_ppi": ..., "se": [...]},
     "subsamples":   {"pre_2020": {...}, "post_2020": {...}},
     "spec_hash":    "<sha256 of pre-commit spec>"
   }
   ```
2. `nb2_params_full.pkl` — Python-native: the full `arch.ARCHModelResult` object for GARCH-X (keeps Hessian, residuals, conditional_volatility series) plus statsmodels `RegressionResults` for OLS. Loaded by the Layer 2 notebook via `pickle.load`.

JSON is the contract; pickle is the convenience companion. Both committed under `research/model/estimates/`.

---

## Question 3 — Layer 1 → Layer 2 coupling: preserving econometric honesty

### Precedent: Milionis et al. 2022 (LVR, arXiv:2208.06046)
- Closed-form LVR is a function of instantaneous volatility σ², not of a fitted GARCH object directly. Downstream LVR-based simulators (e.g. Alexander-Lambert-Fritz 2025, arXiv:2502.04097) consume σ as a **point-estimate scalar or a path**, not a posterior. No bootstrap propagation in the published AMM-simulator code reviewed.

### Precedent: Heston-Nandi / Duan GARCH option pricing
- Plug-in convention dominates. Parameter-uncertainty confidence bands on option prices exist in Barone-Adesi et al. (filtered historical simulation), but are the exception, not the rule.

### Verdict — honest coupling pattern for the RAN simulator
- **Uncertainty propagation**: Recommend plug-in point estimate as the HEADLINE result, plus a parametric bootstrap sleeve — draw K=500 parameter vectors from `N(θ̂, Σ̂)` (Σ̂ = HAC-robust for OLS, QMLE Hessian inverse for GARCH-X), run the RAN Monte Carlo per draw, report the 5-95% band on LP payoff. This matches the ScoPe (Csáji 2018, arXiv:1807.08390) and Horowitz (2018, arXiv:1809.04016) bootstrap-in-econometrics tradition.
- **Regime stability**: If subsample estimates (`pre_2020`, `post_2020`) disagree meaningfully (e.g., Wald test rejects pooling), Layer 2 should run THE SIMULATOR TWICE with regime-specific β̂ and report both. Do not pool silently.
- **OLS vs GARCH-X reconciliation when they disagree**: No clean precedent; this is the user's call. Recommended protocol:
  - If both agree within ±1 SE on the CPI-surprise loading → use OLS β̂ as the headline scalar for the RAN mean-equation input; use GARCH-X ω, α₁, β₁, ν_t for the variance process.
  - If they disagree → Layer 2 runs TWO simulations, one parameterized by OLS+Gaussian-homoskedastic residuals and one by GARCH-X+Student-t. Report both payoff distributions. The econometric disagreement becomes a visible part of the structural result, not hidden by a choice.
  - T3b gate (β̂ − 1.28·SE > 0) applies to the OLS primary only; if the gate fails under OLS but passes under GARCH-X, the project's pre-commitment requires reporting failure — do not let GARCH-X "rescue" the gate.

---

## Locked recommendations

1. **NB2 section order (LOCKED):**
   1. Data load + spec hash check
   2. Descriptive statistics (RV, CPI surprise, controls)
   3. OLS primary with coefficient ladder (6 columns: baseline + 5 cumulative controls), Newey-West HAC(4)
   4. OLS diagnostics: JB on residuals, Breusch-Pagan, Durbin-Watson — all displayed, no silent branching
   5. Student-t OLS as a DISPLAYED alternative (not a fallback) if JB rejects
   6. GARCH(1,1)-X with CPI-surprise in the variance equation
   7. CPI-vs-PPI decomposition (co-primary)
   8. Subsample estimates (regime check)
   9. T3b gate evaluation on OLS primary
   10. Reconciliation dashboard: side-by-side OLS / GARCH-X / decomposition coefficients and signs
   11. Serialization: write `nb2_params_point.json` + `nb2_params_full.pkl`
   12. One-line economic magnitude prints ("β̂ = X ⇒ Y bp/σ"); defer full RAN-payoff narrative to Layer 2

2. **Layer 2 handoff contract (LOCKED):**
   - Point estimates + HAC/QMLE covariance matrix + residual-distribution choice (Gaussian / Student-t ν)
   - Format: `nb2_params_point.json` (contract) + `nb2_params_full.pkl` (convenience)
   - Parameters serialized: β̂ (mean eq.), {ω, α₁, β₁} (variance eq.), δ (CPI-surprise loading in variance), ν (Student-t df), Σ̂ (full covariance), subsample-specific replicates
   - No MCMC posterior (no precedent, not required by pre-commitment)

3. **OLS / GARCH-X reconciliation rule (LOCKED):**
   - Agreement within ±1 SE → OLS β̂ feeds mean equation, GARCH-X feeds variance process in Layer 2.
   - Disagreement → Layer 2 runs BOTH parameterizations; report both payoff distributions; econometric disagreement surfaces as a structural uncertainty band, not a silent choice.
   - T3b gate pass/fail determined by OLS primary only; GARCH-X cannot override.

---

## Honest limitations

- No public replication code was located for Cao-Kogan-Tsoukalas 2025 (SSRN 4591447); pattern inferred from class of structural-AMM simulators only.
- No AEA/JAE macro-announcement paper with a public JB→Student-t auto-fallback convention was found; this appears to be a gap the user's project is reasonable to fill with a displayed-alternative pattern rather than an auto-branching pattern.
- Parametric-bootstrap sleeve for Layer 2 is a user-facing honesty recommendation, not a dominant published convention in AMM simulators (which tend to plug-in). The user should decide whether to adopt it based on the RAN audience.
