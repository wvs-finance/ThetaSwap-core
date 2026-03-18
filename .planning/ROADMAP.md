# Roadmap: D2P CLI — ThetaSwap Deployment Pipeline

## Overview

Three phases deliver the `d2p` binary: scaffolding the Rust crate (Phase 1), implementing the forge-to-cast fallback deploy logic with all correctness mitigations (Phase 2), and wiring the CLI argument parser to call that logic (Phase 3). Each phase ships a testable artifact. The hard work is Phase 2 — Phase 3 is mechanical wiring once the deploy contract exists.

## Phases

- [x] **Phase 1: Crate Foundation** - Rust crate skeleton with typed errors, deploy params, and output structs (completed 2026-03-17)
- [ ] **Phase 2: Deploy Logic** - forge-to-cast fallback runner with receipt verification and pipe-friendly output
- [ ] **Phase 3: CLI Wiring** - clap argument parser wired to deploy runner, producing the complete `d2p` binary

## Phase Details

### Phase 1: Crate Foundation
**Goal**: A compilable `d2p/` crate with all shared types that downstream modules depend on
**Depends on**: Nothing (first phase)
**Requirements**: SET-01, SET-02, SET-03
**Success Criteria** (what must be TRUE):
  1. `cargo build` in `d2p/` succeeds with zero errors
  2. `D2pError` enum, `DeployParams` struct, and `DeployOutput` struct exist as distinct modules
  3. All four dependencies (clap 4.5, anyhow 1.x, thiserror 2.x, serde_json 1.x) are pinned in Cargo.toml
**Plans**: 1 plan

Plans:
- [ ] 01-01-PLAN.md — Scaffold crate manifest, entry point, shared types, and unit tests

### Phase 2: Deploy Logic
**Goal**: Working `Runner::deploy()` that tries `forge create`, falls back to `cast send --create`, verifies receipt status, and returns a pipe-friendly output or a typed error — before any CLI argument parsing exists
**Depends on**: Phase 1
**Requirements**: DEP-01, DEP-02, DEP-03, DEP-04, DEP-05, DEP-06, OUT-01, OUT-04
**Success Criteria** (what must be TRUE):
  1. Calling `Runner::deploy(params)` directly in a Rust test produces a `DeployOutput` with address and tx hash on success
  2. When `forge create` fails, the runner automatically retries with `cast send --create` and logs a warning to stderr
  3. `cast receipt <txhash> --field status` is called after every deployment and returns `0x1` before output is returned
  4. Stdout of `DeployOutput::display()` contains only the deployed address and tx hash — no diagnostic noise
  5. If `forge` or `cast` are not on PATH, the call fails immediately with an actionable error message
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — primary.rs (forge create) + fallback.rs (cast send --create) with arg-order and JSON parsing tests
- [ ] 02-02-PLAN.md — verify.rs (cast receipt --json) + Runner orchestration + check_prerequisites() in mod.rs

### Phase 3: CLI Wiring
**Goal**: Complete `d2p` binary where `d2p ts reactive uniswap-v3` accepts all documented flags and env vars, invokes the Phase 2 runner, and exits cleanly
**Depends on**: Phase 2
**Requirements**: CMD-01, CMD-02, CMD-03, CMD-04, CMD-05, CMD-06, CMD-07, CMD-08, CMD-09, OUT-02, OUT-03
**Success Criteria** (what must be TRUE):
  1. `d2p ts reactive uniswap-v3 --rpc-url <url> --private-key <key> --callback <addr> --value 10react` deploys UniswapV3Reactive and prints the address + tx hash to stdout
  2. `d2p ts reactive --help` shows usage with flag descriptions and examples
  3. `d2p --version` prints the version from Cargo.toml
  4. Missing required flag `--callback` with no env fallback causes exit code 1 with an error on stderr, nothing on stdout
  5. `ETH_RPC_URL` and `ETH_PRIVATE_KEY` env vars are accepted as fallbacks when flags are omitted
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Crate Foundation | 1/1 | Complete    | 2026-03-18 |
| 2. Deploy Logic | 1/2 | In Progress|  |
| 3. CLI Wiring | 0/? | Not started | - |
