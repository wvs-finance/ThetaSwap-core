# Technical Writer Review — Abrigo Branding Agent Design Spec

**Reviewer lens:** Documentation craft and clarity.
**Target reader:** A future contributor (human or AI) with no prior context who lands on the spec and must implement, extend, or critique it correctly.
**Spec under review:** `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` (Draft Rev 1, 2026-04-15).
**Review file:** `contracts/.scratch/2026-04-15-abrigo-spec-review-technical-writer.md`.

---

## Overall verdict: FLAG

The spec is unusually well-written for a draft rev 1 — it is structurally sound, obeys the code-agnostic rule, and defers cleanly to memory as sources of truth. A stranger reading §0–§9 would understand the product, the agent's job, and the review loop with no hand-holding. The flags below are not structural — they are **consistency, citation accuracy, and glossary discipline** issues that would cause a careful implementer to stop and ask. None are BLOCK-class: an author edit pass of roughly 60–90 minutes resolves the list.

The single most important class of finding: the spec's own glossary (§0) and its prose use **inconsistent names for the same memory files and agents** (§13 says `project_ran_brand_name.md`; §6.1 says "the Abrigo brand-name memory file"; §4.1 says "memory file `project_ran_positioning_principles.md`" but §6.1 just says "the positioning principles memory file"). This is the class of drift the spec is engineered against at the artifact level; it should also be avoided at the spec-prose level.

Ship-readiness one-liner: **Clear enough for a stranger to implement the workspace + lifecycle without the author in the room. Not yet clear enough to stand as the single reference for writing the agent prompt, because terminology drift and two miscited sections would force the implementer to guess.**

---

## Findings by lens

### 1. Glossary completeness

**Load-bearing terms used later but not defined in §0:**

- **"orchestrator"** — appears in §6.2, §7.6, §10 ("a foreground Claude session, or a future meta-agent"). It is a distinct role from the brand agent and the review triad, and the reader must know whether it is human, a specific Claude session, a specific sub-agent, or a to-be-built meta-agent. §10 says it "translates requests into `Agent` dispatches"; §7.6 says it waits for verdicts. Define in §0.
- **"founder"** — appears 19+ times and has specific rights in the workflow (triggers drafts, edits `facts.yml`, overrides BLOCKs, submits forms). §6.1 implies "the founder" is the sole human in the loop. Since this spec may later be used by a team, the term should be defined — is "founder" a role or a specific person? Propose defining as "the human principal operating the Abrigo workspace; the only human in §7.4's lifecycle."
- **"artifact"** vs. **"draft"** vs. **"final artifact"** — §7.4 step 4 says "promoted to the artifact's final path" while §8.2 says "Citations are stripped when the draft graduates to a final artifact." The word "artifact" is doing triple duty: (a) a catalog entry (§9), (b) any file produced under `.branding/`, (c) the post-PASS, citation-stripped canonical output. Define all three in §0, or pick one.
- **"story field"** / **"tech-disclosure field"** — used as bare terms in §0's two-tier-field-rule bullet, then introduced more formally in §4.2 as "Tier 1 (story) or Tier 2 (tech-disclosure)." The §0 bullet refers to them before defining them. Either define once in §0 ("Tier 1 / story field: ...; Tier 2 / tech-disclosure field: ...") or forward-reference §4.2.
- **"graduate"** — §7.4 step 4 and §8.2 use "graduates" / "graduate" for the promotion event. This is non-obvious terminology (it means something specific in the lifecycle); define in §0.
- **"Geoffrey-Moore frame"** — §9.4 uses this without explanation. A non-MBA reader will not know what this is. Either define in §0 or inline the template's structural requirements (which are given, but the name is still unexplained).

**Defined terms that appear unused or under-used:**

- **"Painkiller"** — defined in §0 but the Y-combinator framing attribution is unnecessary for the spec's job. Consider trimming to just the painkiller-vs-vitamin distinction; the YC genealogy is biographical.
- **"BLOCK / FLAG / PASS"** — defined minimally in §0 ("the verdict set every reviewer returns per finding"), then redefined in full in §7.3. The §0 entry adds no information and risks drift. Either make §0 the full source and have §7.3 reference it, or drop the §0 entry.

**Concrete rewrite proposal for §0:**

Add these entries and standardize prose to use them verbatim:

```
- Orchestrator — the foreground Claude session (or a future meta-agent) that translates
  the founder's natural-language requests into Agent dispatches, waits for reviewer
  verdicts, and surfaces results. Distinct from the brand agent and the reviewer agents.
- Founder — the human principal operating the Abrigo workspace. Sole editor of
  facts.yml, sole authority to submit forms, sole authority to override a BLOCK.
- Draft — any versioned file under a drafts/ subdirectory (e.g., drafts/v1.md).
  Carries citations as footnotes.
- Final artifact — the citation-stripped, all-PASS output promoted to the artifact's
  canonical path (e.g., artifacts/one-pager.md, forms/<org>/answers.md).
- Graduate — the promotion event in §7.4 step 4: a draft that earns all-PASS becomes
  the final artifact at the canonical path.
- Story field / Tech-disclosure field — synonyms for Tier 1 / Tier 2 fields under §4.2.
```

---

### 2. Forward/backward references (six cross-references verified)

I cross-checked six citations in the spec against the content they claim to reference.

**Citation 1 — §9 header: "Each artifact has a canonical path, a canonical reviewer triad (per §7.1), and a canonical shape."**
- **Target:** §7.1 table.
- **Accuracy:** Correct. §7.1 does enumerate reviewer triads per artifact type.
- **Issue:** None.

**Citation 2 — §8.4: "This flagging is out of scope for the initial agent build and is captured as a follow-on capability in §12."**
- **Target:** §12 follow-on capabilities list.
- **Accuracy:** Partially correct. §12 step 7 lists "evidence-staleness detector" as a follow-on. The §12 entry is a single noun-phrase; §8.4 describes a behavior. A reader cross-walking from §8.4 to §12 will see the bullet but not the specific "flag cited artifacts for re-review" semantics.
- **Rewrite:** In §12 step 7, expand to: "**Evidence-staleness detector.** When the `MACRO_RISKS/` folder updates, flag every artifact under `.branding/` whose citations touched affected files, so the review triad can be re-dispatched. See §8.4 for behavior." Makes the citation round-trip load-bearing.

**Citation 3 — §4.1: "The authoritative source of these principles is the memory file `project_ran_positioning_principles.md`. If the memory updates, the agent prompt updates to match."**
- **Target:** memory file `project_ran_positioning_principles.md` (confirmed exists in the user memory directory).
- **Accuracy:** The file exists. I did not read its contents, so I cannot verify it contains six principles identical to those enumerated in §4.1. **This is exactly the drift risk §13 is designed to mitigate, and the drift has already begun**: §4.1 spells out the six principles in prose. If the memory file later updates to seven principles, the spec's §4.1 list becomes stale. Either (a) remove the prose enumeration and replace with "see the memory file for the current principle list" or (b) mark the §4.1 list as "snapshot at spec date; the memory file is authoritative." Option (a) is cleaner but sacrifices reader onboarding; option (b) is the honest compromise.

**Citation 4 — §6.1: "The painkiller evidence base memory file (pointer to the MACRO_RISKS folder)."**
- **Target:** `project_abrigo_painkiller_evidence_base.md`.
- **Accuracy:** The memory file exists. §0 defines the term and says "Primary: `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/`." §8.1 gives the full catalog. §6.1's one-liner undersells the evidence base's structure — a reader landing on §6.1 cold will not know the evidence base has primary / secondary / tertiary tiers. Link to §8.1 from §6.1.

**Citation 5 — §9.3: "**Initial concrete target:** Crecimiento Foundation application."**
- **Target:** §3 non-goals, "Acting as the Crecimiento-specific agent" + §11.2.
- **Accuracy:** The three statements are internally consistent (Crecimiento is a first target, not the scope), but the reader has to assemble the position from §2, §3, §9.3, and §11.2 to see it. §1 (Context) mentions Crecimiento as the "immediate trigger" but does not say "the design generalizes beyond it"; that commitment is buried in §3. Consider moving the "generalizes beyond Crecimiento" sentence from §3 into §1 so the reader meets the claim where Crecimiento first appears.

**Citation 6 — §13: "**Tier 1 feasibility survey:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`"**
- **Target:** The file path.
- **Accuracy:** File exists (verified via Glob). Good.

**Citation 7 — §5.2 bullet on `facts.yml`: "web3 ecosystems, AI tools, verticals"**
- **Target:** §9.3 Crecimiento field enumeration.
- **Accuracy:** The §5.2 bullet and §9.3 enumeration list the same fields with slightly different phrasing (§5.2 says "Crecimiento-style tech-stack disclosures"; §9.3 gives the full field list). The two lists diverge in small ways: §5.2 lists "X account, web page URL" last; §9.3 lists "Web page, X account" next-to-last. Harmonize or reference §9.3 from §5.2.

---

### 3. Reader onboarding (§0–§4 only)

**Pass test.** A contributor who reads only §0–§4 gets:
- What the product is: Abrigo, a shelter-themed external brand for an on-chain hedge product targeting underserved-FX markets. Defined in §0.
- What the spec governs: agent + workspace for external-facing copy. §0 scope line + §1 + §2.
- Why it exists: founders currently generate ad-hoc copy; there is no protocol. §1.
- What the design commits to: §4 positioning, two-tier, evidence, protocol-name abstraction, dual narrative, pilot-then-mission.

**Minor fail.** A reader who stops at §4 will not know:
- That a **review triad** gates every artifact. §2 mentions "a per-artifact three-way review loop" in one bullet; §4 is silent. A reader scanning only §4 (the "principles") will not realize the review loop is a principle-level commitment. **Rewrite:** Add a §4.7 "Review-Gated Artifacts" principle: "No artifact ships without an all-PASS review triad. The reviewers and lifecycle are specified in §7."
- That **background dispatch** is a first-class design commitment. §2 mentions it; §4 omits it. Either add a §4.7 bullet or fold background dispatch into a "Ways of Working" principle.

**Concrete rewrite:** Add two terse principles to §4 so the reader of §0–§4 sees the full commitment surface before meeting the workspace layout.

---

### 4. Concreteness of examples

**§9.3 Crecimiento worked example — verdict: appropriately concrete, minor over-specification.**

The field-by-field enumeration is the right density: a reader implementing the agent prompt can see exactly what the form asks and how each field classifies. The Tier 1 / Tier 2 calls are the payoff of §4.2.

- **Over-constraint flag:** The line "Customer type (Tier 1 — this field straddles; classify as Tier 1 and use mainstream language, e.g. "households in underserved-FX markets, plus liquidity providers supplying the hedge")" pre-writes the answer. This is implementation seepage. The spec is supposed to define the **rules** for classification; the **answer text** belongs in `forms/crecimiento/drafts/v1.md`, not the spec. **Rewrite:** "Customer type (Tier 1 — ambiguous; per §4.2 boundary rule, ambiguous fields classify as Tier 1)." Let the agent produce the text.
- **Under-constraint flag:** "Pitch deck reference (Tier 1 — points to generated artifact if available)" leaves the "if not available" branch unspecified. Does the agent leave the field blank? Write "deck forthcoming"? Generate one? Add a rule.

**§10 invocation patterns — verdict: right abstraction level.**

- Five canonical request forms is a good count — enough to anchor the contract, not so many that it reads as exhaustive. The sentence "The exact prompt wiring of each request form is an implementation-plan concern, not a spec concern" is exactly right and should be a model for other specs.
- **Flag:** The §10 examples all begin with *"Draft..."* / *"Fill..."* / *"Revise..."* / *"Run..."* / *"Show..."* — the agent has no invocation for **rejecting** a request that is out of scope (e.g., the founder says "write me an engineering spec"). §6.4 says out-of-scope attempts "must be refused." §10 should include a canonical refusal example for symmetry and so the reader knows the refusal is a first-class path, not an edge case.

---

### 5. Separation of contract vs. implementation (code-agnostic rule)

The spec is largely disciplined about this, but there are leaks.

**Leak 1 — §6.2:** "The agent is invoked via the `Agent` tool with `run_in_background: true`."
- This is a specific Claude Code API call. Per the memory convention (`feedback_no_code_in_specs_or_plans.md`: "Specs AND implementation plans must be 100% code-agnostic"), this is implementation detail.
- **Rewrite:** "The agent is dispatched asynchronously so the founder's foreground session is not blocked. The specific tool wiring belongs to the implementation plan." Move the `Agent` / `run_in_background` sentence to the future plan.
- Same issue at §7.6: "Reviewer dispatches are parallel and background (`run_in_background: true`)."
- Same issue at §10: "The orchestrator translates requests into `Agent` dispatches with `run_in_background: true`."

**Leak 2 — §0 background-dispatch glossary entry:** "agent execution pattern where the subagent runs asynchronously via the `Agent` tool with `run_in_background: true`..." — same leak at the definitional level. Rewrite to describe behavior without naming the tool.

**Leak 3 — §5.3:** "A single line in `contracts/.gitignore`: `/.branding/`." This is prescribing a specific file edit. It is borderline — some would call it a config decision, not code — but strictly it is an implementation artifact. At minimum, change "A single line" to "A single ignore rule that excludes the entire workspace directory"; the exact pattern belongs to the plan.

**Non-leak (good examples worth preserving):**
- §9.3's "Shape: per-question answer, each classified Tier 1 or Tier 2 up-front..." — describes the contract, not the syntax.
- §8.2's citation format `<relative-path>:<line-range>` — this is a **contract** for how citations must be verifiable, not an implementation detail. Keep.

---

### 6. Structural hygiene

**Section-length proportionality — verdict: mostly balanced, one outlier.**

| Section | Approximate word count | Role | Appropriate? |
|---|---|---|---|
| §0 Glossary | ~300 | Foundation | Yes |
| §1 Context | ~180 | Motivation | Yes |
| §2 Goals | ~90 | Foundation | Yes |
| §3 Non-Goals | ~100 | Foundation | Yes |
| §4 Design Principles | ~470 | Core contract | Yes |
| §5 Workspace Layout | ~280 | Core contract | Yes |
| §6 Agent Surface | ~270 | Core contract | Yes |
| §7 Review Workflow | ~680 | Core contract | Yes — largest but justified |
| §8 Evidence Grounding | ~400 | Core contract | Yes |
| §9 Artifact Catalog | ~340 | Core contract | Yes |
| §10 Invocation Patterns | ~150 | Usage | Yes |
| §11 Open Questions and Risks | ~440 | Risk | Bloated; see below |
| §12 Next Steps | ~170 | Handoff | Yes |
| §13 Sources of Truth | ~100 | Handoff | Yes |

**Bloat / misplacement flags in §11:**

- **§11.5 Reviewer Contradiction Frequency** is not a risk — it is a **monitoring commitment** ("monitored via post-hoc review of the `reviews/*-override.md` files"). Move to §12 as a follow-on capability, or fold into §7.5 as "ongoing monitoring."
- **§11.6 Founder Override Traceability** is half-risk, half-design-rule. The sentence "If overrides start accumulating, a pattern in them may indicate a positioning-principle drift that should be captured as a memory-file update" is a **feedback-loop principle**, not a risk. It belongs in §4 as a principle ("override patterns are signal") or in §7.4 as a lifecycle rule.
- **§11.7 Scope of Tier 2 Disclosure** contains an actual design rule ("Default for now: disclose at the level of granularity the form field asks for") buried inside a risk. This rule is load-bearing for §4.2 and §9.3. Promote it to §4.2.

**Rewrite:** Trim §11 to true risks (brand-name / trademark, evidence-base coupling, reviewer agent availability, Crecimiento priority). Move the three items above to their natural homes.

---

### 7. Terminological consistency — agent and memory-file naming

**Drift in agent name:**

- §0: "Abrigo branding subagent"
- Title: "Abrigo Branding Agent"
- §4: "brand agent" (§4's heading is "Design Principles" but the agent is referred to as "the agent" / "brand agent")
- §6: "Brand Agent Responsibilities" heading, then "the brand agent" in prose, then "The agent" mixed in
- §6.3: "The brand agent never reviews its own output"
- §7.1: "brand agent"
- §10: "brand agent"

Recommended canonical form: **brand agent** (lowercase, two words), with the product name form **Abrigo Brand Agent** used only in the spec title and §0. Then replace every occurrence of "branding subagent," "branding agent," and "Abrigo agent" with the canonical form.

**Drift in memory-file reference form:**

- §0 uses filenames: `project_ran_positioning_principles.md`, `project_abrigo_two_tier_field_rule.md`, `project_abrigo_painkiller_evidence_base.md`.
- §4.1 uses: "memory file `project_ran_positioning_principles.md`"
- §4.2 uses: "memory file `project_abrigo_two_tier_field_rule.md`"
- §4.3 uses: "memory file `project_abrigo_painkiller_evidence_base.md`"
- §6.1 uses human-language labels: "The positioning principles memory file," "The two-tier field rule memory file," "The Abrigo brand-name memory file," "The product-framing memory file," "The painkiller evidence base memory file."
- §13 uses filenames again: `project_ran_positioning_principles.md`, ..., `project_ran_brand_name.md`, `project_ran_product_framing.md`.

**Issue:** §6.1 lists five memory files by description; §13 lists seven by filename; §0 defines three by filename. The reader cannot mechanically map §6.1's "the product-framing memory file" to §13's `project_ran_product_framing.md` without squinting. Worse: §0 does not define "product framing" as a term, even though §6.1 requires the agent to read that memory file on every invocation.

**Rewrite:** Pick one convention. Recommendation: use filenames everywhere. Rewrite §6.1 as:

> Inputs the agent reads on every invocation:
> - `project_ran_positioning_principles.md`
> - `project_abrigo_two_tier_field_rule.md`
> - `project_ran_brand_name.md`
> - `project_ran_product_framing.md`
> - `project_abrigo_painkiller_evidence_base.md` (which points to `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/`)
> - `contracts/.branding/facts.yml`
> - The invocation-specific input …

This also closes the §0 gap (add `project_ran_brand_name.md` and `project_ran_product_framing.md` to §0's glossary as they are load-bearing).

---

### 8. Heading / list consistency

**Heading grammatical forms — mixed but not badly:**

- Noun phrases: "Context," "Goals," "Non-Goals," "Design Principles," "Workspace Layout," "Agent Surface," "Review Workflow," "Evidence Grounding Protocol," "Artifact Catalog," "Invocation Patterns," "Open Questions and Risks," "Next Steps," "Sources of Truth." All noun phrases.
- Subsection headings in §4 are noun phrases ("Positioning," "Two-Tier Field Rule," "Evidence Grounding," "Protocol-Name Abstraction," "Dual Narrative," "Pilot-Then-Mission Arc") — consistent.
- Subsection headings in §7 are noun phrases — consistent.
- **§11 subsections are noun phrases** ("Brand-Name Trademark and Domain," "Crecimiento as a Priority Target," "Evidence-Base Coupling," "Reviewer Agent Availability," "Reviewer Contradiction Frequency," "Founder Override Traceability," "Scope of Tier 2 Disclosure") — consistent.

**Heading hygiene is good.** No fix required.

**List parallelism — one flag:**

§2 Goals mixes imperative and noun phrases:
- "Provide a single, reusable agent..." (imperative, missing subject)
- "Keep all generated copy..." (imperative)
- "Ground every painkiller-adjacent claim..." (imperative)
- "Enforce a per-artifact three-way review loop..." (imperative)
- "Run drafts and reviews in the background..." (imperative)

Actually all five are imperatives. Consistent. Not a flag.

§3 Non-Goals list:
- "Generating engineering specs..." (gerund)
- "Naming or explaining the underlying protocols..." (gerund)
- "Selling decentralization..." (gerund)
- "Maintaining a trademark / domain registry..." (gerund)
- "Auto-submitting forms..." (gerund)
- "Acting as the Crecimiento-specific agent..." (gerund)

All gerunds. Consistent. Not a flag.

§4.1 principles — numbered list of declarative sentences:
1. "Target is non-crypto mainstream users."
2. "Decentralization is not a value proposition and is never sold."
3. "The product is a painkiller..."
4. "The pitch claims a 10x improvement..."
5. "Education is friction."
6. "Crypto-native and mainstream are distinct markets..."

All declarative. Consistent.

**§7.2 reviewer charters — parallelism flag:**

- "**Brand Guardian.** Enforces every positioning principle..."
- "**Reality Checker.** Verifies every painkiller claim..."
- "**Executive Summary Generator (third seat for one-pager).** Applies consultant-grade frameworks..."
- "**Content Creator (third seat for elevator pitches).** Evaluates spoken-word voice..."
- "**Proposal Strategist (third seat for application-form answers).** Evaluates win-theme alignment..."
- "**Cultural Intelligence Strategist (third seat for tagline / positioning).** Evaluates resonance..."

The first two ("Brand Guardian," "Reality Checker") do not carry the "(third seat for X)" suffix because they are the always-on pair. Consider naming them explicitly: "**Brand Guardian (always-on).** ..." and "**Reality Checker (always-on).** ..." to make parallelism complete and tell the reader the seat taxonomy without re-reading §7.1.

---

### 9. Handoff artifacts (§12 and §13)

**§12 Next Steps — verdict: adequate for an implementer, a few gaps.**

- Step 1 (three-way spec review) — correct and in convention.
- Step 2 (implementation plan via the writing-plans skill) — correct.
- Step 3 (populate `facts.yml`) — flag: the spec never defines the **schema** for `facts.yml`. §5.2 enumerates fields in prose ("team size, cofounder count, company stage, ..."); §9.3 enumerates the Crecimiento-driven fields. An implementer producing the plan will ask: does the founder write this file against a schema-by-example, a JSON schema, free-form YAML? The spec is silent. Either add a §5.4 "facts.yml Shape" subsection enumerating the required keys, or explicitly defer to the implementation plan with a sentence.
- Step 4 (author agent and reviewer prompts) — correct.
- Step 5 (first end-to-end dry run on the one-pager) — clear success criterion ("iterate to full PASS").
- Step 6 (Crecimiento submission) — tied to the validation gate in step 5. Good.
- Step 7 (follow-on capabilities) — flag: this is a capability backlog, not a next step. Move to a §12.bis or rename step 7 to "Backlog (explicitly out of scope for v1)" so the first-time reader does not treat it as required for ship.

**§13 Sources of Truth — verdict: complete but could link.**

- Memory-file entries are filenames only; a contributor on a fresh machine will not know where these live in the filesystem. Consider one leading sentence: "Memory files live in `~/.claude/projects/<project-id>/memory/`. See `MEMORY.md` in that directory for a current index." This is the one place where a stranger will be blocked without an explicit path.
- The last three entries (Tier 1 feasibility, RAN notebook, MACRO_RISKS folder) give full paths. The memory-file entries give only filenames. Inconsistent. Harmonize.

---

### 10. Memory-file coupling — is the deferral clean?

**Verdict: clean intent, leaky execution.**

The spec states its intent cleanly at the top of §13: "This spec defers to external sources of truth rather than duplicating their content. If any source updates, the spec's behavior updates with it."

**But the spec does duplicate content:**

- §4.1 spells out the six positioning principles verbatim, even though the memory file is the source of truth. If the memory updates to seven principles or re-phrases the 10x claim, the spec drifts silently.
- §4.2 restates the two-tier field rule's boundary rule ("when a field is ambiguous, classify as Tier 1") rather than deferring to the memory file.
- §9.3's Crecimiento field enumeration duplicates field lists that, if a Crecimiento-specific memory ever exists, would belong there.

**Recommendation:** Choose a stance and apply it consistently:

- **Option A (strict deferral):** §4.1, §4.2, §4.3 each reduce to a one-sentence principle name + a pointer to the memory file. Loses reader onboarding but eliminates drift.
- **Option B (snapshot with disclaimer):** Keep the prose enumeration but add a standard disclaimer at the top of §4 — "The following principles are snapshot at spec date. The memory files in §13 are authoritative and supersede this section if they diverge." Retains onboarding, names the drift risk explicitly.

Option B is the honest compromise for a rev-1 draft. Pick one and apply uniformly.

---

## Ship-readiness assessment

**Can a stranger implement this spec without the author in the room?**

**Mostly yes.** The spec's structure — context, goals, principles, workspace, agent surface, review workflow, evidence, catalog, invocation, next steps, sources — is textbook. A contributor can get to `contracts/.branding/` built, `facts.yml` schema'd, and a one-pager draft cycle running from §5, §6, §7, §9 alone.

**Gaps that would force the stranger to guess or ask:**

1. **The `facts.yml` schema is only described prose-ively in §5.2 and §9.3.** An implementer writing the plan will synthesize a schema from two places and may miss a field. Add a dedicated subsection or a schema-by-example block.
2. **The orchestrator's role is under-specified.** §10 says it translates requests; §7.6 says it waits for verdicts. Is it a human operation, a Claude Code session following a runbook, or a future sub-agent? The ambiguity is load-bearing for the implementation plan.
3. **Memory-file terminology drift (finding 7) and the `Agent` / `run_in_background` leaks (finding 5)** will each cause the implementer to pause and ask which convention is authoritative.
4. **§4.1's prose enumeration of the positioning principles vs. the memory file as source of truth (finding 10)** sets up a drift risk the author has not resolved.

**None of these are BLOCK-class.** Each is a focused 10–20 minute edit. The author should do a consistency pass against findings 7, 8, and 10 before dispatching the implementation plan skill.

**One-sentence verdict:** The spec is implementable as written, but it needs a consistency pass (memory-file names, agent names, `Agent`-tool references, `facts.yml` schema) before it cleanly stands alone as the single reference a stranger uses to implement the Abrigo brand agent without the author's shoulder to tap.

---

## Suggested edit order (to resolve all flags)

1. §0: add `orchestrator`, `founder`, `draft`, `final artifact`, `graduate`, `story field`/`tech-disclosure field`, `Geoffrey-Moore frame`; drop or defer the under-used `Painkiller` YC genealogy and `BLOCK / FLAG / PASS` stub.
2. §4: add §4.7 (review-gated artifacts) and §4.8 (background execution) so the principle surface matches §2's goal commitments.
3. §4.1–§4.3: add snapshot disclaimer or reduce to memory-file pointers (pick Option B per finding 10).
4. §4.2: promote §11.7's Tier-2 granularity default rule into §4.2.
5. §5.2/§5.4: extract a `facts.yml` shape block enumerating required keys.
6. §6.1: rewrite the memory-file input list as filenames (harmonize with §13).
7. §6.2 / §7.6 / §10 / §0: strip `Agent` tool and `run_in_background` references; re-describe as "asynchronous dispatch" behavior.
8. §7.2: add "(always-on)" suffix to Brand Guardian and Reality Checker for parallelism.
9. §9.3: cut the pre-written Customer-type answer; specify the pitch-deck-unavailable branch.
10. §10: add a canonical refusal example.
11. §11: move §11.5, §11.6, §11.7 to §4, §7, or §12 per finding 6.
12. §12 step 3: link to the new `facts.yml` shape block; step 7: rename to "Backlog."
13. §12 step 7: expand the evidence-staleness bullet to close the §8.4 round-trip.
14. §13: add a leading sentence pointing to `~/.claude/projects/<project-id>/memory/`; harmonize filename-vs-path format.
15. Global: replace "branding subagent," "branding agent," "Abrigo agent" with "brand agent" (preserve "Abrigo Brand Agent" only in title and §0).

After this pass, the verdict moves from FLAG to PASS.
