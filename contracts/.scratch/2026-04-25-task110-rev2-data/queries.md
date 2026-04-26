# Queries — Task 11.O Rev-2 Phase 5a Panel Construction

**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (commit `d9e7ed4c8`)
**Output dir:** `contracts/.scratch/2026-04-25-task110-rev2-data/`
**Builder module:** `contracts/scripts/phase5_data_prep.py` (single public entry point: `build_panel`)
**Database:** `contracts/data/structural_econ.duckdb` (read-only)

This file documents the DuckDB SQL underpinning each of the 14 resolution-matrix rows. Every row consumes the same JOIN structure with parametric variation in three dimensions: (a) `proxy_kind` for X_d, (b) `source_methodology` for Y₃, (c) the control list. Optional `locf_tail_cutoff` truncates `week_start` at the upper bound (Row 3 only).

---

## 1. Master JOIN template

All 14 rows derive from one canonical join. Variable substitution per row is documented in §3.

```sql
WITH xd AS (
    SELECT week_start, value_usd, is_partial_week, proxy_kind
    FROM onchain_xd_weekly
    WHERE proxy_kind = ?                                -- $1: x_d_kind
),
y3 AS (
    SELECT week_start, y3_value, copm_diff, brl_diff,
           kes_diff, eur_diff, source_methodology
    FROM onchain_y3_weekly
    WHERE source_methodology = ?                        -- $2: y3_methodology
),
wp_friday AS (
    -- Translate weekly_panel from Monday-anchor to Friday-anchor.
    -- Spec §1.2 invariant: every panel row lives on a Friday.
    SELECT (week_start + INTERVAL 4 DAY)::DATE AS week_start,
           vix_avg, oil_return, us_cpi_surprise,
           banrep_rate_surprise, intervention_dummy,
           is_cpi_release_week, is_ppi_release_week
    FROM weekly_panel
)
SELECT
    xd.week_start,
    y3.y3_value,
    y3.copm_diff, y3.brl_diff, y3.kes_diff, y3.eur_diff,
    TRY_CAST(xd.value_usd AS DOUBLE) AS x_d,
    wp.vix_avg,                                          -- $3..$8: subset of these
    wp.oil_return,
    wp.us_cpi_surprise,
    wp.banrep_rate_surprise,
    wrp.fed_funds_weekly,
    wp.intervention_dummy
FROM xd
INNER JOIN y3 USING (week_start)                         -- inner: requires Y₃ presence
LEFT JOIN wp_friday wp USING (week_start)                -- left: control NOT NULL filter in WHERE
LEFT JOIN weekly_rate_panel wrp USING (week_start)       -- left: same
WHERE TRY_CAST(xd.value_usd AS DOUBLE) > 0               -- joint-nonzero gate on X_d
  AND wp.vix_avg              IS NOT NULL                -- joint-nonzero on every requested control
  AND wp.oil_return           IS NOT NULL
  AND wp.us_cpi_surprise      IS NOT NULL
  AND wp.banrep_rate_surprise IS NOT NULL
  AND wp.intervention_dummy   IS NOT NULL
  AND wrp.fed_funds_weekly    IS NOT NULL
  -- Optional: AND xd.week_start <= ?                    -- $9: locf_tail_cutoff (Row 3 only)
ORDER BY xd.week_start
```

### 1.1 Why each JOIN is INNER vs. LEFT

* **`xd INNER JOIN y3 USING (week_start)`** — both sides must be present at the Friday anchor; weeks where either is missing drop out. This is the joint-nonzero baseline for X_d × Y₃.
* **`LEFT JOIN wp_friday`** + `WHERE wp.* IS NOT NULL` — semantically identical to an INNER JOIN on the `(week_start, vix_avg IS NOT NULL, …)` predicate. We use the LEFT-then-WHERE form so we can compose the WHERE filter dynamically per row's control set without rewriting the JOIN.
* **`LEFT JOIN weekly_rate_panel`** + `WHERE wrp.fed_funds_weekly IS NOT NULL` — same composition pattern.

### 1.2 Friday-anchor reconciliation (load-bearing)

`weekly_panel` is **Monday-anchored** (Rev-4 prior-art convention; verified live as `EXTRACT('isodow' FROM week_start) = 1`). Every other table in the JOIN is Friday-anchored (`isodow = 5`). The `+ INTERVAL 4 DAY` shift in the `wp_friday` CTE translates Monday → Friday of the same calendar week.

This is enforced by the test suite in two complementary checks:
* `test_weekly_panel_is_monday_anchored` — verifies the source is Monday.
* `test_other_weekly_tables_are_friday_anchored` — verifies the joined tables are Friday.
* `test_build_panel_returns_friday_anchored_rows_only` — verifies the OUTPUT is Friday.

If any of these flips, the joint-nonzero count silently zeroes (we observed exactly this behavior pre-fix: `WHERE wp.vix_avg IS NOT NULL` yielded `n=0` because all `wp.week_start` were Monday and never matched the Friday-anchored xd/y3 rows).

---

## 2. Row recipes (parameter substitution map)

### Row 1 — Primary (gate-bearing)

```python
build_panel(
    conn,
    x_d_kind='carbon_basket_user_volume_usd',
    y3_methodology='y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable',
    controls=('vix_avg', 'oil_return', 'us_cpi_surprise',
              'banrep_rate_surprise', 'fed_funds_weekly', 'intervention_dummy'),
)
```

Pre-committed n = **76** (spec §5 + §6). Output: `panel_row_01_primary.parquet`.

### Row 2 — Bootstrap reconciliation

Same panel as Row 1; estimator differs at fit time. Output: `panel_row_02_bootstrap_recon.parquet` (byte-identical content to Row 1; preserved as a separate artifact for downstream traceability).

### Row 3 — LOCF-tail-excluded sensitivity

```python
build_panel(
    conn,
    x_d_kind='carbon_basket_user_volume_usd',
    y3_methodology='y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable',
    controls=SIX_CONTROLS,
    locf_tail_cutoff=date(2025, 12, 31),         # truncates 11 LOCF-tail weeks
)
```

Pre-committed n = **65** (spec §6 + Reality Checker probe-5 in `2026-04-25-y3-rev532-review-reality-checker.md`). The cutoff `2025-12-31` is the EU HICP last-real-publication boundary; weeks after this carry LOCF-extended EU CPI. Output: `panel_row_03_locf_tail_excluded.parquet`.

### Row 4 — IMF-IFS-only sensitivity

```python
build_panel(
    conn,
    x_d_kind='carbon_basket_user_volume_usd',
    y3_methodology='y3_v2_imf_only_sensitivity_3country_ke_unavailable',
    controls=SIX_CONTROLS,
)
```

Pre-committed n = **56** (spec §5 — dual-axis FAIL: N < 75 AND power < 0.80). Output: `panel_row_04_imf_only_sensitivity.parquet`.

### Row 5 — Lag sensitivity

Same panel as Row 1; the X_d{t-1} substitution is performed by the Analytics Reporter at fit time (single-column shift). Output: `panel_row_05_lag_sensitivity.parquet`.

### Row 6 — Parsimonious controls

```python
build_panel(
    conn,
    x_d_kind='carbon_basket_user_volume_usd',
    y3_methodology='y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable',
    controls=('vix_avg', 'oil_return', 'intervention_dummy'),
)
```

Pre-committed n = **76** (drops 3 controls but no row drops because the 6-control filter already required all 6 non-null; the 3-control set is a subset). Output: `panel_row_06_parsimonious_controls.parquet`.

### Row 7 — Arb-only diagnostic

```python
build_panel(
    conn,
    x_d_kind='carbon_basket_arb_volume_usd',
    y3_methodology='y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable',
    controls=SIX_CONTROLS,
)
```

Pre-committed n = **45** (under-N; diagnostic only — `BancorArbitrage` `0x8c05ea30…` trader filter). Output: `panel_row_07_arb_only.parquet`.

### Row 8 — Per-currency COPM diagnostic

```python
build_panel(
    conn,
    x_d_kind='carbon_per_currency_copm_volume_usd',
    y3_methodology='y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable',
    controls=SIX_CONTROLS,
)
```

Pre-committed n = **47**. Output: `panel_row_08_per_currency_copm.parquet`.

### Row 9 — Y₃-bond diagnostic — **DEFERRED**

Bond-data fetcher (10Y sovereign-bond yield-change replacing R_equity) not yet ingested per spec §10 ε.2. Out-of-scope for Phase 5a. Empty schema-typed parquet emitted: `panel_row_09_y3_bond_diagnostic.parquet`.

### Row 10 — Population-weighted aggregation — **DEFERRED**

Aggregator weight-vector argument unbuilt per spec §10 ε.3. Out-of-scope for Phase 5a. Empty schema-typed parquet emitted: `panel_row_10_population_weighted.parquet`.

### Row 11 — Student-t innovations

Same panel as Row 1; Student-t refit at Analytics Reporter fit-time. Output: `panel_row_11_student_t.parquet`.

### Row 12 — HAC(12) bandwidth

Same panel as Row 1; HAC truncation lag swap from 4 → 12 at fit time. Output: `panel_row_12_hac12_bandwidth.parquet`.

### Row 13 — First-differenced

Same panel as Row 1; Δlog(X_d) and ΔY₃ transforms at fit time (Analytics Reporter drops the first row, yielding n=75 at the regression stage). Output: `panel_row_13_first_differenced.parquet`.

### Row 14 — WC-CPI weights sensitivity

Same panel as Row 1. The per-country diff columns (`copm_diff`, `brl_diff`, `eur_diff`) are preserved on every panel row so the Analytics Reporter can re-aggregate Y₃ under alternative working-class-bundle weights {50/30/20, 70/20/10} at fit time without re-running any fetcher. Output: `panel_row_14_wc_cpi_weights_sens.parquet`.

---

## 3. SQL fragment composition logic

The implementation in `scripts/phase5_data_prep.py` builds the SQL programmatically per row — there is no fixed string template. Helpers:

* `_build_select_columns_sql(controls)` → comma-joined SELECT pieces, dispatching `vix_avg / oil_return / us_cpi_surprise / banrep_rate_surprise / intervention_dummy` to the `wp.` alias and `fed_funds_weekly` to the `wrp.` alias.
* `_build_where_clause(controls)` → ` AND `-joined `wp.col IS NOT NULL` / `wrp.col IS NOT NULL` predicates.
* The optional `locf_tail_cutoff` argument appends ` AND xd.week_start <= ?` to the WHERE clause.

This design lets the same canonical CTE structure satisfy every row (1–8, 11–14) without per-row SQL string maintenance — the only deviations are `proxy_kind`, `source_methodology`, the control set, and the LOCF cutoff.

---

## 4. Why this composition matters

The original spec authoring computed pre-committed counts (76, 65, 56, 45, 47) at memo-write time. Reproducing them byte-exact downstream is the load-bearing **anti-fishing audit**: if any panel drift goes unnoticed, the spec's pre-registered FAIL gates (Rows 3 and 4) lose discipline. The TDD test suite in `scripts/tests/inequality/test_phase5_data_prep.py` re-validates these five counts against live DuckDB on every run.

Any future schema change (renaming `value_usd` to `usd_value`, splitting `vix_avg` out of `weekly_panel`, etc.) will fail the schema-invariant tests (Section 1) before it can corrupt a downstream regression.
