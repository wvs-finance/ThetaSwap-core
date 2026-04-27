# Estimates — Task 11.O Rev-2 Phase 5b (14-Row Resolution Matrix)

**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`  
**Phase 5a artifacts:** `contracts/.scratch/2026-04-25-task110-rev2-data/`  
**Output:** `contracts/.scratch/2026-04-25-task110-rev2-analysis/`  

---

## 1. Resolution-matrix coefficient table (β̂_X_d)

| Row | Label | Estimator | n | β̂ | SE | t-stat | p (two) | p (one) | lower-90 | Gate |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Primary (gate-bearing) | ols_hac4 | 76 | -2.799e-08 | 1.423e-08 | -1.966 | 0.0493 | 0.9754 | -4.621e-08 | **FAIL** |
| 2 | Bootstrap reconciliation (Politis-Romano stationary block) | bootstrap_pr_4_10000 | 76 | -2.799e-08 | 2.222e-08 | -1.260 | 0.1198 | 0.9401 | -5.643e-08 | **FAIL** |
| 3 | LOCF-tail-excluded sensitivity (PRE-REGISTERED FAIL) | ols_hac4 | 65 | -1.894e-08 | 1.602e-08 | -1.182 | 0.2371 | 0.8815 | -3.945e-08 | **FAIL** |
| 4 | IMF-IFS-only sensitivity (PRE-REGISTERED FAIL — dual axis) | ols_hac4 | 56 | -1.548e-08 | 1.497e-08 | -1.034 | 0.3011 | 0.8495 | -3.465e-08 | **FAIL** |
| 5 | Lag sensitivity (X_d_{t-1}) | ols_hac4 | 75 | 4.260e-09 | 1.704e-08 | 0.250 | 0.8026 | 0.4013 | -1.755e-08 | **FAIL** |
| 6 | Parsimonious controls (3-control: VIX + oil + intervention) | ols_hac4 | 76 | -7.317e-09 | 1.091e-08 | -0.671 | 0.5024 | 0.7488 | -2.128e-08 | **FAIL** |
| 7 | Arb-only diagnostic (BancorArbitrage trader) | ols_hac4 | 45 | -3.410e-08 | 9.282e-08 | -0.367 | 0.7134 | 0.6433 | -1.529e-07 | **FAIL** |
| 8 | Per-currency COPM diagnostic (Mento Colombian Peso leg) | ols_hac4 | 47 | -1.634e-07 | 1.287e-07 | -1.270 | 0.2041 | 0.8979 | -3.280e-07 | **FAIL** |
| 9 | Y₃-bond diagnostic | deferred | 0 | — | — | — | — | — | — | DEFERRED |
| 10 | Population-weighted Y₃ | deferred | 0 | — | — | — | — | — | — | DEFERRED |
| 11 | Student-t innovations refit | student_t_mle | 76 | -2.799e-08 | 1.904e-08 | -1.470 | 0.1825 | 0.9087 | -5.236e-08 | **FAIL** |
| 12 | HAC(12) bandwidth sensitivity | ols_hac12 | 76 | -2.799e-08 | 1.061e-08 | -2.638 | 0.0084 | 0.9958 | -4.157e-08 | **FAIL** |
| 13 | First-differenced (Δlog X_d, ΔY₃) | ols_hac4 | 75 | -0.002155 | 0.001887 | -1.142 | 0.2534 | 0.8733 | -0.004570 | **FAIL** |
| 14a | WC-CPI weights (50/30/20) | ols_hac4 | 76 | -2.919e-08 | 1.718e-08 | -1.699 | 0.0893 | 0.9553 | -5.119e-08 | **FAIL** |
| 14b | WC-CPI weights (60/25/15) [primary] | ols_hac4 | 76 | -2.978e-08 | 1.911e-08 | -1.559 | 0.1191 | 0.9404 | -5.425e-08 | **FAIL** |
| 14c | WC-CPI weights (70/20/10) | ols_hac4 | 76 | -3.038e-08 | 2.123e-08 | -1.430 | 0.1526 | 0.9237 | -5.756e-08 | **FAIL** |

---

## 2. Per-row interpretation

### Row 1 — Primary (gate-bearing)

- **Sample size:** n = 76 (pre-committed = 76, **MATCH**)
- **β̂ (X_d coefficient):** -2.799e-08
- **SE:** 1.423e-08 (ols_hac4)
- **t-statistic:** -1.966
- **Two-sided p-value (T3a):** 0.0493
- **One-sided p-value:** 0.9754
- **90% one-sided lower bound (β̂ − 1.28·SE):** -4.621e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** OLS + HAC(4) Newey-West, 6 controls, contemporaneous X_d, identity Y₃. The gate-bearing row.


### Row 2 — Bootstrap reconciliation (Politis-Romano stationary block)

- **Sample size:** n = 76 (pre-committed = 76, **MATCH**)
- **β̂ (X_d coefficient):** -2.799e-08
- **SE:** 2.222e-08 (bootstrap_pr_4_10000)
- **t-statistic:** -1.260
- **Two-sided p-value (T3a):** 0.1198
- **One-sided p-value:** 0.9401
- **90% one-sided lower bound (β̂ − 1.28·SE):** -5.643e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** Politis-Romano stationary block bootstrap, mean block length = 4, 10000 resamples. SE empirical, p-value = empirical right-tail-at-zero, CI = empirical 5/95 quantile.


### Row 3 — LOCF-tail-excluded sensitivity (PRE-REGISTERED FAIL)

- **Sample size:** n = 65 (pre-committed = 65, **MATCH**)
- **β̂ (X_d coefficient):** -1.894e-08
- **SE:** 1.602e-08 (ols_hac4)
- **t-statistic:** -1.182
- **Two-sided p-value (T3a):** 0.2371
- **One-sided p-value:** 0.8815
- **90% one-sided lower bound (β̂ − 1.28·SE):** -3.945e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** OLS + HAC(4); week_start ≤ 2025-12-31 cutoff. Pre-registered FAIL on N_MIN (n=65 < 75).


### Row 4 — IMF-IFS-only sensitivity (PRE-REGISTERED FAIL — dual axis)

- **Sample size:** n = 56 (pre-committed = 56, **MATCH**)
- **β̂ (X_d coefficient):** -1.548e-08
- **SE:** 1.497e-08 (ols_hac4)
- **t-statistic:** -1.034
- **Two-sided p-value (T3a):** 0.3011
- **One-sided p-value:** 0.8495
- **90% one-sided lower bound (β̂ − 1.28·SE):** -3.465e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** OLS + HAC(4); IMF-IFS-only Y₃ panel. Pre-registered FAIL: n=56 < 75 AND power=0.7301 < 0.80.


### Row 5 — Lag sensitivity (X_d_{t-1})

- **Sample size:** n = 75
- **β̂ (X_d coefficient):** 4.260e-09
- **SE:** 1.704e-08 (ols_hac4)
- **t-statistic:** 0.250
- **Two-sided p-value (T3a):** 0.8026
- **One-sided p-value:** 0.4013
- **90% one-sided lower bound (β̂ − 1.28·SE):** -1.755e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** OLS + HAC(4), one-period lag X_d_{t-1}. Drops first row → n = 75.


### Row 6 — Parsimonious controls (3-control: VIX + oil + intervention)

- **Sample size:** n = 76 (pre-committed = 76, **MATCH**)
- **β̂ (X_d coefficient):** -7.317e-09
- **SE:** 1.091e-08 (ols_hac4)
- **t-statistic:** -0.671
- **Two-sided p-value (T3a):** 0.5024
- **One-sided p-value:** 0.7488
- **90% one-sided lower bound (β̂ − 1.28·SE):** -2.128e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** Drops 3 of 6 controls (us_cpi_surprise, banrep_rate_surprise, fed_funds_weekly). Used in T7 parameter-stability check vs Row 1.


### Row 7 — Arb-only diagnostic (BancorArbitrage trader)

- **Sample size:** n = 45 (pre-committed = 45, **MATCH**)
- **β̂ (X_d coefficient):** -3.410e-08
- **SE:** 9.282e-08 (ols_hac4)
- **t-statistic:** -0.367
- **Two-sided p-value (T3a):** 0.7134
- **One-sided p-value:** 0.6433
- **90% one-sided lower bound (β̂ − 1.28·SE):** -1.529e-07
- **T3b gate verdict:** **FAIL**
- **Notes:** Diagnostic only (n=45 < N_MIN=75); arb-only X_d via `carbon_basket_arb_volume_usd`.


### Row 8 — Per-currency COPM diagnostic (Mento Colombian Peso leg)

- **Sample size:** n = 47 (pre-committed = 47, **MATCH**)
- **β̂ (X_d coefficient):** -1.634e-07
- **SE:** 1.287e-07 (ols_hac4)
- **t-statistic:** -1.270
- **Two-sided p-value (T3a):** 0.2041
- **One-sided p-value:** 0.8979
- **90% one-sided lower bound (β̂ − 1.28·SE):** -3.280e-07
- **T3b gate verdict:** **FAIL**
- **Notes:** Diagnostic only (n=47 < N_MIN=75); per-currency COPM X_d.


### Row 9 — Y₃-bond diagnostic

**Status:** DEFERRED. DEFERRED per spec §10 ε.2. Bond-data fetcher not yet ingested; 10Y sovereign-bond yield-change replacing R_equity is a future-revision item.

Per spec §10 ε.2/ε.3, this row is reserved for a future Phase-5a panel re-build.
It is held as a deferred placeholder in the deliverable contract and contributes
neither evidence for nor against the gate verdict.


### Row 10 — Population-weighted Y₃

**Status:** DEFERRED. DEFERRED per spec §10 ε.3. Aggregator weight-vector argument unbuilt; population-weighted Y₃ is a future-revision item.

Per spec §10 ε.2/ε.3, this row is reserved for a future Phase-5a panel re-build.
It is held as a deferred placeholder in the deliverable contract and contributes
neither evidence for nor against the gate verdict.


### Row 11 — Student-t innovations refit

- **Sample size:** n = 76 (pre-committed = 76, **MATCH**)
- **β̂ (X_d coefficient):** -2.799e-08
- **SE:** 1.904e-08 (student_t_mle)
- **t-statistic:** -1.470
- **Two-sided p-value (T3a):** 0.1825
- **One-sided p-value:** 0.9087
- **90% one-sided lower bound (β̂ − 1.28·SE):** -5.236e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** Student-t MLE refit on residuals (df_t estimated = 7.440). Heavy-tail robustness check.


### Row 12 — HAC(12) bandwidth sensitivity

- **Sample size:** n = 76 (pre-committed = 76, **MATCH**)
- **β̂ (X_d coefficient):** -2.799e-08
- **SE:** 1.061e-08 (ols_hac12)
- **t-statistic:** -2.638
- **Two-sided p-value (T3a):** 0.0084
- **One-sided p-value:** 0.9958
- **90% one-sided lower bound (β̂ − 1.28·SE):** -4.157e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** OLS + HAC(12) Newey-West (vs primary HAC(4)). Bandwidth-robustness diagnostic.


### Row 13 — First-differenced (Δlog X_d, ΔY₃)

- **Sample size:** n = 75
- **β̂ (X_d coefficient):** -0.002155
- **SE:** 0.001887 (ols_hac4)
- **t-statistic:** -1.142
- **Two-sided p-value (T3a):** 0.2534
- **One-sided p-value:** 0.8733
- **90% one-sided lower bound (β̂ − 1.28·SE):** -0.004570
- **T3b gate verdict:** **FAIL**
- **Notes:** Δlog(X_d) and ΔY₃ first-difference; drops first row → n = 75. Stationarity-robustness.


### Row 14a — WC-CPI weights (50/30/20)

- **Sample size:** n = 76 (pre-committed = 76, **MATCH**)
- **β̂ (X_d coefficient):** -2.919e-08
- **SE:** 1.718e-08 (ols_hac4)
- **t-statistic:** -1.699
- **Two-sided p-value (T3a):** 0.0893
- **One-sided p-value:** 0.9553
- **90% one-sided lower bound (β̂ − 1.28·SE):** -5.119e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** WC-CPI bundle weights = (0.5, 0.3, 0.2); per-country diff cross-weight approximation (see manifest §1.4 caveat — faithful per-bucket weight Y₃ re-aggregation requires Phase-5a panel re-build with sub-bucket component returns surfaced).


### Row 14b — WC-CPI weights (60/25/15) [primary]

- **Sample size:** n = 76 (pre-committed = 76, **MATCH**)
- **β̂ (X_d coefficient):** -2.978e-08
- **SE:** 1.911e-08 (ols_hac4)
- **t-statistic:** -1.559
- **Two-sided p-value (T3a):** 0.1191
- **One-sided p-value:** 0.9404
- **90% one-sided lower bound (β̂ − 1.28·SE):** -5.425e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** WC-CPI bundle weights = (0.6, 0.25, 0.15); per-country diff cross-weight approximation (see manifest §1.4 caveat — faithful per-bucket weight Y₃ re-aggregation requires Phase-5a panel re-build with sub-bucket component returns surfaced).


### Row 14c — WC-CPI weights (70/20/10)

- **Sample size:** n = 76 (pre-committed = 76, **MATCH**)
- **β̂ (X_d coefficient):** -3.038e-08
- **SE:** 2.123e-08 (ols_hac4)
- **t-statistic:** -1.430
- **Two-sided p-value (T3a):** 0.1526
- **One-sided p-value:** 0.9237
- **90% one-sided lower bound (β̂ − 1.28·SE):** -5.756e-08
- **T3b gate verdict:** **FAIL**
- **Notes:** WC-CPI bundle weights = (0.7, 0.2, 0.1); per-country diff cross-weight approximation (see manifest §1.4 caveat — faithful per-bucket weight Y₃ re-aggregation requires Phase-5a panel re-build with sub-bucket component returns surfaced).


