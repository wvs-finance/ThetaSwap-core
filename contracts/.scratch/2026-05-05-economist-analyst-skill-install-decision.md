---
artifact_kind: ea_skill_install_adjudication_memo
emit_timestamp_utc: 2026-05-05
parent_plan_pin: contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md (v1.1, sha 6da9cce597abb7ed9da2a8f82700f502c04a0ba25d315d05c3085f7ebfe1f86b)
authority: feedback_pathological_halt_anti_fishing_checkpoint (≥3 pivot options enumerated; user adjudicates) + global CLAUDE.md MCP rule (verify repo via docker/github MCP first; prioritize docker MCP install; if docker unavailable, INFORM USER before proceeding)
trigger: Phase 0 Task 0.2 dispatch; SPM D4 v1.0 BLOCK closure required explicit pre-Phase-2.5 install-gate adjudication (was soft pre-flight in v1.0)
---

# Economist Analyst skill installation decision — Phase 0 Task 0.2

## §1. Why this memo exists

Per Phase 0 Task 0.2 Step 3 of plan v1.1, the dev-AI iteration's Phase 2.5 (post-Analytics-Reporter-notebook-trio multi-school interpretation) requires the **Economist Analyst Claude Code skill** (`rysweet/amplihack` repo) be invoked OR its framework be applied manually. Per global CLAUDE.md MCP rule + 2026-05-04 user adjudication (Option F: research capabilities only), the install method requires explicit user adjudication BEFORE Phase 2.5 dispatch — left as soft pre-flight in plan v1.0, this memo executes the explicit gate per SPM D4 v1.0 closure.

## §2. Repo + capabilities verification

Per Phase 0 Task 0.2 Step 1:

- **Repo verified**: `https://github.com/rysweet/amplihack` (verified via `mcp__github__get_file_contents` 2026-05-04 in earlier session; full README read; 16 stars; framework includes 6 schools — Classical / Keynesian / Austrian / Behavioral / Monetarist / Neoclassical Synthesis).
- **Skill marketplace entry**: `https://mcpmarket.com/es/tools/skills/economist-analyst-1` (verified via Playwright 2026-05-04; install command shown: `npx skillfish add rysweet/amplihack economist-analyst`).
- **Synthesis memo**: `contracts/.scratch/2026-05-04-economist-analyst-integration-synthesis.md` (committed 2026-05-04 at sha `56aa476e5`; §3 four-touchpoint framework + §3.bis pipeline integration with DE → AR → Economist Analyst → /structural-econometrics).

## §3. Install paths enumerated (3 options)

### Option (i) — Docker MCP install (PRIORITIZED per global CLAUDE.md rule)

**Command**: would require docker MCP server (`mcp__docker__*` tools) to be loaded in this Claude Code session.

**Verified availability**: docker MCP is **NOT loaded** in this environment (verified 2026-05-04 via `ToolSearch` query "docker mcp" — no `mcp__docker__*` tools returned). Per global CLAUDE.md rule: *"You MUST always prioritize installations methods with docker MCP. If that method is not available. Inform the user before proceeding."* — this is the user-information step.

**Status**: **CURRENTLY UNAVAILABLE.** The global rule prioritizes docker MCP but operationally we cannot use it without the docker MCP server loaded into Claude Code's tool inventory.

**Pros**: highest-discipline install per global rule; reproducible across sessions; clean uninstall path.

**Cons**: blocked on docker MCP availability; no concrete path to install in this environment.

### Option (ii) — GitHub clone + Skill.Fish install

**Command**: `npx skillfish add rysweet/amplihack economist-analyst` (per mcpmarket entry).

**Alternative**: `uvx --from git+https://github.com/rysweet/amplihack amplihack claude` (per `rysweet/amplihack` README; runs the full amplihack framework with the Economist Analyst skill auto-loaded).

**Pros**: available now (no missing prerequisites); skill loads in Claude Code as native skill; installed-skill version is more capable than manual application.

**Cons**: introduces external dependency (Skill.Fish package manager OR full amplihack runtime) that may have own install pre-requisites (Python 3.11+, Node.js 18+, uv per amplihack README); needs uninstall plan for cleanup; does NOT satisfy global CLAUDE.md "prioritize docker MCP" rule (this is the documented fallback path).

### Option (iii) — Skill-not-installed; orchestrator applies framework manually (CURRENT default per Option F)

**Command**: none (orchestrator applies the synthesis-memo §3 four-touchpoint framework verbatim during Phase 2.5 Tasks 2.5.1-2.5.4).

**Pros**: zero install dependency; no uninstall needed; aligns with current Option F user adjudication 2026-05-04; saves 0.5-1 day of MCP discovery / install / verify per SPM D1 timeline analysis; framework content is identical to skill output (synthesis memo §3 is the same source the skill itself reads).

**Cons**: orchestrator-applied framework lacks the skill's auto-invocation context-detection (orchestrator must manually invoke per touchpoint); slightly less consistent across sessions if orchestrator instance changes (but synthesis memo §3 is sha-pinned for verbatim citation).

## §4. Recommendation

**Option (iii) — skill-not-installed manual-framework-application** is the recommended default. Rationale:

1. Aligns with current 2026-05-04 user adjudication (Option F: research capabilities only)
2. Zero install dependency; saves 0.5-1 day of MCP-discovery time per SPM D1 timeline
3. Synthesis memo §3 four-touchpoint framework is sha-pinned for verbatim citation; orchestrator-applied output is reproducible
4. Phase 2.5 Tasks 2.5.1-2.5.4 are designed (per SPM D9 closure) for either skill-invoked OR manual-framework-application paths — switching paths later requires only Doc-Verify trailer change (`orchestrator-applied-EA-framework` vs `EA-skill-invoked`)
5. If user later changes mind (e.g., wants installed-skill version for future iterations beyond dev-AI), Option (ii) is still available — the install can happen at the start of a future iteration's Phase 2.5

## §5. User adjudication — pick one

**Pick (i)** — Docker MCP install. **Status: CURRENTLY UNAVAILABLE** in this environment per §3. If user picks (i), orchestrator HALTs Phase 0 Task 0.2 pending docker MCP server loading; this is a HALT-and-surface per `feedback_pathological_halt_anti_fishing_checkpoint`.

**Pick (ii)** — GitHub clone + Skill.Fish install (`npx skillfish add rysweet/amplihack economist-analyst`). Orchestrator runs install command in Phase 0 Task 0.2 Step 4 sub-phase; verifies skill loads in Claude Code; pins `ea_install_path_pin: github_skillfish` in plan v1.1.1 frontmatter.

**Pick (iii)** — Skill-not-installed; manual-framework-application via synthesis memo §3 (RECOMMENDED). Orchestrator pins `ea_install_path_pin: option_f_manual_framework` in plan v1.1.1 frontmatter; Phase 2.5 Tasks 2.5.1-2.5.4 invoke synthesis memo §3 verbatim during execution; Doc-Verify trailer at Task 2.5.4 commit reads `orchestrator-applied-EA-framework`.

## §6. Post-pick action

After user picks:
1. Orchestrator updates plan frontmatter with `ea_install_path_pin: <user_pick>` (creates plan v1.1.1 micro-edit; single-line frontmatter change; no full re-verify needed).
2. If pick (ii): orchestrator runs the install command in a follow-up commit; verifies skill loads; documents in this memo §7 install-execution log.
3. If pick (iii): orchestrator confirms synthesis memo §3 is sha-pinned and readable; documents in this memo §7 manual-framework-confirmation log.
4. Phase 0 Task 0.2 marked complete; Phase 1 dispatch unblocked.

## §7. Install-execution log (filled post-pick)

**User pick 2026-05-05**: Option (iii) — Skill-not-installed; orchestrator applies framework manually via synthesis memo §3 four-touchpoint framework verbatim.

**Adjudication trail**:
1. User initially picked (i) Docker MCP install.
2. Orchestrator surfaced HALT-and-surface: docker MCP unavailable in this environment (no `mcp__docker__*` tools loaded; verified 2026-05-04).
3. User picked (i.b) — invoke update-config skill to author docker MCP entry.
4. Orchestrator surfaced category clarification: Economist Analyst is a Claude Code SKILL (not MCP server); Docker MCP Gateway fronts MCP servers, doesn't install skills. Three sub-options enumerated (α full Docker MCP setup ~30-60 min / β downgrade to (ii)-or-(iii) / γ defer both).
5. User picked β-pivot 2026-05-05.
6. Per memo §4 recommendation, β-pivot defaults to (iii) skill-not-installed-manual-framework-application unless user explicitly picks (ii).

**Confirmed pick: (iii)**. Orchestrator pins `ea_install_path_pin: option_iii_manual_framework_application` in plan v1.1 frontmatter (v1.1 → v1.1.1 micro-edit; single-line frontmatter change). Phase 2.5 Tasks 2.5.1-2.5.4 invoke synthesis memo `contracts/.scratch/2026-05-04-economist-analyst-integration-synthesis.md` §3 four-touchpoint framework verbatim during execution. Doc-Verify trailer at Task 2.5.4 commit reads `orchestrator-applied-EA-framework`.

**Docker MCP Gateway infrastructure**: deferred to a separate future task when an actual MCP server is needed (not for the Economist Analyst skill, which has its own install path). Environment is ready (Docker 29.2.1 + Go 1.25.7); install plan documented in this memo §6 + the Docker MCP Gateway README at `https://github.com/docker/mcp-gateway`.

End of EA skill installation adjudication memo.
