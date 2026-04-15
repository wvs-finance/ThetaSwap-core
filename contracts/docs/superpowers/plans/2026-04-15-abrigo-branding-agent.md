# Abrigo Branding Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **No-code rule:** Per project convention `feedback_no_code_in_specs_or_plans.md`, this plan is code-agnostic. Each task specifies required file content in prose, required test assertions in prose, and exact file paths + shell commands. The engineer executing the task writes the actual markdown / YAML / prompt text under supervision.

**Plan Status:** Rev 2 (absorbs three-way plan-review findings from 2026-04-15: corrects archive paths, replaces settings.json-only enforcement with PreToolUse hook + session permissions, expands Task 1.3 time estimate, fixes `<artifact>` glob ambiguity, adds Phase 7.0 intake-open pre-check, adds Phase 8 scoping, fixes memory-count in Task 2.1, adds verbatim-facts rule to brand agent contract, adds PASS-weak handling for sketch-form evidence.)

**Goal:** Build the Abrigo branding-agent system defined in `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` Rev 3, through and including the first Crecimiento Foundation form submission.

**Architecture:** A single background-dispatched brand agent (committed subagent definition at `contracts/.claude/agents/abrigo-brand-agent.md`) writes copy drafts into a gitignored workspace at `contracts/.branding/`. A three-reviewer panel (Brand Guardian + Claim Auditor + rotating third seat) verifies every draft. A PreToolUse hook plus session-level `settings.json` permissions enforce read/write scope boundaries at runtime. The founder's foreground Claude session plays the orchestrator role in v1.

**Tech Stack:** Claude Code subagents (markdown with frontmatter), Claude Code hooks (PreToolUse), Claude Code `settings.json` session-level permissions, shell commands (git, mv, mkdir, sha256sum), YAML for `facts.yml`, markdown for all artifacts and verdict files. No compiled code, no build system, no external services.

**Reference documents:**
- Spec: `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` (Rev 3)
- Positioning memory: `project_ran_positioning_principles.md`
- Product framing memory: `project_ran_product_framing.md`
- Brand name memory: `project_ran_brand_name.md`
- Two-tier field rule memory: `project_abrigo_two_tier_field_rule.md`
- Painkiller evidence memory: `project_abrigo_painkiller_evidence_base.md`
- Painkiller evidence base: `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/`
- Three-way review convention: `feedback_three_way_review.md`
- No-code convention: `feedback_no_code_in_specs_or_plans.md`

---

## Phase 0 — Prerequisites

Bootstrap the runtime conditions the spec assumes. Nothing in later phases will work correctly until Phase 0 completes.

### Task 0.1: Un-archive the five reviewer agents (rename on move)

**Files:**
- Move + rename: `/home/jmsbpp/.claude/agents/_archived/design/design-brand-guardian.md` → `/home/jmsbpp/.claude/agents/brand-guardian.md`
- Move + rename: `/home/jmsbpp/.claude/agents/_archived/support/support-executive-summary-generator.md` → `/home/jmsbpp/.claude/agents/executive-summary-generator.md`
- Move + rename: `/home/jmsbpp/.claude/agents/_archived/marketing/marketing-content-creator.md` → `/home/jmsbpp/.claude/agents/content-creator.md`
- Move + rename: `/home/jmsbpp/.claude/agents/_archived/sales/sales-proposal-strategist.md` → `/home/jmsbpp/.claude/agents/proposal-strategist.md`
- Move + rename: `/home/jmsbpp/.claude/agents/_archived/specialized/specialized-cultural-intelligence-strategist.md` → `/home/jmsbpp/.claude/agents/cultural-intelligence-strategist.md`

Per spec Rev 3 §15, the real archived paths carry category prefixes; the plan's Rev 1 paths were wrong. Rename drops the prefix so dispatch names are clean.

- [ ] **Step 1: Define success criteria.** After this task, `ls /home/jmsbpp/.claude/agents/*.md` must include all five clean filenames, the frontmatter `name:` field of each file must equal its new clean basename (not the prefixed archived name), and the Claude Code session must be able to dispatch each via `subagent_type: <clean-name>`.

- [ ] **Step 2: Verify archive state.** Run each of these separately and confirm a non-empty result per command:
  - `ls /home/jmsbpp/.claude/agents/_archived/design/design-brand-guardian.md`
  - `ls /home/jmsbpp/.claude/agents/_archived/support/support-executive-summary-generator.md`
  - `ls /home/jmsbpp/.claude/agents/_archived/marketing/marketing-content-creator.md`
  - `ls /home/jmsbpp/.claude/agents/_archived/sales/sales-proposal-strategist.md`
  - `ls /home/jmsbpp/.claude/agents/_archived/specialized/specialized-cultural-intelligence-strategist.md`
  
  If any is missing, the spec Rev 3 §15 path is wrong; abort and surface to the founder before moving anything.

- [ ] **Step 3: Move + rename each file one at a time.** Use five separate `mv` commands (not a glob, not a loop). After each `mv`, run `ls` on both the source directory and `/home/jmsbpp/.claude/agents/` to confirm the move. If any `mv` fails, stop and investigate before continuing.

- [ ] **Step 4: Update the frontmatter `name:` field** in each moved file to match the new clean basename. A file's frontmatter still saying `name: design-brand-guardian` after the move breaks dispatch. Edit each file; verify with `grep -n '^name:' /home/jmsbpp/.claude/agents/<clean-name>.md`.

- [ ] **Step 5: Check for internal references to the old prefixed name.** `grep -r 'design-brand-guardian\|support-executive-summary-generator\|marketing-content-creator\|sales-proposal-strategist\|specialized-cultural-intelligence-strategist' /home/jmsbpp/.claude/agents/ /home/jmsbpp/.claude/commands/ 2>/dev/null`. Any hits point to places the rename broke cross-references; patch those.

- [ ] **Step 6: Restart the Claude Code session** so the moved agents become dispatchable under the new names. A fresh session always suffices.

- [ ] **Step 7: Charter-drift check per reviewer.** For each of the five agents, read frontmatter + first 50 lines of prompt body. Compare against the §7.2 charter summary in the spec. Spec Rev 3 §15 defaults to option (c) when drift is present: author Abrigo-specific variants. Write findings to `contracts/.scratch/2026-04-15-abrigo-reviewer-charter-check.md` with one entry per reviewer: "matches §7.2" or "drift: <describe>; remediation: (c) variant authored at contracts/.claude/agents/abrigo-<seat>.md". If any reviewer requires option (c), add the variant-authoring sub-tasks now (new §5.5 tasks, below) before proceeding.

- [ ] **Step 8: Rollback plan.** If a move later needs to be reversed (e.g., charter drift is unfixable), `mv` the file back from the clean active path to its original archived path including the category subdirectory. Keep a scratch note listing each original path so the mapping is not lost. Write the note to `contracts/.scratch/2026-04-15-abrigo-un-archive-rollback.md` before Step 3.

- [ ] **Step 9: Commit the charter-check report and rollback note.**

```bash
git add contracts/.scratch/2026-04-15-abrigo-reviewer-charter-check.md contracts/.scratch/2026-04-15-abrigo-un-archive-rollback.md
git commit -m "chore(abrigo): verify reviewer charters post-un-archive"
```

### Task 0.2: Author the PreToolUse hook and session-level permissions

**Files:**
- Create: `contracts/.claude/hooks/abrigo-scope-guard.sh` (or `.py` — pick one per the Claude Code hook schema; verify in Step 1)
- Create or modify: `contracts/.claude/settings.json` (session-level permissions + hook registration)

Per spec Rev 3 §14, enforcement uses two layers: a PreToolUse hook (primary gate, per-subagent scoping) and session-level `settings.json` permissions (second layer, blast-radius denials regardless of subagent). Per-subagent write allow/deny patterns in `settings.json` alone are not a documented Claude Code feature; the plan-review Reality Checker verified this — do not revert to a settings-only approach.

**Layer 1: PreToolUse Hook**

- [ ] **Step 1: Verify the hook feature schema.** Consult the Claude Code documentation (or use the `update-config` skill) to confirm (a) how hooks are registered in `settings.json`, (b) what JSON input the hook receives for Write / Edit tool calls (must include tool name, target file path, and ideally the active subagent's name or dispatch context), (c) what exit code / stdout convention the hook uses to deny a call. Write findings to `contracts/.scratch/2026-04-15-abrigo-hook-schema.md`.

- [ ] **Step 2: Define hook success criteria.** The hook must (a) receive every Write / Edit / MultiEdit tool call before execution; (b) parse the active subagent identity from the dispatch context (name, id, or equivalent signal); (c) parse the target path from the tool input; (d) deny the call with a non-zero exit code or explicit deny signal when subagent × path is out-of-scope per spec §14.1; (e) allow the call silently when in-scope; (f) log every decision to `contracts/.scratch/abrigo-hook-decisions.log` for debugging.

- [ ] **Step 3: Define per-subagent scope map.** Encode in the hook:
  - `abrigo-brand-agent`: write-allow `contracts/.branding/**`; deny all other paths including external paths.
  - `brand-guardian`, `executive-summary-generator`, `content-creator`, `proposal-strategist`, `cultural-intelligence-strategist`: write-allow `contracts/.scratch/**`, `contracts/.branding/**/reviews/**`; deny elsewhere. `contracts/.branding/**/drafts/**` is write-deny for reviewers (they don't modify drafts).
  - `testing-reality-checker` when dispatched as Claim Auditor (identified by a marker in the invocation prompt that the hook's dispatch-context parser recognizes): same scope as other reviewers.
  - Any subagent not listed: pass through (no enforcement) to avoid breaking unrelated workflows.

- [ ] **Step 4: Author the hook script** per Step 2's contract. Prefer a small script (~50 lines) that reads the JSON event, evaluates the scope map, and emits allow/deny. Keep it dependency-free (bash, Python stdlib, or Node stdlib — whichever the Claude Code hook schema natively supports best).

- [ ] **Step 5: Register the hook** in `contracts/.claude/settings.json` under the PreToolUse event per the schema from Step 1.

- [ ] **Step 6: Smoke-test the hook.** The brand agent does not exist yet (Task 2.1) but the hook can be exercised by dispatching any available subagent with a write to an out-of-scope path and verifying the hook denies. Use `testing-reality-checker` or any active agent; temporarily add it to the scope map for this test, then remove after.

**Layer 2: Session-level permissions**

- [ ] **Step 7: Define session-permissions success criteria.** The `settings.json` `permissions.deny` block denies writes to `src/**`, `test/**`, `script/**`, `lib/**`, `docs/superpowers/specs/**`, `docs/superpowers/plans/**`, `/home/jmsbpp/apps/liq-soldk-dev/**`, `/home/jmsbpp/.claude/**` (except through explicit founder action). These denials apply regardless of which subagent (if any) is active.

- [ ] **Step 8: Write the permissions block.** Use the `update-config` skill to produce syntax-correct JSON. Hand-writing risks schema drift.

- [ ] **Step 9: Smoke-test session permissions.** From the founder's foreground session, attempt `Write` to `src/TEST_DENIED.txt`. Expected: denied. Remove any artifact if created.

- [ ] **Step 10: Document the interaction between layers.** Write a short `contracts/.claude/PERMISSIONS.md` noting: the hook handles per-subagent scoping; session permissions handle blast-radius denials; when a write is denied, the founder inspects the hook log and session permissions to determine which layer caught it.

- [ ] **Step 11: Commit.**

```bash
git add contracts/.claude/settings.json contracts/.claude/hooks/ contracts/.claude/PERMISSIONS.md contracts/.scratch/2026-04-15-abrigo-hook-schema.md
git commit -m "feat(abrigo): PreToolUse scope-guard hook + session permissions"
```

### Task 0.3a: MACRO_RISKS evidence-base pre-flight

**Files:**
- Create: `contracts/.scratch/2026-04-15-abrigo-evidence-preflight.md`

- [ ] **Step 1: Define success criteria.** A note documenting (a) that `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/` exists and is readable; (b) which files inside have prose-finished content (usable for strong PASS) versus sketch content (usable only for PASS-weak per spec §11.13); (c) at least one concrete line-range citation that could ground a directional inflation-erosion claim about Colombian households, for use in Task 3.2's smoke test.

- [ ] **Step 2: Verify folder readable.** `ls /home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/`. If empty or missing, halt and surface to founder.

- [ ] **Step 3: Classify each file** as prose-finished or sketch. Read each `.md` file; note which are pseudocode/arrow-notation sketches and which are finished prose.

- [ ] **Step 4: Find a load-bearing citation.** Identify at least one prose paragraph in `MACRO_RISKS.md` or a sibling file that, at a specific line range, supports a directional claim about inflation eroding household purchasing power in underserved-FX markets. Record the path and line range in the note. Task 3.2 smoke test uses this citation.

- [ ] **Step 5: Commit.**

```bash
git add contracts/.scratch/2026-04-15-abrigo-evidence-preflight.md
git commit -m "chore(abrigo): MACRO_RISKS evidence-base preflight check"
```

### Task 0.3: Add `.branding/` to `.gitignore`

**Files:**
- Modify: `contracts/.gitignore`

- [ ] **Step 1: Define success criteria.** A new line `/.branding/` is added to `contracts/.gitignore`. Running `git status` from the worktree root does not list any file under `contracts/.branding/`, including files created by later tasks.

- [ ] **Step 2: Inspect the current `.gitignore`** with `cat contracts/.gitignore` and identify a sensible insertion point (adjacent to `/out`, `/cache`, `/broadcast` which are already ignored as peer directories).

- [ ] **Step 3: Add the single line `/.branding/`** to `.gitignore` at the chosen insertion point.

- [ ] **Step 4: Verify the ignore works.** Run `mkdir -p contracts/.branding && touch contracts/.branding/probe.txt && git status contracts/`. Confirm `probe.txt` is not listed. Remove `probe.txt` after confirming.

- [ ] **Step 5: Commit.**

```bash
git add contracts/.gitignore
git commit -m "chore(abrigo): gitignore the branding workspace"
```

---

## Phase 1 — Workspace Bootstrap

Create the gitignored working surface, populate the hand-edited source of truth, and document the conventions.

### Task 1.1: Create the `.branding/` directory tree

**Files:**
- Create: `contracts/.branding/` (root)
- Create: `contracts/.branding/forms/` (per-form subdirectories land here later)
- Create: `contracts/.branding/forms/crecimiento/`
- Create: `contracts/.branding/forms/crecimiento/drafts/`
- Create: `contracts/.branding/forms/crecimiento/reviews/`
- Create: `contracts/.branding/artifacts/`
- Create: `contracts/.branding/artifacts/one-pager/`
- Create: `contracts/.branding/artifacts/one-pager/drafts/`
- Create: `contracts/.branding/artifacts/one-pager/reviews/`

- [ ] **Step 1: Define success criteria.** All listed directories exist and are empty (no files yet). `ls -R contracts/.branding/` shows the tree. `git status` lists nothing (Task 0.3 must be complete).

- [ ] **Step 2: Create the tree** using one `mkdir -p` invocation per directory or a single invocation with multiple arguments. Prefer explicit creation over `mkdir -p contracts/.branding/{forms/crecimiento/{drafts,reviews},artifacts/one-pager/{drafts,reviews}}` brace expansion — Claude Code's bash environment behaves differently than an interactive shell and the expansion can silently produce the wrong tree.

- [ ] **Step 3: Verify** with `ls -R contracts/.branding/` and visually confirm the tree matches the spec §5.2.

- [ ] **Step 4: No commit for this task.** Contents are gitignored; there is nothing to track.

### Task 1.2: Author `contracts/.branding/README.md`

**Files:**
- Create: `contracts/.branding/README.md`

- [ ] **Step 1: Define success criteria.** A human-readable markdown document placed at the root of the gitignored workspace, explaining: (a) the purpose of the workspace, (b) that everything in it is gitignored on purpose, (c) what each subdirectory holds, (d) the canonical request forms from spec §10, (e) a pointer to the spec and the memory files, (f) the graduate-file lifecycle (`drafts/v{N}.md` → final path after 3 PASSes at same revision), (g) a note that the file itself is also gitignored.

- [ ] **Step 2: Write the README.** Describe workspace conventions in the founder's own voice (second person, "you"). Follow the spec §5–§10 for authoritative content. Do not repeat the positioning principles verbatim — link to the memory file instead.

- [ ] **Step 3: Verify readability.** Read the file end-to-end. A contributor landing cold should understand the directory's purpose within 60 seconds. If not, revise.

- [ ] **Step 4: No commit.** Gitignored.

### Task 1.3: Populate `contracts/.branding/facts.yml`

**Files:**
- Create: `contracts/.branding/facts.yml`

**Time estimate:** 30–60 minutes. This is a founder-authored business-facts file with ~25 fields, several of which require real decisions (stage enum selection, raising-round framing, cofounder-role wording, traction statement phrasing). The plan's overall "2–5 minute step" guideline does not apply; this is a sit-down session.

- [ ] **Step 1: Define success criteria.** A YAML document with every hard-tier field from spec §5.2.1 populated with a truthful current value. Every soft field is either populated with a real value or explicitly set to `pending` with a sibling `facts_citations.<field>` entry explaining when and how the value will arrive. The brand agent (Task 2.1) must be able to read the file and not fail any hard-field check.

- [ ] **Step 2: List the hard fields** from spec §5.2.1 (Tier 1 + Tier 2): `brand_name`, `legal_entity_status`, `founding_date`, `pilot_market`, `mission_scope`, `cofounder_count`, `cofounder_roles`, `team_size`, `employee_roles`, `company_stage`, `product_stage`, `current_raising_round`, `primary_language_stack`, `hosting_provider`, `web3_ecosystems`, `ai_tools_used`, `verticals`, `other_tech_notes`.

- [ ] **Step 3: List the soft fields** from spec §5.2.1: `pilot_traction_statement`, `user_count`, `transaction_volume`, `partnership_list`, `website_url`, `x_handle`, `contact_email`, `pitch_deck_url`, `brand_name_qualifier`, `tagline_pin`. Note that `brand_name_qualifier` and `tagline_pin` were omitted from the Rev 1 enumeration; this Rev 2 adds them per the plan-review finding.

- [ ] **Step 4: Founder writes hard-field values.** This is not work the brand agent can do. Defaults per spec: `brand_name: Abrigo`, `pilot_market: Colombia`, `mission_scope: underserved-FX countries`. The Tier 2 tech-disclosure fields name protocols and ecosystems factually here per the two-tier rule — Angstrom, Panoptic, Mento, Celo, Claude Code, Ethereum L1, etc. as appropriate.

- [ ] **Step 5: Founder writes or `pending`-marks soft fields.** For any field marked `pending`, add `facts_citations.<field>: <plan-or-source-path>` explaining how the value will be sourced later. Example: `facts_citations.x_handle: "pending domain clearance; expected within 1 week per project_ran_brand_name.md"`.

- [ ] **Step 6: Schema validation.** Until the brand agent exists, validate manually: every hard field is present and non-empty; every soft `pending` has a citation plan; `brand_name_qualifier` and `tagline_pin` are populated or explicitly `null` (not missing).

- [ ] **Step 7: No commit.** Gitignored.

---

## Phase 2 — Brand Agent Definition

Author the committed subagent that drafts copy.

### Task 2.1: Author `contracts/.claude/agents/abrigo-brand-agent.md`

**Files:**
- Create: `contracts/.claude/agents/abrigo-brand-agent.md`

- [ ] **Step 1: Define success criteria (the prompt's behavioral contract).** The subagent, when dispatched, must: (a) read every source of truth in spec §13 before drafting — 7 memory files plus 3 non-memory sources (the Tier 1 feasibility methodology spec, `ranPricing.ipynb`, and the `MACRO_RISKS/` folder); (b) read `contracts/.branding/facts.yml` and refuse to draft artifacts dependent on any missing hard field; (c) read the painkiller evidence base before painkiller-adjacent drafting; (d) obey the two-tier field rule when filling forms; (e) attach citations (file path + line range) to every painkiller-adjacent claim; (f) never name Angstrom, Panoptic, Mento, Uniswap, or Ethereum in Tier 1 copy; (g) write output only to `contracts/.branding/**/drafts/v{N}.md` and an accompanying `v{N}-diff-rationale.md` when revising; (h) never write to any other path; (i) never review its own output; (j) output a companion `v{N}-facts-snapshot.yml` capturing the subset of `facts.yml` that the draft cited (spec §11.8); (k) output a companion `v{N}-source-manifest.md` with content-hashes of every cited evidence file (spec §8.4); (l) **never paraphrase, round, infer, or compute quantitative facts** — traction numbers, team sizes, stage labels, dates, URLs, handles — but substitute the verbatim value from `facts.yml` (spec §6.1 quantitative-facts rule, §11.9).

- [ ] **Step 2: Write the subagent definition** as a markdown file with YAML frontmatter containing `name: abrigo-brand-agent`, a description field suitable for the Agent tool's routing, and (if the Claude Code version supports it) a tool allowlist restricting to Read, Write, Edit, Grep, Glob. The body of the file is the system prompt encoding the behavioral contract above plus the positioning principles (by reference to the memory file, not by duplication), the two-tier field rule, and the artifact-shape spec from §9.

- [ ] **Step 3: Pre-flight dry-read.** Before smoke-testing, read the entire prompt aloud. Every behavioral requirement in Step 1 must be addressable by a specific paragraph of the prompt. Any requirement that the prompt does not clearly cover is a prompt bug.

- [ ] **Step 4: Smoke test — memory loading.** Dispatch the agent with a trivial prompt ("read every memory file in your sources of truth and report the filename of each"). Verify the agent responds with all seven memory filenames. If it misses any, refine the prompt.

- [ ] **Step 5: Smoke test — facts.yml validation.** Dispatch the agent with a prompt asking it to list the hard fields present in `facts.yml` and any missing ones. Verify output matches Task 1.3's populated set.

- [ ] **Step 6: Smoke test — protocol-name abstraction.** Dispatch the agent with a prompt asking it to write one sentence explaining the product to a Colombian household. Verify the output names none of {Angstrom, Panoptic, Mento, Uniswap, Ethereum, options, pool, LP, tick, liquidity}. If any appear, refine the prompt.

- [ ] **Step 7: Smoke test — write-scope boundary.** Dispatch the agent with a prompt asking it to modify an arbitrary file under `contracts/src/` (pick any existing `.sol` file from the tree — confirm it exists via `ls` before dispatching, because hard-coded paths rot). Verify the PreToolUse hook from Task 0.2 denies the write. If the write succeeds, Task 0.2 is wrong — go back and fix the hook before continuing.

- [ ] **Step 8: Smoke test — verbatim-facts rule.** Dispatch the agent with a prompt: "draft one sentence summarizing our team size for the Crecimiento application." Read the draft. If the number in the draft is literally the value of `facts.yml:team_size` (e.g., "2 people" if the field is `2`), PASS. If the agent paraphrased ("a small team," "a couple of founders," rounded to "around 3"), the prompt needs sharpening on the quantitative-facts rule.

- [ ] **Step 9: Smoke test — citation attachment.** Dispatch the agent with a prompt: "draft one sentence about inflation shock for Colombian households, with a citation." Verify the output contains a citation in the form `<path>:<line-range>` pointing to a real location inside `MACRO_RISKS/`. If the citation is absent or to a nonexistent path, refine the prompt.

- [ ] **Step 10: Smoke test — self-review refusal.** Dispatch the agent with a prompt: "review your own draft from the previous dispatch and produce a verdict file." Verify the agent refuses (spec §6.3). If it complies, the prompt's self-review prohibition is not load-bearing; refine.

- [ ] **Step 11: Smoke test — companion-file emission.** Dispatch the agent with a prompt asking it to draft the one-pager. After it completes, confirm `v1.md`, `v1-facts-snapshot.yml`, and `v1-source-manifest.md` all exist in the drafts directory. If any is missing, refine the prompt.

- [ ] **Step 12: Commit.**

```bash
git add contracts/.claude/agents/abrigo-brand-agent.md
git commit -m "feat(abrigo): brand agent subagent definition"
```

---

## Phase 3 — Review Triad Wiring

Wire the orchestrator's dispatch prompts for each reviewer seat.

### Task 3.1: Author orchestrator-side invocation prompts for Brand Guardian and rotating third seats

**Files:**
- Create: `contracts/.claude/agents/abrigo-orchestrator-prompts/brand-guardian-invocation.md`
- Create: `contracts/.claude/agents/abrigo-orchestrator-prompts/executive-summary-generator-invocation.md`
- Create: `contracts/.claude/agents/abrigo-orchestrator-prompts/content-creator-invocation.md`
- Create: `contracts/.claude/agents/abrigo-orchestrator-prompts/proposal-strategist-invocation.md`
- Create: `contracts/.claude/agents/abrigo-orchestrator-prompts/cultural-intelligence-strategist-invocation.md`

These are not subagent definitions — they are text templates the orchestrator (the founder's foreground session) copies into its dispatch prompts when invoking each reviewer. Keeping them versioned as separate files lets them evolve without re-writing the orchestrator's session instructions.

- [ ] **Step 1: Define success criteria per template.** Each template must instruct the reviewer to: (a) read the spec's §7.2 charter for its seat; (b) read the artifact under review at the specified path; (c) read `facts.yml` snapshot (not live) for the revision being reviewed; (d) read all relevant memory files; (e) for Brand Guardian, read Appendix A permissions and verify the draft does not reference the protocol names; (f) output a single verdict file at the artifact-specific reviews path — for artifact-type deliverables the path is `contracts/.branding/artifacts/<artifact-name>/reviews/v{N}-<seat>.md`, for form-type deliverables the path is `contracts/.branding/forms/<org-slug>/reviews/v{N}-<seat>.md`; the template receives the full reviews-path as a placeholder from the orchestrator rather than constructing it from a single ambiguous `<artifact>` token; (g) apply the §7.2.1 charter-overlap tiebreakers when the seat is Brand Guardian (skip findings CIS owns) or Proposal Strategist (read Claim Auditor verdict first).

- [ ] **Step 2: Write each template** following the Step 1 contract. Templates differ in which third-seat charter they instantiate; Brand Guardian's template is identical across artifact types. Each template accepts three orchestrator-substituted placeholders: `{draft_path}` (the absolute path of the draft file under review), `{reviews_dir}` (the directory where the verdict file is written — either `artifacts/<name>/reviews/` or `forms/<org>/reviews/`), and `{revision_number}` (the numeric `N` in `v{N}`). No single ambiguous `<artifact>` token.

- [ ] **Step 3: Templates must not cite the wrong files.** Brand Guardian's template cites the positioning-principle memory and brand-name memory. Executive Summary Generator's cites no memory beyond the spec's §9.1 artifact shape. Content Creator's cites §9.2. Proposal Strategist's cites §9.3. Cultural Intelligence Strategist's cites the mission-scope note in the product-framing memory.

- [ ] **Step 4: Verify each template independently.** For each template, dispatch the corresponding reviewer against a minimal contrived draft (e.g., a 2-sentence fake one-pager) and verify the reviewer produces a verdict file at the expected path with the expected structure.

- [ ] **Step 5: Commit.**

```bash
git add contracts/.claude/agents/abrigo-orchestrator-prompts/
git commit -m "feat(abrigo): orchestrator invocation templates for review triad"
```

### Task 3.2: Author the Claim Auditor prompt augmentation

**Files:**
- Create: `contracts/.claude/agents/abrigo-orchestrator-prompts/claim-auditor-invocation.md`

This template redirects the existing Reality Checker subagent from its native code/UI QA charter to copy-claim auditing against the painkiller evidence base. Per spec §7.1 the underlying subagent is reused unchanged; the augmentation lives entirely in this dispatch prompt.

- [ ] **Step 1: Define success criteria.** The template instructs the Reality Checker to (a) ignore its default code/UI QA posture for this invocation; (b) treat every painkiller-adjacent claim in the draft as a hypothesis requiring citation-check against the painkiller evidence base; (c) resolve each citation against the actual file and line range, not the prose around it; (d) emit a verdict file at `{reviews_dir}/v{N}-claim-auditor.md` where `{reviews_dir}` is passed by the orchestrator (same substitution convention as Task 3.1); (e) default to BLOCK on any uncited claim; (f) FLAG claims whose citation supports only a weaker directional phrasing; (g) PASS only claims whose citation supports the claim as-phrased; (h) use the PASS-weak verdict from spec §11.13 when a citation supports the claim only at sketch-form evidence quality. The template explicitly defers to spec §8.3's evidence-failure-mode table.

- [ ] **Step 2: Write the template** per Step 1's contract. Include the painkiller evidence base paths from spec §8.1 as required reading.

- [ ] **Step 3: Smoke test — BLOCK on uncited claim.** Dispatch the Reality Checker with this template against a contrived draft containing one sentence "Colombians lose 12.7% of their savings to inflation yearly" with no citation. Verify the verdict is BLOCK on that finding.

- [ ] **Step 4: Smoke test — PASS on grounded claim.** Modify the contrived draft to add a citation pointing to a real paragraph in `MACRO_RISKS.md` (use a line range you can verify supports some inflation-erosion claim, or adjust the claim to match what the file says). Dispatch again. Verify the finding PASSes or FLAGs appropriately.

- [ ] **Step 5: Smoke test — name-collision non-interference.** Dispatch the Reality Checker without the augmentation prompt against a normal code-review task to verify the augmentation is per-invocation and does not permanently alter the agent.

- [ ] **Step 6: Commit.**

```bash
git add contracts/.claude/agents/abrigo-orchestrator-prompts/claim-auditor-invocation.md
git commit -m "feat(abrigo): claim auditor prompt augmentation (reuses reality checker)"
```

---

## Phase 4 — Source-Manifest Staleness

Define and verify the minimum viable evidence-staleness protocol from spec §8.4.

### Task 4.1: Author the source-manifest format specification

**Files:**
- Create: `contracts/.claude/agents/abrigo-orchestrator-prompts/source-manifest-format.md`

- [ ] **Step 1: Define success criteria.** A short prose specification of the `v{N}-source-manifest.md` file format that the brand agent emits alongside every draft and the `source-manifest.md` file that travels with every graduated artifact. The format must: (a) list every cited evidence-base file; (b) record the content-hash of each at the time the brand agent cited it; (c) be parseable by the orchestrator with shell utilities (so: a simple list of `<path>\t<hash>` lines, or a YAML list with `path` and `hash` keys — pick one, be explicit).

- [ ] **Step 2: Write the format.** Pick one of: (a) tab-separated `path\thash` lines, (b) YAML list with `path` and `hash` keys. YAML is easier to extend later; TSV is simpler to shell-parse. Recommend YAML.

- [ ] **Step 3: Specify the hash algorithm.** SHA-256 of the raw file bytes. No whitespace normalization, no line-ending normalization. Record hashes with `sha256sum` (Linux) and document the command in the format spec.

- [ ] **Step 4: Specify staleness-check algorithm.** For a graduated artifact's `source-manifest.md`: orchestrator iterates every entry, runs `sha256sum <path>`, compares to recorded hash. Mismatches are collected into a `source-manifest-drift.md` sibling file listing each drifted path. If the drift file is non-empty before external submission, orchestrator notifies the founder.

- [ ] **Step 5: Commit.**

```bash
git add contracts/.claude/agents/abrigo-orchestrator-prompts/source-manifest-format.md
git commit -m "feat(abrigo): source-manifest format for evidence staleness protocol"
```

### Task 4.2: Staleness round-trip verification (contrived)

**Files:**
- Temporary scratch: `contracts/.branding/artifacts/one-pager/drafts/v1-source-manifest.md` (created and deleted inside this task)
- Temporary scratch: a contrived file inside `.branding/` that is "cited" for test purposes — do not touch the real MACRO_RISKS folder

- [ ] **Step 1: Define success criteria.** Orchestrator can detect a mutated source file and emit a `source-manifest-drift.md`.

- [ ] **Step 2: Create a contrived test fixture.** Inside `contracts/.branding/`, create a disposable subdirectory `_staleness-test/` containing one text file `evidence.md` with fixed content. Do not touch the real evidence folder.

- [ ] **Step 3: Write a manifest** per Task 4.1's format citing the fixture file with its current SHA-256 hash.

- [ ] **Step 4: Mutate the fixture** (append one line to `evidence.md`).

- [ ] **Step 5: Run the staleness-check algorithm manually** — recompute hash, compare, write a drift file listing the path.

- [ ] **Step 6: Verify drift file content** matches what the algorithm should emit.

- [ ] **Step 7: Clean up.** Remove `_staleness-test/` and the contrived manifest.

- [ ] **Step 8: No commit.** The test is ephemeral; the algorithm specification was committed in Task 4.1.

---

## Phase 5 — Orchestrator Operating Procedure

Document the operating procedure the founder (in v1, human + foreground Claude session) follows when running the system.

### Task 5.1: Author the orchestrator operating procedure

**Files:**
- Create: `contracts/.claude/agents/abrigo-orchestrator-prompts/orchestrator-procedure.md`

- [ ] **Step 1: Define success criteria.** A single markdown document that walks the orchestrator through each canonical request form from spec §10 with exact behavior for each: which subagent to dispatch, what prompt template to use, what placeholder substitutions to make, what files to expect as output, when to trigger the revision cycle, how to detect the three-PASS-at-same-revision graduation condition, how to surface contradictions, how to run the pre-submission staleness check.

- [ ] **Step 2: Write the procedure** as an ordered walkthrough of the artifact lifecycle (spec §7.4). Include a decision tree for verdict aggregation: if all three seats PASS → graduate; if any BLOCK or FLAG → revise; if two consecutive revisions BLOCK on the same finding → surface to founder.

- [ ] **Step 3: Document revision-stamping rigor.** The procedure must explicitly check that all three verdict files reference the same `v{N}` before declaring graduation. Document the check as a specific step.

- [ ] **Step 4: Document contradiction-surfacing.** When two reviewers' findings contradict (e.g., Brand Guardian wants softening, Claim Auditor wants sharpening), the procedure instructs the orchestrator to present both verdict files and the contradiction summary to the founder for resolution rather than asking the brand agent to merge.

- [ ] **Step 5: Document the pre-submission publish-check.** Before any external submission (form submit, deck share, public one-pager link), the orchestrator runs the staleness algorithm from Task 4.1 and surfaces any drift.

- [ ] **Step 6: Commit.**

```bash
git add contracts/.claude/agents/abrigo-orchestrator-prompts/orchestrator-procedure.md
git commit -m "feat(abrigo): orchestrator operating procedure"
```

---

## Phase 6 — First Dry Run (One-Pager)

End-to-end validation of the system on a real artifact before attempting the Crecimiento form.

### Task 6.1: Draft the one-pager

**Files:**
- Create: `contracts/.branding/artifacts/one-pager/drafts/v1.md`
- Create: `contracts/.branding/artifacts/one-pager/drafts/v1-facts-snapshot.yml`
- Create: `contracts/.branding/artifacts/one-pager/drafts/v1-source-manifest.md`

- [ ] **Step 1: Define success criteria.** A one-pager draft exists at the v1 path, follows the §9.1 shape (problem / solution / dual protagonist / pilot / mission / traction / team / contact), cites painkiller claims, has a facts snapshot and source manifest alongside.

- [ ] **Step 2: Orchestrator dispatches the brand agent** with the prompt "Draft the Abrigo one-pager per spec §9.1. Write to `contracts/.branding/artifacts/one-pager/drafts/v1.md` with companion snapshot and manifest files." Run in background per spec §6.2.

- [ ] **Step 3: Founder reads the draft.** Read v1.md end-to-end. Read the facts-snapshot and source-manifest companion files. Confirm the companion files exist and are populated.

- [ ] **Step 4: Founder intuition-check before review.** If the draft obviously violates the positioning rules on the founder's first read (names a protocol, sells decentralization, reads as crypto-native), do not spend reviewer cycles — revise the brand-agent prompt (Task 2.1) first. If the draft reads at least plausibly on-brand, proceed to review.

- [ ] **Step 5: No commit.** Gitignored.

### Task 6.2: Review triad on the one-pager

**Files:**
- Create: `contracts/.branding/artifacts/one-pager/reviews/v1-brand-guardian.md`
- Create: `contracts/.branding/artifacts/one-pager/reviews/v1-claim-auditor.md`
- Create: `contracts/.branding/artifacts/one-pager/reviews/v1-executive-summary-generator.md`

- [ ] **Step 1: Define success criteria.** Three verdict files exist at the v1 paths, each with an overall verdict and per-finding verdicts.

- [ ] **Step 2: Orchestrator dispatches the three reviewers in parallel**, all background. Each uses its Phase 3 invocation template with the artifact path and revision number substituted.

- [ ] **Step 3: Wait for all three completions.** Do not read verdict files until all three exist.

- [ ] **Step 4: Read all three verdicts.** Note overall verdicts and contradictions.

- [ ] **Step 5: No commit.** Gitignored.

### Task 6.3: Iterate until graduation

**Files:**
- Create: `contracts/.branding/artifacts/one-pager/drafts/v{N}.md` for each revision
- Create: `contracts/.branding/artifacts/one-pager/drafts/v{N}-diff-rationale.md` for each revision
- Create: `contracts/.branding/artifacts/one-pager/drafts/v{N}-facts-snapshot.yml` for each revision
- Create: `contracts/.branding/artifacts/one-pager/drafts/v{N}-source-manifest.md` for each revision
- Create: `contracts/.branding/artifacts/one-pager/reviews/v{N}-{seat}.md` for each revision × seat

- [ ] **Step 1: Define success criteria.** For some revision `N`, all three verdict files at `v{N}` report PASS, and the orchestrator's revision-stamp check from Task 5.1 passes.

- [ ] **Step 2: For each FLAG/BLOCK revision, orchestrator re-dispatches the brand agent** with the current draft plus all three verdicts. Brand agent produces `v{N+1}.md`, `v{N+1}-diff-rationale.md`, `v{N+1}-facts-snapshot.yml`, `v{N+1}-source-manifest.md`.

- [ ] **Step 3: Re-dispatch the triad against `v{N+1}`.**

- [ ] **Step 4: Repeat until three PASSes at the same revision**, or until two consecutive revisions BLOCK on the same finding (in which case surface to founder), **or until a hard cap of 5 revisions is reached** (after which the orchestrator halts and surfaces "no convergence after 5 attempts" to the founder with all verdict files attached). The cap prevents infinite loops when reviewer charters are fundamentally misaligned with the draft's premise.

- [ ] **Step 5: Founder-override safety valve.** If progress stalls on a finding the founder believes is wrong, write `contracts/.branding/artifacts/one-pager/reviews/v{N}-override.md` with justification and graduate manually.

- [ ] **Step 6: No commit.** Gitignored.

### Task 6.4: Graduate the one-pager

**Files:**
- Move: `contracts/.branding/artifacts/one-pager/drafts/v{N}.md` → `contracts/.branding/artifacts/one-pager.md`
- Copy: `contracts/.branding/artifacts/one-pager/drafts/v{N}-source-manifest.md` → `contracts/.branding/artifacts/one-pager-source-manifest.md`

- [ ] **Step 1: Define success criteria.** The final artifact lives at `contracts/.branding/artifacts/one-pager.md`. Its source manifest sits beside it at `one-pager-source-manifest.md`. The drafts folder retains the full history for provenance but is not read further.

- [ ] **Step 2: Promote the draft.** `mv` the graduated draft. `cp` the manifest (keep the drafts copy for provenance).

- [ ] **Step 3: Run the publish-check.** Execute the staleness algorithm from Task 4.1 against the new manifest. Expected: no drift at this moment (same session that generated it). If drift shows, something is wrong with the hash recording — debug before proceeding.

- [ ] **Step 4: No commit.** Gitignored.

---

## Phase 7 — Crecimiento Submission

With the lifecycle validated in Phase 6, produce the real first-use output. Phase 7 adds one gating pre-check before any drafting work: the external application target must be verified live and accepting submissions. This gate is required by spec §11.12.

### Task 7.0: Verify Crecimiento intake is open

**Files:**
- Create: `contracts/.scratch/2026-04-15-crecimiento-intake-check.md`

- [ ] **Step 1: Define success criteria.** A short note stating (a) the date the intake was verified, (b) the URL of the application page checked, (c) whether the form was live, (d) any stated deadline, (e) any prerequisites the form mentions (KYC, legal entity, documents). If the form is closed or the URL 404s, Phase 7 halts and the founder decides whether to defer or switch targets.

- [ ] **Step 2: Founder visits the Crecimiento application URL.** The URL should already be known from the prior form paste (conversation context); if not, search Crecimiento Foundation's public presence. Confirm the form loads and accepts applications as of today.

- [ ] **Step 3: Write the intake-check note.** Include a screenshot path (saved to `.scratch/`) if possible, or at minimum the page title and first question verbatim as proof of load.

- [ ] **Step 4: Decision gate.** If intake closed: halt Phase 7, escalate to founder. If open: proceed to Task 7.1.

- [ ] **Step 5: Commit the intake-check note.**

```bash
git add contracts/.scratch/2026-04-15-crecimiento-intake-check.md
git commit -m "chore(abrigo): verify Crecimiento intake open before drafting"
```

### Task 7.1: Paste Crecimiento questions

**Files:**
- Create: `contracts/.branding/forms/crecimiento/questions.md`

- [ ] **Step 1: Define success criteria.** A markdown file containing every Crecimiento form question verbatim, in the order the form presents them, with field-label and field-type noted (required / optional, single-line / multi-line / select).

- [ ] **Step 2: Founder pastes the form.** The founder copies the form from Crecimiento's application page into `questions.md`. Mark each question with the tier classification in a comment — this is a Phase-7-specific note, not a brand-agent input.

- [ ] **Step 3: Founder pre-classifies each question Tier 1 or Tier 2.** This is a sanity check against the two-tier rule before the agent classifies. Disagreements between founder and brand agent at draft time are resolved by re-reading the two-tier memory.

- [ ] **Step 4: No commit.** Gitignored.

### Task 7.2: Draft the Crecimiento answers

**Files:**
- Create: `contracts/.branding/forms/crecimiento/drafts/v1.md` (with companion snapshot and manifest)

- [ ] **Step 1: Define success criteria.** Draft covers every question from `questions.md`. Each answer is labeled Tier 1 or Tier 2 by the brand agent. Tier 1 answers obey positioning rules. Tier 2 answers are factually drawn from `facts.yml`. Length limits from the form are respected.

- [ ] **Step 2: Orchestrator dispatches the brand agent** with the instruction "Fill the Crecimiento form at `contracts/.branding/forms/crecimiento/questions.md`. Write to `forms/crecimiento/drafts/v1.md` with companion files."

- [ ] **Step 3: Founder reads the draft.** Sanity-check tier classification on every question. Flag any classification disagreement for the brand-agent prompt refinement (Task 2.1) and for this draft's revision cycle.

- [ ] **Step 4: No commit.** Gitignored.

### Task 7.3: Review triad on Crecimiento answers

**Files:**
- Create: `contracts/.branding/forms/crecimiento/reviews/v1-brand-guardian.md`
- Create: `contracts/.branding/forms/crecimiento/reviews/v1-claim-auditor.md`
- Create: `contracts/.branding/forms/crecimiento/reviews/v1-proposal-strategist.md`

Third seat is Proposal Strategist per spec §7.1.

- [ ] **Step 1: Define success criteria.** Three verdicts, each using the form-answer-specific charter. Brand Guardian additionally checks that Tier 2 answers (tech-disclosure) do NOT leak crypto into Tier 1 answers. Proposal Strategist checks the application as a whole reads as a funding argument, not a list of disconnected paragraphs.

- [ ] **Step 2: Dispatch all three in parallel, background.** Use the Phase 3 templates with `{artifact_type}=application-form-answers`.

- [ ] **Step 3: Iterate per Phase 6 Task 6.3** until three PASSes at the same revision or founder override.

- [ ] **Step 4: No commit.** Gitignored.

### Task 7.4: Graduate and publish-check Crecimiento answers

**Files:**
- Move: `contracts/.branding/forms/crecimiento/drafts/v{N}.md` → `contracts/.branding/forms/crecimiento/answers.md`
- Copy: the corresponding source manifest to `forms/crecimiento/answers-source-manifest.md`

- [ ] **Step 1: Define success criteria.** Final answer file at `forms/crecimiento/answers.md`. Source manifest beside it. Staleness check runs clean.

- [ ] **Step 2: Promote, copy manifest, run publish-check** per Task 6.4 pattern.

- [ ] **Step 3: No commit.** Gitignored.

### Task 7.5: Founder submits the form

- [ ] **Step 1: Define success criteria.** The founder pastes each answer from `answers.md` into the Crecimiento application form and submits.

- [ ] **Step 2: Manual submission.** Not automatable in v1 — forms with file uploads and dropdown selectors resist robotic submission. The brand-agent system is a drafting system, not a submission system.

- [ ] **Step 3: Snapshot the submitted form state.** After submission, copy `answers.md` to `forms/crecimiento/submitted.md` and mark it read-only. This is the frozen-forever record of what was actually submitted; any later edits to `answers.md` do not affect the submitted file.

- [ ] **Step 4: No commit.** Gitignored.

---

## Phase 8 — Wrap-Up

Previous phases built, validated, and executed the system end-to-end on one real external submission. Phase 8 captures learnings so the next submission (another accelerator, a grant, an investor) benefits, and queues follow-on capabilities the spec punted. No new subsystems are built in Phase 8.

### Task 8.1: Retrospective and memory updates

**Files:**
- Update: `contracts/.scratch/2026-04-15-abrigo-v1-retrospective.md`

- [ ] **Step 1: Define success criteria.** A short retrospective documenting what worked, what broke, which prompts needed refinement, which reviewer seats returned the most useful findings, any memory file that needs updating.

- [ ] **Step 2: Write the retrospective** after the Crecimiento submission lands. Cover: number of revision rounds to graduation for the one-pager; same for the Crecimiento form; reviewer contradictions encountered; any BLOCK → PASS paths that were slow.

- [ ] **Step 3: Update memory files** based on learnings. The positioning-principles, product-framing, and two-tier-field-rule memories may need refinement. Do not edit them speculatively; only edit them against concrete lessons.

- [ ] **Step 4: Commit retrospective.**

```bash
git add contracts/.scratch/2026-04-15-abrigo-v1-retrospective.md
git commit -m "docs(abrigo): v1 retrospective after first Crecimiento submission"
```

### Task 8.2: Queue follow-on capabilities

**Files:**
- Update: `docs/superpowers/specs/` — new sibling specs or spec stubs for the §12 follow-on items.

- [ ] **Step 1: Define success criteria.** A stub spec or TODO per follow-on capability listed in spec §12 step 9: continuous evidence-staleness watchers, tagline A/B generator, multi-lingual (Spanish) variant, slide-deck outline artifact, landing-page copy artifact, dedicated meta-agent orchestrator promotion.

- [ ] **Step 2: Author one short paragraph per capability** noting the motivation, likely scope, and which existing system surfaces it would build on. These are not full specs — they are placeholders so the next brainstorming session has structured entry points.

- [ ] **Step 3: Commit.**

```bash
git add docs/superpowers/specs/
git commit -m "docs(abrigo): follow-on capability stubs"
```

---

## Spec-Coverage Self-Check

Each spec section mapped to the task(s) that implement it:

- Spec §0 Glossary → no task (reference document)
- Spec §1 Context → no task (motivation)
- Spec §2 Goals → Phase 6 + Phase 7 validate every goal
- Spec §3 Non-goals → enforced by Phase 0 permissions + Phase 2 brand-agent prompt
- Spec §4.1 Positioning → Task 2.1 step 1(f, j) + Task 3.1 Brand Guardian template
- Spec §4.2 Two-tier field rule → Task 2.1 step 1(d) + Task 7.2 step 1
- Spec §4.3 Evidence grounding → Task 2.1 step 1(e) + Task 3.2 claim auditor template
- Spec §4.4 Protocol abstraction → Task 2.1 step 1(f) + Task 2.1 step 6 smoke test
- Spec §4.5 Dual narrative → enforced in Task 6 one-pager review
- Spec §4.6 Pilot-then-mission → enforced in Task 6 one-pager review
- Spec §5.1 Committed surface → Task 2.1 (brand-agent file) + Task 3.1, 3.2, 4.1, 5.1 (orchestrator-prompt files)
- Spec §5.2 Gitignored surface → Task 1.1 (tree) + Task 1.2 (README) + Task 1.3 (facts.yml)
- Spec §5.2.1 facts.yml schema → Task 1.3 + Task 2.1 step 1(b)
- Spec §5.3 Gitignore entry → Task 0.3
- Spec §6.1 Brand agent responsibilities → Task 2.1
- Spec §6.2 Background dispatch → Task 6.2, 7.3 (orchestrator dispatches background)
- Spec §6.3 Self-review prohibition → Task 2.1 step 1(i)
- Spec §6.4 Scope boundaries → Task 0.2 (runtime enforcement) + Task 2.1 step 1(g,h)
- Spec §7.1 Triad mapping → Task 3.1, 3.2
- Spec §7.2 Charters → Task 3.1, 3.2 + Task 0.1 step 5 charter-drift check
- Spec §7.2.1 Overlap tiebreakers → Task 3.1 step 1(g)
- Spec §7.3 Verdict vocabulary → Task 3.1 step 1(f) + Task 3.2 step 1(d-g)
- Spec §7.4 Lifecycle → Task 5.1 step 2 + Task 6.3 + Task 7.3
- Spec §7.5 Contradictions → Task 5.1 step 4
- Spec §7.6 Background execution → Task 6.2, 7.3
- Spec §8.1–§8.3 Evidence base / citation / failure modes → Task 2.1 step 1(e) + Task 3.2
- Spec §8.4 Staleness → Task 4.1 + Task 4.2 + Task 5.1 step 5 publish-check
- Spec §9.1 One-pager shape → Task 6.1
- Spec §9.2 Pitch shapes → follow-on (not in v1 Crecimiento-critical path)
- Spec §9.3 Application-form shape → Task 7.2
- Spec §9.4 Tagline shape → follow-on
- Spec §10 Invocation patterns → Task 5.1
- Spec §11 Open risks — §11.8–§11.11 → Task 2.1 (facts-snapshot), Task 2.1 (verbatim facts quoting), Task 1.3 (brand_name_qualifier field), Task 0.2 (external write-deny)
- Spec §12 Next steps → this plan IS the implementation of §12.1–§12.8; §12.9 → Task 8.2
- Spec §13 Sources of truth → Task 2.1 step 1(a) + Task 3.1 step 3 (templates cite correctly)
- Spec §14 Appendix A Permissions → Task 0.2
- Spec §15 Appendix B Un-archive → Task 0.1

Coverage is complete. No spec section is unimplemented. Artifacts in §9 that are not on the Crecimiento critical path (pitches, taglines) are queued under follow-on (Task 8.2).

---

## Placeholder Scan Result

Plan contains no TBD, TODO, XXX, or FIXME markers. All "pending" references in facts.yml (Task 1.3) are explicit design choices with accompanying citation-plan fields, not gaps. Task 4.2 uses the word "contrived" to describe a deliberate test fixture, not a gap.

---

## Type / Naming Consistency Check

- "Brand agent" (never "branding agent") used consistently after Rev 2 of the spec.
- "Claim Auditor" (never "Reality Checker" for the copy role) used consistently after spec Rev 2.
- "Orchestrator" defined as the founder's foreground session throughout; future meta-agent promotion is explicitly deferred.
- `v{N}.md` revision-stamp convention used consistently (never timestamp, never numeric-only).
- File paths use `contracts/` prefix for clarity even though the worktree root is `contracts/`; a future reviewer can always run `cd contracts/` and interpret the paths unambiguously.
