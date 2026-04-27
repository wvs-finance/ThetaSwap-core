# Abrigo Branding-Agent Plan — Reality-Check Review

**Reviewer:** TestingRealityChecker
**Plan:** `contracts/docs/superpowers/plans/2026-04-15-abrigo-branding-agent.md`
**Spec:** `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` (Rev 2)
**Date:** 2026-04-15
**Default verdict:** NEEDS WORK (confirmed by findings below)

---

## Executive Summary

Two load-bearing assumptions in Phase 0 collapse under verification. Task 0.1 cites five filenames that do not exist at the stated paths — all five reviewer agents are real, but live at different filenames under category-prefixed subdirectories. Task 0.2 assumes Claude Code's `settings.json` supports per-agent write permission scoping; no evidence in the spec or plan demonstrates that feature exists as described, and the broader Claude Code permission model is session-scoped rather than per-subagent-name-scoped. Either finding alone blocks the plan from executing as written.

Three secondary issues (evidence-base fitness for Task 4.2, time-claim mismatch on Task 1.3, unverified Crecimiento portal in Phase 7) are fixable with targeted edits.

Spec Rev 2 additions (Claim Auditor role, §7.2.1 tiebreakers, revision-stamping, source-manifest protocol, §11 risks, appendices) are traced to concrete tasks and appear covered.

---

## Finding 1 — CRITICAL — Task 0.1 filename paths are wrong; spec Appendix B is also wrong

**Severity:** Blocker. Task 0.1 cannot execute as written; every `mv` command would fail "No such file or directory."

**Claim (plan, lines 33–37):**
> Move: `/home/jmsbpp/.claude/agents/_archived/brand-guardian.md` → `/home/jmsbpp/.claude/agents/brand-guardian.md`
> (and four parallel moves for executive-summary-generator, content-creator, proposal-strategist, cultural-intelligence-strategist)

**Claim (spec Appendix B / §15, lines 474–478):** lists the same five bare filenames.

**Evidence (Glob results):**

| Plan / spec claims | Actual path |
|---|---|
| `_archived/brand-guardian.md` | `_archived/design/design-brand-guardian.md` |
| `_archived/executive-summary-generator.md` | `_archived/support/support-executive-summary-generator.md` |
| `_archived/content-creator.md` | `_archived/marketing/marketing-content-creator.md` |
| `_archived/proposal-strategist.md` | `_archived/sales/sales-proposal-strategist.md` |
| `_archived/cultural-intelligence-strategist.md` | `_archived/specialized/specialized-cultural-intelligence-strategist.md` |

None of the five flat paths exists. A recursive Glob at `_archived/**/brand-guardian.md` returned no match; the only hit for `*brand-guardian*` is `design/design-brand-guardian.md`.

**Secondary consequence.** The spec's §11.4 claim that "five of the six named reviewer agents are archived at `/home/jmsbpp/.claude/agents/_archived/`" is literally true (they are archived under that tree) but misleading about filenames. Any engineer reading the plan and running Task 0.1 Step 2 (`ls _archived/` and "confirm the five filenames exist there") will find they do not.

**Required changes:**
1. Update the plan's Task 0.1 `Files:` block to use the real paths with category prefixes and subdirectories.
2. Decide the un-archive target filenames. Two reasonable choices: (a) preserve the category prefix (`/home/jmsbpp/.claude/agents/design/design-brand-guardian.md`) which matches the convention visible in `/home/jmsbpp/.claude/agents/engineering/engineering-*`, or (b) rename on move to bare names. The spec's §7.1 table and §14 Appendix A both reference bare names ("brand-guardian", "executive-summary-generator", etc.), so option (b) forces a rename-on-move and Step 5 charter-drift check must confirm the `name:` frontmatter field matches.
3. Update spec Appendix B (§15) to reflect the real archived paths and whatever un-archived target is chosen.
4. Re-verify Task 0.1 Step 2's precondition language: "confirm the five filenames exist there. Abort if any is missing" — the current wording would cause the engineer to abort every time because the bare filenames do not exist.

---

## Finding 2 — CRITICAL — Task 0.2's per-agent write-scope enforcement model is not a documented Claude Code feature

**Severity:** Blocker. If the feature does not exist, the spec's "Enforcement model" language at §6.4 is fiction and §14 Appendix A's "Required behavior for the brand agent" / "for reviewer agents" cannot be satisfied at runtime.

**Claim (plan, Task 0.2 Step 1):**
> The configuration must (a) deny write access from the brand agent to every path outside `contracts/.branding/`; (b) deny write access from reviewer agents to every path outside `contracts/.scratch/` and `contracts/.branding/<artifact>/reviews/`; (c) deny write access from any agent to `/home/jmsbpp/apps/liq-soldk-dev/`

**Claim (plan, Task 0.2 Step 4):**
> The configuration binds `abrigo-brand-agent` to write-allow on `contracts/.branding/**` and write-deny everywhere else. It binds each reviewer seat (`brand-guardian`, `executive-summary-generator`, ...) to write-allow on `contracts/.scratch/**` ...

**Reality check.** Claude Code's documented `settings.json` permission model (`permissions.allow`, `permissions.deny` with tool patterns like `Write(<glob>)`) is session-scoped — patterns apply to the active session and to any subagent dispatched from that session. Per-agent (per-`subagent_type`) permission scoping, where different `allow/deny` lists bind to different `name:` values in subagent-definition frontmatter, is not a surface the Claude Code documentation describes. The plan's Task 0.2 Step 3 ("use the update-config skill ... handles the settings.json schema correctly") hand-waves past this: the skill helps write correct settings.json, but cannot invent a schema that does not exist.

The plan also shows awareness of the gap (Task 0.2 Step 3: "hand-writing JSON risks schema drift") without naming it. Step 5's smoke test ("dispatch the brand agent with a prompt that asks it to write a file at `contracts/src/test.txt`. Expected: the write is denied by the runtime. If the write succeeds, the configuration is wrong") will in practice succeed (the write will be allowed), at which point the engineer will discover the model doesn't work and the plan falls over.

**Required changes:**
1. Confirm or disprove the per-subagent permission feature by checking Claude Code release notes or the `update-config` skill's documentation before the plan claims to use it. If the feature does not exist, the spec §6.4 "Enforcement model" paragraph and §14 Appendix A require redesign, not just plan edits.
2. If per-agent scoping is unavailable, fall back to one of:
   - **Hooks-based enforcement.** A `PreToolUse` hook matching `Write` and rejecting any path outside `contracts/.branding/` when the calling subagent is a brand or reviewer role. This requires knowing the subagent identity at hook time.
   - **Prompt-discipline-only.** Acknowledge that v1 is prompt-discipline-enforced, drop the "runtime is first line of defense" language from the spec, and add a §11 risk capturing that the enforcement is advisory not coercive.
   - **Dedicated sandbox.** Run the brand agent in a subprocess with OS-level write restrictions. Much heavier; probably overkill for v1.
3. Whichever path is chosen, Task 0.2 Step 5's smoke test must be updated to verify the actually-chosen enforcement path, not a fictional one.
4. If the fallback is prompt-discipline, Task 2.1 Step 7's smoke test ("verify the runtime permissions (Task 0.2) deny the write") is also fictional and needs redesign.

---

## Finding 3 — MAJOR — Task 4.2 fixture methodology is sound, but the real evidence base may not support the claim Task 3.2 Step 4 asks the Claim Auditor to verify

**Severity:** High. Does not block Phase 0–Phase 5, but will block Phase 6 on contact with reality.

**Claim (plan, Task 3.2 Step 4):**
> Smoke test — PASS on grounded claim. Modify the contrived draft to add a citation pointing to a real paragraph in `MACRO_RISKS.md` (use a line range you can verify supports some inflation-erosion claim, or adjust the claim to match what the file says). Dispatch again. Verify the finding PASSes or FLAGs appropriately.

**Evidence (Read of `MACRO_RISKS.md` lines 1–80):** The file is a sketch / in-progress note using arrow-notation pseudocode:
```
MacroRisk {
    LocalInflation       -->    AMP/other currrency , PAXG/ , WBTC ,
    InterestRateShock    -->    stETH yield vs. local stablecoin yield spread
    ...
}
```
followed by scattered prose fragments on pension funds, labor unions, and historical CPI-futures attempts (USA 1985, Brazil 1987). There is no prose paragraph that defensibly grounds a claim of the form "inflation erodes Colombian household savings" — the file gestures at the topic taxonomically but does not state or cite the claim.

Spec §8.3 Evidence Failure Modes explicitly says directional claims PASS only when the source is itself directional, and quantitative claims require a quantitative source. The phrase "inflation erodes savings in underserved-FX markets" is directional — the file's taxonomy entry `LocalInflation --> AMP/other currency, PAXG/, WBTC` can arguably support it, but a Reality Checker operating under the Claim Auditor charter will likely BLOCK the claim for want of prose substance, not PASS it.

**Required changes:**
1. The plan should not assume Task 3.2 Step 4 will find a clean PASS. Rewrite Step 4 as: "Inspect the MACRO_RISKS folder. Identify a file whose prose supports a directional inflation-erosion claim at a specific line range. If no file does, the Claim Auditor PASS test can only be exercised against a claim of the form 'macro-risk proxies include local inflation,' grounded in lines 7–13 of `MACRO_RISKS.md`."
2. Add a precondition check to Phase 4 or Phase 6: the plan cannot proceed past the first draft unless at least one painkiller claim can be grounded. If the MACRO_RISKS notes are not yet fit-for-citation, the plan's pathway to a graduated one-pager is blocked on research, not on agent engineering.
3. Flag this as a spec-level concern too: spec §8.1 names MACRO_RISKS as the "primary" evidence base. If the folder's contents are sketchier than the spec implies, §8.1 is overclaiming.

---

## Finding 4 — MODERATE — Task 1.3's "2-5 minute step" framing is wrong by an order of magnitude

**Severity:** Moderate. Misleads execution planning; does not block correctness.

**Claim (plan, line 3):** "Steps use checkbox (`- [ ]`) syntax for tracking." — implicit, and the plan's overall framing ("2-5 minute steps" promised in the user's original question, which matches the checkbox-per-step convention elsewhere) sets an expectation that every checkbox is a short, atomic action.

**Evidence (plan, Task 1.3):** Step 3 says "Founder writes the values." It names ~25 schema fields (18 hard + 7 soft) from spec §5.2.1. Several are factual-recall (`brand_name`, `founding_date`, `pilot_market`) — genuinely 2-5 minutes. Several are decisions with consequences (`company_stage` picking one of five enum values that maps to Crecimiento's stage field; `current_raising_round` ditto; `cofounder_roles` list requiring accuracy about org structure; `employee_roles` list ditto; `partnership_list` requiring the founder to decide what counts as a partnership). These are not 2-5 minutes of work; they are 30-60 minutes of writing and thinking, and some may require founder offline verification (e.g., confirming `legal_entity_status`).

**Required changes:**
1. Reframe Task 1.3 Step 3 as a "founder work session" rather than a checkbox step. Possibly split into sub-tasks: "1.3a factual recall" (2-5 min), "1.3b stage / round / roles decisions" (30-60 min, may require offline verification), "1.3c soft fields with citations" (variable, deferred until citations exist).
2. Relax the plan's header framing. "Steps use checkbox syntax for tracking" is fine; "2-5 minute steps" is not universally true.

---

## Finding 5 — MODERATE — Phase 7 does not verify the Crecimiento application portal is live and accepting submissions before driving artifacts toward it

**Severity:** Moderate. The entire Phase 7 motivation collapses if Crecimiento is closed.

**Claim (plan, Task 7.1 Step 2):** "The founder copies the form from Crecimiento's application page into `questions.md`."

**Gap.** No precondition task verifies that Crecimiento's current intake cycle is open, deadline is future, and the form schema hasn't changed since the spec was drafted. Spec §11.2 acknowledges this as a risk ("If the Crecimiento submission deadline slips or the foundation's program changes shape, the spec's artifact catalog remains valid") but the plan does not translate the risk into a concrete gating check.

**Required changes:**
1. Add Task 7.0 — "Verify Crecimiento intake is open." A single step: founder navigates to the Crecimiento application portal, confirms the cycle is active, records the deadline in `contracts/.branding/forms/crecimiento/intake-status.md` (gitignored). If the cycle is closed, Phase 7 pauses and the plan's work product is the one-pager from Phase 6 plus the infrastructure; the Crecimiento-specific output is deferred.
2. Consider whether Task 7.5 ("Founder submits the form") belongs in this plan at all. The founder submitting is a manual step the plan cannot verify. Step 1's "Define success criteria" is "The founder pastes each answer from `answers.md` into the Crecimiento application form and submits." — success criterion "submits" is not engineering-verifiable; it is a human action the plan has no instrument to confirm. This is a mild fantasy-task flag: the task can be marked done without the work being done.

---

## Finding 6 — MINOR — Task 2.1 Step 7 smoke test path may not exist

**Severity:** Low.

**Claim (plan, Task 2.1 Step 7):** "Dispatch the agent with a prompt asking it to modify `contracts/src/vaults/VaultBase.sol`."

**Evidence (gitStatus):** The gitStatus shows `src/vaults/` as untracked, but does not list a `VaultBase.sol` specifically. The file may not exist. If the smoke test points the agent at a nonexistent path, the write may "fail" for the wrong reason (file not found rather than permission denied), obscuring whether Task 0.2's enforcement is actually working.

**Required changes:** Either verify `contracts/src/vaults/VaultBase.sol` exists before writing Task 2.1, or change the target to a file known to exist (e.g., `contracts/foundry.toml`, which is in gitStatus as modified). The smoke test is meaningful only if the file exists.

---

## Finding 7 — MINOR — Graduated artifacts sit entirely outside version control; Task 6.4 / 7.4 "No commit" decisions are correct but leave the final deliverables with zero provenance trail

**Severity:** Low. Not a plan defect per se; a design consequence worth naming.

**Observation.** Task 0.3 gitignores `.branding/`, which is correct per spec §5.3. Task 6.4 graduates the one-pager to `contracts/.branding/artifacts/one-pager.md` and marks "No commit. Gitignored." Task 7.4 does the same for `forms/crecimiento/answers.md`. Task 7.5 creates `forms/crecimiento/submitted.md` as the frozen-forever record — also gitignored.

The `submitted.md` file is the only record of what was sent to Crecimiento. It lives only on the founder's disk, with no backup via `git push`. If the worktree is deleted, resliced, or corrupted, the submitted record is lost. The spec's provenance model (source manifests, facts snapshots, diff rationales) is internally consistent, but the chain-of-custody ends at an ungitignored file on one machine.

**Required changes (optional):**
1. Consider whether `submitted.md` specifically should be moved out of the gitignored tree to `contracts/docs/abrigo-submissions/` or similar, so there is at least one committed record per submission.
2. Or, add a Task 7.6: "Manually copy `submitted.md` to an external backup location (personal vault, cloud drive) the founder trusts."
3. If the decision is to leave everything ungitignored on purpose, add a §11 risk to the spec naming the no-backup condition.

---

## Spec Rev 2 Coverage Spot-Check

The plan's "Spec-Coverage Self-Check" section maps spec sections to tasks. Rev 2 additions are covered as follows:

| Rev 2 addition | Plan coverage | Verified? |
|---|---|---|
| Claim Auditor role (§7.1, §7.2) | Task 3.2 authors the dispatch-prompt augmentation for the Reality Checker | Yes — Task 3.2 Steps 1–5 explicitly cover per-invocation augmentation, BLOCK/PASS behavior, and name-collision non-interference |
| Charter-overlap tiebreakers (§7.2.1) | Task 3.1 Step 1(g) | Yes — template contract includes tiebreaker enforcement for Brand Guardian (skip CIS-owned findings) and Proposal Strategist (read Claim Auditor verdict first) |
| Revision-stamping rigor (§7.4 file-naming convention) | Task 5.1 Step 3 | Yes — "The procedure must explicitly check that all three verdict files reference the same `v{N}` before declaring graduation" |
| Source-manifest / evidence-staleness protocol (§8.4) | Tasks 4.1, 4.2, 5.1 Step 5 | Yes — format specified, round-trip test specified, publish-check specified |
| New §11 risks (11.8 facts mid-cycle, 11.9 cross-artifact, 11.10 rename, 11.11 external write-deny) | Task 2.1 Step 1(j) facts-snapshot; Task 2.1 implicit for 11.9; Task 1.3 brand_name_qualifier; Task 0.2 Step 1(c) external write-deny | Yes, though 11.9's "forbidden from paraphrasing traction numbers" is not called out explicitly in Task 2.1's behavioral contract — engineer has to infer it from §5.2.1 |
| Appendix A (permissions model) | Task 0.2 | Covered, but see Finding 2 — the task cannot be executed as written |
| Appendix B (un-archive reviewer agents) | Task 0.1 | Covered, but see Finding 1 — the task paths are wrong |

**Gap:** Spec §11.9 ("brand agent is forbidden from paraphrasing traction numbers, team sizes, stage labels, or similar quantitative facts and must instead substitute the verbatim `facts.yml` value") is not visible in the plan's Task 2.1 Step 1 behavioral contract. It should be added as an explicit behavioral requirement.

---

## Task 0.1 Step 5 Charter-Drift Check — Is §7.2 sufficient?

**Question:** Is spec §7.2 a sufficient specification of each reviewer's charter to detect drift?

**Assessment:** Partially. §7.2 gives each reviewer one paragraph of charter prose (what the seat enforces, what it does not). For detecting **gross** drift — e.g., the archived Brand Guardian turns out to be a generic content creator, not a brand-rules enforcer — §7.2 is sufficient; the engineer can read the archived agent's prompt and tell at a glance whether it matches.

For detecting **subtle** drift — e.g., the archived Brand Guardian enforces "brand voice" in the general sense but not the six Abrigo-specific positioning principles; the archived Content Creator evaluates written copy but not spoken-word pacing — §7.2 is not specific enough. §7.2's Content Creator paragraph says "Evaluates spoken-word voice, pacing, listener retention, transition craft, and the 30-second hook." The archived agent is almost certainly a generic content creator without that spoken-word specificity.

**Consequence for Task 0.1 Step 5:** Every reviewer is likely to have at least subtle drift from §7.2, which triggers the spec §15 choice between (a) amend the agent's prompt, (b) amend §7.2 and re-review, or (c) author Abrigo-specific variants. Option (c) is the path of least resistance and likely the right default for v1.

**Required changes:**
1. Set Task 0.1 Step 5's default resolution to option (c) — author Abrigo-specific variants at `contracts/.claude/agents/abrigo-{seat}.md` — rather than treating all three options as equally likely. This changes the committed-surface file count and should be reflected in spec §5.1.
2. If option (c) is the default, Task 0.1 becomes larger than it currently appears: the engineer is not just `mv`-ing five files; the engineer is authoring five Abrigo-specific reviewer agents. That work is closer to Task 2.1's scope than to a Phase 0 bootstrap step, and may deserve its own phase.

---

## Fantasy-Task Scan

Default to finding tasks whose success criteria cannot be concretely verified by an engineer at completion.

- **Task 7.5 Step 1** — "The founder pastes each answer from `answers.md` into the Crecimiento application form and submits." — success criterion is a human action; the plan has no instrument to verify completion. Flagged in Finding 5.
- **Task 6.1 Step 4** — "Founder intuition-check before review." — subjective. Not an engineering-verifiable success criterion; acceptable because Step 4 is a judgment gate, not a deliverable.
- **Task 8.1 Step 3** — "Update memory files based on learnings. ... Do not edit them speculatively; only edit them against concrete lessons." — relies on the engineer's discipline, not on a verification command. Acceptable because memory-file editing is inherently editorial.
- **Task 2.1 Step 3** — "Pre-flight dry-read. Before smoke-testing, read the entire prompt aloud." — "aloud" is rhetorical; the verifiable version is "for each behavioral requirement in Step 1, grep / annotate the paragraph of the prompt that addresses it; fail any requirement that is not addressable."

No additional fantasy tasks beyond those already flagged.

---

## "No Commit" Decision Audit

Tasks that say "No commit — gitignored":

| Task | Target path | Under `.branding/`? | Decision correct? |
|---|---|---|---|
| 1.1 | `contracts/.branding/` tree | Yes | Yes |
| 1.2 | `contracts/.branding/README.md` | Yes | Yes |
| 1.3 | `contracts/.branding/facts.yml` | Yes | Yes |
| 4.2 | ephemeral `_staleness-test/` | Yes | Yes |
| 6.1, 6.2, 6.3, 6.4 | `contracts/.branding/artifacts/one-pager/**` and graduated `one-pager.md` | Yes | Yes |
| 7.1, 7.2, 7.3, 7.4, 7.5 | `contracts/.branding/forms/crecimiento/**` and graduated / submitted files | Yes | Yes |

All "No commit" decisions are consistent with the gitignore rule from Task 0.3. See Finding 7 for a separate concern about the consequence (final deliverables have no committed provenance).

---

## Ship-Readiness Assessment

**Verdict:** NEEDS WORK.

**Rationale:** Findings 1 and 2 are blockers that halt Phase 0 before any real work begins. Finding 1 is a mechanical fix (correct paths). Finding 2 is architectural (the spec's enforcement model may not map to any real Claude Code feature, which invalidates §6.4 and §14 as written). Either one alone is ship-blocking; the pair makes it clear the plan was written against a mental model of the spec rather than against a verified runtime surface.

**Required revisions before this plan is executable:**
1. (CRITICAL) Update Task 0.1 paths to reflect the real archived locations with category-prefixed filenames; simultaneously update spec §15 Appendix B.
2. (CRITICAL) Verify Claude Code's per-subagent permission feature exists as described. If not, redesign Task 0.2 and spec §6.4 / §14 to use hooks, sandbox, or prompt-discipline fallback. Smoke tests in Task 0.2 Step 5 and Task 2.1 Step 7 must match the chosen mechanism.
3. (HIGH) Add a realistic assessment of what the MACRO_RISKS evidence base can defensibly ground. Adjust Task 3.2 Step 4 to cite a claim the file actually supports, or flag that the evidence base needs a pass before Phase 6 can succeed.
4. (MEDIUM) Reframe Task 1.3's time cost.
5. (MEDIUM) Add Task 7.0 to verify Crecimiento intake is open.
6. (LOW) Verify Task 2.1 Step 7's target file exists or substitute a known file.
7. (LOW) Decide whether graduated/submitted files should have at least one committed backup.
8. (MEDIUM) Add §11.9's "forbid paraphrasing quantitative facts" requirement to Task 2.1's behavioral contract.
9. (MEDIUM) Reset Task 0.1 Step 5's default resolution to option (c) — Abrigo-specific reviewer variants — because §7.2's charter specificity is likely to be exceeded by drift in every archived reviewer.

**Estimated revision effort:** 4–8 hours of plan/spec editing, plus whatever research is needed to confirm or disprove Finding 2's Claude Code feature question (possibly 30–60 minutes of Claude Code docs + `update-config` skill inspection).

**Reviewer's recommendation to founder:** Hold Phase 0 execution until Findings 1 and 2 are resolved at the spec level. The remaining findings can be addressed as plan-only edits during or immediately after the spec revision.

---

**Evidence locations:**
- Archived reviewer agents (real paths): `/home/jmsbpp/.claude/agents/_archived/design/design-brand-guardian.md`, `_archived/support/support-executive-summary-generator.md`, `_archived/marketing/marketing-content-creator.md`, `_archived/sales/sales-proposal-strategist.md`, `_archived/specialized/specialized-cultural-intelligence-strategist.md`
- Evidence base: `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/MACRO_RISKS.md` (lines 1–80 inspected)
- Tier 1 methodology spec: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` (exists, confirmed via Glob)
- Plan under review: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/plans/2026-04-15-abrigo-branding-agent.md`
- Spec under review: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md`
