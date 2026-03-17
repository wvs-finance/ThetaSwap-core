# D2P CLI — ThetaSwap Deployment Pipeline

## What This Is

A Rust CLI tool (`d2p`) that wraps Foundry's `forge create` and `cast send --create` to deploy ThetaSwap reactive contracts. The first subcommand is `d2p ts reactive <protocol>`, which deploys protocol-specific reactive contracts (starting with UniswapV3Reactive) and outputs the deployed address + tx hash on success. It's a thin, pipe-friendly deployment wrapper that handles Foundry quirks (forge create RPC issues) with automatic fallback.

## Core Value

Reliable single-command deployment of reactive contracts with automatic fallback when `forge create` fails — always get a deployed address or a clear error.

## Requirements

### Validated

<!-- Inferred from existing codebase — these capabilities already exist in Solidity -->

- ✓ UniswapV3Reactive contract exists with single-arg constructor (callback address) — `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol`
- ✓ FeeConcentrationIndexV2 orchestrator with diamond storage pattern — `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`
- ✓ Protocol facet system (V3, V4) via IFCIProtocolFacet — `src/fee-concentration-index-v2/protocols/`
- ✓ Reactive Network integration (subscriptions, callbacks, event routing) — `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol`
- ✓ Foundry build toolchain configured (foundry.toml, remappings, profiles) — `foundry.toml`
- ✓ Live deployments on Sepolia + Lasna verified working — memory: V2 deployment details

### Active

<!-- CLI tool scope — what we're building -->

- [ ] `d2p ts reactive uniswap-v3` deploys UniswapV3Reactive with callback address constructor arg
- [ ] CLI accepts `--rpc-url`, `--private-key`, `--callback`, and `--value` flags
- [ ] Primary path: `forge create` with `--broadcast --legacy` flags baked in
- [ ] Fallback path: if `forge create` reverts, try-catch to `cast send --create` with identical bytecode + constructor args
- [ ] On success: stdout prints deployed contract address + tx hash (pipe-friendly)
- [ ] On failure: clear error message to stderr, non-zero exit code
- [ ] CLI is a Rust binary using clap for arg parsing

### Out of Scope

- Other `d2p ts` subcommands beyond `reactive` — future milestone
- Protocol support beyond `uniswap-v3` — future milestone (structure should allow it)
- Contract verification (etherscan/blockscout) post-deploy — separate concern
- Interactive prompts or TUI — this is a pipe-friendly CLI
- Wallet management or keystore integration — raw private key via flag for now

## Context

- The existing codebase is a Solidity project (Foundry-based) with a complex multi-protocol hook system
- `forge create --rpc-url` sometimes silently ignores the RPC flag, requiring fallback to `cast send --create`
- Deployments to Reactive Network (Lasna) require `--legacy` flag
- UniswapV3Reactive constructor is `payable` — needs `--value` to fund `depositToSystem` at deploy time
- The Rust CLI lives in this same repo, likely under a `cli/` or `d2p/` directory
- Foundry tools (`forge`, `cast`) must be available on PATH

## Constraints

- **Language**: Rust — user specified
- **Dependencies**: Must have `forge` and `cast` on PATH (Foundry toolchain)
- **Solidity compiler**: Existing `foundry.toml` config used for compilation (solc 0.8.26, via_ir, cancun)
- **Output format**: Address + tx hash on stdout, errors on stderr — pipe-friendly
- **Constructor**: UniswapV3Reactive takes `address callback_` and is `payable`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Rust for CLI | User specified; good for CLI tooling, single binary distribution | — Pending |
| forge create as primary, cast send as fallback | forge create sometimes ignores --rpc-url; cast send --create is more reliable | — Pending |
| --broadcast and --legacy baked in | Always needed for reactive deployments; reduces user error | — Pending |
| Pipe-friendly output (address + tx hash) | Enables scripting and composability with other tools | — Pending |

---
*Last updated: 2026-03-17 after initialization*
