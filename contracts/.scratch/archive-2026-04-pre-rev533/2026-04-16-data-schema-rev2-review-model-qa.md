# Model QA Review: Data Schema & Acquisition Strategy Rev 2

**Reviewer:** Model QA Specialist
**Date:** 2026-04-16
**Document under review:** `specs/2026-04-16-data-schema-acquisition.md` (Rev 2)
**Upstream spec:** `specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)
**Review scope:** 8 items per user request

---

## 1. Variable Completeness

**Methodology:** Enumerated every variable appearing in the upstream spec's primary OLS (section 4.1), GARCH-X co-primary (section 4.1 equation B), co-primary decomposition (section 4.1 decomposition equation), sensitivities A1-A9 (section 6.2), and spec tests T1-T7 (section 5). Checked each against the data schema's raw tables and derived panels.

### 1.1 Primary OLS: RV^(1/3) = alpha + beta*s_CPI + gamma_1*s_US_CPI + gamma_2*s_BanRep + gamma_3*VIX + gamma_4*I + gamma_5*r_oil + epsilon

| Variable | Schema column | Table | Status |
|---|---|---|---|
| RV^(1/3) | `rv_cuberoot` | weekly_panel | OK |
| RV (raw) | `rv` | weekly_panel | OK |
| log(RV) | `rv_log` | weekly_panel | OK |
| s_CPI (survey) | `cpi_surprise_survey` (deferred) | weekly_panel | OK (deferred, correct) |
| s_CPI (AR(1) fallback) | `cpi_surprise_ar1` | weekly_panel | OK |
| s_US_CPI | `us_cpi_surprise` | weekly_panel | OK |
| s_BanRep | `banrep_rate_surprise` (deferred) | weekly_panel | OK (deferred, correct) |
| VIX | `vix_avg` | weekly_panel | OK |
| I_t | `intervention_dummy` (deferred) | weekly_panel | OK (deferred, correct) |
| r_oil | `oil_return` | weekly_panel | OK |

### 1.2 GARCH(1,1)-X co-primary: h_t = omega + alpha_1*eps_{t-1}^2 + beta_1*h_{t-1} + delta*|s_CPI|

| Variable | Schema column | Table | Status |
|---|---|---|---|
| r_t (daily COP/USD return) | `cop_usd_return` | daily_panel | OK |
| |s_CPI| on release date | `abs_cpi_surprise` | daily_panel | OK |
| Signed surprise (for asymmetric variant) | `cpi_surprise_ar1_daily` | daily_panel | OK |

### 1.3 Co-primary decomposition

| Variable | Schema column | Table | Status |
|---|---|---|---|
| dane_ipp_pct (raw PPI MoM change) | `dane_ipp_pct` | weekly_panel | OK |
| Standardized PPI (tilde{s}_PPI) | N/A (estimation applies transform per section 4.3) | weekly_panel | OK (boundary correct) |

### 1.4 Sensitivities A1-A9

| Sensitivity | Required data | Schema support | Status |
|---|---|---|---|
| A1 (monthly horizon) | Monthly RV aggregation | Computable from `banrep_trm_daily` raw | OK (section 7 notes this explicitly) |
| A2 (CPI vs PPI decomposition) | Separate CPI/PPI columns | `cpi_surprise_ar1` + `dane_ipp_pct` + `is_cpi_release_week` + `is_ppi_release_week` | OK |
| A3 (sub-sample splits) | Date column for filtering | `week_start` | OK |
| A4 (release-day exclusion) | Daily data to recompute RV excluding release days | `banrep_trm_daily` + `dane_release_calendar` | OK (section 7 notes this) |
| A5 (lagged RV control) | Lagged `rv` or `rv_log` | Computable from `weekly_panel` at estimation time | OK |
| A6 (bivariate, no controls) | Subset of primary variables | Already in weekly_panel | OK |
| A7 (GARCH-X) | daily_panel | Covered by section 4.2 | OK |
| A8 (oil level control) | log(WTI price level) | `oil_log_level` | OK |
| A9 (asymmetric effects) | s^+ = max(s,0), s^- = min(s,0) | Computable from `cpi_surprise_ar1` at estimation time | OK |

### 1.5 Specification Tests T1-T7

| Test | Required data | Schema support | Status |
|---|---|---|---|
| T1 (consensus rationality: E[s_t | s_{t-1}, RV_{t-1}, VIX_{t-1}] = 0) | Lagged surprise, RV, VIX | All in weekly_panel | OK |
| T2 (Levene test: Var(RV|release) > Var(RV|non-release)) | release-week flag | `is_cpi_release_week`, `is_ppi_release_week` | OK |
| T3a, T3b (beta significance) | Estimation output | N/A (not a data column) | OK |
| T4 (Ljung-Box on residuals) | Estimation output | N/A | OK |
| T5 (Jarque-Bera on residuals) | Estimation output | N/A | OK |
| T6 (Chow/Bai-Perron structural break) | Date-ordered panel | `week_start` | OK |
| T7 (intervention control: beta stable with/without I_t) | `intervention_dummy` | Deferred but schema-ready | OK |

### 1.6 Remaining Gaps

**FLAG-1: No daily controls in GARCH-X for VIX and oil beyond the basic columns.**

The upstream GARCH-X equation in section 4.1 shows only |s_CPI| as the exogenous regressor in the variance equation. However, the upstream spec's A7 description does not explicitly include daily VIX or oil in the GARCH-X variance equation. The daily_panel does include `vix` and `oil_return` columns. If the mean equation of the GARCH-X needs daily controls (standard practice: r_t = mu + gamma*VIX_t + ...), the daily columns are present. No gap here -- this is covered.

**FLAG-2: `dane_ipc_pct` column exists in weekly_panel but the upstream primary uses `s_CPI` (surprise), not raw IPC change.**

This is actually correct: `dane_ipc_pct` is the raw input from which `cpi_surprise_ar1` is computed. The raw change is also useful for diagnostics (e.g., verifying the AR(1) residual). No gap.

**Verdict on completeness: PASS.** Every variable required by the primary OLS, GARCH-X co-primary, co-primary decomposition, sensitivities A1-A9, and spec tests T1-T7 is either present as a column in the derived panels, present in raw tables for recomputation, or correctly deferred (BanRep survey, IBR, SUAMECA).

---

## 2. daily_panel Correctness for GARCH(1,1)-X

### 2.1 Variance Equation Mapping

The upstream equation: h_t = omega + alpha_1 * epsilon_{t-1}^2 + beta_1 * h_{t-1} + delta * |s_t^CPI|

The daily_panel provides:
- `cop_usd_return` (r_t) -- from which epsilon_t = r_t - mu is computed during estimation
- `abs_cpi_surprise` placed on the **exact release date**, 0.0 on all other days

This is correct. The GARCH(1,1) internal dynamics (epsilon_{t-1}^2, h_{t-1}) are latent states computed by the estimation engine, not stored in the panel. The panel only needs to supply the observable exogenous variable (|s_CPI|) and the return series.

### 2.2 Surprise Placement on Exact Release Date

The schema places the surprise on the exact DANE release date. The upstream spec section 3.3 notes: "TRM is a single daily rate -- intraday price discovery is not captured. DANE releases typically published between 6-8pm COT; the reaction appears in the NEXT business day's TRM."

**FLAG-3: Surprise placement timing ambiguity for GARCH-X.**

The daily_panel places |s_CPI| on the release date itself (the day DANE publishes the number). But the data schema's own section 3.1 acknowledges that "the reaction appears in the NEXT business day's TRM." For the GARCH-X variance equation, this means delta*|s_CPI| on day t should predict elevated h_t, but the actual return reaction r_t occurs on day t+1. Placing the surprise on day t means delta captures the effect on same-day conditional variance, while the realized return jump is on t+1.

This is not necessarily wrong -- it depends on interpretation:
- If the GARCH-X is estimating "does knowledge of the surprise increase conditional variance on the announcement day?", placement on day t is correct (forward-looking variance).
- If the GARCH-X is estimating "does the surprise increase the variance of the day the market reacts?", then placement on day t+1 is correct.

The upstream spec does not disambiguate this. The weekly OLS sidesteps the issue because the release and the reaction fall within the same week. For the daily GARCH-X, this is a material design choice.

**Severity: FLAG.** The estimation module should test both placements (day t and day t+1) as a robustness check. The data pipeline should document which convention it implements and why. The current choice (day t) is defensible but not the only valid one.

### 2.3 Daily Controls

The daily_panel includes `vix` (daily VIXCLS) and `oil_return` (daily WTI log-return). These are sufficient for a GARCH-X mean equation with daily controls. The variance equation in the upstream spec only includes |s_CPI| as exogenous, so no additional daily controls are needed in the variance equation itself.

**Verdict: PASS WITH FLAG** (FLAG-3 on surprise placement timing).

---

## 3. NULL vs 0 Semantics

### 3.1 The 0.0 Convention for Non-Release Weeks

The schema stores 0.0 for surprise columns on non-release weeks. The econometric rationale: in the OLS equation, a non-release week has no news, so the surprise contribution to RV should be zero. Setting s_t = 0 on non-release weeks means the surprise term beta*s_t = 0, and the intercept + controls explain the full RV for that week. This is the standard approach in event-study regressions (Andersen et al. 2003 use indicator-interacted surprises, which is algebraically equivalent).

This is **correct** for the OLS primary and co-primary decomposition.

### 3.2 Edge Cases

**FLAG-4: The 0.0 convention inflates the kurtosis of the surprise distribution.**

With ~260 release weeks out of ~1,100 total, approximately 76% of observations have s_t = 0. The surprise distribution is a mixture: a point mass at zero (~76%) plus a continuous distribution (~24%). This is not a bias issue for OLS coefficient estimation (the zero observations are informative: "no news, what is baseline vol?"), but it affects:

1. **Jarque-Bera test (T5):** The residual distribution will inherit the mixture structure. JB may reject normality partly due to the zero-inflation, not due to genuine non-normality of the error term. Recommendation: run T5 on the full sample AND on the release-week subsample separately.

2. **Heteroskedasticity of residuals:** Non-release weeks have residual variance = Var(epsilon | no news), while release weeks have residual variance = Var(epsilon | news). This is exactly what Newey-West HAC handles (already specified), so no bias, but it does motivate the Levene test T2 as a pre-check.

3. **GARCH-X daily panel:** The 0.0 convention is even more extreme -- approximately 250 release days out of ~5,500 daily observations (4.5%). The GARCH-X delta coefficient is identified from <5% of observations. This is not inherently problematic (exogenous variables that are mostly zero are common in event-study GARCH models), but the standard errors on delta will be large relative to the OLS beta.

**Severity: FLAG (not BLOCK).** The 0.0 convention is correct. The edge cases affect test interpretation, not coefficient consistency. Document the mixture structure in estimation diagnostics.

### 3.3 An Actual 0.0 Surprise vs No Release

There is a subtle distinction: on a release week, if actual CPI exactly equals the AR(1) forecast, the surprise is genuinely 0.0. The schema cannot distinguish this from a non-release week (both store 0.0 in the surprise column). However, the `is_cpi_release_week` flag resolves this ambiguity -- the estimation module can use the flag to identify release weeks where the surprise happened to be zero vs weeks with no release at all. This is correctly handled.

**Verdict: PASS.** The 0.0 semantics are econometrically correct. Edge cases are real but manageable at the estimation stage.

---

## 4. RV Computation from TRM vs DEXCOUS

### 4.1 Source Change Impact

FRED DEXCOUS (had it existed) would have been a noon buying rate in New York, denominated as USD per COP or COP per USD depending on convention. BanRep TRM is the official Colombian benchmark, computed from actual interbank COP/USD transactions on SET FX.

Key differences affecting RV:

1. **Timing:** DEXCOUS would reflect New York noon; TRM reflects the weighted average of Colombian trading-day transactions. Since DANE releases occur at 6-8pm COT (after both markets), the timing difference is negligible for weekly RV.

2. **Quote convention:** TRM is COP per 1 USD (direct quote for Colombia). The RV computation uses log-returns r_d = log(P_d / P_{d-1}), which is invariant to quote direction (log(1/x_d / (1/x_{d-1})) = -log(x_d/x_{d-1})), so a USD/COP vs COP/USD difference only flips the sign of returns, not the magnitude. Since RV = sum(r_d^2), the sign cancels. No impact.

3. **Liquidity/bid-ask:** TRM from SET FX is based on actual interbank transactions; a FRED cross-rate would typically be an indicative rate. TRM is likely LESS noisy than a FRED indicative rate, which means RV from TRM is a cleaner measure of true FX volatility with less microstructure noise. This is an improvement, not a degradation.

4. **Holiday calendar:** TRM follows Colombian business days; DEXCOUS would have followed US business days. This means TRM captures Colombian trading days that DEXCOUS would miss (Colombian workdays that are US holidays) and vice versa. For weekly RV, this changes `n_trading_days` slightly but does not bias the measure.

### 4.2 Interpretation

RV from TRM measures realized volatility of the Colombian interbank COP/USD rate. This is actually MORE aligned with the upstream spec's economic question (Colombian price-level surprise affecting Colombian FX vol) than a New York-based DEXCOUS rate would have been. The LHS variable is improved by the switch.

**FLAG-5: The upstream spec (Rev 4) section 4.3 table still references FRED DEXCOUS and marks it as "confirmed free-tier".**

The data schema's section 8 correctly flags this as requiring an upstream amendment. But until the upstream spec is amended, there is a document inconsistency. The data schema is correct; the upstream spec is stale on this point.

**Verdict: PASS.** TRM is a superior source for RV computation. No methodological change needed. The upstream spec amendment (section 8 of the data schema) must be executed.

---

## 5. AR(1) Surprise Construction

### 5.1 US CPI AR(1) Specification

The schema specifies (section 4.1, "US CPI surprise construction"):
- Source: CPIAUCSL (monthly, from `fred_monthly`)
- Method: AR(1) on MoM % changes
- Window: expanding (not rolling)
- Warmup: first 12 months -- their surprises are not used
- Surprise = actual - AR(1) forecast
- Mapped to release week via `bls_release_calendar`

This is correctly specified. The expanding window means the AR(1) coefficients are re-estimated each month using all data up to t-1, which avoids look-ahead bias. The 12-month warmup provides a minimum of 12 observations for the first AR(1) estimation (just barely adequate for a 2-parameter model: intercept + AR(1) coefficient).

### 5.2 Colombian CPI AR(1) Specification

The schema specifies (section 4.1, "Colombian CPI AR(1) surprise construction"):
- Source: DANE IPC MoM % changes (from `dane_ipc_monthly`)
- Same method as US CPI: expanding-window AR(1)
- Warmup: first 12 months of DANE IPC
- Download starts 2002-01-01 (section 3.4), estimation sample starts ~2003

This matches. The 12-month warmup starting from 2002-01-01 means the first usable surprise is approximately 2003-01-01, aligning with the upstream spec's sample start.

### 5.3 Specification Gaps

**NIT-1: The AR(1) re-estimation frequency is not stated.**

The schema says "expanding window" but does not explicitly state whether the AR(1) is re-estimated monthly (every new observation) or at some other frequency. Monthly re-estimation is the natural choice for monthly data and should be stated explicitly.

**NIT-2: The MoM % change computation is ambiguous for CPIAUCSL.**

CPIAUCSL is a seasonally adjusted index. MoM % change = (CPI_t / CPI_{t-1} - 1) * 100. The schema does not state whether the AR(1) operates on the raw % change or on the annualized rate. Standard practice in the event-study literature (Andersen et al. 2003) uses the raw MoM change. This should be documented.

**FLAG-6: No mention of seasonal AR(1) or AR(12) as alternative.**

Colombian CPI has strong seasonal patterns (especially food prices in January). A simple AR(1) may not capture seasonal autocorrelation, leading to systematic under/over-prediction in certain months. The upstream spec (section 4.1 fallback paragraph) cites Andersen et al. 2003 as justification for AR(1), but that paper uses US data where CPIAUCSL is seasonally adjusted. DANE IPC may or may not be seasonally adjusted -- the schema downloads `ipc_pct_change` "as published" (section 3.4), which for DANE is typically NOT seasonally adjusted.

If the DANE IPC MoM changes have seasonal patterns, the AR(1) residuals will contain seasonal signal, and the "surprise" will partly reflect predictable seasonality rather than genuine news. This would attenuate beta (the surprise is noisier than the true information shock).

**Severity: FLAG.** The estimation module should test AR(1) vs AR(12) or seasonal AR(1) on the DANE IPC series and report which produces residuals with no seasonal autocorrelation. The pipeline need not change (it stores raw data), but the estimation spec should address this.

**Verdict: PASS WITH FLAGS** (FLAG-6 on seasonality, NIT-1 and NIT-2 on documentation).

---

## 6. Release-Week Mapping and T2/Decomposition Support

### 6.1 Separate CPI/PPI Flags

Rev 2 replaced the single `is_release_week` with `is_cpi_release_week` and `is_ppi_release_week`. This directly supports:

- **T2 (Levene test):** Can now test Var(RV | CPI release) > Var(RV | non-release) separately from Var(RV | PPI release) > Var(RV | non-release). Can also test the composite: Var(RV | any release) > Var(RV | no release).

- **Co-primary decomposition:** The decomposition equation includes both s_CPI and delta_IPP. With separate flags, the estimation module can correctly identify which weeks have CPI news, which have PPI news, and which have both (DANE often releases CPI and PPI on the same day or same week per the upstream spec section 4.4: "DANE releases CPI and PPI on the same day").

### 6.2 Same-Day CPI+PPI Release

**FLAG-7: The schema does not explicitly document what happens when CPI and PPI release on the same day/week.**

If both CPI and PPI are released in the same week, both `is_cpi_release_week` and `is_ppi_release_week` are TRUE, `cpi_surprise_ar1` is nonzero, and `dane_ipp_pct` is nonzero. This is the correct behavior for the decomposition equation (both regressors are active). The Levene test T2 should account for this overlap -- weeks with both releases should be classified as "both" rather than double-counted in separate CPI-only and PPI-only bins.

This is an estimation-module concern, not a pipeline concern. The data schema provides the correct building blocks.

### 6.3 Daily Panel Release-Day Flags

The daily_panel has `is_cpi_release_day` and `is_ppi_release_day`, mirroring the weekly flags. This supports release-day-level analysis (e.g., A4 release-day exclusion from RV).

**Verdict: PASS.** The split flags fully support T2 and the decomposition.

---

## 7. VIX Endogeneity

### 7.1 The Concern

VIX is a measure of implied volatility on US equity options. The upstream spec treats VIX as exogenous to Colombian FX (section 2.5: "Determined by US equity options; exogenous to Colombian FX specifically"). The concern is that VIX and COP/USD realized vol may be jointly determined by a common global risk factor, making VIX an endogenous control.

### 7.2 How `vix_friday_close` Helps

The schema adds `vix_friday_close` alongside `vix_avg`:
- `vix_avg`: weekly average of daily VIXCLS closes -- contemporaneous with the weekly RV measurement window
- `vix_friday_close`: point-in-time value at week end -- contemporaneous but single-point

Having both allows the estimation module to:
1. Use `vix_avg` as the baseline control (current primary)
2. Use `vix_friday_close` as a robustness check (less averaging, more point-in-time)
3. Use lagged VIX (prior week's `vix_avg` or `vix_friday_close`) to break simultaneity

**FLAG-8: The schema provides the data but does not address the endogeneity concern structurally.**

Adding `vix_friday_close` alongside `vix_avg` is a robustness dimension, not an endogeneity solution. The genuine endogeneity concern is: if a global risk-off event simultaneously raises VIX and COP/USD vol, then including contemporaneous VIX as a control ABSORBS some of the CPI-surprise effect that operates through the global risk channel (if CPI surprise triggers risk-off which raises both VIX and COP/USD vol, VIX absorbs that pathway, attenuating beta).

The proper treatment is:
- **Sensitivity A6 (bivariate, no controls):** Already specified in the upstream spec. Comparing beta with and without VIX reveals how much VIX absorbs.
- **Lagged VIX:** Using prior-week VIX as a predetermined control breaks contemporaneous endogeneity. The data supports this (lag is computable from the panel) but neither the data schema nor the upstream spec explicitly calls for lagged VIX as a sensitivity.

**Severity: FLAG.** The data schema correctly provides both VIX measures. The endogeneity concern is an estimation-module issue. Recommend adding "lagged VIX" as an explicit sensitivity (can be added to the estimation spec without changing the data pipeline).

**Verdict: PASS WITH FLAG** (FLAG-8: data is sufficient, but the endogeneity treatment is an estimation-spec concern).

---

## 8. Standardization Boundary

### 8.1 Pipeline vs Estimation Division

Section 4.3 states: "The pipeline provides raw inputs. Standardization (mean-subtraction + sigma-division) is performed by the estimation module."

This is the correct boundary for the following reasons:

1. **Sub-sample sensitivity (A3):** If the pipeline pre-standardized dane_ipp_pct, the mean and sigma would be computed over the full sample. But A3 requires sub-sample splits (2003-14, 2015-20, 2021-25), and standardization parameters should be computed within each sub-sample. Pipeline pre-standardization would be incorrect for A3.

2. **Expanding-window consistency:** The AR(1) surprise construction already uses expanding windows. If standardization were also applied in the pipeline, it would need to be expanding-window too (to avoid look-ahead). Delegating to estimation keeps the pipeline simple and the estimation module responsible for all statistical transforms.

3. **Reproducibility:** Raw data in the pipeline means the estimation module can always recompute transforms. Pre-transformed data loses information (the raw values).

### 8.2 Which Columns Are Raw vs Pre-Computed

| Column | Raw or derived? | Correct? |
|---|---|---|
| rv, rv_cuberoot, rv_log | Derived from TRM daily | These are AGGREGATIONS, not statistical transforms. The pipeline correctly computes them because they are deterministic functions of the raw daily data, not sample-dependent. |
| cpi_surprise_ar1 | Derived via expanding-window AR(1) | This is a borderline case -- the AR(1) is sample-dependent (expanding window). However, the surprise construction is a DATA PREPARATION step (constructing the RHS variable), not a statistical transform applied during estimation. Placing it in the pipeline is defensible and matches the upstream spec's treatment of the surprise as a "given" input to the regression. |
| dane_ipp_pct | Raw (as published by DANE) | Correct. Standardization applied at estimation time. |
| oil_return | Derived (log-return) | Deterministic, not sample-dependent. Correct in pipeline. |
| oil_log_level | Derived (log of price) | Deterministic. Correct in pipeline. |

**NIT-3: The cpi_surprise_ar1 column blurs the standardization boundary slightly.**

The AR(1) residual construction involves estimating AR(1) coefficients on an expanding window, which is sample-dependent. Strictly, this should be in the estimation module. However, the practical argument for including it in the pipeline is strong: the surprise is a well-defined, pre-committed construction that does not change with the regression specification. The estimation module would need the AR(1) surprise for every specification (primary, decomposition, GARCH-X, all sensitivities). Computing it once in the pipeline avoids redundant computation.

**Severity: NIT.** Acceptable as-is. The boundary documentation in section 4.3 should explicitly note that `cpi_surprise_ar1` is an exception: a sample-dependent derived variable that the pipeline computes because its construction is specification-invariant.

**Verdict: PASS.** The boundary is correctly drawn.

---

## Summary of Findings

| # | Finding | Severity | Domain | Recommendation |
|---|---|---|---|---|
| FLAG-3 | Surprise placement on exact release date vs next business day for daily GARCH-X | FLAG | daily_panel | Document convention; estimation module should test both placements (day t, day t+1) as robustness |
| FLAG-4 | 0.0 convention creates mixture distribution affecting JB test and GARCH-X SE | FLAG | NULL semantics | Document mixture structure; run T5 on full sample AND release-week subsample |
| FLAG-5 | Upstream spec still references DEXCOUS in section 4.3 table | FLAG | Documentation | Execute upstream amendment per section 8 of data schema |
| FLAG-6 | AR(1) may not capture seasonal patterns in non-seasonally-adjusted DANE IPC | FLAG | AR(1) surprise | Estimation module should test AR(1) vs AR(12) or seasonal AR for DANE IPC |
| FLAG-7 | Same-day CPI+PPI release handling not explicitly documented | FLAG | Release mapping | Add a note on overlap treatment for Levene test bins |
| FLAG-8 | VIX endogeneity not structurally addressed; lagged VIX not specified as sensitivity | FLAG | VIX | Add lagged VIX as explicit sensitivity in estimation spec |
| NIT-1 | AR(1) re-estimation frequency not stated (monthly assumed) | NIT | AR(1) surprise | State "re-estimated monthly (each new observation)" explicitly |
| NIT-2 | MoM % change computation not documented (raw vs annualized) | NIT | AR(1) surprise | State "raw MoM % change = (CPI_t / CPI_{t-1} - 1) * 100" |
| NIT-3 | cpi_surprise_ar1 blurs pipeline/estimation boundary | NIT | Standardization | Add explicit note in section 4.3 that AR(1) surprise is a specification-invariant exception |

**No BLOCKs identified.** All six original BLOCKs from Rev 1 have been adequately addressed. The remaining issues are estimation-module concerns that do not require data schema changes -- the pipeline provides sufficient raw data to implement any of the recommended robustness checks.

---

## Overall Verdict: PASS WITH FLAGS

The Rev 2 data schema is fit for purpose. It captures every variable needed for the primary OLS, GARCH-X co-primary, co-primary decomposition, all nine sensitivity specifications, and all seven specification tests. The daily_panel correctly serves the GARCH-X variance equation. The NULL-vs-0 semantics are econometrically correct. The TRM-based RV computation is an improvement over the nonexistent DEXCOUS. The AR(1) surprise construction is correctly specified with appropriate warmup periods. The standardization boundary is correctly drawn.

Six FLAGS remain, all resolvable at the estimation-spec stage without changing the data pipeline. Three NITs are documentation improvements.

The pipeline can proceed to implementation.
