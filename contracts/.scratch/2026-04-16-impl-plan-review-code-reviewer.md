# Code Reviewer: Structural Econometrics Data Pipeline Implementation Plan

**Reviewed:** `contracts/docs/superpowers/plans/2026-04-16-structural-econ-data-pipeline.md`
**Against spec:** `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md` (Rev 4)
**Style references:** `ran_utils.py`, `ran_data_api.py`, `conftest.py`
**Date:** 2026-04-16

---

## Summary

The plan is well-structured: 8 tasks, clear TDD steps, correct frozen-dataclass style, and good separation between raw parsing (pure) and HTTP (explicit side-effect). The SQL panel builders are the weak point -- several DuckDB SQL constructs are wrong or fragile, the AR(1) warmup boundary is not tested, and roughly a dozen spec-mandated behaviors have no corresponding tests. The plan is implementable but needs fixes before agent dispatch.

---

## BLOCK-1: `fred_daily` and `fred_monthly` missing `_ingested_at` column

**Where:** Task 1, `_DDL_FRED_DAILY` (line 283) and `_DDL_FRED_MONTHLY` (line 291)

The spec (section 3.2, 3.3) does not require `_ingested_at` for FRED tables (they use composite PK, no audit column). However, every other raw table has it. The real problem is that `INSERT OR REPLACE` with a DEFAULT-stamped `_ingested_at` will silently reset the timestamp on re-ingestion for tables that have it -- but for `fred_daily` and `fred_monthly`, there is no audit trail of re-ingestion at all. This is a consistency gap but not a spec violation.

**Action required:** Decide whether FRED tables should have `_ingested_at`. If yes, add it to DDL + update `DESCRIBE` tests. If no (spec says no), document the rationale. Either way, flag it as a conscious design choice.

---

## BLOCK-2: `LAST()` is not a DuckDB aggregate function

**Where:** Task 5, `vix_weekly` CTE (line 1351), `oil_weekly` CTE (line 1361)

DuckDB does not have a `LAST(value ORDER BY date)` aggregate. The correct DuckDB syntax for "last value within a group ordered by a column" is:

```sql
ARG_MAX(value, date) AS vix_friday_close
```

Or use `LAST_VALUE` as a window function (not as a plain aggregate in GROUP BY). As written, these CTEs will produce a SQL error at runtime.

**Action required:** Replace `LAST(value ORDER BY date)` with `ARG_MAX(value, date)` in both `vix_weekly` and `oil_weekly` CTEs.

---

## BLOCK-3: `dane_ipc_release` CTE uses invalid DuckDB syntax

**Where:** Task 5, `dane_ipc_release` CTE (lines 1380-1386)

The expression `dr.week_start.year()::INT` is not valid DuckDB SQL. DuckDB uses `EXTRACT(YEAR FROM dr.week_start)::INT` or `YEAR(dr.week_start)`. The correlated subquery inside `CASE WHEN ... THEN (SELECT month ...)` is also needlessly complex and likely wrong -- it joins on a reconstructed date using `make_date` with fragile logic that doesn't correctly map release calendar entries to IPC months.

Moreover, this CTE is defined but **never referenced** in the final SELECT. The weekly panel hardcodes `dane_ipc_pct = 0.0` (line 1422), making this dead SQL.

**Action required:** Either wire `dane_ipc_release` into the final SELECT so release weeks get real `dane_ipc_pct` values, or remove the dead CTE. Currently, `dane_ipc_pct` is always 0.0 even on release weeks, which means Task 6's AR(1) surprise is the only path to non-zero values -- but `dane_ipc_pct` itself is never populated, contradicting the spec's weekly_panel definition (section 4.1).

---

## BLOCK-4: `build_weekly_panel` SQL uses string interpolation for dates

**Where:** Task 5, lines 1316-1436

The SQL uses `f"... WHERE date >= '{sample_start}'::DATE"` -- Python f-string interpolation of a `date` object into SQL. While not a SQL injection risk (it's a date, not user input), it's fragile: if `sample_start` has an unexpected `__str__` format, the query breaks silently. DuckDB's Python API supports parameterized queries.

**Action required:** Use parameterized queries (`?` placeholders with `conn.execute(sql, [sample_start])`) instead of f-string interpolation. This matches the style used in all other modules in the plan.

---

## BLOCK-5: `test_validate_weekly_panel_catches_null_surprise` missing import

**Where:** Task 8, line 1843

The test uses `pytest.raises` but `pytest` is not imported in the appended code block. The original `test_econ_pipeline.py` (Task 7 Step 1) imports `duckdb` and `date` but not `pytest`.

**Action required:** Add `import pytest` to `test_econ_pipeline.py` or ensure the initial file creation includes it.

---

## FLAG-1: No tests for IBR (SDMX XML) parsing

**Where:** Task 2

The plan declares `parse_ibr_sdmx_xml` and `fetch_ibr` but provides **zero tests** for IBR parsing. The test file (`test_econ_banrep.py`) only tests TRM and intervention. SDMX XML parsing is the most fragile parsing code in the plan (namespace handling, dimension filtering for SUBJECT=IRIBRM00 + UNIT_MEASURE=ER). This is the highest-risk untested code path.

**Action required:** Add at minimum:
- `test_parse_ibr_sdmx_xml_extracts_rows()` with a sample SDMX XML snippet
- `test_parse_ibr_sdmx_xml_filters_subject()` verifying non-IRIBRM00 series are excluded
- `test_ibr_rows_insert_into_db()` verifying DB insertion

---

## FLAG-2: No test for weeks with holidays (n_trading_days < 5)

**Where:** Task 5

The spec explicitly documents degenerate weeks with `n_trading_days <= 1` (section 4.1). The plan seeds exactly 5 trading days per week in `_seed_trm`, so `n_trading_days` is always 5 in tests. There is no test verifying that a 3-day or 1-day week produces correct RV and `n_trading_days`.

**Action required:** Add a test case with a short week (e.g., only 3 TRM observations in one week) and verify `n_trading_days == 3` and RV is sum of 3 squared returns.

---

## FLAG-3: No test for US CPI surprise construction

**Where:** Task 6

`us_cpi_surprise` is documented in the spec (section 4.1) as AR(1) on CPIAUCSL MoM % changes mapped to BLS release weeks. The plan's `compute_ar1_surprises` only handles DANE IPC. There is no code or test for US CPI surprise at all -- `us_cpi_surprise` stays 0.0 forever.

**Action required:** Either implement US CPI AR(1) surprise in Task 6 (parallel to DANE IPC), or explicitly document that `us_cpi_surprise` is deferred and add it to "What This Plan Does NOT Cover." Currently it's a silent omission.

---

## FLAG-4: AR(1) warmup boundary not tested

**Where:** Task 6

The test seeds 24 months of IPC data (2022-01 to 2023-12) with `warmup_months=12`. But it never asserts that the first 12 months produce no surprises. The test only checks `nonzero[0] > 0`, which could pass even if warmup observations leak into the panel. A correct test would verify that no surprise appears before month 13.

**Action required:** Add assertion that `cpi_surprise_ar1 == 0.0` for all weeks before the warmup cutoff date.

---

## FLAG-5: `dane_ipp_pct` never populated

**Where:** Task 5

The weekly panel hardcodes `dane_ipp_pct = 0.0` (line 1423). The spec defines `dane_ipp_pct` as "IPP MoM % change on release week; 0.0 on non-release weeks." There is no CTE that joins `dane_ipp_monthly` to the release calendar for IPP. Unlike CPI surprise (which Task 6 handles via AR(1)), `dane_ipp_pct` is a raw value from the IPP table -- it should be populated in the SQL, not via post-processing.

**Action required:** Add a CTE that maps IPP release weeks to `ipp_pct_change` values from `dane_ipp_monthly`, and wire it into the final SELECT.

---

## FLAG-6: `banrep_rate_surprise` never computed

**Where:** Tasks 5-6

Both `weekly_panel` and `daily_panel` hardcode `banrep_rate_surprise = 0.0`. The spec (section 3.10) says "The pipeline provides the raw daily IBR series; the estimation module constructs the surprise." So 0.0 is correct per the spec's boundary. But the plan's Self-Review Checklist (line 1966) claims "Manifest logging: Task 7" without mentioning that `banrep_rate_surprise` is deferred to the estimation module. This should be explicitly called out.

**Action required:** Add `banrep_rate_surprise` to the deferred-items section of the plan, citing spec section 3.10.

---

## FLAG-7: FRED `fetch_fred_series` requires `api_key` parameter but no test covers this

**Where:** Task 3

`fetch_fred_series(series_id, api_key, start)` requires an `api_key` positional argument. But no test verifies that the function correctly passes `api_key` to the FRED API. The live-fetcher tests are omitted (expected), but there should be at least a test that `parse_fred_observations` handles the response structure when `api_key` is invalid (FRED returns an error JSON, not a 4xx).

FRED returns `{"error_code": 1, "error_message": "Bad Request..."}` for invalid API keys -- this is a 200 OK with error in the body. `fetch_fred_series` calls `resp.raise_for_status()` which won't catch this.

**Action required:** Add a test for FRED error-in-200 responses and handle them in `fetch_fred_series`.

---

## FLAG-8: `_parse_amount` does not handle comma-separated numbers

**Where:** Task 2, `econ_banrep.py` line 630

Looking at the cached intervention JSON, amounts appear as plain numbers (`119.3`, `77`, `1.8`). But BanRep data from other sources sometimes uses comma as thousands separator (e.g., `1,098`). If any intervention amount in the JSON contains commas, `float(s)` will raise `ValueError`.

**Action required:** Verify the cached JSON never contains commas in amounts. If it might, add `s = s.replace(",", "")` before `float(s)`.

---

## FLAG-9: `log_manifest` PK collision risk

**Where:** Task 7, line 1779

The manifest PK is `(source, downloaded_at)` where `downloaded_at` is `datetime.now()`. If two fetchers for different sources run within the same microsecond (unlikely but possible with parallel execution), no collision. But if the same source is logged twice in rapid succession (e.g., retry), microsecond-resolution `datetime.now()` could collide. The spec acknowledges "PK collisions are prevented by microsecond-precision timestamps" but this is optimistic.

**Action required:** Either accept the risk (low probability) or add a try/except around the INSERT with a brief sleep-and-retry on `ConstraintException`.

---

## FLAG-10: No test for `parse_dane_ipp_csv`

**Where:** Task 4

`parse_dane_ipp_csv` is implemented but has zero tests. Only `parse_dane_ipc_csv` and `parse_dane_release_calendar_csv` are tested.

**Action required:** Add tests for `parse_dane_ipp_csv` parallel to the IPC tests.

---

## FLAG-11: `DaneIppRow` not imported in test file

**Where:** Task 4, `test_econ_dane.py` line 963

The import statement imports `parse_dane_ipc_csv`, `parse_dane_release_calendar_csv`, `DaneIpcRow`, `DaneReleaseCalendarRow` but not `parse_dane_ipp_csv` or `DaneIppRow`. This is consistent with FLAG-10 (no IPP tests).

---

## FLAG-12: Weekly panel `oil_return` is NULL for the first week in sample

**Where:** Task 5

The `oil_with_return` CTE uses `LAG(last_oil_price) OVER (ORDER BY week_start)`. The first week's `oil_return` will be NULL because there's no prior week. The test `test_weekly_panel_oil_return` seeds oil data starting from `2024-01-05` (a Friday before week 1), but this price falls in a different week from `2024-01-08`. The LAG window is over `oil_weekly` (which groups by `date_trunc('week', date)`), so `2024-01-05` belongs to the week of `2024-01-01`. The test expects `oil_return = log(74.0/72.0)` which requires the prior week's oil price to be 72.0 -- this works because `2024-01-05` is in the prior week.

However, if `sample_start` filtering in the `oil_weekly` CTE excludes the prior week (`WHERE date >= '2024-01-08'`), then the LAG has no prior row and `oil_return` would be NULL. The test passes `sample_start=date(2024, 1, 8)`, and the oil CTE filters `date >= sample_start`. Since `2024-01-05 < 2024-01-08`, the prior week's oil data is excluded, making `oil_return` NULL for week 2024-01-08.

**Action required:** The test assertion `oil_ret = math.log(74.0 / 72.0)` will fail because the prior-week oil observation is filtered out by `sample_start`. Either: (a) remove the `date >= sample_start` filter from the oil CTE (raw data should go back further than the panel start), or (b) adjust the test to seed oil data that falls within the sample window's prior week. This is a latent test failure.

---

## NIT-1: `EXPECTED_TABLES` does not include derived panel tables

**Where:** Task 1, line 236

`EXPECTED_TABLES` is a frozenset of the 10 raw tables. But `weekly_panel` and `daily_panel` are also tables (created in Task 5). The set name `EXPECTED_TABLES` is slightly misleading since `init_db` does not create the derived tables. Consider renaming to `RAW_TABLES` or `SCHEMA_TABLES`.

---

## NIT-2: `econ_schema.py` uses `frozenset` for `EXPECTED_TABLES` but `Final` typing

**Where:** Task 1, line 236

`EXPECTED_TABLES: Final[frozenset[str]]` -- good. Consistent with `ran_utils.py` style.

---

## NIT-3: `_DDL_DOWNLOAD_MANIFEST` PK includes `downloaded_at` TIMESTAMP

**Where:** Task 1, line 353

DuckDB TIMESTAMP PKs with microsecond precision are unusual. This works but is worth a comment in the DDL explaining why.

---

## NIT-4: `econ_panels.py` imports `math` at module level but only needs it if numpy is available

**Where:** Task 5, line 1298

The `import math` is fine (stdlib). But the `import numpy as np` added in Task 6 (line 1608) should be at module level, not inside the function, for consistency with the codebase style in `ran_utils.py`.

---

## NIT-5: `compute_ar1_surprises` mutates DB state but is in `econ_panels.py`

**Where:** Task 6

The function issues `UPDATE` statements, making it impure. This is acceptable (the spec places AR(1) in the pipeline), but it breaks the module's docstring claim of "All computation is done in SQL via DuckDB. Python orchestrates the queries." The AR(1) computation is done in numpy, not SQL. Update the docstring.

---

## NIT-6: `ValidationError` is a class, not a frozen dataclass

**Where:** Task 8, line 1857

`class ValidationError(Exception)` uses inheritance (from Exception). This is acceptable -- the functional-python skill explicitly exempts test infrastructure and exceptions from the "no classes" rule. But worth noting for completeness.

---

## NIT-7: TDD step granularity in Task 2

**Where:** Task 2

Steps 1-4 cover TRM parsing (3 tests), then Steps 5-6 cover intervention (3 tests). But IBR is implemented in Step 3 with zero test steps. The TDD protocol requires test-first for every behavior. IBR implementation without prior test violates Rule 1.

---

## Functional-Python Compliance

| Check | Status |
|---|---|
| All dataclasses frozen? | PASS -- all 8 domain types use `@dataclass(frozen=True, slots=True)` |
| Functions pure (except HTTP)? | PASS -- parsing functions are pure; `fetch_*` functions have explicit HTTP side effects |
| Final types for constants? | PASS -- all module-level constants use `Final[...]` |
| No inheritance in production? | PASS -- `ValidationError(Exception)` is the only class with inheritance; acceptable |
| `from __future__ import annotations`? | PASS -- all modules include it |

---

## TDD Step Correctness

| Check | Status |
|---|---|
| Write test before implementation? | MOSTLY PASS -- IBR has no test (FLAG-1), IPP has no test (FLAG-10) |
| Verify fail before implementing? | PASS -- every task has explicit "Expected: FAIL" steps |
| Atomic steps (2-5 min)? | PASS -- each step is small and focused |
| One commit per task? | PASS -- clear commit boundaries |

---

## Verdict: PASS WITH FLAGS

The plan is structurally sound and follows the TDD protocol for the majority of behaviors. The frozen-dataclass style, module separation, and test fixture approach are all correct. However, 12 flags identify real gaps that must be addressed before agent dispatch:

**Must fix before dispatch:**
- BLOCK-2: `LAST()` is not a DuckDB function -- runtime SQL error guaranteed
- BLOCK-3: Dead/broken `dane_ipc_release` CTE
- BLOCK-5: Missing `import pytest`
- FLAG-1: Zero IBR tests (highest-risk untested code)
- FLAG-3: US CPI surprise completely missing
- FLAG-5: `dane_ipp_pct` never populated
- FLAG-12: Latent test failure due to `sample_start` filtering oil data

**Should fix before dispatch:**
- BLOCK-1: FRED `_ingested_at` consistency decision
- BLOCK-4: String interpolation vs parameterized queries
- FLAG-2: No short-week test
- FLAG-4: Warmup boundary not asserted
- FLAG-7: FRED error-in-200 not handled
- FLAG-10: No IPP CSV tests
