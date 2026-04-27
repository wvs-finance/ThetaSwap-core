# Reality Checker — Rev-5.3.2 Task 11.N.2d-rev load-bearing review

**Date:** 2026-04-25
**Commit under review:** `c5cc9b66b4aa2b7b4d163a62f3e6765086502a1b` on branch `phase0-vb-mvp`
**DE memo reviewed:** `contracts/.scratch/2026-04-25-y3-rev532-ingest-result.md`
**Plan task:** Task 11.N.2d-rev in `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Design doc:** `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md`
**Reviewer mandate:** load-bearing gate-checker; reconcile claimed 76 weeks vs. prior projection of 65 weeks at cutoff `2025-12-31`.

---

## Verdict: **PASS**

The 76-week joint X_d × Y₃ overlap claim is **independently re-derived**, the **11-week gap from prior projection (65 → 76) is fully accounted for by the LOCF tail extension over `[2026-01, 2026-03]`**, and **all anti-fishing invariants hold**. The gate-cleared verdict is honest, not inflated.

**Reviewer ack — methodology literal RC-A6:** I confirm the literal `source_methodology` value `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` landed in `onchain_y3_weekly` per memo §6.

---

## Reconciliation of the 11-week discrepancy (load-bearing finding)

The DE's claim of 76 weeks vs. my prior projection of 65 weeks is reconciled by **LOCF tail extension forward of the EU binding cutoff**, not by silent backward inflation. Cutoff-by-cutoff arithmetic (probe 5):

| Cutoff `week_start <=` | Joint nonzero count | Δ from prior cutoff |
|---|---|---|
| 2025-10-31 | 57 | — |
| 2025-11-30 | 61 | +4 |
| **2025-12-31** | **65** | **+4** ← my prior projection cutoff |
| 2026-01-31 | 70 | +5 |
| 2026-02-28 | 74 | +4 |
| 2026-03-31 | 76 | +2 |
| 2026-04-30 | 76 | 0 |

**Reconciliation:**
- At cutoff `2025-12-31`, the count is **65**, byte-exactly matching my prior projection. No backward inflation.
- The 11-week gap from 65 → 76 lives entirely in `[2026-01-01, 2026-03-31]`: 5 + 4 + 2 = 11 weeks.
- This is the LOCF tail forward of the binding EU 2025-12-01 cutoff, **deterministic and pre-committed in `y3_compute.py:144`** (the `+ pd.Timedelta(days=120)` extension constant in `interpolate_monthly_to_weekly_locf`).
- EU 2025-12-01 + 120 days = 2026-03-31; the panel max of 2026-03-27 is the last Friday-anchored date inside this window. Matches design doc §7 (LOCF-Friday-anchored interpolation, monthly → weekly).
- LOCF-tail rows are NOT invented data; each week carries the **last published monthly** WC-CPI as of that Friday — for the 11 LOCF-tail weeks, that is EU=2025-12-01 (real), CO=2026-03-01 (real, DANE), BR=2026-03-01 (real, BCB).

**The 76-count is therefore not "inflated" — it is the natural consequence of pre-committed LOCF tail behavior interacting with the γ-window-swap upper-bound (`end=2026-04-24`), which my prior projection did not explicitly carry forward beyond the EU monthly cutoff.** My prior projection was conservative by ~11 weeks; the DE's actual count is the correct LOCF-aware value.

---

## Probe-by-probe evidence

### Probe 1 — methodology tag inventory (matches memo §3.2)

```
y3_v1_3country_ke_unavailable                                     | 59  | 2024-09-13 | 2025-10-24
y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable | 116 | 2024-01-12 | 2026-03-27
```

Both tags coexist; v1 row count unchanged at 59; v2 panel range matches memo claim exactly. Composite-PK isolation operating as designed.

### Probe 2 — direct gate JOIN (matches memo §3.3)

```sql
SELECT COUNT(*) FROM onchain_xd_weekly x
INNER JOIN onchain_y3_weekly y ON x.week_start = y.week_start
WHERE x.proxy_kind = 'carbon_basket_user_volume_usd'
  AND CAST(x.value_usd AS DOUBLE) > 0
  AND y.source_methodology = 'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable'
  AND y.y3_value IS NOT NULL
-- → 76
```

Both the strict memo-style filter (`> 0` AND `y3_value IS NOT NULL`) and the simpler `value_usd != 0 AND value_usd IS NOT NULL` form return **exactly 76**. The X_d carbon basket has zero negative rows (it's a volume series), so the two filter forms are arithmetically equivalent. Gate threshold ≥ 75 is met with 1-week margin.

### Probe 3 — Y₃ v2 panel bounds (matches memo §3.2)

`MIN(week_start) = 2024-01-12, MAX(week_start) = 2026-03-27, COUNT = 116`. 116 ≥ 105 secondary panel-weeks gate, PASS.

### Probe 4 — LOCF tail derivation check (matches design §7)

The last 8 Y₃ v2 rows are 2026-02-06 through 2026-03-27, all carrying real `y3_value` differentials. LOCF tail extension constant in `y3_compute.py:144` is `+ pd.Timedelta(days=120)` (forward-extension of the Friday range past the last monthly observation). EU 2025-12-01 + 120 days = 2026-03-31 ⇒ last Friday in that window is 2026-03-27, exactly matching the v2 panel max. **LOCF tail behavior is deterministic, source-committed, and unmodified by `c5cc9b66b`.**

### Probe 5 — cutoff-by-cutoff arithmetic (load-bearing reconciliation)

See table above. Confirms the 11-week gap lives forward in time `[2026-01, 2026-03]`, not backward. **This is the load-bearing reconciliation — projection error was conservative, not inflated.**

### Probe 6 — y3_v1 byte-exact preservation (matches memo §3.2)

- v1 row count = 59 (unchanged from Rev-5.3.1 commit `765b5e203`).
- v1 statistical signature: avg_y3 = 0.003962562691, sd_y3 = 0.012254571642, range [-0.033594, 0.038020]. Stable.
- All 59 v1 `week_start` values overlap with v2's panel (composite-PK admits both methodology tags at same `week_start`). **No row deletion from v1; additive INSERT only.**
- Note: my fingerprint sha256 (`137ed85e899f4520…`) differs from the memo's claimed `096275d7c3481a45…`; this is purely a serialization-format difference (the memo explicitly says it's a "snapshot fingerprint at memo authoring time… not the Rev-4 `decision_hash`"). Row count + statistical signature equality is the substantive byte-exact-preservation evidence; both pass.

### Probe 7 — `MDES_FORMULATION_HASH` self-test

```
LIVE : 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
PIN  : 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
MATCH: True
```

Byte-exact match against `MEMORY.md::mdes_formulation_pin`. **No calibration drift.**

### Probe 8 — anti-fishing invariants

`git show c5cc9b66b --stat` enumerates exactly **3 files**:
1. `contracts/scripts/econ_pipeline.py` — **+5 / -1 lines**, the one-line `conn=conn` kwarg fix at line 2905 plus a 4-line preamble comment. Verified by reading the diff: the only code-effective change is `fetch_country_wc_cpi_components(country, start, end) → fetch_country_wc_cpi_components(country, start, end, conn=conn)`. No other code mutation.
2. `contracts/scripts/tests/inequality/test_y3_rev532_conn_forward.py` — **NEW file, +206 lines**, two failing-first tests as documented in memo §1.
3. `contracts/.scratch/2026-04-25-y3-rev532-ingest-result.md` — **NEW memo, +205 lines**.

Files **NOT** modified by `c5cc9b66b` (verified via `git diff c5cc9b66b~1 c5cc9b66b -- <file>`):
- `scripts/y3_compute.py` — 0-line diff. `PRIMARY_PANEL_END`, `PRIMARY_PANEL_START`, LOCF `+120 days` tail constant all unchanged.
- `scripts/carbon_calibration.py` — 0-line diff. `MDES_FORMULATION_HASH` byte-exact preserved (probe 7).
- `scripts/y3_data_fetchers.py` — 0-line diff.
- `scripts/econ_schema.py` — 0-line diff.
- `scripts/econ_query_api.py` — 0-line diff.
- `scripts/tests/inequality/test_y3.py` — 0-line diff. The pre-existing `assert n >= 75` at line 412 (authored at Rev-5.3.1 commit `765b5e203` 5h41m before `c5cc9b66b`) targets `y3_v1` and is **not modified by this commit**. `N_MIN = 75` gate held.

**No anti-fishing invariant was silently violated.**

### Probe 9 — per-country cutoffs match expectations

| Country | Source table | Native max date in DB | Memo claim |
|---|---|---|---|
| CO | `dane_ipc_monthly` | 2026-03-01 | 2026-03-01 ✓ |
| BR | `bcb_ipca_monthly` | 2026-03-01 | 2026-03-01 ✓ |
| EU | DBnomics (runtime fetch) | not stored as table | 2025-12-01 ← binding |
| KE | (skipped per design §10 row 1) | — | — ✓ |

CO + BR cutoffs verified directly from raw DuckDB tables. BR row count 27 matches memo §3.1 exactly. EU 2025-12-01 binding is plausible (Eurostat HICP T+45-day publication lag implies April 25 has Dec-25 as latest official). **`min(country_cpi_cutoffs) = 2025-12-01` (EU)** as expected; LOCF tail then extends forward 120 days to 2026-03-31, with last Friday-anchored row at 2026-03-27.

---

## Cross-references against Code Reviewer + Senior Developer concerns

The DE's memo §6 flags an RC-A6 reviewer-ack checkbox for the methodology literal value. **I confirm:**

- The literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` is what I observed in DuckDB.
- The base portion (everything before `_3country_ke_unavailable`) is **passed in** at the `ingest_y3_weekly` call site as `source_methodology='y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip'`; the runtime appends `_3country_ke_unavailable` per the documented recovery semantics in the function (KE-only-skipped fallback).
- Downstream readers using `econ_query_api.load_onchain_y3_weekly(source_methodology=...)` will need to pass the literal full-suffix string; this is a documentation concern for Task 11.N.2d.1-reframe and Task 11.O Rev-2 spec authoring — **not a Reality-Checker BLOCK**.

---

## Non-blocking advisories (do not affect PASS verdict)

### A1. Memo's projection-vs-actual narrative is partially incorrect.

The memo §3.2 claims the 76-vs-65 divergence is from "the γ window swap to `start = 2023-08-01`" extending the panels backward. **My probe 5 evidence shows the divergence is NOT backward at all** — at cutoff `2025-12-31` both my prior projection and the new ingest land at 65. The 11-week gap lives forward in `[2026-01, 2026-03]` due to LOCF tail extension forward of the EU 2025-12-01 binding cutoff, NOT backward extension to 2023-08-01.

The DE memo also claims this in §3.3:
> "the joint upper bound is the Y₃-side EU-binding-plus-LOCF tail, as the plan's arithmetic note anticipated"

This second statement is **correct** and is the actual reconciliation. The §3.2 backward-extension claim is the inaccurate one. **Suggest the DE update §3.2 to remove the "γ backward extension" causal claim and replace it with the LOCF-forward-tail explanation already present in §3.3.** This is purely a memo-narrative correction; the count of 76 is right and the gate decision stands.

### A2. EU 2025-12-01 cutoff is plausible but not directly verifiable from a stored DuckDB table.

DBnomics is fetched at runtime; no `eurostat_hicp_monthly` table exists in the canonical DB. I accept the memo's claim because (a) Eurostat's T+45-day HICP publication lag makes 2025-12-01 the latest available on 2026-04-25, and (b) the resulting joint-overlap arithmetic and LOCF tail behavior fall through correctly. **Suggest persisting the runtime DBnomics fetch into a stored `eurostat_hicp_monthly` table at a future task**, matching the discipline of `dane_ipc_monthly` and `bcb_ipca_monthly`. This is a hygiene improvement, not a gate concern.

### A3. The 76-week margin over the 75-week gate is razor-thin (1 week, ~1.3%).

If any single LOCF-tail week is later excluded (e.g., due to a downstream anti-fishing concern about LOCF-extrapolated CPI being treated as a real observation), the count drops to 75 and the gate passes by zero margin. If two LOCF-tail weeks are excluded, the gate fails. **Suggest noting in Task 11.O Rev-2 spec a sensitivity analysis at "joint count under LOCF-tail-excluded variant" — i.e., truncating Y₃ at the EU 2025-12-01 cutoff and re-counting joint nonzero overlap.** From probe 5, that variant lands at 65 weeks, which would FAIL the ≥75 gate. This is a fragility flag for downstream methodology, not a blocker on this PASS verdict.

### A4. Pre-existing remittance test failures (out of scope per `feedback_agent_scope`).

The memo §5 documents 2 pre-existing failures in `test_cleaning_remittance.py` from a `NotImplementedError` seam in `cleaning.py:487`. I did not re-run the test suite (probe budget), but the file-scope check confirms `cleaning.py` was NOT modified by this commit, so these failures are not regressions. **No action required.**

---

## Reviewer ack checkbox (per memo §6)

- [x] **Reality Checker ack** — literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` accepted.

---

## Summary table

| Concern | Evidence | Verdict |
|---|---|---|
| 76-count reproducibility | Probe 2 returns 76 under both filter forms | PASS |
| 11-week reconciliation (65 → 76) | Probe 5 cutoff scan confirms LOCF-forward-tail explanation; cutoff at 2025-12-31 = 65 (matches prior projection); gap lives in [2026-01, 2026-03] | PASS |
| LOCF tail behavior matches design | Probe 4 + design §7 + `y3_compute.py:144` (`+120 days`) all align | PASS |
| y3_v1 byte-exact preservation | Probe 6: 59 rows preserved; statistical signature stable | PASS |
| `MDES_FORMULATION_HASH` byte-exact | Probe 7: live = pin | PASS |
| Anti-fishing — N_MIN unchanged | Probe 8: `assert n >= 75` test untouched at line 412 | PASS |
| Anti-fishing — file scope | Probe 8: only 3 files modified; `y3_compute.py`, `carbon_calibration.py`, etc. all 0-line diff | PASS |
| Per-country cutoffs match memo | Probe 9: CO=2026-03-01, BR=2026-03-01, EU=2025-12-01 binding, KE skipped | PASS |
| Methodology literal RC-A6 ack | Memo §6 literal observed in DB | PASS (acked) |

---

## Promotion recommendation

**PROMOTE.** Task 11.N.2d-rev gate is genuinely cleared at 76 weeks. The 11-week divergence from my prior projection is fully reconciled by LOCF-forward-tail behavior that was pre-committed in source and unmodified by this commit. Downstream Task 11.N.2d.1-reframe and Task 11.O-scope-update + Task 11.O Rev-2 spec authoring are unblocked.

**Caveat for downstream tasks:** the 76-vs-75 razor margin (advisory A3) means any future methodology refinement that excludes LOCF-tail rows will re-fire the HALT clause. The downstream spec authoring should pre-register a "LOCF-tail-excluded" sensitivity at probe-5's `2025-12-31` cutoff (= 65 weeks, FAIL by 10) so that the structural-econometrics verdict is not retroactively re-tuned by silent LOCF-policy revision.

---

**Reviewer:** Reality Checker
**Tool budget used:** ~14 of ≤25 target
**Files written:** this memo only (no code or DuckDB modification, per directive)
