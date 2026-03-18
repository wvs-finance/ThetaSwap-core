# Requirements: D2P CLI — ThetaSwap Deployment Pipeline

**Defined:** 2026-03-17
**Core Value:** Reliable single-command deployment of reactive contracts with automatic fallback when forge create fails

## v1 Requirements

### Command Structure

- [ ] **CMD-01**: User can run `d2p ts reactive uniswap-v3` to deploy UniswapV3Reactive
- [ ] **CMD-02**: CLI accepts `--rpc-url` flag with `ETH_RPC_URL` env var fallback
- [ ] **CMD-03**: CLI accepts `--private-key` flag with `ETH_PRIVATE_KEY` env var fallback
- [ ] **CMD-04**: CLI accepts `--callback` flag for callback proxy address (required, no default)
- [ ] **CMD-05**: CLI accepts `--value` flag with human-friendly unit parsing (e.g., `10react`, `0.01ether`), defaulting to `10 react`
- [ ] **CMD-06**: `--legacy` is baked into the `forge create` path (not user-supplied)
- [ ] **CMD-07**: `d2p ts reactive --help` shows usage with examples
- [ ] **CMD-08**: `d2p --version` shows version from Cargo.toml
- [ ] **CMD-09**: CLI accepts `--project` flag for Solidity project root path, defaulting to CWD; forge create runs from this directory

### Deployment Logic

- [x] **DEP-01**: Primary path runs `forge create UniswapV3Reactive --constructor-args <callback> --broadcast --legacy --value <value> --rpc-url <rpc> --private-key <key>`
- [x] **DEP-02**: If forge create fails, fallback runs `cast send --create` with identical bytecode and constructor args
- [x] **DEP-03**: `--legacy` is only applied to the forge create path, not the cast send fallback
- [x] **DEP-04**: On startup, CLI checks `forge` and `cast` are on PATH; fails with actionable error ("Install Foundry: https://getfoundry.sh") if missing
- [x] **DEP-05**: After successful deployment, CLI runs `cast receipt <txhash> --field status` and verifies `0x1` before printing output
- [x] **DEP-06**: `--constructor-args` is placed last in the forge create command (Foundry variadic parsing bug workaround)

### Output Contract

- [x] **OUT-01**: On success, stdout prints deployed contract address and tx hash (pipe-friendly)
- [ ] **OUT-02**: On failure, stderr shows which command was attempted and what went wrong
- [ ] **OUT-03**: Exit code 0 on verified success, exit code 1 on any failure
- [x] **OUT-04**: No diagnostic noise on stdout — all logs/warnings go to stderr

### Project Setup

- [x] **SET-01**: Rust crate lives in `d2p/` directory within the monorepo
- [x] **SET-02**: Dependencies: clap 4.5, anyhow 1.x, thiserror 2.x, serde_json 1.x
- [x] **SET-03**: Binary compiles with `cargo build` from `d2p/` directory

## v2 Requirements

### Extended Protocol Support

- **EXT-01**: `d2p ts reactive uniswap-v4` deploys UniswapV4 reactive contract
- **EXT-02**: `--json` output flag for structured JSON output

### Additional Subcommands

- **SUB-01**: Other `d2p ts` subcommands beyond `reactive`

## Out of Scope

| Feature | Reason |
|---------|--------|
| Interactive prompts / TUI | Conflicts with pipe-friendly stdout; breaks CI and scripting |
| Deployment artifact storage (JSON registry) | Scope explosion; pipe stdout to file instead |
| Etherscan / Blockscout verification | Use `forge verify-contract` directly; doubles scope |
| Wallet / keystore management | Adds heavy dependencies; raw private key via env var sufficient |
| Dry-run / simulation mode | `forge script` already does this better |
| Multi-contract orchestration | Chain multiple `d2p` invocations in shell scripts |
| Config file (TOML/YAML) | Shell aliases or `.env` cover this at zero implementation cost |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CMD-01 | Phase 3 | Pending |
| CMD-02 | Phase 3 | Pending |
| CMD-03 | Phase 3 | Pending |
| CMD-04 | Phase 3 | Pending |
| CMD-05 | Phase 3 | Pending |
| CMD-06 | Phase 3 | Pending |
| CMD-07 | Phase 3 | Pending |
| CMD-08 | Phase 3 | Pending |
| CMD-09 | Phase 3 | Pending |
| DEP-01 | Phase 2 | Complete |
| DEP-02 | Phase 2 | Complete |
| DEP-03 | Phase 2 | Complete |
| DEP-04 | Phase 2 | Complete |
| DEP-05 | Phase 2 | Complete |
| DEP-06 | Phase 2 | Complete |
| OUT-01 | Phase 2 | Complete |
| OUT-02 | Phase 3 | Pending |
| OUT-03 | Phase 3 | Pending |
| OUT-04 | Phase 2 | Complete |
| SET-01 | Phase 1 | Complete |
| SET-02 | Phase 1 | Complete |
| SET-03 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-17 after roadmap creation*
