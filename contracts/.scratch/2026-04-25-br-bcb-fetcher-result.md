# Task 11.N.2.BR-bcb-fetcher — Verification Memo

**Date:** 2026-04-25
**Plan revision:** Rev-5.3.2 CORRECTIONS block
**Plan path:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (lines ~1890–1915)
**Sibling precedent:** Task 11.N.2.CO-dane-wire (commit `f7b03caac`)
**Branch HEAD prior to commit:** `f7b03caac`
**Author:** Data Engineer subagent (this stream)

---

## Summary

Upgraded the Brazilian CPI source feeding the Y₃ inequality-differential
pipeline from IMF-IFS-via-DBnomics (stuck at 2025-07-01, 9-month lag) to
the BCB SGS direct API series 433 (current through 2026-03-01, 1-month
lag). Cutoff date = **2026-03-01**, comfortably satisfying the
≥ 2026-02-01 staleness gate at the 2026-04-25 authoring date.

The CO sibling pattern is mirrored with one structural difference: BCB
SGS/433 returns *variation %* per month (not levels), so the cumulative
index is materialized at ingest time so the downstream Y₃ consumer
(`y3_compute.compute_weekly_log_change`) sees a level series and Δlog
behaves correctly. The cumulative-index base value is `I_0 = 100`,
methodologically arbitrary but deterministic; Δlog is invariant under
positive global rescale (verified by
`test_cumulative_index_dlog_matches_pct_change_within_tolerance`).

---

## Pre-flight verification

| Check | Result |
|---|---|
| BCB SGS/433 endpoint live | ✅ 200 OK; `[{"data":"01/03/2026","valor":"0.88"}, ...]` |
| Pre-flight cumulative-index requirement | ✅ confirmed: API emits *variation %*, level series materialized at ingest time |
| Cumulative-index base choice | I_0 = 100 (deterministic; no tuning) |
| `dane_ipc_monthly` schema reference | ✅ ran `DESCRIBE` to mirror style |

---

## Strict TDD protocol (per `feedback_strict_tdd`)

**RED phase verified.** Initial run of `test_y3_br_bcb_wire.py` failed at
the very first test (`test_expected_tables_includes_bcb_ipca_monthly`)
on `AssertionError: assert 'bcb_ipca_monthly' in frozenset(...)`.
Subsequent tests would have failed on `ImportError` (no
`migrate_bcb_ipca_monthly`, no `BcbIpcaMonthly`, no
`ingest_bcb_ipca_monthly`, no `_fetch_bcb_headline_broadcast`).

**GREEN phase verified.** After implementation: 16/16 BR tests pass.

---

## Test scoreboard

### In-scope (this task)

| Suite | Result |
|---|---|
| `scripts/tests/inequality/test_y3_br_bcb_wire.py` | **16 passed** |

### In-scope regression (pre-existing inequality suite)

| Suite | Result |
|---|---|
| `scripts/tests/inequality/` (all) | **82 passed, 1 skipped** |

The 1 skip is the pre-existing `test_y3_panel_meets_n_min_or_skips`
guard (predates Rev-5.3.2; Y₃ panel coverage gate test).

### Full-suite regression check

```
$ pytest contracts/scripts/tests/ --no-header
...
2 failed, 1016 passed, 7 skipped, 16 warnings in 263.23s
```

The **2 failures** are the same pre-existing failures disclosed in the
CO sibling memo:

* `scripts/tests/remittance/test_cleaning_remittance.py::test_load_cleaned_remittance_panel_raises_file_not_found_without_fixture`
* `scripts/tests/remittance/test_cleaning_remittance.py::test_load_cleaned_remittance_panel_calls_rev4_loader_first`

Root cause: `scripts/cleaning.py:487` raises `NotImplementedError`
("load_cleaned_remittance_panel V1 body is the Task-9 seam only; the
full loader lands with Task 11 (fixture) + Task 15 (panel-integration)").
This predates this task (commit `28d76cbb0`-era seam) and is out of
scope per `feedback_agent_scope`. **No NEW failures introduced** by this
task.

---

## Acceptance-criterion checklist (from plan body Task 11.N.2.BR-bcb-fetcher)

- [x] Failing-test-first per strict TDD (verified red → green)
- [x] `ingest_bcb_ipca_monthly` produces ≥ 12 rows of recent data
      (actual: **27 rows** for `[2024-01-01, 2026-04-24]`)
- [x] Cutoff ≥ 2026-02-01
      (actual: **2026-03-01**)
- [x] `fetch_country_wc_cpi_components('BR', date(2024,1,1), date(2026,4,24), conn=...)`
      returns cutoff ≥ 2026-02-01
      (actual: **2026-03-01** — verified via
      `test_fetch_country_wc_cpi_components_br_via_bcb_cutoff_ge_2026_02_01`)
- [x] All 4 component columns byte-equal per row
      (verified via `test_fetch_country_wc_cpi_components_br_via_bcb_returns_4_components`)
- [x] `_fetch_imf_ifs_headline_broadcast` byte-exact preserved
      (verified via `test_fetch_imf_ifs_headline_broadcast_signature_preserved`
      and the BR-without-conn dispatch test)
- [x] Existing tests under `scripts/tests/inequality/` remain green
      (82 passed, 1 skipped — pre-existing skip)
- [x] Verification memo at `contracts/.scratch/2026-04-25-br-bcb-fetcher-result.md`
      (this file)

---

## Anti-fishing guards honored

* **Cumulative-index base value not tuned.** I_0 = 100 was chosen
  deterministically before measuring any downstream metric. The choice
  is documented in the docstring of `materialize_ipca_cumulative_index`
  and tested for Δlog-invariance by
  `test_cumulative_index_dlog_matches_pct_change_within_tolerance`
  (Δlog of cumulative index ≈ ln(1 + var/100) within 1e-9).
* **No additional transformations.** No smoothing, no seasonal
  adjustment, no outlier clipping — only the cumulative-index materialization
  permitted by design doc §10 row 2.
* **IMF-IFS path preserved byte-exact** for the Task 11.N.2d.1-reframe
  sensitivity comparator. BR with `conn=None` continues to dispatch to
  `_fetch_imf_ifs_headline_broadcast`; KE always dispatches there
  (KE-fallback unchanged). Locked in by
  `test_fetch_country_wc_cpi_components_br_without_conn_uses_imf_path`
  and `test_ke_still_routes_to_imf_ifs_path`.
* **CO routing unchanged.** `test_co_with_conn_still_routes_to_dane`
  locks in the cross-country isolation: the BR change does not regress
  CO.

---

## PROVENANCE INTEGRITY (per task-body §"PROVENANCE INTEGRITY")

**Fresh symbols introduced in this commit (none pre-staged from prior streams):**

* `econ_schema._DDL_BCB_IPCA_MONTHLY`        — DDL for the new raw table
* `econ_schema.migrate_bcb_ipca_monthly`     — additive idempotent migration fn
* `econ_schema.EXPECTED_TABLES`              — extended with `"bcb_ipca_monthly"` (existing constant; new entry is fresh)
* `econ_pipeline._BCB_SGS_433_URL`           — endpoint format string
* `econ_pipeline._BCB_IPCA_CUMULATIVE_BASE`  — I_0 base constant
* `econ_pipeline.BcbIpcaObservation`         — parsed-payload dataclass
* `econ_pipeline.parse_bcb_sgs_433_json`     — pure JSON parser
* `econ_pipeline.fetch_bcb_sgs_433`          — HTTP fetcher
* `econ_pipeline.materialize_ipca_cumulative_index` — variation → level utility
* `econ_pipeline.upsert_bcb_ipca_monthly`    — idempotent UPSERT helper
* `econ_pipeline.ingest_bcb_ipca_monthly`    — top-level ingest fn
* `econ_query_api.BcbIpcaMonthly`            — frozen+slots reader dataclass
* `econ_query_api.load_bcb_ipca_monthly`     — pure reader fn
* `y3_data_fetchers._fetch_bcb_headline_broadcast` — new BR dispatch helper
* `tests/inequality/test_y3_br_bcb_wire.py`  — 16 tests (Step A schema / B ingest / C reader / D BR dispatch / E cross-country safety)

**Verified absent in `git show f7b03caac~1`:** all symbols above.
None were pre-staged in a prior stream — the entire surface area was
authored under this task. This contrasts with the CO precedent, where
`DaneIpcMonthly` and `load_dane_ipc_monthly` had been pre-staged in
`econ_query_api.py` by an earlier stream and were merely consumed by
the CO wire. (The CO memo's CORRIGENDUM noted this distinction; the
present task explicitly does not repeat the mis-claim.)

---

## Files modified (per `feedback_agent_scope`)

| Path | Change |
|---|---|
| `contracts/scripts/econ_schema.py` | Added `_DDL_BCB_IPCA_MONTHLY`, `migrate_bcb_ipca_monthly`, extended `EXPECTED_TABLES` and `init_db` |
| `contracts/scripts/econ_pipeline.py` | Added BCB ingest stack: parse + fetch + cumulative-index utility + UPSERT + top-level `ingest_bcb_ipca_monthly` |
| `contracts/scripts/econ_query_api.py` | Added `BcbIpcaMonthly` dataclass + `load_bcb_ipca_monthly` reader |
| `contracts/scripts/y3_data_fetchers.py` | Added BR-`conn` dispatch + `_fetch_bcb_headline_broadcast` helper; preserved IMF-IFS path |
| `contracts/scripts/tests/inequality/test_y3_br_bcb_wire.py` (NEW) | 16 TDD tests across 5 steps |
| `contracts/.scratch/2026-04-25-br-bcb-fetcher-result.md` (NEW) | this verification memo |

**No edits made to:**
- `dane_ipc_monthly` schema or rows (consume-only contract honored)
- `_fetch_dane_headline_broadcast` (unchanged)
- `_fetch_imf_ifs_headline_broadcast` (signature byte-exact)
- The plan markdown
- Any spec document
- `y3_compute.py` (pure-compute layer untouched)

---

## Smoke-test snapshot (for reviewer)

```text
$ python -c 'from scripts.econ_query_api import load_bcb_ipca_monthly; ...'
rows: 27
first: BcbIpcaMonthly(date=2024-01-01, pct=0.42, idx=100.42)
last:  BcbIpcaMonthly(date=2026-03-01, pct=0.88, idx=111.4018)
cutoff: 2026-03-01
```

Cutoff is 1.8 months stale at the 2026-04-25 authoring date — the
prior IMF-IFS-via-DBnomics path would have been ~9 months stale at the
same instant. Source upgrade delivers the ~7-month freshness gain that
Path-ζ's BR component was justified by.

---

## Reviewers (next step)

After this commit, the foreground orchestrator dispatches:
- Code Reviewer
- Reality Checker
- Senior Developer

per `feedback_implementation_review_agents`. The Data Engineer
subagent does NOT dispatch them.
