# Rev-4 Plan Review — Code Reviewer

**Target:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `dded7d637`
**Diff base:** `726ce8f74` (Rev 3.2) → `dded7d637` (Rev 4)
**Reviewer:** Code Reviewer (independent; no coordination with RC/TW)

## 1. Verdict

**ACCEPT-WITH-FIXES** — 1 BLOCKER, 3 MAJORs, 2 MINORs. The Phase-1.5.5 insertion is structurally sound and the anti-fishing pre-commitment is well designed. However, the task-count arithmetic is off by one and a cluster of upstream sections still reference "Rev-1.1" where Rev-4 now demands "Rev-2". Neither weakens the anti-fishing discipline per se, but they will leak into downstream subagent prompts if not patched.

## 2. Finding Table

| ID | Severity | Location | Issue | Recommended Fix |
|---|---|---|---|---|
| CR-P1 | BLOCKER | Line 12 (Rev-4 history bullet) + general arithmetic | Rev-4 bullet claims "Task count: **50** (5+5+5+5+**5**+18+8 after Phase 1.5.5 insertion)". Enumerating `### Task` headers gives 51 (Phase 0=5, Phase 1=5, Phase 1.5=5 [A–E], Phase 1.5.5=5 [F–J], Phase 2=5 [11, 12, 13, 14, 15], Phase 3=18, Phase 4=8 = **51**). The spelled-out sum (5+5+5+5+5+18+8) also equals 51, not 50. Rev-3.1 had 46 tasks; +5 new → 51. This is a textbook silent-test-pass risk: a completion checker comparing claimed N to actual N will flag stop-ship. | Amend Rev-4 bullet to say "Task count: **51** (5+5+5+5+5+18+8)". Remove the bold on the Phase-1.5.5 "5" (no emphasis needed since every term equals 5). |
| CR-P2 | MAJOR | Lines 188, 204, 519, 523, 970, 973, 977 (Task 9 rider, Task 10 rider, Task 13 Step 1 + commit msg, methodology-appendix rows) | These upstream sections still direct implementers to "Rev-1.1 spec §4.1 / §6 / §12 row 5 / §4.5 / row 9". Rev-4 declares Rev-1.1.1 SUPERSEDED and makes Rev-2 (authored at Task 11.I) canonical. When Task 13/19/21b/22b executes, its subagent will read "per Rev-1.1 spec" and load a superseded file. No amendment rider has been added pointing these readers at Rev-2. Rev-3.1 established the "plan-body amendment rider" pattern precisely for this; Rev-4 should follow suit. | Add a short "Rev-4 amendment rider" block under Task 9 + Task 10 + Task 13 + the Appendix A methodology entries stating: "Under Rev-4, 'Rev-1.1 spec' in the rider above resolves to 'Rev-2 spec at `...spec-rev2.md`' once Task 11.I commits; until then implementers in Phase 1.5.5 bypass these riders and consume the argmax filter directly from Task 11.H results." |
| CR-P3 | MAJOR | Task 11.H Step 1 (line 448, "Pre-commitment") | Anti-fishing guard text is strong, BUT Step 2's independent-reproduction witness requires matching to "sixth decimal" and the pinned values are tested against the fixture filter's M-score only. If a future implementer silently edits the pre-reg file between commits (changes `M_threshold` from 0.70 to 0.65, or relaxes a component floor), Step 3 will still run and pass the test suite — the prereg file's decision-hash is NOT included in any test assertion. The prereg is "load-bearing" but not hash-pinned. | Add a Step-2 assertion: compute `sha256(prereg_md_file)` inside `test_ccop_filter_search.py` and assert it matches a value pinned at commit time. Any mutation of the prereg file post-commit breaks the test. Mirrors the Rev-4 `nb1_panel_fingerprint.json` decision-hash pattern. |
| CR-P4 | MAJOR | Task 11.H Step 3 recovery options (α, β, γ) | Option (β) "accept a lower M_threshold with documented rationale recorded in a new Rev-5 history bullet" is a loophole: it lets a user escalation unilaterally relax a pre-commitment. This is exactly the specification-search failure-mode Simonsohn et al. warn against, now wearing a recovery-protocol hat. The anti-fishing guard one paragraph later says "mid-search modification is banned (deferred to Task 11.H.2 with full re-commitment)" — option (β) contradicts that by allowing a lower threshold post-hoc WITHOUT a Task 11.H.2 re-commitment cycle. | Strike option (β). Replace with: "(β) full Task 11.H.2 re-commitment cycle with a new prereg, new search space F', and fresh reviewer dispatch — a lowered M_threshold is only valid as Step 1 of H.2, never as an amendment to the current H run." This preserves the H/H.2 dichotomy. |
| CR-P5 | MINOR | Task 11.J Rule 13 cycle-cap scoping | Text reads "Rule 13's 3-cycle cap does NOT apply to filter iteration (it applies only at Task 11.J)". The exemption scope is clear for Task 11.H, but the plan body at Rule 13 (line 40) still reads "Any task that says 'iterate to PASS' ... is capped at 3 reviewer cycles." A literal reading of Rule 13 would still cap 11.H because filter iteration IS an iterate-to-argmax loop. A drift-prone reader could cite Rule 13 to force-halt Task 11.H at cycle 3. | Patch Rule 13 in-place: append "**Exception:** Task 11.H filter iteration is a pre-committed deterministic enumeration, not a reviewer loop; the 3-cycle cap does NOT apply. See Phase-1.5.5 preamble." Belt-and-braces with the Phase-1.5.5 scoping text. |
| CR-P6 | MINOR | Task 11.J Files block | Placeholder date `2026-04-2X` appears in three filenames (`2026-04-2X-remittance-spec-rev2-review-*.md`). Prior reviews (Task 11.E) used concrete dates at authoring-time; this plan is being committed now, and the Task 11.J date is knowable-at-execution-time from the orchestrator's `date`. Leaving `2X` forces the executing subagent to pick a date with no committed convention, risking `.scratch` path drift. | Either (a) replace `2X` with `YY` and add a note "YY resolves to execution date via `$(date +%d)`", or (b) commit to a placeholder-resolution rule in Rule 12 (artifact path constants). |

## 3. Consistency Check — Upstream-Reference Audit

**Sections that still reference pre-Rev-4 spec versions and need Rev-4 amendment riders:**

| Section | Current Text | Rev-4 Expectation |
|---|---|---|
| Goal (line 14) | "per Rev-1.1 spec §4.1 after Task 11.D patch" | Should add parenthetical: "(Rev-4: Rev-1.1 superseded by Rev-2 post-Task 11.I)" |
| Task 9 rider (line 188) | "after reading Rev-1.1 spec §4.1 (Task 11.D output)" | Add rider: Rev-2 spec §4.1 post-Task 11.I supersedes |
| Task 10 rider (line 204) | "per Rev-1.1 spec §6", "§12 rows 6/7/8" | Same rider pattern |
| Task 13 Step 1 (line 519) | "Each column's computation rule matches the Rev-1.1 spec exactly" | Rev-2 spec, since Task 13 executes in Phase 2b AFTER Task 11.I |
| Task 13 Step 5 commit (line 523) | "per Rev-1.1 spec" | Update to "Rev-2 spec" |
| Appendix A methodology links (lines 970, 973, 977) | "Rev-1.1 §4.5", "Rev-1.1 §12 row 5", "Rev-1.1 spec row 9" | Update to Rev-2 once authored; OR add umbrella note at Appendix head: "Post-Task-11.I, all 'Rev-1.1' references resolve to Rev-2." |

**Non-superseded consistent references (OK):** Rule 13 (line 40), Phase-1.5 rationale (line 247), recovery protocols (lines 277–281, 325–328), Task 11.D/11.E bodies (lines 334–378) — these describe pre-Rev-4 historical work correctly.

## 4. Answers to Reviewer Focus Prompts

1. **Task 11.H pre-commitment enforcement:** Strong in prose, weak in enforcement. The Step 1 Model QA verification checks "no filter has been evaluated yet" at prereg-time, but nothing pins the prereg content post-commit. See CR-P3. An implementer could edit the prereg between Step-1 commit and Step-3 execution and no test would catch it. Fix: hash-pin the prereg file in the test.
2. **Rule 13 exemption scoping:** Exemption is correctly scoped in Phase-1.5.5 preamble AND Task 11.H Step 3 AND Task 11.J Step 2. Triple-locked — good. But Rule 13 itself (line 40) doesn't mention the exception; see CR-P5.
3. **MDES recomputation (Task 11.I Step 2):** The requirement is strong — `scipy.stats.ncf.ppf` root-finding is MANDATED, the analytical-approximation ban is explicit ("Do NOT use the analytical approximation"), and an independent-reproduction witness is required. A careful reader will not miss it. A careless reader could — consider escalating "Do NOT" to "BANNED — THIS IS THE EXACT ERROR REV-4 EXISTS TO FIX" with a pointer to the CR-E2 report. Minor stylistic fix, not blocker.
4. **Task ordering 11.F → 11.G → 11.H → 11.I → 11.J:** Sequencing is correct and latent parallelism is correctly disallowed: 11.G consumes 11.F output, 11.H consumes 11.G's search space and objective, 11.I consumes 11.H's argmax, 11.J reviews 11.I. No safe parallelism exists between any adjacent pair. Task 12 failing-test parallelism (per Rev-3.1) is preserved at Task 11.J gate. Clean.
5. **File-path + commit-message correctness:** All `.scratch` paths resolve to the correct worktree. The Task 11.E review files cited in the Rev-4 history bullet (`2026-04-24-tier1e-rev111-*`) exist on disk (verified `ls`). Commit-message format follows prior-rev conventions (`spec(remittance): ...`, `prereg(abrigo): ...`, `result(abrigo): ...`). Minor inconsistency: Task 11.G uses `brainstorm(abrigo)` and Task 11.H uses `prereg(abrigo)` / `result(abrigo)` — scope-token `abrigo` vs `remittance` drifts within Rev-4. Not blocker; see CR-P6 for similar placeholder-date issue at Task 11.J.
6. **Task 11.G.0.1 sub-task hint:** Defined precisely enough for a seasoned Data Engineer but fragile for a fresh subagent. Trigger ("≥3 candidate filters require address-level Dune data not present in the current CSV") is concrete; deliverable ("re-fetch via a new Dune query with per-tx `from_address`, `to_address`, `amount_usd` granularity") is concrete; gate ("its own mini-review before Task 11.H") is specified. What's missing: (a) credit-budget guidance for the new Dune query (the Task 11.A parent specifies ≤30 free-tier credits; 11.G.0.1 inherits this silently); (b) what happens to Task 11.G's committed brainstorm file when 11.G.0.1 discovers new filter families — does 11.G commit again or does 11.G.0.1 append? Not blocker but will bite later. Optional fix: add a one-line "11.G.0.1 inherits Task 11.A credit budget; appends to the existing 11.G brainstorm file."
7. **Consistency with non-superseded plan text:** See finding table CR-P2 and Section 3 above. Seven upstream references need Rev-4 amendment riders.
8. **Task-count arithmetic:** Off by one. See CR-P1 (BLOCKER).

## 5. What's Good (Praise Where Due)

- The **symmetric similarity objective M** construction is a clever anti-fishing move: by pre-committing four component measures (Pearson, Spearman, sign-concordance, Kendall) with explicit weights AND per-component floors, the plan forecloses the "one inflated component gaming M" attack vector. This is econometrically more defensible than a single-number threshold.
- The **H.2 re-commitment escape hatch** is the correct pattern: rather than letting the current H run be modified, a new H.2 cycle with fresh prereg is the documented path. This preserves the pre-registration discipline that vindicated the CPI-FAIL exercise.
- The **Rev-1.1.1 = SUPERSEDED marker at commit `ac5189363`** is explicit and citeable. A future reader can reconstruct the chain.
- Task 11.I Step 4's directive ("Do not read pre-Rev-2 sections for methodology guidance") is exactly the right `§0 banner` to place on Rev-2. Mirrors the CPI-FAIL `gate_verdict.json` pattern.

---

**Report path:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-24-plan-rev4-review-code-reviewer.md`
**Word count:** ~850 body + tables (slightly over 600 target, tables pushed the length — keeping as-is for decision-useful detail).
