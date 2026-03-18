# External Integrations

**Analysis Date:** 2026-03-18

## APIs & External Services

**Alchemy (RPC provider):**
- Ethereum mainnet, Sepolia, Unichain, Unichain Sepolia — all four chains use Alchemy-hosted RPC
  - Auth: `ALCHEMY_API_KEY` env var
  - Endpoints configured in `foundry.toml` `[rpc_endpoints]` section
  - Sepolia RPC also referenced in deploy scripts: `https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_API_KEY}`

**Reactive Network (Lasna):**
- Lasna RPC: `https://lasna-rpc.rnk.dev` — deployment target for `UniswapV3Reactive` and `ReactiveDispatchMod` contracts
  - Auth: `REACTIVE_RPC_URL` env var
  - On-chain system contract: `0x0000000000000000000000000000000000fffFfF` (Reactive system/subscription service)
  - SDK/Client: `reactive-lib` (`lib/reactive-lib/`) — `IReactive`, `ISubscriptionService`; `reactive-hooks` (`lib/reactive-hooks/`) — EDT, registry, `SubscriptionLib`, `DebtMod`
  - Used in: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol`, `src/fee-concentration-index-v2/modules/ReactiveDispatchMod.sol`

**The Graph (Uniswap V3 subgraph):**
- Endpoint: `https://gateway.thegraph.com/api/{key}/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV`
  - Auth: `THE_GRAPH_API_KEY` env var (loaded via `python-dotenv` in `research/econometrics/cross_pool/subgraph.py`)
  - Purpose: pool discovery, TVL ranking for cross-pool econometric analysis
  - GraphQL query: `research/data/queries/subgraph/pool-discovery.graphql`
  - Client: `httpx` 0.28.1

**Dune Analytics:**
- Used historically for data collection (frozen into local JSON datasets)
  - Query files: `research/data/queries/dune/fci_weth_usdc_v4.sql`
  - All data is now frozen — no live Dune API calls at runtime
  - Data integrity verified by: `research/data/scripts/verify_provenance.py` (SHA-256 hash checks)
  - Frozen datasets: `research/data/frozen/*.json` (positions, daily_at, il_proxy)

## Data Storage

**Databases:**
- None — no traditional database

**On-chain storage:**
- Uniswap V4 PoolManager (Unichain Sepolia: `0x00B036B58a818B1BC34d502D3fE730Db729e62AC`) — canonical pool state
- Uniswap V3 pools on Sepolia — source of events consumed by the reactive integration
- Diamond storage pattern — all contract state uses keccak256-namespaced storage slots; storage modules in `src/fee-concentration-index/modules/`, `src/fee-concentration-index-v2/modules/`, `src/fci-token-vault/storage/`, `src/protocol-adapter/storage/`

**File Storage:**
- Local filesystem only: `research/data/fixtures/` — FFI-readable fixture JSON files for fork tests
- `foundry.toml` grants Forge read access: `{ access = "read", path = "research/data/fixtures" }`
- Broadcast files: `broadcast/` — deploy state (e.g., `broadcast/diff-test-state.json`, `broadcast/reactive-deploy.json`)

**Caching:**
- None at application level; Forge build cache at `cache/`

## Authentication & Identity

**Auth Provider:**
- No external auth — contracts use owner-based access control
  - Implementation: `LibOwner` pattern at `src/fee-concentration-index-v2/modules/dependencies/LibOwner.sol` — `initOwner`, `requireOwner`, `transferOwnership`
  - Admin migrations: `AdminLib` at `src/fee-concentration-index-v2/modules/dependencies/AdminLib.sol` — `migrateFunds`
- Wallet accounts for deploy: HD wallet from `MNEMONIC` env var (BIP-44, indices 0-3), utility at `src/utils/Accounts.sol`

## Monitoring & Observability

**Error Tracking:**
- None (no external service)

**Logs:**
- Forge `console2` in deploy scripts and tests for deployment addresses and state
- Reactive Network callback failure: on-chain `CallbackFailure` events emitted by the Lasna proxy when callback OOGs or reverts
- `FCITermAccumulated` event in `FeeConcentrationIndexV2` — indexed by `poolId`, `protocolFlags`, `posKey`; observable on-chain

## CI/CD & Deployment

**Hosting:**
- GitHub Actions (`.github/workflows/test.yml`) — three jobs: `build`, `test`, `research`
  - Triggers: push to `main` or `008-*` branches, pull requests, manual dispatch
  - Foundry: installed via `foundry-rs/foundry-toolchain@v1`
  - Python: `actions/setup-python@v5` with Python 3.13

**CI Jobs:**
- `build` — `forge build` with `FOUNDRY_PROFILE=lite` (src only, no FFI)
- `test` — `forge test` for `test/fci-token-vault/**` and `test/fee-concentration-index-v2/**`
- `research` — Python tests, data provenance verification, Jupyter notebook execution (headless)

**Deployment tooling:**
- `forge script` with `--broadcast --slow` for Solidity deployments
- `cast send --create` preferred over `forge create` for reliability (noted in `MEMORY.md`)
- `cast wallet derive-private-key` for key derivation from mnemonic in shell scripts
- Shell orchestrator: `foundry-script/reactive-integration/run-differential.sh` — 6-phase deploy (FCI hook → reactive contract → fund → pool setup → V3 ops → verify convergence)

**Contract Verification:**
- Etherscan: mainnet and Sepolia via `ETHERSCAN_API_KEY`
- Blockscout: Unichain (`https://unichain.blockscout.com/api`), Unichain Sepolia (`https://unichain-sepolia.blockscout.com/api`)

## Environment Configuration

**Required env vars:**
- `MNEMONIC` — HD wallet seed for all Foundry broadcast scripts
- `ALCHEMY_API_KEY` — Alchemy RPC (mainnet, Sepolia, Unichain, Unichain Sepolia)
- `REACTIVE_RPC_URL` — Lasna RPC (`https://lasna-rpc.rnk.dev`)
- `ETHERSCAN_API_KEY` — contract verification
- `SEPOLIA_CALLBACK_PROXY` — callback proxy address for reactive deploy scripts
- `V3_POOL` — V3 pool address for reactive integration
- `V3_ORIGIN_CHAIN_ID` — origin chain ID for reactive subscriptions

**Secrets location:**
- `.env` file in project root (git-ignored); loaded by `source .env` in shell scripts and `vm.envString()` in Foundry scripts

## Webhooks & Callbacks

**Incoming (reactive callbacks):**
- `unlockCallbackReactive(address,bytes)` — defined in `src/protocol-adapter/interfaces/IUnlockCallbackReactiveExt.sol`
  - Called by the Reactive Network callback proxy on Sepolia when V3 events (Swap/Mint/Burn) are captured on Lasna
  - Callback proxy address (live, Sepolia): `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA`
  - Gas limit: 1,000,000 (`CALLBACK_GAS_LIMIT` constant in `UniswapV3Reactive.sol` and `ReactiveDispatchMod.sol`)

**Outgoing (subscriptions):**
- `ISubscriptionService.subscribe/unsubscribe` — called by `UniswapV3Reactive.registerPool` / `unregisterPool` on the Reactive Network system contract (`0x0000000000000000000000000000000000fffFfF`) to watch V3 pool events
  - Subscribed events: `V3_SWAP_SIG`, `V3_MINT_SIG`, `V3_BURN_SIG` (defined in `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol`)
  - Self-sync: `PoolAdded` event (sig: `POOL_ADDED_SIG` in `src/fee-concentration-index-v2/libraries/PoolAddedSig.sol`) triggers `handlePoolAdded` inside `ReactiveDispatchMod` to auto-register new pool subscriptions

## Known Live Deployments (Sepolia + Lasna, branch 008)

| Component | Address | Chain |
|-----------|---------|-------|
| ReactiveHookAdapter (v3) | `0xF3B1023A4Ee10CB8F51E277899018Cd6D2836071` | Sepolia |
| ThetaSwapReactive (v9) | `0x302adeea6BE9a6e22f319f9ee2ABE1Be60Cc4C14` | Lasna |
| V3 Pool (fee=3000) | `0xcB80f9b60627DF6915cc8D34F5d1EF11617b8Af8` | Sepolia |
| Callback Proxy | `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA` | Sepolia |
| Deployer EOA | `0xe69228626E4800578D06a93BaaA595f6634A47C3` | Both |
| Unichain Sepolia PoolManager | `0x00B036B58a818B1BC34d502D3fE730Db729e62AC` | Unichain Sepolia |
| Unichain Sepolia PositionManager | `0xf969Aee60879C54bAAed9F3eD26147Db216Fd664` | Unichain Sepolia |

---

*Integration audit: 2026-03-18*
