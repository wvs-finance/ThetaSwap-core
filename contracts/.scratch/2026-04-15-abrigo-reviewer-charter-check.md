# Reviewer Charter-Drift Check (Post-Un-Archive)

**Date:** 2026-04-15
**Task:** Plan Rev 2, Task 0.1 Step 7
**Spec reference:** `docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` Rev 3, §7.2, §15

## Method

For each of the five un-archived reviewer agents, read the frontmatter `name:` and `description:` fields plus the first portion of the prompt body. Compare against the §7.2 charter summary for the corresponding triad seat. Note drift and remediation.

## Findings

### Brand Guardian (`/home/jmsbpp/.claude/agents/brand-guardian.md`)

- **Frontmatter name:** `Brand Guardian`
- **Frontmatter description:** *"Expert brand strategist and guardian specializing in brand identity development, consistency maintenance, and strategic brand positioning"*
- **§7.2 charter (Abrigo-specific):** *"Enforces every positioning principle, the two-tier field rule, brand-name consistency, and protocol-name abstraction."*
- **Drift:** generic scope vs. Abrigo-specific positioning rules. Agent does not know about the two-tier field rule, protocol-name abstraction, or the specific Abrigo positioning principles.
- **Remediation:** dispatch-time prompt augmentation via Task 3.1 invocation template. The template injects §7.2 charter + positioning memory + two-tier rule + brand-name memory as required reading before the agent reviews. Agent file itself unchanged.
- **Status:** acceptable drift; no blocker.

### Executive Summary Generator (`/home/jmsbpp/.claude/agents/executive-summary-generator.md`)

- **Frontmatter name:** `Executive Summary Generator`
- **Frontmatter description:** *"Consultant-grade AI specialist ... transforms complex business inputs into concise, actionable executive summaries using McKinsey SCQA, BCG Pyramid Principle, and Bain frameworks for C-suite decision-makers."*
- **§7.2 charter (Abrigo-specific):** *"Applies consultant-grade frameworks (SCQA, pyramid principle, Bain/BCG executive-summary craft) to ensure the one-pager has a single clear thesis, a logical cascade, and a decision-readiness surface."*
- **Drift:** near-match. Frontmatter already names SCQA, Pyramid, Bain. §7.2 adds the Abrigo-specific one-pager shape (§9.1) as the target. Agent does not know about §9.1.
- **Remediation:** dispatch-time template cites §9.1 artifact shape as required reading.
- **Status:** minimal drift; no blocker.

### Content Creator (`/home/jmsbpp/.claude/agents/content-creator.md`)

- **Frontmatter name:** `Content Creator`
- **Frontmatter description:** *"Expert content strategist and creator for multi-platform campaigns. Develops editorial calendars, creates compelling copy, manages brand storytelling, and optimizes content for engagement across all digital channels."*
- **§7.2 charter (Abrigo-specific):** *"Evaluates spoken-word voice, pacing, listener retention, transition craft, and the 30-second hook. Ensures the pitch sounds like a human speaking, not a document being read."*
- **Drift:** moderate. Generic agent is written-copy-focused; §7.2 is spoken-word-focused for elevator pitches. The two lenses overlap but are not identical.
- **Remediation:** dispatch-time template redirects the agent from written-copy to spoken-word evaluation for pitch artifacts only. For any future artifact that is written copy (social posts, long-form blog), the generic charter applies and no redirection is needed.
- **Status:** acceptable drift with explicit dispatch-time override.

### Proposal Strategist (`/home/jmsbpp/.claude/agents/proposal-strategist.md`)

- **Frontmatter name:** `Proposal Strategist`
- **Frontmatter description:** *"Strategic proposal architect who transforms RFPs and sales opportunities into compelling win narratives. Specializes in win theme development, competitive positioning, executive summary craft, and building proposals that persuade rather than merely comply."*
- **§7.2 charter (Abrigo-specific):** *"Evaluates win-theme alignment, per-question compliance with the form's explicit prompt, and the competitive positioning implicit in each answer."*
- **Drift:** near-match. Generic agent already covers win themes and executive summary craft. §7.2 adds the Abrigo-specific form-filling context (hackathon / accelerator / grant applications, not sales RFPs).
- **Remediation:** dispatch-time template names the specific form (Crecimiento, or future targets) and cites §7.2.1 tiebreaker with Claim Auditor.
- **Status:** minimal drift; no blocker.

### Cultural Intelligence Strategist (`/home/jmsbpp/.claude/agents/cultural-intelligence-strategist.md`)

- **Frontmatter name:** `Cultural Intelligence Strategist`
- **Frontmatter description:** *"CQ specialist that detects invisible exclusion, researches global context, and ensures software resonates authentically across intersectional identities."*
- **§7.2 charter (Abrigo-specific):** *"Evaluates resonance across the mission geography (underserved-FX countries broadly, Colombia specifically), absence of unintentional stereotype, and dignity of the household protagonist."*
- **Drift:** near-match. Generic agent covers exclusion detection and cultural resonance. §7.2 adds the Abrigo-specific mission geography (underserved-FX, Colombia pilot).
- **Remediation:** dispatch-time template cites mission-scope note in product-framing memory + the household-protagonist narrative.
- **Status:** minimal drift; no blocker.

## Resolution Strategy

All five drifts are addressed by Task 3.1 / 3.2 dispatch-time prompt augmentation. No agent files are modified; no Abrigo-specific variants authored. This is **spec Rev 3 §15 option (a) realized at dispatch time** rather than at agent-file-edit time, which is cleaner because:
- Agent files stay generic and reusable for other projects.
- All Abrigo-specific context lives in versioned invocation templates under `contracts/.claude/agents/abrigo-orchestrator-prompts/`.
- Rollback is a template edit, not a user-level agent-file edit.

## Proceed Decision

**Proceed to Task 0.2.** No Abrigo-specific agent variants need to be authored in Phase 0. Task 3.1 (invocation templates) is the concrete implementation of charter alignment.
