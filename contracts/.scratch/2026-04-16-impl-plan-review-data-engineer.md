# Data Engineer Review: Structural Econometrics Data Pipeline Implementation Plan

**Reviewer:** Data Engineer Agent
**Date:** 2026-04-16
**Plan:** `contracts/docs/superpowers/plans/2026-04-16-structural-econ-data-pipeline.md`
**Spec:** `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md` (Rev 4)

---

## 1. DDL Correctness (Plan Task 1 vs Spec sections 3.1-3.11)

**PASS** — `banrep_trm_daily` (spec 3.1): columns `date DATE PRIMARY KEY`, `trm DOUBLE NOT NULL`, `_ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp`. All match.

**PASS** — `fred_daily` (spec 3.2): composite PK `(series_id, date)`, CHECK constraint on series_id for `VIXCLS`, `DCOILWTICO`, `DCOILBRENTEU`, `value DOUBLE` nullable. All match.

**PASS** — `fred_monthly` (spec 3.3): composite PK `(series_id, date)`, CHECK `('CPIAUCSL')`, `value DOUBLE` nullable. All match.

**PASS** — `dane_ipc_monthly` (spec 3.4): `date DATE PRIMARY KEY`, `ipc_index DOUBLE`, `ipc_pct_change DOUBLE`, `_ingested_at`. All match.

**PASS** — `dane_ipp_monthly` (spec 3.5): `date DATE PRIMARY KEY`, `ipp_index DOUBLE`, `ipp_pct_change DOUBLE`, `_ingested_at`. All match.

**PASS** — `dane_release_calendar` (spec 3.6): PK `(year, month, series)`, UNIQUE `(release_date, series)`, CHECK on series, imputed BOOLEAN. All match.

**PASS** — `bls_release_calendar` (spec 3.7): PK `(year, month)`, UNIQUE `(release_date)`. All match.

**PASS** — `download_manifest` (spec 3.8): PK `(source, downloaded_at)`, all 9 columns present. All match.

**PASS** — `banrep_ibr_daily` (spec 3.10): `date DATE PRIMARY KEY`, `ibr_overnight_er DOUBLE NOT NULL`, `_ingested_at`. All match.

**PASS** — `banrep_intervention_daily` (spec 3.11): `date DATE PRIMARY KEY`, 8 intervention DOUBLE columns (nullable), `_ingested_at`. All match.

**FLAG F1 — `fred_daily` and `fred_monthly` missing `_ingested_at`:** The spec does not explicitly require `_ingested_at` on FRED tables (only banrep_trm_daily, dane_ipc_monthly, dane_ipp_monthly, banrep_ibr_daily, banrep_intervention_daily have it in the spec). The plan correctly omits it from FRED tables, matching the spec. However, spec section 3.1 says `_ingested_at` tracks "when this value was last written" for `INSERT OR REPLACE`. FRED tables also use `INSERT OR REPLACE` per section 3.9. The asymmetry is a spec-level concern, not a plan defect. No action needed in the plan, but flagging for awareness.

---

## 2. Pipeline Idempotency

**PASS** — Raw tables use `CREATE TABLE IF NOT EXISTS` (idempotent schema creation) and test `INSERT OR REPLACE` for data upsert. The `init_db` function is tested for idempotency (calling twice does not error).

**PASS** — `download_manifest` is correctly `INSERT`-only (append), not `INSERT OR REPLACE`. The test `test_download_manifest_append_only` explicitly verifies multiple rows for the same source coexist.

**PASS** — Derived panels use `CREATE OR REPLACE TABLE ... AS (SELECT ...)` in `build_weekly_panel` and `build_daily_panel`. This is atomic in DuckDB.

**FLAG F2 — `INSERT OR REPLACE` on `download_manifest` PK could silently succeed within same microsecond:** The manifest PK is `(source, downloaded_at)`. The `log_manifest` function uses `datetime.now()` for `downloaded_at`. If two calls happen within the same microsecond (unlikely but possible in fast loops or tests), the second INSERT would violate the PK. The plan uses plain `INSERT` (correct per spec), and the microsecond precision makes collisions vanishingly rare in practice. No fix needed, but the plan should document this assumption. Currently it does not.

---

## 3. DuckDB SQL in Panel Builders (Task 5)

**BLOCK B1 — `dane_ipc_release` CTE uses invalid DuckDB syntax:** The CTE at lines ~1383-1385 of the plan contains:

```sql
JOIN dane_ipc_monthly dim ON dim.date = make_date(dr.week_start.year()::INT,
    CASE WHEN (SELECT month FROM dane_release_calendar WHERE release_date = dr.release_date AND series = 'ipc' LIMIT 1) IS NOT NULL
    THEN (SELECT month FROM dane_release_calendar WHERE release_date = dr.release_date AND series = 'ipc' LIMIT 1) ELSE 1 END, 1)
```

This has multiple problems:
1. `dr.week_start.year()` is not valid DuckDB SQL. DuckDB uses `EXTRACT(YEAR FROM dr.week_start)` or `YEAR(dr.week_start)`.
2. The correlated subquery inside the JOIN condition is unnecessarily complex and may be slow.
3. The CTE is never actually referenced in the final SELECT. The final query hardcodes `0.0 AS dane_ipc_pct` and `0.0 AS cpi_surprise_ar1`. So this CTE is dead code within the SQL but still must parse and execute. If it fails to parse, the entire `CREATE OR REPLACE TABLE` statement fails.

The intent (Task 6 note says "AR(1) surprise columns initialized to 0.0, Task 6 adds post-processing") means the dead CTE should be **removed entirely** from the SQL. It serves no purpose and introduces a parse-time failure.

**BLOCK B2 — `LAST(value ORDER BY date)` syntax in VIX/oil CTEs:** DuckDB 1.5.1 does support `LAST(value ORDER BY date)` as an ordered aggregate, but only since DuckDB 0.10+. This should work in 1.5.1, but the syntax is uncommonly tested. The safer DuckDB equivalent is:

```sql
(ARRAY_AGG(value ORDER BY date DESC))[1]
```

or a window-function approach. Since DuckDB 1.5.1 does support `LAST(... ORDER BY ...)`, this is a **NIT**, not a block. But if the plan is ever run against DuckDB < 0.10, it will fail silently.

**FLAG F3 — `COALESCE(crw.week_start IS NOT NULL, FALSE)` is a type-confusion anti-pattern:** `crw.week_start IS NOT NULL` already returns BOOLEAN (never NULL). Wrapping it in `COALESCE(..., FALSE)` is unnecessary. DuckDB accepts this, but it signals potential confusion about NULL semantics. In the LEFT JOIN case, when `crw.week_start` is NULL (no match), `crw.week_start IS NOT NULL` correctly returns FALSE without COALESCE. Same issue applies to `prw.week_start IS NOT NULL` and both `COALESCE(cd.date IS NOT NULL, FALSE)` / `COALESCE(pd.date IS NOT NULL, FALSE)` in the daily panel SQL. Not a correctness bug, but misleading.

**FLAG F4 — Weekly panel oil_return uses prior-week close, but first week will be NULL:** The `oil_with_return` CTE uses `LAG(last_oil_price) OVER (ORDER BY week_start)`. The first week in the sample will have `oil_return = NULL`. The final SELECT uses `COALESCE(o.oil_return, 0.0)`, which maps this NULL to 0.0. This means the first week reports `oil_return = 0.0`, which is wrong (it should be NULL or the week should be dropped). The test `test_weekly_panel_oil_return` seeds oil data for a "prior Friday" (2024-01-05) and expects `oil_return = log(74.0/72.0)`, which works because the oil_weekly CTE includes the prior-week data. But this only works because `sample_start=date(2024, 1, 8)` and the oil data starts at 2024-01-05 (which falls in the week starting 2024-01-01). The `oil_weekly` CTE filters `date >= sample_start`, which is 2024-01-08 -- but 2024-01-05 is BEFORE sample_start. So `oil_weekly` will NOT include the 2024-01-05 row. This means the first week's oil_return in the test will actually be NULL (no prior week in the CTE), coalesced to 0.0. **The test `test_weekly_panel_oil_return` will fail.**

The fix: the `oil_weekly` CTE's filter should include a lookback window (e.g., `date >= sample_start - INTERVAL 7 DAY`) to capture the prior week's last oil price. Alternatively, remove the date filter from the oil CTE entirely (let it read all raw data) and only filter the final output.

**FLAG F5 — `trm_returns` CTE filters `date >= sample_start` but LAG needs the prior row:** The first row at `sample_start` will have `LAG(trm) = NULL` because there is no prior row in the filtered set. The `trm_weekly` CTE then filters out `WHERE log_return IS NOT NULL`, which drops this first date. But the return for the first date AFTER `sample_start` that has a prior trading day BEFORE `sample_start` is also lost. For example, if `sample_start = 2024-01-08` (Monday), the LAG for 2024-01-08 would need the Friday 2024-01-05 TRM, but it is excluded by the filter. The test seeds 2024-01-05 data and expects 5 trading days in the first week, implying the Monday return uses Friday's price. But the CTE filter excludes Friday. The test likely passes with `n_trading_days = 4` (Tue-Fri returns only), not 5. **This is either a test expectation bug or a CTE filter bug.**

The fix: include a lookback in the filter, e.g., `WHERE date >= (sample_start - INTERVAL 7 DAY)`, and then filter the final output to `week_start >= sample_start`.

---

## 4. Data Type Casting

**PASS** — Socrata `valor` string to DOUBLE: `float(valor_str)` in `parse_trm_socrata_response`. Correct.

**PASS** — Socrata date parsing: `datetime.fromisoformat(fecha_str.replace(".000", "")).date()`. This works for `"2026-04-16T00:00:00.000"` format. The `.replace(".000", "")` strips the millisecond suffix before `fromisoformat`. Correct for the documented format.

**NIT N1 — Socrata date parsing fragility:** If Socrata ever returns microseconds (`.000000`), the `.replace(".000", "")` would produce `"2026-04-16T00:00:00"` (correct by accident -- removes the first `.000`). But if the timestamp is `"2026-04-16T12:30:45.123"`, `.replace(".000", "")` would not match and the milliseconds would cause `fromisoformat` to still work (Python 3.11+ handles fractional seconds in `fromisoformat`). So this is not a bug, but the replacement is unnecessary given Python 3.13's `fromisoformat` handles the `.000` suffix natively. Minor cleanup opportunity.

**PASS** — FRED `"."` to NULL: `value = None if value_str.strip() == "." else float(value_str)`. Correct.

**PASS** — SDMX XML date parsing: `datetime.strptime(date_str, "%Y%m%d").date()`. The spec says TIME_PERIOD format is YYYYMMDD. Correct.

**FLAG F6 — Intervention JSON date parsing assumes YYYY/MM/DD:** `datetime.strptime(date_str, "%Y/%m/%d").date()`. The spec (section 3.11) says "parse date from YYYY/MM/DD format." The plan matches. However, there is no validation that the cached JSON actually uses this format. The test `test_load_intervention_from_json` uses the real cached file, which provides an integration check. Acceptable.

**PASS** — Intervention amount parsing: `_parse_amount(s)` strips whitespace and returns `None` for empty strings. Matches spec: "empty string -> NULL."

---

## 5. Missing Tasks / Coverage

Checking all 10 raw tables + 2 derived tables + manifest + validation from the spec:

| Spec Item | Plan Task | Status |
|---|---|---|
| banrep_trm_daily (3.1) | Task 1 (DDL) + Task 2 (fetch) | COVERED |
| fred_daily (3.2) | Task 1 (DDL) + Task 3 (fetch) | COVERED |
| fred_monthly (3.3) | Task 1 (DDL) + Task 3 (fetch) | COVERED |
| dane_ipc_monthly (3.4) | Task 1 (DDL) + Task 4 (parse) | COVERED |
| dane_ipp_monthly (3.5) | Task 1 (DDL) + Task 4 (parse) | COVERED |
| dane_release_calendar (3.6) | Task 1 (DDL) + Task 4 (parse) | COVERED |
| bls_release_calendar (3.7) | Task 1 (DDL) + Task 3 (fetch) | COVERED |
| download_manifest (3.8) | Task 1 (DDL) + Task 7 (log) | COVERED |
| banrep_ibr_daily (3.10) | Task 1 (DDL) + Task 2 (fetch) | COVERED |
| banrep_intervention_daily (3.11) | Task 1 (DDL) + Task 2 (load) | COVERED |
| weekly_panel (4.1) | Task 5 (build) + Task 6 (AR1) | COVERED |
| daily_panel (4.2) | Task 5 (build) + Task 6 (AR1) | COVERED |
| Validation (5 step 6) | Task 8 | COVERED |

**FLAG F7 — `dane_ipp_monthly` has no parser test with real CSV structure:** Task 4 defines `parse_dane_ipp_csv` in the implementation but the test file only tests `parse_dane_ipc_csv` and `parse_dane_release_calendar_csv`. There is no test for `parse_dane_ipp_csv`. The `DaneIppRow` dataclass is defined but never tested. The implementation of `parse_dane_ipp_csv` is present in the plan code but untested, violating the plan's own TDD rule (Rule 1).

**FLAG F8 — No IBR SDMX parsing test:** Task 2 test file (`test_econ_banrep.py`) includes tests for TRM and intervention but no test for `parse_ibr_sdmx_xml`. The function is defined in the implementation and imported in the test file header, but no test exercises it. Given that SDMX XML parsing is the most fragile part of the pipeline (namespace handling, dimension filtering), this is a significant gap.

**FLAG F9 — US CPI surprise construction is not implemented:** The spec section 4.1 requires `us_cpi_surprise` to be populated with AR(1) residuals of CPIAUCSL MoM % changes, mapped to BLS release weeks via `bls_release_calendar`. Task 6 (`compute_ar1_surprises`) only implements the DANE IPC surprise. The `us_cpi_surprise` column remains hardcoded to 0.0 in the weekly panel SQL and is never updated. The plan's self-review checklist at the bottom does not mention this gap. This is spec-required (section 4.1: "US CPI surprise construction: AR(1) on monthly CPIAUCSL MoM % changes").

**FLAG F10 — `banrep_rate_surprise` construction is not implemented:** The spec section 4.1 says `banrep_rate_surprise` should be "change in IBR overnight around BanRep board meeting." However, spec section 3.10 also says "The meeting calendar is NOT defined in this spec -- it is an estimation-module input." And section 7 lists it as "not covered." The plan hardcodes `banrep_rate_surprise = 0.0`, which is consistent with the spec's deferral. No action needed. But the plan should explicitly note this deferral (currently it is only mentioned in Task 5's note about AR(1) columns being initialized to 0.0).

**FLAG F11 — `dane_ipp_pct` is never populated in weekly_panel:** The spec requires `dane_ipp_pct` to be "IPP MoM % change on release week; 0.0 on non-release weeks." Task 6 (`compute_ar1_surprises`) only populates `dane_ipc_pct` (CPI), not `dane_ipp_pct` (PPI). The IPP release-week mapping and value population is missing from the plan entirely.

**FLAG F12 — No full pipeline orchestration function:** Task 7 only implements `log_manifest` and `compute_sha256`. The plan describes an orchestrator (`econ_pipeline.py`) that coordinates "download all -> build panels -> validate" but never provides the actual orchestration function (e.g., `run_pipeline()`). The file structure table says `econ_pipeline.py` handles "Orchestrate: download all -> build panels -> validate" but the implementation only covers manifest logging and validation. The actual download-and-insert logic for each source (calling `fetch_trm`, inserting rows, calling `log_manifest`) is never written in any task.

---

## 6. Task Ordering and Dependencies

**PASS** — Task 1 (schema) has no dependencies. Correct as first task.

**PASS** — Tasks 2, 3, 4 (fetchers/loaders) depend on Task 1 (import `init_db`). Correct ordering.

**PASS** — Task 5 (panels) depends on Tasks 1-4 (needs raw tables populated for testing). Correct ordering.

**PASS** — Task 6 (AR1) depends on Task 5 (needs `build_weekly_panel` and `build_daily_panel`). Correct ordering.

**PASS** — Task 7 (pipeline) depends on Task 1 (schema). Independent of Tasks 2-6 for its own tests. Correct.

**PASS** — Task 8 (validation) depends on Task 5 (imports `build_weekly_panel`). Correct ordering.

**FLAG F13 — Task 8 test imports from Task 5 test file:** `test_econ_pipeline.py` imports `_seed_trm` and `_seed_fred` from `scripts.tests.test_econ_panels`. This creates a cross-test-file dependency. While functional, it means Task 8 tests cannot run without Task 5 test file being present. This is acceptable for this project's structure but worth noting.

**NIT N2 — Task 8 test file imports `pytest` but the import is not shown:** The test `test_validate_weekly_panel_catches_null_surprise` uses `pytest.raises` but the appended code block does not show the `import pytest` statement. The original Task 7 test file header also does not show `import pytest`. The implementation agent would need to add this import.

---

## Summary of Issues

| ID | Severity | Description |
|---|---|---|
| B1 | BLOCK | `dane_ipc_release` CTE has invalid DuckDB syntax (`week_start.year()`) and is dead code -- should be removed |
| B2 | NIT | `LAST(value ORDER BY date)` works in DuckDB 1.5.1 but is uncommonly tested |
| F1 | FLAG | `_ingested_at` asymmetry between BanRep/DANE tables and FRED tables (spec-level, not plan defect) |
| F2 | FLAG | Manifest PK microsecond collision risk undocumented |
| F3 | FLAG | `COALESCE(x IS NOT NULL, FALSE)` is unnecessary; `x IS NOT NULL` suffices |
| F4 | FLAG | oil_return first week coalesced to 0.0 instead of NULL; oil CTE date filter excludes prior-week data needed for LAG |
| F5 | FLAG | trm_returns CTE filter excludes prior trading day needed for first-day LAG; `n_trading_days` test expectation may be wrong |
| F6 | FLAG | Intervention JSON date format assumption relies on integration test (acceptable) |
| F7 | FLAG | `parse_dane_ipp_csv` defined but never tested (TDD violation) |
| F8 | FLAG | `parse_ibr_sdmx_xml` defined but never tested (TDD violation; most fragile parser) |
| F9 | FLAG | `us_cpi_surprise` remains 0.0 -- AR(1) on CPIAUCSL never implemented despite spec requirement |
| F10 | FLAG | `banrep_rate_surprise` deferral is consistent with spec but not explicitly noted in plan |
| F11 | FLAG | `dane_ipp_pct` never populated in weekly_panel (spec requires release-week value) |
| F12 | FLAG | No actual pipeline orchestration function (`run_pipeline`) -- only manifest + validation helpers |
| F13 | FLAG | Cross-test-file import dependency (Task 8 imports from Task 5 test helpers) |
| N1 | NIT | Socrata date `.replace(".000", "")` is unnecessary on Python 3.13 |
| N2 | NIT | Missing `import pytest` in Task 8 appended test code |

---

## Verdict: NEEDS WORK

The plan has **1 BLOCK** (invalid SQL in the weekly panel CTE that will cause a runtime parse error) and **4 substantive FLAGS** that represent missing functionality required by the spec (F7/F8: untested parsers violating TDD; F9/F11: two spec-required derived columns never populated; F12: no orchestration function). The DDL is correct and the idempotency pattern is sound, but the panel-building SQL and the AR(1) construction have gaps that must be addressed before implementation can proceed.

### Required fixes before implementation:

1. **B1:** Remove the dead `dane_ipc_release` CTE from the weekly panel SQL. It has invalid syntax and is never referenced.
2. **F4 + F5:** Add a lookback window to the `trm_returns` and `oil_weekly` CTEs (e.g., `date >= sample_start - INTERVAL 7 DAY`) so LAG can access prior-period data. Filter the final output to `week_start >= sample_start`.
3. **F7 + F8:** Add tests for `parse_dane_ipp_csv` and `parse_ibr_sdmx_xml`. The IBR test should use a sample SDMX XML fragment with the correct namespace structure.
4. **F9:** Add US CPI AR(1) surprise construction in Task 6 (same expanding-window method applied to CPIAUCSL, mapped via `bls_release_calendar`).
5. **F11:** Add `dane_ipp_pct` population logic -- map IPP releases to weeks via `dane_release_calendar` and populate with `ipp_pct_change`.
6. **F12:** Add a `run_pipeline(conn, ...)` function in Task 7 that orchestrates the full flow: init_db -> fetch/load all sources -> insert -> build panels -> compute AR(1) -> validate.
