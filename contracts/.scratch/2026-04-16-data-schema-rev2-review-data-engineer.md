# Data Schema & Acquisition Strategy Rev 2 Review -- Data Engineer

**Date:** 2026-04-16
**Spec reviewed:** `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md` (Rev 2)
**Upstream reference:** `contracts/notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)
**Reviewer role:** Data Engineer (schema normalization, pipeline idempotency, DuckDB specifics)
**Prior review:** Rev 1 raised 5 BLOCKs + 9 FLAGs + 7 NITs. Verdict was NEEDS WORK.

---

## Rev 1 Resolution Audit

All 5 original BLOCKs have been addressed:

- **B1 (DEXCOUS nonexistent):** Resolved. `banrep_trm_daily` replaces the phantom FRED series. TRM is the correct Colombian source. STOP condition documented.
- **B2 (No daily panel for GARCH-X):** Resolved. `daily_panel` (Section 4.2) added with correct release-date-level surprise placement.
- **B3 (No upsert strategy):** Resolved. Section 3.9 specifies `INSERT OR REPLACE` for raw tables, `CREATE OR REPLACE TABLE AS (...)` for derived tables.
- **B4 (Cross-week log-return):** Resolved. RV computation now explicitly states "last available prior price regardless of week boundary." Multi-day gaps accepted per Andersen et al. 2003.
- **B5 (Oil series ambiguity):** Resolved. WTI is primary; Brent in `fred_daily` for ad-hoc only. "Last available trading day" replaces "Friday close."
- **B6 (Manifest no PK):** Resolved. Composite PK `(source, downloaded_at)` added. Status lifecycle documented.

All consensus FLAGs also addressed: BLS release calendar table added (F-BLS), NULL vs 0 semantics explicit (F-NULL), CPI/PPI release booleans split (F-CPI/PPI), VIX Friday close added (F-VIX), AR(1) column added as core (F-AR1), row count corrected (F-rowcount), FRED missing-value rule explicit (F-FRED-missing), standardization boundary documented (F-standardization), holiday mismatch documented (F-holidays), DANE pre-2010 imputation strategy noted (F-DANE-gaps), TRM promoted to Priority 1 top (F-risk-reorder).

---

## New Issues in Rev 2

### BLOCK-01: `banrep_trm_daily` lacks source metadata columns required by pipeline pattern

Every other raw table either inherits metadata through the long-format `series_id` discriminator (fred_daily, fred_monthly) or is manually compiled with provenance flags (dane_release_calendar.imputed). The `banrep_trm_daily` table has only `(date, trm)`. Since BanRep's data delivery mechanism is unverified (could be API, CSV, Excel, web scrape), there is no way to distinguish:

- TRM values from the initial bulk download vs. incremental appends
- TRM values that were revised by BanRep (TRM occasionally has T+1 corrections)

Without at least an `_ingested_at TIMESTAMP DEFAULT current_timestamp` column, the `INSERT OR REPLACE` strategy silently overwrites without audit trail. The `download_manifest` captures batch-level metadata but not row-level provenance.

**Impact:** If BanRep revises a historical TRM value and the pipeline re-downloads, the old value disappears with no trace. For the LHS variable of the entire model, this is a data lineage gap.

**Fix:** Add `_ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp` to `banrep_trm_daily`. On `INSERT OR REPLACE`, the timestamp updates to the latest ingestion. Combined with the manifest's `sha256`, this provides sufficient row-level + batch-level audit for a research pipeline. Same column should be added to `dane_ipc_monthly` and `dane_ipp_monthly` for consistency.

### BLOCK-02: `daily_panel` missing BanRep rate and oil-level controls needed by GARCH-X sensitivity specs

The upstream spec Section 6.2, A8 adds `log(P_t^oil)` as a regressor. The weekly_panel correctly includes `oil_log_level`. But the `daily_panel` has `oil_return` (daily) and no `oil_log_level` column. If the GARCH-X estimation module needs to run sensitivity A8 on daily data, it must recompute from `fred_daily` directly, breaking the "panels are estimation-ready" contract.

More critically, the upstream spec Section 4.1 primary equation includes `gamma_2 * s_t^BanRep` and `gamma_3 * VIX_t` as controls. The GARCH-X variance equation (A7 in Section 6.2) can incorporate exogenous regressors beyond just `|s_t^CPI|`. The daily_panel has `vix` (good) but no `banrep_rate_surprise` placeholder even in the deferred section.

**Fix:** Add `oil_log_level DOUBLE` to `daily_panel` (log of WTI daily price; NULL on non-trading days). Add `banrep_rate_surprise` to the daily_panel deferred columns list, same as it appears in weekly_panel's deferred section. This keeps the two panels symmetric in their coverage of the upstream spec's variable set.

### FLAG-01: `INSERT OR REPLACE` on `download_manifest` conflicts with append-only audit semantics

Section 3.9 states: "All raw tables use `INSERT OR REPLACE` on conflict with the primary key." The `download_manifest` has PK `(source, downloaded_at)` and is described as "append-only audit trail" (Section 3.8). These two statements are in tension:

- If the pipeline is re-run within the same second for the same source (unlikely but possible in automated testing or fast-retry scenarios), `INSERT OR REPLACE` would overwrite the previous manifest row instead of appending.
- More practically, the blanket rule "all raw tables use INSERT OR REPLACE" could lead an implementer to apply it to manifest without thinking about the append-only intent.

**Fix:** Carve out `download_manifest` from the `INSERT OR REPLACE` rule. Manifest should use plain `INSERT` (append-only). If a PK collision occurs (same source, same second), either (a) add millisecond precision to `downloaded_at` (DuckDB TIMESTAMP has microsecond precision by default, so this is already handled if the Python code uses `datetime.now()` rather than truncating to seconds), or (b) accept the collision as a degenerate edge case. The key point is: the spec should state "INSERT OR REPLACE for all raw tables EXCEPT download_manifest, which is INSERT-only (append)."

### FLAG-02: `fred_daily` CHECK constraint still references DEXCOUS

Section 3.2 defines: `CHECK (series_id IN ('VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU'))`. The Rev 2 changelog says "FRED `fred_daily` CHECK constraint updated." This is correct -- DEXCOUS is removed. However, the Rev 1 review text (which will be read by implementers alongside the spec) still shows `CHECK (series_id IN ('DEXCOUS', 'VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU'))` in FLAG-01. This is a review-document artifact, not a spec issue, but worth noting: the spec itself is correct; the old review text should not be treated as current.

No spec change needed. Noting for completeness.

### FLAG-03: `bls_release_calendar` has no UNIQUE constraint on `release_date`

The BLS publishes one CPI release per month, so `release_date` should be unique. The PK is `(year, month)` which prevents duplicate reference months, but nothing prevents two rows pointing to the same release_date (e.g., a data-entry error mapping both January and February to the same date). A `UNIQUE(release_date)` constraint would catch this.

Contrast with `dane_release_calendar` which correctly has `UNIQUE(release_date, series)` -- the BLS table should have analogous protection.

**Fix:** Add `UNIQUE(release_date)` to `bls_release_calendar`.

### FLAG-04: First-week drop for `daily_panel` not documented

Section 4.1 (weekly_panel) correctly states: "The first week in the sample has no prior price for its first return; it is dropped from the panel." But Section 4.2 (daily_panel) has no equivalent statement. The daily_panel's first row would have `cop_usd_return = NULL` (no prior TRM to compute log-return from). The spec should state whether this row is dropped or retained with NULL.

For GARCH-X MLE estimation, the first observation is typically dropped or handled via the unconditional variance initialization. The pipeline should either:
- Drop the first row (matching weekly_panel behavior), or
- Retain it with `cop_usd_return = NULL` and let the estimation module handle it.

**Fix:** Add a sentence to Section 4.2: "The first trading day in the sample has no prior TRM for return computation; `cop_usd_return` is NULL. The estimation module drops this row during GARCH initialization." This is the cleaner boundary -- the pipeline preserves data, estimation handles sample selection.

### FLAG-05: No explicit date-range filter for derived panels

The weekly_panel is described as "~2003-2025" but the raw tables may contain data outside this range (FRED series start as early as 1990s; BanRep TRM potentially from 1991). The derivation does not specify a WHERE clause on dates. If TRM data from 1991 is loaded, the weekly_panel would include ~600 extra weeks from 1991-2002 with no DANE release data, no BanRep EME data, and unreliable pre-2003 Colombian macro data.

The AR(1) warmup period (first 12 months of DANE IPC) provides an implicit lower bound (~2003 if IPC starts 2002), but this is indirect. The spec should define an explicit sample start date for derived panels.

**Fix:** Add a configuration parameter or explicit WHERE clause: "weekly_panel and daily_panel include observations starting from the first Monday after 12 months of DANE IPC data are available (approximately 2003-01), ensuring AR(1) warmup is complete." This makes the derivation deterministic regardless of how much raw data is loaded.

### FLAG-06: `dane_ipc_monthly` and `dane_ipp_monthly` store both index level and percent change -- potential consistency risk

Both tables store `ipc_index` + `ipc_pct_change` (and similarly for IPP). If DANE publishes a revised index level but the pipeline re-downloads only the index and recomputes `pct_change` differently from DANE's published value (or vice versa), the two columns diverge silently.

The spec does not state whether `pct_change` is (a) taken directly from DANE's publication, or (b) computed by the pipeline as `(index_t / index_{t-1} - 1) * 100`. These can differ due to DANE's rounding or base-period adjustments.

**Fix:** Add a note: "`ipc_pct_change` is stored as published by DANE, NOT recomputed from `ipc_index`. If DANE does not publish percent change directly, compute as `(ipc_index / lag(ipc_index) - 1) * 100` and document this in the manifest notes." Same for IPP.

### NIT-01: `daily_panel` could benefit from a `week_start` column for join efficiency

The weekly_panel is keyed on `week_start`. If any downstream analysis needs to join daily and weekly panels (e.g., attaching weekly controls to daily observations for hybrid models), a `week_start DATE` column on `daily_panel` computed as `date_trunc('week', date)` (DuckDB returns the Monday) would make this trivial. Without it, the join requires a range predicate (`daily.date >= weekly.week_start AND daily.date < weekly.week_start + INTERVAL 7 DAY`), which is correct but less readable.

**Fix:** Add `week_start DATE` as a computed column: `date_trunc('week', date)::DATE`. Low cost, high convenience.

### NIT-02: `n_trading_days` semantics under Colombian holidays

Section 4.1 states `n_trading_days` counts COP/USD trading days only. A Colombian holiday week (e.g., Semana Santa can remove 2 days) might have `n_trading_days = 3`, meaning RV is computed from only 2-3 returns. The upstream spec does not scale RV by trading days (no annualization or day-count adjustment), which is standard for event-study RV. But weeks with very few returns (n=1 or n=2) produce noisy RV estimates.

The spec should document whether weeks with `n_trading_days < 3` (i.e., fewer than 2 returns) are retained or filtered. This is an estimation decision, but the pipeline should at minimum flag them.

**Fix:** No schema change needed, but add a note in Section 4.1: "Weeks with `n_trading_days <= 1` (zero or one return) have undefined or degenerate RV (sum of zero or one squared return). These weeks are retained in the panel for completeness; the estimation module should filter or flag them."

### NIT-03: No version or schema-migration tracking

The spec is at Rev 2 and may evolve further. If the DuckDB file is created under Rev 2's schema and later Rev 3 adds a column, there is no migration path -- the implementer must know to rebuild. For a research pipeline with ~1,100 weekly rows, full rebuild is cheap. But a `_schema_version` metadata table (single row: `version INTEGER, created_at TIMESTAMP`) would let the pipeline detect stale schemas and trigger automatic rebuild.

**Fix:** Optional. Add a `_meta` table with `schema_version INTEGER` and `created_at TIMESTAMP`. The pipeline checks `schema_version` on startup; if it does not match the code's expected version, it drops and recreates all tables. Cheap insurance for a fast-moving spec.

---

## Cross-Check: Upstream Spec Variables vs Schema Coverage

Systematic verification of every variable in the upstream spec (Section 4.3 table) against the data schema:

| Upstream variable | Schema location | Status |
|---|---|---|
| RV_t (realized vol) | weekly_panel.rv | Covered |
| RV_t^{1/3} (cube-root) | weekly_panel.rv_cuberoot | Covered |
| log(RV_t) | weekly_panel.rv_log | Covered |
| s_t^CPI (survey surprise) | weekly_panel.cpi_surprise_survey (deferred) | Covered (deferred) |
| s_t^CPI AR(1) fallback | weekly_panel.cpi_surprise_ar1 | Covered |
| Delta IPP_t (PPI change) | weekly_panel.dane_ipp_pct | Covered |
| s_t^{US CPI} | weekly_panel.us_cpi_surprise | Covered |
| s_t^{BanRep} | weekly_panel.banrep_rate_surprise (deferred) | Covered (deferred) |
| VIX_t | weekly_panel.vix_avg + vix_friday_close | Covered |
| I_t (intervention) | weekly_panel.intervention_dummy (deferred) | Covered (deferred) |
| r_t^{oil} | weekly_panel.oil_return | Covered |
| log(P_t^oil) (A8) | weekly_panel.oil_log_level | Covered |
| Daily COP/USD return (GARCH) | daily_panel.cop_usd_return | Covered |
| |s_t^CPI| daily (GARCH) | daily_panel.abs_cpi_surprise | Covered |
| Daily VIX (GARCH) | daily_panel.vix | Covered |
| Daily oil return (GARCH) | daily_panel.oil_return | Covered |
| Daily oil log-level (GARCH A8) | daily_panel -- **MISSING** | See BLOCK-02 |
| is_cpi_release_week | weekly_panel.is_cpi_release_week | Covered |
| is_ppi_release_week | weekly_panel.is_ppi_release_week | Covered |
| is_cpi_release_day | daily_panel.is_cpi_release_day | Covered |
| is_ppi_release_day | daily_panel.is_ppi_release_day | Covered |
| Lagged RV (A5) | Computable from weekly_panel | Covered (estimation computes lag) |
| Asymmetric s+ / s- (A9) | Computable from cpi_surprise_ar1 | Covered (estimation splits) |

Coverage is complete except for `oil_log_level` on daily_panel (BLOCK-02).

---

## Issue Summary

| # | Severity | Category | Description |
|---|---|---|---|
| BLOCK-01 | BLOCK | Schema | `banrep_trm_daily` lacks `_ingested_at` audit column for LHS variable provenance |
| BLOCK-02 | BLOCK | Missing column | `daily_panel` missing `oil_log_level` for GARCH-X sensitivity A8 |
| FLAG-01 | FLAG | Idempotency | `INSERT OR REPLACE` applied to `download_manifest` contradicts append-only semantics |
| FLAG-02 | FLAG | Schema | Rev 1 review text has stale DEXCOUS in CHECK example (spec itself is correct) |
| FLAG-03 | FLAG | Schema | `bls_release_calendar` missing UNIQUE(release_date) constraint |
| FLAG-04 | FLAG | Derivation | First-row handling in `daily_panel` not documented (NULL return) |
| FLAG-05 | FLAG | Derivation | No explicit date-range filter for derived panels; raw data may extend to 1991 |
| FLAG-06 | FLAG | Data quality | `ipc_pct_change` / `ipp_pct_change` source ambiguity (DANE-published vs recomputed) |
| NIT-01 | NIT | Schema | `daily_panel` could use `week_start` column for join convenience |
| NIT-02 | NIT | Derivation | Degenerate weeks (n_trading_days <= 1) handling not documented |
| NIT-03 | NIT | Operations | No schema-version metadata table for migration detection |

---

## Verdict: PASS WITH FLAGS

Rev 2 resolves all 5 original BLOCKs and all consensus FLAGs from the 3-way review. The spec is now implementable. The BanRep TRM pivot (B1) is the most significant structural improvement -- correctly identifying that FRED has no daily COP/USD and establishing TRM as the canonical source with a hard STOP condition.

The 2 new BLOCKs are straightforward fixes:
- BLOCK-01 (ingested_at column) is a single column addition to 3 tables -- 5 minutes of spec work.
- BLOCK-02 (daily oil_log_level) is a single column addition to the daily_panel derivation.

Neither BLOCK requires architectural changes. The pipeline design, idempotency strategy, manifest audit trail, and raw-to-derived computation logic are all sound. The risk-first acquisition ordering, the NULL-vs-0 semantics, and the standardization boundary decision are particularly well-reasoned.

**Recommended fix order:**
1. BLOCK-01 (ingested_at) -- affects data lineage for the most critical table
2. BLOCK-02 (daily oil_log_level) -- single column, keeps daily/weekly panels symmetric
3. FLAG-01 (manifest INSERT-only) -- one sentence clarification
4. FLAG-03 through FLAG-06 -- minor constraint and documentation additions

After these fixes, the spec is ready for implementation.
