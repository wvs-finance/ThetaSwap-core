# Data Dictionary — Task 11.O Rev-2 Phase 5a Panel Variables

**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`
**Output dir:** `contracts/.scratch/2026-04-25-task110-rev2-data/`
**Date:** 2026-04-26

This file documents every column on every panel artifact. It is the single source of truth for variable provenance, units, cleaning rules, and admitted spec-literal values. The Analytics Reporter (Phase 5b) consumes these definitions to build the regression specification matrix in §4.1 of the spec.

---

## 1. Index columns

### 1.1 `week_start`

| | |
|---|---|
| **Type** | `DATE` |
| **Anchor** | Friday-anchored America/Bogota (ISO weekday 5) |
| **Source** | `onchain_xd_weekly.week_start` (Friday native; the panel join key) |
| **Range, primary panel** | [2024-09-27, 2026-03-13] |
| **Range, IMF-only sensitivity** | [2024-09-27, 2025-10-24] |
| **Cleaning** | `weekly_panel.week_start` is Monday-anchored (`isodow=1`); shifted to Friday via `+ INTERVAL 4 DAY` inside the JOIN CTE before key matching. Other tables (`onchain_xd_weekly`, `onchain_y3_weekly`, `weekly_rate_panel`) are Friday-native. |
| **Invariant test** | `test_build_panel_returns_friday_anchored_rows_only` — every output row's `isoweekday() == 5`. |

---

## 2. Outcome variable (LHS of spec equation §4.1)

### 2.1 `y3_value`

| | |
|---|---|
| **Type** | `DOUBLE` |
| **Spec § ref** | §1.3 (outcome variable definition); §1.4 (identity transform pre-registration) |
| **Construction** | `(1/N) × Σ Δ_country` for `N=3` countries (CO, BR, EU; KE skipped per design doc §10 row 1). `Δ_country = R_equity_country + Δlog(WC_CPI_country)` |
| **Source table** | `onchain_y3_weekly` (filtered by `source_methodology` per row recipe). |
| **Distribution (76-week primary)** | mean ≈ 0.005, std ≈ 0.015, range ≈ [−0.042, 0.042] (signed log-difference) |
| **Transform applied here** | None (identity — Y₃ is already a log-difference; cube-root would be dimensionally inappropriate). Spec §1.4. |
| **Sign convention** | rises when inequality widens via either rich-side equity gains OR working-class cost-of-living squeeze |

#### 2.1.1 Admitted `source_methodology` literals (byte-exact)

* `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` — Rev-5.3.2 primary panel (116 source rows; 76 joint with X_d × full controls). **Used by Rows 1–3, 5–8, 11–14.**
* `y3_v2_imf_only_sensitivity_3country_ke_unavailable` — Rev-5.3.2 IMF-IFS-only sensitivity (116 source rows; 56 joint). **Used by Row 4 only.**
* `y3_v1`, `y3_v1_3country_ke_unavailable` — pre-Rev-5.3.2 legacy literals; **NOT consumed by any Rev-2 panel** but admitted in the upstream guard.

The admitted set lives in `scripts.econ_query_api._KNOWN_Y3_METHODOLOGY_TAGS` (`frozenset`); typoes raise `ValueError` per the Rev-5.3.2 admitted-set guard (commit `2a0377057`).

### 2.2 Per-country diagnostics (preserved on every panel for Row 14 re-aggregation)

| Column | Type | Notes |
|---|---|---|
| `copm_diff` | `DOUBLE`, nullable | `Δ_CO = R_COLCAP + Δlog(WC_CPI_CO)` |
| `brl_diff`  | `DOUBLE`, nullable | `Δ_BR = R_IBOVESPA + Δlog(WC_CPI_BR)` |
| `kes_diff`  | `DOUBLE`, nullable | KE skipped → always `NULL` in the 3-country panel |
| `eur_diff`  | `DOUBLE`, nullable | `Δ_EU = R_STOXX600 + Δlog(WC_CPI_EU)` |

Row 14 reuses `(copm_diff, brl_diff, eur_diff)` as the inputs to the alternative-weight aggregation `{50/30/20, 70/20/10}`; this is performed by the Analytics Reporter at fit time without a new fetcher.

---

## 3. Variable of interest (X_d, RHS of spec equation §4.1)

### 3.1 `x_d`

| | |
|---|---|
| **Type** | `DOUBLE` (cast from VARCHAR via `TRY_CAST(value_usd AS DOUBLE)`) |
| **Source table** | `onchain_xd_weekly.value_usd` (filtered by `proxy_kind` per row recipe) |
| **Unit** | USD weekly volume |
| **Cleaning** | The source column is `VARCHAR` for arbitrary-precision preservation of the upstream Dune query result (per existing convention). Cast to DOUBLE on read; the joint-nonzero filter `TRY_CAST > 0` ensures NaN-from-bad-cast rows drop out. |
| **Range, primary panel** | observed min ≈ 1e3 USD, max ≈ 5e5 USD per week (carbon basket on Celo) |

#### 3.1.1 Admitted `proxy_kind` literals (byte-exact)

| Literal | n_nonzero (live DB) | Used by | Notes |
|---|---|---|---|
| `carbon_basket_user_volume_usd` | 77 / 82 | Rows 1–6, 11–14 | **Primary X_d.** Carbon DeFi `tokenstraded` events partitioned to `trader != BancorArbitrage` (user-only). Spec §1.1. |
| `carbon_basket_arb_volume_usd` | 45 / 82 | Row 7 | Diagnostic. `trader == BancorArbitrage` (arbitrage-only). |
| `carbon_per_currency_copm_volume_usd` | 47 / 82 | Row 8 | Diagnostic. Carbon volume restricted to COPM (Mento Colombian Peso) leg. |
| `carbon_basket_user_volume_usd` (LOCF cutoff) | 67 / 65 (joint) | Row 3 | Same primary X_d, with `week_start <= 2025-12-31` truncation. |

Other available `proxy_kind` literals (not consumed by any Phase-5a row):
* `b2b_to_b2c_net_flow_usd` (79 / 63)
* `net_primary_issuance_usd` (84 / 38)
* `carbon_per_currency_brlm_volume_usd` (82 / 44)
* `carbon_per_currency_eurm_volume_usd` (82 / 41)
* `carbon_per_currency_kesm_volume_usd` (82 / 30)
* `carbon_per_currency_usdm_volume_usd` (82 / 2)
* `carbon_per_currency_xofm_volume_usd` (82 / 0)

---

## 4. Control set (γ_1 … γ_6 in spec equation §4.1)

### 4.1 `vix_avg`

| | |
|---|---|
| **Type** | `DOUBLE` |
| **Unit** | volatility index points (VIX scale; ~10–80 range) |
| **Source table** | `weekly_panel.vix_avg` (Monday-anchored; shifted +4 days) |
| **Construction** | weekly mean of CBOE VIX daily closes (Mon–Fri inclusive) |
| **Pre-fit** | per Rev-4 Decision #7 (FX-vol notebook) |

### 4.2 `oil_return`

| | |
|---|---|
| **Type** | `DOUBLE` |
| **Unit** | log-return (dimensionless; weekly delta of `log(WTI_close)`) |
| **Source table** | `weekly_panel.oil_return` |
| **Construction** | `Δlog(WTI_friday_close)` weekly; uses last-positive close to skip illiquidity gaps |
| **Pre-fit** | per Rev-4 Decision #8 |

### 4.3 `us_cpi_surprise`

| | |
|---|---|
| **Type** | `DOUBLE` |
| **Unit** | percentage-point surprise (AR(1) residual) |
| **Source table** | `weekly_panel.us_cpi_surprise` |
| **Construction** | AR(1)-expanding-window monthly residual on US CPI; loaded onto the publication week (zero on non-release weeks) |
| **Pre-fit** | per Rev-4 Decision #5 |

### 4.4 `banrep_rate_surprise`

| | |
|---|---|
| **Type** | `DOUBLE` |
| **Unit** | bp surprise (event-study sign-preserving sum of ΔIBR) |
| **Source table** | `weekly_panel.banrep_rate_surprise` |
| **Construction** | per BanRep meeting day, the (T+0) − (T−1) IBR overnight change, sign-preserving sum into the meeting week; zero on non-meeting weeks |
| **Pre-fit** | per Rev-4 Decision #6 |

### 4.5 `fed_funds_weekly`

| | |
|---|---|
| **Type** | `DOUBLE` |
| **Unit** | percent (effective rate %) |
| **Source table** | `weekly_rate_panel.fed_funds_weekly` (Friday-anchored; **no shift required**) |
| **Construction** | weekly mean of the FRED `DFF` daily series |
| **Pre-fit** | per Task 11.M.6 schema split (Fed-funds factored out of `weekly_panel` into `weekly_rate_panel` for cadence-clean separation) |

### 4.6 `intervention_dummy`

| | |
|---|---|
| **Type** | `SMALLINT` (0 or 1) |
| **Unit** | binary flag |
| **Source table** | `weekly_panel.intervention_dummy` |
| **Construction** | 1 iff BanRep FX-intervention activity was reported in the week per `banrep_intervention_daily`; 0 otherwise |
| **Pre-fit** | per Rev-4 Decision #9 (replaces `cpi_surprise_ar1` per spec §4.4 substitution) |

### 4.7 Substitution rationale (spec §4.4)

`cpi_surprise_ar1` (Colombian CPI surprise, Rev-4 control) is **substituted** with `intervention_dummy` because Y₃ already contains `Δlog(WC_CPI)` directly on the LHS as part of its construction (see §2.1). Re-including a CPI surprise on the RHS would double-count the Colombian inflation channel. Reference: Anzoátegui-Zapata & Galvis 2019; Uribe-Gil & Galvis-Ciro 2022 (BIS WP 1022).

---

## 5. Lag-structure metadata

The primary specification (§4.1) is **contemporaneous X_d,t only**. Sensitivity Row 5 applies a one-period lag (`X_d_{t-1}`) at fit time — no panel-level transformation; the Analytics Reporter shifts the `x_d` column by one row.

Sensitivity Row 13 applies `Δlog(X_d)` and `ΔY₃` (first-difference) at fit time; this drops the first observation, yielding n = 75 at the regression stage even though the source panel has n = 76.

---

## 6. Methodology metadata (carried on every panel artifact)

While the parquet files do NOT include explicit methodology columns, the row-level metadata (X_d kind, Y₃ methodology, control set, LOCF cutoff) is captured in `_audit_summary.json` and reproduced in `manifest.md`. This is the audit trail for any downstream reproducibility check.

---

## 7. Source data lineage

```
Dune ──► onchain_carbon_tokenstraded   ─┐
                                        ├─► onchain_xd_weekly  (basket-aggregate user/arb/per-ccy partitions)
Dune ──► onchain_carbon_arbitrages     ─┘

DANE   ──► dane_ipc_monthly        ─┐
BCB    ──► bcb_ipca_monthly        ├─► (y3_compute) ──► onchain_y3_weekly  (Friday-anchored, LOCF-tail-extended)
Eurostat ► (DBnomics) ────────────┘                                     (per source_methodology)

FRED   ──► fred_daily              ───► weekly_panel  (Monday-anchored)
                                  └──► weekly_rate_panel (Friday-anchored)
BanRep ──► banrep_*_daily          ───► weekly_panel
DANE/BLS calendars              ───────► weekly_panel.is_*_release_week
```

All ingest paths upstream are read-only at this Phase-5a stage; no panel writes back into source tables. The DuckDB connection in `build_panel` is opened with `read_only=True` per the conftest fixture.
