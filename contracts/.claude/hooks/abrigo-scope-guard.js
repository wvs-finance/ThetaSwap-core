#!/usr/bin/env node
// Abrigo scope-guard — PreToolUse hook.
//
// Purpose: enforce the write-scope boundaries defined in
// docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md
// §14.1 Appendix A at runtime, independently of prompt discipline.
//
// Two layers of denial:
//   (a) Blast-radius (always enforced, subagent-agnostic): deny writes to
//       protected paths regardless of who tried. Redundant with session-level
//       permissions.deny but harmless; catches bugs in session settings.
//   (b) Per-subagent scoping (enforced when subagent identity is available in
//       the hook JSON): restrict brand agent to .branding/, reviewer agents
//       to .scratch/ and .branding/**/reviews/. Graceful fallback when
//       subagent identity is not surfaced: layer (a) still runs.
//
// Exit codes:
//   0 — allow the tool call
//   2 — deny the tool call; stderr is shown to the user / agent
//   1 — hook error (rare; treat as allow to avoid false denials from bugs)
//
// Every decision is appended to contracts/.scratch/abrigo-hook-decisions.log
// for debugging. The log is gitignored via contracts/.gitignore.

const fs = require('fs');
const path = require('path');

// 3-second stdin-close safety valve. If stdin never closes, exit 0 (allow).
let input = '';
const stdinTimeout = setTimeout(() => process.exit(0), 3000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => (input += chunk));
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  let data;
  try {
    data = JSON.parse(input);
  } catch (e) {
    // Malformed input — allow rather than block on bug.
    process.exit(0);
  }

  const toolName = data.tool_name || '';
  const toolInput = data.tool_input || {};
  const cwd = data.cwd || process.cwd();

  // Only gate write-class tools.
  const writeTools = new Set(['Write', 'Edit', 'MultiEdit', 'NotebookEdit']);
  if (!writeTools.has(toolName)) {
    log(cwd, { decision: 'allow', reason: 'non-write tool', toolName });
    process.exit(0);
  }

  // Extract target path. Schema varies slightly by tool.
  let targetPath = toolInput.file_path || toolInput.notebook_path || '';
  if (!targetPath) {
    log(cwd, { decision: 'allow', reason: 'no target path detected', toolName, toolInput });
    process.exit(0);
  }
  targetPath = path.resolve(cwd, targetPath);

  // Attempt to identify the active subagent. Fields to probe (schema may
  // change across Claude Code versions):
  const subagentCandidates = [
    data.subagent_name,
    data.subagent_type,
    data.agent_name,
    data.agent_type,
    data.subagent,
    data.agent,
  ].filter(Boolean);
  const subagent = subagentCandidates[0] || null;

  // Layer (a): blast-radius denials, always enforced.
  const blastRadiusDenyPatterns = [
    /\/src\//,
    /\/test\//,
    /\/script\//,
    /\/lib\//,
    /\/docs\/superpowers\/specs\//,
    /\/docs\/superpowers\/plans\//,
    /^\/home\/jmsbpp\/apps\/liq-soldk-dev\//,
    /^\/home\/jmsbpp\/\.claude\//,
  ];
  for (const pat of blastRadiusDenyPatterns) {
    if (pat.test(targetPath)) {
      log(cwd, {
        decision: 'deny',
        layer: 'blast-radius',
        reason: `target matches protected pattern ${pat.source}`,
        toolName,
        targetPath,
        subagent,
      });
      process.stderr.write(
        `[abrigo-scope-guard] BLOCKED: ${toolName} on ${targetPath} — path matches blast-radius deny pattern ${pat.source}. ` +
          `Spec §14 Appendix A denies writes to src/, test/, script/, lib/, superpowers/specs|plans/, external evidence base, and ~/.claude/ ` +
          `regardless of active subagent.\n`
      );
      process.exit(2);
    }
  }

  // Layer (b): per-subagent scope. Only enforced if subagent identity is known.
  if (subagent) {
    const brandingRoot = path.resolve(cwd, 'contracts/.branding');
    const scratchRoot = path.resolve(cwd, 'contracts/.scratch');

    const isBrandAgent = /abrigo-brand-agent/i.test(subagent);
    const isReviewerSeat = /brand-guardian|executive-summary-generator|content-creator|proposal-strategist|cultural-intelligence-strategist|testing-reality-checker/i.test(
      subagent
    );

    if (isBrandAgent) {
      if (!targetPath.startsWith(brandingRoot)) {
        log(cwd, {
          decision: 'deny',
          layer: 'per-subagent',
          reason: 'brand agent writing outside .branding/',
          toolName,
          targetPath,
          subagent,
        });
        process.stderr.write(
          `[abrigo-scope-guard] BLOCKED: subagent ${subagent} attempted to write to ${targetPath}. ` +
            `The brand agent may only write under contracts/.branding/.\n`
        );
        process.exit(2);
      }
    } else if (isReviewerSeat) {
      const inScratch = targetPath.startsWith(scratchRoot);
      const inReviews = targetPath.startsWith(brandingRoot) && /\/reviews\//.test(targetPath);
      if (!inScratch && !inReviews) {
        log(cwd, {
          decision: 'deny',
          layer: 'per-subagent',
          reason: 'reviewer writing outside .scratch/ and .branding/**/reviews/',
          toolName,
          targetPath,
          subagent,
        });
        process.stderr.write(
          `[abrigo-scope-guard] BLOCKED: reviewer ${subagent} attempted to write to ${targetPath}. ` +
            `Reviewers may only write to contracts/.scratch/ or contracts/.branding/**/reviews/.\n`
        );
        process.exit(2);
      }
    }
    // Other subagents: no per-subagent scoping; blast-radius already enforced.
  }

  log(cwd, {
    decision: 'allow',
    layer: subagent ? 'per-subagent' : 'blast-radius',
    toolName,
    targetPath,
    subagent,
  });
  process.exit(0);
});

function log(cwd, entry) {
  try {
    const logDir = path.join(cwd, 'contracts/.scratch');
    if (!fs.existsSync(logDir)) return;
    const logPath = path.join(logDir, 'abrigo-hook-decisions.log');
    const timestamp = new Date().toISOString();
    fs.appendFileSync(logPath, JSON.stringify({ timestamp, ...entry }) + '\n');
  } catch (e) {
    // Never fail the hook on logging errors.
  }
}
