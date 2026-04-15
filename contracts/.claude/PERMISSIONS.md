# Abrigo Permissions Model

This directory's `settings.json` configures two layers of write-scope enforcement for the Abrigo branding workflow defined in `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` §14 Appendix A.

## Layer 1 — PreToolUse scope-guard hook (primary gate)

- **Registered in:** `settings.json` → `hooks.PreToolUse`.
- **Implementation:** `contracts/.claude/hooks/abrigo-scope-guard.js`.
- **Triggers on:** `Write`, `Edit`, `MultiEdit`, `NotebookEdit` tool calls.
- **Catches:**
  - Blast-radius denials: writes to `src/`, `test/`, `script/`, `lib/`, `docs/superpowers/specs/`, `docs/superpowers/plans/`, `/home/jmsbpp/apps/liq-soldk-dev/`, `/home/jmsbpp/.claude/` — always denied regardless of active subagent.
  - Per-subagent scoping (when subagent identity is surfaced in the hook JSON):
    - `abrigo-brand-agent`: may write only under `contracts/.branding/`.
    - Reviewer seats (`brand-guardian`, `executive-summary-generator`, `content-creator`, `proposal-strategist`, `cultural-intelligence-strategist`, `testing-reality-checker` when dispatched as Claim Auditor): may write only under `contracts/.scratch/` and `contracts/.branding/**/reviews/`.
- **Decision log:** `contracts/.scratch/abrigo-hook-decisions.log` (gitignored, rotated manually if large).
- **Graceful fallback:** if subagent identity is not surfaced by the Claude Code runtime, per-subagent rules are silently skipped; blast-radius denials still apply.
- **Exit codes:** `0` = allow, `2` = deny (stderr shown to agent), `1` = error (treated as allow to avoid false denials from hook bugs).

## Layer 2 — Session-level `permissions.deny`

- **Location:** `settings.json` → `permissions.deny`.
- **Catches:** writes to the external painkiller evidence base at `/home/jmsbpp/apps/liq-soldk-dev/**`. Redundant with Layer 1 blast-radius denial but enforced by the Claude Code runtime without touching the hook; survives hook bugs.
- **Scope:** applies to every session that opens this worktree, regardless of which subagent (if any) is active.
- **Intentionally narrow:** session-level denies do NOT block the founder's foreground session from editing `src/`, `test/`, `lib/`, etc., because the founder edits those files during normal engineering work. The hook denies them only when a subagent tries.

## Interaction

```
tool call issued
    │
    ▼
Claude Code runtime checks session `permissions.deny` ───▶ deny if match
    │
    ▼ (no match)
PreToolUse hook runs (`abrigo-scope-guard.js`)
    │
    ├── blast-radius pattern match? ───▶ exit 2 (deny)
    │
    ├── subagent identity known and path out-of-scope? ───▶ exit 2 (deny)
    │
    ▼
exit 0 (allow) ───▶ tool call proceeds
```

## Adding or removing a protected path

- **Blast-radius (applies to all agents):** edit `abrigo-scope-guard.js` → `blastRadiusDenyPatterns` array. Changes take effect at next session start.
- **Session-level (applies to foreground session too):** edit `settings.json` → `permissions.deny`. Takes effect at next session start.
- **Per-subagent scope:** edit the relevant subagent branch in `abrigo-scope-guard.js`.

## Debugging denials

1. Review the hook log: `tail -n 50 contracts/.scratch/abrigo-hook-decisions.log`.
2. Confirm whether the denial came from Layer 1 (hook, stderr includes `[abrigo-scope-guard] BLOCKED`) or Layer 2 (runtime, stderr includes Claude Code's generic permission message).
3. If Layer 1 denied a legitimate call: patch `abrigo-scope-guard.js`. If Layer 2 denied a legitimate call: patch `settings.json` → `permissions.deny`.

## Rollback

To disable Abrigo enforcement entirely (e.g., for an engineering session where the hook interferes):
1. Remove or rename `settings.json` → `hooks.PreToolUse` block.
2. Remove or rename `settings.json` → `permissions.deny` block.
3. Restart the Claude Code session. Re-enable by restoring the blocks.
