# Abrigo Branding Agent Design Spec — Code Reviewer Report

**Reviewer:** Code Reviewer (adversarial, architectural-rigor lens)
**Spec under review:** `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` (Rev 1, 2026-04-15)
**Date:** 2026-04-15

---

## Executive Verdict: **FLAG**

The spec is well-organized, internally coherent, and mostly discharges its stated goal: produce a code-agnostic design contract for a background-dispatched branding subagent plus its gitignored workspace. Glossary, non-goals, and source-of-truth pointers are handled with more discipline than most specs in this repo.

It does not rise to PASS because several interfaces are specified at the level of prose intent rather than contract. A downstream implementer can build *a* system from this spec, but not *the same* system two different implementers would build, which is the bar for engineering-grade design. The specific gaps that drive FLAG rather than PASS:

1. `facts.yml` has no schema. §5.2 enumerates fields as a sentence; §9.3 and §11.7 each reference the file as if its structure is settled. It is not.
2. Several filesystem contracts are under-specified (draft revision naming, review verdict file naming, `diff-rationale.md` location, how `questions.md` pastes get parsed).
3. Failure modes are named but not all have resolution semantics (§7.5 reviewer contradictions; §8.4 evidence staleness; §11.4 reviewer unavailability).
4. Reviewer charters in §7.2 contain two pairs with genuine overlap that the spec asserts away rather than resolves: Brand Guardian vs. Cultural Intelligence Strategist, and Reality Checker vs. Proposal Strategist.
5. External-path coupling (§8.1, §11.3) is acknowledged but the mitigation is incomplete.

None of these is a BLOCK on its own. Collectively they are enough that the implementation plan downstream of this spec will have to make meaningful interface decisions, and those decisions should be made here.

---

## Section-by-Section Findings

### §0 Glossary — **PASS**

Twelve terms, each a single sentence. Covers the non-obvious vocabulary (Abrigo, painkiller, two-tier, dual narrative, background dispatch, review triad, verdict set). The glossary correctly names memory files as authoritative rather than duplicating their content. No issues.

### §1 Context — **PASS**

One paragraph, purpose-built, names the immediate trigger (Crecimiento). Does not ramble. The sentence "The form surfaces the tension the agent must resolve" is the single cleanest framing of why the two-tier rule exists; retain it.

### §2 Goals / §3 Non-Goals — **PASS**

Five goals, seven non-goals. The non-goals are sharper than the goals (generating engineering specs, naming underlying protocols in story fields, selling decentralization, auto-submitting, trademark registry, not-Crecimiento-specific). This is the correct shape: a branding-agent spec is defined more by what it refuses than by what it does. No issues.

### §4 Design Principles — **PASS with one nit**

§4.1–§4.6 read cleanly. Each subsection names an authoritative memory file for principles that belong to the project, not to this spec. Good dependency hygiene at the prose level.

Nit (💭): §4.2 says "Tier 2 disclosure content never flows back into Tier 1 copy." This is a one-way data-flow rule that is important enough to be stated as a testable invariant in §6 or §7, not buried in §4.2. Consider lifting it into the Brand Guardian charter (§7.2) as an explicit check.

### §5 Workspace Layout — **FLAG**

§5.1 is fine. §5.2 is where the spec's interface rigor starts to fray.

**🟡 `facts.yml` schema is implicit and non-trivial.** §5.2 enumerates fields prose-style: "team size, cofounder count, company stage, product stage, pilot status, current traction figures, Crecimiento-style tech-stack disclosures (hosting provider, web3 ecosystems, AI tools, verticals), X account, web page URL." §9.3 re-enumerates a near-but-not-identical list for Crecimiento. §11.7 flags granularity ambiguity but defers it. Three observations:

- The schema is referenced by at least three consumers (the brand agent, the reviewers who check citations against it, the founder who hand-edits it) but specified once, imprecisely.
- "Traction figures" is not a scalar; it is a sub-schema. Same for "tech stack" (depth? format?).
- The field list in §5.2 and the field list in §9.3 are not the same list. Which is canonical?

The no-code rule does not prohibit specifying a schema in prose. A numbered subsection titled "5.2.1 `facts.yml` fields" that lists each key, its type in English ("string," "integer," "list of strings," "sub-record with the following keys …"), and whether it is required vs. optional, would close this gap without introducing YAML syntax.

**🟡 Draft and review file naming is under-specified.** §5.2 references `drafts/` (timestamped), `reviews/` (keyed by reviewer seat), `answers.md`, `submitted.md`. §7.4 later uses `drafts/v1.md`, `drafts/v2.md`, `reviews/v1-<seat>.md`, `drafts/v2-diff-rationale.md`, `reviews/<artifact>-override.md`. These are not consistent: §5.2 says "timestamped by revision," §7.4 says "v1." Pick one and use it everywhere. If the scheme is `vN` without timestamps, state that explicitly; if both, specify the pattern.

**🟡 `questions.md` parsing contract is absent.** §5.2 says `questions.md` is "raw pasted form questions, hand-edited by the founder." The brand agent must parse this into a per-field prompt list (since §9.3 answers are per-question). What is the minimum parseable shape? Markdown headings? Numbered list? Labeled blocks? If the founder pastes whatever the form gives them, the agent needs a contract. Default resolution: specify one lightweight convention (e.g., "each question is introduced by a level-3 heading whose text is the field label; any length limit is stated inline on the next line") and document it in §5.2 or a new §5.2.2.

**🟡 Gitignore entry inconsistency.** §5.3 says "A single line in `contracts/.gitignore`: `/.branding/`." The leading slash anchors at the root of whatever directory contains the `.gitignore`. `contracts/.gitignore` lives in `contracts/`, so the correct entry for `contracts/.branding/` is either `.branding/` or `/.branding/`. The spec's form is correct under standard gitignore semantics, but worth a one-line sanity note because a future contributor editing from the repo root may mis-apply it.

### §6 Agent Surface — **FLAG**

§6.1 is thorough on inputs but thin on outputs. "A draft file under the appropriate `drafts/` subdirectory, timestamped" — see §5.2 finding above. "For revisions: a new draft file and a `diff-rationale.md` explaining what changed" — the spec does not say where `diff-rationale.md` lives. §7.4 calls it `drafts/v2-diff-rationale.md`. Unify.

§6.2 "Background Dispatch" is vague about the trigger interface. The sentence "The founder issues one human-language trigger" describes a capability, not a contract. If this spec is the contract, the contract should state: the brand agent is dispatchable by (a) the founder's foreground Claude session via `Agent` tool invocation with `run_in_background: true`, (b) a future meta-orchestrator with the same invocation signature. §10 later lists invocation patterns, but §10 is about what the founder types; §6.2 is about what the system accepts. They are different contracts.

§6.3 Self-Review Prohibition is one sentence and correct. No issues.

§6.4 Scope Boundaries is mostly good but has a gap: "Any attempt to modify files in `src/`, `test/`, `script/`, `docs/superpowers/specs/`, memory, or anywhere else in the worktree is out of scope and must be refused." "Must be refused" — by whom, and how? If the agent itself is the enforcer, the spec should say so and name the mechanism (Claude Code's tool permission system, an explicit guardrail in the agent prompt, or both). If the expectation is that the agent simply won't attempt writes outside `.branding/` because the prompt tells it not to, say that — but that is a behavioral expectation, not a hard boundary, and should be named as such.

### §7 Review Workflow — **FLAG**

This is the most consequential section and the one that most needs tightening.

**🔴 Charter overlap: Brand Guardian vs. Cultural Intelligence Strategist.**
§7.2 Brand Guardian "enforces every positioning principle" including principle #6 ("crypto-native and mainstream are distinct markets with distinct rules … copy that reads naturally only to crypto-natives is off-positioning"). Cultural Intelligence Strategist "evaluates resonance across the mission geography … absence of unintentional stereotype, and dignity of the household protagonist."

These overlap on the question of audience fit. A tagline that reads as Silicon Valley boilerplate fails both charters: Brand Guardian because it reads crypto-native / startup-jargon, Cultural Intelligence Strategist because it lacks resonance for a Colombian household. Who blocks? The spec claims "distinct, non-overlapping lens" but does not resolve this.

Recommended fix: narrow Brand Guardian to "brand contract compliance against named rules" (positioning-principle list, two-tier classification, protocol-abstraction, name consistency) and narrow Cultural Intelligence Strategist to "audience-resonance / dignity judgments not reducible to a named rule." In practice this means Brand Guardian checks off a rubric and Cultural Intelligence Strategist applies judgment. State this explicitly.

**🔴 Charter overlap: Reality Checker vs. Proposal Strategist.**
Reality Checker "verifies every painkiller claim … against the painkiller evidence base." Proposal Strategist "evaluates win-theme alignment, per-question compliance with the form's explicit prompt, and the competitive positioning implicit in each answer."

Overlap lives in "competitive positioning implicit in each answer." A 10x-better claim is both a painkiller claim (Reality Checker territory) and a competitive-positioning claim (Proposal Strategist territory). The spec does not say which seat adjudicates.

Recommended fix: Reality Checker owns whether the claim is *supportable from the evidence base*. Proposal Strategist owns whether the claim is *positioned to win this specific form*. Two different questions; state them as such.

**🟡 §7.3 verdict aggregation rule is under-specified.** "A reviewer's overall artifact verdict is the most severe per-finding verdict." Fine. But what is *the artifact's* verdict across three reviewers? The spec implies in §7.4 that all three must PASS to graduate, but never states it. State: "An artifact graduates to its canonical path only if all three reviewers return overall PASS."

**🟡 §7.4 step 7 "escalate to the founder" has no protocol.** "If a reviewer BLOCKs the same finding across two consecutive revisions without the brand agent converging, escalate to the founder." How? Write a file? Emit a notification? The background-dispatch model means the founder is not watching the `.branding/` tree continuously. Specify the escalation surface (e.g., "an `escalations.md` file at the artifact root, touched on every unresolved-BLOCK condition, whose existence is surfaced by the orchestrator on the next foreground interaction").

**🟡 §7.5 reviewer contradictions has no stall semantics.** The rule is "brand agent does not attempt to resolve; surfaces to founder." Good. But between surfacing and founder resolution, what is the artifact state? Is v2 blocked until the founder adjudicates? Does the brand agent produce v2 anyway, choosing one reviewer's guidance arbitrarily? Specify: "When a reviewer contradiction is surfaced, the lifecycle pauses at v(N); the brand agent does not produce v(N+1) until the founder writes a resolution note at a specified path."

**🟡 §7.6 background execution and parallelism.** "The orchestrator … waits for all three verdicts before triggering a revision cycle." Fine at the happy path. Not specified: what if one reviewer never returns (agent crashes, tool timeout, background dispatch loses the handle)? A timeout or liveness rule belongs here. Default resolution: "If a reviewer has not returned a verdict within N foreground turns, the orchestrator marks that seat TIMEOUT and surfaces to the founder. No artifact graduates with a TIMEOUT seat."

### §8 Evidence Grounding Protocol — **FLAG**

§8.1 catalog is clear and cites real paths. §8.2 citation protocol is operationally specific (`<relative-path>:<line-range>`, footnotes/inline comments, stripped on graduation). Good.

**🟡 §8.3 evidence failure mode table is the best part of the spec. Extend the pattern.** The four cases (no citation, wrong source, weaker-source, directional-only) are exactly the level of concrete resolution semantics the rest of the spec needs. Use this subsection as the template for §7.5 (contradiction resolution) and §11.4 (reviewer unavailability).

**🔴 §8.4 evidence staleness is deferred without a minimum viable protocol.** The spec says "When the founder updates the MACRO_RISKS folder, the Abrigo workspace should be flagged for re-review. This flagging is out of scope for the initial agent build." That is acceptable as a follow-on *feature*. It is not acceptable as a reliability contract, because the gap means the system can ship stale-cited artifacts the reviewers will not catch on any new artifact they are not re-reviewing.

Minimum viable protocol (does not require new tooling): "Every artifact's `drafts/vN.md` records at the top the git-sha or mtime of each file in the evidence base it cites. On re-review, Reality Checker flags any artifact whose recorded shas/mtimes differ from the current state of the evidence base."

Or, simpler: "Every graduated artifact records the date and evidence-base file list at its top; the founder is responsible for re-running the review triad after any MACRO_RISKS update." Either works. The current spec has *neither*, and §11.3 mitigation ("revisions will re-ground automatically") only fires when a revision is triggered — which is exactly what staleness doesn't trigger.

**🟡 §8.1 path stability.** `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` is an absolute path outside the worktree, outside the repo, on a single developer's filesystem. §11.3 flags this as a risk and relies on the memory file for the source of truth. That is the right move, but the spec should name the mitigation more crisply: "The evidence-base memory file is the sole citation of the evidence-base path. If the folder moves, the memory file updates; the agent reads from the memory file. The spec itself cites the path in §8.1 as a current-state reference, not as a contract." Say that.

### §9 Artifact Catalog — **PASS with nits**

§9.1–§9.4 each specify canonical path, shape, reviewer triad. Shape descriptions are prose-level and deliberately non-prescriptive, which is correct for a code-agnostic spec.

Nit 💭: §9.3 re-enumerates the Crecimiento field list with implicit tier classifications. Two of the classifications are worth an explicit paragraph:

- "Startup name (Tier 1 — always 'Abrigo')." Calling this Tier 1 is correct but the application is degenerate (the field has only one valid value per the brand memory). Consider a note that trivially-constant Tier 1 fields bypass the draft-review lifecycle.
- "Customer type (Tier 1 — this field straddles)." The spec decides correctly and shows its reasoning. Good.

Nit 💭: §9.4 positioning-statement frame: "For [target user] who [pain], Abrigo is [category] that [benefit] unlike [alternative] which [failure]" — the Geoffrey Moore frame is a fine default. It is also a specific template that belongs in the artifact-shape prose, not in the spec's design-principles layer. It reads fine here; just flag that this templating choice should be a reviewable decision in the implementation-plan step, not a sunk commitment.

### §10 Invocation Patterns — **PASS with one borderline**

The five quoted request forms are illustrative, not prescriptive ("The exact prompt wiring of each request form is an implementation-plan concern, not a spec concern"). This is the right stance.

Borderline 💭: §10 is the closest the spec comes to violating the no-code-in-specs rule. The quoted request strings ("Draft the one-pager.", "Fill the Crecimiento form.") are not code, but they are very close to a UX contract. As long as §10 reads as "these are the shapes the founder will use, not the literal strings the orchestrator must match," it is fine. The current disclaimer at the end of §10 carries that weight. Leave as-is.

### §11 Open Questions and Risks — **PASS**

Seven items, each named with a mitigation or deferral. §11.3 (evidence-base coupling) and §11.4 (reviewer availability) are the two most load-bearing; both are flagged honestly.

§11.4 is borderline: "If any are unavailable or have materially different charters … the reviewer mapping must be revisited during implementation." What if they are unavailable *at runtime*, not at spec time? This is the reviewer-unavailability failure mode the request letter asks about. The spec treats it as a spec-time risk only. Name the runtime case: "If a reviewer seat is unavailable at dispatch time, the orchestrator marks that seat as UNAVAILABLE and surfaces to the founder; no artifact graduates with an UNAVAILABLE seat."

### §12 Next Steps — **PASS**

Seven steps, correctly ordered (three-way review → plan → facts.yml → authoring → dry run → Crecimiento → follow-on). No issues.

### §13 Sources of Truth — **PASS**

Ten entries, each a real file. Good dependency hygiene.

---

## No-Code-in-Specs Compliance Check

The spec contains:
- Zero code blocks (```...```)
- Zero function signatures
- Zero Solidity
- Zero YAML or JSON examples
- One quoted filesystem path per line where filesystem paths are the contract (unavoidable)
- One quoted gitignore entry (§5.3) — this is a configuration string, not code; acceptable
- Five quoted natural-language request forms in §10 — documented as illustrative, not prescriptive

**Verdict: compliant.** The spec does not pre-commit to implementation choices. The one area where it could drift (an implicit `facts.yml` schema) is called out above as a §5 finding, with a suggested prose-level resolution that stays code-agnostic.

---

## Explicit Questions the Spec Fails to Answer

1. What is the canonical schema of `facts.yml` — every key, its type (in English), whether required, and what the nesting looks like for non-scalar entries (traction figures, tech stack)?
2. What is the draft revision naming scheme — `vN.md`, timestamped, or both? Does `diff-rationale.md` live under `drafts/` or at the artifact root?
3. What is the minimum parseable shape of `questions.md`? What does a founder paste look like, and how does the agent deterministically split it into per-field prompts?
4. Exactly what distinguishes Brand Guardian's audit from Cultural Intelligence Strategist's, and Reality Checker's from Proposal Strategist's, when both reviewers could plausibly BLOCK the same line of copy?
5. An artifact's overall verdict requires all three seats PASS — is that correct? State it.
6. When a reviewer BLOCKs the same finding twice, the founder is escalated. By what surface? (File, notification, foreground-turn flag?)
7. When two reviewers contradict, v(N+1) is blocked until founder resolution — is that the intended lifecycle state? If not, what is?
8. If a reviewer never returns (timeout, crash, unavailability), how long does the orchestrator wait, and what's the verdict state of the seat?
9. How does the system detect evidence-base staleness? If it cannot detect, how does the founder know to re-review?
10. When the agent is told to modify something outside `.branding/`, is the refusal enforced by prompt, by tool permission, or both?
11. Does a trivially-constant Tier 1 field ("startup name" = "Abrigo") still go through the draft-review lifecycle, or does it bypass?
12. If the brand name `Abrigo` is forced to change (trademark conflict → "Abrigo Money"), which files regenerate and in what order? The spec asserts this "would not change the spec's design" (§11.1) but does not name the regeneration protocol.

---

## Concrete Revision Recommendations (priority order)

### P0 — Must address before spec approval

1. **Add §5.2.1 `facts.yml` schema (prose form).** List every key, English type, required/optional, and any sub-record structure. Reconcile against the Crecimiento field list in §9.3 so both sections agree.

2. **Resolve the two reviewer-charter overlaps in §7.2.**
   - Brand Guardian: "rubric-based compliance against the positioning principles, two-tier rule, protocol-abstraction, and brand-name convention." Reducible to a checklist.
   - Cultural Intelligence Strategist: "judgment-based resonance, dignity, and stereotype absence, particularly for the household protagonist in the mission geography." Not reducible to a checklist.
   - Reality Checker: "supportability of every painkiller and quantitative claim from the evidence base."
   - Proposal Strategist: "form-specific win-theme alignment, prompt compliance, and competitive positioning relative to the target program's criteria."
   State these as the canonical, non-overlapping charters.

3. **Specify draft / review / diff-rationale / override filename conventions once, in §5.2,** and reference that convention from §7.4. Remove the contradiction between "timestamped" and "vN."

4. **Add minimum viable evidence-staleness protocol (§8.4).** Either record evidence-base shas per artifact, or record the review date and enumerate the cited files. Either is a two-sentence addition.

### P1 — Should address before implementation starts

5. **Add resolution semantics to §7.5, §7.6, §11.4.** Reviewer contradiction → lifecycle pauses at v(N), resolution lands at a named path, v(N+1) proceeds from resolution. Reviewer timeout → N-turn limit (or wall-clock), seat marked TIMEOUT, founder surfaced, no graduation. Reviewer unavailability at runtime → same treatment as timeout.

6. **Specify the `questions.md` parsing contract in §5.2** — one paragraph naming the minimum structure the agent can assume and what the founder is expected to paste.

7. **Specify the escalation surface in §7.4 step 7** — file path or mechanism the orchestrator uses to notify the founder of unresolved BLOCKs.

8. **Clarify §6.4 enforcement mechanism** — prompt-level, permission-level, or both — for "must be refused" writes outside `.branding/`.

### P2 — Nice to have

9. **Lift the one-way data-flow rule (Tier 2 never flows to Tier 1)** from §4.2 into the Brand Guardian charter in §7.2 as an explicit check.

10. **Name the brand-rename regeneration protocol** in §11.1 — one sentence stating which artifacts regenerate and confirming the workflow triggers it automatically.

11. **Note in §8.1** that the evidence-base path shown is a current-state reference, not a contract; the memory file is the source of truth for the path.

12. **Note in §9.3** that trivially-constant Tier 1 fields (startup name) may bypass the draft-review lifecycle.

---

## Summary

This is a serviceable Rev 1. It is better than most first-draft specs in this repo at dependency hygiene (defers to memory files rather than duplicating) and at non-goal discipline. It is worse than it should be at interface-contract rigor: the `facts.yml` schema, the filename conventions, the reviewer charter non-overlap claims, and the failure-mode resolution semantics all need to tighten before a future implementer can build this without making unilateral interface decisions.

The twelve questions above are the minimum answer set. The four P0 revisions are the minimum edits that would move the verdict from FLAG to PASS.

The spec is not doing anything wrong. It is doing a couple of important things incompletely.

---

*Report path: `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-15-abrigo-spec-review-code-reviewer.md`*
