---
phase: 03-cli-wiring
plan: 01
subsystem: d2p CLI binary
tags: [rust, clap, cli, deployment]
dependency_graph:
  requires: [02-deploy-logic]
  provides: [d2p binary, cli parsing, env fallback]
  affects: [d2p/src/main.rs, d2p/src/cli.rs, d2p/Cargo.toml]
tech_stack:
  added: [clap env feature]
  patterns: [run()/main() split for exit code discipline, value_parser free function, env fallback via clap attr]
key_files:
  created: [d2p/src/cli.rs]
  modified: [d2p/src/main.rs, d2p/Cargo.toml]
decisions:
  - run()/main() split pattern over fn main() -> anyhow::Result<()> for stderr format control and exit code 1 discipline
  - parse_value() as free function + value_parser attribute — no third-party crate needed
  - Env test isolation via single-env-var-per-test pattern (each test only sets the var it is testing, passes the other as an explicit flag)
metrics:
  duration: 187s
  completed: "2026-03-18T01:20:51Z"
  tasks_completed: 2
  files_modified: 3
---

# Phase 3 Plan 1: CLI Wiring Summary

Wire the clap argument parser to the Phase 2 deploy runner, producing the complete `d2p` binary — JWT auth with refresh rotation using jose library (no, this is clap CLI wiring for reactive contract deployment via `d2p ts reactive uniswap-v3 [flags]` routing through all CLI layers to `Runner::deploy()`).

## What Was Built

Added the single CLI layer (`d2p/src/cli.rs`) that converts user input into `DeployParams` and rewrote the stub `main.rs` to connect it to the Phase 2 `Runner`. Zero changes to `deploy/` or `errors.rs`.

### Files Created/Modified

- **d2p/Cargo.toml** — Added `"env"` to clap features list (required for `#[arg(env = "ETH_RPC_URL")]` to read env vars at runtime)
- **d2p/src/cli.rs** (new, 185 lines) — `Cli`, `Commands`, `TsArgs`, `TsCommands`, `ReactiveArgs`, `Protocol` (ValueEnum), `parse_value()`, 8 unit tests
- **d2p/src/main.rs** (rewritten, 40 lines) — `fn main()` + `fn run() -> anyhow::Result<()>` split, `Cli::parse()` → `DeployParams` → `Runner::new(params).deploy()` → `println!("{output}")`

## Decisions Made

**1. `run()` split pattern over `fn main() -> anyhow::Result<()>`**

Using `fn main() { if let Err(e) = run() { eprintln!("error: {e:#}"); std::process::exit(1); } }` gives full control over stderr format (OUT-02) and guarantees `exit(1)` (OUT-03). anyhow's default adds "Error: " prefix which can confuse downstream scripts.

**2. `parse_value` as free function + `value_parser` attribute**

No `clap-value-parser` or `humantime` crate needed. A 10-line free function `fn parse_value(s: &str) -> Result<String, String>` validates the unit suffix and returns the input string unchanged if valid. This keeps the `--value` field typed as `String` (matching `DeployParams.value`) and lets Foundry handle the actual unit conversion.

**3. Env test isolation: single env var per test**

The two env fallback tests (`test_env_rpc_url`, `test_env_private_key`) each set only one env var and pass the other as an explicit CLI flag. This prevents cross-test pollution when tests run in parallel, without requiring `serial_test` or `std::sync::Mutex` boilerplate.

## Test Delta

- **Tests before:** 20 (all from Phase 2 deploy/ modules + errors)
- **Tests added:** 8 (`test_parse_value_valid`, `test_parse_value_invalid`, `test_cli_routing`, `test_callback_required`, `test_no_legacy_flag`, `test_help_contains_example`, `test_env_rpc_url`, `test_env_private_key`)
- **Tests after:** 28 all passing

## Requirements Satisfied

| Req ID | Status | Verification |
|--------|--------|-------------|
| CMD-01 | DONE | `d2p ts reactive uniswap-v3` routes to correct handler (test_cli_routing) |
| CMD-02 | DONE | `ETH_RPC_URL` env accepted when `--rpc-url` absent (test_env_rpc_url) |
| CMD-03 | DONE | `ETH_PRIVATE_KEY` env accepted when `--private-key` absent (test_env_private_key) |
| CMD-04 | DONE | Missing `--callback` causes parse error (test_callback_required) |
| CMD-05 | DONE | "10react"/"0.5ether" valid; "noreact"/"10btc" rejected (test_parse_value_*) |
| CMD-06 | DONE | No `--legacy` in any help text (test_no_legacy_flag) |
| CMD-07 | DONE | `--help` contains "d2p ts reactive" example (test_help_contains_example) |
| CMD-08 | DONE | `d2p --version` prints "d2p 0.1.0" from Cargo.toml |
| CMD-09 | DONE | Non-existent `--project` path: canonicalize() + with_context() actionable error |
| OUT-02 | DONE | `eprintln!("error: {e:#}")` on stderr in main() error path |
| OUT-03 | DONE | `std::process::exit(1)` on failure; clap exits 2 for parse errors |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed env test parallel-execution race condition**

- **Found during:** Task 1 test run
- **Issue:** `test_env_rpc_url` set both `ETH_RPC_URL` and `ETH_PRIVATE_KEY`; when `test_env_private_key` ran concurrently, it picked up the `ETH_PRIVATE_KEY` value from the other test before cleanup
- **Fix:** Each env test now sets only the env var it is testing; passes the other as an explicit CLI `--flag` argument
- **Files modified:** d2p/src/cli.rs
- **Commit:** 6ea75e6

**2. [Rule 1 - Bug] Fixed test_help_contains_example using try_parse_from with --help**

- **Found during:** Task 1 initial test run
- **Issue:** `get_long_about()` on a subcommand found via `find_subcommand_mut` returned empty string; `render_long_help()` did not include the long_about text
- **Fix:** Changed test to call `Cli::try_parse_from(["d2p", "ts", "reactive", "--help"])` and match on the resulting `Err`, which contains the full rendered help text including the long_about
- **Files modified:** d2p/src/cli.rs
- **Commit:** 749a7a3

## Self-Check: PASSED

- FOUND: d2p/src/cli.rs
- FOUND: d2p/src/main.rs
- FOUND: d2p/Cargo.toml
- FOUND: .planning/phases/03-cli-wiring/03-01-SUMMARY.md
- FOUND commit: 749a7a3 (Task 1)
- FOUND commit: 6ea75e6 (Task 2)
