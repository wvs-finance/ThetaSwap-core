# Rev-3 Plan Review — Senior PM (independent)

**Reviewer:** Senior Project Manager (independent, one of three parallel reviewers)
**Document:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `6034b360f`
**Scope:** Rev-3 patch only (Tasks 11.A–11.E + gating language + task-count update). Methodology of Rev-1.1 is out of scope (that is Task 11.E's review).
**Baseline:** Rev-2 PM estimate was 40 subagent-hours / 31–47 wall-clock hours (see `contracts/.scratch/2026-04-20-remittance-plan-review-senior-pm.md:61-77`).

---

## 1. Executive verdict

**PASS-WITH-FIXES.**

Rev-3 is an honest, methodologically coherent response to a real-world data discovery (BanRep publishes remittance quarterly, not monthly). The 5-task insert (11.A–11.E) is the right shape: acquire daily X, aggregate richly, bridge-validate, patch the spec, three-way-review the patch. The anti-fishing framing ("pivot in response to data-reality, not to a null result") is defensible because: (a) Task 11 committed `DONE_WITH_CONCERNS` before any Phase-2+ estimation ran, so no β̂ has been seen; (b) the Rev-1 spec was explicit that monthly-cadence primary was conditional on public-availability, which failed; (c) the original monthly formulation is being *superseded* in `§4.1`, not being *replaced after the fact* with a rescue alternative.

The plan is executable, but four fixes are needed before Task 11.E converges: recovery-path ambiguity (11.A Dune free-tier), under-specified Rule-13 application to 11.E, silence on retroactive authorization of the in-flight 11.A subagent, and Phase-2 boundary over-loading that obscures the parallelism Rev-2 PM F4 explicitly granted.

---

## 2. BLOCK findings

### B1. Retroactive-authorization semantics of the in-flight 11.A subagent are unwritten.

As of `6034b360f`, a 11.A implementer is already running (launched before plan commit). The plan's Gate at Task 11.E says "Tasks 12+ shall NOT resume until 11.E PASSes" but says nothing about what happens if 11.A's in-flight subagent returns artifacts before 11.E exists, nor whether those artifacts can be committed, nor whether they count toward Rule-13's cycle cap.

**Three scenarios the plan must disambiguate:**
1. 11.A subagent completes successfully before 11.E runs → are the CSV + loader committed under the Task-11.A commit message? Or held until 11.E PASSes?
2. 11.A subagent fails (Dune free-tier hit) → does the foreground re-launch per the fallback (Step 7 note), or does 11.E review the failure-mode choice first?
3. 11.A subagent returns `DONE_WITH_CONCERNS` (as Task 11 did) → is that a Task-11.E input, or does it halt?

**Fix:** Task 11.A header needs one paragraph: "In-flight dispatch clause — the 11.A subagent launched at `<hash>` is authorized to commit its artifacts under this task's commit message if and only if its artifacts satisfy Step-1's failing-test assertions. Those artifacts remain speculative (unused by downstream tasks) until Task 11.E PASSes, at which point they retroactively become load-bearing. If 11.A returns fallback/no-data, Task 11.E input the failure mode + proposed remediation."

### B2. Task 11.E's Rule-13 cycle-cap boundary is ambiguous.

Rule 13 caps "iterate to PASS" loops at 3 cycles. The plan says 11.E Step 3 "Rule 13 applies; escalate to user if not converging." Unwritten: does "cycle" mean (a) 3 re-dispatches of the *same reviewer* who BLOCKed, (b) 3 round-trips of *all three reviewers together*, or (c) 3 attempts at the Rev-1.1 spec-patch itself (i.e., 3 Task-11.D → 11.E pairs)?

Rev-4's spec-derivation costed 12 cycles (noted in Rev-2 plan Rule 13 justification). If the cap is interpretation (c), any genuine methodology re-derivation during 11.E will blow the cap on its first misfire. If (a), the plan is fine. If (b), the plan drastically under-budgets review cost.

**Fix:** Task 11.E Step 3 explicitly names the cycle unit. Recommend (a) per-reviewer re-dispatches capped at 3, with the overall Task 11.D ↔ 11.E loop capped at 3 as a second budget. Document both budgets numerically.

---

## 3. FLAG findings

### F1. Recovery paths for three distinct Rev-3 failure modes are under-specified.

Three failure modes are worth explicit plan text:

- **11.A Dune MCP free-tier exhausted.** The Step-7 note says "document errors + propose fallback (manual Dune CSV paste / Celo RPC)." That is a hand-off, not a decision. Who decides which fallback? The foreground? A fresh user-escalation? If paste-in, does that still satisfy the Step-1 "non-empty `source_query_ids`" assertion? The test spec in 11.A asserts determinism — a paste-in CSV is fine for determinism but the provenance log (`dune_onchain_sources.md`) semantics shift.
- **11.C bridge-gate returns FAIL-BRIDGE.** The plan says "primary regression still runs; economic-interpretation narrative shifts from remittance to crypto-rail income-conversion." That shift has downstream effects: the design-doc anti-fishing framing ("Phase-A.0 is the remittance external-inflow channel") weakens. Does FAIL-BRIDGE trigger a second Rev-1.1.1 spec patch to re-scope the X interpretation? Or is the shift confined to the completion memory (Task 30a)?
- **11.E returns BLOCK from any reviewer.** Task 11.E Step 3 names this. But the plan does not say whether a BLOCK from Code Reviewer (e.g., "file path wrong") vs Reality Checker (e.g., "cited paper doesn't exist") vs Technical Writer (e.g., "ambiguous supersedes banner") each route to the same fix-cycle or to different responders. Rev-2 handles this cleanly via "Technical Writer consolidates" (Task 5 pattern); Task 11.E Step 2 says "Consolidate via Technical Writer; apply all BLOCKs + FLAGs in place" which is good — but a methodology BLOCK should escalate to `structural-econometrics` skill per Task 5's precedent, and that path is unwritten for 11.E.

**Fix:** Add a "Failure-mode decision tree" sub-section to Task 11.A Step 7, Task 11.C Step 3, and Task 11.E Step 3.

### F2. Phase-2 boundary is overloaded; 11.A–11.E should be promoted to a Phase 1.5 "Bridge" sub-phase.

Rev-3 Phase 2 now spans: Task 11 (done), 11.A–11.E (5 new tasks), 12, 13, 14, 15 (4 original). That is 10 tasks spanning two distinct workstreams — (i) data-acquisition-and-spec-patch (11.A–E) and (ii) panel-extension-and-hash (12–15). Rev-2 PM F4 explicitly said "11 and 12 share no code dependency, can run in parallel." Rev-3's gate ("Phase 2+ does not resume until 11.E PASSes") silently retracts that parallelism, because Task 12 is now inside "Phase 2+" and therefore blocked.

**Two candidate fixes:**
- **Preferred:** promote 11.A–11.E to "Phase 1.5 — Bridge" (5 tasks between Phase 1 and Phase 2). Task 12/13/14/15 remain in Phase 2 and become unblocked once Phase 1.5 closes. The Rev-2 F4 parallelism of Task 12 with Task 11 is preserved by qualifying "can run in parallel after Phase 1.5 Task 11.B commits the dataclass-consuming interface."
- **Alternative:** keep 11.A–E inside Phase 2 but clarify the gate: "Tasks 12, 13, 14, 15 may begin in parallel with 11.A–E's test-authoring Steps, but no Phase-3 task may begin until 11.E PASSes." This preserves Rev-2 F4's parallelism but requires the gate text to be far more surgical.

### F3. Task 11.C granularity is borderline under-scoped given X-trio HALTs.

11.C specifies "4-5 X-trio cells" with HALT between each. At ~5-10 min per HALT for foreground review + decision, that is 20-50 min of review alone, before subagent work. The plan's per-task atomicity ceiling (implied 30-60 min) is at the upper bound. The 11.C task description also bundles: (i) test authoring, (ii) notebook authoring, (iii) nbconvert-execute, (iv) scratch-log verdict emission. That is four distinct concerns — comparable to Task 18 (NB1 §3-5, which is already considered substantial in the Rev-2 review).

**Fix (recommendation, not a block):** split 11.C into 11.C.1 (notebook §1-2: alignment + quarterly aggregation) and 11.C.2 (notebook §3-4: Pearson + verdict). Precedent: Rev-2 B3 split Task 17 into 17a/17b/17c for the same atomicity reason.

### F4. Task 11.D bundles TW + optional structural-econometrics re-invocation without a decision gate.

Task 11.D header says: "Technical Writer (amendment) + structural-econometrics skill re-invocation if any new methodology decision surfaces." The Step 2 language ("Any methodology-row whose resolution is unclear gets escalated") is good, but Step 1's concrete work (patch in place, add supersedes banner, update 4 matrix rows) is all TW-level. The skill re-invocation is buried as a conditional inside Step 2. If the skill *does* need re-invocation (plausible — §4.5 MDES at new N_eff is a methodology decision), Task 11.D silently doubles in duration.

**Fix:** either split into 11.D.0 (TW-only textual patch) + 11.D.1 (conditional skill re-invocation for flagged rows), or add an explicit Step 0 that enumerates which matrix rows require re-derivation and which are textual-only. This gives the foreground an up-front decision rather than a mid-task surprise.

---

## 4. NIT findings

### N1. Task-count-growth narrative at §"Total task count (Rev-3): 46" inherits a Rev-2 comparison to "Rev-4 CPI 33-task" without re-baselining.

Rev-2 ended at 41 tasks (correctly labeled). Rev-3 adds 5 → 46. The closing paragraph still references "Rev-2 remittance is 41 tasks — slightly higher than Rev-4" and doesn't update the Rev-3 framing. Minor readability issue.

**Fix:** update the closing paragraph to reflect 46 tasks and state the 5-task growth attribution = Rev-3 methodology escalation.

### N2. The phrase "Rev 3 patch is awaiting three-way plan review" appears twice (frontmatter + Revision history) but does not name the three reviewers.

Elsewhere the plan is scrupulous about naming reviewer identities (per-reviewer focus blocks in Tasks 18a/21d/24c/28 are a standout). The Rev-3 banner should name: Code Reviewer + Reality Checker + Senior PM, matching this very review.

**Fix:** one-line append "(reviewers: Code Reviewer, Reality Checker, Senior PM — same trio as Rev-2 plan review)."

### N3. Fallback text in 11.A Step 7 uses "document attempted URLs + MCP errors" but no scratch-file path is named.

Other tasks use the `contracts/.scratch/` convention. 11.A's fallback leaves the error log unplaced.

**Fix:** name the scratch path — e.g., `contracts/.scratch/2026-04-20-dune-mcp-fallback-log.md`.

---

## 5. Estimated subagent-hours + wall-clock added by Rev 3

**Baseline (Rev-2):** 40 subagent-hours / 31–47 wall-clock hours.

**Rev-3 additions (5 tasks):**

| Task | Subagent-hours | Wall-clock | Notes |
|---|---|---|---|
| 11.A | 2–3 (DE + MCP I/O; unbounded on retry if free-tier hit) | 2–4 | Real-world I/O is the cost driver; Fallback adds 1-3h wall-clock |
| 11.B | 1 (standard TDD on pure aggregation) | 1–1.5 | Lowest-risk task in the patch |
| 11.C | 2–3 (AR + 4-5 X-trios) | 3–5 | X-trio HALTs dominant; F3 split would redistribute, not reduce |
| 11.D | 0.5–2 (TW-only) or 2–4 (w/ skill re-invocation) | 1–4 | F4 branch-point; average ~1.5h |
| 11.E | 3–4 (3 parallel reviewers + TW consolidation) | 3–5 | Rule-13 cycle cap bounds worst case; typical single-cycle ~3h |
| **Added** | **8.5–15 subagent-hours** | **10–19.5 wall-clock hours** | |

**Rev-3 revised totals:**
- Subagent-hours: **48.5–55** (up from 40)
- Wall-clock: **41–66.5 hours, i.e., 2.5–4 working days**

**Context for the growth:** the patch is ~15% subagent-cost growth for a methodology escalation. That is cheap compared to the alternative (ship a FAIL primary built on quarterly-LOCF-interpolated monthly, then retrofit mid-Phase-3). The Rev-4 CPI precedent (one spec re-derivation cycle ≈ 2h) bounds the worst case: if 11.E fails and needs Rule-13-capped iteration, add up to another ~6 wall-clock hours.

---

## 6. Positive findings (preserve these)

1. **The anti-fishing framing in the Rev-3 Revision history entry is tight.** "Rev 3 inserts … 5 new tasks (11.A–11.E) that: (a) acquires daily on-chain COPM + cCOP flow data via Dune MCP, (b) aggregates daily → weekly … (c) cross-validates against the BanRep quarterly series via a pre-registered bridge ρ-gate at N=7 quarterly obs, (d) patches the Rev-1 spec to Rev-1.1 with the new primary X definition + BanRep quarterly as validation row, (e) three-way reviews the Rev-1.1 patch before Phase 2 resumes at Task 12" — this enumeration clarifies the causal chain and names the gate trigger explicitly.

2. **The decision to insert 11.E (three-way review of the spec patch) rather than let Task 11.D stand alone is correct.** This preserves the Phase-0 pre-commitment discipline. A Rev-1.1 patch that was not three-way-reviewed would be a back-door to unreviewed-spec execution — exactly the failure mode the Abrigo memory rules guard against.

3. **Task 11.C's pre-registered ρ-gate thresholds (PASS > 0.5, FAIL ≤ 0.3, INCONCLUSIVE in between) are committed BEFORE any correlation is computed.** This is the correct discipline for a bridge-validation artifact that could otherwise be fishing-adjacent.

4. **11.A Step 3 names specific cached query IDs (`#6941901`, `#6940691`, `#6939814`).** Grounds the Dune MCP acquisition in concrete artifacts rather than aspirational "queries to be built."

5. **11.A Step 3 bounds the credit budget at 30 free-tier credits.** Execution-realism — Dune free tier is not infinite.

6. **The Rev-3 Revision-history entry explicitly acknowledges the "DONE_WITH_CONCERNS" commit at `939df12e1` as the triggering evidence.** No hand-waving; the plan points to the artifact.

7. **Task 11.D preserves the 13-input resolution matrix as a first-class audit object.** The fix-log Step 2 documents every matrix-row change individually rather than doing a blanket refresh.

8. **The Gate language at Task 11.E ("Tasks 12+ shall NOT resume until Task 11.E returns a unanimous PASS-WITH-FIXES or PASS verdict") is categorically clear.** Operationally this is what protects Phase-2+ against executing against an unreviewed spec amendment.

---

**Word count:** ~1280. Report file: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-plan-rev3-review-senior-pm.md`.
