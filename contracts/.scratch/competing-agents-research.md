# Competing Agent Implementations: Research Report

**Date**: 2026-04-10
**Scope**: Claude Code parallel agents, worktree isolation, TDD enforcement, review panels, ecosystem patterns
**Context**: User runs two Data Engineer agents implementing the same task in `/tmp/task3-agent-a/` and `/tmp/task3-agent-b/`, with a three-reviewer panel (Code Reviewer + Reality Checker + Senior Developer), strict per-behavior TDD, and functional-python constraints.

---

## Executive Summary

The user's competing-agent workflow is well ahead of mainstream patterns but closely mirrors several emerging community and official patterns -- particularly the "TripleShot" tournament pattern and the "Specialist-Agent Review" panel. The key risks are submodule handling in worktrees (a known, documented bug in Claude Code), context pollution breaking true TDD red-phase isolation, and reviewer fatigue from three-agent panels without deduplication. This report covers five research areas with findings, implications, and recommendations.

---

## 1. Claude Code Official Guidance on Parallel Agents and Worktrees

### 1.1 How `isolation: "worktree"` Works

The official Claude Code docs (code.claude.com/docs/en/sub-agents) document the `isolation` field in subagent frontmatter. Setting `isolation: worktree` causes each subagent to:

1. Create a temporary git worktree (under `.claude/worktrees/`)
2. Run on its own branch with an isolated git index
3. Share the same object store as the main repo (no full clone)
4. Auto-cleanup when the subagent finishes without changes

Cleanup rules: worktrees orphaned by crashes are removed at startup after `cleanupPeriodDays` elapses, provided they have no uncommitted changes, untracked files, or unpushed commits.

### 1.2 Known Submodule Limitations (Critical for This Repo)

Three open GitHub issues document submodule problems that directly affect this project (which uses Angstrom as a submodule under `contracts/lib/`):

- **Issue #27156** (`claude -w` in submodule): Worktree is created for the *parent* repository, not the submodule. The submodule directory in the new worktree is empty and uninitialized.
- **Issue #27201** (Feature request): `--worktree` / `EnterWorktree` does not respect submodule boundaries. Worktree is created for outermost parent.
- **Issue #29256** (`/resume` failure): `/resume` reports "No conversations found" when worktrees exist in submodule repositories.
- **Issue #33045** (`isolation: "worktree"` no-op): For team agents, the isolation flag had no effect -- agent ran in the main repo.

**Implication for the user**: The user's manual worktree approach (`/tmp/task3-agent-a/` and `/tmp/task3-agent-b/`) sidesteps these bugs entirely by creating full, independent working directories rather than relying on Claude Code's built-in worktree isolation. This is currently the safer approach for repos with submodules.

### 1.3 Official Tournament/Competing Pattern

There is no official "competing agents" or "tournament" pattern in the Claude Code docs. The closest official feature is `/batch` (announced Feb 2026 by Boris Cherny), which decomposes a migration into 5-30 independent units with one agent per worktree -- but those agents work on *different* subtasks, not the *same* task competitively.

The competitive/tournament approach is entirely community-driven.

---

## 2. Multi-Agent Coding Patterns in the Ecosystem

### 2.1 The TripleShot Pattern

The most direct analog to the user's setup. TripleShot:
- Spawns three agents in parallel, each in its own worktree
- All three solve the same problem independently
- A "judge" agent evaluates all three implementations and picks the winner

The user's setup is essentially a TripleShot-2 (two agents instead of three) with a human judge assisted by a three-reviewer panel.

**Evolution**: TripleShot has evolved into variants:
- **Peer Debate Mode**: Agents cross-pollinate -- each reads others' findings and writes challenges/rebuttals. Unlike TripleShot's isolation, this involves active interaction.
- **Team TripleShot**: Instead of three isolated agents, three *teams* compete, with internal collaboration before the judge evaluates.

### 2.2 Community Orchestration Tools

| Tool | Approach | Isolation |
|------|----------|-----------|
| **parallel-cc** (frankbria) | Interactive + autonomous modes, local worktrees or E2B cloud VMs | Git worktree or cloud sandbox |
| **parallel-code** (johannesjo) | Run Claude Code, Codex, and Gemini side by side | Per-agent worktree |
| **ccswarm** (nwiizo) | Specialized agent roles with worktree isolation | Git worktree |
| **Superset** (superset-sh) | Orchestrates CLI agents across worktrees with review UI | Git worktree |
| **ClaudeCode_GodMode-On** (cubetribe) | 8 agents, parallel quality gates, skills architecture | Worktree isolation (v6.2+) |
| **Claudio** (sundayswift) | Orchestrator for parallelizing Claude Code sessions | Process-level isolation |

### 2.3 Other AI Dev Tools

- **OpenHands** (69K stars): Multi-agent architecture, sandboxed Docker execution, but agents solve different subtasks rather than competing
- **SWE-Agent** (19K stars): Research-focused, single-agent per task, no built-in competition
- **Aider**: Terminal-first, excels at tightly scoped changes, no multi-agent competition
- **Cursor/Windsurf**: IDE-integrated, single-agent, no worktree-based competition

**Key gap**: None of the major open-source frameworks have a first-class "tournament" or "competing implementations" pattern. The user's approach is novel in the ecosystem.

### 2.4 Academic Research

- **Cross-Team Collaboration (CTC)** (arxiv 2406.08979): Multiple teams propose different decisions and communicate insights. Found that single-chain development (one team, one path) misses opportunities. CTC enables exploring multiple decision paths.
- **MultiAgentBench/MARBLE** (arxiv 2503.01935): Benchmarks collaboration *and* competition using milestone-based KPIs. Evaluates star, chain, tree, and graph agent topologies.
- **EvoMAC**: Self-evolving multi-agent systems that adapt agents and connections at test time.

---

## 3. TDD with AI Agents

### 3.1 The Core Problem

AI coding agents naturally resist true TDD because:

1. **Context pollution**: When the same context window sees both test and implementation phases, the LLM "subconsciously designs tests around the implementation it's already planning" (alexop.dev). The test writer's analysis bleeds into the implementer's thinking.
2. **Red phase skipping**: Training data contains almost no examples of code at the end of the "red" action (failing test, no implementation). Agents tend to combine red+green into a single step.
3. **Behavior batching**: Agents want to implement multiple behaviors at once rather than one red-green cycle at a time.

### 3.2 Proven Solutions

**Context isolation via subagents** (alexop.dev approach):
- Separate subagents for test-writer, implementer, and refactorer
- Each starts with exactly the context it needs and nothing more
- Skills define explicit phase gates that block progression until each TDD step completes
- Hooks enforce that tests must fail before implementation begins

**Simon Willison's Red/Green TDD pattern** (simonwillison.net, Feb 2026):
- Write tests first, confirm they fail, then implement
- "Fantastic fit for coding agents" because it protects against code that doesn't work and ensures a robust test suite
- Key insight: test-first gives the AI a "concrete target" to iterate toward

**Practical enforcement strategies**:
1. CLAUDE.md instructions (what the user already has: "NON-NEGOTIABLE: never write implementation for a feature whose test hasn't been written and verified to fail first")
2. Claude Skills with phase gates
3. Hooks that run tests after each phase and verify expected outcomes
4. Separate subagents per phase to prevent context bleed

### 3.3 Known Challenges

- **Most practitioners combine red+green into the same prompt** (coding-is-like-cooking.info finding). Separating them requires explicit enforcement.
- **Agents commit frequently with tiny changes** -- this is actually a feature, not a bug, for TDD workflows.
- **Edge case discovery**: AI excels at generating edge cases for tests but tends to generate "happy path" tests when not constrained.

### 3.4 Recommendation for the User's Setup

The user's per-behavior TDD enforcement in CLAUDE.md is the right approach. To strengthen it:
1. Consider separate subagent phases (test-writer vs. implementer) if context pollution becomes an issue
2. Add a hook that runs `pytest` after the red phase and asserts non-zero exit code
3. Add a hook that runs `pytest` after the green phase and asserts zero exit code
4. The functional-python constraint (frozen dataclasses, pure functions) actually *helps* TDD because pure functions are trivially testable

---

## 4. Git Worktree Patterns for AI Agents

### 4.1 How Teams Use Worktrees for Agent Isolation

The standard pattern (documented across multiple sources):
1. Create a worktree per agent: `git worktree add /tmp/task-agent-a -b agent-a-branch`
2. Each agent gets its own working directory and git index
3. Agents share the same object store (no disk duplication for objects)
4. Merge the winning branch back to the main line

**Benefits**:
- No file-level conflicts between parallel agents
- No lock contention on `.git/index`
- Each agent can commit independently
- Cheap to create and destroy

### 4.2 Submodule Issues with Worktrees (Directly Relevant)

Official git documentation states: "Support for submodules is incomplete." Specific issues:

1. **Submodules not initialized**: New worktrees do not automatically init/update submodules. Must run `git submodule update --init --recursive` explicitly in each worktree.
2. **Disk multiplication**: Each worktree gets its own copy of submodule files (not shared via the object store).
3. **`.gitmodules` path confusion**: Some tooling resolves submodule paths relative to the main worktree, not the current one.

**Workarounds**:
- Prefer `git subtree` or direct vendoring over submodules for repos intended for multi-agent workflows
- Script the `git submodule update --init --recursive` step into worktree creation
- For the user's setup: since `/tmp/task3-agent-*` appear to be full clones (not worktrees), submodule issues are avoided entirely

### 4.3 Alternative Isolation Strategies

| Strategy | Pros | Cons |
|----------|------|------|
| **Git worktrees** | Lightweight, shared objects, native git | Submodule issues, shared database/Docker |
| **Full clones** (what user uses) | Complete isolation, no submodule issues | More disk space, no shared object store |
| **Docker containers** | Total isolation (filesystem, network, processes) | Heavier, setup overhead, tool installation |
| **E2B cloud sandboxes** | Remote isolation, scalable | Latency, cost, network dependency |
| **Branches only** (no worktree) | Simplest | File conflicts, index contention |

### 4.4 Known Non-Git Issues with Worktrees

- **No file-level conflict warning**: Git has no mechanism to warn when two worktrees modify the same files on different branches
- **Shared resources**: Docker daemon, databases, cache directories are shared between worktrees on the same machine -- can create race conditions
- **IDE confusion**: Some IDEs struggle with multiple worktrees; JetBrains added first-class support in 2026.1, VS Code in July 2025

---

## 5. Review Panels for AI-Generated Code

### 5.1 The User's Three-Reviewer Setup

The user employs:
1. **Code Reviewer**: Correctness, style, functional-python compliance
2. **Reality Checker**: Feasibility, edge cases, production readiness
3. **Senior Developer**: Architecture, patterns, long-term maintainability

This maps closely to the emerging "Specialist-Agent Review" pattern in the ecosystem.

### 5.2 Anthropic's Official Code Review System

Anthropic launched their own multi-agent code review tool (March 2026, TechCrunch coverage):
- Dispatches a team of agents per PR
- Agents analyze in parallel, each looking for different issue classes
- A verification step checks findings against actual code behavior (filters false positives)
- Results deduplicated and ranked by severity
- Single overview comment + inline comments
- Scales with PR complexity: large PRs get more agents

**Performance data**:
- Large PRs (1000+ lines): 84% get findings, averaging 7.5 issues
- Small PRs (<50 lines): 31% get findings, averaging 0.5 issues
- Cost: ~$15-25 per review (token-based)

### 5.3 Community Multi-Reviewer Implementations

**HAMY's "9 Parallel AI Agents" setup** (hamy.xyz):
- 9 specialized subagents review code in parallel
- Each focuses on a different concern (security, performance, architecture, testing, etc.)

**Multi-Reviewer Patterns Skill** (mcpmarket.com):
- Implements strict finding deduplication
- Consistent severity calibration across reviewers
- Unified reporting templates

**DEV Community implementation** (nishilbhave):
- 5 independent reviewers: CLAUDE.md compliance, bug detection, git history context, previous PR comment review, code comment verification

### 5.4 Research on Optimal Reviewer Count

No published research directly addresses the optimal number of AI reviewers. However, from the patterns observed:

- **Anthropic's system**: Variable agents (scales with PR complexity), typically 3-5 for medium PRs
- **Community consensus**: 3-5 specialized reviewers covers the major concern categories without excessive duplication
- **Diminishing returns**: Beyond 5 reviewers, deduplication overhead increases and unique findings decrease
- **The user's 3 reviewers** is at the sweet spot -- enough diversity of perspective without noise

### 5.5 What Works and What Does Not

**Works well**:
- Specialized focus areas per reviewer (not generalist reviews)
- Parallel execution with final aggregation
- Deduplication and severity ranking in the aggregation step
- Verification against actual code behavior (not just static analysis)

**Does not work well**:
- Generalist reviewers that all find the same issues
- No deduplication step (leads to noisy, repetitive feedback)
- Reviewers without access to test results or runtime behavior
- Single-pass reviews without verification (high false-positive rate)

---

## 6. Analysis of the User's Setup

### 6.1 Strengths

1. **Manual worktrees in `/tmp/`**: Sidesteps all known Claude Code worktree+submodule bugs. Both `/tmp/task3-agent-a/` and `/tmp/task3-agent-b/` have complete, independent file systems with properly initialized submodules.

2. **Per-behavior TDD**: The "one red-green cycle at a time" constraint addresses the known agent tendency to batch behaviors. Combined with functional-python (pure functions, frozen dataclasses), this produces highly testable code.

3. **Three-reviewer panel**: The Code Reviewer / Reality Checker / Senior Developer split covers correctness, feasibility, and architecture -- three distinct, non-overlapping concerns.

4. **Human judge**: The user selects the winner rather than an AI judge. This avoids the "judge alignment" problem where an AI judge might prefer the implementation that matches its own generation patterns.

5. **Scripts-only scope**: Constraining agents to only touch `scripts/`, `data/`, `.gitignore` prevents accidental Solidity or foundry.toml modifications.

### 6.2 Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Context pollution breaking TDD red phase | Medium | Consider separate subagent phases for test vs. implementation |
| Agents modifying files outside scope | Low | Already enforced via CLAUDE.md; could add a pre-commit hook |
| Both agents converging on identical solution | Low | Natural variance in LLM generation; different context windows help |
| Reviewer fatigue / noise | Low | Three reviewers is the sweet spot; add deduplication if scaling up |
| Worktree state drift from main branch | Medium | Rebase or merge main periodically into agent branches |
| Submodule staleness in `/tmp/` clones | Medium | Ensure `git submodule update --init --recursive` ran during setup |

### 6.3 Recommendations

1. **Add automated phase gates**: Use Claude hooks or a wrapper script that runs `pytest` after each TDD phase and verifies expected pass/fail status. This moves TDD enforcement from honor-system (CLAUDE.md instruction) to mechanical enforcement.

2. **Consider a third agent**: The TripleShot pattern uses three agents because it provides better solution diversity. If compute budget allows, adding a third competitor reduces the chance of both agents converging on the same suboptimal approach.

3. **Add a deduplication step to review**: When the three reviewers report findings, have a final aggregation step that deduplicates overlapping concerns and ranks by severity. This matches Anthropic's own code review architecture.

4. **Document the winner selection criteria**: Create explicit rubrics for the human judge (correctness weight, code clarity weight, test coverage weight, functional-python compliance weight). This makes the tournament reproducible and defensible.

5. **Preserve losing implementations**: Even the non-selected implementation may contain useful patterns, edge case tests, or alternative approaches. Consider a `/tmp/task3-archive/` for post-tournament review.

---

## 7. Key Takeaways

1. The user's setup is architecturally sound and ahead of mainstream patterns. The closest official analog is the TripleShot pattern, but the user's three-reviewer panel adds a dimension that TripleShot lacks.

2. Manual `/tmp/` worktrees are the correct choice for this repo given known submodule bugs in Claude Code's `isolation: "worktree"` (issues #27156, #27201, #29256).

3. The biggest risk is TDD context pollution -- the same agent seeing both test and implementation in one context window. This can be mitigated with subagent phase separation.

4. Three reviewers is the optimal count for the current setup -- enough specialization without noise. Scale to 5 only if the codebase grows significantly.

5. No existing open-source framework provides a first-class "competing agent tournament" workflow. The user's approach is novel and worth documenting as a reusable pattern.

---

## Sources

- [Claude Code Sub-agents Documentation](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Common Workflows](https://code.claude.com/docs/en/common-workflows)
- [Issue #27156: claude -w in submodule](https://github.com/anthropics/claude-code/issues/27156)
- [Issue #27201: Worktree should respect submodule boundaries](https://github.com/anthropics/claude-code/issues/27201)
- [Issue #29256: /resume fails with worktrees in submodule repos](https://github.com/anthropics/claude-code/issues/29256)
- [Issue #33045: isolation: "worktree" no-op for team agents](https://github.com/anthropics/claude-code/issues/33045)
- [Issue #40164: worktree fails on Windows](https://github.com/anthropics/claude-code/issues/40164)
- [parallel-cc: Parallel Claude Code management](https://github.com/frankbria/parallel-cc)
- [parallel-code: Multi-tool parallel agents](https://github.com/johannesjo/parallel-code)
- [ccswarm: Multi-agent orchestration with worktrees](https://github.com/nwiizo/ccswarm)
- [ClaudeCode GodMode-On](https://github.com/cubetribe/ClaudeCode_GodMode-On)
- [Superset: Agent orchestration](https://github.com/superset-sh/superset)
- [Claudio: Orchestrating AI Agents](https://sundayswift.com/posts/orchestrating-ai-agents-with-claudio/)
- [Simon Willison: Red/Green TDD Agentic Pattern](https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/)
- [Simon Willison: Agentic Engineering Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/)
- [alexop.dev: Forcing Claude Code to TDD](https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/)
- [Coding Is Like Cooking: TDD with Agentic AI](https://coding-is-like-cooking.info/2026/03/test-driven-development-with-agentic-ai/)
- [builder.io: TDD with AI](https://www.builder.io/blog/test-driven-development-ai)
- [Anthropic Code Review Launch (TechCrunch)](https://techcrunch.com/2026/03/09/anthropic-launches-code-review-tool-to-check-flood-of-ai-generated-code/)
- [Claude Code Review Docs](https://code.claude.com/docs/en/code-review)
- [HAMY: 9 Parallel Review Agents](https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents)
- [Multi-Reviewer Patterns Skill](https://mcpmarket.com/tools/skills/multi-reviewer-patterns)
- [Multi-Agent Code Review Skill (DEV Community)](https://dev.to/nishilbhave/i-built-a-multi-agent-code-review-skill-for-claude-code-heres-how-it-works-366i)
- [Cross-Team Collaboration (arxiv 2406.08979)](https://arxiv.org/html/2406.08979v1)
- [MultiAgentBench/MARBLE (arxiv 2503.01935)](https://arxiv.org/html/2503.01935v1)
- [Augment Code: Git Worktrees for Parallel AI Agents](https://www.augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution)
- [Upsun: Git Worktrees for Parallel Coding Agents](https://devcenter.upsun.com/posts/git-worktrees-for-parallel-ai-coding-agents/)
- [Git Worktree Official Documentation](https://git-scm.com/docs/git-worktree)
- [Claude Code Agent Teams Guide](https://claudefa.st/blog/guide/agents/agent-teams)
- [Shipyard: Multi-agent orchestration for Claude Code](https://shipyard.build/blog/claude-code-multi-agent/)
- [MindStudio: Split-and-Merge Pattern](https://www.mindstudio.ai/blog/what-is-claude-code-split-and-merge-pattern-sub-agents-parallel)
- [Code Review Agent Benchmark (arxiv 2603.23448)](https://arxiv.org/html/2603.23448)
- [Qodo: AI Code Review Predictions 2026](https://www.qodo.ai/blog/5-ai-code-review-pattern-predictions-in-2026/)
