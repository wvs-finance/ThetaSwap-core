# Model QA Review: Data Schema & Acquisition Strategy

**Reviewed spec:** `2026-04-16-data-schema-acquisition.md`
**Upstream spec:** `2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)
**Reviewer:** Model QA Specialist
**Date:** 2026-04-16

---

## 1. Variable Completeness

Systematic cross-check of every variable required by the upstream spec against the data schema.

### 1.1 Primary estimation equation (upstream SS 4.1)

| Variable | Upstream symbol | Schema coverage | Status |
|---|---|---|---|
| Weekly RV (+ cube-root, log, raw transforms) | RV_t, RV^{1/3}, log(RV) | `weekly_panel.rv`, `rv_cuberoot`, `rv_log` | OK |
| Colombian CPI surprise (survey) | s_t^CPI | Deferred column `cpi_surprise_survey` | OK (correctly deferred) |
| Colombian CPI surprise (AR(1) fallback) | hat{s}_t^CPI | Constructable from `dane_ipc_monthly.ipc_pct_change` | OK (raw material present) |
| US CPI surprise (AR(1)) | s_t^{US CPI} | `weekly_panel.us_cpi_surprise` | OK |
| BanRep rate surprise | s_t^BanRep | Deferred column `banrep_rate_surprise` | OK (correctly deferred) |
| VIX | VIX_t | `weekly_panel.vix_avg` | OK |
| Intervention dummy | I_t | Deferred column `intervention_dummy` | OK (correctly deferred) |
| Oil return | r_t^oil | `weekly_panel.oil_return` | OK |

### 1.2 Co-primary decomposition (upstream SS 4.1)

| Variable | Upstream symbol | Schema coverage | Status |
|---|---|---|---|
| PPI change (standardized) | Delta IPP_t | `weekly_panel.dane_ipp_pct` | PARTIAL |

**Finding D-1 (FLAG):** The upstream spec requires STANDARDIZED PPI change: (Delta IPP - mean) / sigma. The schema stores only `dane_ipp_pct` (raw MoM % change). The standardization can be computed at estimation time, but the schema description does not mention this transformation or store the mean/sigma reference values. This is acceptable if the estimation spec handles it, but the schema should at minimum document that `dane_ipp_pct` is the RAW input for the standardized variable. No data loss, but a documentation gap that could lead to implementation error (using raw PPI change instead of standardized).

### 1.3 GARCH(1,1)-X co-primary (upstream SS 4.1, A7)

| Variable | Upstream symbol | Schema coverage | Status |
|---|---|---|---|
| Daily COP/USD returns r_t | r_t | `fred_daily` WHERE series_id='DEXCOUS' | SEE FINDING D-2 |
| Absolute CPI surprise | abs(s_t^CPI) | Constructable from surprise columns | OK |

**Finding D-2 (BLOCK):** The GARCH(1,1)-X model operates on DAILY COP/USD returns with daily conditional variance h_t. The upstream spec explicitly defines: h_t = omega + alpha_1 * epsilon_{t-1}^2 + beta_1 * h_{t-1} + delta * |s_t^CPI|. This is a daily model. The `weekly_panel` does not support this. The raw table `fred_daily` preserves daily DEXCOUS observations, which is correct. However, the schema has no mention of a daily panel or daily-frequency derived table for GARCH-X estimation. The GARCH-X needs:

- Daily COP/USD log-returns (computable from `fred_daily`)
- Daily CPI surprise indicator (which day within the release week carries the surprise? The GARCH-X requires the surprise to be placed on the EXACT release date, not spread across the week)
- Daily VIX (available from `fred_daily`)
- Daily oil return or level (available from `fred_daily`)
- Daily intervention indicator (would need daily granularity from SUAMECA)

The schema stores the raw daily data but does not define how to construct the daily estimation panel for GARCH-X. The `dane_release_calendar` has the release_date, which can map the surprise to the exact day. But the gap is: the schema spec only defines ONE derived table (`weekly_panel`) and does not acknowledge that the GARCH-X co-primary requires a DIFFERENT derived table at daily frequency with different variable mappings.

### 1.4 Sensitivity specifications A1-A9

| Sensitivity | Data requirement | Schema support | Status |
|---|---|---|---|
| A1: Monthly horizon | Monthly RV = sum of squared daily returns in calendar month | Computable from `fred_daily` | OK (no monthly panel defined, but raw data sufficient) |
| A2: CPI vs PPI decomposition | Separate CPI and PPI surprises | `dane_ipc_pct` + `dane_ipp_pct` in `weekly_panel` | OK |
| A3: Sub-sample splits | Date-based filtering | `week_start` column | OK |
| A4: Release-day exclusion | Must exclude release-day returns from RV | Requires `dane_release_calendar.release_date` + daily returns | PARTIAL (see D-3) |
| A5: Lagged RV control | lag(RV) or lag(log(RV)) | Computable from `weekly_panel` | OK |
| A6: Bivariate | Subset of primary | OK | OK |
| A7: GARCH-X | See D-2 above | See D-2 | BLOCK |
| A8: Oil level control | log(WTI Friday close) | `weekly_panel.oil_log_level` | OK |
| A9: Asymmetric effects | s_t^+ = max(s,0), s_t^- = min(s,0) | Computable from surprise columns | OK |

**Finding D-3 (FLAG):** Sensitivity A4 (release-day exclusion) requires recomputing RV EXCLUDING the return on the DANE release date. This means the pipeline must be able to recompute RV with a specific day removed. The current schema computes RV once and stores it. The raw `fred_daily` data supports recomputation, but the schema does not define a mechanism for this (e.g., a parameterized RV computation function, or a separate column `rv_excl_release_day`). This is an estimation-time concern, not a data-loss concern, but the schema should acknowledge it.

### 1.5 Specification tests T1-T7

| Test | Data requirement | Schema support | Status |
|---|---|---|---|
| T1: Consensus rationality (F-test on lags) | lag(s_t), lag(RV_t), lag(VIX_t) | All computable from `weekly_panel` | OK |
| T2: Release-week variance comparison | `is_release_week` + RV | `weekly_panel.is_release_week`, `weekly_panel.rv` | OK |
| T3a/T3b: Beta tests | Standard estimation output | OK | OK |
| T4: Ljung-Box on residuals | Residuals from estimation | OK (estimation-time) | OK |
| T5: Jarque-Bera | Residuals from estimation | OK (estimation-time) | OK |
| T6: Structural break (Chow / Bai-Perron) | Sub-sample splits by date | `week_start` supports filtering | OK |
| T7: Intervention adequacy | Estimation with/without I_t | Requires `intervention_dummy` column | OK (deferred correctly) |

---

## 2. RV Computation Correctness

### 2.1 Definition match

The schema defines: RV = sum of r_d^2 where r_d = log(P_d / P_{d-1}) for daily observations within Monday-Friday.

The upstream spec (SS 4.3) defines: RV_t = sum_{d in week} r_d^2.

These match.

### 2.2 FRED DEXCOUS vs SET FX

**Finding D-4 (FLAG):** The upstream spec explicitly warns in SS 3.3 that "FRED noon rate vs SET FX close" introduces measurement error in the LHS, with bias direction: attenuation. The schema uses DEXCOUS (Federal Reserve noon buying rate) as the sole FX data source. This is the correct choice given the free-tier constraint, and the upstream spec has already classified and accepted this measurement error. However, the schema should explicitly acknowledge this known measurement error source and reference SS 3.3 so that downstream implementers do not treat the RV as if it were computed from SET FX close rates.

Specific concern: DEXCOUS is the Federal Reserve noon buying rate, reported once per day. SET FX is Colombia's official benchmark, computed from actual interbank transactions. The noon-rate timing means that intraday COP/USD movements AFTER the noon fix (e.g., from a DANE release published at 11pm Bogota time, or a BanRep decision in the afternoon) may appear in the NEXT day's return rather than the same day's. For DANE releases typically published between 6-8pm COT, the price reaction would be fully captured in the NEXT business day's DEXCOUS return, meaning the weekly RV should still capture the effect within the same week. But for Friday afternoon releases, some of the reaction might spill into Monday's return (next week). This is a known limitation, not a design error.

### 2.3 Short-week scaling

**Finding D-5 (NIT):** The schema states "no scaling for weeks with fewer than 5 trading days -- this is standard per Andersen et al. 2003." This is defensible but deserves nuance. Andersen et al. 2003 work with 5-minute returns where n is large; at n=5 daily returns, a week with n=3 (e.g., US+Colombian holiday overlap) will have mechanically lower RV simply from fewer squared terms. The `n_trading_days` column is correctly included, which allows the estimation code to either: (a) scale by 5/n, (b) include n_trading_days as a control, or (c) filter out short weeks as a robustness check. The raw information is preserved. No data loss.

The choice NOT to scale in the derived table is actually preferable because scaling imposes an assumption (iid returns within the week) that may not hold. Better to leave this to the estimation code.

---

## 3. AR(1) Surprise Construction

### 3.1 US CPI surprise

The schema defines: AR(1) on monthly CPIAUCSL MoM % changes. Surprise = actual - AR(1) forecast. Mapped to the week containing the BLS release date.

**Finding D-6 (FLAG):** The schema mentions mapping to "the week containing the BLS release date" but does NOT define a table or column for the BLS release calendar. The `dane_release_calendar` only covers DANE CPI and PPI releases. To correctly map US CPI surprises to weeks, the pipeline needs to know WHEN each CPIAUCSL observation was released by the BLS. Options:

1. Hardcode: BLS publishes CPI on a fixed schedule (typically 2nd or 3rd week of the month, for the prior month's data). The FRED API provides `realtime_start` and `realtime_end` metadata that can identify the release date for each observation.
2. Use FRED's release dates API: `GET /fred/release/dates?release_id=10` (release 10 = CPI) provides the exact release dates.
3. Manual compilation analogous to `dane_release_calendar`.

The schema does not specify which approach will be used, nor does it define storage for BLS release dates. Without this, the `us_cpi_surprise` column in `weekly_panel` cannot be correctly mapped to its release week.

### 3.2 Colombian CPI surprise (AR(1) fallback)

The schema stores `dane_ipc_monthly.ipc_pct_change` (MoM % change) and `dane_release_calendar` (release dates). This is sufficient to construct an AR(1) surprise: fit AR(1) on ipc_pct_change, compute residual, map to release week via dane_release_calendar.

**Finding D-7 (NIT):** The schema does not explicitly define the AR(1) Colombian CPI surprise as a column in `weekly_panel`. The `dane_ipc_pct` column stores the RAW MoM change, not the surprise. If the BanRep EME survey data is unavailable (triggering the AR(1) fallback), the pipeline will need to compute a Colombian CPI AR(1) surprise and store it somewhere. The schema implicitly assumes this will be handled at estimation time, which is acceptable, but the `weekly_panel` table definition should note that for the AR(1) fallback case, a `cpi_surprise_ar1` column would need to be added (alongside the already-planned `cpi_surprise_survey` deferred column).

---

## 4. Weekly Aggregation Choices

### 4.1 VIX: weekly average vs Friday close

**Finding D-8 (FLAG):** The schema uses weekly average VIX (`vix_avg`). The upstream spec (SS 4.3) lists VIX_t as a control but does not specify the aggregation method. The choice matters:

- **Weekly average**: Smoother, captures the average risk environment during the week. Appropriate if the model interprets VIX as "ambient risk appetite during the week."
- **Friday close**: Contemporaneous with the oil_return measurement (Friday-to-Friday). Appropriate if the model interprets VIX as "risk conditions at the point of weekly observation."
- **Monday open or release-day value**: Would better capture the pre-release risk environment.

The Andersen et al. 2003 event-study framework typically uses the announcement-day value of controls, not weekly averages. At the weekly aggregation level of this spec, this distinction matters less, but there is a subtle timing issue: if VIX spikes BECAUSE of a DANE release (reverse causality through global EM risk channels), the weekly average VIX would be endogenous to the CPI surprise. A Friday-close VIX (or better, a Monday-open VIX) would reduce this concern.

Recommendation: Store BOTH `vix_avg` (current) and `vix_friday_close` (add) in the weekly panel. Let the estimation code choose. The raw data in `fred_daily` supports this at zero additional acquisition cost.

### 4.2 Oil return: Friday-to-Friday log-return

This is standard for weekly commodity return computation. No issues.

### 4.3 Oil level: Friday close

`oil_log_level` defined as log(WTI Friday close). Correct for sensitivity A8.

---

## 5. GARCH-X Data Needs

**Finding D-2 (restated, BLOCK):** This is the most material gap in the schema. The GARCH(1,1)-X is a co-primary estimator (promoted from sensitivity in Rev 3, with explicit reconciliation protocol in Rev 4). It operates on DAILY returns, not weekly aggregates. The schema must either:

(a) Define a `daily_panel` derived table with: daily COP/USD log-return, daily VIX, daily oil return, and a release-day indicator (binary: 1 if DANE CPI or PPI was released on this date, mapped from `dane_release_calendar.release_date`). The CPI surprise magnitude would be placed on the release date only (zero on all other days, or use the `|s_t^CPI|` value on the release day and 0 otherwise).

(b) Explicitly state that the GARCH-X estimation code will construct its own daily panel from the raw tables, bypassing `weekly_panel`. This is acceptable but should be documented in the schema spec so the estimation spec knows which raw tables to use and how.

Currently the schema is silent on this. The raw data exists (`fred_daily` has daily DEXCOUS, VIXCLS, DCOILWTICO), and `dane_release_calendar` has release dates, so there is no data LOSS. But the schema's scope claim -- "weekly_panel: the estimation-ready dataset" -- is incorrect for the GARCH-X co-primary. The GARCH-X needs a DIFFERENT estimation-ready dataset.

**Sub-finding D-2a (FLAG):** The GARCH-X may need daily intervention data (not just weekly). If BanRep intervenes on specific days, the GARCH-X conditional variance equation should control for intervention-day effects. The current schema defers the intervention dummy to the weekly panel only. If SUAMECA data includes intervention dates (not just weeks), the daily panel should include a daily intervention indicator.

---

## 6. Release-Week Mapping

### 6.1 Implementation correctness

The schema maps `dane_release_calendar.release_date` to `weekly_panel.week_start` (Monday of the week). The `is_release_week` flag is TRUE if any DANE CPI or PPI release falls within that Monday-Friday window.

This is correct and straightforward.

### 6.2 Edge cases

**Finding D-9 (NIT):** Friday release edge case. If DANE releases CPI on a Friday, the FX market reaction (particularly via DEXCOUS noon rate) may not appear until the following Monday. The schema correctly assigns the release to the Friday's week (the release HAPPENED that week), but the VOL RESPONSE may partially fall in the next week. This is acknowledged in the upstream spec as a timing issue (SS 3.3: "Delayed portfolio rebalancing... attenuation"). The schema's treatment is correct -- the release date determines the week, not the market reaction date. The upstream spec's HAC standard errors (lag=4) will account for any spillover.

**Finding D-10 (FLAG):** The schema defines `is_release_week` as TRUE if CPI OR PPI was released that week. The upstream spec treats CPI and PPI releases as distinct events (the co-primary decomposition estimates separate beta_1 and beta_2). The schema does store `dane_ipc_pct` and `dane_ipp_pct` separately (NULL when no release), which allows the estimation code to distinguish CPI-only weeks from PPI-only weeks from joint-release weeks. However, the `is_release_week` flag conflates the two. The upstream spec's T2 test (Levene test: release vs non-release variance) should ideally distinguish: CPI-release weeks, PPI-release weeks, both-release weeks, and neither-release weeks, because the identification argument rests on CPI surprise specifically (not PPI).

Recommendation: Add `is_cpi_release_week` and `is_ppi_release_week` as separate boolean columns. Keep `is_release_week` as the OR for convenience. The `dane_release_calendar` already has the `series` column to support this.

---

## 7. Specification Test Data Needs

| Test | Requirement | Schema support | Verdict |
|---|---|---|---|
| T1: lag(s_t), lag(RV_t), lag(VIX_t) | Lagged weekly values | All in `weekly_panel`, laggable by `week_start` ordering | OK |
| T2: Release vs non-release variance | `is_release_week` + RV | Present | OK (see D-10 for refinement) |
| T3a/T3b | Estimation output | N/A for schema | OK |
| T4: Ljung-Box | Residuals | N/A for schema | OK |
| T5: Jarque-Bera | Residuals | N/A for schema | OK |
| T6: Sub-sample splits | Date filtering | `week_start` | OK |
| T7: With/without I_t | Requires intervention data | Deferred correctly | OK |

All specification tests are supported by the schema.

---

## 8. Sensitivity Spec Data Needs

| Sensitivity | Requirement | Schema support | Verdict |
|---|---|---|---|
| A1: Monthly horizon | Monthly RV from daily returns | `fred_daily` has daily DEXCOUS; no monthly panel defined | OK (computable, see D-11) |
| A2: CPI vs PPI decomposition | Separate CPI/PPI in weekly panel | `dane_ipc_pct`, `dane_ipp_pct` | OK |
| A3: Sub-sample splits | Date filtering | `week_start` | OK |
| A4: Release-day exclusion | Recompute RV excluding release-day return | Requires daily returns + release dates; both available in raw tables | OK (see D-3) |
| A5: Lagged RV | lag(RV) | Computable from `weekly_panel` | OK |
| A6: Bivariate | Subset | OK | OK |
| A7: GARCH-X | Daily panel | See D-2 (BLOCK) | BLOCK |
| A8: Oil level | log(WTI Friday close) | `weekly_panel.oil_log_level` | OK |
| A9: Asymmetric | max(s,0), min(s,0) splits | Computable from surprise columns | OK |

**Finding D-11 (NIT):** Sensitivity A1 (monthly horizon) requires monthly RV = sum of squared daily log-returns within a calendar month, plus monthly values of all controls. The schema does not define a monthly panel. This is acceptable because: (a) monthly RV is computable from `fred_daily`, (b) monthly VIX/oil are computable from `fred_daily`, (c) monthly CPI surprise is directly available from `dane_ipc_monthly`/`fred_monthly`. The estimation spec should handle this. But the schema could note that A1 requires a separate monthly aggregation.

---

## 9. Additional Issues

**Finding D-12 (NIT):** The schema downloads both `DCOILWTICO` (WTI) and `DCOILBRENTEU` (Brent) into `fred_daily`, but the `weekly_panel` only uses WTI for `oil_return` and `oil_log_level`. The upstream spec (SS 4.3) lists "DCOILWTICO (WTI) or DCOILBRENTEU (Brent)" as alternatives. Brent may be more relevant for Colombia (Brent is the international benchmark; Colombian crude tracks Brent more closely than WTI). The schema should either: (a) define which oil series the weekly panel uses and why, or (b) include both WTI and Brent return/level columns so the estimation code can test sensitivity to the choice. The raw data for both is being downloaded, so this is a zero-cost addition to the weekly panel.

**Finding D-13 (NIT):** The schema does not define how to handle FRED holidays/missing values in the RV computation. DEXCOUS has NULLs for US holidays and weekends. Colombian holidays where the US market is open (and vice versa) create mismatches. For example, if Monday is a Colombian holiday but not a US holiday, DEXCOUS may report a rate but SET FX did not trade. The noon rate would still be quoted (DEXCOUS is a Fed rate, not a SET FX rate), so this may not be a problem for DEXCOUS specifically. But the schema should document the holiday-handling rule: are NULLs in DEXCOUS simply skipped in the log-return chain (so P_{d-1} is the last non-NULL date), or are they filled forward?

**Finding D-14 (FLAG):** The `weekly_panel` defines `us_cpi_surprise` as "NULL if no US CPI release this week." The upstream spec's primary equation includes s_t^{US CPI} as a control on ALL weeks (it appears outside any indicator function). If `us_cpi_surprise` is NULL for ~48 of 52 weeks per year, the OLS estimation cannot use it as a continuous control -- it would need to be zero-filled on non-release weeks (surprise = 0 when no release occurs, which is the correct econometric interpretation: no news = no surprise). The schema should clarify: is the NULL intended to be treated as zero at estimation time? If so, the column should store 0.0, not NULL, on non-release weeks. NULL has a different semantic meaning (missing/unknown) than 0 (no surprise occurred).

The same concern applies to `dane_ipc_pct` and `dane_ipp_pct` on non-release weeks.

---

## Findings Summary

| # | Finding | Severity | Domain | Description |
|---|---|---|---|---|
| D-1 | PPI standardization undocumented | FLAG | Variable completeness | Schema stores raw PPI change, not standardized; gap between schema and upstream co-primary decomposition |
| D-2 | No daily panel for GARCH-X | BLOCK | GARCH-X data needs | Co-primary estimator requires daily-frequency derived table; schema only defines weekly_panel |
| D-2a | Daily intervention for GARCH-X | FLAG | GARCH-X data needs | GARCH-X may need daily intervention indicator, not just weekly |
| D-3 | Release-day RV exclusion not defined | FLAG | Sensitivity A4 | Schema does not define mechanism for recomputing RV with release-day excluded |
| D-4 | DEXCOUS measurement error undocumented | FLAG | RV computation | Known measurement error (upstream SS 3.3) not referenced in schema for implementer awareness |
| D-5 | Short-week scaling choice | NIT | RV computation | No scaling is defensible; n_trading_days column preserves flexibility |
| D-6 | BLS release calendar missing | FLAG | AR(1) surprise | No table or mechanism to map US CPI releases to weeks |
| D-7 | Colombian AR(1) surprise column missing | NIT | AR(1) surprise | No explicit weekly_panel column for Colombian CPI AR(1) fallback surprise |
| D-8 | VIX aggregation choice | FLAG | Aggregation | Weekly average VIX may be endogenous; Friday close or Monday open alternative not stored |
| D-9 | Friday release spillover | NIT | Release mapping | Acknowledged timing issue, correctly handled |
| D-10 | Release-week flag conflates CPI and PPI | FLAG | Release mapping | Single is_release_week flag; should split into is_cpi_release_week and is_ppi_release_week |
| D-11 | Monthly panel for A1 not defined | NIT | Sensitivity A1 | Computable from raw data but not documented |
| D-12 | Oil series choice undocumented | NIT | Variable definition | Both WTI and Brent downloaded but only WTI used in weekly_panel |
| D-13 | Holiday handling undocumented | NIT | RV computation | No rule for DEXCOUS NULL handling in log-return chain |
| D-14 | NULL vs zero on non-release weeks | FLAG | Variable definition | us_cpi_surprise, dane_ipc_pct, dane_ipp_pct are NULL on non-release weeks; OLS requires 0, not NULL |

---

## Verdict: PASS WITH FLAGS

**1 BLOCK, 8 FLAGs, 6 NITs.**

The schema correctly acquires and stores ALL raw data needed for the full estimation. The priority ordering (risk-first) is sound. The weekly panel design is well-structured for the OLS primary. The critical gap is the absence of a daily-frequency derived table (or explicit documentation path) for the GARCH(1,1)-X co-primary, which was promoted to co-primary status in Rev 3 and given an explicit reconciliation protocol in Rev 4. This is not a data-loss issue (the raw daily data is preserved in `fred_daily`), but it is a schema-completeness issue: the spec claims `weekly_panel` is "the estimation-ready dataset" when in fact TWO estimation-ready datasets are needed.

**Remediation priority:**

1. **(BLOCK) D-2:** Add a `daily_panel` derived table definition, or explicitly document that GARCH-X estimation constructs its own panel from raw tables. Define the daily variable mappings (return, surprise placement on release date, daily VIX, daily oil, daily intervention).

2. **(FLAGs, should fix before implementation):**
   - D-6: Define BLS release date acquisition (FRED release dates API or manual).
   - D-14: Change NULL semantics to 0 for surprise/release variables on non-release weeks, or document the NULL-to-zero imputation rule for estimation.
   - D-8: Add `vix_friday_close` column alongside `vix_avg`.
   - D-10: Add `is_cpi_release_week` and `is_ppi_release_week` columns.
   - D-1, D-3, D-4, D-2a: Documentation additions.

3. **(NITs, improve when convenient):** D-5, D-7, D-9, D-11, D-12, D-13.

The schema is well-designed within its stated scope. The BLOCK is a scope gap (daily panel), not an error in what is defined. Once D-2 is addressed, the schema faithfully serves the upstream spec.
