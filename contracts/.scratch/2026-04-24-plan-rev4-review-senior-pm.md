# Plan Rev-4 Review — Senior PM

**Target:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `dded7d637`
**Diff base:** `726ce8f74` (Rev-3.4)
**Lens:** scope, execution feasibility, task granularity, dependency graph, convergence bounds.

## 1. Verdict

**ACCEPT-WITH-FIXES.** Phase 1.5.5 architecture (F→G→H→I→J) is sound and anti-fishing pre-commitment is the correct alternative to cycle-capping. Five governance gaps must close before dispatch.

## 2. Findings

**PM-P1 [BLOCK] — Task-count inconsistency.** Line 12 declares Rev-4 total = 50; line 991 still says `Total task count (Rev-3.1): 46`; line 999 sum-check is stale. Readers hit contradiction. **Fix:** append Rev-4 block after line 999 (`Total task count (Rev-4): 50 = 5+5+5+5+5+18+8`) and rename §"Total task count" to a history list keeping both tallies.

**PM-P2 [BLOCK] — Task 11.H α/β/γ escalation criteria unspecified.** Step 3 lists three M_THRESHOLD_UNMET branches but leaves the choice to ad-hoc user call. β (lower threshold via Rev-5 bullet) is the cheapest path and is exactly the specification-search failure the anti-fishing guard blocks. **Fix:** add decision matrix — α if `M_max ∈ [M_threshold−0.05, M_threshold)` AND ≥2 uninspected filter families remain; β ONLY if a `M_threshold_fallback` was pre-committed at Step 1 (it is not currently); γ if `M_max < 0.50` or F exhausted.

**PM-P3 [FLAG] — Task 11.H dual-subagent unordered.** "Data Engineer + Model QA" lacks hand-off spec. Step 1 requires Model QA pre-commitment verification BEFORE any filter evaluation; Steps 2–4 are Data Engineer. **Fix:** sequence explicitly — `Model QA (Step 1) → Data Engineer (Steps 2–4); Model QA re-dispatched at Step 4 iff argmax falls outside pre-committed F`.

**PM-P4 [FLAG] — Task 12 parallelism stale.** Lines 249/489 permit Task 12 failing-test authoring in parallel with Phase 1.5.5 under the Rev-3.1 rationale. But Rev-1.1.1's 6-channel primary-X is superseded; Task 11.H argmax may yield scalar or channel-pruned vector. Task 12 schema assertions risk encoding a dead shape. **Fix:** narrow parallelism to `decision-hash-extension invariant tests only; primary-X schema assertions await Rev-2 spec`.

**PM-P5 [FLAG] — Task 11.G skill self-invocation ambiguity.** Line 408 says `foreground invocation of superpowers:brainstorming skill by the orchestrator`. The orchestrator IS the reader — dispatch-to-self. Rule 2 (foreground never authors) is grazed. **Fix:** add a Rule-2 exception (`skills invoked via Skill tool satisfy Rule 2`) or dispatch a fresh subagent.

**PM-P6 [NIT] — Phase 1.5.5 convergence condition nowhere consolidated.** The plan mentions "Phase 1.5.5 converges" at lines 3 and 489 but the condition is scattered across five task gates. **Fix:** add a paragraph after line 386: `Phase 1.5.5 is CONVERGED when: (i) 11.F peak-day report committed; (ii) 11.G brainstorm + M objective committed with ≥5 filter families; (iii) 11.H results committed with M_max ≥ M_threshold AND component floors met (or PM-P2 branch resolved); (iv) 11.I Rev-2 spec + Rev-1 supersession banner committed; (v) 11.J unanimous PASS/PASS-WITH-FIXES + TW consolidation committed.`

**PM-P7 [NIT] — Review-trio composition drift unflagged.** Plan reviews use CR+RC+PM; spec reviews (Task 11.J) use CR+RC+TW. Intentional precedent since Rev-2 but unstated here. **Fix:** one-line footnote in Rev-4 history bullet.

## 3. Risk register (likelihood × impact)

1. **[HIGH × HIGH] Non-stop policy becomes indefinite.** M_threshold=0.70 may be unreachable given Rev-1.1.1 baseline (ρ=0.7554, sign=0.40 → baseline M≈0.53). β is seductive. Mitigate via PM-P2 + pre-committed `M_threshold_fallback`.
2. **[MED × HIGH] Task 11.G.0.1 triggers silently.** Line 425 spawns a new Dune query (free-tier quota) with its own mini-review, not in the 50-task tally. Mitigate by promoting 11.G.0.1 to a numbered task OR excluding address-requiring filters from F.
3. **[MED × MED] Task-12 schema dead shape.** Per PM-P4.

## 4. Recommended amendment riders

1. **R4-1:** patch line 991 to Rev-4 total (PM-P1).
2. **R4-2:** add Task 11.H Step-3.5 α/β/γ decision matrix + pre-committed fallback threshold (PM-P2).
3. **R4-3:** rewrite Task 11.H Subagent line as sequenced `Model QA → Data Engineer` (PM-P3).
4. **R4-4:** narrow Task-12 parallelism clause at lines 249 and 489 (PM-P4).
5. **R4-5:** add Rule-2 skill-as-subagent exception (PM-P5).
6. **R4-6:** insert Phase 1.5.5 convergence-definition paragraph (PM-P6).
7. **R4-7:** add plan-review vs spec-review trio footnote (PM-P7).

Consolidated-fixes style (same pattern Rev-3.1 used for Rev-3). No Rev-5 cycle required.
