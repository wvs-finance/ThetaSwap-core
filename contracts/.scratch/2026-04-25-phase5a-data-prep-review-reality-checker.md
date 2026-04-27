# Reality Checker — Phase 5a Data Engineer Implementation Review

**Commit under review:** `2eed63994` — *feat(abrigo): Rev-5.3.2 Task 11.O Rev-2 Phase 5a — Data Engineer prep*
**Review date:** 2026-04-26
**Reviewer:** Reality Checker (TestingRealityChecker)
**Default verdict:** NEEDS-WORK
**Final verdict:** **PASS-with-non-blocking-advisories**

---

## Reality-check command trail (live, byte-exact, ≤ 20 tool uses)

All probes executed against the working DuckDB at
`contracts/data/structural_econ.duckdb` and the 14 new parquet files at
`contracts/.scratch/2026-04-25-task110-rev2-data/panel_row_*.parquet`. No code,
parquet, or DuckDB rows were modified during this review.

---

## Probe 1 — Joint-nonzero re-derivation from parquet (PASS)

Re-read all 14 parquet files via `duckdb.read_parquet(...)` in a fresh
in-memory connection (zero risk of cross-test fixture contamination), counted
rows + counted `x_d > 0` rows. **Both equal expected** for every populated row,
and the deferred rows 9/10 are empty as the spec requires.

| Row | Spec n  | Parquet rows | x_d>0 count | Status |
|----:|--------:|-------------:|------------:|:------:|
|  1  |  76 *   |      76      |     76      |   OK   |
|  2  |  76     |      76      |     76      |   OK   |
|  3  |  65 *   |      65      |     65      |   OK   |
|  4  |  56 *   |      56      |     56      |   OK   |
|  5  |  76     |      76      |     76      |   OK   |
|  6  |  76     |      76      |     76      |   OK   |
|  7  |  45 *   |      45      |     45      |   OK   |
|  8  |  47 *   |      47      |     47      |   OK   |
|  9  |   0     |       0      |     N/A     |   OK   |
| 10  |   0     |       0      |     N/A     |   OK   |
| 11  |  76     |      76      |     76      |   OK   |
| 12  |  76     |      76      |     76      |   OK   |
| 13  |  76     |      76      |     76      |   OK   |
| 14  |  76     |      76      |     76      |   OK   |

\* = byte-exact spec pre-commitment. **5 of 5 spec-pinned counts match
byte-exact** (76 / 65 / 56 / 45 / 47).

This is the strongest signal in the entire review: the joint-nonzero filter
implemented in `_build_where_clause` + the Friday-anchor reconciliation in
`_translate_weekly_panel_to_friday` (the +4 day shift in the `wp_friday` CTE)
together reproduce the pre-committed counts that were independently audited
by the Reality Checker probe-5 sweep at
`contracts/.scratch/2026-04-25-y3-rev532-review-reality-checker.md`. **The
anti-fishing seal is intact.**

---

## Probe 2 — Friday-anchor invariant on output panels (PASS)

Per-row `EXTRACT(isodow FROM week_start)` audit on every output parquet:

```
Row  1: ALL Friday (isodow=5), n=76
Row  2: ALL Friday (isodow=5), n=76
Row  3: ALL Friday (isodow=5), n=65
Row  4: ALL Friday (isodow=5), n=56
Row  5: ALL Friday (isodow=5), n=76
Row  6: ALL Friday (isodow=5), n=76
Row  7: ALL Friday (isodow=5), n=45
Row  8: ALL Friday (isodow=5), n=47
Row 11: ALL Friday (isodow=5), n=76
Row 12: ALL Friday (isodow=5), n=76
Row 13: ALL Friday (isodow=5), n=76
Row 14: ALL Friday (isodow=5), n=76
Total isodow!=5 violations across all panels: 0
```

The Friday-anchor invariant holds across all 12 populated panels. No
silent-zero-from-anchor-misalignment regression is possible downstream.

---

## Probe 3 — Cross-panel time alignment (Row 1 vs Row 14) (PASS)

Spec promise: Row 14 (`wc_cpi_weights_sensitivity`) is the SAME panel as
Row 1 (primary), with the alternative WC-CPI weighting applied at
**fit time** in Phase 5b. Therefore week_start sets must be set-equal.

```
Row 1 week_start count:  76
Row 14 week_start count: 76
Set equality (Row1 == Row14): True
Row1 \ Row14: []
Row14 \ Row1: []
```

PASS. No leakage of the alternative-weights resampling into the panel
construction stage.

---

## Probe 4 — Deferred rows 9/10 schema integrity (PASS)

Both deferred rows are 387-byte parquet files with **valid 14-column
schema** including a `deferred_reason` annotation column:

```
Row 9 (y3_bond_diagnostic): bytes=387, rows=0
  schema: week_start, y3_value, x_d, copm_diff, brl_diff, kes_diff, eur_diff,
          vix_avg, oil_return, us_cpi_surprise, banrep_rate_surprise,
          fed_funds_weekly, intervention_dummy, deferred_reason
Row 10 (population_weighted): same shape, rows=0
```

Schema-typed empties — Analytics Reporter can read them with the same
`read_parquet` invocation as a populated row and skip on `len(df)==0`.
This is correct deferred-row engineering.

---

## Probe 5 — Outlier preservation (flag-not-remove) (PASS)

Per spec §10 ζ.4 + DE manifest claim, outliers are flagged in the audit
report but **not removed** from the panel. Verified on Row 1 primary:

```
vix_avg:           min=13.28, max=42.24,  |z|>3 count = 1   (kept)
oil_return:        min=-0.127, max=0.304, |z|>3 count = 1   (kept)
us_cpi_surprise:                          |z|>3 count = 2   (kept)
```

Max VIX 42.24 is the early-2025 spike that any outlier-removal would have
silently dropped; it is preserved. PASS.

---

## Probe 6 — Source-table integrity (PASS)

Source-table row counts post-commit:

```
onchain_xd_weekly:    819 rows
onchain_y3_weekly:    291 rows
weekly_panel:        1215 rows
weekly_rate_panel:   1760 rows
```

These are consistent with the live-DuckDB row counts pre-Phase-5a as
referenced in `project_duckdb_xd_weekly_state_post_rev531`. No DE
side-effect on source tables — read-only consumption confirmed by the
ADD-only commit (probe 10).

---

## Probe 7 — Monday-vs-Friday anchor audit (PASS)

```
weekly_panel:        isodow=1 -> n=1215         (Monday-anchored)
weekly_rate_panel:   isodow=5 -> n=1760         (Friday-anchored)
onchain_xd_weekly:   isodow=5 -> n=819          (Friday-anchored)
onchain_y3_weekly:   isodow=5 -> n=291          (Friday-anchored)
```

Confirms the load-bearing assertion in the commit message: **only**
`weekly_panel` is Monday-anchored. The `+ INTERVAL 4 DAY` shift in the
`wp_friday` CTE is therefore the unique correct reconciliation point;
applying it anywhere else (or omitting it) would silently zero the join.
This is the most subtle and most important correctness invariant in the
implementation, and it is correct.

---

## Probe 8 — pyarrow-free parquet readability (PASS)

Live import probe in the contracts venv:

```
pyarrow installed:      False
fastparquet installed:  False
DuckDB read of panel_row_01_primary.parquet succeeded: n=76
```

`COPY ... TO ... (FORMAT PARQUET, COMPRESSION ZSTD)` writes are readable
via `read_parquet(...)` without any of the standard Python parquet
libraries. The DE's claim that this avoids a venv-dependency footgun is
correct, and the Analytics Reporter inherits the same DuckDB-native read
path.

---

## Probe 9 — Test-suite re-run

### Probe 9a — Phase-5 data-prep suite (PASS)

```
$ pytest scripts/tests/inequality/test_phase5_data_prep.py -q
..................                                                       [100%]
18 passed in 0.33s
```

18 of 18. The DE's TDD claim (red→green at the strict-TDD discipline level)
is corroborated.

### Probe 9b — Broader inequality suite (NON-BLOCKING ADVISORY — see §Findings)

```
$ pytest scripts/tests/inequality/ -q
9 failed, 109 passed, 1 skipped in 1.54s
```

The 9 failures are confined to `test_y3_br_bcb_wire.py` and emit
**identical** error messages:

```
duckdb.duckdb.ConnectionException: Connection Error: Can't open a connection
to same database file with a different configuration than existing connections
```

I performed a **bisection** to attribute the regression:

| Run order | Result |
|:---|:---:|
| `test_y3_br_bcb_wire.py` alone | 16/16 pass |
| `test_y3_br_bcb_wire.py` then `test_phase5_data_prep.py` | 34/34 pass |
| `test_phase5_data_prep.py` then `test_y3_br_bcb_wire.py` | 9 fail, 25 pass |
| **`test_y3_default_methodology.py` then `test_y3_br_bcb_wire.py`** | **9 fail, 9 pass** |

**The regression is PRE-EXISTING, not introduced by Phase 5a.** Any test that
consumes the session-scoped `conn` fixture (defined at
`scripts/tests/conftest.py` L321 with `read_only=True`) before BCB-wire's
own `read_only=False` `duckdb.connect(...)` triggers the same
configuration-conflict failure. Phase 5a happens to alphabetically sort
**ahead** of `test_y3_br_bcb_wire.py` (`test_phase5_*` < `test_y3_*`), which
is why the collision now surfaces. The same collision exists for any
earlier conn-fixture user; Phase 5a only made it visible.

**This is a non-blocking advisory**, not a NEEDS-WORK because:
1. Phase 5a did not author or modify the conftest fixture.
2. Phase 5a did not modify `test_y3_br_bcb_wire.py`.
3. Phase 5a did not modify any Y3-BCB ingestion code.
4. The fix (loosen the conflicting connection mode in `test_y3_br_bcb_wire.py`
   or refactor the `conn` fixture to give read-only and read-write callers
   distinct DuckDB process-isolation paths) is **out of scope** for a
   data-prep commit.

**Advisory:** queue a separate fixture-hardening task (suggested name:
"Task 11.O Phase-5a fixture-collision hardening") so the next addition of
a conn-fixture-user does not silently re-trigger this. The DE's commit
message claim of "no regressions in the broader inequality suite (was 100/1
pre-Phase-5a)" is **factually imprecise** — the suite count is now 118 not
100, and the 9 failures, while pre-existing, were latent rather than
observed before Phase 5a. **Recommendation: amend the manifest's claim wording or
file the advisory as a follow-up issue.**

---

## Probe 10 — Anti-fishing trail (PASS)

`git show 2eed63994 --diff-filter=AMD --name-status`:

```
21 A   (Added)
 0 M   (Modified)
 0 D   (Deleted)
```

**Zero modified files.** The commit is byte-strictly ADD-only:

* 1× `scripts/phase5_data_prep.py` (NEW; 355 lines)
* 1× `scripts/tests/inequality/test_phase5_data_prep.py` (NEW; 430 lines)
* 14× `panel_row_*.parquet`
* 5× documentation/audit (`queries.md`, `data_dictionary.md`, `validation.md`,
   `manifest.md`, `_audit_summary.json`)

No edits to:
- `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (spec)
- `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (plan)
- any design / calibration / schema / `econ_query_api.py` / `econ_pipeline.py`
- the `_KNOWN_Y3_METHODOLOGY_TAGS` admitted set

The anti-fishing seal at the spec/plan/design layer is **intact**.

---

## Findings summary

| Probe | Claim                                                       | Verdict |
|:-----:|:------------------------------------------------------------|:-------:|
|   1   | 5/5 spec-pinned joint-nonzero counts byte-exact             | PASS    |
|   2   | All output panels Friday-anchored (isodow=5)                | PASS    |
|   3   | Row 1 ≡ Row 14 week_start sets                              | PASS    |
|   4   | Rows 9/10 empty schema-typed parquets                       | PASS    |
|   5   | Outliers flagged not removed                                | PASS    |
|   6   | Source-table integrity preserved                            | PASS    |
|   7   | Monday-vs-Friday anchor audit confirms +4 day shift correct | PASS    |
|   8   | pyarrow-free parquet round-trip works                       | PASS    |
|   9a  | Phase 5a test suite 18/18                                   | PASS    |
|   9b  | Broader inequality suite                                    | ADVISORY|
|  10   | Commit is ADD-only; no spec/plan/design edits               | PASS    |

---

## Final verdict

**PASS-with-non-blocking-advisories**

The Data Engineer's claim that the panel parquet contents reproduce the
spec-pinned joint-nonzero counts (76/65/56/45/47) byte-exact under live
DuckDB is **corroborated independently by the Reality Checker**. All ten
load-bearing invariants — joint-count reproduction, Friday-anchor invariant,
Row 1 ↔ Row 14 set equality, deferred-row schema integrity, outlier
flag-not-remove, source-table read-only consumption, anchor reconciliation
correctness, pyarrow-free I/O, TDD test pass, and ADD-only commit footprint
— hold under live verification.

The single advisory (probe 9b: surfaced fixture-collision in
`test_y3_br_bcb_wire.py` when run after any session-conn-fixture consumer)
is a **pre-existing latent footgun in `scripts/tests/conftest.py`**, not a
Phase 5a regression. It should be tracked as a follow-up task but does
NOT block Phase 5b dispatch.

### Recommendations to Senior Developer / orchestrator before Phase 5b dispatch

1. **Amend (or memo-correct) the commit-message claim** "no regressions in
   the broader inequality suite (was 100/1 pre-Phase-5a)" to reflect
   probe-9b reality: the suite was 100/1 **on a different test ordering**;
   under the alphabetically-default ordering with Phase 5a present, 9
   pre-existing fixture collisions in `test_y3_br_bcb_wire.py` now surface.
   This is a documentation-fidelity issue, not a code issue.

2. **Queue a non-blocking follow-up task** to refactor the session-scoped
   `conn` fixture (or the read-write callers in `test_y3_br_bcb_wire.py`)
   so that `read_only=True` and `read_only=False` paths can coexist within
   one pytest session without DuckDB connection-config conflicts. Suggested
   approach: per-test in-process DuckDB attach with the canonical file
   open in a single mode, or use `conn.duplicate()` semantics.

3. **Phase 5b can proceed.** All input contracts to Analytics Reporter
   (14 parquet files + manifest + data dictionary + audit summary) are
   correct, byte-exact reproducible, and pyarrow-free readable.

---

**Files relevant to this review (absolute paths):**

* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/phase5_data_prep.py`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/inequality/test_phase5_data_prep.py`
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/conftest.py` (session conn fixture L321; pre-existing collision source)
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/scripts/tests/inequality/test_y3_br_bcb_wire.py` (pre-existing read-write fixture mismatch)
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-data/` (14 parquets + 5 docs)
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (spec; unmodified)
* `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/data/structural_econ.duckdb` (live DuckDB used for verification)
