---
phase: 02-deploy-logic
plan: "02"
subsystem: d2p-deploy-logic
tags: [rust, tdd, subprocess, foundry, receipt-verification, runner]
dependency_graph:
  requires: [02-01]
  provides: [Runner::deploy(), verify::verify(), check_prerequisites()]
  affects: [03-cli]
tech_stack:
  added: []
  patterns: [parse_receipt_status helper, TDD red-green, check_prerequisites loop]
key_files:
  created:
    - d2p/src/deploy/verify.rs
  modified:
    - d2p/src/deploy/mod.rs
decisions:
  - "parse_receipt_status() accepts only '0x1' — human string '1 (success)' from cast receipt positional field is explicitly rejected (Pitfall 3)"
  - "check_prerequisites() uses io::ErrorKind::NotFound on Command::new(tool).arg('--version') — no which crate needed"
  - "Runner::deploy() calls check_prerequisites() as first operation before any subprocess spawn"
  - "verify::verify() called after primary OR fallback path — receipt status checked before returning DeployOutput"
metrics:
  duration: "~3 minutes"
  completed: "2026-03-18T00:55:03Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 02 Plan 02: Deploy Logic — Runner + verify.rs Summary

**One-liner:** Receipt verification with cast receipt --json "0x1" check and Runner orchestrator wiring primary, fallback, and verify together.

## What Was Built

### verify.rs (new file)

`d2p/src/deploy/verify.rs` implements receipt verification as a two-function module:

- `fn parse_receipt_status(stdout: &[u8]) -> anyhow::Result<()>` — private helper that parses JSON bytes and matches `v["status"].as_str()` against `"0x1"` exclusively. Returns `Err` with "reverted" on `"0x0"`, and `Err` with "missing status" when the field is absent. The human-readable string `"1 (success)"` that `cast receipt <TXHASH> status` (positional form) emits is explicitly rejected — only the hex form from `--json` is valid.
- `pub fn verify(tx_hash: &str, rpc_url: &str) -> anyhow::Result<()>` — spawns `cast receipt --rpc-url <rpc_url> <tx_hash> --json`, checks exit code, then delegates to `parse_receipt_status`. Arg order matches RESEARCH.md Pattern 3.

### deploy/mod.rs (extended)

Three additions appended to the existing file without touching `DeployParams`, `DeployOutput`, or their tests:

1. `pub fn check_prerequisites() -> anyhow::Result<()>` — loops over `["forge", "cast"]`, spawns `<tool> --version`, returns actionable error `"{tool} not found on PATH — install Foundry: https://getfoundry.sh"` on `io::ErrorKind::NotFound` (DEP-04).

2. `pub struct Runner { params: DeployParams }` — private field; constructed via `Runner::new(params)`.

3. `impl Runner { pub fn deploy(&self) -> anyhow::Result<DeployOutput> }` — calls `check_prerequisites()` first, then `primary::run()`, falls back to `fallback::run()` with `eprintln!("[warn] forge create failed ({e}), retrying with cast send --create")`, then calls `verify::verify(&out.tx_hash, &self.params.rpc_url)?` before returning `DeployOutput`.

## Test Results

Full suite: **20 tests, 0 failed**

| Source | Tests | Count |
|--------|-------|-------|
| errors.rs | test_d2p_error_variants | 1 |
| deploy/mod.rs (Phase 1) | test_deploy_output_display, test_deploy_params_debug | 2 |
| deploy/primary.rs | test_forge_args_order, test_forge_args_contains_legacy, test_forge_args_contains_broadcast, test_forge_args_no_env_inheritance, test_parse_forge_json | 5 |
| deploy/fallback.rs | test_cast_args_no_legacy, test_cast_args_order, test_parse_cast_json, test_read_bytecode_missing_artifact, test_read_bytecode_missing_field | 5 |
| deploy/verify.rs (new) | test_verify_receipt_success, test_verify_receipt_reverted, test_verify_receipt_missing_status, test_verify_rejects_human_string | 4 |
| deploy/mod.rs (new) | test_check_prerequisites_missing_tool, test_check_prerequisites_bad_name, test_deploy_output_display_no_newline_suffix | 3 |

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Reject "1 (success)" explicitly | cast receipt positional field (non-JSON) returns human string; only --json "0x1" is machine-comparable (Pitfall 3, DEP-05) |
| No which crate | io::ErrorKind::NotFound from Command::new(tool).arg("--version") is deterministic and sufficient; avoids external dependency |
| check_prerequisites() as free function, not method | Callable before Runner construction; consistent with RESEARCH.md Pattern 4 |
| verify::verify() after primary AND fallback | DEP-05 is unconditional — both strategies require receipt confirmation |
| eprintln! fallback warning format | Matches must_haves truth: "forge create failed" + "cast send --create" in warning message |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] `d2p/src/deploy/verify.rs` — exists with `parse_receipt_status` and `pub fn verify`
- [x] `d2p/src/deploy/mod.rs` — contains `check_prerequisites`, `Runner`, `Runner::deploy()`
- [x] Task 1 commit: b514fe0
- [x] Task 2 commit: db025ed
- [x] `cargo test -- --include-ignored`: 20 passed, 0 failed
- [x] `grep -n "0x1" verify.rs` — shows exact comparison
- [x] `grep -n '"receipt"' verify.rs` — shows first cast arg
- [x] `grep -n "getfoundry.sh" mod.rs` — shows install URL in error
- [x] `grep -n "forge create failed" mod.rs` — shows fallback warning format string
- [x] `grep -n "verify::verify" mod.rs` — shows verify called in deploy()
- [x] `grep -n "check_prerequisites" mod.rs` — shows it is first call in deploy()
- [x] `cargo build` exits 0

## Self-Check: PASSED
