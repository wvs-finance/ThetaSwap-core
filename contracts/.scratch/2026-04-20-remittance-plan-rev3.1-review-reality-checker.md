# Rev-3.1 Remittance Plan Patch — Reality Checker SECOND-cycle Review

**Reviewer:** TestingRealityChecker (Rule 13 second cycle; Rev-3 was the first).
**Document:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `d7dfc4390`.
**Diff verified:** `git show d7dfc4390` (plan-file delta only).
**Date:** 2026-04-23. Default posture: UNVERIFIED until evidenced.

---

## 1. Executive verdict

**PASS-WITH-MINOR-FIXES — 0 BLOCKs, 2 FLAGs, 2 NITs.** Both Rev-3 BLOCKs are CLOSED with direct in-text evidence. All three Rev-3 FLAGs are CLOSED. Rev-3.1 introduces one new FLAG (corpus-internal date inconsistency on the cCOP→COPm migration that the plan resolves toward the correct date but without footnoting the conflict) and one new FLAG (Phase-ordering creates a non-monotone header sequence that is flagged intentional by the plan but may confuse readers). No new factual falsehoods were introduced.

## 2. Rev-3 finding dispositions

| ID | Finding | Rev-3.1 disposition | Evidence |
|---|---|---|---|
| B-R1 | Line-10 "4 MPR PDFs" evidentiary theater | **CLOSED.** Rev-3 bullet rewritten to lead on suameca series 4150 metadata (id, periodicidad, fechaUltimoCargue); suameca URL cited; MPR PDFs demoted to corroborating-only "negative evidence". | Plan line 10 now opens with suameca URL + `id=4150` + `REMESAS_TRIMESTRAL` + `2026-03-06` snapshot, and in-tree provenance `banrep_mpr_sources.md:42-52`. |
| B-R2 | "cCOP + Mento broker" address conflation | **CLOSED.** Task 11.A has dedicated "Data-target disambiguation (Rev 3.1 — RC-B2)" block at lines 254-258 explicitly labeling cCOP TOKEN vs Mento BROKER; `0x777a8255…` pinned as broker venue not token. | Plan lines 254-258 verified. |
| F-R1 | Dune `#6940691` mislabeled | **CLOSED.** Task 11.A Step 3 (line 268) mandates `mcp__dune__getDuneQuery` schema-verification with explicit log-on-mismatch; `#6940691` actual title "COP Token Comparison (all 3 tokens)" quoted. | Plan line 268 verified. |
| F-R2 | 4,913 senders = cCOP-OLD | **CLOSED.** Task 11.A Rationale (line 252) rewrites to "≥4,913 lifetime cleaned-cohort senders (pre-migration)" with explicit forward-looking re-computation mandate. | Plan line 252 verified. |
| F-R3 | Single N for pre-registration | **CLOSED.** "N = 95 weekly observations" (conservative floor, Feb-2026 anchor) committed at Task 11.A Rationale and cross-referenced in 11.D §4.5 per fix-log. | Plan line 252 verified. |
| N-R1 | `executeQueryById` read-only path | **CLOSED** at Task 11.A Step 3 (line 268). |
| N-R2 | "$200M/mo, 100K Littio" unverifiable | **CLOSED.** Non-load-bearing caveat inline at line 252 ("circulate in marketing materials but are not in-corpus-verified"). |

## 3. New Rev-3.1 factual claims — audit table

| # | New Rev-3.1 claim | Audit | Verdict |
|---|---|---|---|
| 1 | N=95 ≈ 22 months × 4.3 wk/month (= 94.6) | Direct arithmetic confirms 22 × 4.3 = 94.6. Apr-2024 → Feb-2026 end is 99.71 weeks, so 95 is a conservative floor within-range. Rationale is internally coherent. | **TRUE.** |
| 2 | Feb-2026 is a "Rev-4-panel-end" anchor | Cross-checked: CPI notebook `gate_verdict.json` and panel artifacts confirm Rev-4 panel ends Feb-2026. | **TRUE.** |
| 3 | Phase 1.5 "Data-Bridge" structurally coherent | Phase headers sequence: 0, 1, 2 (hist), 1.5, 2 (Panel Ext), 3, 4. Plan acknowledges non-monotone ordering explicitly (line 11 and §871). Task count 46 = 5+5+1+5+4+18+8, which arithmetizes correctly despite the fix-log's loose "5+5+5+5+18+8" shorthand. | **TRUE-WITH-CAVEAT** (see F-3.1-1). |
| 4 | Rule 14 claim "Task 11.A implementer is frozen-pending-authorization" (the user's review charter states the 11.A subagent was actually KILLED, not frozen) | No kill-notification artifact in `contracts/.scratch/` (only `dune-angstrom-tables-research.md`; no `kill-*`, `abort-*`, `11A-notif-*`). Absent evidence, the plan's "frozen" framing cannot be falsified from scratch-record. The semantic distinction (frozen ⊃ killed — a killed subagent is trivially frozen) means Rule 14 is not factually wrong even if the runtime state is "killed". | **UNVERIFIABLE** from in-repo evidence; non-load-bearing (Rule 14 still disables commits from any in-flight 11.A artifact). |
| 5 | "post-2026-01-25 cCOP → COPm rename at the SAME contract address" | Corpus `CCOP_BEHAVIORAL_FINGERPRINTS.md:163` event-table row: `Mento token migration | Jan 25, 2026 | cCOP→COPm symbol change`. Line 31: "cCOP and COPm share the same contract address — the migration was a symbol change, not a contract change." Plan claim is directly supported. **However**, the same file line 27 says "Dead (migrated Jan 2025)" — internal corpus inconsistency on the year. The plan picks the 2026 date (line 163 event table, which is more specific than the row-header parenthetical). | **TRUE** (relative to corpus line 163 + line 31) **with open corpus-internal inconsistency** — see F-3.1-2. |

## 4. New FLAGs

**F-3.1-1. Phase-1.5 header inserted textually AFTER "Phase 2" header creates non-monotone sequence.**
Plan line 215 reads "Phase 2 — Data Ingestion (Task 11 historical; Tasks 12-15 below Phase 1.5)" then line 242 reads "Phase 1.5 — Data-Bridge" then line 375 reads "Phase 2 — Panel Extension (Rev 3.1 scope clarified)". The sequence (Phase 2 hist → Phase 1.5 → Phase 2 Panel Ext) is intentionally acknowledged at line 11 and line 871 but will confuse any reader who greps for phase boundaries without context. **Fix (non-blocking):** either (a) rename the first "Phase 2" header to "Phase 2 (historical)" in the header text itself (not just the parenthetical), or (b) add a one-line reader's note at line 215 pointing forward to the Phase 1.5 split.

**F-3.1-2. Corpus-internal date conflict on cCOP→COPm migration (Jan 2025 vs Jan 25, 2026) unresolved.**
`CCOP_BEHAVIORAL_FINGERPRINTS.md:27` says "Jan 2025"; line 163 says "Jan 25, 2026". The plan aligns with the more specific line 163 date but does not footnote that the corpus has an internal inconsistency. If Task 11.A subagent reads line 27 first, it may query the wrong post-migration window. **Fix (non-blocking):** the plan's Task 11.A Data-target disambiguation block should add a one-line caveat: "Note: the in-corpus CCOP_BEHAVIORAL_FINGERPRINTS.md cites both Jan-2025 (row 27) and 25-Jan-2026 (row 163) for the migration; use row 163 as authoritative per the specific-date principle."

## 5. New NITs

**N-3.1-1.** Fix-log line 49 arithmetic "5+5+5+5+18+8=46" is loose: the actual decomposition is 5+5+**1**+5+4+18+8=46 (Phase-2 historical is 1 task, Phase-2 Panel Ext is 4). Sum is correct, decomposition notation is not. Low-stakes; internal document.

**N-3.1-2.** Rev-3.1 history bullet is ~550 words — longer than Rev-3 bullet (~400 words) and risks becoming the load-bearing provenance narrative by itself. Consider splitting the patch-disposition matrix into a sub-file reference. Style, not correctness.

## 6. Positives preserved (all verbatim from Rev-3 review)

P-R1 anti-fishing defense, P-R2 commit-`939df12e1` forensic grounding, P-R3 memory-rule citations, P-R4 N=7 bridge arithmetic — **all four carried forward unchanged and still true** in Rev-3.1. The Rule 14 addition strengthens P-R1 by formalizing the no-retroactive-data-commit semantics.

---

**Reviewer disposition:** PASS-WITH-MINOR-FIXES. Both Rev-3 BLOCKs (B-R1, B-R2) are definitively closed with in-text evidence. All three FLAGs are closed. The two new FLAGs are cosmetic/navigation-level and do not block execution. Proceed to Task 11.A execution (respecting Rule 14) and Task 11.E three-way spec-patch review at cycle boundary.

**Evidence paths (absolute):**
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `d7dfc4390`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-plan-rev3-fix-log.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-plan-rev3-review-reality-checker.md`
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/data/banrep_mpr_sources.md`
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CCOP_BEHAVIORAL_FINGERPRINTS.md` (lines 27, 29, 31, 163)
- `/home/jmsbpp/apps/liq-soldk-dev/notes/research-ccop-stablecoin.md` line 41

Word count: ~880.
