# MR-β.1 Sub-plan Fix-up Re-review — Reality Checker

**Reviewer:** TestingRealityChecker (Reality Checker, single-pass re-review)
**Date:** 2026-04-26
**Target:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (319 lines, uncommitted; fix-up TW agent `a25d6f5d61211ca41`)
**Prior review:** `contracts/.scratch/2026-04-25-subplan-mr-beta-1-review-reality-checker.md` — NEEDS-WORK with R-1 / R-2 / R-3
**Verdict:** **PASS-with-non-blocking-advisories**

---

## TL;DR

All three NEEDS-WORK findings (R-1, R-2, R-3) are resolved cleanly. Live-DuckDB ground-truth confirms the sub-plan's 14-table count and the per-table enumeration. The supply-field internal contradiction is eliminated by a clean drop-with-redirect (Approach a). The `onchain_copm_ccop_daily_flow` table now carries explicit narrative treatment + per-table disambiguation entry. CORRECTIONS block (§H) records all dispositions with reasons. No anti-fishing invariant relaxed; no scope creep beyond the Rev-5.3.4 RESCOPE; no major-plan / code / DuckDB / memory edits; commit-uncommitted state preserved. Sub-plan is **ready for commit + sub-task dispatch**.

---

## Verification trail (5 tool uses)

### 1. Ground-truth: live DuckDB pre-flight enumeration

Executed against `contracts/data/structural_econ.duckdb` (read-only):

```
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE 'onchain_%' ORDER BY table_name
```

Result: **14 tables** (matching the sub-plan's "14 live `onchain_*` tables" claim).

Live tables:

1. `onchain_carbon_arbitrages`
2. `onchain_carbon_tokenstraded`
3. `onchain_copm_address_activity_top400`
4. `onchain_copm_burns`
5. `onchain_copm_ccop_daily_flow`
6. `onchain_copm_daily_transfers`
7. `onchain_copm_freeze_thaw`
8. `onchain_copm_mints`
9. `onchain_copm_time_patterns`
10. `onchain_copm_transfers`
11. `onchain_copm_transfers_sample`
12. `onchain_copm_transfers_top100_edges`
13. `onchain_xd_weekly`
14. `onchain_y3_weekly`

### 2. R-1 verification — Coverage gap fix landed

| Check | Status |
|-------|--------|
| Pre-flight enumeration query REQUIRED in sub-task 2 | PASS — lines 80–86 (sqlite_master form + DuckDB information_schema equivalent) |
| DIRECT / DERIVATIVE / DEFERRED tagging scheme defined | PASS — lines 88–92 with explicit per-tag definition + audit obligation |
| All 14 live `onchain_*` tables enumerated by name | PASS — backtick-grep against sub-plan returned ≥1 occurrence for each of the 14 tables (lines 96–105) |
| Coverage completeness verifiable via count comparison | PASS — line 133: "count(tagged tables) MUST equal count(rows from pre-flight enumeration query). Any divergence HALTS." |
| HALT on divergence wired correctly | PASS — line 86 + line 133 + acceptance §3 (line 126) |

**R-1 RESOLVED.** Coverage moved from 2/14 (≈14%) to 14/14 (100%). The pre-flight enumeration query is REQUIRED (not optional), the count-comparison is falsifiable, and the divergence path HALTs.

### 3. R-2 verification — `onchain_copm_ccop_daily_flow` disambiguation fix landed

| Check | Status |
|-------|--------|
| Table appears by name in sub-task 2 | PASS — line 97, classified DIRECT |
| 3-part narrative treatment present | PASS — line 97 sub-bullets (a) verify filter addresses, (b) document COPM vs. cCOP-historical-data scope, (c) recommend (do NOT execute) future-revision rename |
| Sub-task 2 acceptance line for this table | PASS — acceptance §7 (line 130): "Treats `onchain_copm_ccop_daily_flow` per RC R-2 explicit narrative treatment …" |
| Sub-task 3 explicit per-table disambiguation entry (NOT aggregated) | PASS — registry doc structure bullet (line 151): "the registry doc carries an **explicit per-table entry** for `onchain_copm_ccop_daily_flow`, recording: (a) … (b) … (c) … This is the single most pointed naming-confusion artifact in the project; it MUST appear by name in the registry doc, not be aggregated into a generic note." |
| §B-2 no-rename invariant preserved | PASS — line 97 + line 151 explicitly forbid execution; recommendation only |

**R-2 RESOLVED.** The most ambiguous artifact in the project (the table whose literal name embeds the cCOP-vs-COPM confusion the rescoped deliverable exists to lock down) now has dedicated narrative treatment in BOTH sub-task 2 (audit obligation) and sub-task 3 (registry doc entry). The `MUST appear by name … not be aggregated into a generic note` clause closes the aggregation-loophole RC originally flagged.

### 4. R-3 verification — Supply-field contradiction fix landed (Approach a)

| Check | Status |
|-------|--------|
| Supply field DROPPED from sub-task 1 per-token field list | PASS — lines 56–62 enumerate ticker, legacy ticker, contract address, deployment date, Mento Reserve relationship, basket-membership, provenance citation; **no supply field** |
| Sub-task 1 carries explicit deletion rationale | PASS — lines 64: "The supply field is **deliberately omitted from the registry**. Total supply moves over time and would conflict with the §B-3 / sub-task 3 byte-exact-immutability invariant …" |
| Sub-task 3 per-token-section bullet excludes total supply | PASS — line 149: "Total supply is **explicitly out of scope** for the registry per RC R-3 immutability hygiene; consumers needing current supply query live DuckDB / Celoscan / Dune at consumption time." |
| Redirect to live sources documented | PASS — lines 64 + 149 both name DuckDB / Celoscan / Dune as the consumption-time query path |
| Byte-exact-immutability claim now honest | PASS — with the only time-varying field removed, §B-3 invariant + sub-task 3 acceptance ("the doc is byte-exact-immutable post-converge") are mutually consistent |

**R-3 RESOLVED.** Approach (a) was the cleanest path; the fix preserves the registry-as-source-of-truth invariant without smuggling in a circulating-supply dashboard. The CORRECTIONS-block disposition (§H R-3) accurately describes the resolution and cross-references the deletion sites.

### 5. CORRECTIONS block (§H) verification

| Required content | Status |
|------------------|--------|
| Records R-1 / R-2 / R-3 resolutions with substantive reasoning | PASS — §H "RC NEEDS-WORK findings — resolutions" (lines 290–294) |
| Records R-4 / R-5 dispositions | PASS — §H "RC non-blocking advisories — disposition" (lines 296–299): R-4 → Reality-Checker spot-check at sub-tasks 1+2; R-5 → registry doc as single annotation target |
| Records CR-A / CR-B / CR-C dispositions | PASS — §H "CR non-blocking advisories — disposition" (lines 301–305) |
| Records TW-A1 / TW-A4 resolutions | PASS — §H "TW peer advisories — disposition" lines 309–310 |
| Records DECLINED dispositions for TW-A2 / A3 / A5 / A6 with reasons | PASS — §H lines 311–315; each decline carries an explicit reason (over-engineering / out-of-sub-plan-scope / premature anchor / load-bearing invariant) |
| Resolution status summary | PASS — §H lines 317–319 explicitly recap convergence state and post-fix-up RC-only re-review path |

**CORRECTIONS block PASS.** The block follows the major-plan Rev-5.3.x CORRECTIONS pattern (record finding + record resolution + cross-link affected lines) and explicitly states which dispositions were declined with reasons. No silent omissions.

### 6. Regression checks — invariants preserved

| Invariant | Status |
|-----------|--------|
| Anti-fishing invariants (§B) preserved | PASS — §B 7 invariants intact (lines 36–42); no relaxation; pathological-HALT path explicitly cited at lines 66, 86, 126, 254, 280 |
| No DuckDB row mutation | PASS — §B-1 (line 36) + §G out-of-scope (line 273) |
| No schema migration / table rename | PASS — §B-2 (line 37) + §G out-of-scope (lines 273, 274) |
| No major-plan edit | PASS — §G out-of-scope (line 272); fix-up touched only the sub-plan |
| No code edit | PASS — §G out-of-scope (lines 274, 275); editorial-only deliverable per §B-5 (line 40) |
| No project-memory file silently rewritten | PASS — §B-4 (line 39) + §G out-of-scope (lines 270, 271); two load-bearing memory files (`project_mento_canonical_naming_2026`, `project_abrigo_mento_native_only`) explicitly excluded from edit scope |
| Rev-5.3.2 published estimates byte-exact | PASS — §B-1 (line 36); commit anchor at line 255 (`799cbc280`) |
| `decision_hash` and `MDES_FORMULATION_HASH` immutable | PASS — §B-1 (line 36) cites both sha256 values verbatim |
| Commit-uncommitted state preserved | PASS — `git status --short` returned `?? docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (untracked, uncommitted) |
| Line count target | PASS — `wc -l` returned 319 lines, matching the user's pre-review brief |
| Rev-5.3.4 RESCOPE honored (no Rev-5.3.3 framing reverts) | PASS — §A explicit RESCOPE statement (lines 19–21) + §B-6 invariant (line 41); §H corrections do not re-introduce the Rev-5.3.3 "correct the project memory naming error" framing |

**No regressions detected.**

---

## Non-blocking advisories (RC re-review)

These do NOT block PASS. Recorded for awareness; orchestrator field-judgment.

- **NB-1 — Sub-task 2 line 99 ("`onchain_copm_burns`, `onchain_copm_mints` — DIRECT or DERIVATIVE; verify per pre-flight schema inspection") leaves the classification under-determined.** This is acceptable because the audit memo's job IS to determine the classification (DIRECT if filtered from raw Transfer events with `from = 0x0…` / `to = 0x0…`; DERIVATIVE if computed from `onchain_copm_transfers`). The audit memo will close this; no sub-plan-authoring fix needed. Recording as advisory only.
- **NB-2 — Line 105 (`onchain_y3_weekly` — DIRECT or DEFERRED depending on whether the Y₃ inequality-differential panel is currently consumed").** Same pattern as NB-1: the classification will be determined at audit-execution time by inspecting current β-track / α-track artifact dependencies. Acceptable under the dispatched-subagent's pre-flight inspection mandate; no sub-plan-authoring fix needed.
- **NB-3 — Line 79 explicitly puts table-comment annotations / loader-docstring edits / `econ_schema.py` schema comments OUT OF SCOPE.** This is the correct R-5 resolution (single-file annotation locus) but means the registry doc is the ONLY place an outsider learns table-to-address linkage. Acceptable given the §B-3 invariant making the registry the authoritative source-of-truth. Future-revision teams may want to consider a one-line table-comment cross-pointer back to the registry path; that is explicitly out-of-scope for THIS sub-plan, which is the right call.

None of these advisories warrant a fix-up cycle.

---

## Verdict

**PASS-with-non-blocking-advisories.**

The sub-plan is ready for:

1. **Commit.** The fix-up made all required corrections; the file is uncommitted and the commit message should reference the R-1/R-2/R-3 resolutions and the §H CORRECTIONS block. Suggested commit subject pattern: `review(abrigo): Rev-5.3.4 Task 11.P.MR-β.1 sub-plan — fix-up converged (R-1/R-2/R-3 resolved, RC PASS-w-adv)`.
2. **Sub-task dispatch.** All five sub-tasks (address inventory → DuckDB audit → registry spec doc → TR corrigendum → safeguard memo) carry crisp acceptance criteria, named subagents, and dependency wiring. Sub-task 1 dispatch can proceed once the sub-plan is committed; the spec-review trio convergence (CR PASS-w-adv + TW peer PASS-w-adv + this RC PASS-w-adv) is the green light per `feedback_three_way_review`.

No further fix-up cycles required from RC. Three NEEDS-WORK findings closed, two RC advisories resolved at lightweight, no anti-fishing invariant relaxed, and the live-DuckDB ground-truth (14 tables) matches the sub-plan's enumeration exactly.

---

**Evidence locations:**
- Sub-plan under review: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (319 lines, uncommitted)
- Live DuckDB ground-truth: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/data/structural_econ.duckdb` (14 onchain_* tables, query in §1 above)
- Prior NEEDS-WORK review: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-subplan-mr-beta-1-review-reality-checker.md`
