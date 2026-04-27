# Abrigo Branding Agent — Reality-Check Review

**Reviewer:** TestingRealityChecker (evidence-based lens)
**Target spec:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md`
**Date:** 2026-04-15
**Evidence base for this review:** direct filesystem inspection of the paths the spec pins, the Claude subagent catalog at `/home/jmsbpp/.claude/agents/`, and the memory files at `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/`.

---

## Executive Verdict: **NEEDS WORK**

The spec is internally coherent and stylistically mature. Its pinned evidence paths mostly exist. But it rests on four structural assumptions that filesystem inspection contradicts or that the spec itself hand-waves. Two of them (reviewer-agent availability and the read-only/write-only boundary) are **BLOCK**-class: the spec is not buildable as written without resolving them. The remaining findings are fixable with targeted edits, but the agent should not advance to an implementation plan until the blockers are closed. Default-to-NEEDS-WORK holds; the spec has not cleared the evidence bar required for PASS.

---

## Findings

### Finding 1 — BLOCK: Five of six "specialized reviewer agents" are in `_archived/` and cannot be assumed available

**What the spec says.** §7.1, §7.2, and §11.4 assume six reviewer agents are available in the current Claude Code subagent catalog: Brand Guardian, Reality Checker, Executive Summary Generator, Content Creator, Proposal Strategist, Cultural Intelligence Strategist. The review-triad table in §7.1 binds each artifact type to a specific third-seat agent by name.

**What I verified.** Globbing `/home/jmsbpp/.claude/agents/**/*.md` for each name:

| Agent name | Path | Status |
|---|---|---|
| Brand Guardian | `_archived/design/design-brand-guardian.md` | **ARCHIVED** |
| Reality Checker | `testing/testing-reality-checker.md` | Active, but see Finding 2 |
| Executive Summary Generator | `_archived/support/support-executive-summary-generator.md` | **ARCHIVED** |
| Content Creator | `_archived/marketing/marketing-content-creator.md` | **ARCHIVED** |
| Proposal Strategist | `_archived/sales/sales-proposal-strategist.md` | **ARCHIVED** |
| Cultural Intelligence Strategist | `_archived/specialized/specialized-cultural-intelligence-strategist.md` | **ARCHIVED** |

Five of the six reviewer seats the spec commits to by name live under `_archived/`. Files under `_archived/` are, by convention in this layout, not part of the active subagent catalog that the Claude Code harness will load.

**Gap.** The spec promises a review triad that depends on five archived agents. §11.4 flags this as an "open risk" but does not commit to a resolution; the body of the spec proceeds as if the agents are available. Every artifact lifecycle in §7.4 is predicated on three-agent parallel dispatch with specific charters. If the agents are not available, either (a) the spec must define fresh per-seat agent definitions (pushing real design work from §11.4 back into the body of the spec), or (b) the spec must describe a fallback configuration (e.g., single reviewer with multi-pass prompts) — which would change the review workflow materially.

**Severity.** BLOCK. An implementation plan cannot be drafted against §7 until this is resolved.

**Required change.** Either:
1. Un-archive and re-validate the five reviewers' charters against the charters §7.2 assigns them, with file-path citations in the spec, **or**
2. Commit the spec to authoring fresh per-seat agent definitions (§5.1 already reserves `contracts/.claude/agents/abrigo-brand-reviewer-*.md` for this), list the seats that need authorship, and scope that authorship as part of the implementation plan. In this case, delete the reuse promise from §5.1 and §7.1.

Either fix must be explicit in §7 or §5.1 — not deferred to §11.

---

### Finding 2 — BLOCK: The "Reality Checker" active agent is a code-QA agent, not a copy-claims auditor

**What the spec says.** §7.2 assigns the Reality Checker to "verify every painkiller claim, every '10x better than' comparison, and every sizing / prevalence assertion against the painkiller evidence base." The Reality Checker is Seat 2 on every artifact triad. The memory file `project_abrigo_painkiller_evidence_base.md` similarly expects the Reality Checker to read the MACRO_RISKS folder and emit per-claim PASS/FLAG/BLOCK.

**What I verified.** The only active "reality checker" agent in the catalog is `/home/jmsbpp/.claude/agents/testing/testing-reality-checker.md`. Its category (`testing/`) and filename prefix (`testing-`) signal that it's scoped to software/test QA — the agent currently reviewing this spec is that agent, and my system prompt is entirely about screenshot evidence, responsive layouts, "production readiness," and Laravel-or-simple-stack inspection. Nothing in this agent's charter addresses painkiller copy, source-citation verification, or research-folder grounding.

**Gap.** The spec assumes a "Reality Checker" whose charter is literature / evidence-citation audit. The active catalog has a Reality Checker whose charter is integration-test visual QA. These are different agents. Dispatching the active one against a one-pager will produce garbage — it will look for screenshots of the one-pager instead of auditing its citations.

**Severity.** BLOCK. This is the same class of problem as Finding 1 but worse because the spec treats Reality Checker as a given rather than as an open risk.

**Required change.** Either authoring a new `abrigo-brand-reality-checker` reviewer seat with the evidence-citation charter, or explicitly re-scoping the existing `testing-reality-checker` (e.g., by wrapping it with a copy-specific prompt). Commit the decision in §5.1 and rename the seat in §7 to remove the collision with the active agent's name.

---

### Finding 3 — BLOCK: "Read-only against codebase, write-only against .branding/" is hand-waved, not enforced

**What the spec says.** §6.4 declares: "The agent is read-only against the codebase, memory files, and evidence base. The agent is write-only against `contracts/.branding/`. Any attempt to modify files in `src/`, `test/`, `script/`, `docs/superpowers/specs/`, memory, or anywhere else in the worktree is out of scope and must be refused."

**What I verified.** Claude Code enforces tool boundaries via subagent configuration — the tool allowlist and deny list are structured metadata in the agent's frontmatter (for subagent-definition files) or in harness settings, not prose declarations. I checked `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.claude/agents/` (empty) and `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.claude/agents/` (empty). No agent definition currently exists to compare against. The spec itself gives zero guidance on what tool allowlist / deny-patterns will enforce the §6.4 boundary. It says "must be refused" — which is a prompt-discipline statement, not a configuration statement.

**Gap.** A subagent that has `Edit` and `Write` tools enabled and a prose rule "don't touch `src/`" will touch `src/` as soon as a reviewer in the same session asks it to fix a compile error. The boundary §6.4 promises cannot be enforced by prompt alone. The user's long-running memory file `feedback_scripts_only_scope.md` marks this class of constraint as NON-NEGOTIABLE, which reinforces that the project takes it seriously — but the spec does not translate that seriousness into a concrete configuration claim.

**Severity.** BLOCK. This is the architecturally load-bearing scope-containment claim of the whole design; §3 (Non-Goals) and §6.4 both rest on it. The spec must either commit the enforcement mechanism or acknowledge that enforcement is prompt-discipline only and describe the remediation protocol when the boundary is breached.

**Required change.** Add a subsection (probably §6.5) titled "Tool Boundary Enforcement" that specifies: (a) the allowed tool set for the brand-agent (likely `Read`, `Write` restricted to `.branding/`, `Grep`, `Glob`; not `Edit` or `Bash`), (b) the deny patterns on `Write` (restricted to `contracts/.branding/**`), (c) explicit enumeration of *how* that configuration is encoded (subagent frontmatter? settings.json hooks? harness-level permissions?), (d) what happens if the agent attempts a disallowed write (refusal? harness-level denial? error-path behavior?). If the only available enforcement is prompt discipline, the spec must say so and describe the review protocol that catches breaches.

---

### Finding 4 — FLAG: Review lifecycle can graduate artifacts on stale drafts

**What the spec says.** §7.4 defines a seven-step lifecycle. Step 4: "If all three seats return PASS, the artifact graduates." Steps 5–6: on FLAG or BLOCK, re-dispatch brand agent with draft plus all three verdict files; reviewers re-dispatch against v2.

**What I verified.** Reading the lifecycle carefully, several concrete failure modes are not closed:

1. **Stale-verdict race.** §7.6 says reviewers run in parallel via `run_in_background: true`. If the founder triggers a revision before all three verdicts land — or if the brand agent's revision lands before the review re-dispatch fires — v2 may be reviewed against partial v1 verdict context, or v1 verdicts may be re-applied to v2 without re-dispatch. The spec says "the orchestrator waits for all three verdicts" but does not say what file predicates determine "all three verdicts landed" or how the orchestrator detects the revision is against v2 not v1.

2. **PASS from an old draft.** Step 4 says "if all three seats return PASS, the artifact graduates." It does not say the three PASSes must be against the *same* revision. If reviewer A PASSes v1, reviewer B BLOCKs v1, v2 is drafted, reviewer B PASSes v2, and reviewer C never reruns — does the artifact graduate? By a strict reading of step 4, yes. That's wrong.

3. **Facts.yml mid-cycle edit (see also Finding 7).** The founder is the source of truth for `facts.yml`. If the founder edits it between v1 draft and v2 review, the brand agent's v2 may cite new facts that the reviewer's v1 context doesn't know about. Nothing in §7.4 detects this.

4. **Override accumulation.** §7.4 step 8 allows the founder to override any BLOCK. Step 7 says to escalate after two consecutive BLOCK cycles. These interact: the founder may override rather than iterate, and overrides accumulate across artifacts (§11.6 flags this but defers).

**Gap.** The spec describes the happy path cleanly. It does not define the state machine rigorously enough to prevent accidental graduation on incomplete reviews.

**Severity.** FLAG. The risk is real but containable with a revision-stamping rule.

**Required change.** Add to §7.4:
- Every draft file and every verdict file carries an explicit revision number (`v{N}`) in the filename (the spec already implies this; make it a rule).
- The orchestrator graduates an artifact only if three PASS verdict files exist *with matching revision numbers*, and that revision is the highest present.
- A revision invalidates all verdict files at lower revisions for graduation purposes (they are retained for history; they do not count toward quorum).
- Add a `facts.yml` hash to the draft header so reviewers can detect whether the facts surface shifted between draft and review.

---

### Finding 5 — FLAG: "10x better" and "painkiller validated" appear as positioning commitments, not auditable claims

**What the spec says.** §4.1 lists "10x improvement over existing alternatives" as positioning principle #4 and quotes "painkiller, not a vitamin" as principle #3. The brand agent is required to produce copy that obeys these principles. §8 (Evidence Grounding) requires every "10x better than" comparison to carry a citation.

**What I verified.** The positioning-principles memory file (`project_ran_positioning_principles.md`) confirms the 10x claim is framed as a **positioning rule** for the product's copy, not as a product property the spec itself is asserting. Every first-person assertion of "10x better" in the spec appears inside a quoted rule, not as a claim the spec is making about Abrigo's actual performance over USD savings accounts / informal dollarization / remittance services.

This is a meaningful distinction, and the spec mostly respects it. However, §2 Goals does slip: "Ground every painkiller-adjacent claim in the existing macro-risk research folder, so copy is evidence-backed rather than marketing-puff." That's fine. §4.3 is also fine — every such claim must carry a file-and-line citation. But the spec does not explicitly say **what happens when no Tier-A-or-B evidence exists for the 10x claim.** §8.3 says "Citation supports a weaker version of the claim → FLAG. Propose softened wording" — but that assumes a citation exists at all. What if no evidence supports any form of the 10x claim against USD savings? §8.3's first bullet says "Claim has no citation → BLOCK. Drop the claim or ground it." Combined, these read "drop the claim if ungrounded" — but §4.1 lists 10x as a **positioning principle** that binds all story copy.

**Gap.** If an artifact's audience expects a competitive comparison and no evidence grounds the 10x claim, the brand agent has to either (a) drop the 10x framing (violating positioning principle #4), or (b) soften to "meaningfully better" (violating positioning principle #4's specific 10x magnitude). The spec does not close this contradiction. Strict reading: Reality Checker BLOCK wins; positioning bends. In practice, this tension will appear every time the evidence base says "directional only."

**Severity.** FLAG. The spec's citation protocol does actually resolve this — soften or drop — but the resolution conflicts with a positioning principle presented as absolute. The spec should either (a) demote "10x" from principle-level to aspiration, or (b) explicitly say that Reality Checker's BLOCK on an ungrounded 10x claim overrides Brand Guardian's principle-compliance check.

**Required change.** Add a precedence rule to §7.5: when Brand Guardian and Reality Checker contradict over *evidence-grounding of positioning claims specifically*, Reality Checker wins. Positioning principle #4 is reworded in §4.1 from "The pitch claims a 10x improvement" to "The pitch positions Abrigo as a step-change improvement where evidence supports, and softens to the specific grounded magnitude where it does not." This preserves the posture without the unfalsifiable commitment.

---

### Finding 6 — FLAG: Tier 1 feasibility spec is pinned as "per-channel verdicts" but it is a methodology spec, not a completed survey

**What the spec says.** §8.1 lists the Tier 1 feasibility doc as secondary evidence: "per-channel literature verdicts for inflation and remittance shock."

**What I verified.** Read the file at the pinned path. It is Rev 3 dated 2026-04-14; its §3 (Objective) calls for per-channel literature verdicts and §9 defines the verdict vocabulary (`CONFIRMED`, `PARTIAL_SUPPORT`, `DISCONFIRMED`, `NO_LITERATURE_SUPPORT`, `PROCEED`, `PIVOT_TO_TIER_1B`, `RETIRE_THESIS`, `MIXED`). §11 defines the deliverable as a separate file: `contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md`. Globbed: **that file does not exist.** The verdicts are prospective, not retrospective.

**Gap.** The brand agent cannot cite "the Tier 1 verdict for channel $\pi$" because no such verdict has been produced. The spec treats the feasibility doc as evidence; it is in fact a pre-registered plan to *produce* evidence. §9's modal expected outcome is `PIVOT_TO_TIER_1B`, meaning even when the survey runs, the likely outcome is "not yet confirmed, go do regression" — which is not citable painkiller ground for a pitch today.

**Severity.** FLAG. The spec is citing future work as current work. The primary MACRO_RISKS folder contents are substantive and do ground directional claims; the Tier 1 feasibility doc does not yet ground quantitative verdicts.

**Required change.** Rewrite §8.1's second bullet to: "Tier 1 feasibility **methodology** spec (`2026-04-14-inflation-mirror-tier1-feasibility-design.md`) — defines the per-channel literature verdict protocol; the actual verdict deliverable is at `contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md` **which does not yet exist**. Painkiller claims citing Tier 1 output are BLOCKed until the deliverable lands." This makes the temporal status honest.

---

### Finding 7 — FLAG: Risks §11 missed: facts.yml mid-cycle editing, cross-artifact disclosure contradictions

**What the spec says.** §11 enumerates seven open risks: trademark, Crecimiento priority, evidence-base coupling, reviewer-agent availability (see Finding 1), reviewer contradictions, founder override traceability, Tier 2 disclosure scope.

**What is missing.**

1. **`facts.yml` edited mid-review-cycle.** The founder is the sole editor of `facts.yml`; the agent reads it. If the founder updates team size or traction figures while v1 of the one-pager is under review, v2 may cite different numbers than v1. Reviewers who PASSed v1's claims on the basis of v1's facts may not even re-review v2 if the revision is driven only by a reviewer's FLAG on something unrelated (see Finding 4). Result: shipped artifact cites stale facts.

2. **Cross-artifact disclosure contradiction.** The Crecimiento form asks for current traction; the one-pager and 3-min pitch also cite traction. If the founder updates `facts.yml` between producing the one-pager (Monday) and the Crecimiento form (Friday), the two artifacts will contain different traction figures. The spec has no concept of cross-artifact consistency audit — each artifact is produced and graduated independently. Nothing detects that `artifacts/one-pager.md` and `forms/crecimiento/answers.md` are now mutually contradictory. Worse, `submitted.md` freezes the contradiction.

3. **Brand-name rename mid-lifecycle.** §11.1 acknowledges the "Abrigo" rename risk but says rename would "require regenerating artifacts." It does not define what happens during the rename: are in-flight reviews discarded? Do already-submitted artifacts get a migration note? The spec is silent.

4. **Evidence-base write access.** The agent is described as read-only against the MACRO_RISKS folder (§6.4). The folder lives at `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` — outside the contracts worktree. Worktree-scoped permissions may not cover external paths. If the agent is somehow granted filesystem write on `liq-soldk-dev/`, the spec's scope-containment claim breaks silently. §6.4 lists paths to refuse but does not include external paths explicitly.

**Severity.** FLAG. Not a blocker, but the §11 list should be extended so downstream implementation plans consider these failure modes.

**Required change.** Add to §11:
- **11.8 `facts.yml` Volatility.** Founder edits during an in-flight review cycle invalidate reviewer context. Add a facts-hash in every draft and every verdict file; mismatches require re-review.
- **11.9 Cross-Artifact Consistency.** Traction numbers, team size, and stage figures must be consistent across one-pager, pitches, and submitted form answers. Add a protocol for cross-artifact audit (probably a lightweight human-eye pass rather than a new reviewer seat).
- **11.10 External Read Paths.** The MACRO_RISKS and refs folders are outside the contracts worktree. The agent's read permissions must extend to these paths; its write permissions must not. Verify during agent-definition authorship.

---

### Finding 8 — FLAG: "Background dispatch" assumes orchestration infrastructure the spec does not scope

**What the spec says.** §6.2: "The agent is invoked via the `Agent` tool with `run_in_background: true`. The founder issues one human-language trigger; the agent runs asynchronously; the founder is notified when the draft lands." §7.6: reviewer dispatches are also `run_in_background`. §10 describes "canonical request forms" that an orchestrator translates into `Agent` dispatches.

**What I verified.** "Orchestrator" is mentioned seven times across the spec but never defined. §10 says "a foreground Claude session or orchestrator." The spec does not commit to whether the orchestrator is:
- The founder's foreground Claude Code session (which then has to track four background agents' completion, parse their output files, trigger revisions, detect graduation-quorum, etc.); or
- A future meta-agent (§7.6 parenthetically mentions "or a future meta-agent"); or
- A harness-level hook configured in `settings.json`.

Each of these has materially different properties. The `run_in_background: true` mechanism returns a background shell handle for Bash; for the `Agent` tool, the semantics of background dispatch are less commonly exercised. The spec treats it as given.

**Gap.** A reader tasked with implementing the spec does not know whether to build an orchestrator, use an existing one, or defer the orchestrator question. §7.4's lifecycle has real state (revision counter, quorum tracking, graduation detection, contradiction escalation) that someone has to implement somewhere.

**Severity.** FLAG. The spec is code-agnostic per project rules (good), but it is under-specifying who/what holds the lifecycle state.

**Required change.** Add §6.2.1 "Orchestrator Scope" committing to the simplest sufficient answer. Likely: "Orchestrator responsibility for v1 is the founder's foreground Claude Code session, which uses the `Agent` tool for each dispatch and reads the resulting draft and verdict files manually. A meta-agent is explicitly out of scope for v1 and deferred to the follow-on capabilities list in §12." That makes the infrastructure question honest and scopes away the hardest part.

---

## Summary Table of Severities

| Finding | Subject | Severity |
|---|---|---|
| 1 | Five of six reviewer agents are archived | BLOCK |
| 2 | Reality Checker in active catalog is a code-QA agent, not copy-claim auditor | BLOCK |
| 3 | Tool-boundary enforcement is prose-only, not configuration | BLOCK |
| 4 | Review lifecycle can graduate on stale-revision verdict set | FLAG |
| 5 | "10x better" positioning principle contradicts evidence-grounding when evidence is weak | FLAG |
| 6 | Tier 1 "per-channel verdicts" citation is a methodology, not a verdict | FLAG |
| 7 | §11 risks missed: facts.yml volatility, cross-artifact consistency, brand-name rename, external-path write | FLAG |
| 8 | "Orchestrator" invoked but undefined | FLAG |

Three BLOCKs. Five FLAGs. Verdict: **NEEDS WORK**.

---

## Concrete Required Changes to Advance to PASS

Before this spec is ready for implementation planning, the following are required (in priority order):

1. **Resolve reviewer-agent availability (Finding 1).** Either un-archive and reconcile charters, or commit to authoring fresh seat definitions. Move this from §11.4 into §5.1 / §7.1. This is the biggest structural gap.

2. **Disambiguate Reality Checker (Finding 2).** The copy-auditor Reality Checker and the test-QA Reality Checker are different roles and the spec currently conflates them. Rename or re-scope.

3. **Specify tool-boundary enforcement (Finding 3).** Add §6.5 with concrete allowlist / deny-pattern / enforcement-mechanism claims. Without this, the scope-containment guarantee is fiction.

4. **Tighten the lifecycle state machine (Finding 4).** Revision-number rule + facts-hash rule. Less than a page of spec; closes the stale-verdict race.

5. **Correct temporal-status claims (Finding 6).** The Tier 1 verdict deliverable does not exist; saying it does is a factual error. Rewrite §8.1.

6. **Reconcile the 10x-evidence tension (Finding 5).** One sentence in §7.5 plus a softened phrasing in §4.1.

7. **Extend §11 (Finding 7).** Three new risk bullets. Cheap.

8. **Define orchestrator scope (Finding 8).** One subsection. Commits the spec to the simplest workable answer.

---

## What Was Verified Positively

Not everything is broken; the reality check turned up real craft too:

- `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` exists and contains eight substantive files (~47KB across .md, not counting checkpoint/backup files). Spot-read of `MACRO_RISKS.md` confirms the folder is genuine research substance — macro-risk proxy taxonomy, USA 1985 and Brazil 1987 CPI futures history, income-settlement theory, price-vs-income-settlement tradeoffs — and *can* ground directional painkiller claims, within the limits of Finding 5. The painkiller-evidence-base memory file's summary of the folder (`project_abrigo_painkiller_evidence_base.md`) is accurate.
- `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` exists and is substantive (23KB, Rev 3). Its content is a methodology spec, not a verdict deliverable — see Finding 6.
- `contracts/notebooks/ranPricing.ipynb` exists.
- The memory files the spec defers to (positioning principles, two-tier field rule, painkiller evidence base, brand name, product framing) all exist and contain usable content that the agent prompt can reference.
- The scratch directory convention (`contracts/.scratch/`) is correctly observed; existing reviews for the Tier 1 spec are at `.scratch/2026-04-14-tier1-*-review-*.md`, matching the convention the three-way-review memory file documents.
- §3 Non-Goals correctly excludes decentralization-selling, engineering-spec drafting, and auto-submission.
- §4.5's dual-narrative requirement (household + LP) is a real improvement over single-protagonist copy and is not standard; the spec deserves credit for requiring it.
- §8.3's evidence-failure-mode table is the single strongest piece of the spec; it gives reviewers a concrete decision procedure.

---

## Final Note

The spec is well-written and obviously thought through. Its weaknesses are concentrated in two areas: (1) assuming infrastructure (reviewer agents, orchestrator, tool-boundary enforcement) that it has not verified exists in the form it needs, and (2) elevating positioning claims ("10x better," "painkiller validated") to principle status in a way that will contradict its own evidence-grounding protocol under the likely case that evidence is directional rather than quantitative. Neither is hard to fix. Both must be fixed before the spec is buildable.

Do not advance to implementation plan until at minimum Findings 1, 2, and 3 are resolved.
