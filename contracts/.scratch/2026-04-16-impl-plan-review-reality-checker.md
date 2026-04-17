# Reality Checker Review: Structural Econ Data Pipeline Implementation Plan

**Plan:** `contracts/docs/superpowers/plans/2026-04-16-structural-econ-data-pipeline.md`
**Spec:** `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md` (Rev 4)
**Date:** 2026-04-16
**Reviewer:** Reality Checker

---

## 1. Expected Row Counts

**NIT-1: TRM ~8,250 is reasonable but slightly low.**
TRM runs 1991-12-02 to April 2026 = ~34.4 years. At ~240 Colombian trading days/year (fewer than US due to ~18 public holidays), that gives ~8,256. The estimate of ~8,250 is acceptable. Validation threshold `row_count > 8000` is appropriate — it allows for mild variation without false alarms.

**NIT-2: IBR ~4,500 is reasonable.**
IBR from 2008-01-02 to April 2026 = ~18.3 years x ~245 trading days = ~4,494. The ~4,500 estimate and `row_count > 4000` threshold are both fine.

**NIT-3: FRED VIX ~9,000 is reasonable.**
VIXCLS starts 1990-01-02. ~36 years x ~252 US trading days = ~9,072. Estimate matches. Validation `row_count > 5000` is conservative (intentionally, per spec noting the estimation window is smaller than full download).

**PASS: Intervention exactly 1,674 is verified.**
I read the actual cached file at `contracts/data/raw/banrep_fx_intervention.json`. The JSON has exactly 1,674 rows. First row: `1999/12/01`, last row: `2024/10/04`. The `row_count == 1674` exact check is correct and verified against the file.

---

## 2. API Endpoint URLs

**PASS: Socrata TRM endpoint and dataset ID.**
`https://www.datos.gov.co/resource/32sa-8pi3.json` — matches spec section 1 (Priority 1a) exactly. Dataset ID `32sa-8pi3` is consistent between plan and spec.

**PASS: BanRep SDMX IBR endpoint.**
`https://totoro.banrep.gov.co/nsi-jax-ws/rest/data/ESTAT,DF_IBR_DAILY_HIST,1.0/all/ALL/` — matches spec section 1 (Priority 1b) exactly. Parameters `startPeriod=2008&endPeriod=2027` also match.

**PASS: FRED endpoints.**
`https://api.stlouisfed.org/fred/series/observations` for series data and `https://api.stlouisfed.org/fred/release/dates` for BLS release dates — both are standard FRED REST API paths.

**PASS: `release_id=10` is correct.**
FRED release ID 10 is "Consumer Price Index" (the BLS release covering CPI-U, CPI-W, etc.). The spec correctly notes this at RC-F5.

---

## 3. FRED API Parameters

**PASS: `file_type=json` is correct.**
FRED's API uses `file_type` (not `format` or `output_type`). Valid values are `json`, `xml`, `txt`, `xls`. The plan uses `json` consistently.

**PASS: `observation_start` format is YYYY-MM-DD.**
The plan passes `observation_start=2000-01-01` style strings. FRED requires `YYYY-MM-DD` for this parameter. Correct.

**FLAG-1: FRED release/dates endpoint may need pagination for full history.**
The plan calls `https://api.stlouisfed.org/fred/release/dates?release_id=10&file_type=json` without any date filtering. FRED's release/dates endpoint returns at most 10,000 results per request (default `limit=10000`). With ~280 CPI releases since 2000, this is not a binding constraint NOW, but the endpoint returns ALL release dates for release 10 going back to 1947 (~940 entries). This is still under 10,000 so pagination is not needed, but the plan should note that only post-2000 entries are relevant and could filter with `include_release_dates_with_no_data=false` for cleanliness. **Minor — does not block correctness.**

---

## 4. Socrata Pagination

**PASS: $limit=50000 is specified.**
The plan's mapping table shows `$limit=50000` in the URL: `https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=50000`. The spec documents the 1,000-row default limit (RC-F2) and the plan handles it correctly. At ~8,250 rows, a single request with `$limit=50000` retrieves everything.

**NIT-4: No `$offset` fallback documented.**
If the dataset grows beyond 50,000 rows (unlikely for TRM — would need 200+ years), the plan has no pagination fallback. Not a real concern for this dataset but could be noted for defensive coding. Trivially non-blocking.

---

## 5. BLS Release Date Mapping

**PASS: Month M release maps to CPI for month M-1.**
The plan's `parse_bls_release_dates` correctly implements:
- Release date in January -> `ref_year = year - 1, ref_month = 12` (December CPI)
- Release date in February -> `ref_year = year, ref_month = 1` (January CPI)

The test verifies: release on 2024-01-11 -> `BlsReleaseDate(year=2023, month=12, ...)`. This is correct. BLS releases the prior month's CPI data, typically in the second or third week of the following month.

**FLAG-2: BLS release_id=10 includes non-CPI-U releases.**
Release 10 covers the entire "Consumer Price Index" BLS release, which includes CPI-U, CPI-W, chained CPI, etc. All are released on the SAME date, so the release dates are correct for CPIAUCSL. However, the response includes release dates going back decades. The plan's `parse_bls_release_dates` processes ALL of them, which means the `bls_release_calendar` table will contain entries for years long before the estimation window (pre-2000). This is harmless — the panel builder only joins on weeks within the sample window — but the ~280 row count estimate in the mapping table is for the estimation window only, while the actual table will have ~940 rows. **The validation check `row_count > 250` will pass regardless. Non-blocking.**

---

## 6. Validation Thresholds

**PASS: TRM `row_count > 8000` is reasonable.** Conservative lower bound.

**PASS: IBR `rates > 0 and < 30` is reasonable.** Colombian IBR has historically ranged from ~1% to ~13%. The 0–30% window provides ample headroom.

**PASS: VIX/oil `row_count > 5000` is reasonable.** Conservative for full-history download (~8,000–9,000 rows), adequate for estimation-window focus.

**PASS: Weekly panel `RV > 0; n_trading_days in [1,5]; no NULL in surprise cols; intervention_dummy in {0,1}`.** All match spec section 4.1 and pipeline flow step 6. The 0.0-not-NULL semantics for surprises is correctly enforced.

**NIT-5: No upper-bound validation on TRM values.**
The plan validates IBR has an upper bound (< 30) but does not validate TRM has a plausible range (e.g., 500 < trm < 10000). A TRM of 0 or 1,000,000 would indicate corrupted data. Not critical but would catch parsing errors.

---

## 7. Missing Practical Concerns

**FLAG-3: FRED API key handling is incomplete.**
The plan's `fetch_fred_series` and `fetch_bls_release_dates` both take `api_key` as a parameter, which is correct. However, the pipeline orchestrator (Task 7, `econ_pipeline.py`) does not show how the API key is sourced. The spec says "FRED_API_KEY environment variable" but the orchestrator implementation in Task 7 is minimal (only `log_manifest` and `compute_sha256`). The actual orchestration that calls `fetch_fred_series(series_id, api_key=os.environ["FRED_API_KEY"])` is not written. This is presumably deferred to the agent implementing it, but the plan should note the environment variable dependency explicitly in Task 7.

**FLAG-4: SDMX XML parsing assumes Generic Data format but BanRep may return Structure-Specific.**
The plan's `parse_ibr_sdmx_xml` uses SDMX Generic Data v2.1 namespace (`http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic`). BanRep's SDMX REST API documentation (v3.0) may return Structure-Specific Data by default. The plan does not add an `Accept` header to force `application/vnd.sdmx.genericdata+xml;version=2.1`. If BanRep returns Structure-Specific format, the parser will silently return an empty list (no matching XML elements). **Mitigation:** The validation check `row_count > 4000` would catch this, but the failure mode would be confusing. The plan should either: (a) add an Accept header, or (b) test with a real SDMX response before finalizing the parser. **Should fix.**

**FLAG-5: Socrata TRM date parsing is fragile.**
The plan's `parse_trm_socrata_response` does:
```python
parsed_date = datetime.fromisoformat(fecha_str.replace(".000", "")).date()
```
This replaces `.000` which handles milliseconds, but Socrata may return `.000000` (microseconds) or other variants. `datetime.fromisoformat` in Python 3.11+ handles these natively, but the explicit `.replace(".000", "")` could truncate incorrectly if the string contains `.0001` (would become `1`). Since the spec says the field format is `T00:00:00.000`, this is likely fine in practice, but a safer approach is just `datetime.fromisoformat(fecha_str).date()` since Python 3.11+ handles the full ISO 8601 format including milliseconds. **Minor robustness concern.**

**NIT-6: No HTTP retry logic for any fetcher.**
Network requests to Datos Abiertos, BanRep SDMX, and FRED have no retry-on-failure logic. A single transient timeout or 5xx error will fail the entire pipeline. The spec's pipeline flow (section 5) says "if endpoint fails -> STOP (escalate to user)" for TRM, which is intentional for critical data. But for FRED (Priority 3, "lowest uncertainty"), a retry with backoff would be more robust. Not blocking — the pipeline is designed to be re-runnable.

**NIT-7: No timezone handling documented for DANE release dates.**
DANE releases at 6-8pm COT (UTC-5). The `dane_release_calendar` stores `release_date` as DATE (no time), which is correct since the release day is what matters for weekly/daily panel assignment. However, if the release falls late Friday COT, the market reaction is Monday's TRM, which is the NEXT week. The spec addresses this in section 4.2 (day-t vs day-t+1 as estimation concern). No pipeline-level issue.

**NIT-8: `fred_daily` and `fred_monthly` tables lack `_ingested_at` column.**
The spec defines `_ingested_at` for `banrep_trm_daily`, `dane_ipc_monthly`, `dane_ipp_monthly`, and the BanRep tables. The FRED tables (`fred_daily`, `fred_monthly`) do not have `_ingested_at`. The spec does not require it for FRED tables (they use composite PKs without the audit column). This is consistent between plan and spec, but worth noting that FRED data has no row-level audit trail — only the `download_manifest` tracks when FRED data was fetched.

**FLAG-6: DuckDB `INSERT OR REPLACE` requires careful handling with composite PKs.**
For `fred_daily` (PK = `series_id, date`), `INSERT OR REPLACE` works correctly in DuckDB 1.5.1 — it replaces on PK conflict. However, DuckDB's `INSERT OR REPLACE` behavior with CHECK constraints can be surprising: if the CHECK fails, the INSERT is rejected (not silently skipped). The plan's test `test_fred_daily_check_constraint` correctly tests this. No issue, but noting for completeness.

**FLAG-7: The weekly panel SQL has a problematic DANE IPC release join.**
In Task 5, the `dane_ipc_release` CTE (lines 1380-1386) contains:
```sql
JOIN dane_ipc_monthly dim ON dim.date = make_date(dr.week_start.year()::INT,
    CASE WHEN (SELECT month FROM dane_release_calendar ...) ...
```
This nested subquery inside a JOIN condition is both fragile and potentially incorrect. The release calendar maps `(year, month)` to a `release_date`, and the IPC data for that month should be joined via `make_date(year, month, 1)`. But the CTE uses `dr.week_start.year()` which is the release WEEK's year, not the reference year from the calendar. If a December IPC release happens in January (which it does), `week_start.year()` would be the new year, not December's year. **However**, this CTE is never actually used in the final SELECT — the plan initializes `dane_ipc_pct = 0.0` as a hardcoded value. The actual IPC release mapping is done in Task 6 via `compute_ar1_surprises`. So this dead CTE is misleading but non-blocking.

---

## Verdict: PASS WITH FLAGS

The plan is factually accurate on all major points checked:
- Row count estimates are realistic and verified (intervention exact match confirmed against actual file)
- All API endpoint URLs match the spec
- FRED parameters (`file_type=json`, `observation_start` format, `release_id=10`) are correct
- Socrata `$limit=50000` handles the default 1,000-row truncation
- BLS release-month-minus-one mapping is correctly implemented and tested
- Validation thresholds are reasonable

**Flags requiring attention before implementation:**

| ID | Severity | Issue |
|---|---|---|
| FLAG-1 | Low | FRED release/dates may benefit from `realtime_start` filter to exclude pre-2000 entries |
| FLAG-2 | Low | `bls_release_calendar` will have ~940 rows not ~280; validation still passes |
| FLAG-3 | Medium | FRED API key sourcing not shown in pipeline orchestrator |
| FLAG-4 | Medium | SDMX parser assumes Generic Data format; should set Accept header or validate format |
| FLAG-5 | Low | TRM date parsing `.replace(".000", "")` is fragile; use `fromisoformat` directly |
| FLAG-6 | Low | DuckDB INSERT OR REPLACE with CHECK constraints — already tested, noted for awareness |
| FLAG-7 | Medium | Dead `dane_ipc_release` CTE in weekly panel SQL is misleading; remove it to avoid confusion |

FLAG-3, FLAG-4, and FLAG-7 should be addressed. FLAG-4 in particular could cause a silent empty-result failure on the IBR download. FLAG-7 is dead code that will confuse the implementing agent.

All other items are NITs or informational.
