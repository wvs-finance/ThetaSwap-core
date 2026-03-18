# Codebase Structure

**Analysis Date:** 2026-03-18

## Directory Layout

```
thetaSwap-core-dev/
├── src/                                    # Solidity production contracts
│   ├── fee-concentration-index/            # FCI V1 hook (V4 native, legacy)
│   ├── fee-concentration-index-v2/         # FCI V2 orchestrator + protocol facets
│   │   ├── protocols/
│   │   │   ├── uniswap-v3/                 # V3 reactive facet, callback, reactive contract
│   │   │   └── uniswap-v4/                 # Native V4 facet
│   │   ├── modules/                        # Diamond storage modules
│   │   ├── interfaces/                     # IFCIProtocolFacet, IFeeConcentrationIndexV2
│   │   ├── libraries/                      # FCIProtocolLib, PoolKeyExtLib, event sigs
│   │   └── types/                          # EpochSnapshot, LiquidityPositionSnapshot, FlagsRegistry
│   ├── fci-token-vault/                    # Paired LONG/SHORT vault (ERC-6909)
│   │   ├── facets/                         # CollateralCustodianFacet, OraclePayoffFacet
│   │   ├── modules/                        # Business logic (CEI order)
│   │   │   └── dependencies/               # ERC20Lib, ERC6909Lib, ReentrancyLib
│   │   ├── storage/                        # CustodianStorage, OraclePayoffStorage
│   │   ├── interfaces/                     # ICollateralCustodian, IOraclePayoff
│   │   ├── libraries/                      # SqrtPriceLookbackPayoffX96Lib
│   │   └── tokens/                         # ERC20WrapperFacade
│   ├── protocol-adapter/                   # hookData-aware FCI V1 dispatch bridge
│   │   ├── modules/                        # ProtocolAdapterMod (9 free-function wrappers)
│   │   ├── storage/                        # ProtocolAdapterStorage
│   │   ├── libraries/                      # ProtocolAdapterLib
│   │   └── interfaces/                     # IProtocolStateView, IUnlockCallbackReactiveExt
│   ├── libraries/                          # Cross-feature shared free functions
│   ├── types/                              # Shared type extensions (HookDataFlagsMod, BlockCountExt)
│   └── utils/                              # Non-production helpers (V3CallbackRouter, Pool, TokenPair)
├── test/                                   # Forge tests
│   ├── fee-concentration-index/            # FCI V1 tests (harness, helpers)
│   ├── fee-concentration-index-v2/         # FCI V2 tests (unit, integration, differential)
│   │   └── protocols/
│   │       ├── uniswap-v3/                 # V3 reactive path tests
│   │       └── uniswapV4/                  # V4 native integration tests
│   ├── fci-token-vault/                    # Vault tests (unit, fuzz, adversarial, integration)
│   │   ├── unit/                           # Module-level tests
│   │   ├── fuzz/                           # Invariant + handler
│   │   ├── adversarial/                    # Edge case + lifecycle guard tests
│   │   ├── integration/                    # End-to-end lifecycle
│   │   ├── fixtures/                       # FCIFixture, FacetDeployer, DeltaPlusStub
│   │   ├── helpers/                        # Harness contracts
│   │   └── kontrol/                        # Formal verification specs
│   ├── simulation/                         # JIT game simulations
│   └── utils/                              # Test utilities (Accounts, Pool, TokenPair)
├── foundry-script/                         # Forge deploy and simulation scripts
│   ├── deploy/                             # DeployFci, DeployFCIV2HookV4, CreatePoolV3/V4
│   ├── reactive-integration/               # Reactive integration scripts
│   ├── simulation/                         # JitGame.sol simulation
│   ├── types/                              # Scenario types
│   └── utils/                             # Script utilities
├── specs/                                  # Contract specifications per feature
│   ├── 001-fee-concentration-index/
│   ├── 002-theta-swap-cfmm/
│   ├── 003-reactive-integration/
│   └── 004-fci-token-vault/
├── research/                               # Python research pipeline (MUST stay in sync across branches)
│   ├── backtest/                           # Insurance backtest pipeline (8 modules)
│   ├── econometrics/                       # Duration, hazard, cross-pool analysis (13 modules)
│   ├── data/                               # Fixtures, raw events, oracle scripts
│   │   └── scripts/                        # fci_oracle.py, hhi_oracle.py
│   ├── model/                              # LaTeX spec + main.pdf
│   ├── notebooks/                          # Jupyter notebooks
│   ├── scripts/                            # FFI oracle scripts (called by fuzz tests)
│   ├── simulator/                          # Python FCI simulator
│   └── tests/                              # Python tests (114)
├── docs/
│   ├── plans/                              # Branch-specific implementation plans (YYYY-MM-DD-<topic>.md)
│   ├── archive/                            # Archived documentation
│   └── context/                            # Context documents
├── lib/                                    # Forge git submodule dependencies (DO NOT MODIFY)
├── broadcast/                              # Forge deployment broadcast artifacts
├── out-sol/                                # Solidity build artifacts (generated)
├── app/                                    # Frontend application (React/Vite)
├── uhi8/                                   # Python venv for research (use: uhi8/bin/python)
├── foundry.toml                            # Forge configuration, remappings, RPC endpoints
└── CLAUDE.md                               # Project development guidelines
```

---

## Directory Purposes

**`src/fee-concentration-index/`:**
- Purpose: FCI V1 — the original Uniswap V4 native hook. Deployed as a MasterHook diamond facet.
- Contains: `FeeConcentrationIndex.sol` (hook), `FeeConcentrationEpochStorageMod.sol`, `FeeConcentrationIndexStorageMod.sol`
- Key files: `src/fee-concentration-index/FeeConcentrationIndex.sol`, `src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol`

**`src/fee-concentration-index-v2/`:**
- Purpose: FCI V2 — protocol-agnostic orchestrator. The primary production hook for multi-protocol FCI computation.
- Contains: Orchestrator, protocol facets, storage modules, interfaces, libraries, types
- Key files:
  - `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol` — main orchestrator
  - `src/fee-concentration-index-v2/FCIMetricsFacet.sol` — read-only metrics facet
  - `src/fee-concentration-index-v2/FCIProtocolFacet.sol` — template facet for new protocols
  - `src/fee-concentration-index-v2/types/FlagsRegistry.sol` — protocol `bytes2` flag constants
  - `src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol` — facet registry
  - `src/fee-concentration-index-v2/modules/FCIFacetAdminStorageMod.sol` — per-protocol admin storage
  - `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol` — core FCI state + registry

**`src/fee-concentration-index-v2/protocols/uniswap-v3/`:**
- Purpose: V3 reactive protocol implementation. Three contracts: facet (behavioral), callback (bridge), reactive (subscription).
- Key files:
  - `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol` — delegatecall target
  - `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol` — Sepolia-side callback
  - `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol` — Reactive Network contract
  - `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/V3HookDataLib.sol` — encode/decode hookData
  - `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol` — V3 event topic0 constants

**`src/fee-concentration-index-v2/protocols/uniswap-v4/`:**
- Purpose: Native V4 protocol facet — reads state directly from `IPoolManager.StateLibrary`.
- Key files: `src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol`

**`src/fci-token-vault/`:**
- Purpose: ERC-6909 vault for paired LONG/SHORT positions, backed by USDC. Diamond facet architecture.
- Contains: Two facets (custodian + oracle payoff), storage structs, module logic, ERC-20 wrapper
- Key files:
  - `src/fci-token-vault/facets/CollateralCustodianFacet.sol` — deposit/redeemPair
  - `src/fci-token-vault/facets/OraclePayoffFacet.sol` — settle/redeemLong/redeemShort (Model B, removable)
  - `src/fci-token-vault/storage/CustodianStorage.sol` — slot: `keccak256("thetaswap.collateral-custodian")`
  - `src/fci-token-vault/storage/OraclePayoffStorage.sol`

**`src/protocol-adapter/`:**
- Purpose: Dispatch bridge for FCI V1. `hookData`-aware wrappers that select the right storage slot. Used by FCI V1 to support both native V4 and reactive paths.
- Key files:
  - `src/protocol-adapter/modules/ProtocolAdapterMod.sol` — 9 free-function wrappers
  - `src/protocol-adapter/storage/ProtocolAdapterStorage.sol` — V4 + V3 adapter slots
  - `src/protocol-adapter/libraries/ProtocolAdapterLib.sol` — `fciStorageFor(hookData)`

**`src/libraries/`:**
- Purpose: Cross-feature shared free functions. Extensions of types not defined here.
- Contains:
  - `src/libraries/HookUtilsMod.sol` — `derivePoolAndPosition`, `sortTicks`, `fetchPositionKey`
  - `src/libraries/FeeConcentrationIndexStorageExt.sol` — transient storage helpers (tick cache, removal data)
  - `src/libraries/FeeGrowthReaderExt.sol` — V4 pool fee growth reads via `StateLibrary`
  - `src/libraries/PoolKeyExtMod.sol` — `v3PositionKey`

**`src/types/`:**
- Purpose: Shared type-level extensions and flag definitions for composable type dispatch.
- Contains:
  - `src/types/HookDataFlagsMod.sol` — `REACTIVE_FLAG`, `V3_FLAG`, `V4_FLAG` bitmasks and encode/decode helpers
  - `src/types/BlockCountExt.sol` — `thetaWeight` computation on `BlockCount`

**`src/utils/`:**
- Purpose: Non-production test and deployment helpers only. Not imported by production contracts.
- Contains:
  - `src/utils/V3CallbackRouter.sol` — EOA-friendly V3 mint/swap router (scripts/CI use)
  - `src/utils/Pool.sol`, `src/utils/TokenPair.sol`, `src/utils/Accounts.sol`, `src/utils/Mode.sol`

**`test/fci-token-vault/`:**
- Purpose: Full vault test suite organized by test type.
- Key files:
  - `test/fci-token-vault/fixtures/FCIFixture.sol` — shared `setUp` fixture inheriting `PosmTestSetup`
  - `test/fci-token-vault/fixtures/FacetDeployer.sol` — deploys diamond with both facets
  - `test/fci-token-vault/fuzz/CustodianHandler.sol` + `CustodianInvariant.fuzz.t.sol` — invariant suite

**`test/fee-concentration-index-v2/`:**
- Purpose: FCI V2 tests including V3 reactive integration and V4 native.
- Key files:
  - `test/fee-concentration-index-v2/protocols/uniswapV3/UniswapV3FeeConcentrationIndex.integration.t.sol` — fork integration
  - `test/fee-concentration-index-v2/protocols/uniswapV4/NativeV4FeeConcentrationIndex.integration.t.sol` — V4 integration
  - `test/fee-concentration-index-v2/differential/FCIV1DiffFCIV2.diff.t.sol` — V1 vs V2 differential

**`foundry-script/`:**
- Purpose: Forge deployment and CI scripts. Uses `broadcast/` for artifacts.
- Key files:
  - `foundry-script/deploy/DeployFCIV2HookV4.s.sol` — V2 hook + facet deployment
  - `foundry-script/deploy/DeployFci.s.sol` — V1 hook deployment
  - `foundry-script/deploy/CreatePoolV3.s.sol` / `CreatePoolV4.s.sol` — pool initialization

**`research/`:**
- Purpose: Python research pipeline — backtests, econometrics, FFI oracle scripts. Shared across ALL branches.
- Key files:
  - `research/data/scripts/fci_oracle.py` — oracle used by fork tests via FFI
  - `research/data/fixtures/` — fixture data read by fork tests (`fs_permissions` in `foundry.toml`)

**`lib/`:**
- Purpose: Forge git submodules. NEVER modify directly. Extend types in `src/types/*Ext.sol`.
- Key submodules: `uniswap-hooks/lib/v4-core`, `v3-core`, `typed-uniswap-v4`, `reactive-lib`, `reactive-hooks`, `solady`, `hook-bazaar`, `v4-periphery`, `forge-std`

---

## Key File Locations

**Entry Points:**
- `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol` — main V2 hook orchestrator
- `src/fee-concentration-index/FeeConcentrationIndex.sol` — V1 hook (legacy active)
- `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol` — V3 reactive bridge

**Configuration:**
- `foundry.toml` — compiler settings (`solc = 0.8.26`, `via_ir = true`, `evm_version = cancun`), remappings, RPC endpoints, fuzz config

**Core Logic:**
- `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol` — FCI state struct + mutations
- `src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol` — facet registry + `getProtocolFlagFromHookData`
- `src/fee-concentration-index-v2/types/FlagsRegistry.sol` — protocol flag constants
- `src/types/HookDataFlagsMod.sol` — legacy V1 bitmask flags

**Testing:**
- `test/fci-token-vault/fixtures/FCIFixture.sol` — base fixture for vault tests
- `test/fee-concentration-index/harness/FeeConcentrationIndexHarness.sol` — V1 test harness
- `test/fee-concentration-index-v2/differential/FCIDifferentialBase.sol` — differential test base

---

## Naming Conventions

**Files:**
- Contracts: `PascalCase.sol` (e.g., `FeeConcentrationIndexV2.sol`, `CollateralCustodianFacet.sol`)
- Storage modules: `<Name>StorageMod.sol` (e.g., `FeeConcentrationIndexStorageV2Mod.sol`)
- Libraries (free functions): `<Name>Mod.sol` or `<Name>Lib.sol` or `<Name>Ext.sol`
  - `Mod.sol` — storage module (contains a struct + free functions)
  - `Lib.sol` — pure logic library (no storage struct)
  - `Ext.sol` — extension of a type defined in `lib/` (placed in `src/libraries/` or `src/types/`)
- Interfaces: `I<Name>.sol` (e.g., `IFCIProtocolFacet.sol`)
- Test files: `<Name>.<type>.t.sol` where type is `unit`, `fuzz`, `integration`, `fork`, `diff`, `k` (kontrol)
- Script files: `<Purpose>.s.sol`

**Directories:**
- Feature directories use `kebab-case` (e.g., `fee-concentration-index-v2`, `fci-token-vault`)
- Sub-feature protocol directories: `uniswap-v3`, `uniswap-v4`

**Solidity:**
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `NATIVE_V4`, `FCI_V2_STORAGE_SLOT`)
- Storage structs: `PascalCase` (e.g., `FeeConcentrationIndexV2Storage`)
- Free functions: `camelCase` (e.g., `fciV2Storage`, `getProtocolFlagFromHookData`)
- Events: `PascalCase` (e.g., `FCITermAccumulated`, `PoolAdded`)
- Custom errors: `PascalCase` (e.g., `DepositCapExceeded`, `OnlyReactVM`)

---

## Where to Add New Code

**New Protocol Facet (e.g., Uniswap V2):**
- Implementation: `src/fee-concentration-index-v2/protocols/uniswap-v2/UniswapV2Facet.sol`
- Add flag to: `src/fee-concentration-index-v2/types/FlagsRegistry.sol`
- Library: `src/fee-concentration-index-v2/protocols/uniswap-v2/libraries/`
- Tests: `test/fee-concentration-index-v2/protocols/uniswap-v2/`
- Register facet in V2: call `fci.registerProtocolFacet(UNISWAP_V2, facetAddress)`

**New Vault Facet:**
- Implementation: `src/fci-token-vault/facets/<Name>Facet.sol`
- Storage: `src/fci-token-vault/storage/<Name>Storage.sol`
- Module logic: `src/fci-token-vault/modules/<Name>Mod.sol`
- Tests: `test/fci-token-vault/facet/<Name>Facet.t.sol`, unit in `test/fci-token-vault/unit/<Name>Mod.t.sol`

**New Shared Free Function:**
- If it reads/writes storage: `src/libraries/<Name>StorageExt.sol` or `src/protocol-adapter/modules/`
- If it is pure math/computation: `src/libraries/<Name>Lib.sol`
- If it extends a type from `lib/`: `src/libraries/<TypeName>Ext.sol`

**New Type Extension:**
- Extension of `lib/` type: `src/types/<TypeName>Ext.sol` — never modify `lib/`

**New Deploy Script:**
- Location: `foundry-script/deploy/<Purpose>.s.sol`
- Use `cast send --create` for contract deployment (not `forge create --rpc-url`)

**Branch-Scoped Plan:**
- Location: `docs/plans/YYYY-MM-DD-<topic>.md`
- Only create plans relevant to the current branch feature (see `CLAUDE.md` branch rules)

**Research Changes:**
- Location: `research/` (any subdirectory)
- After any change: commit + push on current branch, then sync to all other feature branches

---

## Special Directories

**`lib/`:**
- Purpose: Forge git submodules — all external dependencies
- Generated: No (checked-in as submodule references)
- Committed: Submodule pointers only; never modify source files within

**`out-sol/`:**
- Purpose: Solidity build artifacts produced by `forge build`
- Generated: Yes
- Committed: No (gitignored)

**`broadcast/`:**
- Purpose: Deployment transaction records from `forge script` with `--broadcast`
- Generated: Yes (from scripts)
- Committed: Yes (tracked for deployment history); `fs_permissions` allows read-write in `foundry.toml`

**`research/data/fixtures/`:**
- Purpose: JSON fixture files read by fork tests via `vm.readFile` (FFI)
- Generated: By Python oracle scripts
- Committed: Yes; path listed in `foundry.toml` `fs_permissions`

**`uhi8/`:**
- Purpose: Python virtual environment for all research/testing Python code
- Generated: Yes (local venv)
- Committed: No (gitignored)
- Usage: Always use `uhi8/bin/python` and `uhi8/bin/pytest`, not system Python

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents consumed by `gsd:plan-phase` and `gsd:execute-phase`
- Generated: By codebase mapper agent
- Committed: Yes

---

*Structure analysis: 2026-03-18*
