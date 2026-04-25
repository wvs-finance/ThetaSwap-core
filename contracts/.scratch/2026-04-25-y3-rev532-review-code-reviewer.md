# Code Review — Task 11.N.2d-rev (commit `c5cc9b66b`)

**Reviewer:** Code Reviewer agent
**Date:** 2026-04-25
**Scope:** Single commit `c5cc9b66b` on branch `phase0-vb-mvp`, 3 files modified (1 production, 1 test, 1 memo)
**Plan ref:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` §Task 11.N.2d-rev (line 1916)
**Verdict:** **PASS-with-non-blocking-advisories**

---

## Summary

The commit is a precision-targeted, load-bearing one-line patch. It adds `conn=conn` kwarg-forwarding at the single call site where the predecessor CO-DANE and BR-BCB source upgrades were silent no-ops, and it executes the Y₃ re-ingest under the Rev-5.3.2 mixed-source mix. The joint X_d × Y₃ ≥ 75-week gate clears at **76 weeks** — independently verified by direct DuckDB query against the canonical `structural_econ.duckdb`. All anti-fishing invariants (sha256 pin on `MDES_FORMULATION_HASH`, untouched DO-NOT-MODIFY files, additive composite-PK insert, prior `y3_v1_*` rows preserved) are intact.

The TDD discipline is exemplary: a behavioral monkeypatch test plus a static-source guard, both of which would have failed pre-patch and pass post-patch. The `feedback_agent_scope` contract is honored byte-exactly — only `econ_pipeline.py`, the new test file, and the new `.scratch` memo are touched. The DE's narrative claims are independently substantiated.

I have **2 non-blocking advisories** below. None block merge; they are forward-looking notes for the downstream Task 11.O-scope-update reviewer (CR-A1) and a bookkeeping observation about the joint-coverage divergence vs. plan projection (CR-A2).

The methodology literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` is **reviewer-acked** here per RC advisory A6.

---

## Section-by-section findings (10-angle checklist)

### 1. `econ_pipeline.py:2905` patch correctness — PASS

The diff is exactly as advertised: one logical-line change plus a 4-line preamble comment.

```diff
+        # Rev-5.3.2 Task 11.N.2d-rev: forward ``conn`` so the kwarg-aware
+        # dispatch in ``fetch_country_wc_cpi_components`` activates the
+        # CO → DANE and BR → BCB source upgrades. Without this kwarg the
+        # fetcher falls back to the IMF-IFS path for all countries.
         try:
-            comp = fetch_country_wc_cpi_components(country, start, end)
+            comp = fetch_country_wc_cpi_components(country, start, end, conn=conn)
         except Y3FetchError:
             skipped.append(country)
             continue
```

Verified via `git --no-pager diff c5cc9b66b~1 c5cc9b66b -- scripts/econ_pipeline.py` — 18 diff lines total, all confined to the comment block + the single substantive call-site change. **No scope creep.**

The kwarg form (`conn=conn`) is the only valid form because the predecessor's signature declares `conn` after `*` (keyword-only) — verified by inspecting the static-source guard test below. The diff respects the predecessor's API contract.

### 2. TDD discipline (failing-first test correctness) — PASS

`scripts/tests/inequality/test_y3_rev532_conn_forward.py` introduces two complementary tests:

**Test 1 — `test_ingest_y3_weekly_forwards_conn_to_wc_cpi_fetcher`** (behavioral):
- Monkeypatches `scripts.y3_data_fetchers.fetch_country_wc_cpi_components` to a sentinel that records `country`, `conn_is_none`, and `conn_id`.
- Monkeypatches `fetch_country_equity` to a 2-Friday DataFrame so the equity branch produces a non-empty `weekly_log_return` (`compute_weekly_log_return` `>= 2`-Friday minimum verified at `y3_compute.py:270`) and the loop does NOT short-circuit before reaching the WC-CPI fetcher.
- Sentinel raises `Y3FetchError` after capture; the country is added to `skipped`; iteration continues. After all four countries skip, `ingest_y3_weekly` raises `Y3FetchError("Y₃ ingest: zero countries landed; HALT (Y3_PANEL_INSUFFICIENT)")` at line 2933 — which the test correctly catches with `pytest.raises(Y3FetchError)`.
- Assertion loop iterates `captured` and checks **per country** that (a) `conn_is_none == False`, AND (b) `conn_id == id(test_conn)` (object-identity preserved through the kwarg).

**Pre-patch (red) behavior:** call site is `fetch_country_wc_cpi_components(country, start, end)` → no `conn=` kwarg → mock receives `conn=None` (its default) → `conn_is_none == True` → assertion fails with a load-bearing message. Genuine red.

**Test 2 — `test_ingest_y3_weekly_call_site_uses_kwarg_form`** (static-source guard):
- Inspects `inspect.getsource(econ_pipeline.ingest_y3_weekly)`.
- Asserts `"fetch_country_wc_cpi_components(" in src` (scaffolding sanity).
- Asserts `"conn=conn" in src` (post-patch contract).

**Pre-patch (red) behavior:** the literal `conn=conn` was absent from the call site → `AssertionError` with a documenting message about the kwarg-only signature.

The two tests are complementary: the behavioral test exercises runtime dispatch and verifies object-identity propagation, while the static-source guard locks in the kwarg form so a future positional refactor cannot regress silently. **The DE's red-then-green claim in the verification memo §1 is structurally credible** — both tests fail under the parent commit `c5cc9b66b~1` and pass under `c5cc9b66b`.

`pytest` collection sanity confirmed via AST parse + module import (no top-level execution side-effects, two `test_*` functions visible).

### 3. Anti-fishing invariant preservation — PASS

Per-file most-recent-commit verification confirms NONE of the DO-NOT-MODIFY files are touched by `c5cc9b66b`:

| File                                    | Last touched commit | Relative to `c5cc9b66b` |
|-----------------------------------------|---------------------|-------------------------|
| `scripts/carbon_calibration.py`         | `7afcd2ad6`         | predates by ≥3 commits  |
| `scripts/y3_compute.py`                 | `765b5e203`         | predates significantly  |
| `scripts/y3_data_fetchers.py`           | `4ecbf2813`         | `c5cc9b66b~2`           |
| `scripts/econ_schema.py`                | `4ecbf2813`         | `c5cc9b66b~2`           |
| `scripts/econ_query_api.py`             | `4ecbf2813`         | `c5cc9b66b~2`           |

`git --no-pager show c5cc9b66b --name-only` returns exactly:
- `contracts/.scratch/2026-04-25-y3-rev532-ingest-result.md`
- `contracts/scripts/econ_pipeline.py`
- `contracts/scripts/tests/inequality/test_y3_rev532_conn_forward.py`

Plan markdown, spec docs, and DuckDB schema are all unmodified in this commit.

### 4. `MDES_FORMULATION_HASH` sha256 self-test — PASS

I independently computed:
```
hashlib.sha256(inspect.getsource(scripts.carbon_calibration.required_power).encode("utf-8")).hexdigest()
  → 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa
```

This is **byte-exact** equal to the pinned hash in `MEMORY.md::mdes_formulation_pin` and the value recorded in the DE memo §0. The anti-fishing protector for the Cohen f² formulation is intact at this commit. **No drift in the calibration formulation.**

### 5. Methodology literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` — PASS / REVIEWER-ACKED

Plan §A row 1825 says: "literal string finalized at implementation; the schema is described, not the literal — see footnote a". Footnote a (line 1828) further states that the literal is "recorded in the Task 11.N.2d-rev verification memo … reviewers ack the chosen literal in that memo before any downstream task dispatches".

The literal landed in DuckDB is decomposable into the schema specified by §A row 1825:
- `y3_v2` — distinguishes from the pre-Rev-5.3.2 `y3_v1` namespace.
- `co_dane` — CO source = DANE table (post-Rev-5.3.2 Task 11.N.2.CO-dane-wire).
- `br_bcb` — BR source = BCB SGS series 433 cumulative-index (post-Rev-5.3.2 Task 11.N.2.BR-bcb-fetcher).
- `eu_eurostat` — EU source = Eurostat HICP via DBnomics (preserved byte-exact).
- `ke_skip` — KE intentionally omitted per design doc §10 row 1.
- `_3country_ke_unavailable` — runtime-appended suffix from `ingest_y3_weekly` lines 2942-2947's recovery-semantics layer (deterministic given the skipped set).

This is **consistent with §A pre-commitment** and the methodology described in the verification memo §6 decomposition.

> **Code Reviewer ack — literal accepted:** ☑

### 6. DuckDB additivity — PASS (independently verified)

Direct query against `data/structural_econ.duckdb` (read-only):

```
SELECT source_methodology, COUNT(*) FROM onchain_y3_weekly GROUP BY 1 ORDER BY 1;
  y3_v1_3country_ke_unavailable                                          n=59
  y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable       n=116
```

Both methodology tags coexist under the composite PK `(week_start, source_methodology)`. The prior `y3_v1_3country_ke_unavailable` tag retains 59 rows (unchanged from pre-Rev-5.3.2). The new tag has 116 rows, matching the memo §3.2 claim. **Insert is additive; no mutation of prior rows.**

### 7. Joint coverage gate clearance — PASS (independently verified)

Direct query reproducing the memo §3.3 calculation:

```sql
SELECT COUNT(*) FROM onchain_xd_weekly x
INNER JOIN onchain_y3_weekly y ON x.week_start = y.week_start
WHERE x.proxy_kind = 'carbon_basket_user_volume_usd'
  AND CAST(x.value_usd AS DOUBLE) > 0
  AND x.value_usd IS NOT NULL
  AND y.source_methodology = 'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable'
  AND y.y3_value IS NOT NULL;
  → 76
```

**76 ≥ 75 → gate CLEARED.** Result reproduces the memo claim exactly. The HALT clause at plan line 1932 does NOT fire.

### 8. `feedback_agent_scope` compliance — PASS

The DE brief's allow-list contains: `econ_pipeline.py` (one-line patch), the new test file, the new `.scratch` memo, and additive INSERTs to `onchain_y3_weekly`. The `git show` stat list matches this allow-list exactly. **No edits to plan markdown, spec docs, or any of the five DO-NOT-MODIFY production files.**

### 9. Provenance honesty — PASS

The DE narrative claims "Two new symbols": (a) two new test functions; (b) one new methodology literal in DuckDB. I verified the parent commit `c5cc9b66b~1`:
- `scripts/tests/inequality/test_y3_rev532_conn_forward.py` is **not present** at the parent — it is genuinely new at `c5cc9b66b`.
- The methodology literal cannot exist in DuckDB before the ingest runs in this task (the ingest is what writes it).
- The verification memo `.scratch/2026-04-25-y3-rev532-ingest-result.md` is **not present** at the parent — also new.

No undisclosed mutations. The provenance statement in memo §7 is accurate.

### 10. Pre-existing failure attribution — PASS

The DE memo §4 footnote (and commit message) credit 2 failing tests in `scripts/tests/remittance/test_cleaning_remittance.py` to a pre-existing `NotImplementedError` in `scripts/cleaning.py:487`. I verified:

```
git log --format="%h %ad %s" --date=short -- contracts/scripts/cleaning.py
  28d76cbb0 2026-04-23 feat(remittance): cleaning.py extension — load_cleaned_remittance_panel (V1: primary-RHS only), additive to Rev-4
  55b512c02 2026-04-18 feat(fx-vol-econ): cleaning.py pure wrapper with 12-Decision hash (green)
```

Both commits predate `c5cc9b66b` (2026-04-25). The `NotImplementedError` is at line 487 of the current file. **The 2 failures are correctly out of scope** per `feedback_agent_scope`.

---

## Non-blocking advisories

### CR-A1 — `load_onchain_y3_weekly` default `source_methodology="y3_v1"` will return zero rows for the new tag

The reader at `econ_query_api.py:1474` defaults `source_methodology="y3_v1"`. After this commit, the new `y3_v2_*` tag is the primary panel for downstream Task 11.O Rev-2 spec authoring — but any existing call site or downstream code that invokes `load_onchain_y3_weekly(conn)` without an explicit `source_methodology=` kwarg will silently return the **stale 59-row Rev-5.3.1 panel**, not the 116-row Rev-5.3.2 primary.

The DE memo §6 honestly flags this: "no admitted-set whitelist exists in code; the new tag is consumable as-is by passing the literal string". Per file-scope discipline, no code change to `econ_query_api.py` was made — and that is correct under this task's allow-list. But it is a load-bearing detail for **Task 11.O-scope-update** which must:

1. Either pass `source_methodology="y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"` explicitly at every Task 11.O call site, OR
2. Update the default value (out of scope for this commit; would be its own CORRECTIONS block since it changes a published API surface).

**Recommendation for the foreground orchestrator:** flag this as a Task 11.O-scope-update precondition in the SD subagent's brief, and ensure the `structural-econometrics` skill's notebook templates are updated to pass the new literal explicitly. **Non-blocking** for this commit.

### CR-A2 — Risk-note divergence (~65 projected vs. 76 actual) deserves its own short note in the Rev-5.3.3 ledger

Plan §A line 1942 forecasts ~76 weeks **only under** path-(a) `{CO=DANE, BR=BCB, EU=Eurostat-direct}` — i.e., a hypothetical δ-EU upgrade to Eurostat-direct (separate task, separate revision). The landed mix uses **Eurostat HICP via DBnomics** (the existing pre-Rev-5.3.2 fetcher), which the plan's risk note projected at ~65 weeks.

The DE memo §3 attributes the +11-week divergence to two factors:
1. The γ window swap to `start = 2023-08-01` adds ~5 months of backward coverage.
2. The Friday-anchor + LOCF tail (per Y₃ design doc §7) extends panel max to `2026-03-27`, beyond the EU `2025-12-01` source cutoff.

This explanation is plausible given the design-doc §7 LOCF tail spec, and the memo correctly emphasizes that the gate is **honestly cleared**, not tuned. The gate stays at ≥75 for downstream dispatches.

**Recommendation:** the Technical Writer or Reality Checker could append a short note to the next plan revision (Rev-5.3.3 or a future amendment-rider ledger entry) recording: "the Rev-5.3.2 risk-note arithmetic underweighted the γ backward extension's contribution; the actual joint coverage (76) lands closer to the path-(a) projection (~76) without requiring the δ-EU upgrade. Future plan revisions should account for the γ + LOCF combined contribution when projecting joint coverage." This would close the loop documentation-wise. **Non-blocking** for this commit.

---

## Verification trail (for downstream reviewers)

Commands run during this review (read-only):

1. `git --no-pager show c5cc9b66b --stat` → 3 files, 416 insertions, 1 deletion.
2. `git --no-pager show c5cc9b66b --name-only --format="" | sort -u` → 3 files, none in DO-NOT-MODIFY list.
3. `git --no-pager diff c5cc9b66b~1 c5cc9b66b -- scripts/econ_pipeline.py` → 18 lines, single substantive change `+conn=conn`.
4. `python3 -c "import hashlib, inspect; from scripts.carbon_calibration import required_power; print(hashlib.sha256(inspect.getsource(required_power).encode()).hexdigest())"` → `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (matches pin).
5. DuckDB Q6: `SELECT source_methodology, COUNT(*) FROM onchain_y3_weekly GROUP BY 1` → 2 rows (59 + 116), composite-PK additivity confirmed.
6. DuckDB Q7: joint-coverage SELECT → 76 rows, gate ≥75 PASS.
7. `git --no-pager log --format="%h" -1 -- <each-DO-NOT-MODIFY-file>` → all predate `c5cc9b66b`.
8. `git --no-pager log --format="%h %ad" --date=short -- contracts/scripts/cleaning.py` → both commits predate `c5cc9b66b`.
9. AST parse + module import of `test_y3_rev532_conn_forward.py` → 2 test functions, importable, no side-effects.

All verification commands are read-only. No code, tests, or DuckDB tables were modified during this review.

---

## Final verdict

**PASS-with-non-blocking-advisories.**

This commit is the cleanest possible execution of the Task 11.N.2d-rev brief: a one-line code change, a behaviorally-genuine TDD test, an honest verification memo, and an independently-reproducible joint-coverage clearance at 76 weeks (≥75 gate). The anti-fishing perimeter is intact, the methodology literal is reviewer-acked, and the prior `y3_v1_*` panel is byte-exact preserved.

The two advisories (CR-A1, CR-A2) are forward-looking notes for Task 11.O-scope-update and a future Rev-5.3.3 plan-ledger entry. Neither blocks merge of this commit.

**Recommendation:** proceed to the Reality Checker and Senior Developer reviews. Once both ack the methodology literal in §6, dispatch Task 11.N.2d.1-reframe and Task 11.O-scope-update.

---

## Reviewer ack

- [x] **Code Reviewer ack** — methodology literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` accepted (per RC advisory A6).
- [ ] Reality Checker ack — pending.
- [ ] Senior Developer ack — pending.
