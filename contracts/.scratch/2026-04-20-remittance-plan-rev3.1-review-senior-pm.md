# Rev-3.1 Plan Review (Cycle-2) — Senior PM

**Reviewer:** Senior PM (independent, second cycle per Rule 13 cycle-cap).
**Document:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `d7dfc4390`.
**Scope:** verify Rev-3 PM findings addressed; no new execution-feasibility regressions.
**Baseline:** Rev-3 estimate 48.5–55 subagent-hours / 41–66.5 wall-clock.

---

## 1. Executive verdict

**PASS.**

All 2 BLOCKs CLOSED, all 4 FLAGs CLOSED, all 3 NITs CLOSED. Rev-3.1 applies the consolidated TW fix-log in place with Task IDs preserved (11.A–E; count 46). The Phase-1.5 promotion is textually clean, the Rule 14 insert is precise, and the Rule-13 cycle-cap boundary is numerically named. The +2,100-word budget adds specification density, not work. No net execution-hour growth.

---

## 2. Per-finding disposition

### BLOCKs

| ID | Status | Verification |
|---|---|---|
| **PM-B1** in-flight 11.A subagent semantics | **CLOSED** | Rule 14 present at line 40 in Non-Negotiable Rules block. Three scenarios (a/b/c) enumerated matching my Rev-3 fix text verbatim. Task 11.A implementer named explicitly. Generalization clause covers future mid-execution plan-review convergence points. |
| **PM-B2** Task 11.E Rule-13 cycle-cap | **CLOSED** | Task 11.E Step 3 (line 362) now defines one cycle = (a) 3 reviewers dispatched in parallel + (b) TW consolidation + (c) targeted re-dispatch of offending reviewer. Dual budget present: 3 full round-trips AND 3 re-dispatches per reviewer. Skill re-invocation explicitly excluded from cycle count. Halt-and-escalate on third failure stated. |

### FLAGs

| ID | Status | Verification |
|---|---|---|
| **PM-F1** recovery paths | **CLOSED** | Three "Recovery protocol" sub-sections present at lines 274 (11.A, 3 failure modes), 322 (11.C, PASS/INCONCLUSIVE/FAIL-BRIDGE), 365 (11.E, BLOCK-routing decision tree). All three replace the Rev-3 hand-off-style fallback notes. |
| **PM-F2** Phase-2 overload | **CLOSED** | `## Phase 1.5 — Data-Bridge` section inserted at line 242 with rationale sub-block. `## Phase 2 — Panel Extension` header at line 375. Phase-2 Rev-2 shape (11, 12, 13, 14, 15 = 5 tasks) restored. Gate clarified: Task 12 failing-test authoring may parallelize with Phase 1.5; implementation blocked on 11.E. Rev-2 F4 parallelism preserved. |
| **PM-F3** Task 11.C 3-vs-5 split | **CLOSED** | Task 11.C Step 1 (line 312) carries author-implementer decision gate. 3-HALT branch (clean data) vs 5-HALT split into 11.C.1/11.C.2 (complex data). Decision made at authoring time by foreground. Task count convention preserved (Phase 1.5 stays at 5). |
| **PM-F4** Task 11.D decision gate | **CLOSED** | Task 11.D Step 1 carries per-row classification gate: wording-only vs economic-mechanism change. Mechanism-change triggers `structural-econometrics` skill re-invocation before TW continues. Step body reformatted as checkbox checklist. |

### NITs

| ID | Status | Verification |
|---|---|---|
| **PM-N1** 46-task re-baseline | **CLOSED** | Growth narrative at line 883 enumerates 5-category attribution (a-e) with Rev-3 methodology-escalation as (e). 46-task count explicit. |
| **PM-N2** Rev-3 banner names reviewers | **CLOSED** | Line 11 Rev-3.1 banner: "Code Reviewer + Reality Checker + Senior PM, same trio as Rev-2 plan review." |
| **PM-N3** 11.A fallback scratch path | **CLOSED** | `contracts/.scratch/2026-04-20-dune-mcp-fallback-log.md` named in Task 11.A Recovery Protocol (line 274 block). |

---

## 3. Updated execution-time estimate

**Rev-3.1 changes are specification-density, not task-volume:**

- Rule 14 is a clarification, not new work. Zero subagent-hours.
- Phase 1.5 promotion is a section re-labeling. Zero subagent-hours.
- Recovery protocols document decisions the implementer would have had to make ad-hoc. Net ZERO to −0.5h (decision latency removed).
- 11.C decision gate: saves ~0.5h on clean-data path by authorizing 3-HALT upfront.
- 11.D decision gate: saves ~0.5h on wording-only path by skipping unnecessary skill re-invocation.
- 11.B independent reproduction witness: adds ~0.25h (write a second computation in the test file).
- Rev-1.1 fix-log-as-input to 11.E: zero marginal cost (fix-log was being written regardless).
- 11.A tightened row-count assertions (≥720 AND ≥500 non-zero, NaN-gap ≤3 consecutive): zero marginal cost if data is clean; may shift Task 11.A into its Recovery Protocol earlier if data is dirty, which is a win.

**Net Rev-3.1 delta: −0.5 to +0.25 subagent-hours.** Rev-3.1 stays within Rev-3's envelope:

- **Subagent-hours: 48.25–55.25** (effectively unchanged from Rev-3's 48.5–55).
- **Wall-clock: 41–66.5 hours, 2.5–4 working days.** Unchanged.

---

## 4. Phase 1.5 dependency check (requested)

Does Phase 1.5's insertion break any Tasks 12–15 dependency that relied on Rev-2 Phase-2 flow?

**No.** Verified at lines 246 and 371:

- **Task 12** dependency-source is `CleanedRemittancePanelV1` (Task 9 Phase-1 output), not Task 11 BanRep data. Rev-2 PM F4 parallelism preserved. Task 12's failing-test authoring may run in parallel with Phase 1.5; implementation gated on 11.E.
- **Tasks 13–15** were always serially downstream of Task 12 in Rev-2 shape; Phase 1.5 changes nothing for them.
- **Phase 3** (Tasks 16+) was always gated on Phase 2 closure; Phase 1.5 inserts a cleaner intermediate gate.

The Rev-2 F4 parallelism contract is restored exactly, not approximated.

---

## 5. Task 11.A / 11.E bloat check (requested)

**Task 11.A:** new content = 3-scenario recovery protocol + cCOP-TOKEN-vs-Mento-BROKER disambiguation + pre-committed N=95 + tightened row-count + scratch-path name. All are specification items consumed by the implementer in the first 5 minutes of work. None creates new sub-steps. Task remains within the 2–3 subagent-hour envelope. **Not over-scoped.**

**Task 11.E:** Step 3 now carries a 3-overall + 3-per-reviewer dual budget. Per-cycle work (3 parallel reviewers + TW consolidation + targeted re-dispatch) is exactly the Rev-2 Task 5 pattern, which consistently converges at 3h/cycle. Worst-case 3 cycles = 9 subagent-hours; typical 1 cycle = 3h. **Budget adequate.**

---

## 6. New BLOCKs / FLAGs / NITs

**None.** Rev-3.1 is cleanly executable.

One minor observation (not a finding): Rule 14's "frozen-pending-authorization" terminology is unique to this plan. If the team adopts it project-wide, `CLAUDE.md` or a feedback memory note should eventually codify it. Deferrable; not a Rev-3.1 blocker.

---

**Word count:** ~830. Per-cycle review bound respected.
