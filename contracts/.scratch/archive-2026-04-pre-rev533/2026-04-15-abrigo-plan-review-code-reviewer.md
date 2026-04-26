# Abrigo Branding Agent — Implementation-Plan Review (Code Reviewer lens)

**Reviewer:** Code Reviewer agent
**Date:** 2026-04-15
**Plan under review:** `contracts/docs/superpowers/plans/2026-04-15-abrigo-branding-agent.md`
**Spec under review:** `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` (Rev 2)
**Review lens:** plan rigor — task atomicity, TDD compliance given the no-code constraint, dependency ordering, spec coverage, smoke-test adequacy, commit hygiene, rollback safety, external-path handling, task self-containment.

---

## Executive Verdict: **BLOCK**

Two defects make the plan non-executable as written:

1. **Task 0.1 will fail on the first `mv`.** The plan asserts the five reviewer agents are at `/home/jmsbpp/.claude/agents/_archived/<name>.md` (flat filenames). They are actually at category-prefixed paths (`_archived/design/design-brand-guardian.md`, `_archived/marketing/marketing-content-creator.md`, etc.). No file named `brand-guardian.md` exists at the asserted location. Every source path in the Task 0.1 move list is wrong; Step 2's own "abort if any is missing" guard will trigger and block the plan before any work starts. The spec's Appendix B has the same defect — it was carried forward into the plan without verification.

2. **Task 0.1 + Appendix B charter assumption is unverified and likely false.** The actual archived files are named `design-brand-guardian.md`, `marketing-content-creator.md`, `communications-executive-summary-generator.md` (probable), `communications-proposal-strategist.md` (probable), `marketing-cultural-intelligence-strategist.md` (probable). Un-archiving them by the renamed flat path means either (a) the agent registration name changes (breaking the `subagent_type` the spec assumes), or (b) they are moved without renaming, in which case the dispatch prompts in Task 3.1 that use `subagent_type: brand-guardian` will fail to route. The plan does not notice this coupling and does not instruct the engineer to choose between renaming (and updating all dispatch call-sites) versus keeping prefixed names (and updating all invocation templates to match). This is exactly the kind of cross-task consistency failure `feedback_three_way_review.md` was put in place to catch.

Everything that follows the Phase 0 reviewer bootstrap depends on dispatchable reviewer agents matching §7.2 charters. If the archived files are actually category-renamed versions of generic community agents (strong prior, given the naming convention), the charter-drift check in Task 0.1 Step 5 will report drift for most or all five, and the plan will deadlock at Phase 0 pending spec amendments.

These are fixable with a Phase 0 amendment (see §Revision Recommendations) but until the amendment lands the plan cannot execute.

Beyond the two blockers, I found four FLAGs and six nits. Details below.

---

## Section-by-Section Findings

### 1. Task atomicity — PASS with one FLAG

Most tasks produce a single self-contained artifact. The task/phase boundary tracks the artifact boundary cleanly: `0.1→reviewer bootstrap`, `0.2→permissions`, `0.3→gitignore`, `1.1→tree`, `1.2→README`, `1.3→facts.yml`, `2.1→brand agent`, `3.1→template batch`, `3.2→claim-auditor template`, `4.1→format spec`, `4.2→round-trip test`, `5.1→procedure`, `6.1-6.4→one-pager lifecycle`, `7.1-7.5→Crecimiento lifecycle`, `8.1→retro`, `8.2→follow-on stubs`.

**FLAG — Task 3.1 is a bundle of five templates.** The task creates five distinct orchestrator-side invocation templates for five different reviewer seats. Each could be its own task with its own smoke test (Step 4 mentions "dispatch the corresponding reviewer against a minimal contrived draft and verify the reviewer produces a verdict file" but does not specify per-template contrived drafts). A contrived one-pager stub may exercise Executive Summary Generator well but not Cultural Intelligence Strategist. Recommend splitting into 3.1a–3.1e, each with an artifact-appropriate smoke test. This matters because if one of the five reviewer agents (Task 0.1) has charter drift and has to be amended or replaced with an Abrigo-specific variant, the corresponding template must also change — as written, the commit in 3.1 Step 5 lumps all five into one changeset that you cannot partially revert.

### 2. TDD compliance given the no-code constraint — FLAG

The memory `feedback_strict_tdd.md` mandates "never write implementation for a feature whose test hasn't been written and verified to fail first." The plan's equivalent is the **define-success-criteria → produce → verify** pattern present in almost every task.

**What the plan gets right.** Every task begins with a Step 1 "Define success criteria" statement written in behavioural prose. Where a reasonable test exists, it is followed by a verify/smoke-test step (Task 1.3 Step 5 schema check; Task 2.1 Steps 4–7 four smoke tests; Task 3.2 Steps 3–5 three smoke tests; Task 4.2 the whole round-trip). This is structurally TDD-shaped.

**What the plan gets wrong (TDD-value lost).** Strict TDD's core risk-reduction comes from **the test being runnable and verified to fail before the implementation exists**. The plan's success criteria are declarative prose the engineer checks off *after* the implementation is written. Three specific places where this drops a failure the real TDD pattern would have caught:

- **Task 0.2 Step 5** dispatches the brand agent to write outside `.branding/` and expects deny. But the brand agent does not yet exist at this point in the plan (brand agent is Task 2.1). Step 5 explicitly says "even before its prompt exists." In practice: there is no agent-as-subject to dispatch, so the smoke test is "dispatch a named subagent that does not resolve" — the runtime will reject on routing, not on write-deny, producing a **false-positive PASS** that hides a broken permissions config. A real fail-first test would use a simpler, already-existing subagent (any generic one) to probe the write-deny on the branding path, *then* later retest with the real brand agent.

- **Task 2.1 Step 7** repeats the same write-scope smoke test after the brand agent exists. This is the right place for it. But the plan never resolves the contradiction: if Task 0.2 Step 5 is a false-positive (as above), Task 2.1 Step 7 is the *first* real test of write-deny — and if it fails, the plan's backtrack is "go back and fix 0.2." That rollback path is painful because Phase 1 already happened in between. Fail-first discipline would test write-deny with a trivial subagent in Task 0.2 and declare Step 5 actually-PASSed *before* Phase 1.

- **Task 6.1 Step 4** (founder intuition-check) is structurally a test-after-implementation: the draft is produced, then the founder reads it. If it "obviously violates positioning rules," the plan says to revise Task 2.1 and re-draft. This is the correct control loop but it is not TDD — it is QA. A more TDD-flavoured structure would be to write a "positioning-violation oracle" contrived-input test (dispatch the brand agent with a deliberately crypto-heavy input and verify it produces abstracted output) in Task 2.1 and only proceed to Task 6.1 after that oracle passes.

**Verdict on TDD lens.** The plan captures TDD's *structure* (success criteria before artifacts) but not TDD's *discipline* (failing test before implementation). For a prompt-engineering plan where the "implementation" is prose, this is a reasonable compromise — no one writes a failing Claude-response oracle for every behavioural claim — but the plan should be explicit about this being a compromise and should raise the bar on the two smoke tests that can be fail-first-able: the permissions write-deny (Task 0.2) and the memory-loading smoke (Task 2.1 Step 4). Recommend both be restructured as fail-first.

### 3. Dependency ordering — PASS with one FLAG

Phase 0 correctly front-loads: reviewer un-archive (0.1), permissions (0.2), gitignore (0.3). Phase 1 depends on 0.3 (Task 1.1 Step 1 explicitly says so). Phase 2 depends on 0.2 (Task 2.1 Step 7 tests the permissions built in 0.2). Phase 3 depends on 0.1 (the five reviewers must exist before templates are authored against them). Phase 5 depends on 4.1 (staleness algorithm). Phase 6 depends on everything prior. Phase 7 depends on 6 for lifecycle confidence. Phase 8 is trailing.

**FLAG — Task 0.2 has hidden dependency on Task 2.1.** Task 0.2 Step 5 smoke-tests the brand agent's write-deny by dispatching a subagent named `abrigo-brand-agent`. That subagent definition does not exist until Task 2.1. As written, Step 5 dispatches a non-existent subagent. Two possible fixes: (a) move the dispatch-write-deny smoke to Task 2.1 (keep Task 0.2's Step 5 as a permissions-syntax validation via a generic subagent), or (b) reorder so Task 2.1 runs before Task 0.2 Step 5 but keep Task 0.2 Steps 1–4 + 6 in Phase 0. Option (a) is cleaner.

Minor: Task 4.2 step 2 creates `_staleness-test/` *inside* `contracts/.branding/`, which requires Task 1.1 to have created the `.branding/` root. Task 4.2 does not declare this dependency. Noncritical (Phase 4 runs after Phase 1 naturally), but should be explicit.

### 4. Spec-coverage claim — SPOT-CHECK RESULTS

I selected six spec sections at random and verified the claimed mapping.

- **§4.5 Dual narrative → "enforced in Task 6 one-pager review."** The spec requires any longer-form artifact to name two protagonists (household + LP). Task 6.2's review triad includes Brand Guardian + Claim Auditor + Executive Summary Generator. Brand Guardian's charter per §7.2 covers positioning principles, but dual-narrative is a §4.5 framing rule, not one of the numbered positioning principles in memory. Nothing in Task 3.1 Step 1's template contract explicitly instructs Brand Guardian to check for two protagonists. **FLAG — coverage is aspirational, not concrete.** The dual-narrative rule needs to be either explicitly embedded in Brand Guardian's template (Task 3.1) or in the brand agent's prompt (Task 2.1). Currently it is in neither.

- **§4.6 Pilot-then-mission → "enforced in Task 6 one-pager review."** Same defect as §4.5. The Brand Guardian template instructions in Task 3.1 do not call out pilot/mission-arc adjudication. The one-pager shape in §9.1 mentions "pilot" and "mission" as separate paragraphs, and Task 6.1 Step 1 references §9.1 — so if the brand agent produces the shape, the arc is structurally present. But nothing validates that a draft conflating "Abrigo is a Colombian fintech" gets BLOCKed. **FLAG.**

- **§7.5 Contradictions → "Task 5.1 step 4."** Task 5.1 Step 4 does say "Document contradiction-surfacing. When two reviewers' findings contradict [...] the procedure instructs the orchestrator to present both verdict files and the contradiction summary to the founder for resolution rather than asking the brand agent to merge." This matches the spec. **PASS.**

- **§8.4 Staleness → "Task 4.1 + Task 4.2 + Task 5.1 step 5 publish-check."** Task 4.1 defines the manifest format + hash algorithm + staleness-check algorithm. Task 4.2 contrives a round-trip. Task 5.1 Step 5 wires the publish-check into orchestrator procedure. This covers §8.4 items 1–3. Item 4 (founder-triggered Claim-Auditor re-dispatch on drift) is NOT in any task. **FLAG — §8.4.4 refresh-verdict loop is unimplemented.** A spec-coverage claim of "complete" is wrong here.

- **§9.3 Application-form shape → "Task 7.2."** §9.3 specifies tier labeling per question, length-limit respect, tier-specific source-of-truth routing. Task 7.2 Step 1 captures all three. **PASS.**

- **§11 Open risks — §11.8–§11.11 → claimed individually.** §11.8 facts snapshot → Task 2.1 step 1(j) covers `v{N}-facts-snapshot.yml`. **PASS.** §11.9 verbatim facts quoting → claim says "Task 2.1 (verbatim facts quoting)" but neither 2.1 Step 1 nor Step 2 explicitly forbids paraphrasing quantitative facts; §11.9 requires "the brand agent is forbidden from paraphrasing traction numbers, team sizes, stage labels [...] and must instead substitute the verbatim facts.yml value." The brand-agent-prompt behavioral contract in Task 2.1 Step 1 does not enumerate this. **FLAG — §11.9 coverage is not concrete.** §11.10 brand_name_qualifier → Task 1.3 Step 2 lists the hard fields but not the soft-positioning-override fields; `brand_name_qualifier` should be populated (or marked `pending`) per §5.2.1. Task 1.3 Step 4 mentions it implicitly. **Weak PASS.** §11.11 external write-deny → Task 0.2 Step 1(c) explicitly addresses it. **PASS.**

**Net spec-coverage finding:** the "Coverage is complete" claim at the bottom of §Spec-Coverage Self-Check is too strong. Four specific requirements (§4.5 dual narrative, §4.6 pilot-mission, §8.4.4 refresh-verdict, §11.9 verbatim facts) map to tasks that gesture at them but do not encode them concretely. A rigorous recovery is either to tighten Task 2.1 and Task 3.1 to enumerate each, or to adjust the self-check to say "partial."

### 5. Smoke-test adequacy (Task 2.1 Steps 4–7) — FLAG

Four smoke tests: memory-load (4), facts-validation (5), protocol-abstraction (6), write-deny (7).

**What they catch:** gross prompt malformation (memory files not wired), gross `facts.yml` contract failure, gross protocol-name leakage, gross permission misconfiguration.

**What they miss:**

- **Painkiller-claim citation behaviour.** Task 2.1 Step 1(e) requires citations with file path + line range for every painkiller-adjacent claim. No smoke test dispatches the agent to produce such a claim and checks for a citation. This is the single most load-bearing behaviour in the whole system (per §4.3, §8.2) and it is not smoke-tested.
- **Two-tier classification.** Task 2.1 Step 1(d) requires two-tier-rule obedience. No smoke test provides an ambiguous field and checks tier classification. Missing this means a broken tier heuristic ships into Phase 7 (Crecimiento) undetected.
- **Self-review refusal.** Task 2.1 Step 1(i) forbids self-review. No smoke test tries to dispatch the brand agent to review its own output and verifies it refuses. If the prompt leaks this posture, Task 6.2's review discipline is silently bypassed.
- **Diff-rationale on revision.** Task 2.1 Step 1(g) requires `v{N}-diff-rationale.md` when revising. No smoke test dispatches a revision (draft + fake reviewer verdicts) and checks that the rationale is produced. This is the primary mechanism that keeps the iteration loop traceable and it is untested until Task 6.3.
- **Facts-snapshot and source-manifest companion files.** Task 2.1 Step 1(j, k) requires these. Tested as a precondition of Task 6.1 Step 3 but not in the dedicated smoke test battery.

A failure mode the current smokes miss: an agent that loads all memory files, passes the facts-validation call, passes the one-sentence-to-a-household call, respects write-deny, but quietly never produces citations or never attaches a source-manifest. The plan discovers this only in Phase 6.1 after all of Phase 2–5 is built. Recommend adding at least three more smoke tests in Task 2.1: citation behaviour, diff-rationale on fake-revision input, and companion-file production.

### 6. Task 0.2 permissions deferral to update-config skill — FLAG

The plan defers `settings.json` syntax to the `update-config` skill (Task 0.2 Step 3). On the surface this is appropriate (schema drift is real; the skill is the authority).

**Hidden risk:** the spec's required permissions model (§14) demands **per-agent** write-allow/write-deny rules (brand-agent scoped to `.branding/`, reviewer agents scoped to `.scratch/` + `reviews/`). Claude Code's current settings.json permissions schema is **not** obviously per-agent-scoped in the documented public surface — most guidance is session-level allow/deny patterns on tools and paths. I could not verify from this review whether per-agent scoping is actually a first-class feature of the schema today. If it is not, the update-config skill cannot satisfy the spec, and the plan will deadlock.

The plan does not pre-verify this. Task 0.2 Step 2 ("inspect existing settings") and Step 3 ("use update-config skill") assume the skill will accept the requested shape. If the skill fails or the schema does not support per-agent rules, the plan has no fallback specified.

**Recommendation:** Add a Step 0 to Task 0.2 that consults the update-config skill's documentation (or runs a dry-run interaction) to confirm per-agent scoping is supported. If it is not, the spec must either (a) accept a weaker enforcement model (session-level deny + prompt-discipline as primary), or (b) design a wrapper pattern (hooks that inspect the dispatched subagent name and reject writes). Either way the fallback should be declared before Phase 1 starts.

### 7. Commit hygiene — PASS with one FLAG

**Rule applied:** committed surface → commit; `.branding/` → no commit.

Committed-surface tasks that correctly commit: 0.1 (`contracts/.scratch/<charter-check>.md`), 0.2 (`settings.json`), 0.3 (`.gitignore`), 2.1 (`abrigo-brand-agent.md`), 3.1 (`abrigo-orchestrator-prompts/`), 3.2 (`claim-auditor-invocation.md`), 4.1 (`source-manifest-format.md`), 5.1 (`orchestrator-procedure.md`), 8.1 (`.scratch/retrospective.md`), 8.2 (`docs/superpowers/specs/`).

Gitignored tasks that correctly skip commit: 1.1, 1.2, 1.3, 4.2, 6.1–6.4, 7.1–7.5.

**FLAG — Task 8.2 commit target.** Task 8.2's commit message is `docs(abrigo): follow-on capability stubs` and stages `docs/superpowers/specs/`. Staging the whole specs directory is too broad (the current worktree has many untracked specs per git status) and risks accidentally committing other people's WIP specs. Recommend Task 8.2 name each stub file individually in `git add`.

Minor: Task 0.1 Step 6's commit stages only the scratch report, not the moved agent files. This is correct (the moved files live at `/home/jmsbpp/.claude/agents/` which is outside the worktree — you cannot and should not commit them from here). But the plan does not explain this. A reader will wonder why the moves are not staged. Add a one-line note.

### 8. Rollback / recovery — BLOCKER-ADJACENT

**User-level state is mutated without a documented rollback path.** Task 0.1 moves files under `/home/jmsbpp/.claude/agents/` — outside the worktree, outside version control. If a later task reveals the un-archive was wrong (e.g., Step 5's charter-drift check finds all five drifted and the engineer picks option (c) "author Abrigo-specific variants"), the original archive state is gone. The plan has no "move back to `_archived/`" rollback step.

**Task 0.2 `settings.json` rollback.** If the permissions config breaks access (e.g., denies too much and the brand agent cannot read memory files), the engineer needs a rollback. The plan's commit in Step 6 is committed to the branch, so `git revert` is available — but the plan does not call out this safety net. Worse, if the session is in-flight and the broken config denies the very tool needed to fix `settings.json`, the engineer must restart Claude Code or edit the file by another means. Add a documented rollback: "if smoke-test Step 5 fails and cannot be recovered inside the session, run `git checkout contracts/.claude/settings.json` from an outside shell."

**Task 4.2 cleanup.** Step 7 removes `_staleness-test/`. What if Step 5 fails and the plan aborts before Step 7? The test fixture sits in `.branding/` forever. Add "if this task aborts, clean up `_staleness-test/` before re-running." Minor.

**Cross-worktree state.** The plan creates state in three separate FS regions: (1) the worktree (`contracts/`), (2) user home (`~/.claude/agents/`), (3) external read-only (`liq-soldk-dev/notes/MACRO_RISKS/`). Only (1) is git-tracked. The plan does not document what to do if a branch is abandoned — the un-archived agents stay un-archived in (2) regardless of whether the branch merges or dies. This is probably fine (un-archiving is arguably idempotent and beneficial even without this work), but the plan should say so.

### 9. External-path handling (MACRO_RISKS) — FLAG

The plan references `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` in three places: Task 2.1 Step 1(c), Task 3.2 Step 4, and implicitly throughout source-manifest hashing.

**Availability.** I verified the folder exists and contains seven or so files. But the plan does not include a pre-flight check that the folder exists before Phase 2 begins. If a contributor runs this plan on a fresh clone without `liq-soldk-dev/` set up, every painkiller-grounded draft in Phase 6+ BLOCKs at claim-audit time.

**Movement.** Spec §11.3 explicitly names this risk. The plan inherits it without mitigation. Task 0.2 denies writes to the path — good. But no task verifies the path exists and is readable before Phase 2 starts.

**Emptiness.** The plan assumes the evidence base has the content to support the claims. If the MACRO_RISKS files are empty or do not contain specific inflation-erosion claims, the brand agent's citations are to files that say nothing useful, and the Claim Auditor will BLOCK everything. The plan has no test that the evidence base is *usable*, only that it *exists*.

**Recommendation:** Add a Phase 0 task (0.4) that runs a read pre-flight: verifies the path exists, that it contains at least one `.md` file, and optionally that specific expected file names are present (per spec §8.1 "seven files covering the macro-risk proxy taxonomy, historical precedents..."). If any are missing, abort Phase 0 and route to the founder.

### 10. Self-contained task clarity (Task 6.3 in isolation) — FLAG

Task 6.3 is "Iterate until graduation." Success criterion (Step 1) is clear. Step 2 says "for each FLAG/BLOCK revision, orchestrator re-dispatches the brand agent with the current draft plus all three verdicts." Step 4 says "repeat until three PASSes at the same revision."

**What an engineer executing 6.3 without context is missing:**
- The prompt template the orchestrator uses for revision dispatch. Task 2.1 defines revision-task behaviour in prose (Step 1(g)) but no concrete dispatch prompt exists. The engineer must invent one mid-Phase-6.
- The revision-stamp check mechanics. Task 5.1 Step 3 says the procedure documents this check, but Task 6.3 does not cite Task 5.1 nor say "follow the procedure from Task 5.1 Step 3." An engineer reading 6.3 cold sees "the orchestrator's revision-stamp check from Task 5.1" in Step 1 but no step in 6.3 runs it.
- What "escalate to founder" means operationally if two consecutive revisions BLOCK on the same finding (Step 4's escape hatch).
- Whether companion files `v{N+1}-facts-snapshot.yml` should re-read facts.yml live or carry forward `v{N}`'s snapshot. Spec §11.8 says the snapshot is for reviewers consulting on that revision; the brand agent reads facts.yml live at next-revision draft time. Task 6.3 does not restate this.

An engineer executing 6.3 in isolation can probably piece this together by reading 6.1, 6.2, 2.1, 5.1 — but the plan's checkbox structure invites subagent-driven execution where each task is dispatched independently. Under that mode, 6.3's context-hunger is a problem.

**Recommendation:** 6.3 Step 2 should explicitly reference "revision-task prompt template (to be added to Task 5.1 output as an appendix)" and Step 1's verification should call `orchestrator-procedure.md`'s revision-stamp check by name. Small edits; large clarity improvement.

---

## Other Nits (non-blocking)

- **N1.** The plan's header says "contracts/docs/..." spec path, but the worktree root already includes `contracts/`. Paths in the plan alternate between `contracts/.branding/` (when writing to the worktree) and worktree-relative paths. The plan's §Type/Naming Consistency Check addresses this by saying the `contracts/` prefix is always included for clarity. Accept — but verify the `git add` commands in every commit step agree. They do (`git add contracts/.gitignore` etc.).

- **N2.** Task 1.3 Step 2's hard-fields enumeration does not include `brand_name_qualifier` or `tagline_pin` (which spec §5.2.1 classifies as soft-positioning-override). Task 1.3 Step 4 implicitly covers them. Tighten Step 4 to name both explicitly.

- **N3.** Task 3.1's five templates share boilerplate (read spec, read artifact, read facts snapshot, read memories, output verdict file). The plan does not extract the boilerplate into a shared template nor say the engineer should. Five near-duplicate files are error-prone to keep in sync.

- **N4.** Task 4.1 Step 2 says "Recommend YAML" for the manifest format but Step 1 says "pick one, be explicit." Recommendation without execution leaves the decision ambiguous. Turn the recommendation into a decision.

- **N5.** Task 8.1 Step 2's retrospective covers revision counts and contradiction volume but not the Task 0.1 charter-drift outcome. The retrospective should also capture whether the un-archived agents needed amendment (option (a)), spec amendment (option (b)), or Abrigo-specific variants (option (c)) — that signal is the primary input for a Rev 3 spec.

- **N6.** Task 6.3's Step 4 ("repeat until three PASSes at the same revision, OR until two consecutive revisions BLOCK on the same finding") has no cap. Infinite revision loops are possible. Add a hard cap (e.g., N=5 revisions) after which the founder is auto-escalated to.

---

## Priority-Ordered Revision Recommendations

**Must fix before this plan can execute (BLOCKERS):**

1. **B1. Fix Task 0.1 source paths.** Inventory the actual archived agent filenames and either (a) rename on move, updating every downstream dispatch in Tasks 3.1/3.2 to match the new names, or (b) keep the prefixed filenames and update every dispatch template to reference them by the prefixed name. Spec Appendix B needs the same correction. Do this before Phase 0 starts.

2. **B2. Resolve the archived-reviewer charter assumption.** Either verify the five archived files' charters match §7.2 (by reading them) and update the plan with concrete pointers to each agent's current frontmatter, or mark the charter-drift outcome as the single most likely source of Phase 0 breakage and add an explicit Phase 0.5 to author Abrigo-specific variants when drift is found.

**Must fix before Phase 1 (FLAGS):**

3. **F1. Verify per-agent permissions are schema-supported (Task 0.2).** Before Task 0.2 Step 3 runs, confirm the update-config skill can express the per-agent write-allow/deny model. Document the fallback if it cannot.

4. **F2. Fix the Task 0.2 Step 5 false-positive smoke test.** Dispatch a generic existing subagent (not the non-existent abrigo-brand-agent) to probe write-deny on `.branding/`. Keep a second smoke in Task 2.1 Step 7 for the real agent.

5. **F3. Concretize §4.5, §4.6, §8.4.4, §11.9 coverage.** Add dual-narrative and pilot-mission adjudication to Brand Guardian template (Task 3.1) or brand-agent prompt (Task 2.1). Add refresh-verdict dispatch to orchestrator procedure (Task 5.1). Forbid paraphrasing of quantitative facts explicitly in Task 2.1 Step 1.

6. **F4. Add a MACRO_RISKS pre-flight (new Task 0.4).** Verify path exists, at least one `.md` file is present, expected filenames per §8.1 are present. Abort Phase 0 on failure.

**Should fix before Phase 2 (FLAGS):**

7. **F5. Strengthen Task 2.1 smoke-test battery.** Add citation-behaviour, revision/diff-rationale, companion-file, and self-review-refusal smokes to Steps 4–7.

8. **F6. Document rollback paths.** Task 0.1 (un-archive reversal), Task 0.2 (settings.json revert), Task 4.2 (fixture cleanup on abort).

9. **F7. Split Task 3.1 into per-template subtasks.** Each with its own artifact-appropriate smoke test and its own commit.

**Should fix opportunistically (NITS):**

10. N1–N6 above.

---

## Overall Assessment

The plan is structurally sound, commit hygiene is consistent, the no-code convention is obeyed, and the spec-coverage self-check is the right mechanism even if I'm disputing some of its claims. The BLOCKERs are narrow but hard: both are spec-inheritance defects (the plan carried forward assumptions from §Appendix B that the spec itself never verified). The FLAGS are addressable with 1–2 hours of plan revision work. The execution risk is not in the plan's craftsmanship — it's in the runtime assumptions about Claude Code's permissions schema and the archived-agent inventory. Verify both empirically before executing, and this becomes a well-scoped, safely-parallel implementation effort.

**Recommendation: BLOCK on B1 + B2 until the plan is amended. FLAG F1 is the next-highest risk (schema support) and I recommend resolving it before the plan is ratified, not after Phase 0 begins.**
