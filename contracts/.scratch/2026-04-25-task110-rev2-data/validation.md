# Validation — Task 11.O Rev-2 Phase 5a Data Quality Checks

**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`
**Output dir:** `contracts/.scratch/2026-04-25-task110-rev2-data/`
**Validation script:** TDD test suite at `contracts/scripts/tests/inequality/test_phase5_data_prep.py` (18 assertions; all green at commit time)

This file documents the data-quality checks applied to each panel artifact, the byte-exact joint-nonzero counts vs. spec pre-commitments, and the outlier flagging conventions. Per the Data Engineer agent contract, **outliers are flagged but never removed**; the Analytics Reporter at Phase 5b decides whether to act on them.

---

## 1. Joint-nonzero count audit (gate-bearing)

The spec pre-commits five joint-nonzero counts (§5 anti-fishing audit table + §6 resolution matrix). These are byte-exact reproduced from the live DuckDB by `build_panel`. Drift on any of these would silently corrupt the regression sample size and break the spec's pre-registered FAIL gates.

| Row | Pre-committed n | Actual n | Match | Spec ref |
|---|---|---|---|---|
| Row 1 (primary) | 76 | **76** | OK | §5 + §6 |
| Row 3 (LOCF-tail-excluded) | 65 | **65** | OK | §6 row 3 (RC probe-5) |
| Row 4 (IMF-IFS-only) | 56 | **56** | OK | §5 + §6 row 4 |
| Row 7 (arb-only) | 45 | **45** | OK | §6 row 7 |
| Row 8 (per-currency COPM) | 47 | **47** | OK | §6 row 8 |

**Verification mechanism:** `test_build_panel_row_*_returns_*_rows` in the TDD suite. These tests query the live `contracts/data/structural_econ.duckdb` via the session-scoped `conn` fixture; no synthetic fixtures.

---

## 2. Time-alignment validation

### 2.1 Anchor convention sources

| Table | Anchor (isodow) | Source-of-truth |
|---|---|---|
| `onchain_xd_weekly` | 5 (Friday) | per `weekly_onchain_flow_vector` ingest convention |
| `onchain_y3_weekly` | 5 (Friday) | per `y3_compute` Friday-anchor lock |
| `weekly_panel` | **1 (Monday)** | per Rev-4 prior-art convention |
| `weekly_rate_panel` | 5 (Friday) | per Task 11.M.6 schema split |

The `weekly_panel` Monday anchor is **reconciled to Friday** inside `build_panel`'s `wp_friday` CTE via `(week_start + INTERVAL 4 DAY)::DATE`. All output rows are Friday-anchored.

### 2.2 Tests enforcing the invariant

* `test_weekly_panel_is_monday_anchored` — verifies the source is Monday before the shift.
* `test_other_weekly_tables_are_friday_anchored` — verifies the three Friday-native tables.
* `test_build_panel_returns_friday_anchored_rows_only` — verifies the OUTPUT is always Friday after the shift.

### 2.3 Per-row anchor + duplicate audit

| Row | n | isodow | n_duplicate_week_starts |
|---|---|---|---|
| Row 1 | 76 | {5} | 0 |
| Row 3 | 65 | {5} | 0 |
| Row 4 | 56 | {5} | 0 |
| Row 6 | 76 | {5} | 0 |
| Row 7 | 45 | {5} | 0 |
| Row 8 | 47 | {5} | 0 |

All buildable rows have a clean Friday anchor with zero duplicate week_starts.

---

## 3. Missing-data handling

### 3.1 Joint-nonzero filter (load-bearing)

A row is admitted into the panel iff **ALL** of:

1. `TRY_CAST(onchain_xd_weekly.value_usd AS DOUBLE) > 0` for the requested `proxy_kind`.
2. `onchain_y3_weekly.y3_value` is present (non-null) for the requested `source_methodology`.
3. Every requested control column is non-null at the matching Friday anchor.
4. (Optional) `week_start <= locf_tail_cutoff` if a cutoff is supplied.

This is the **same filter** the Reality Checker probe-5 applied at the cutoff sweep in `2026-04-25-y3-rev532-review-reality-checker.md`. Deviating from it would change the joint-nonzero counts pre-committed in spec §5.

### 3.2 No silent imputation

No control column is imputed. No NaN-to-zero substitution. No interpolation across weeks. The TDD suite enforces this via `test_build_panel_no_null_in_six_controls`: every panel row has every requested control non-null.

### 3.3 KE-skip discipline

`onchain_y3_weekly.kes_diff` is intentionally NULL on every row of the primary methodology (`y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`); this is design-locked per the Y₃ design doc §10 row 1 and is NOT a data-quality defect. The N=3 equal-weight aggregator in `y3_compute` averages over `(copm_diff, brl_diff, eur_diff)` and gracefully ignores `kes_diff`. The panels carry `kes_diff` as an explicit NULL column for the Row 14 alt-weights re-aggregation to retain the full per-country surface.

---

## 4. Outlier flagging (NOT removed)

Per the Data Engineer agent contract, **outliers are flagged and surfaced; they are NOT removed**. The Analytics Reporter at Phase 5b is the deciding party. Below are the |z| > 3 counts on the **primary panel** (Row 1, n=76).

| Column | mean | std | min | max | |z| > 3 |
|---|---|---|---|---|---|
| `y3_value` | +0.0049 | 0.0147 | −0.0424 | +0.0418 | 1 |
| `x_d` | +77,415 | 113,309 | +72.43 | +504,506 | 2 |
| `vix_avg` | +18.65 | 4.48 | +13.28 | +42.24 | 1 |
| `oil_return` | +0.0034 | 0.0556 | −0.1274 | +0.3042 | 1 |
| `us_cpi_surprise` | +0.0049 | 0.0422 | −0.1844 | +0.1552 | 2 |
| `banrep_rate_surprise` | −0.0069 | 0.1473 | −0.5130 | +0.9950 | 3 |
| `fed_funds_weekly` | +4.21 | 0.346 | +3.64 | +4.83 | 0 |
| `intervention_dummy` | +0.026 | 0.161 | 0 | 1 | 2* |

\* `intervention_dummy` |z|>3 count is not a meaningful outlier flag for a binary indicator; reported for completeness only.

### 4.1 Notable observations

* **`x_d` is heavy right-tailed** — std (~113k) exceeds mean (~77k), and max (~504k) is ~6.5× the mean. This is consistent with Carbon DeFi's irregular volume (whale weeks). The Analytics Reporter should consider `log(x_d)` if the Phase 5b residual diagnostics suggest variance heterogeneity.
* **`vix_avg` max = 42.24** — a single high-VIX week (likely 2025 Q3 macro stress); this is a real macro spike, not data error.
* **`banrep_rate_surprise` max = +0.995** — a single ~100bp BanRep meeting surprise; consistent with the 2025 cutting-cycle reversal events.

None of these outliers should be removed by the Data Engineer; they reflect real macro-financial variation and removing them would bias the regression sample. They are surfaced here so the Analytics Reporter can document any decision (residual-diagnostic-driven trimming, robust regression, etc.) explicitly in their Phase 5b memo.

---

## 5. Schema-invariant tests (defense against silent column-name drift)

The TDD suite includes 4 schema-shape audits that run against the live DuckDB on every test invocation:

1. `test_onchain_xd_weekly_schema_exposes_value_usd_and_proxy_kind` — verifies the X_d source-table columns.
2. `test_onchain_y3_weekly_schema_exposes_y3_and_per_country_diffs` — verifies the Y₃ source-table columns.
3. `test_weekly_panel_schema_exposes_six_macro_controls` — verifies five-of-six controls live in `weekly_panel`.
4. `test_weekly_rate_panel_schema_exposes_fed_funds_weekly` — verifies the Fed-funds split.

Any upstream rename (e.g., `value_usd` → `usd_value`, or `vix_avg` re-located out of `weekly_panel`) will fire one of these tests immediately, before the panel-build helpers can corrupt downstream analysis.

---

## 6. Methodology admitted-set guard (defense-in-depth)

`test_build_panel_rejects_unknown_y3_methodology` verifies that passing a typoed `y3_methodology` (e.g., `'y3_v999_typoed'`) raises `ValueError` immediately, with the admitted-set enumerated in the error message. This re-tests the admitted-set guard from `scripts.econ_query_api._KNOWN_Y3_METHODOLOGY_TAGS` (Rev-5.3.2 commit `2a0377057`) at the panel-build seam.

---

## 7. Per-row sample-size summary post-control-inclusion

| Row | n_obs | n_x_d_nonzero | dt_min | dt_max | Status |
|---|---|---|---|---|---|
| Row 1 (primary) | 76 | 76 | 2024-09-27 | 2026-03-13 | OK |
| Row 2 (bootstrap recon) | 76 | 76 | 2024-09-27 | 2026-03-13 | OK (same panel as Row 1) |
| Row 3 (LOCF-tail-excluded) | 65 | 65 | 2024-09-27 | 2025-12-26 | OK (pre-registered FAIL) |
| Row 4 (IMF-only) | 56 | 56 | 2024-09-27 | 2025-10-24 | OK (pre-registered dual-FAIL) |
| Row 5 (lag) | 76 | 76 | 2024-09-27 | 2026-03-13 | OK (lag applied at fit time → 75) |
| Row 6 (parsimonious) | 76 | 76 | 2024-09-27 | 2026-03-13 | OK |
| Row 7 (arb-only) | 45 | 45 | 2024-08-30 | 2025-07-04 | OK (under-N diagnostic) |
| Row 8 (per-ccy COPM) | 47 | 47 | 2024-10-04 | 2025-09-26 | OK (under-N diagnostic) |
| Row 9 (Y₃-bond) | **0** | **0** | — | — | **DEFERRED** (spec §10 ε.2) |
| Row 10 (population-weighted) | **0** | **0** | — | — | **DEFERRED** (spec §10 ε.3) |
| Row 11 (Student-t) | 76 | 76 | 2024-09-27 | 2026-03-13 | OK (same panel as Row 1) |
| Row 12 (HAC(12)) | 76 | 76 | 2024-09-27 | 2026-03-13 | OK (same panel as Row 1) |
| Row 13 (first-differenced) | 76 | 76 | 2024-09-27 | 2026-03-13 | OK (Δ at fit time → 75) |
| Row 14 (WC-CPI weights sens) | 76 | 76 | 2024-09-27 | 2026-03-13 | OK (alt-weight re-aggregation at fit time) |

---

## 8. Test invocation reference

```bash
cd contracts && source .venv/bin/activate
PYTHONPATH=. python -m pytest scripts/tests/inequality/test_phase5_data_prep.py -v
```

Expected: 18 passed (12 build-panel tests + 6 schema/anchor invariant tests).

Test breakdown:
* Section 1 (schema): 4 tests
* Section 2 (anchor): 2 tests
* Section 3 (joint-nonzero): 5 tests (Row 1, 3, 4, 7, 8)
* Section 4 (output-column contract): 4 tests
* Section 5 (audit helper): 1 test
* Section 6 (admitted-set guard): 1 test

Pre-implementation (red phase): 12 of 18 fail with `ModuleNotFoundError: No module named 'scripts.phase5_data_prep'`. Post-implementation (green phase): 18 of 18 pass.

---

## 9. Anti-fishing posture

Per the spec §9 anti-fishing audit trail and `feedback_pathological_halt_anti_fishing_checkpoint`:

* **No silent threshold tuning.** The five joint-nonzero counts (76 / 65 / 56 / 45 / 47) are PRESERVED byte-exact from the spec; deviation requires a CORRECTIONS block in the next plan revision and a 3-way review.
* **No mid-stream X_d swap.** The primary X_d is locked to `carbon_basket_user_volume_usd`; no post-hoc swap to `b2b_to_b2c_net_flow_usd` (which has 79 nonzero weeks, a temptation rejected per §9.4).
* **No silent test-pass.** Every test in the suite either fails red before implementation or asserts a load-bearing invariant against live DuckDB. No empty-assert / always-true scaffolding.
* **No missing-data imputation.** All NaN handling is by row-drop via the joint-nonzero filter, never by imputation.
