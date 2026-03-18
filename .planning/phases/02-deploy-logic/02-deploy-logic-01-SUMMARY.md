---
phase: 02-deploy-logic
plan: "01"
subsystem: d2p-deploy-strategies
tags: [rust, subprocess, forge, cast, tdd, serde, deployment]
dependency_graph:
  requires: [01-crate-foundation-01]
  provides: [primary-deploy-strategy, fallback-deploy-strategy]
  affects: [02-deploy-logic-02]
tech_stack:
  added: [serde with derive feature]
  patterns: [typed-subprocess-args, serde-json-structured-output, env-isolation]
key_files:
  created:
    - d2p/src/deploy/primary.rs
    - d2p/src/deploy/fallback.rs
  modified:
    - d2p/src/deploy/mod.rs
    - d2p/Cargo.toml
key_decisions:
  - "serde crate with derive feature added to Cargo.toml — serde_json alone insufficient for #[derive(serde::Deserialize)]"
  - "--constructor-args enforced last in forge create arg vec (Foundry issue #770, DEP-06)"
  - "--legacy absent from fallback path (DEP-03); cast send uses EIP-1559 by default"
  - "Actionable error message for missing artifact includes 'forge build' (Pitfall 5)"
  - "ETH_RPC_URL env_remove on both subprocess commands to prevent parent env shadowing --rpc-url"
metrics:
  duration: "144 seconds (~2 minutes)"
  completed_date: "2026-03-18"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 2
  tests_added: 10
  tests_total: 13
requirements: [DEP-01, DEP-02, DEP-03, DEP-06]
---

# Phase 02 Plan 01: Deploy Strategy Modules Summary

**One-liner:** forge create primary and cast send --create fallback modules with serde JSON parsing, arg-order enforcement, and 10 unit tests covering all correctness constraints.

## What Was Built

### primary.rs — forge create strategy

- `ForgeCreateJson` struct: deserializes `deployedTo` and `transactionHash` from `forge create --json` stdout (Foundry v1.5.1-stable verified shape).
- `build_args()`: arg vector with `--constructor-args` as the last two elements (DEP-06, Foundry issue #770). Includes `--broadcast`, `--legacy`, `--value`, `--json`.
- `run()`: spawns forge subprocess with `env_remove("ETH_RPC_URL")`, maps `NotFound` to `D2pError::ProcessNotFound`, non-zero exit to `D2pError::NonZeroExit`, parse failure to `D2pError::ParseFailure`.

### fallback.rs — cast send --create strategy

- `CastSendJson` struct: deserializes `contractAddress` and `transactionHash` from `cast send --create --json` stdout.
- `read_bytecode()`: reads `{project_dir}/out/{Name}.sol/{Name}.json` and extracts `.bytecode.object`. Returns actionable error containing "forge build" when artifact missing (Pitfall 5).
- `build_args()`: all flags before `--create` subcommand (Pitfall 2). No `--legacy` (DEP-03). Bytecode immediately after `--create`, then `constructor(address)`, then callback.
- `run()`: same error-mapping pattern as primary.

## Tests Added

| Test | File | Requirement Covered |
|------|------|---------------------|
| test_forge_args_order | primary.rs | DEP-06: --constructor-args last |
| test_forge_args_contains_legacy | primary.rs | DEP-01: --legacy present |
| test_forge_args_contains_broadcast | primary.rs | DEP-01: --broadcast present |
| test_forge_args_no_env_inheritance | primary.rs | Pitfall 6: ETH_RPC_URL not in args |
| test_parse_forge_json | primary.rs | serde rename: deployedTo, transactionHash |
| test_cast_args_no_legacy | fallback.rs | DEP-03: --legacy absent |
| test_cast_args_order | fallback.rs | DEP-02, Pitfall 2: flags before --create |
| test_parse_cast_json | fallback.rs | serde rename: contractAddress, transactionHash |
| test_read_bytecode_missing_artifact | fallback.rs | Pitfall 5: actionable error with "forge build" |
| test_read_bytecode_missing_field | fallback.rs | bytecode.object absent returns Err |

Full test suite: **13 tests pass** (10 new + 3 Phase 1).

## Commits

| Hash | Task | Description |
|------|------|-------------|
| 151f64f | Task 1 | feat(02-deploy-logic-01): primary.rs forge create module |
| 9523270 | Task 2 | feat(02-deploy-logic-01): fallback.rs cast send --create module |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added serde with derive feature to Cargo.toml**
- **Found during:** Task 1 — cargo compile failed
- **Issue:** `serde_json` was in Cargo.toml but `serde` itself was not. `#[derive(serde::Deserialize)]` requires the `serde` crate with `features = ["derive"]`. The RESEARCH.md noted Cargo.toml was complete for Phase 2, but this dependency was overlooked.
- **Fix:** Added `serde = { version = "1", features = ["derive"] }` to `[dependencies]` in `d2p/Cargo.toml`.
- **Files modified:** `d2p/Cargo.toml`
- **Commit:** 151f64f (included in Task 1 commit)

**2. [Rule 2 - Missing] Removed unused `anyhow::Context` import from primary.rs**
- **Found during:** Task 1 — compiler warning
- **Issue:** Plan specified `use anyhow::Context;` but `primary.rs` has no `.with_context()` calls (unlike `fallback.rs` which uses it in `read_bytecode`).
- **Fix:** Removed unused import from `primary.rs`.
- **Files modified:** `d2p/src/deploy/primary.rs`
- **Commit:** 151f64f

## Self-Check: PASSED

| Item | Status |
|------|--------|
| d2p/src/deploy/primary.rs | FOUND |
| d2p/src/deploy/fallback.rs | FOUND |
| SUMMARY.md | FOUND |
| commit 151f64f (Task 1) | FOUND |
| commit 9523270 (Task 2) | FOUND |
| cargo test — 13/13 pass | VERIFIED |
