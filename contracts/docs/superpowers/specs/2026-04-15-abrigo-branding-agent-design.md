# Abrigo Branding Agent — Design Spec

**Status:** Draft Rev 3
**Date:** 2026-04-15
**Scope:** Design contract for a specialized, background-dispatched brand agent (§0) plus the gitignored workspace it reads from and writes to. Covers agent responsibilities, workspace layout, review workflow, evidence-grounding protocol, and artifact catalog.
**Out of scope:** the actual subagent prompt text, review-agent prompt text, executable code or scripts, runtime-configuration syntax, any engineering of the underlying RAN / vault stack. This spec is code-agnostic per the project's "no code in specs or plans" rule; an implementation plan is a downstream artifact.

**Revision history:**
- Rev 1 (2026-04-15): initial draft.
- Rev 2 (2026-04-15): addresses three-way review findings — resolves the archived-reviewer-agent dependency, the name collision between the existing Reality Checker and the copy-claim auditor charter, the prose-only boundary promise, filename-convention contradictions, facts.yml schema gap, reviewer-charter overlaps, evidence-staleness gap, terminology drift, code-rule leaks, §4.1 memory duplication, missing risks, and the orchestrator term. Corrects the Tier 1 citation from an aspirational deliverable to the methodology spec.
- Rev 3 (2026-04-15): addresses three-way plan-review findings that surfaced two architectural defects propagated from Rev 2. (a) Appendix B §15 filenames were wrong — the archived agents live with category prefixes under `_archived/<category>/<category>-<name>.md`; corrected the source paths and committed to rename-on-un-archive so the active names are clean. (b) The Rev 2 enforcement model in §14 Appendix A assumed Claude Code supports per-subagent write allow/deny patterns in `settings.json`; verification found this is not a documented feature. Replaced with a PreToolUse hook as the primary runtime gate, with session-level permissions as a second layer. Also: corrected stale "Reality Checker" references in §9 to "Claim Auditor," added a Crecimiento-intake-open pre-check risk (§11.12), added a MACRO_RISKS-evidence-fitness risk (§11.13), and added the "never paraphrase quantitative facts" behavioral requirement to §6.1 (carried over from §11.9).

---

## 0. Glossary

- **Abrigo** — working external brand name for the company, superseding "ThetaSwap" for all pitch, hackathon, marketing, and user-surface copy. Spanish for *shelter / coat*. The repository itself is not renamed; the brand name applies only to external-facing artifacts.
- **RAN** — Range Accrual Note. The permissionless on-chain instrument the product issues. See `contracts/notebooks/ranPricing.ipynb`.
- **Mento local stablecoin** — a local-currency-pegged stablecoin in the Mento ecosystem (e.g. cCOP, cKES, cREAL). Used as the unit-of-account leg against a macro-factor proxy leg.
- **Mission = underserved-FX** — shorthand for countries whose local currency is weak relative to the US dollar, whose populations bear asymmetric macro-shock risk.
- **Pilot = Colombia** — the first concrete market the product is calibrated to (via cCOP pairs and Colombian macro data: CPI, TRM, DANE, BanRep, remittance corridors).
- **Painkiller** — Y-combinator-style framing: a product that addresses a real, felt, costly problem the user is already paying to avoid. Opposed to *vitamin*, a nice-to-have.
- **Positioning principles** — the six-point framework governing all external-facing copy. Source of truth: memory file `project_ran_positioning_principles.md`. The spec defers to the memory file for exact content and does not enumerate the principles verbatim.
- **Two-tier field rule** — classification protocol separating *story fields* (positioning rules apply without exception) from *tech-disclosure fields* (factual technical disclosure appropriate for form operators). Source of truth: memory file `project_abrigo_two_tier_field_rule.md`.
- **Painkiller evidence base** — the research artifacts that substantiate painkiller claims in copy. Primary: `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/`. Secondary: Tier 1 feasibility methodology spec and `ranPricing.ipynb` Applications section. Source of truth: memory file `project_abrigo_painkiller_evidence_base.md`.
- **Brand agent** — canonical term for the Abrigo-specific subagent that drafts copy. Used consistently throughout the spec in preference to *branding agent*, *Abrigo agent*, or *brand subagent*.
- **Background dispatch** — agent execution pattern where the subagent runs asynchronously, writes outputs to `.branding/`, and notifies when drafts or reviews complete. The specific tool call, parameters, and hook wiring that realize this pattern are implementation concerns deferred to the plan.
- **Review triad** — three specialized reviewer agents dispatched in parallel after each artifact draft. Always-on pair (Brand Guardian, Claim Auditor) plus one artifact-specific third seat.
- **Claim Auditor** — the copy-claim-verification role in the review triad. The role is realized by invoking the existing Reality Checker subagent with a per-invocation prompt augmentation that redirects its charter from code/UI QA to copy-claim defensibility against the painkiller evidence base. The underlying subagent is unchanged; the role is defined by how it is called. The previous "Reality Checker" label for this role is withdrawn; see §7.2.
- **BLOCK / FLAG / PASS** — the verdict set every reviewer returns per finding.
- **Orchestrator** — the coordinating agent that dispatches the brand agent and the review triad, gathers verdict files, routes revisions, and surfaces contradictions to the founder. In v1 the orchestrator is the founder's foreground Claude session. A later spec may promote this to a dedicated meta-agent; that change does not affect the brand-agent or reviewer charters defined here.
- **Founder** — the human operator of the Abrigo project who invokes the orchestrator, edits `facts.yml`, and submits final artifacts to external parties. The only human role the spec names.
- **Graduate** — the lifecycle transition in which a draft that has achieved three PASS verdicts at the same revision number is promoted from its `drafts/` subdirectory to the artifact's canonical final path. Defined operationally in §7.4.
- **Final artifact** — a file at its canonical final path (see §9) that has graduated and is ready for external use. Distinguished from `drafts/` content.
- **Geoffrey-Moore frame** — the positioning-statement template "For [target user] who [pain], Abrigo is [category] that [benefit] unlike [alternative] which [failure]." Used in §9.4 for tagline / positioning output shape. Attributed to Geoffrey Moore, *Crossing the Chasm*.

---

## 1. Context

The project currently produces engineering artifacts (specs, plans, code, notebooks, research) but has no protocol for producing external-facing copy. External-facing copy has different rules than engineering copy: it addresses a non-technical audience, must obey a tight positioning frame, must be grounded in real research, and should not name the underlying DeFi primitives that engineering documents name freely. This gap means that when a hackathon, accelerator, grant, or investor asks the founder to "explain the product," the answer is generated ad-hoc, risks drifting between answers, and absorbs founder attention that should go to engineering.

The immediate trigger is a Crecimiento Foundation startup application form with ~20 structured fields covering story, stage, tech stack, and ecosystem affiliation. The form surfaces the tension the agent must resolve: the same form contains fields where crypto is a liability (story fields aimed at evaluating the product thesis) and fields where crypto is load-bearing (the foundation negotiates vendor credits on behalf of startups based on disclosed tech stack).

---

## 2. Goals

- Provide a single, reusable agent that can draft on-brand Abrigo copy for any application-form question, pitch artifact, or explainer, consistent with the positioning principles.
- Keep all generated copy and its working state outside version control; keep the agent definition itself versioned.
- Ground every painkiller-adjacent claim in the existing macro-risk research folder, so copy is evidence-backed rather than marketing-puff.
- Enforce a per-artifact three-way review loop that separates brand compliance, claim defensibility, and structural craft.
- Run drafts and reviews in the background so the founder's foreground context stays focused on engineering.

## 3. Non-Goals

- Generating engineering specs, plans, or code. The agent only writes external-facing copy; engineering work is unaffected.
- Naming or explaining the underlying protocols (Angstrom, Panoptic, Mento, Ethereum L1, Uniswap V4) in story fields. Tech-disclosure fields may name them when factually required.
- Selling decentralization as a product value proposition.
- Maintaining a trademark / domain registry; that work is a sibling action captured in the Abrigo brand-name memory, not handled by this agent.
- Auto-submitting forms. The agent drafts answers; a human edits and submits.
- Acting as the Crecimiento-specific agent. Crecimiento is the first concrete form target, but the design must generalize to any application form.

---

## 4. Design Principles

### 4.1 Positioning

All story-tier copy produced by the brand agent obeys the positioning principles defined in memory file `project_ran_positioning_principles.md`. The spec does not restate them here; any summary would risk drifting from the memory as it evolves. Implementers, reviewers, and the brand agent itself read the memory file as the single source of truth.

One interaction between principles must be handled explicitly because it appears contradictory at first reading:

- The "10x better than existing alternatives" principle obliges strong improvement claims. The evidence-grounding protocol in §8 requires every such claim to carry a citation and to be softened to directional phrasing when the cited evidence is itself directional. Resolution: the brand agent frames comparisons as strong when the evidence base supports strong phrasing, directional when it does not, and never as absolute when it lacks a citation. The Claim Auditor (§7.2) enforces this at review time.

### 4.2 Two-Tier Field Rule

For any structured form, the agent classifies each field into Tier 1 (story) or Tier 2 (tech-disclosure) before drafting. Tier 1 fields receive positioning-compliant copy. Tier 2 fields receive factual technical disclosure drawn from `facts.yml`. Boundary rule: when a field is ambiguous, classify as Tier 1. Tier 2 disclosure content never flows back into Tier 1 copy.

Authoritative source: memory file `project_abrigo_two_tier_field_rule.md`.

### 4.3 Evidence Grounding

Every painkiller claim, every "10x better than" comparison, every problem-statement assertion, and every sizing or prevalence claim carries a citation to a specific file and line range in the painkiller evidence base. Claims that cannot be grounded are either dropped or softened to explicit "directional, evidence pending" phrasing. Citations are carried in the draft as footnotes or inline comments and stripped before the artifact ships.

Authoritative source: memory file `project_abrigo_painkiller_evidence_base.md`.

### 4.4 Protocol-Name Abstraction

Story copy never names Angstrom, Panoptic, Mento, Uniswap, Ethereum, any specific L1/L2, or any specific on-chain primitive. Abstract terms are substituted: "MEV-free observation layer," "options / replicating-portfolio execution layer," "local stablecoin," "custom continuous payoff." Tech-disclosure copy names them factually and without editorial.

### 4.5 Dual Narrative

The hero-user construction for any longer-form artifact (one-pager, 3-minute pitch, problem field in an application) names two protagonists: a household or remittance-receiver in an underserved-FX market who *buys* protection, and a liquidity provider or structured-product writer who *supplies* that protection and earns the premium. Short-form artifacts (30-second pitch, tagline) may lead with one side and imply the other, but the full narrative always has both.

### 4.6 Pilot-Then-Mission Arc

Copy presents Colombia as the first concrete market, not the product focus. The mission is underserved-FX countries broadly; the pilot is the proof of the approach. Artifacts that collapse this arc ("Abrigo is a Colombian fintech") are off-positioning.

---

## 5. Workspace Layout

Two directories govern agent operation: a committed definition surface and a gitignored working surface.

### 5.1 Committed Surface

- `contracts/.claude/agents/abrigo-brand-agent.md` — the brand agent's subagent definition. Versioned. Readable by any contributor. Embeds the positioning principles, two-tier field rule, evidence-grounding protocol, and brand-name convention by reference to the memory files or directly where appropriate.
- `contracts/.claude/agents/abrigo-brand-reviewer-*.md` — optional per-reviewer-seat definition files if the review triad requires Abrigo-specific customization beyond what the generic reviewers provide. May not all be needed; the default is to reuse the existing Brand Guardian, Reality Checker, Proposal Strategist, Content Creator, Executive Summary Generator, and Cultural Intelligence Strategist agents.

### 5.2 Gitignored Working Surface

- `contracts/.branding/` — root of the gitignored workspace. Added as a single line to `contracts/.gitignore`.
  - `facts.yml` — hand-edited source of truth for concrete facts the agent cites. The file is read by the brand agent and by every reviewer; it is written only by the founder. Schema defined in §5.2.1.
  - `forms/<org-slug>/` — one subdirectory per application target. Example: `forms/crecimiento/`.
    - `questions.md` — raw pasted form questions, hand-edited by the founder.
    - `drafts/` — agent-generated answer drafts, timestamped by revision.
    - `reviews/` — reviewer verdicts by draft revision, keyed by reviewer seat.
    - `answers.md` — the current approved answer set, emerging after all reviewers PASS.
    - `submitted.md` — frozen snapshot after the founder submits, never regenerated.
  - `artifacts/` — derived, regenerable, non-form-specific.
    - `one-pager.md` — standalone product explainer for non-crypto readers.
    - `pitch-30s.md`, `pitch-60s.md`, `pitch-3min.md` — elevator pitches at three lengths.
    - `taglines.md` — tagline and positioning-statement candidates.
    - Each has parallel `drafts/` and `reviews/` subdirectories during production.
  - `README.md` — directory conventions and invocation examples for human readers.

### 5.2.1 facts.yml Schema

The facts file is a flat key-value document with the following named fields. All are single-valued unless described as a list. Every field has a defined handling when missing: either the brand agent refuses to cite it (hard fields) or substitutes an explicit placeholder like "not yet available" that triggers a FLAG at review (soft fields).

**Company facts (hard):** `brand_name`, `legal_entity_status`, `founding_date`, `pilot_market`, `mission_scope`.

**Team facts (hard):** `cofounder_count`, `cofounder_roles` (list), `team_size`, `employee_roles` (list).

**Stage facts (hard):** `company_stage` (one of: idea, prototype, pilot, revenue, scale), `product_stage` (one of: concept, MVP, private-beta, public-beta, live), `current_raising_round` (one of: pre-seed, seed, series-A, not-raising, grant-only).

**Traction facts (soft):** `pilot_traction_statement`, `user_count`, `transaction_volume`, `partnership_list` (list). When soft fields are populated, claims citing them are subject to Claim Auditor verification against source references also stored in `facts.yml` under a parallel `facts_citations` key.

**Tech-disclosure facts (hard, Tier 2 only):** `primary_language_stack` (list), `hosting_provider`, `web3_ecosystems` (list), `ai_tools_used` (list), `verticals` (list), `other_tech_notes`.

**Contact facts (soft):** `website_url`, `x_handle`, `contact_email`, `pitch_deck_url`.

**Positioning overrides (soft):** `brand_name_qualifier` (e.g., "Abrigo Money" when the bare name is blocked), `tagline_pin` (a tagline locked by the founder that the agent must reuse verbatim rather than regenerate).

The schema is enforced by the brand agent on every read: missing hard fields cause the agent to refuse to draft any artifact that depends on them and to surface the missing fields to the founder. Missing soft fields produce explicit "pending" placeholders in the draft, which the Claim Auditor FLAGs.

### 5.3 Gitignore Entry

A single line in `contracts/.gitignore`: `/.branding/`. No other ignore rules are needed; the directory is self-contained.

---

## 6. Agent Surface

### 6.1 Brand Agent Responsibilities

The brand agent is responsible for drafting copy. It is not responsible for reviewing its own output, maintaining `facts.yml`, or submitting forms.

Inputs the agent reads on every invocation:
- The positioning principles memory file.
- The two-tier field rule memory file.
- The Abrigo brand-name memory file.
- The product-framing memory file.
- The painkiller evidence base memory file (pointer to the MACRO_RISKS folder).
- `facts.yml` in the working surface.
- The invocation-specific input: a form-question set, an artifact type request, or a revision task.
- For revision tasks: all reviewer verdict files from the prior round.

Outputs the agent writes:
- A draft file under the appropriate `drafts/` subdirectory, revision-stamped `v{N}.md`.
- A companion `v{N}-facts-snapshot.yml` recording the subset of `facts.yml` the draft cited (§11.8).
- A companion `v{N}-source-manifest.md` with content-hashes of every cited evidence file (§8.4).
- For revisions: a new draft file, a `v{N}-diff-rationale.md` explaining what changed in response to each reviewer finding, and refreshed companion files.

**Quantitative-facts rule.** The brand agent never paraphrases, rounds, infers, or computes quantitative facts (traction numbers, team sizes, stage labels, dates, URLs, handles). It always substitutes the verbatim value from `facts.yml`. Paraphrased quantitative facts are a BLOCK finding at review time. This rule prevents cross-artifact drift when the founder cites the same fact differently in different places (§11.9).

### 6.2 Background Dispatch

The agent runs asynchronously on every invocation. The founder issues a natural-language trigger to the orchestrator ("draft the one-pager," "fill Crecimiento questions"); the orchestrator dispatches the brand agent in the background; the founder is notified when the draft lands. The orchestrator then triggers the review round. The specific tool, parameter, and hook configuration that realize background dispatch are implementation-plan concerns, not spec concerns.

### 6.3 Self-Review Prohibition

The brand agent never reviews its own output. Every review is performed by a separate specialized reviewer agent.

### 6.4 Scope Boundaries

The brand agent is read-only against the codebase, memory files, and evidence base. It is write-only against `contracts/.branding/`. Any attempt to modify files in `src/`, `test/`, `script/`, `docs/superpowers/specs/`, memory, or anywhere else in the worktree is out of scope.

**Enforcement model.** This boundary is not enforced by prompt discipline alone. It is enforced at runtime by a PreToolUse hook that inspects the active subagent identity and the target path of every Write / Edit tool call, denying calls that cross the boundary. See Appendix A (§14) for the required-behavior surface of the hook. A second layer of session-level `settings.json` permissions denies the broadest classes of destructive operations (writes to `src/`, `test/`, `script/`, memory files, external paths) regardless of which agent issued them. Prompt discipline is the third line of defense; the hook is the first, session permissions the second.

---

## 7. Review Workflow

### 7.1 Review Triad by Artifact Type

Every artifact is reviewed by three agents dispatched in parallel. Two seats are always the same; the third rotates by artifact type.

| Artifact type | Seat 1 | Seat 2 | Seat 3 (artifact-specific) |
|---|---|---|---|
| One-pager / product explainer | Brand Guardian | Claim Auditor | Executive Summary Generator |
| Elevator pitch (30s / 60s / 3min) | Brand Guardian | Claim Auditor | Content Creator |
| Application-form answers (Crecimiento and similar) | Brand Guardian | Claim Auditor | Proposal Strategist |
| Tagline / positioning statement | Brand Guardian | Claim Auditor | Cultural Intelligence Strategist |

For novel artifact types not listed here, the default third seat is Executive Summary Generator (structural rigor). The mapping may be extended by future specs.

The Claim Auditor seat is realized by invoking the existing Reality Checker subagent with a per-invocation prompt augmentation that redirects its charter to copy-claim auditing against the painkiller evidence base. The underlying subagent is unchanged; the augmentation lives in the orchestrator's dispatch prompt and is versioned alongside this spec's implementation plan. This is a deliberate role-switching pattern — the existing Reality Checker's core posture ("require evidence, default to NEEDS WORK") transfers cleanly to copy claims, and creating a second similarly-named agent would be worse than disciplined reuse.

### 7.2 Reviewer Charters

Each reviewer seat enforces a distinct, non-overlapping lens.

**Brand Guardian.** Enforces every positioning principle, the two-tier field rule, brand-name consistency, and protocol-name abstraction. Does not evaluate structural craft, claim defensibility, or cultural resonance. Findings focus on "does this copy obey the Abrigo brand contract."

**Claim Auditor.** Verifies every painkiller claim, every "10x better than" comparison, and every sizing / prevalence assertion against the painkiller evidence base. Does not evaluate tone, brand voice, structural craft, or cultural resonance. Findings focus on "is this claim defensible from the cited source." Implemented as the existing Reality Checker subagent with a copy-claim-auditor prompt augmentation per §7.1.

**Executive Summary Generator (third seat for one-pager).** Applies consultant-grade frameworks (SCQA, pyramid principle, Bain/BCG executive-summary craft) to ensure the one-pager has a single clear thesis, a logical cascade, and a decision-readiness surface for a C-suite or foundation reader.

**Content Creator (third seat for elevator pitches).** Evaluates spoken-word voice, pacing, listener retention, transition craft, and the 30-second hook. Ensures the pitch sounds like a human speaking, not a document being read.

**Proposal Strategist (third seat for application-form answers).** Evaluates win-theme alignment, per-question compliance with the form's explicit prompt, and the competitive positioning implicit in each answer. Ensures the application reads as a coherent argument for funding or inclusion, not a collection of disconnected paragraphs.

**Cultural Intelligence Strategist (third seat for tagline / positioning).** Evaluates resonance across the mission geography (underserved-FX countries broadly, Colombia specifically), absence of unintentional stereotype, and dignity of the household protagonist. Ensures the copy lands authentically for the people it names.

### 7.2.1 Charter-Overlap Tiebreakers

Two pairs of adjacent charters have visible overlap at the edges. The spec resolves the overlap with explicit tiebreakers so reviewers do not produce contradictory findings on the same copy element.

**Brand Guardian vs. Cultural Intelligence Strategist.** Both can plausibly surface concerns about how the copy reads to an audience. The boundary: Brand Guardian adjudicates compliance with the fixed positioning contract (principles, name, abstraction, two-tier rule); CIS adjudicates resonance, dignity, and cultural fit given the mission geography. If a finding fits both lenses, Brand Guardian owns it and CIS skips it. CIS only flags issues that Brand Guardian's charter cannot see: stereotype, exclusion, culturally-loaded phrasing, translation adjacency.

**Claim Auditor vs. Proposal Strategist.** Both touch competitive claims. The boundary: Claim Auditor adjudicates whether a specific claim is defensible from a cited source (evidence-check); Proposal Strategist adjudicates whether the overall narrative assembles claims into a persuasive case for funding (composition-check). A sentence that overclaims from a weak source is Claim Auditor's finding. A sentence that is individually defensible but wrecks the flow of the application is Proposal Strategist's finding. When unclear, Claim Auditor reviews first and Proposal Strategist sees the Claim-Auditor verdict before forming its own.

### 7.3 Verdict Vocabulary

Every reviewer returns one of three per-finding verdicts:

- **PASS.** The finding is compliant with the reviewer's charter.
- **FLAG.** The finding is non-blocking but non-ideal; the reviewer proposes a specific softening or sharpening.
- **BLOCK.** The finding violates the reviewer's charter and must be fixed before the artifact can ship.

A reviewer's overall artifact verdict is the most severe per-finding verdict: any BLOCK downgrades the artifact to BLOCK, FLAG without BLOCK downgrades to FLAG, otherwise PASS.

### 7.4 Artifact Lifecycle

File-naming convention: every draft is `drafts/v{N}.md`, every verdict is `reviews/v{N}-{seat}.md`, every diff rationale is `drafts/v{N}-diff-rationale.md`, every founder override is `reviews/v{N}-override.md`. All files in a review cycle share the same `v{N}` revision stamp. The prose "timestamped by revision" phrasing used elsewhere in this spec refers to this `v{N}` stamp, not to wall-clock timestamps.

1. Founder triggers the brand agent with an artifact request.
2. Brand agent reads its standard inputs, drafts the artifact, writes it under `drafts/v1.md`.
3. Review triad dispatched in parallel, each writing its verdict file under `reviews/v1-{seat}.md` where `{seat}` is `brand-guardian`, `claim-auditor`, or the third-seat reviewer name.
4. Graduation requires three PASS verdicts that all reference the same revision `N`. Verdicts from earlier revisions do not count toward graduation of a later revision. The orchestrator checks the revision stamp on each verdict file before declaring a PASS-set complete.
5. If all three seats return PASS for the same revision, the artifact graduates: `drafts/v{N}.md` is promoted to the artifact's final path (`artifacts/one-pager.md`, `forms/<org>/answers.md`, etc.), and the cycle ends.
6. If any seat returns FLAG or BLOCK on revision `N`, the brand agent is re-dispatched with `drafts/v{N}.md` plus all three `v{N}-*` verdict files. It produces `drafts/v{N+1}.md` and `drafts/v{N+1}-diff-rationale.md` explaining how each finding was addressed.
7. Review triad re-dispatched against `v{N+1}`. Repeat.
8. If a reviewer BLOCKs the same finding across two consecutive revisions without the brand agent converging, escalate to the founder for resolution.
9. The founder may override any BLOCK with an explicit written justification stored in `reviews/v{N}-override.md` (for the revision at which the override applies).

### 7.5 Reviewer Contradictions

If two reviewers return contradictory findings on the same draft (e.g., Brand Guardian demands softer language, Claim Auditor demands sharper evidence-backed language), the brand agent does not attempt to resolve the contradiction. It surfaces the contradiction to the founder with both verdict files and a short summary of the conflict.

### 7.6 Background Execution

Reviewer dispatches are parallel and background. The orchestrator waits for all three verdicts at the current revision before triggering a revision cycle. The specific dispatch mechanics are implementation-plan concerns.

---

## 8. Evidence Grounding Protocol

### 8.1 Evidence Base Catalog

- **Primary:** `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` (outside the contracts worktree). Seven files covering the macro-risk proxy taxonomy, historical precedents (USA 1985 and Brazil 1987 CPI futures), income-settlement theory, signal-to-index construction, and price-settlement design.
- **Secondary — Tier 1 feasibility methodology:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` — defines the literature-survey methodology and the operational threshold for confirming per-channel signals. **The methodology spec is the citable artifact; the per-channel verdict deliverable it will produce has not been written yet.** Painkiller claims that depend on a confirmed channel verdict must wait until the deliverable exists. Directional claims drawn from the methodology spec itself are acceptable with "directional, evidence pending" phrasing.
- **Secondary — instrument definition:** `contracts/notebooks/ranPricing.ipynb` — Applications section (CES basket framing, `\mu(\pi)` inflation channel, example pool construction).
- **Tertiary:** `/home/jmsbpp/apps/liq-soldk-dev/refs/macro-risk/` — primary-source papers and data referenced by the MACRO_RISKS notes.

### 8.2 Citation Protocol

Every painkiller-adjacent claim carries a citation of the form `<relative-path>:<line-range>` in the draft. Brand agent attaches citations as footnotes or inline comments, structured so the reviewer can verify them mechanically. Citations are stripped when the draft graduates to a final artifact.

### 8.3 Evidence Failure Modes

- **Claim has no citation.** BLOCK. Drop the claim or ground it.
- **Citation exists but source does not support the claim.** BLOCK. Rewrite to match what the source says.
- **Citation supports a weaker version of the claim.** FLAG. Propose softened wording.
- **Source itself is directional rather than quantitative.** PASS only if the claim is phrased directionally ("inflation erodes savings in underserved-FX markets" PASSes with a directional source; "inflation erodes 12.7% of savings annually" requires a quantitative source).

### 8.4 Evidence Staleness

The painkiller evidence base is live research; it may update after any artifact is produced. If a cited source changes, previously-graduated artifacts may contain claims that no longer match the source.

**Minimum viable staleness protocol (required for v1):**

1. Every graduated artifact carries a `source-manifest.md` alongside it in the same directory. The manifest lists each cited file path and the content-hash of that file at the time the Claim Auditor PASSed the artifact.
2. Before the founder publishes or externally submits a graduated artifact (one-pager, elevator pitch, application-form answers), the orchestrator re-reads each cited file, recomputes its content-hash, and compares to the manifest. Any mismatch means at least one source has changed since the artifact was cleared, and the orchestrator surfaces the affected artifact to the founder with a "re-review recommended" notification.
3. The founder may publish without re-review (owner's call), but the manifest discrepancy is recorded in the artifact's `source-manifest-drift.md` sibling file as provenance.
4. The orchestrator may, on founder trigger, re-dispatch the Claim Auditor on any artifact with drift to produce a refresh-verdict. A FLAG or BLOCK from the refresh-verdict puts the artifact back into the revision cycle.

Content-hash scheme is an implementation concern; any deterministic whole-file hash suffices.

A richer staleness capability (continuous watchers, automatic refresh triggers) is a follow-on capability listed in §12.

---

## 9. Artifact Catalog

Each artifact has a canonical path, a canonical reviewer triad (per §7.1), and a canonical shape.

### 9.1 One-Pager / Product Explainer

Canonical path: `contracts/.branding/artifacts/one-pager.md`.

Shape: problem (painkiller, dual-protagonist), solution (the hedge primitive, abstracted), how it works for each protagonist in mainstream language, pilot (Colombia, one paragraph), mission (underserved-FX, one paragraph), traction (from `facts.yml`), team (from `facts.yml`), contact (from `facts.yml`).

Reviewer triad: Brand Guardian, Claim Auditor, Executive Summary Generator.

### 9.2 Elevator Pitches

Canonical paths: `contracts/.branding/artifacts/pitch-30s.md`, `pitch-60s.md`, `pitch-3min.md`.

Shape at 30s: single-protagonist hook, core painkiller, one-sentence solution, one-sentence pilot. 60s adds the second protagonist and traction. 3min adds the mission arc, competitive-alternative comparison, and an explicit ask.

Reviewer triad: Brand Guardian, Claim Auditor, Content Creator.

### 9.3 Application-Form Answers

Canonical path: `contracts/.branding/forms/<org-slug>/answers.md`.

Shape: per-question answer, each classified Tier 1 or Tier 2 up-front, each answer respecting the field's length limit if specified by the form. For Tier 1 answers, positioning rules bind; for Tier 2 answers, facts from `facts.yml` bind.

Reviewer triad: Brand Guardian, Claim Auditor, Proposal Strategist.

**Initial concrete target:** Crecimiento Foundation application. Fields explicitly enumerated by the founder:
- Startup name (Tier 1 — always "Abrigo" per brand memory)
- One-sentence pitch (Tier 1)
- Expanded description: problem / target audience / value proposition / current challenges / long-term vision (Tier 1)
- Pitch deck reference (Tier 1 — points to generated artifact if available)
- Cofounder count, team size (Tier 2 — from facts.yml)
- Startup stage, raising round, product stage (Tier 2 — from facts.yml)
- Customer type (Tier 1 — this field straddles; classify as Tier 1 and use mainstream language, e.g. "households in underserved-FX markets, plus liquidity providers supplying the hedge")
- Tech stack, hosting provider, web3 ecosystems, AI tools, verticals, other (Tier 2 — factual disclosure from facts.yml, with crypto/web3 fully named here)
- Web page, X account (Tier 2 — from facts.yml)

### 9.4 Tagline / Positioning Statement

Canonical path: `contracts/.branding/artifacts/taglines.md`.

Shape: 3–5 tagline candidates, one positioning statement in the Geoffrey-Moore frame ("For [target user] who [pain], Abrigo is [category] that [benefit] unlike [alternative] which [failure]"), one value-prop sentence, one X bio variant.

Reviewer triad: Brand Guardian, Claim Auditor, Cultural Intelligence Strategist.

---

## 10. Invocation Patterns

The founder invokes the brand agent through natural-language requests to the orchestrator. The orchestrator translates each request into a background dispatch and writes results to `contracts/.branding/` per the workspace conventions.

Canonical request forms (illustrative, not normative):
- *"Draft the one-pager."* → brand agent drafts `artifacts/one-pager/drafts/v1.md`.
- *"Fill the Crecimiento form."* → founder first pastes questions into `forms/crecimiento/questions.md`; agent drafts `forms/crecimiento/drafts/v1.md`.
- *"Revise the one-pager."* → agent reads the latest draft plus all reviewer verdicts and drafts the next revision.
- *"Run the review triad on the current one-pager draft."* → orchestrator dispatches the three reviewers in parallel.
- *"Show me what the reviewers said."* → orchestrator surfaces the latest verdict files.

The dispatch mechanics and prompt wiring of each request form are implementation-plan concerns, not spec concerns.

---

## 11. Open Questions and Risks

### 11.1 Brand-Name Trademark and Domain

"Abrigo" is commercially crowded. A US-based SaaS banking-compliance vendor named Abrigo exists, as does the Brazilian fashion brand "Reserva" (considered and rejected in the name brainstorm). Before any public launch, trademark clearance and domain availability must be verified. This spec proceeds under the assumption that the working name Abrigo is stable enough to draft on; a rename (e.g., to "Abrigo Money" or "Abrigo Protect") would require regenerating artifacts but would not change the spec's design.

### 11.2 Crecimiento as a Priority Target

The Crecimiento Foundation form is the first concrete application target and drove much of the spec's shape. If the Crecimiento submission deadline slips or the foundation's program changes shape, the spec's artifact catalog remains valid; only the `forms/crecimiento/` subdirectory is affected.

### 11.3 Evidence-Base Coupling

The painkiller evidence grounding couples the agent's output to the state of the `liq-soldk-dev/notes/MACRO_RISKS/` folder at draft time. If the folder moves, renames, or is restructured, every cited artifact becomes stale. Mitigation: the Claim Auditor is explicitly responsible for checking citation validity on every review; revisions after a folder move will re-ground automatically as long as the new folder location is updated in the evidence-base memory file.

### 11.4 Reviewer Agent Availability

As of Rev 2, five of the six named reviewer agents (Brand Guardian, Proposal Strategist, Content Creator, Executive Summary Generator, Cultural Intelligence Strategist) are archived at `/home/jmsbpp/.claude/agents/_archived/` and must be un-archived before the implementation plan runs. The un-archival is a Phase 0 step in the implementation plan, not an open risk carried forward. Appendix B (§15) lists the specific files and the post-un-archive verification required to confirm each agent's charter still matches what §7.2 assumes. The sixth seat, Claim Auditor, is realized by the active Reality Checker with prompt augmentation and requires no un-archival.

### 11.5 Reviewer Contradiction Frequency

The design anticipates occasional Brand Guardian / Claim Auditor contradictions — one wants language abstracted, one wants it sharpened by evidence. If contradictions are frequent rather than occasional, the reviewer charters may need refinement to make their non-overlap cleaner. Monitored via post-hoc review of the `reviews/*-override.md` files.

### 11.6 Founder Override Traceability

Founder overrides of BLOCK verdicts are stored in `reviews/<artifact>-override.md` but are not surfaced to downstream reviewers in subsequent artifacts. If overrides start accumulating, a pattern in them may indicate a positioning-principle drift that should be captured as a memory-file update rather than repeated overrides.

### 11.7 Scope of Tier 2 Disclosure

The two-tier field rule says Tier 2 discloses factually, but it does not say whether to name every implementation detail (e.g., specific L2 chain, specific DEX venue) or only the categories. Default for now: disclose at the level of granularity the form field asks for. If Crecimiento asks "which web3 ecosystems," name the ecosystems; if it asks "describe your technical architecture," describe at the layer / category level. Refinement deferred to first submission.

### 11.8 Facts Edits Mid-Review-Cycle

If the founder edits `facts.yml` between a draft and its review (or between a review and its revision), reviewers that read `facts.yml` at verdict time will see different content than the brand agent saw at draft time. This can produce false-positive BLOCKs where the reviewer faults a claim that matched `facts.yml` when it was drafted. Mitigation: the brand agent copies the subset of `facts.yml` it cited into the draft's companion file `drafts/v{N}-facts-snapshot.yml`. Reviewers consult the snapshot, not the live file, when evaluating fact-adjacent claims on that revision. The live `facts.yml` is only re-read by the brand agent when drafting the next revision.

### 11.9 Cross-Artifact Disclosure Contradictions

If the one-pager claims one traction number and the Crecimiento form claims another, the founder is exposed to inconsistency. Mitigation: Tier 2 fact citations always resolve against the current `facts.yml`; the brand agent is forbidden from paraphrasing traction numbers, team sizes, stage labels, or similar quantitative facts and must instead substitute the verbatim `facts.yml` value. Drift between artifacts is therefore a drift in `facts.yml` over time, not a drift between artifacts at a given time.

### 11.10 Brand-Name Rename Protocol

If trademark clearance forces a rename from "Abrigo" to a qualifier (e.g., "Abrigo Money"), every graduated artifact must be regenerated. Mitigation: the brand name is read from the `brand_name_qualifier` facts field (falling back to `brand_name`) on every draft. Rename is a one-line facts update followed by orchestrator-triggered regeneration of every artifact in `.branding/artifacts/` and every `forms/*/answers.md`. The spec treats this as routine operation, not emergency recovery.

### 11.11 External-Path Reads Only

The painkiller evidence base at `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` lives outside the contracts worktree. The brand agent and reviewers read it; they never write to it. The runtime permissions configuration (§14) must include a write-deny for that external path to prevent accidental writes even if prompt discipline slips. If the founder restructures the external path, they update the permissions configuration and the evidence-base memory file in parallel.

### 11.12 External Application Target Freshness

The Crecimiento Foundation form is the first concrete application target. Before the brand agent drafts form answers, the founder verifies that the form is still live and accepting submissions (intake-open check). A form closed between brainstorming and drafting wastes cycles. Mitigation: Phase 7 of the implementation plan includes an explicit intake-open pre-check as Task 7.0. This principle extends to every future application target.

### 11.13 Evidence Base Fitness

The primary painkiller evidence base (`MACRO_RISKS/`) is a research-in-progress folder. Portions are in arrow-notation pseudocode or sketch form rather than prose that cleanly grounds a specific directional claim at a specific line range. The Claim Auditor's PASS verdicts against sketch-form passages are weaker than PASS verdicts against finished prose. Mitigation options, in precedence: (a) cite only the finished-prose passages, (b) soften claims to directional phrasing even when the folder has quantitative hints, (c) upgrade the folder itself — author finishing passes on the sections the brand agent cites most often. Option (c) is out of scope for v1 but should be scheduled as follow-on research work. In the interim, the Claim Auditor's verdict vocabulary is expanded to include "PASS-weak" for sketch-grounded directional claims; these are acceptable for v1 but tagged for later upgrade.

---

## 12. Next Steps

Following approval of this spec:

1. **Three-way spec review.** Per the standing project convention, dispatch Code Reviewer + Reality Checker + Technical Writer to review this spec revision. Reviewer reports land in `contracts/.scratch/`. (Rev 1 was reviewed on 2026-04-15; reports are on disk; Rev 2 incorporates their findings and may require a second pass.)
2. **Phase 0 of the implementation plan — un-archive reviewer agents** (Appendix B). Move the five reviewer-agent files out of `/home/jmsbpp/.claude/agents/_archived/` and verify each charter matches §7.2.
3. **Phase 0 of the implementation plan — write permissions configuration** (Appendix A). Configure runtime write-deny for brand agent and reviewer agents per the required-behavior surface.
4. **Implementation plan.** Invoke the writing-plans skill to produce a detailed implementation plan covering brand-agent authorship, reviewer-prompt augmentations (Claim Auditor especially), orchestrator dispatch logic, `facts.yml` bootstrapping, `.gitignore` update, staleness-manifest mechanics, and the first Crecimiento submission cycle.
5. **Populate `facts.yml`.** Founder pre-fills the hard-tier fields before any artifact is drafted.
6. **Author the agent and reviewer prompts.** Per the implementation plan; not part of this spec.
7. **First end-to-end dry run.** Draft the one-pager, run the review triad, iterate to full PASS, confirm the lifecycle (revision stamping, graduation, staleness manifest) works before attempting the Crecimiento form.
8. **Crecimiento submission.** With the lifecycle validated, fill the form and submit.
9. **Follow-on capabilities (out of scope for v1):** continuous evidence-staleness watchers, tagline A/B generator, multi-lingual (Spanish) copy variant, slide-deck outline artifact, landing-page copy artifact, dedicated meta-agent orchestrator promotion.

---

## 13. Sources of Truth

This spec defers to external sources of truth rather than duplicating their content. Where §4.1 summarizes principles, the summary is non-authoritative and defers to the memory file on every point of conflict. If any source updates, the spec's behavior updates with it.

- **Positioning principles:** memory file `project_ran_positioning_principles.md`
- **Product framing:** memory file `project_ran_product_framing.md`
- **Brand name:** memory file `project_ran_brand_name.md`
- **Two-tier field rule:** memory file `project_abrigo_two_tier_field_rule.md`
- **Painkiller evidence base:** memory file `project_abrigo_painkiller_evidence_base.md`
- **Three-way review convention:** memory file `feedback_three_way_review.md`
- **No-code-in-specs convention:** memory file `feedback_no_code_in_specs_or_plans.md`
- **Research output folder convention:** memory file `feedback_research_output_folder.md`
- **Tier 1 feasibility methodology:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` (methodology spec; the per-channel verdict deliverable is future work and does not yet exist)
- **RAN instrument definition:** `contracts/notebooks/ranPricing.ipynb`
- **Macro-risk research folder:** `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/`

---

## 14. Appendix A — Permissions Model

The scope boundary in §6.4 is enforced at runtime by a PreToolUse hook (primary gate) and session-level `settings.json` permissions (second layer). This spec describes the required behavior of both layers; the hook script, exact `settings.json` keys, and testing approach belong to the implementation plan.

### 14.1 PreToolUse Hook (Primary Gate)

The hook inspects every Write and Edit tool call before execution, determines the active subagent identity from the dispatch context, and denies the call when the target path falls outside that subagent's allowed subtree. The hook is a documented Claude Code feature; per-subagent write allow/deny patterns in `settings.json` alone are not.

**Required behavior for the brand agent (`abrigo-brand-agent`):**
- Write access: allowed only under `contracts/.branding/`.
- Write access: denied for every path outside that subtree.
- Write access: denied for `/home/jmsbpp/apps/liq-soldk-dev/` and any external path the agent reads.
- Read access: unrestricted below the worktree root; allowed on the external painkiller evidence base.

**Required behavior for reviewer agents (`brand-guardian`, `executive-summary-generator`, `content-creator`, `proposal-strategist`, `cultural-intelligence-strategist`, and the Reality Checker when dispatched as Claim Auditor):**
- Write access: allowed under `contracts/.scratch/` and `contracts/.branding/**/reviews/`.
- Write access: denied for every other path, including `contracts/.branding/**/drafts/` (reviewers do not modify drafts).
- Read access: the artifact under review, the facts snapshot for the revision, relevant memory files, and the painkiller evidence base.

**Required behavior for the orchestrator:**
- In v1 the orchestrator runs in the founder's foreground session and inherits that session's permissions. No hook intercept.
- When the orchestrator is promoted to a dedicated meta-agent in a future spec, its permissions model is defined at that time.

### 14.2 Session-Level Settings (Second Layer)

Independent of which subagent is active, the session-level `settings.json` permissions block denies the broadest-blast-radius operations:
- Writes to `src/**`, `test/**`, `script/**`, `lib/**`, `docs/superpowers/specs/**`, `docs/superpowers/plans/**` (except through explicit founder action outside the branding workflow).
- Writes to `/home/jmsbpp/apps/liq-soldk-dev/**` (external evidence base is read-only).
- Writes to `/home/jmsbpp/.claude/**` (user-level agent definitions and memory).

These denials apply even if the PreToolUse hook has a bug. They trade some developer-workflow friction (the founder occasionally needs to temporarily relax them to commit Solidity changes) for a hard backstop against the branding workflow contaminating engineering code.

### 14.3 What Each Layer Catches

- **Hook alone:** per-subagent boundary violations the session permissions would allow (e.g., brand agent trying to write to `contracts/test/`, which session permissions block anyway; or brand agent trying to write to `contracts/lib/`, which session permissions also block; or brand agent trying to write to `contracts/docs/`, which session permissions might not block).
- **Session permissions alone:** catastrophic writes from any agent or from the foreground session itself to high-blast-radius paths.
- **Both together:** the branding workflow is contained end-to-end.

### 14.4 Out of Scope for This Spec

The hook script's language, event wiring, `settings.json` schema keys, denial-pattern syntax, and test harness. All implementation-plan content. The required-behavior surface above is the spec's contract.

---

## 15. Appendix B — Reviewer Agents to Un-Archive

The five reviewer agents the triad depends on currently live under `/home/jmsbpp/.claude/agents/_archived/<category>/<category>-<name>.md`. Phase 0 of the implementation plan un-archives them by moving each file to a clean active location with the category prefix dropped.

| Source path (archived) | Destination path (active) |
|---|---|
| `_archived/design/design-brand-guardian.md` | `/home/jmsbpp/.claude/agents/brand-guardian.md` |
| `_archived/support/support-executive-summary-generator.md` | `/home/jmsbpp/.claude/agents/executive-summary-generator.md` |
| `_archived/marketing/marketing-content-creator.md` | `/home/jmsbpp/.claude/agents/content-creator.md` |
| `_archived/sales/sales-proposal-strategist.md` | `/home/jmsbpp/.claude/agents/proposal-strategist.md` |
| `_archived/specialized/specialized-cultural-intelligence-strategist.md` | `/home/jmsbpp/.claude/agents/cultural-intelligence-strategist.md` |

The rename drops the category prefix so dispatch names in the orchestrator's Phase 3 invocation templates are clean. If any of these agents references its own category-prefixed name internally (in frontmatter `name:` fields, cross-links, or prompt text), the rename requires updating those internal references too; the implementation plan handles this per file.

**Post-un-archive verification (per reviewer):**
- Confirm the agent's frontmatter `name:` field matches its new clean filename.
- Confirm the agent's charter as declared in its frontmatter description and prompt body matches the corresponding §7.2 charter summary.
- If charter has drifted from §7.2: default to option (c) below. The archived agents are generic; Abrigo's positioning rules are specific enough that generic charters will miss Abrigo-specific concerns (protocol-name abstraction, painkiller-evidence grounding, two-tier field rule). Options in precedence order:
  - (c) **Preferred default.** Author an Abrigo-specific variant under `contracts/.claude/agents/abrigo-<seat>.md` layered on top of the un-archived generic; the generic stays available for other projects.
  - (a) Amend the generic agent's prompt to cover Abrigo's specificity; acceptable only if the amendment does not narrow the agent's usefulness to other projects.
  - (b) Amend this spec's §7.2 to match the generic's existing charter; acceptable only if §7.2's Abrigo-specific requirements can be dropped without weakening the review.
- Confirm the agent's hook-permission behavior (post-un-archive, per Appendix A §14.1) matches the reviewer permissions model. If it does not, update the PreToolUse hook to recognize the new name.

The Claim Auditor seat requires no un-archival: it is realized by invoking the active Reality Checker at `/home/jmsbpp/.claude/agents/testing/testing-reality-checker.md` with a per-invocation prompt augmentation documented in the implementation plan.
