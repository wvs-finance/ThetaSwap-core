# Technical Writer Review — Abrigo Branding Agent Implementation Plan

**Plan:** `contracts/docs/superpowers/plans/2026-04-15-abrigo-branding-agent.md`
**Spec:** `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` (Rev 2)
**Reviewer lens:** documentation craft — can a future engineer (human or AI) land on this plan cold and execute it?
**Date:** 2026-04-15

---

## Overall Verdict: **FLAG**

The plan is unusually well-crafted for documentation clarity. Task titles, step numbering, phase structure, terminology discipline, and spec-coverage self-check are all strong. The plan reads top-to-bottom AND executes task-by-task without obvious friction. "Brand agent" is used consistently, "Claim Auditor" (role) vs. "Reality Checker" (underlying subagent) is used correctly throughout, and file-naming conventions (`v{N}.md`) are applied uniformly.

However, five concrete defects will trip a cold executor, two of them load-bearing:

1. **Undefined `<artifact>` placeholder** (blocking-adjacent — appears in Task 0.2, Task 3.1, Task 3.2 Step 1 file-path templates, never defined).
2. **Task 1.3 schema gap** — the two `positioning overrides (soft)` fields from spec §5.2.1 (`brand_name_qualifier`, `tagline_pin`) are never enumerated in Step 2, Step 3, or Step 4. The coverage-map at line 541 claims Task 1.3 covers `brand_name_qualifier`. It does not.
3. **"Founder writes the values" scope unbounded** in Task 1.3 Step 3 (see Lens 5 finding).
4. **Phase 8 has no scoping paragraph** — every other phase sets up what is different from its predecessor.
5. **Spec §9.1–§9.4 still carry the withdrawn "Reality Checker" label** for the Claim Auditor seat. The plan inherits correctness but the executor cross-referencing §9.1 will see "Reality Checker" and may author the wrong verdict filename (`v1-reality-checker.md` vs. spec's §7.4 `v1-claim-auditor.md`). This is a spec defect that leaks into plan execution — must be called out.

None of the findings block execution — a competent engineer can resolve each on the fly — but #1 and #2 require a 10-minute plan patch before handoff. The retrospective and §11 risk coverage are thorough; the spec-coverage self-check at the end is a documentation-craft highlight.

---

## Findings by Lens

### Lens 1: Task-title clarity

**PASS.** Every task title stands alone as a scope description without needing to read the body:

- "Un-archive the five reviewer agents" (0.1)
- "Author the runtime permissions configuration" (0.2)
- "Populate `contracts/.branding/facts.yml` (hard fields only)" (1.3)
- "Author the Claim Auditor prompt augmentation" (3.2)
- "Iterate until graduation" (6.3)
- "Paste Crecimiento questions" (7.1)

The one-word-title risk is avoided. Even terse titles like "Iterate until graduation" make scope clear because "graduation" is defined in spec §0. "Retrospective and memory updates" (8.1) is the only title that benefits from surrounding phase context, but it's inside Phase 8 "Wrap-Up" so the framing is adequate.

### Lens 2: Step-heading consistency

**PASS with minor note.**

All 22 tasks open with `- [ ] **Step 1: Define success criteria.**` with identical phrasing, period, and boldface. This is impressive discipline and will make the plan mechanically parseable by `executing-plans`.

Verb tenses are consistent (imperative: "Define," "Write," "Verify," "Commit"). Capitalization is consistent. Bullet style (`- [ ]`) is uniform. Bold-step-label pattern is uniform. Minor note: "Step 2" verbs vary legitimately by task purpose ("Inspect the existing settings," "List the hard fields," "Write the procedure") — this is appropriate per-task specialization, not inconsistency.

### Lens 3: Forward/backward references

Cross-checked ten references:

| Reference | Target | Verdict |
|---|---|---|
| Task 0.1 Step 5 → "spec §7.2 charter summary" | spec §7.2 | ✓ exists; lists six reviewer charters |
| Task 0.1 Step 5 → "spec's choice (a/b/c) per §15" | spec §15 Appendix B | ✓ exists; enumerates (a) amend prompt, (b) amend spec, (c) author variant |
| Task 1.2 Step 2 → "spec §5–§10 for authoritative content" | spec §5 Workspace + §10 Invocation | ✓ exists; content matches citation |
| Task 2.1 Step 1 → "seven memory files listed in spec §13" | spec §13 Sources of truth | ⚠ spec §13 lists 10 items, not 7; see Lens 8 |
| Task 3.1 Step 1(g) → "§7.2.1 charter-overlap tiebreakers" | spec §7.2.1 | ✓ exists; BG-vs-CIS and CA-vs-PS are the two documented pairs |
| Task 3.2 Step 1 → "§8.3's evidence-failure-mode table" | spec §8.3 | ✓ exists; four failure modes listed |
| Task 4.1 Step 1 → "spec §8.4" | spec §8.4 | ✓ exists; minimum viable staleness protocol |
| Task 5.1 Step 2 → "spec §7.4 artifact lifecycle" | spec §7.4 | ✓ exists; nine-step lifecycle |
| Task 6.3 "Task 6.4 pattern" (actually Task 7.4 Step 2) | Task 6.4 | ✓ Task 6.4 Steps 2–3 describe `mv`+`cp`+publish-check, which 7.4 re-uses |
| Task 7.3 Step 3 → "Phase 6 Task 6.3" | Task 6.3 | ✓ Task 6.3's revise-and-redispatch loop is the referent |
| Task 8.2 Step 1 → "spec §12 step 9" | spec §12 item 9 | ✓ exists; lists six follow-on capabilities |

**One discrepancy found.** Task 2.1 Step 1(a) says "read all seven memory files listed in spec §13 before drafting." Spec §13 enumerates ten items: seven memory files + `inflation-mirror-tier1-feasibility-design.md` + `ranPricing.ipynb` + `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/`. Of these, the brand agent should read seven memory files PLUS the Tier 1 methodology spec PLUS the evidence base. The plan's "seven memory files" is literally correct (memory files are seven) but elides the other three mandatory reads. A cold executor who only tells the agent to read seven files will miss the evidence base and the methodology spec — both load-bearing for painkiller claims.

**Recommendation:** change Task 2.1 Step 1(a) to "read all seven memory files AND the three non-memory sources in spec §13 before drafting" or enumerate them inline.

### Lens 4: Definitions repeated or missing

**PASS.** The plan never re-defines glossary terms from spec §0 (Abrigo, RAN, brand agent, orchestrator, Claim Auditor, graduate, etc.). It links by reference.

One **load-bearing undefined term**: `<artifact>` appears as a path-template placeholder in Task 0.2 Step 1(b), Task 3.1 Step 1(f), and Task 3.2 Step 1(d) — `contracts/.branding/<artifact>/reviews/v{N}-{seat}.md`. The placeholder is never defined. It evaluates to different subtrees depending on the artifact type:

- For the one-pager: `contracts/.branding/artifacts/one-pager/reviews/` (note the **extra `artifacts/` segment**).
- For the Crecimiento form: `contracts/.branding/forms/crecimiento/reviews/` (note the **`forms/` segment replacing `artifacts/`**).

A cold executor will plausibly mis-author the permissions glob in Task 0.2 as `contracts/.branding/*/reviews/**` (one-level wildcard), which would cover `forms/crecimiento/reviews/` but NOT `artifacts/one-pager/reviews/` (two levels deep). This is a latent misconfiguration that only surfaces at smoke-test time.

**Recommendation:** add one line under the plan header defining `<artifact>` as a placeholder for either `artifacts/<name>` or `forms/<org>` (per spec §5.2 tree) and adjust the permissions glob in Task 0.2 Step 1(b) to cover both depths (e.g., `contracts/.branding/**/reviews/**`, which the plan does use at Task 0.2 Step 4 but not Step 1 — see inconsistency between Step 1(b) and Step 4's glob depth).

### Lens 5: Task 1.3 `facts.yml` authoring scope

**FLAG — bounded enough for the hard fields, under-bounded for positioning overrides.**

Task 1.3 Step 3 "Founder writes the values" is scoped correctly to Step 2's enumerated hard fields (Abrigo, Colombia, underserved-FX, etc.) — a careful founder reads Step 2, sees the eighteen enumerated hard fields, and populates them. No plausible reading "rewrite the whole schema" risk here because the schema is spec §5.2.1 and the plan does not say "edit the schema."

**However:** the spec §5.2.1 enumerates a `Positioning overrides (soft)` block with two fields: `brand_name_qualifier` and `tagline_pin`. Step 2 (hard fields) correctly omits them. Step 4 (soft fields) enumerates traction and contact soft fields but **silently omits both positioning-override fields**. A cold executor following Step 4 literally will produce a `facts.yml` missing two spec-mandated keys. The brand agent's schema validation in Step 5 will then FLAG (not BLOCK, since they are soft) but the `brand_name_qualifier` rename-protocol described in spec §11.10 will silently not function. Coverage map line 541 incorrectly claims "Task 1.3 (brand_name_qualifier field)."

**Recommendation:** add `brand_name_qualifier` and `tagline_pin` to Task 1.3 Step 4 as soft fields to populate or mark `pending`.

### Lens 6: Phase transitions

**FLAG — Phase 8 lacks a scoping paragraph; others are adequate.**

| Phase | Opening paragraph | Sets up difference? |
|---|---|---|
| 0 — Prerequisites | "Bootstrap the runtime conditions the spec assumes. Nothing in later phases will work correctly until Phase 0 completes." | ✓ |
| 1 — Workspace Bootstrap | "Create the gitignored working surface, populate the hand-edited source of truth, and document the conventions." | ✓ |
| 2 — Brand Agent Definition | "Author the committed subagent that drafts copy." | ✓ terse but sufficient |
| 3 — Review Triad Wiring | "Wire the orchestrator's dispatch prompts for each reviewer seat." | ✓ |
| 4 — Source-Manifest Staleness | "Define and verify the minimum viable evidence-staleness protocol from spec §8.4." | ✓ |
| 5 — Orchestrator Operating Procedure | "Document the operating procedure the founder (in v1, human + foreground Claude session) follows when running the system." | ✓ |
| 6 — First Dry Run (One-Pager) | "End-to-end validation of the system on a real artifact before attempting the Crecimiento form." | ✓ |
| 7 — Crecimiento Submission | "With the lifecycle validated, produce the real first-use output." | ✓ |
| 8 — Wrap-Up | **(none — jumps straight to Task 8.1)** | ✗ |

**Recommendation:** add one sentence after `## Phase 8 — Wrap-Up` such as "Close the first cycle: capture what was learned and queue the follow-on work the spec deferred."

### Lens 7: Success-criteria scoping

**PASS.** Spot-checked 12 tasks; every Step 1 produces a concrete, verifiable condition:

- Task 0.3: "`git status` from the worktree root does not list any file under `contracts/.branding/`." — shell-verifiable.
- Task 1.1: "`ls -R contracts/.branding/` shows the tree." — shell-verifiable.
- Task 2.1: "(a) read all seven memory files ... (b) refuse to draft artifacts dependent on any missing hard field ..." — 11-point behavioral contract, each individually smoke-testable (Steps 4–7 actually exercise four of them).
- Task 6.3: "For some revision `N`, all three verdict files at `v{N}` report PASS, and the orchestrator's revision-stamp check from Task 5.1 passes." — file-system verifiable.
- Task 4.2: "Orchestrator can detect a mutated source file and emit a `source-manifest-drift.md`." — terse but binary-outcome, verifiable.

No task's success criteria pass vacuously. The one slightly soft criterion is Task 8.1 ("A short retrospective documenting...") but retrospectives are inherently discretionary and the criterion lists required sections.

### Lens 8: Reading order vs. execution order

**PASS with one tension.**

The plan reads top-to-bottom without forward-references requiring reader skip. Phases are ordered to respect dependencies (Phase 0 prerequisites → Phase 1 workspace → Phase 2 agent → Phase 3 reviewers → Phase 4 staleness → Phase 5 orchestrator → Phase 6 dry run → Phase 7 real run → Phase 8 wrap).

**One tension:** Task 2.1 Step 1 enumerates outputs the brand agent must produce including `v{N}-facts-snapshot.yml` and `v{N}-source-manifest.md`. The source-manifest format is not defined until Task 4.1 (Phase 4). A reader landing at Task 2.1 and asking "what is a source-manifest file supposed to look like?" must jump forward to Task 4.1. A cold executor writing the brand agent prompt at Phase 2 does not yet have Task 4.1's format spec to embed.

**Recommendation:** either (a) move Task 4.1 (the source-manifest format spec) to Phase 1 or a new "Phase 1.5: Shared formats" so the brand agent prompt in Phase 2 can cite a concrete spec, or (b) add a note to Task 2.1 Step 2 saying "source-manifest and facts-snapshot formats are specified in Task 4.1; the brand-agent prompt can reference that section or embed the format inline — update to cross-reference Task 4.1 once authored."

A secondary minor tension: Task 2.1 Step 7 smoke-tests the permissions boundary from Task 0.2 by dispatching the brand agent. This is correct sequencing (Task 0.2 completes in Phase 0 before Phase 2 runs), but the dependency is implicit. A one-line precondition note at the top of Task 2.1 would help.

### Lens 9: Terminology discipline

**PASS.**

- "Brand agent" (spec Rev 2 standard) used consistently. The phrase "branding agent" appears only in the document title ("Abrigo Branding Agent Implementation Plan") and once in the type-consistency check. The title is acceptable as a proper noun referring to the overall system; the spec's own header also uses "Abrigo Branding Agent — Design Spec."
- "Claim Auditor" used for the role; "Reality Checker" used only when referring to the underlying subagent that realizes the role (Task 0.2 Step 4, Task 3.2 Step 1, Task 3.2 Steps 3 and 5). This matches spec §0 and §7.1 exactly.
- "Orchestrator" used consistently; never confused with "founder" or "brand agent."
- `v{N}.md` revision stamp used consistently. No wall-clock timestamps leak through.

One observation outside the plan's control: **spec §9.1–§9.4 still label the Reality Checker as the Claim Auditor seat** (lines 311, 319, 327, 346). The plan correctly uses "Claim Auditor" throughout. An executor who reads §9 for artifact shapes will encounter the old label and may author verdict filenames with `reality-checker` instead of `claim-auditor`, contradicting spec §7.4's `{seat}` slug convention.

**Recommendation (outside plan scope but blocking-adjacent):** spec §9 should be patched in a Rev 3 to use "Claim Auditor" per the Rev 2 glossary decision. Alternatively, add a sentence to the plan's header or to Task 3.2 saying "If you see 'Reality Checker' in spec §9.1–§9.4 artifact-shape tables, read it as 'Claim Auditor' per the Rev 2 glossary."

### Lens 10: Handoff to executing-plans skill

**PASS.**

The plan's structure matches `superpowers:executing-plans` expectations:

- **Phases** as `## Phase N — Name` (nine phases, sequential).
- **Tasks** as `### Task N.M: Title` (22 tasks total).
- **Steps** as `- [ ] **Step K: Verb.** body.` (uniform checkbox syntax).
- **No ambiguous completion conditions** — every task has either a commit step or an explicit "No commit. Gitignored." marker.
- **Verifiable success criteria at Step 1** of every task.
- **Atomic commits** specified with HEREDOC-free `git commit -m "..."` messages matching conventional-commit style (feat/chore/docs/fix).

The plan header also advertises `superpowers:subagent-driven-development` as the preferred executor, which is consistent with the plan having many tasks that are author-a-document tasks suitable for parallel dispatch.

One edge case: Tasks with "No commit. Gitignored." as their final step have no git-landmark for the executor to confirm task completion. `executing-plans` typically uses the commit as the task-boundary signal. For gitignored tasks, the plan relies on the checkbox-all-checked condition. This is fine as long as the executor reads the "No commit" marker as "task complete when all boxes ticked." A defensive note at the plan header clarifying this would help.

---

## Additional Findings (minor)

- **Line 61 (Task 0.2 Step 1(b)):** the permissions glob `contracts/.branding/<artifact>/reviews/` should arguably be `contracts/.branding/**/reviews/**` to cover both `artifacts/one-pager/reviews/` and `forms/crecimiento/reviews/` at their respective tree depths. Task 0.2 Step 4 does use `**/reviews/**`, so the Step 1 phrasing is merely imprecise (not wrong at configuration time), but the imprecision will propagate into the smoke-test's denial expectations.
- **Line 108 (spec §5.1):** the spec still says "the default is to reuse the existing Brand Guardian, **Reality Checker**, Proposal Strategist, ..." — one more spec-side "Reality Checker" leak that the plan inherits correctness around.
- **Task 6.3 Step 5 founder-override file path** uses `reviews/v{N}-override.md`. Spec §7.4 item 9 agrees. ✓
- **Task 4.1 hash algorithm choice:** SHA-256 with `sha256sum`. Reasonable; matches spec §8.4 "any deterministic whole-file hash suffices." ✓
- **Spec-coverage self-check** at plan end is unusually thorough (37 section-to-task mappings). Two entries are inaccurate:
  - Line 541: "Task 1.3 (brand_name_qualifier field)" — see Lens 5; the field is not present in Task 1.3's current text.
  - Line 541: "Task 2.1 (verbatim facts quoting)" — Task 2.1 does not explicitly enumerate the verbatim-quoting constraint from spec §11.9. The closest is Step 1(j) ("output a companion `v{N}-facts-snapshot.yml`"). The verbatim-quoting obligation deserves its own bullet in Step 1.

---

## Ship-Readiness Assessment

**Can a stranger execute this plan without author help?** Mostly yes, with one caveat.

**What works without author help:**
- Phase 0 is bulletproof — precise file paths, explicit verification, commit messages provided.
- Phase 1 workspace setup is mechanical.
- Phases 3–5 have strong cross-references to spec sections; a stranger with the spec open in a second pane can execute without questions.
- Phases 6–7 (dry run and real run) follow a clear revise-until-PASS loop with a founder-override escape hatch for the common stall case.
- Commit messages and acceptance criteria are uniform and pass the `executing-plans` conformance check.

**What requires author help or a plan patch before execution:**
1. **Task 0.2 Step 1(b) `<artifact>` placeholder** — a stranger will write the wrong permissions glob without one line of clarification. Fix: replace `<artifact>` with `**` in the Step 1 phrasing OR add a placeholder-legend at the plan header.
2. **Task 1.3 Step 4 missing positioning-override soft fields** — a stranger will populate `facts.yml` without `brand_name_qualifier` and `tagline_pin`. Fix: add the two fields to Step 4's enumeration.
3. **Spec §9.1–§9.4 "Reality Checker" leak** — a stranger reading the spec for artifact shapes will see the old label. Fix: either patch spec §9 (recommended) or add a plan-header note clarifying the terminology override.

**Estimated patch time:** 10 minutes for items 1–2. Item 3 is a spec fix, not a plan fix, and is outside the plan author's scope but should be raised with the spec owner.

**Recommendation:** FLAG — apply the three-minute plan patch for items 1 and 2, and open a spec-defect note for item 3. After that, the plan is ready to hand to a cold executor.

---

## Notable Strengths

- Spec-coverage self-check (lines 507–547) is a documentation-craft highlight. Every spec section is mapped to an implementing task, with follow-ons explicitly deferred. This is rare in implementation plans and massively reduces the "did we miss something?" risk.
- Placeholder-scan result (lines 551–553) proactively calls out that "pending" and "contrived" are intentional, not gaps. Prevents a reviewer from flagging these as TODOs.
- Type/naming-consistency check (lines 557–562) documents the terminology discipline the plan maintains. Useful as a future-proofing device when the plan is revised.
- Phase 0 smoke-tests the write-deny **before** Phase 2 writes the brand-agent prompt that would violate it. Correct sequencing of runtime-enforcement work ahead of the work it enforces.
- Task 3.2's three smoke tests (BLOCK on uncited / PASS on grounded / non-interference with native charter) exercise the Claim Auditor augmentation's three critical failure modes.

The plan author clearly thought hard about the cold-executor experience. The findings above are the marginal gaps, not systemic issues.
