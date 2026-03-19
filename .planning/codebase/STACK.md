# Technology Stack

**Analysis Date:** 2026-03-18

## Languages

**Primary:**
- Solidity ^0.8.26 — all on-chain contracts in `src/`, tests in `test/`, deploy scripts in `foundry-script/`
- Python 3.13 — research pipeline: backtest, econometrics, oracle FFI, Jupyter notebooks in `research/`

**Secondary:**
- Bash — deployment orchestration scripts (`foundry-script/reactive-integration/run-differential.sh`, `foundry-script/deploy/run-differential.sh`)

## Runtime

**Environment:**
- EVM (Cancun hardfork) — `evm_version = "cancun"` in `foundry.toml`
- Python venv managed by `uv` at `uhi8/` — `uhi8/bin/python` for all Python invocations

**Package Manager:**
- Foundry (forge 1.5.1-stable) for Solidity
- uv for Python — lockfile: `uv.lock` (present, pinned)
- git submodules for Solidity dependencies (see `lib/`)

## Frameworks

**Core (Solidity):**
- Uniswap V4 core (`lib/uniswap-hooks/lib/v4-core/`) — `IPoolManager`, `PoolKey`, `StateLibrary`, `TickBitmap`, hook callbacks
- Uniswap V3 core (`lib/v3-core/`) — `IUniswapV3Pool`, tick/fee-growth reading in reactive integration
- Uniswap V4 periphery (`lib/v4-periphery/`) — `HookMiner`, `PositionConfig`, `PositionManager`
- Uniswap V3 periphery (`lib/v3-periphery/`) — router interfaces used in deploy scripts
- MasterHook diamond (`lib/hook-bazaar/contracts/src/master-hook-pkg/`) — `MasterHook`, `HookFacetTemplate`, diamond dispatch; FCI deploys as a facet via delegatecall
- Reactive Network (`lib/reactive-lib/`, `lib/reactive-hooks/`) — `IReactive`, `ISubscriptionService`, event dispatch/subscription layer for cross-chain V3→V4 reactive integration

**Testing:**
- forge-std (`lib/forge-std/`) — `Test`, `Script`, `console2`, `IERC20`, `IERC165`
- Kontrol (`lib/kontrol-cheatcodes/`) — formal verification via `KontrolCheats`; `.k.sol` files prove invariants (e.g., `test/fci-token-vault/kontrol/SqrtPriceLookbackPayoffX96.k.sol`)
- Chimera (`lib/chimera/`) — `BaseSetup`, `BaseCryticToFoundry`, property-based testing scaffolding
- pytest 9.0.2 — Python test runner for `research/tests/` (114 tests)

**Build/Dev:**
- Foundry with IR pipeline — `via_ir = true` in `foundry.toml`
- Makefile — orchestrates `install`, `test`, `notebooks`, `verify-data`
- uv — Python venv and dependency management
- JupyterLab 4.5.5 — research notebooks executed headless in CI

## Key Dependencies

**Critical (Solidity):**
- `typed-uniswap-v4` (`lib/typed-uniswap-v4/`) — domain types: `TickRange`, `FeeShareRatio`, `FeeConcentrationState`, `SwapCount`, `BlockCount`, `SqrtPriceX96`, `FeeRevenue`, etc. Core mathematical vocabulary of the FCI algorithm
- `solady` (`lib/solady/`) — `FixedPointMathLib` (expWad, mulDiv for payoff math), `SafeTransferLib` (token transfers in vault), `LibCall` (delegatecall wrapper in FCI V2 orchestrator)
- `reactive-hooks` (`lib/reactive-hooks/`) — origin/callback registry, event dispatch table (EDT), subscription helpers; consumed by `ReactiveDispatchMod.sol`
- `angstrom` (`lib/angstrom/`) — `CalldataReader`, `CalldataReaderLib` for efficient calldata parsing in FCI hook data routing
- `openzeppelin-contracts` (`lib/openzeppelin-contracts/`) — `EnumerableSet` in `FCIFacetAdminStorageMod.sol`

**Infrastructure:**
- `solmate` (via `lib/v4-periphery/lib/solmate/`) — `MockERC20` for test token setup
- `foundry-devops` (`lib/foundry-devops/`) — deployment utilities
- `foundational-hooks` (via `lib/typed-uniswap-v4/`) — `SqrtPriceLibrary`, `Q96` constant
- `permit2` (via `lib/v4-periphery/`) — referenced via remapping but not directly used in production src
- `2025-12-panoptic` (`lib/2025-12-panoptic/`) — present as reference/research submodule
- `angstrom` (`lib/angstrom/`) — CalldataReader utility only; not full Angstrom integration
- `bunni-v2` (`lib/bunni-v2/`) — present as research reference submodule
- `Compose` / `compose-extensions` — hook composition utilities from hook-bazaar ecosystem

**Critical (Python):**
- `jax[cpu]` 0.9.1 — JAX arrays for econometric computations; used in `research/econometrics/`
- `scipy` 1.17.1 — duration models, hazard functions in `research/econometrics/`
- `numpy` 2.4.3 — array math throughout research pipeline
- `matplotlib` 3.10.8 — plotting in `research/backtest/plotting.py`
- `httpx` 0.28.1 — HTTP client for The Graph subgraph queries in `research/econometrics/cross_pool/subgraph.py`
- `eth_abi` 5.2.0 — ABI encoding/decoding in Python oracle scripts
- `pycryptodome` 3.23.0 — keccak256 implementation in FCI oracle scripts (`research/data/scripts/fci_oracle.py`, `fci_epoch_oracle.py`)
- `python-dotenv` — loads `.env` for subgraph API key in research scripts

## Configuration

**Environment (required .env vars):**
- `MNEMONIC` — HD wallet for Foundry deploy scripts (`vm.envString("MNEMONIC")`)
- `ALCHEMY_API_KEY` — RPC URLs for mainnet, Sepolia, Unichain, Unichain Sepolia
- `REACTIVE_RPC_URL` — Lasna (Reactive Network) RPC endpoint (`https://lasna-rpc.rnk.dev`)
- `ETHERSCAN_API_KEY` — contract verification on Etherscan and Blockscout
- `SEPOLIA_CALLBACK_PROXY` — used in reactive integration deploy scripts
- `V3_POOL` — V3 pool address for reactive integration
- `V3_ORIGIN_CHAIN_ID` — source chain for reactive subscriptions

**Build:**
- `foundry.toml` — profiles (`default`, `lite`, `ci`, `fuzz-heavy`), remappings, RPC endpoints, fuzz parameters
- `remappings.txt` — path aliases for test imports
- `pyproject.toml` — Python package definition, pytest config
- `uv.lock` — pinned Python dependency tree

**Forge profiles:**
- `default` — full build with FFI enabled, 6 threads, `via_ir`
- `lite` — skips `test/` and `foundry-script/` for fast src-only builds
- `ci` — FFI disabled, `force = false` (used in GitHub Actions)
- `fuzz-heavy` — extended fuzz runs (64 runs, 131072 max rejects)

**Forge fuzz config:**
- `runs = 256`, `max_test_rejects = 65536`
- `fs_permissions`: read from `research/data/fixtures`, read-write to `broadcast/`

## Platform Requirements

**Development:**
- Foundry (forge 1.5.1+)
- Python 3.13 via uv
- git submodules recursive (`git submodule update --init --recursive`)
- `.env` file with all required env vars

**Production:**
- Sepolia testnet (chain 11155111) — FCI hook + UniswapV3 adapter
- Lasna (Reactive Network) — `UniswapV3Reactive` / `ReactiveDispatchMod` contract
- Unichain Sepolia (chain 1301) — V4 PoolManager deployment target
- Ethereum mainnet (chain 1) — configured but not yet deployed

---

*Stack analysis: 2026-03-18*
