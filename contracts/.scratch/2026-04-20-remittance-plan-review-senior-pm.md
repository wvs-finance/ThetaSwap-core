# Remittance-Surprise Implementation Plan — Senior PM Review

**Reviewer:** Senior Project Manager (discipline: task granularity, phase realism, execution-driver feasibility)
**Plan under review:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
**Reference:** Rev-4 CPI plan (36 tasks as labeled, 33 as counted in CLAUDE.md), shipped in ~2 wall-clock days with FAIL verdict.
**Date:** 2026-04-20

---

## 1. Executive Verdict

**VERDICT: PASS-WITH-FIXES.** The plan is executable as written by a subagent-driven driver, but task granularity is materially coarser than Rev-4. Nine of the 30 tasks (Phase-3 authoring Tasks 16-24) have silently absorbed sub-task scope that Rev-4 explicitly split (Rev-4 Task 1 became 1a/1b/1c/1d). Without splits, the plan's ~30 nominal tasks equate to roughly 45-50 Rev-4-equivalent tasks of actual subagent work. The three-way-review cost is accurately allocated (2 cycles — Phase 0 spec + Phase 4 impl — matching Rev-4), but Phase 2 and Phase 3 are missing the inter-phase review gates that Rev-4 had at Tasks 15, 23, 31. That is a real execution risk, not a cosmetic one.

---

## 2. BLOCK Findings (would stall or misexecute)

### B1. Phase 3 has no intra-phase review gates, unlike Rev-4.
Rev-4 had three inter-phase three-way reviews (Tasks 15 after NB1, 23 after NB2, 31 after NB3), each consuming 3 parallel agents + 1 consolidation. This plan has only one unified Phase-4 three-way review (Task 28). Downstream: a systemic NB1-§2 error (e.g., a miscoded decision-hash) would be caught only after Tasks 16 through 26 have already been authored. For a notebook pipeline where NB2 § depends on NB1 §8 fingerprint and NB3 depends on NB2 PKL, late discovery is extremely expensive. Rev-4's gate pattern was adopted precisely because defect cost grows quadratically with position. **Fix:** insert three-way reviews after Task 18 (end of NB1), Task 21 (end of NB2), and Task 24 (end of NB3). That adds 3 tasks and ~3 wall-clock hours but matches the Rev-4 reviewer assignment already enforced by memory rule `feedback_three_way_review.md`.

### B2. Task 1 spec-derivation success criterion is under-specified for Tasks 2-4 to verdict on.
Task 1 Step 4 says "verify each of the 13 mandatory inputs is explicitly addressed with a resolved choice." The list is present, but there is no objective acceptance signal (e.g., "each mandatory input has a §N heading, a pre-committed choice, and a citation"). An open-ended skill invocation can loop on "resolved" vs "partially resolved" ambiguity, and the Phase-0 reviewer trio (Tasks 2-4) will not have a shared rubric. Rev-4 shipped its own Rev-4 spec after 12 reviewer cycles — that cost is implicit here. **Fix:** Task 1 Step 4 must require a one-page "13-input resolution matrix" table (input, chosen value, citation, deferred-alternative-if-any) as a hard pre-commit deliverable. Tasks 2-4 reviewers verdict against that table.

### B3. Phase-3 X-trio halt counts are materially under-estimated.
Task 17 (NB1 §2) explicitly dispatches "one trio per decision; 12 trios total." That's 12 HALT-and-resume cycles in a single task. Rev-4's equivalent (Task 8) was ONE decision (Decision #1), with Decisions #2-12 split across Tasks 9-12. Tasks 22 (NB3 §1-6, 7 trios) and 23 (NB3 §7-9, conditional ≥3 trios) have the same over-packing. At ~5 min of foreground review per trio plus agent dispatch overhead, Task 17 alone is ≥2 hours wall-clock, violating the "2-30 min subagent task" granularity guidance. **Fix:** split Task 17 into three tasks of 4 decisions each (mirroring Rev-4 Tasks 9-12 pattern). Split Task 22 into §1-3 (T1-T3a) and §4-6 (T3b replay + T4-T7). Task 23 is acceptable as-is because the anti-fishing halt short-circuits §9 authoring under FAIL.

---

## 3. FLAG Findings (efficiency / risk)

### F1. Task 15 (panel integration smoke test) blocks Phase-3 on a vaguely-scoped "fix any panel-load failures" step.
Step 3 says "Dispatch Data Engineer to address any panel-load failures; do not modify Rev-4 artifacts." If a failure implicates a Rev-4 decision (e.g., the date-column join semantics), this step deadlocks. Add an escalation branch: "if failure requires Rev-4 modification, halt and escalate to user for scope-expansion approval."

### F2. Tasks 21 and 24 bundle Analytics Reporter + Data Engineer in a single task.
Task 21 dispatches Analytics Reporter for §7-12 authoring AND Data Engineer for `build_payload_remittance` helper. Task 24 similarly dispatches both for §10-11 authoring + `build_gate_verdict_remittance` + `render_readme` extension. This violates "one subagent per task" from the superpowers:subagent-driven-development skill. **Fix:** split each into an infrastructure sub-task (DE builds helper, tested) followed by an authoring sub-task (AR uses helper).

### F3. Review-recovery paths ("Iterate to PASS") are the Rev-4 pattern but lack a cycle cap.
Task 27 Step 4 and Task 29 Step 3 both say "iterate to PASS" / "halt and re-invoke." Rev-4's Task 15 ran up to 12 reviewer cycles on the Rev-4 spec. For an executor driver, an unbounded loop is a stall risk. Suggest adding "after 3 reviewer cycles, halt and escalate to user for scope renegotiation" as a non-normative guardrail.

### F4. Tasks 11 and 12 are artificially serialized.
Task 11 (BanRep fetcher) and Task 12 (decision-hash extension) share no code dependency — Task 12 only depends on Task 9's `CleanedRemittancePanel` dataclass. Task 11's CSV fixture is consumed by Task 13 (auxiliary columns), not Task 12. Parallelizing 11+12+13's test-authoring step while serializing the implement steps would cut Phase 2 wall-clock by roughly 30%.

### F5. Task 25's three nbconvert guards are sequenced LATE.
Task 25 creates end-to-end nbconvert guards AFTER all 9 notebook-authoring tasks (16-24). Rev-4 lesson (memory `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.md`): the 5 silent-test-pass instances were caught exactly because Task 32's integration guard ran late. Good news: this plan DOES have Task 25 + Task 26, which matches Rev-4's pattern. Bad news: the plan does NOT require Tasks 16-24 to run `nbconvert --execute` at Step 3 before Step 4 test-assertion. Each authoring task's Step 3 says "nbconvert-execute" but doesn't specify whether the executed notebook is the committed notebook or a temp copy. **Fix:** each Phase-3 task's Step 3 must `subprocess.run(["jupyter","nbconvert","--execute","--inplace",<path>])` and assert returncode=0 inline, not defer entirely to Task 25.

### F6. Task 30 bundles three distinct close activities.
"Technical Writer authors completion memory" + "foreground updates MEMORY.md" + "foreground appends design-doc footer" + "run full test suite one final time" + "push to origin" is at least 4 subagent-workloads in one task. Rev-4 Task 33 was correspondingly lean (3 steps). Split into Task 30a (completion memory + MEMORY update) and Task 30b (design-doc footer + final test suite + push).

---

## 4. NIT Findings

- **N1.** Task count "30 (leaner than Rev-4's 33)" — Rev-4 CLAUDE.md cites 33 tasks but the plan itself shows 36 (1a/1b/1c/1d expansions). The comparison should use "36 Rev-4 tasks vs. 30 remittance tasks" for honesty.
- **N2.** Task 7 mentions "defers to the Rev-4 conftest fixture if it exists" but doesn't specify what happens if it DOESN'T exist (plan should assume it exists since Rev-4 shipped).
- **N3.** Task 8's placeholder README is overwritten by Task 24, but no intermediate state is validated — a silent failure to overwrite would ship a placeholder README.
- **N4.** Task 30 Step 4 says "Merge `phase0-vb-mvp` status" — ambiguous (merge what into what?). Clarify: "verify clean git status and push branch to origin."
- **N5.** Phase 0 spec review (Tasks 2-4) correctly uses CR + RC + TW per memory `feedback_three_way_review.md`. Phase 4 impl review (Task 28) correctly uses CR + RC + Senior Developer per memory `feedback_implementation_review_agents.md`. Reviewer assignments are correct — this is a positive, flagged here for documentation completeness.

---

## 5. Estimated Execution Time

**Subagent-hours (agent compute, parallel-capable):**
- Phase 0 (Tasks 1-5): ~5 subagent-hours (1 spec derivation + 3 parallel reviews + 1 consolidation).
- Phase 1 (Tasks 6-10): ~5 subagent-hours (5 mostly-parallel Data Engineer tasks).
- Phase 2 (Tasks 11-15): ~5 subagent-hours.
- Phase 3 (Tasks 16-24): ~18 subagent-hours (9 authoring tasks × ~2h each, X-trio overhead dominant).
- Phase 4 (Tasks 25-30): ~8 subagent-hours (integration + MQ + 3-way impl review + fix pass + close).
- **Total: ~40 subagent-hours.**

**Wall-clock hours (with foreground review between trios):**
- Phase 0: 4-6 hours (serial).
- Phase 1: 3-5 hours (some parallelism).
- Phase 2: 4-6 hours.
- Phase 3: 14-20 hours (X-trio HALTs × ~50 trios aggregate).
- Phase 4: 6-10 hours (review cycles; Task 29 fix iteration unbounded).
- **Total: 31-47 wall-clock hours, i.e., 2-3 working days assuming ~16h/day effective throughput with a human-in-loop.**

Matches Rev-4's ~2 wall-clock days if splits in B3 and F2 are applied. Without splits, risk of 3-4 days due to overloaded Task 17 and Task 22.

---

## 6. Proposed Splits / Merges

**Split (required for granularity parity with Rev-4):**
- **Task 17 → 17a/17b/17c** (4 decisions each).
- **Task 21 → 21a** (helper: DE builds `build_payload_remittance`) + **21b** (AR authors §7-12).
- **Task 22 → 22a** (§1-3: T1-T3a replay) + **22b** (§4-6: T4-T7).
- **Task 24 → 24a** (helpers: `build_gate_verdict_remittance`, `render_readme` extension) + **24b** (AR authors §10-11).
- **Task 30 → 30a** (completion memory + MEMORY.md) + **30b** (design-doc footer, final test, push).

**Insert (per B1):**
- **Task 18.5** (three-way review after NB1).
- **Task 21.5** (three-way review after NB2).
- **Task 24.5** (three-way review after NB3).

**Merge (optional):** Tasks 2, 3, 4 (three parallel spec reviewers) could be documented as a single task with three parallel dispatches, matching how Rev-4 Tasks 15/23/31 were structured. Current 1-task-per-reviewer form is acceptable but adds commit overhead. Keep current form.

**Net delta:** +8 tasks (from 30 to 38), bringing task-count parity with Rev-4's 36 and restoring gate discipline.

---

## 7. Positive Findings (to preserve)

- **P1.** Non-Negotiable Rules block (12 items) is comprehensive and mirrors Rev-4. Rules 5 (additive-only), 6 (citation), 11 (test-naming) are specifically well-anchored.
- **P2.** X-Trio Checkpoint Protocol is restated verbatim from Rev-4, preserving the non-negotiable pace discipline from memory `feedback_notebook_trio_checkpoint.md`.
- **P3.** Task 25 (three nbconvert guards) directly addresses the 5 silent-test-pass instances from Rev-4. This is the single most important lesson carried forward.
- **P4.** Task 26 (determinism + 5-mutation gauntlet) is the Rev-4 Task 32 pattern applied correctly.
- **P5.** Spec-coverage self-check table (bottom of plan, 13 mandatory inputs × task mapping) is a discipline Rev-4 plan did NOT have. Keep it.
- **P6.** Anti-fishing framing baked into Task 8 (notebook headers), Task 23 (§9 halt condition), Task 30 (completion memory) — three layers of anti-fishing per memory `project_fx_vol_econ_gate_verdict_and_product_read.md`.
- **P7.** Reviewer-trio assignments per memory rules (CR+RC+TW for spec, CR+RC+SD for impl) — no swap or inversion. Rev-4 shipped this correctly and this plan preserves it.
- **P8.** Reuse of Rev-4 `scripts/` (cleaning.py, nb2_serialize.py, gate_aggregate.py, render_readme.py, env.py) via additive functions is the right architectural choice — it cuts ~9 infrastructure tasks vs. Rev-4's Phase 0 of 9.

---

## Summary

Plan is executable but needs 8 task splits/insertions (§6) to match Rev-4 granularity and restore the inter-phase three-way-review gates that Rev-4's success depended on. With those splits applied, the plan lands at ~38 tasks and ~2.5 wall-clock days — comparable to Rev-4. Without splits, Phase-3 Task 17 alone becomes a ~2h super-task that violates the subagent-driven-development "one atomic subagent dispatch per task" contract and increases late-defect-discovery risk.

Reviewer assignments are correct, X-trio protocol is preserved, silent-test-pass guards (Tasks 25-26) are in place. The plan's weakness is task-size realism in Phase 3, not methodology or scope.

**Final verdict: PASS-WITH-FIXES.** Apply B1, B2, B3, F2 before execution. F1, F3, F4, F5, F6 are strongly recommended. NITs are cosmetic.
