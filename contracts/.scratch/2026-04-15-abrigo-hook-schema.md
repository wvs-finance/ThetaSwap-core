# Claude Code Hook Schema Findings (Abrigo Task 0.2 Step 1)

**Date:** 2026-04-15

## Schema confirmed from existing user-level hooks

The user's existing `/home/jmsbpp/.claude/settings.json` registers hooks under the top-level `hooks` key, keyed by event name. Each entry is an array; each array element is an object with a `hooks` array whose elements are `{type: "command", command: "<shell-invocation>"}`.

Example (existing PostToolUse):
```
"hooks": {
  "PostToolUse": [
    {
      "hooks": [
        { "type": "command", "command": "node \"/home/jmsbpp/.claude/hooks/gsd-context-monitor.js\"" }
      ]
    }
  ]
}
```

Matcher field is supported (filters which tool names the hook intercepts). Omitting `matcher` matches all tools.

## Hook input schema (from `gsd-context-monitor.js`)

Hooks receive JSON on stdin. Documented fields (from the existing PostToolUse hook):
- `session_id` — session identifier.
- `cwd` — working directory at invocation.

Additional fields available for PreToolUse (probed by this hook, logged when seen):
- `tool_name` — the tool about to run (e.g., `Write`, `Edit`, `MultiEdit`).
- `tool_input` — the tool's input parameters, including `file_path` for Write/Edit.

Subagent identity (unconfirmed; probed by abrigo-scope-guard across multiple candidate field names):
- `subagent_name`
- `subagent_type`
- `agent_name`
- `agent_type`
- `subagent`
- `agent`

**Empirical approach:** `abrigo-scope-guard.js` probes all six candidates, uses the first non-empty value, and logs the full JSON when a subagent identity is detected. The first real dispatch through the hook will reveal which field Claude Code actually populates (if any). Until then, per-subagent scoping degrades gracefully to blast-radius-only enforcement.

## Exit codes

- `0` — allow the tool call, continue normally.
- `2` — deny the tool call; stderr is surfaced to the calling agent. Standard Claude Code convention per the reference docs.
- `1` — hook error; treat as allow to avoid false denials from bugs in the hook.

## Project-local hook registration

Project-local hook registration lives in `contracts/.claude/settings.json`. The Claude Code runtime substitutes `$CLAUDE_PROJECT_DIR` to the worktree root when executing the hook command. This keeps the hook registration portable across clones.

## Limitations accepted for v1

1. Per-subagent scoping requires the PreToolUse hook JSON to surface subagent identity. If Claude Code does not surface it, the hook falls back to blast-radius-only enforcement. This is not a regression from the pre-hook state; it's a safety net that catches more than session-level permissions alone.

2. The hook does not distinguish between "brand agent drafting a revision" and "brand agent accidentally writing to src/". It only sees tool name, target path, and whatever subagent identity fields are available. More contextual scoping (e.g., read-only mode when the agent has completed drafting) would require a richer state machine than a stateless PreToolUse hook.

3. The hook log at `contracts/.scratch/abrigo-hook-decisions.log` is gitignored (by `.scratch/` precedent in project conventions if gitignored, else by explicit `.log` pattern). Founder reviews this log periodically to refine the scope rules if denials are overbroad or permissions too loose.
