# Code Reviewer — Rev-5 Plan Review

**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `8db00fe74`
**Baseline:** `28e0ba227` (Rev-4.1)
**Date:** 2026-04-24

## 1. Verdict

**ACCEPT-WITH-FIXES** — Rev-5 is structurally sound and the DuckDB migration is pattern-fit, but four code-level issues must be addressed before dispatching Tasks 11.M.5 / 11.N / 11.Q: task-count miscount, hidden schema-mutation pathway not tested, Goal-line drop of remittance framing leaves upstream Tasks 11.A/B/C with orphaned purpose, and retired-task headers insufficiently demarcated for deep-link readers.

## 2. Findings

### CR-P1 [BLOCKER] — Task-count arithmetic wrong in both places

**Location:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md:3` (status banner "**Task count: 53**") vs `:17` (Rev-5 history bullet "Task count: **54** (51 − 4 retired + 7 new)").

**Issue:** I enumerated `### Task` headers: Phase 0 = 5 (1–5); Phase 1 = 3 (6,7,8); Phase 2a = 3 (9,10,11); Phase 1.5 = 5 (11.A–E); Phase 1.5.5 **active** Rev-5 = 11.F, 11.K, 11.L, 11.M, 11.M.5, 11.N, 11.O, 11.P, 11.Q = **9**; Phase 2b = 4 (12,13,14,15); Phase 3 = 18 (16, 17a/b/c, 18, 18a, 19, 20, 21a/b/c, 21d, 22a/b, 23, 24a/b, 24c); Phase 4 = 8 (25–30c). Total = 5+3+3+5+9+4+18+8 = **55**. Status banner says 53; history says 54. Neither matches. Arithmetic in the history bullet ("51 − 4 retired + 7 new") also errs: 51 − 4 = 47, + 7 = 54 — but Rev-4.1 baseline had 51 active tasks, and L/M/M.5/N/O/P/Q is 7 new, so expected active = **54**; my count of 55 means one active task is double-counted OR the status banner is just wrong. Likely the status banner "53" should be "54" (matches history), and my 55 reflects one inadvertent extra header.

**Fix:** reconcile to a single number. Recommend: recount by executing `grep -c '^### Task ' contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` minus the 4 retired headers, update both `:3` and `:17` to the same integer, and add a one-line enumeration-by-phase in the status banner for reviewer audit.

### CR-P2 [MAJOR] — Task 11.M.5 additive-only test insufficient

**Location:** Task 11.M.5 Step 1 (`:96`).

**Issue:** Step 1(c) asserts Rev-4 CPI `decision_hash` is byte-exact post-migration. This catches new columns/tables injected into the existing view, but does NOT catch (i) `ALTER TABLE banrep_trm_daily ADD COLUMN …` issued by a careless migration, then immediately dropped; (ii) `CHECK` constraint rewrites on `fred_daily` that mutate validated-value semantics without touching existing rows (e.g., `CHECK (series_id IN ('VIXCLS','DCOILWTICO','DCOILBRENTEU'))` → adding a fourth id); (iii) DDL that re-orders columns via `CREATE OR REPLACE TABLE` with row-for-row identical content. `decision_hash` in `nb1_panel_fingerprint.json` is a Pandas-side value-checksum; it won't detect schema-level drift.

**Fix:** Step 1 must add a **schema-fingerprint assertion** independent of row values: capture `conn.execute("DESCRIBE <table>").fetchall()` for each of `EXPECTED_TABLES` in `econ_schema.py:14` pre-migration and assert byte-exact post-migration (column names, types, constraints, `NOT NULL`, PK, CHECK expressions). This is the only way to catch schema drift in an additive-only claim.

### CR-P3 [MAJOR] — 11.G/H/I/J deep-link hazard

**Location:** `:477` (retirement banner) vs `:483`, `:515`, `:535`, `:553` (individual task headers).

**Issue:** Only Task 11.G's heading has the `— ⟨RETIRED Rev-5⟩` suffix. Tasks 11.H, 11.I, 11.J retain clean `### Task 11.H:`/`### Task 11.I:`/`### Task 11.J:` headers (lines 515, 535, 553). An implementer or subagent deep-linking to `#task-11h-non-stop-filter-iteration…` via markdown anchor will land on a section with no retirement warning visible above the fold. The banner at :477 is 38 lines above 11.H; if a subagent's context window only includes lines 515+, it will mistake 11.H for active work.

**Fix:** append ` — ⟨RETIRED Rev-5⟩` to headings at `:515`, `:535`, `:553`. Optionally, add a 1-line banner immediately after each heading: `> **RETIRED** (Rev-5): see retirement block at §Phase 1.5.5 Task 11.G.`

### CR-P4 [MAJOR] — Goal-line drop orphans Task 11.A/B/C rationale

**Location:** `:22` (Rev-5 Goal) vs `:253` (Task 11.A title: "Daily on-chain COPM + cCOP flow acquisition"), `:286` (11.B "Weekly rich-aggregation module"), `:307` (11.C "Bridge-validation notebook (pre-registered ρ-gate)").

**Issue:** Rev-5 Goal drops remittance framing and pivots to inequality-differential, but 11.A/B/C were authored under Rev-3 explicitly as the BanRep-quarterly bridge-validation path for remittance (11.C's name literally says "ρ-gate"). Post-pivot, 11.C's "validation anchor = BanRep quarterly remittance" rationale is stale: the inequality-differential exercise does not validate against BanRep remittance. Yet these tasks are not marked retired (because 11.A/B produced infrastructure Rev-5 reuses via 11.M.5). This creates an ambiguity: is 11.C active? Its DONE_WITH_CONCERNS state at `91e5d2664` suggests yes — but its output (ρ=0.7554, sign=2/5) is now irrelevant to the pivoted objective.

**Fix:** add a one-line status marker at `:307` (11.C heading): `— ⟨HISTORICAL Rev-5⟩ (output preserved as provenance; no longer gating)`. Alternatively amend the Rev-5 Goal at `:22` to explicitly state 11.A/B artifacts are inherited as provenance and 11.C's validation is no longer load-bearing.

### CR-P5 [MINOR] — 11.N I/O contract end-to-end typed

**Location:** `:637` (Task 11.N Step 3).

**Issue:** Step 3 specifies `compute_weekly_xd(per_tx_frozen_dc, friday_anchor_tz)` returning "frozen-dataclass weekly panel". The input type should explicitly reference the `load_onchain_copm_transfers()` return type declared in Task 11.M.5 — otherwise there's a typing gap: 11.M.5 declares `load_onchain_copm_*()` returns "typed frozen dataclasses" but doesn't name the class. Without a shared type name, 11.N's Data Engineer could introduce a parallel dataclass and the contract would silently diverge.

**Fix:** 11.M.5 Step 4 (`:99`) must name the returned dataclass types (e.g., `CopmTransfersTable`, `CopmMintsTable`, …) in the step text so 11.N can reference them by name.

### CR-P6 [MINOR] — 11.O MDES independent-reproduction witness under-specified

**Location:** `:656` (Task 11.O Step 3).

**Issue:** "Verify with an independent-reproduction witness (second compute path via `statsmodels.stats.power.FTestPower` or manual non-central-F root-find)." is offered as alternatives. Task 11.H Step 2 (retired but the pattern carried over) used "match to the sixth decimal" as the tolerance. 11.O gives no tolerance. A witness without a match tolerance is non-assertion.

**Fix:** add explicit tolerance: `|λ_scipy − λ_witness| < 1e-6` (absolute) or relative `< 1e-8`. Also require BOTH witnesses (statsmodels + manual root-find), not one of the two, because if the analytical approximation that produced the Rev-1.1.1 error matches the primary compute it wouldn't catch the error.

### CR-P7 [MINOR] — 11.L → 11.O enforcement is procedural, not mechanical

**Location:** `:570` banner ("output is MANDATORY input to Task 11.O") and `:648` (11.O input list).

**Issue:** 11.O Inputs list names 11.L's report as first input, and the skill invocation in Step 1 "consumes Task 11.L recommendations." But nothing prevents the orchestrator from dispatching 11.O before 11.L's commit lands. Compare 11.P's Gate line (`:680`): "Phase 2b Task 12 … is blocked until …" — that's a mechanical gate. 11.O has no equivalent gate pointing at 11.L's commit.

**Fix:** add a Gate line to 11.L: `**Gate:** commit hash of 11.L report is an explicit prerequisite in 11.O Step 1's pre-flight check; 11.O Step 1 FAILS if the commit hash is absent from its input-manifest log.`

## 3. DuckDB-pattern-fit audit — Task 11.M.5

**PATTERN-FIT: YES, with fixes above.** Cited evidence:

- `econ_schema.py:14` declares `EXPECTED_TABLES: Final[frozenset[str]]` and `_ALL_DDL: Final[tuple[str, ...]]` at `:144`. Task 11.M.5 Step 2 adding 5 new tables is consistent — it must extend both constants.
- `econ_schema.py` uses `CREATE TABLE IF NOT EXISTS` with `PRIMARY KEY` + `_ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp`. Task 11.M.5 should follow this convention: the Step 2 text says "varbinary for addresses, timestamp for dates, uint256 for amounts" — DuckDB has no `uint256`; the appropriate types are `UBIGINT` / `HUGEINT` / `DECIMAL(38,0)` / `VARCHAR` (Dune wei-unit strings). This needs correction before Step 2 dispatches.
- `econ_pipeline.py:17` `log_manifest(...)` pattern is INSERT-only with SHA-256. Task 11.M.5 Step 3 ingestion MUST call `log_manifest` for each CSV ingested (not described in the task text — add this).
- `econ_query_api.py:52` declares `@dataclass(frozen=True, slots=True)` result types (e.g., `ManifestRow`, `DateCoverage`); functions take `conn: duckdb.DuckDBPyConnection` as first arg. Task 11.M.5 Step 4 `load_onchain_*()` signatures must match: `def load_onchain_copm_transfers(conn: duckdb.DuckDBPyConnection, start: date | None = None, end: date | None = None) -> CopmTransfersTable:`.
- `econ_query_api.py:81` uses a private `_check_table` guard. Task 11.M.5 Step 4 must reuse `_check_table` inside each new loader.

## 4. Task-count recount

| Phase | Range | Active count |
|---|---|---|
| Phase 0 | 1–5 | 5 |
| Phase 1 | 6–8 | 3 |
| Phase 2a | 9, 10, 11 | 3 |
| Phase 1.5 | 11.A–E | 5 |
| Phase 1.5.5 (Rev-5 active) | 11.F, 11.K, 11.L, 11.M, 11.M.5, 11.N, 11.O, 11.P, 11.Q | 9 |
| Phase 1.5.5 (RETIRED) | 11.G, 11.H, 11.I, 11.J | 0 (retired) |
| Phase 2b | 12–15 | 4 |
| Phase 3 | 16, 17a/b/c, 18, 18a, 19, 20, 21a/b/c, 21d, 22a/b, 23, 24a/b, 24c | 18 |
| Phase 4 | 25, 26, 27, 28, 29, 30a/b/c | 8 |
| **TOTAL ACTIVE** | | **55** |

Claimed in status banner: **53**. Claimed in Rev-5 history bullet: **54**. My enumeration: **55**. Discrepancy flagged in CR-P1.

---

**End of report.** Findings: 1 BLOCKER (CR-P1), 3 MAJOR (CR-P2, CR-P3, CR-P4), 3 MINOR (CR-P5, CR-P6, CR-P7).
