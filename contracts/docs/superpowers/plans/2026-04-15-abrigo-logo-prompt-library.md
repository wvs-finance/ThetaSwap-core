# Abrigo Logo Prompt Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **No-code rule:** Per project convention `feedback_no_code_in_specs_or_plans.md`, this plan is code-agnostic. The artifacts produced here are markdown prose (Midjourney prompts) — the plan describes what each task produces, not the prompt text itself. The Image Prompt Engineer specialist writes the actual prompt bodies under supervision.

**Goal:** Build the 8-variant Abrigo Midjourney logo prompt library defined in `contracts/docs/superpowers/specs/2026-04-15-abrigo-logo-prompt-library-design.md`, through graduation to the final library file.

**Architecture:** A single graduated markdown file at `contracts/.branding/artifacts/logo-prompts.md` containing eight Midjourney prompt variants across four logo types (mark, wordmark, combination, scene). Authored by the Image Prompt Engineer specialist; reviewed by a three-seat triad (Image Prompt Engineer self-review for technical craft + Brand Guardian for brand contract + Cultural Intelligence Strategist for regional reading); iterated per the standard Abrigo artifact lifecycle.

**Tech Stack:** Claude Code subagents (Image Prompt Engineer, Brand Guardian, Cultural Intelligence Strategist), markdown, shell commands (mkdir, git). No compiled code.

**Reference documents:**
- Spec: `contracts/docs/superpowers/specs/2026-04-15-abrigo-logo-prompt-library-design.md`
- Parent-system spec: `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` (Rev 3) — lifecycle §7.4, reviewer inventory §15
- Sibling artifact (graduated): `contracts/.branding/artifacts/taglines.md`
- Existing parent-brand reference (not reused): `contracts/.scratch/dsquared-pi-logo-prompt.md`
- Positioning memory: `project_ran_positioning_principles.md`
- Brand name memory: `project_ran_brand_name.md`

---

## Phase 0 — Prerequisites

### Task 0.1: Verify Image Prompt Engineer charter fit

**Files:**
- Read: `/home/jmsbpp/.claude/agents/image-prompt-engineer.md` (or wherever the agent lives — grep if unclear)
- Create: `contracts/.scratch/2026-04-15-abrigo-logo-engineer-charter-check.md`

- [ ] **Step 1: Define success criteria.** A short note confirming the Image Prompt Engineer's frontmatter charter and prompt body match the spec §8.1 authorship expectation (photography-oriented is acceptable if brand-logo work is within scope; photography-only is not). If the charter is too photography-narrow, note that a dispatch-time augmentation template (parallel to the Claim Auditor pattern) will be needed; do NOT author it yet — that is a spec revision, not a plan task.

- [ ] **Step 2: Locate the agent file.** Run `find /home/jmsbpp/.claude/agents/ -iname '*image*prompt*'` and `find /home/jmsbpp/.claude/agents/ -iname '*prompt*engineer*'`. Confirm the file exists.

- [ ] **Step 3: Read frontmatter + first 50 lines.** Extract the `description:` field and the opening posture paragraphs. Compare to spec §8.1 and §9.1.

- [ ] **Step 4: Write the charter-check note.** One or two paragraphs — charter summary, fit assessment, any redirect needed at dispatch time.

- [ ] **Step 5: Decision gate.** If charter is logo/brand-friendly → proceed to Task 0.2. If photography-only → surface to founder; pause Phase 0.

- [ ] **Step 6: Commit.**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
git add contracts/.scratch/2026-04-15-abrigo-logo-engineer-charter-check.md
git commit -m "chore(abrigo): Image Prompt Engineer charter check for logo library"
```

### Task 0.2: Create logo-prompts directory tree

**Files:**
- Create: `contracts/.branding/artifacts/logo-prompts/drafts/`
- Create: `contracts/.branding/artifacts/logo-prompts/reviews/`

- [ ] **Step 1: Define success criteria.** Two empty directories exist at the listed paths. `ls -R contracts/.branding/artifacts/logo-prompts/` shows the tree. Git status lists nothing (the parent `.branding/` is gitignored).

- [ ] **Step 2: Create the tree.**

```bash
mkdir -p contracts/.branding/artifacts/logo-prompts/drafts contracts/.branding/artifacts/logo-prompts/reviews
```

- [ ] **Step 3: Verify.** Run `ls -R contracts/.branding/artifacts/logo-prompts/`. Both subdirectories must appear.

- [ ] **Step 4: No commit.** Gitignored.

---

## Phase 1 — Draft v1

### Task 1.1: Dispatch Image Prompt Engineer to author v1

**Files:**
- Create: `contracts/.branding/artifacts/logo-prompts/drafts/v1.md`
- Create: `contracts/.branding/artifacts/logo-prompts/drafts/v1-facts-snapshot.yml`
- Create: `contracts/.branding/artifacts/logo-prompts/drafts/v1-source-manifest.md`

- [ ] **Step 1: Define success criteria.** A markdown library at v1.md with all 8 variants present, each following the spec §6 schema (variant name + role, what it emphasizes, usage, full Midjourney prompt with parameters, negative guidance, iteration notes). Library structure per spec §5: 2 symbol-only marks (Archway-A, Terracotta-roof), 2 wordmarks (Humanist wordmark, Editorial display wordmark), 2 combinations (Archway-A stacked, Terracotta-roof inline), 2 scenes (Courtyard-light, Terracotta-roof morning). Visual vocabulary per spec §4 (hybrid vernacular-shelter + modern-finance); all §4.2 bans enforced in every variant's negative-guidance section. Companion facts-snapshot names `brand_name`, `pilot_market`, `mission_scope` from `facts.yml`. Source-manifest is a stub (no painkiller citations in image prompts).

- [ ] **Step 2: Dispatch the Image Prompt Engineer** via the Agent tool with `subagent_type: Image Prompt Engineer` and a prompt that supplies: the spec path, the parent-system spec path (for lifecycle reference), the brand-name + positioning memory file paths, the existing d²π Labs prompt file at `contracts/.scratch/dsquared-pi-logo-prompt.md` (as a Midjourney-syntax reference only, not as content to mimic), explicit output paths (absolute) for all three files, and the §4.2 ban list to embed in every variant.

- [ ] **Step 3: Wait for completion.** Background dispatch returns a summary when done.

- [ ] **Step 4: Verify files landed.** Run `ls -la contracts/.branding/artifacts/logo-prompts/drafts/`. All three files must exist with non-trivial size.

- [ ] **Step 5: Founder intuition-check.** Read v1.md end-to-end. Spot-check: every variant names Midjourney parameters explicitly (`--ar`, `--v`, `--style`, `--stylize`); every variant has a negative-guidance section that names at least the colonial-specificity ban and the crypto-cliché ban; the architectural-scene variants explicitly state no-people; the symbol marks are prompted for flat vector, not photographic. If any variant obviously misses the vocabulary or the bans, abort and re-dispatch rather than spending reviewer cycles.

- [ ] **Step 6: No commit.** Gitignored.

---

## Phase 2 — Review Triad on v1

Three specialists in parallel, background. Verdicts land in `reviews/v1-<seat>.md`.

### Task 2.1: Dispatch Brand Guardian

**Files:**
- Create: `contracts/.branding/artifacts/logo-prompts/reviews/v1-brand-guardian.md`

- [ ] **Step 1: Define success criteria.** A verdict file with per-finding BLOCK/FLAG/PASS + overall verdict, keyed to the §4.2 ban list and the brand-contract dimensions (vocabulary adherence, no colonial labeling, no crypto cliché, no stereotype imagery, visual-vocabulary alignment with warm-but-disciplined hybrid).

- [ ] **Step 2: Dispatch** via Agent tool, `subagent_type: Brand Guardian`, `run_in_background: true`. Supply the invocation template path (`contracts/.claude/agents/abrigo-orchestrator-prompts/brand-guardian-invocation.md`), the substituted placeholders (`{draft_path}` = absolute path to `v1.md`, `{reviews_dir}` = absolute path to `reviews/`, `{revision_number}` = 1, `{artifact_type}` = logo prompt library), and an explicit instruction that for this artifact type Brand Guardian enforces the spec §4.2 ban list in addition to the usual positioning / two-tier / brand-name checks. Also supply the spec path so Brand Guardian can read the vocabulary.

- [ ] **Step 3: No commit, gitignored.** Verdict arrives asynchronously.

### Task 2.2: Dispatch Cultural Intelligence Strategist

**Files:**
- Create: `contracts/.branding/artifacts/logo-prompts/reviews/v1-cultural-intelligence-strategist.md`

- [ ] **Step 1: Define success criteria.** Verdict file with per-finding BLOCK/FLAG/PASS + overall, focused on the three cultural-fit reads from spec §4.3 (Colombian household recognition, decolonial-aware symbolism check, mission-scope translation check). Any finding that a shelter element inadvertently stereotypes, or that the vocabulary does not survive translation to other underserved-FX markets, must be concretely described with proposed fixes.

- [ ] **Step 2: Dispatch** via Agent tool, `subagent_type: Cultural Intelligence Strategist`, `run_in_background: true`. Invocation template at `contracts/.claude/agents/abrigo-orchestrator-prompts/cultural-intelligence-strategist-invocation.md`; same placeholder substitutions as Task 2.1; explicit note that the artifact is image prompts (not copy) so the §7.2.1 tiebreaker still applies (Brand Guardian owns brand-contract, CIS owns stereotype/exclusion/translation-adjacency). Include spec §4.3 as required reading.

- [ ] **Step 3: No commit, gitignored.**

### Task 2.3: Dispatch Image Prompt Engineer self-review

**Files:**
- Create: `contracts/.branding/artifacts/logo-prompts/reviews/v1-image-prompt-engineer.md`

- [ ] **Step 1: Define success criteria.** Verdict file with per-finding BLOCK/FLAG/PASS + overall, focused on technical prompt craft: Midjourney syntax correctness, parameter calibration (ar / v / style / stylize values plausible for the variant's use-case), negative-prompt discipline (bans stated as actual prompt directives, not as prose commentary), prompt length (no runaway), cliché avoidance at the craft level (does the prompt use overworn Midjourney tokens like "photorealistic masterpiece 8k ultra-detailed" that degrade output on brand work). Technical-only — brand and cultural findings are out of scope for this seat.

- [ ] **Step 2: Dispatch** via Agent tool, `subagent_type: Image Prompt Engineer`, `run_in_background: true`. Supply the draft path, the spec's §6 schema as the structural contract to verify, and an explicit "self-review is for technical craft only; brand and cultural content are checked by other seats — do not comment on those here" instruction. Output path absolute.

- [ ] **Step 3: No commit, gitignored.**

### Task 2.4: Wait for all three verdicts and read them

- [ ] **Step 1: Define success criteria.** All three verdict files exist at `reviews/v1-*.md`. Orchestrator has read each file end-to-end and noted overall verdicts + any contradictions.

- [ ] **Step 2: Wait for background completions.** Do not advance until all three have notified.

- [ ] **Step 3: Read each verdict file.** Note per-seat overall verdict (BLOCK / FLAG / PASS). Note any contradictions between seats (e.g., Brand Guardian wants warmer palette, Image Prompt Engineer wants more restrained weight).

- [ ] **Step 4: Decision gate.** If all three PASS at v1 → skip to Phase 4 (graduation). If any BLOCK or FLAG → proceed to Phase 3 revision.

- [ ] **Step 5: No commit, gitignored.**

---

## Phase 3 — Iterate to Graduation

Repeat the revision cycle until three PASS verdicts all reference the same revision `N`, or the hard cap of 5 revisions is reached.

### Task 3.1: Dispatch Image Prompt Engineer to revise

**Files:**
- Create: `contracts/.branding/artifacts/logo-prompts/drafts/v{N+1}.md`
- Create: `contracts/.branding/artifacts/logo-prompts/drafts/v{N+1}-diff-rationale.md`
- Create: `contracts/.branding/artifacts/logo-prompts/drafts/v{N+1}-facts-snapshot.yml`
- Create: `contracts/.branding/artifacts/logo-prompts/drafts/v{N+1}-source-manifest.md`

- [ ] **Step 1: Define success criteria.** A revised library at `v{N+1}.md` that addresses every reviewer finding from revision `N`'s three verdict files, plus a diff-rationale file walking through each finding ID (e.g., BG-F1, CIS-F2, IPE-F3) and explaining how the revision addresses it. Any finding the engineer chooses NOT to fully address must be justified explicitly in the diff-rationale.

- [ ] **Step 2: Dispatch Image Prompt Engineer** via Agent tool, `subagent_type: Image Prompt Engineer`, `run_in_background: true`. Supply the current draft path, all three verdict file paths, absolute output paths for the four v{N+1} files, and explicit instruction to read every verdict before drafting.

- [ ] **Step 3: Verify files landed.** All four v{N+1} files must exist.

- [ ] **Step 4: No commit, gitignored.**

### Task 3.2: Re-dispatch the triad on v{N+1}

Same three dispatches as Phase 2 Tasks 2.1, 2.2, 2.3 but with:
- `{draft_path}` updated to `v{N+1}.md` absolute path
- `{revision_number}` updated to `N+1`
- Each dispatch also reads the diff-rationale file

- [ ] **Step 1: Dispatch Brand Guardian** on v{N+1}, background.
- [ ] **Step 2: Dispatch Cultural Intelligence Strategist** on v{N+1}, background.
- [ ] **Step 3: Dispatch Image Prompt Engineer self-review** on v{N+1}, background.
- [ ] **Step 4: Wait for all three completions.**
- [ ] **Step 5: Read verdicts. Apply graduation rule:** all three overall verdicts must be PASS and all three verdict files must reference revision `N+1` (not an earlier revision).
- [ ] **Step 6: Decision gate.** If graduated → Phase 4. If not → repeat Phase 3 with `N+1` incremented.
- [ ] **Step 7: No commit, gitignored.**

### Task 3.3: Hard-cap guard

- [ ] **Step 1: Define success criteria.** If revision count reaches 5 without graduation, the orchestrator halts and surfaces all verdict files + all draft revisions to the founder with a "no convergence after 5 attempts" note. Founder decides whether to override a BLOCK via `reviews/v{N}-override.md` with written justification, re-scope the spec, or abandon the library.

- [ ] **Step 2: Track revision count explicitly.** After each Task 3.2 cycle, note the current revision number. Do not silently enter revision 6.

- [ ] **Step 3: On cap hit, write the founder-handoff note** at `contracts/.scratch/2026-04-15-abrigo-logo-cap-hit.md` summarizing each revision's blocker pattern, then pause.

- [ ] **Step 4: No commit unless founder authorizes.** The scratch note is not committed until the founder reviews.

---

## Phase 4 — Graduate

### Task 4.1: Promote the graduated revision

**Files:**
- Copy: `contracts/.branding/artifacts/logo-prompts/drafts/v{N}.md` → `contracts/.branding/artifacts/logo-prompts.md`
- Copy: `contracts/.branding/artifacts/logo-prompts/drafts/v{N}-source-manifest.md` → `contracts/.branding/artifacts/logo-prompts-source-manifest.md`

Where `N` is the revision that achieved three PASS verdicts in Phase 3.

- [ ] **Step 1: Define success criteria.** Final library at `contracts/.branding/artifacts/logo-prompts.md`. Source manifest alongside. Drafts retained for provenance (do not delete).

- [ ] **Step 2: Promote.**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
# Replace N with the graduated revision number
cp contracts/.branding/artifacts/logo-prompts/drafts/vN.md contracts/.branding/artifacts/logo-prompts.md
cp contracts/.branding/artifacts/logo-prompts/drafts/vN-source-manifest.md contracts/.branding/artifacts/logo-prompts-source-manifest.md
```

- [ ] **Step 3: Verify.** `ls contracts/.branding/artifacts/logo-prompts.md contracts/.branding/artifacts/logo-prompts-source-manifest.md`. Both exist.

- [ ] **Step 4: No commit, gitignored.**

### Task 4.2: Founder reads the graduated library

- [ ] **Step 1: Define success criteria.** The founder has read all eight variants in `logo-prompts.md` and confirms the library is ready to be used (Midjourney runs against the prompts).

- [ ] **Step 2: Founder reads the file end-to-end.** Flag any variant where the Midjourney prompt feels ambiguous enough that running it would be wasted credits. Flag any variant where the usage guidance does not match real intended surfaces.

- [ ] **Step 3: Log feedback.** If any variant needs touch-up, create an override note at `contracts/.branding/artifacts/logo-prompts/reviews/v{N}-founder-override.md` and either patch the graduated file manually or loop back to Phase 3 for a targeted revision.

- [ ] **Step 4: No commit.**

---

## Phase 5 — Optional Samples Capture

Deferred by default. Run only after the founder has generated images from the library and wants to preserve the best ones with reproducibility metadata.

### Task 5.1: Capture best sample per variant

**Files:**
- Create: `contracts/.branding/artifacts/logo-prompts/samples/<variant-slug>-<timestamp>.png` (or .jpg)
- Create: `contracts/.branding/artifacts/logo-prompts/samples/<variant-slug>-<timestamp>.md` (metadata: which variant, Midjourney seed, URL or image ref, founder notes)

- [ ] **Step 1: Define success criteria.** For each variant the founder chooses to preserve, one image file + one metadata sidecar exist under `samples/`. Metadata includes: variant name (matching the library), the Midjourney seed / job ID, the originating URL if applicable, the founder's notes on why this image represents the variant.

- [ ] **Step 2: Founder drops files into `samples/`** manually. The orchestrator does not generate images.

- [ ] **Step 3: No commit.** Gitignored.

---

## Phase 6 — Wrap-Up

### Task 6.1: Brief retrospective

**Files:**
- Create: `contracts/.scratch/2026-04-15-abrigo-logo-retrospective.md`

- [ ] **Step 1: Define success criteria.** Short retrospective capturing: number of revisions to graduation, which variants needed the most rework, which bans Midjourney's defaults pushed against hardest, any charter-drift observed in Image Prompt Engineer or CIS, any vocabulary additions to bake into spec §4 for the next image-adjacent artifact.

- [ ] **Step 2: Write it.** 150–300 words. Bullet-pointed is fine.

- [ ] **Step 3: Commit.**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
git add contracts/.scratch/2026-04-15-abrigo-logo-retrospective.md
git commit -m "docs(abrigo): logo prompt library v1 retrospective"
```

### Task 6.2: Commit the spec and plan

**Files:**
- `contracts/docs/superpowers/specs/2026-04-15-abrigo-logo-prompt-library-design.md`
- `contracts/docs/superpowers/plans/2026-04-15-abrigo-logo-prompt-library.md`

- [ ] **Step 1: Define success criteria.** Both files are tracked in git (untracked before this task).

- [ ] **Step 2: Commit.**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom
git add contracts/docs/superpowers/specs/2026-04-15-abrigo-logo-prompt-library-design.md contracts/docs/superpowers/plans/2026-04-15-abrigo-logo-prompt-library.md
git commit -m "docs(abrigo): logo prompt library spec + plan"
```

---

## Spec-Coverage Self-Check

| Spec section | Implementing task(s) |
|---|---|
| §0 Glossary | no task (reference) |
| §1 Context | no task (motivation) |
| §2 Goals | Phases 1–4 produce all 4 goals |
| §3 Non-goals | enforced by Task 1.1 Step 1 success criteria |
| §4.1 Vocabulary | Task 1.1 Step 1 requires vocabulary palette; Task 2.1 and 2.2 verify |
| §4.2 Bans | Task 1.1 Step 1 + Step 5 (founder spot-check); Task 2.1 (Brand Guardian enforces) |
| §4.3 Cultural-fit reads | Task 2.2 (CIS enforces) |
| §5 Library structure | Task 1.1 Step 1 (8 variants in four types) |
| §6 Per-variant schema | Task 1.1 Step 1 + Task 2.3 (Image Prompt Engineer self-review verifies schema) |
| §7 File layout | Task 0.2 (directory tree) + Task 1.1 (drafts) + Task 4.1 (graduated) |
| §8.1 Authorship | Task 1.1 + Task 3.1 (Image Prompt Engineer) |
| §8.2 Triad | Tasks 2.1, 2.2, 2.3 + Tasks 3.2 Steps 1–3 |
| §8.3 Lifecycle | Phase 2 → Phase 3 → Phase 4, with hard cap in Task 3.3 |
| §9 Open questions | §9.1 → Task 0.1; §9.2 monitored in Task 6.1; §9.3 monitored in Task 6.1; §9.4 iteration-notes in library; §9.5 explicitly deferred |
| §10 Next steps | steps 1–7 map to plan phases; step 8 is out-of-scope follow-on |
| §11 Sources of truth | cited throughout as required reading |

Coverage complete.

---

## Placeholder Scan

No TBD / TODO / XXX / FIXME. The `v{N}` notation is a lifecycle variable (standard across the Abrigo system per parent spec §7.4), not a placeholder for unfinished content.

## Type / Naming Consistency

- "Image Prompt Engineer" (exact catalog name) used consistently — not "image prompt agent" or "IPE" except as finding-ID prefix.
- "Brand Guardian" and "Cultural Intelligence Strategist" use their full catalog names.
- Revision-stamp convention `v{N}.md` matches the parent spec.
- File paths use `contracts/` prefix even though the worktree root is `contracts/`; a future executor can run `cd contracts/` and interpret absolute paths unambiguously.
