# Rev-3 Plan Fix-Log — 3-way Review Consolidation → Rev 3.1

**Date:** 2026-04-23. **Consolidator:** Technical Writer.
**Sources:** CR (BLOCK), RC (NEEDS-WORK), PM (PASS-WITH-FIXES) at `contracts/.scratch/2026-04-20-remittance-plan-rev3-review-{code-reviewer,reality-checker,senior-pm}.md`.
**Scope:** 6 BLOCKs + 10 FLAGs + 9 NITs, in-place. Task IDs preserved. Task count 46 unchanged.

## BLOCK dispositions — all applied in place

| ID | Disposition summary |
|---|---|
| CR-B1 — stale Goal + Tasks 9/10/13 reference obsolete monthly primary | APPLIED. Plan-body amendment riders added to Goal, Task 9 (V1 scalar vestigial; Phase-1.5 Task 11.B authoritative), Task 10 (AR(1) scoped to validation-row S14 quarterly only), Task 13 (`a1r_monthly_rebase` renamed to `a1r_quarterly_rebase_bridge`), Task 23 §7 ("A1-R monthly" → "A1-R-bridge"), Task 30a completion-memory. Task 13 commit message updated. |
| CR-B2 — Task 11.B "6-decimal tolerance" silent-test-pass bait | APPLIED. Task 11.B Step 1 now mandates an **independent reproduction witness** inlined in the test file (no import of `weekly_onchain_flow_vector`); pinned values committed before Step 3 implementation. Step 2 failure mode redefined. Commit message updated. |
| RC-B1 — line-10 "4 MPR PDFs" = evidentiary theater | APPLIED. Rev-3 history bullet rewritten to lead with BanRep suameca series 4150 metadata (`fechaUltimoCargue=2026-03-06`; in-tree provenance `banrep_mpr_sources.md:42-52`). MPR PDFs demoted to corroborating-only negative evidence. |
| RC-B2 — "cCOP + Mento broker" conflates TOKEN vs VENUE | APPLIED. Task 11.A gets new "Data-target disambiguation" block: cCOP TOKEN (ERC-20, transfer events) vs Mento BROKER `0x777a8255…` (swap venue, Dune `#6939814`). Post-2026-01-25 cCOP→COPm migration note added. |
| PM-B1 — In-flight 11.A subagent retroactive-authorization unwritten | APPLIED. New **Rule 14** in Non-Negotiable Rules formalizing frozen-pending-authorization for subagents dispatched before plan-review convergence. Three-scenario disposition enumerated; Task 11.A implementer named. |
| PM-B2 — Task 11.E Rule-13 cycle-cap boundary ambiguous | APPLIED. Step 3 redefined: one cycle = one full 3-parallel-reviewer round-trip + TW consolidation + targeted BLOCK re-dispatch. Dual budget: 3 overall round-trips AND 3 re-dispatches per reviewer. Skill re-invocation does not count as cycle. |

## FLAG dispositions — all applied in place

| ID | Disposition |
|---|---|
| CR-F1 (row-count zero-pad loophole) | Task 11.A Step 1 tightened: ≥720 rows AND ≥500 non-zero rows; NaN-gap ≤3 consecutive days. |
| CR-F2 (Task 11.C missing nbconvert guard) | New Step 4.5 with explicit `subprocess.run([..., "--execute", "--inplace", ...])` + `returncode==0`. |
| CR-F3 (11.D fix-log not input to 11.E) | Task 11.E Step 1 names both patched spec AND fix-log as first-class review inputs. |
| RC-F1 (Dune `#6940691` mislabeled) | Task 11.A Step 3 mandates `mcp__dune__getDuneQuery` schema-verification before execution; mismatches logged to `dune_onchain_sources.md`. |
| RC-F2 (4,913 senders = cCOP-OLD pre-migration stock) | Task 11.A rationale rewritten; "≥4,913 lifetime cleaned-cohort senders (pre-migration)" is the defensible phrasing; post-migration cohort recomputed at acquisition. |
| RC-F3 (95–104 range needs single N) | Pre-committed **N = 95** (conservative floor) named in Task 11.A rationale; cross-referenced in Task 11.D §4.5 MDES patch. |
| PM-F1 (three recovery paths under-specified) | Explicit "Recovery protocol" subsections added to Tasks 11.A (3 failure modes), 11.C (PASS/INCONCLUSIVE/FAIL-BRIDGE), and 11.E (BLOCK-routing decision tree with 4 branches). |
| PM-F2 (Phase-2 overloaded; 11.A-E → Phase 1.5) | New `## Phase 1.5 — Data-Bridge` section inserted between Phase 1 and Phase 2 (textually after Task-11 historical status). New `## Phase 2 — Panel Extension` header before Task 12. Task count summary updated to 5+5+5+5+18+8=46. Phase 2 Rev-2 shape (11,12,13,14,15) restored. Gate clarified: Task 12 failing-test authoring may parallelize; implementation blocked on Task 11.E. |
| PM-F3 (Task 11.C 4-5 X-trio HALTs borderline) | Task 11.C Step 1 decision-gate: 3-HALT if data clean, 5-HALT split into 11.C.1/11.C.2 if complex. Implementer decides at authoring time. |
| PM-F4 (Task 11.D bundles TW + skill without decision gate) | Task 11.D Step 1 opens with classification gate: per-row (5/6/7/8) "wording-only" vs "economic-mechanism change"; mechanism-change requires skill re-invocation before TW continues. Step body reformatted as checkbox checklist. |

## NIT dispositions

- **CR-N1** (filename rename `dune_onchain_flow_fetcher.py` → `…remittance…`): REJECTED as churn; explicit note in Task 11.A Files block.
- **CR-N2** (11.D matrix rows as checklist): APPLIED inside PM-F4 fix.
- **CR-N3** (`flow_directional_asymmetry_w` ambiguous): APPLIED. Per-channel pos-day rule pinned in Task 11.B Step 1.
- **CR-N4** (task-count growth narrative): APPLIED via PM-N1.
- **RC-N1** (`executeQueryById` not named as read-only path): APPLIED in Task 11.A Step 3.
- **RC-N2** ("$200M/mo, 100K Littio users" unverifiable): APPLIED. Non-load-bearing caveat added.
- **PM-N1** (task-count re-baseline): APPLIED. 5-category growth narrative (a-e) with Rev-3 methodology-escalation as (e).
- **PM-N2** (Rev-3 banner doesn't name reviewers): APPLIED. Status line names "Code Reviewer, Reality Checker, Senior PM — same trio as Rev-2 plan review".
- **PM-N3** (11.A fallback scratch-file path unnamed): APPLIED. `contracts/.scratch/2026-04-20-dune-mcp-fallback-log.md` named in Task 11.A Recovery Protocol.

## Positives preserved + verification

All 11 positive findings retained verbatim (causal-chain tightness, three-way review of Rev-1.1 patch, pre-registered ρ-gate thresholds, Dune IDs + 30-credit budget, categorical Phase-2 gate, §12 row mappings accurate, scripts-only scope, subagent assignments, bridge-gate [−1,1] partition, anti-fishing defense, 7-quarter arithmetic).

Plan delta ≈ **+2,100 words** (within +1,500–2,500 target). `grep -c "^### Task "` = 46. Phase headers: 0, 1, 2 (Task 11 historical), 1.5, 2 (Panel Extension), 3, 4 — split intentional per Rev-3.1 structural note.

**Sign-off:** 6 BLOCKs + 10 FLAGs + 8 of 9 NITs applied in place (CR-N1 rejected as churn). Rev 3.1 stands as executable unless the reviewer trio requests verification.
