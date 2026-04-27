# Data Schema & Acquisition Strategy Review — Data Engineer

**Date:** 2026-04-16
**Spec reviewed:** `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md`
**Upstream reference:** `contracts/notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)
**Reviewer role:** Data Engineer (schema normalization, pipeline idempotency, DuckDB specifics)

---

## 1. Schema Normalization

### BLOCK-01: `download_manifest` has no primary key

The `download_manifest` table has no PK or unique constraint. The same source can be downloaded multiple times (intended for audit), but without a synthetic PK or a composite key, there is no way to:
- Reference a specific download from other tables (e.g., linking raw rows to the manifest entry that produced them).
- Prevent accidental exact-duplicate manifest rows from a retried HTTP request that succeeds twice in the same second.

**Fix:** Add either `(source, downloaded_at)` as composite PK (if timestamps are guaranteed unique per source), or an auto-incrementing `id INTEGER PRIMARY KEY` (DuckDB supports `CREATE SEQUENCE` + `DEFAULT nextval()`). The composite approach is cleaner for a functional pipeline.

### FLAG-01: `fred_daily` and `fred_monthly` long-format PK relies on VARCHAR series_id

The composite PK `(series_id, date)` uses VARCHAR for `series_id`. This is fine for correctness and DuckDB handles VARCHAR PKs well, but the spec doesn't define an allowed-values constraint. If a typo like `DEXCUOS` is inserted, it becomes a phantom series silently.

**Fix:** Add a CHECK constraint: `CHECK (series_id IN ('DEXCOUS', 'VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU'))` on `fred_daily`, and `CHECK (series_id IN ('CPIAUCSL'))` on `fred_monthly`. This is cheap defensive coding.

### NIT-01: `dane_release_calendar` uses (year, month, series) PK instead of (release_date, series)

The PK `(year, month, series)` is semantically correct (one release per reference-month per series). However, the join to `weekly_panel` is on `release_date`, not on `(year, month)`. The PK doesn't prevent two rows with the same `release_date` and `series` (e.g., if DANE reschedules and both the original and actual dates get entered). This is a minor risk — manual compilation makes duplicates unlikely — but a UNIQUE constraint on `(release_date, series)` would be a useful safety net.

---

## 2. Pipeline Idempotency

### BLOCK-02: No upsert strategy defined for raw tables

The spec says raw tables are "append-only after initial download" and re-running "updates raw tables (append new observations)." But there is no explicit upsert/dedup mechanism:

- **FRED tables:** If the pipeline re-downloads the full series (FRED API returns the entire history by default unless `observation_start` is set), a naive `INSERT` will violate the PK constraint. An `INSERT OR REPLACE` / `INSERT ... ON CONFLICT DO UPDATE` must be specified.
- **DANE tables:** Same issue. Re-downloading monthly IPC/IPP data and inserting will clash with existing PKs.
- **Manifest table:** Append-only is correct here (each run is a new row), but only if the PK issue from BLOCK-01 is resolved.

**Fix:** Specify the conflict resolution strategy for each raw table. Recommended: `INSERT OR REPLACE` for all raw tables (the source of truth is the upstream API; local stale data should be overwritten). This makes the pipeline idempotent: run N times, get the same result.

### FLAG-02: weekly_panel recomputation is full-refresh but no TRUNCATE/DROP is specified

The spec says weekly_panel is "recomputed from raw tables — never manually edited." But it doesn't say whether the recomputation is `DROP TABLE + CREATE` or `DELETE FROM + INSERT` or `CREATE OR REPLACE TABLE`. For a ~1,100 row table this is trivial performance-wise, but the spec should be explicit.

**Fix:** Specify `CREATE OR REPLACE TABLE weekly_panel AS (...)` as the recomputation strategy. This is idempotent and atomic in DuckDB.

---

## 3. Long-Format vs Wide-Format

### NIT-02: Long format for `fred_daily` is the correct choice — no issue

Long format with `series_id` discriminator is the right call for FRED daily data:
- Series have different trading calendars (DEXCOUS has no weekends/holidays; VIXCLS has different holiday schedules; oil may differ).
- Adding a new FRED series requires zero schema changes.
- The weekly_panel derivation naturally pivots via `WHERE series_id = 'X'` filters.

Wide format would force NULL-filling for calendar mismatches and require ALTER TABLE for new series. Long format wins clearly.

One minor observation: `fred_monthly` uses the same long format but currently has only one series (`CPIAUCSL`). This is forward-compatible (if US PPI or Fed Funds rate are added later) at no cost. Good design.

---

## 4. Manifest Design

### FLAG-03: Manifest lacks `file_path` or `url` column for full reproducibility

The manifest captures `sha256` of the response body and `source` identifier, but not the actual URL or file path used. For reproducibility:
- FRED API URLs include query parameters (`observation_start`, `file_type`) that affect the response.
- DANE downloads may come from different portal URLs over time.
- Manual CSV downloads should record the filesystem path of the source file.

**Fix:** Add a `url_or_path VARCHAR` column to capture the exact retrieval location.

### FLAG-04: Manifest `status` enum is ambiguous between `success` and `verified`

The spec defines four statuses: `success`, `failure`, `verified`, `unavailable`. The distinction between `success` (download completed) and `verified` (source confirmed available) is unclear:
- Priority 1 verification produces `verified` or `unavailable`.
- Priority 2/3 downloads produce `success` or `failure`.
- But what if a Priority 1 source is verified AND successfully downloaded in the same run? Two rows? One row with status updated?

**Fix:** Define the lifecycle explicitly. Suggestion: `verified` = source confirmed accessible (no data downloaded yet); `success` = data downloaded and inserted; `failure` = download attempted and failed; `unavailable` = source confirmed not machine-readable. A single source may have multiple manifest rows (one `verified`, then one `success`), which is fine for an audit trail.

---

## 5. Raw-to-Derived Computation (weekly_panel)

### BLOCK-03: First log-return of each week requires the prior trading day's price, which may be in the prior week

The RV computation says: "collect all daily COP/USD observations within Monday-Friday. Compute log-returns: r_d = log(P_d / P_{d-1})."

If Monday is a trading day, `P_{d-1}` is Friday of the prior week. But the collection window is "within Monday-Friday" of the current week. This means Monday's return requires a price OUTSIDE the current week's window.

Two sub-issues:
1. The spec must clarify that the price lookup window extends to the prior Friday (or the last available trading day before Monday).
2. For the first week in the sample (~Jan 2003), there is no prior price. The first week must either be dropped or have `rv = NULL`.

Additionally: if Monday is a holiday and Tuesday is the first trading day, the return `log(P_Tue / P_Fri)` spans a weekend+holiday. This is standard practice (Andersen et al. 2003 do not gap-adjust), but worth documenting as a deliberate design choice.

**Fix:** Specify that log-return computation uses the last available DEXCOUS price, regardless of week boundary. Document that multi-day gaps (holidays) are NOT adjusted — the return absorbs the full gap, which is standard.

### BLOCK-04: `oil_return` definition is ambiguous about "Friday close"

"Weekly WTI log-return (Friday close / prior Friday close)" — but DCOILWTICO is a daily spot price, not a "close." More critically: if Friday is a holiday, which day is used? The spec should say "last trading day of current week vs last trading day of prior week," consistent with how RV handles missing days.

**Fix:** Define oil_return as `log(last_available_price_this_week / last_available_price_prior_week)` using DCOILWTICO from fred_daily. Same for oil_log_level: `log(last_available_price_this_week)`.

### FLAG-05: US CPI surprise mapping lacks BLS release calendar table

The spec says US CPI surprise is "mapped to the week containing the BLS release date (BLS publishes a release calendar analogous to DANE's)." But there is no `bls_release_calendar` table defined in the schema. Without it, the pipeline cannot determine which week a US CPI release falls in.

Options:
1. Add a `bls_release_calendar` table (analogous to `dane_release_calendar`).
2. Use FRED's built-in release date metadata (`realtime_start` / `realtime_end` in the API response) to infer release weeks.
3. Hard-code the BLS release schedule (less robust).

**Fix:** Add a `bls_release_calendar` table or specify that FRED vintage dates will be used. This is needed for the `us_cpi_surprise` column derivation.

### FLAG-06: AR(1) warmup period for US CPI surprise is not specified in the derivation

The acquisition spec (Priority 3) correctly notes CPIAUCSL should start "1yr before DEXCOUS start (AR(1) warmup)." But the weekly_panel derivation section does not mention:
- How the AR(1) model is estimated (rolling? expanding window? full-sample?).
- Whether the first 12 months of surprises are dropped from the panel (warmup contamination).
- Whether the AR(1) parameters are re-estimated on each pipeline run or fixed.

**Fix:** Specify that the AR(1) is estimated on an expanding window (or full-sample), the first 12 months of CPIAUCSL are warmup-only (not in weekly_panel), and parameters are re-estimated on full rebuild. This is a computation spec detail, but the schema review must flag it because the weekly_panel derivation is underspecified without it.

### NIT-03: `vix_avg` is weekly average but upstream spec uses VIX_t without specifying averaging

The upstream spec (Section 4.3) uses $\text{VIX}_t$ as a control. The data schema defines `vix_avg` as "weekly average of VIXCLS daily closes." This is a reasonable choice, but alternatives include Friday close or week-open. The choice should be documented as deliberate (weekly average smooths intra-week noise, which is appropriate for a weekly regression).

---

## 6. Missing Tables or Columns

### BLOCK-05: No Brent oil price handling in weekly_panel

The upstream spec (Section 4.3, variable table) lists BOTH `DCOILWTICO` (WTI) and `DCOILBRENTEU` (Brent) as potential oil series. The weekly_panel only defines `oil_return` and `oil_log_level` without specifying WHICH oil series. Sensitivity spec A8 adds oil log-level but doesn't clarify WTI vs Brent.

**Fix:** Either (a) commit to WTI as primary and Brent as sensitivity, with both computed in weekly_panel (`oil_return_wti`, `oil_return_brent`, etc.), or (b) specify WTI as the sole series with a note that Brent is available in fred_daily for ad-hoc sensitivity. Option (b) is simpler and sufficient.

### FLAG-07: No `cpi_surprise_ar1` column for the AR(1) fallback

The upstream spec (Section 4.1) defines an AR(1) fallback for Colombian CPI surprise if BanRep EME consensus is unavailable. The weekly_panel has `dane_ipc_pct` (raw MoM change) but no pre-computed AR(1) CPI surprise column. The deferred `cpi_surprise_survey` handles the consensus case, but the AR(1) version — which is the LIKELY scenario given EME access uncertainty — has no column.

**Fix:** Add `cpi_surprise_ar1 DOUBLE` to weekly_panel: AR(1) residual of DANE IPC MoM change, mapped to the release week. This is computable from confirmed data (dane_ipc_monthly + dane_release_calendar) and should be a core column, not deferred.

### FLAG-08: No `dane_ipp_surprise` or standardized PPI change column

The upstream spec co-primary decomposition uses $\tilde{s}_t^{\text{PPI}} = (\Delta\text{IPP}_t - \overline{\Delta\text{IPP}}) / \hat{\sigma}_{\Delta\text{IPP}}$ (standardized PPI change). The weekly_panel has `dane_ipp_pct` (raw) but no standardized version. Similarly, the CPI surprise (whether AR(1) or survey) is standardized in the upstream spec ($s_t^{\text{CPI}}$ divided by historical sigma).

This is arguably estimation-layer work, not data-pipeline work. But if the pipeline produces the weekly_panel as estimation-ready, the standardized versions should either be included or explicitly deferred to the estimation module.

**Fix:** Document that standardization (mean-subtraction + sigma-division) is performed by the estimation module, not the data pipeline. This is a valid design boundary — the pipeline provides raw inputs, estimation applies transforms. But it must be stated explicitly to avoid confusion about what "estimation-ready" means.

### NIT-04: `is_release_week` does not distinguish CPI-only vs PPI-only vs both

The column is a simple boolean. The upstream spec's co-primary decomposition needs to know whether CPI, PPI, or both were released in a given week (they often co-release but not always). Two separate booleans (`is_cpi_release_week`, `is_ppi_release_week`) would be more useful.

**Fix:** Replace `is_release_week BOOLEAN` with `is_cpi_release_week BOOLEAN` and `is_ppi_release_week BOOLEAN`. Keep the composite `is_release_week` as a computed column if desired: `is_cpi_release_week OR is_ppi_release_week`.

### NIT-05: No `n_vix_days` or `n_oil_days` quality columns

The panel includes `n_trading_days` for RV (number of returns), which is important for interpreting weeks with holidays. But VIX and oil have their own holiday calendars. A week where DEXCOUS has 5 days but VIXCLS has 4 (or vice versa) is handled implicitly (average still works), but recording the count aids diagnostics.

---

## 7. DuckDB-Specific Concerns

### FLAG-09: DuckDB does not enforce PRIMARY KEY constraints at insert time (pre-1.2)

As of DuckDB 1.1.x, PRIMARY KEY constraints are defined but NOT enforced on INSERT — duplicate PKs can be silently inserted. DuckDB 1.2+ (and the spec targets 1.5.1) DOES enforce PK constraints, so this is version-dependent.

**Fix:** Since the spec targets duckdb 1.5.1, PK enforcement is available. Add a note that the pipeline requires duckdb >= 1.2.0 for PK constraint enforcement. If running on an older version, the pipeline must add explicit dedup logic before insert.

### NIT-06: DOUBLE vs DECIMAL for financial data

The spec uses DOUBLE for all numeric columns. For the IPC/IPP indices and percentage changes, DOUBLE is fine (these are published as floating-point values). For currency exchange rates (DEXCOUS), DOUBLE introduces floating-point representation error in log-return calculations, but the error magnitude (~1e-16) is far below the measurement noise in FRED noon rates. No practical concern.

If exact reproducibility with external tools (Excel, R) is needed, DECIMAL(18,6) would be safer for raw prices. But for a research pipeline where all computation is in Python/DuckDB, DOUBLE is the pragmatic choice.

### NIT-07: No explicit schema name or namespace

All tables are in the default `main` schema. For a single-purpose database (`structural_econ.duckdb`) this is fine. If the database ever shared space with other datasets, a `CREATE SCHEMA structural_econ` namespace would be warranted. Not needed now.

---

## Issue Summary

| # | Severity | Category | Description |
|---|---|---|---|
| BLOCK-01 | BLOCK | Schema | `download_manifest` has no primary key |
| BLOCK-02 | BLOCK | Idempotency | No upsert/conflict resolution strategy for raw tables |
| BLOCK-03 | BLOCK | Derivation | RV log-return requires prior-week price; cross-week lookup unspecified |
| BLOCK-04 | BLOCK | Derivation | `oil_return` "Friday close" definition ambiguous for holidays |
| BLOCK-05 | BLOCK | Missing column | WTI vs Brent not disambiguated in weekly_panel |
| FLAG-01 | FLAG | Schema | No CHECK constraint on `series_id` values |
| FLAG-02 | FLAG | Idempotency | weekly_panel recomputation strategy not explicit |
| FLAG-03 | FLAG | Manifest | Missing `url_or_path` column for download provenance |
| FLAG-04 | FLAG | Manifest | `status` enum lifecycle ambiguous |
| FLAG-05 | FLAG | Derivation | US CPI surprise needs BLS release calendar table |
| FLAG-06 | FLAG | Derivation | AR(1) warmup/estimation strategy unspecified |
| FLAG-07 | FLAG | Missing column | No `cpi_surprise_ar1` column for AR(1) fallback |
| FLAG-08 | FLAG | Missing column | Standardization boundary (pipeline vs estimation) undocumented |
| FLAG-09 | FLAG | DuckDB | PK enforcement requires duckdb >= 1.2.0; note needed |
| NIT-01 | NIT | Schema | `dane_release_calendar` could use UNIQUE on (release_date, series) |
| NIT-02 | NIT | Design | Long format for fred_daily confirmed correct |
| NIT-03 | NIT | Derivation | VIX averaging choice should be documented as deliberate |
| NIT-04 | NIT | Missing column | `is_release_week` should split into CPI/PPI booleans |
| NIT-05 | NIT | Missing column | No day-count columns for VIX/oil quality tracking |
| NIT-06 | NIT | DuckDB | DOUBLE vs DECIMAL tradeoff acceptable for research pipeline |
| NIT-07 | NIT | DuckDB | No schema namespace needed for single-purpose DB |

---

## Verdict: NEEDS WORK

5 BLOCKs prevent safe implementation. The spec is well-structured and the acquisition priority ordering is excellent (risk-first is exactly right). The long-format choice, manifest concept, and separation from ran_accumulator.duckdb are all sound decisions.

However, the derivation section (Section 4.1) has multiple ambiguities that would cause bugs in implementation: cross-week price lookups, holiday handling, and the oil series disambiguation. The idempotency story (BLOCK-02) is the most critical gap — without explicit upsert semantics, the pipeline will fail or corrupt on second run.

**Recommended fix order:**
1. BLOCK-02 (upsert strategy) — foundational; affects every table
2. BLOCK-03 + BLOCK-04 (return computation) — affects the primary LHS variable
3. BLOCK-05 (oil disambiguation) — simple decision, big downstream impact
4. BLOCK-01 (manifest PK) — quick fix
5. FLAGs in priority order: FLAG-05 (BLS calendar) > FLAG-07 (AR(1) column) > FLAG-02 (recomputation) > rest
