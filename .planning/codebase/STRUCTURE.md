# Codebase Structure

**Analysis Date:** 2026-03-17

## Directory Layout

```
thetaSwap-core-dev/
├── src/                                          # Solidity contracts (Solidity ^0.8.26)
│   ├── fee-concentration-index/                  # Legacy FCI V1 (kept for reference/migration)
│   │   ├── interfaces/
│   │   ├── modules/
│   │   └── ...
│   ├── fee-concentration-index-v2/               # Protocol-agnostic FCI orchestrator
│   │   ├── FeeConcentrationIndexV2.sol            # Main orchestrator (hook handlers, delegatecall routing)
│   │   ├── interfaces/
│   │   │   ├── IFCIProtocolFacet.sol              # Protocol adapter interface
│   │   │   ├── IFCIMetricsFacet.sol               # Metrics query interface
│   │   │   └── IFeeConcentrationIndexV2.sol
│   │   ├── libraries/
│   │   ├── modules/
│   │   │   ├── FeeConcentrationIndexStorageV2Mod.sol   # Diamond storage for FCI state
│   │   │   ├── FeeConcentrationIndexRegistryStorageMod.sol  # Facet registry (bytes2 flag → address)
│   │   │   ├── FCIProtocolFacetStorageMod.sol          # Per-protocol metrics storage
│   │   │   ├── FCIFacetAdminStorageMod.sol             # Admin configuration storage
│   │   │   └── dependencies/
│   │   ├── protocols/
│   │   │   ├── uniswap-v3/
│   │   │   │   ├── UniswapV3Facet.sol            # V3 protocol adapter (implements IFCIProtocolFacet)
│   │   │   │   ├── UniswapV3Callback.sol         # V3 fee growth baseline reader
│   │   │   │   ├── interfaces/
│   │   │   │   ├── modules/
│   │   │   │   └── libraries/
│   │   │   └── uniswap-v4/
│   │   │       ├── NativeUniswapV4Facet.sol      # V4 protocol adapter
│   │   │       └── libraries/
│   │   ├── types/
│   │   │   ├── LiquidityPositionSnapshot.sol     # Position state snapshot
│   │   │   ├── RangeSnapshot.sol                 # Range metadata
│   │   │   ├── EpochSnapshot.sol                 # Epoch statistics
│   │   │   └── FlagsRegistry.sol                 # Protocol flags (bytes2 constants)
│   │   └── ...
│   ├── reactive-integration/                      # Reactive Network + V3 adapter
│   │   ├── ThetaSwapReactive.sol                  # Thin ReactVM shell (owner, adapter, service)
│   │   ├── FeeConcentrationIndexV2.sol            # Re-exported (FCI used in reactive context)
│   │   ├── adapters/
│   │   │   └── uniswapV3/
│   │   │       ├── ReactiveHookAdapter.sol        # Destination adapter (receives RN callbacks)
│   │   │       ├── ReactiveHookAdapterStorageMod.sol   # Adapter storage (fee snapshots, FCI state)
│   │   │       ├── ReactiveAuthMod.sol            # Authorization checks
│   │   │       ├── ReactiveHookAdapterTranslateMod.sol # Event translation
│   │   │       ├── V3CallbackRouter.sol           # Callback routing logic
│   │   │       └── ...
│   │   ├── template/                              # Protocol adapter template (reusable pattern)
│   │   │   ├── interfaces/
│   │   │   │   ├── IProtocolStateView.sol        # Protocol read abstraction
│   │   │   │   ├── IFCIProtocolFacet.sol         # Reexport
│   │   │   │   └── IUnlockCallbackReactiveExt.sol
│   │   │   ├── modules/
│   │   │   ├── storage/
│   │   │   └── libraries/
│   │   ├── uniswapV3/                             # V3 reactive event handling
│   │   │   ├── modules/
│   │   │   │   └── UniswapV3ReactiveMod.sol      # Event decoding, state tracking
│   │   │   ├── types/
│   │   │   │   ├── UniswapV3CallbackData.sol     # Event data structs (V3SwapData, V3MintData, etc.)
│   │   │   │   ├── TickShadow.sol                # Tick tracking (last observed tick)
│   │   │   │   └── HookDataFlagsMod.sol
│   │   │   └── libraries/
│   │   │       └── UniswapV3UniswapV4HookLib.sol # V3 ↔ V4 adaptation utilities
│   │   ├── uniswapV4/                             # V4 reactive (TBD/placeholder)
│   │   │   └── types/
│   │   ├── libraries/
│   │   │   ├── PoolKeyExtMod.sol                 # PoolKey extension utilities
│   │   │   ├── FeeGrowthReaderExt.sol            # Fee growth snapshot extension
│   │   │   └── FeeConcentrationIndexStorageExt.sol
│   │   ├── modules/
│   │   │   └── FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol
│   │   └── types/
│   ├── fci-token-vault/                           # Insurance vault built on FCI metrics
│   │   ├── facets/
│   │   ├── interfaces/
│   │   ├── modules/
│   │   ├── storage/
│   │   ├── libraries/
│   │   ├── types/
│   │   └── tokens/
│   ├── libraries/
│   │   ├── HookUtilsMod.sol                      # Shared utilities (tick sorting, etc.)
│   │   └── ...
│   ├── types/
│   │   ├── BlockCountExt.sol                     # Extended block count (theta weight)
│   │   ├── EpochSnapshot.sol
│   │   ├── RangeSnapshot.sol
│   │   └── ...
│   └── utils/
│       ├── Accounts.sol                          # Test account types
│       ├── Pool.sol                              # Pool helpers
│       ├── TokenPair.sol                         # Token pair utilities
│       ├── Mode.sol                              # Mode constants
│       └── ...
├── test/                                         # Forge test suite
│   ├── fee-concentration-index/                  # Legacy FCI V1 tests
│   │   ├── unit/
│   │   ├── fuzz/
│   │   ├── harness/
│   │   ├── helpers/
│   │   └── ...
│   ├── fee-concentration-index-v2/               # FCI V2 tests
│   │   ├── protocols/
│   │   │   ├── uniswap-v3/
│   │   │   │   ├── integration/
│   │   │   │   │   └── FeeConcentrationIndexV2Full.integration.t.sol  # End-to-end V3 + FCI V2
│   │   │   │   ├── mocks/
│   │   │   │   └── ...
│   │   │   └── uniswapV4/
│   │   ├── differential/
│   │   └── ...
│   ├── reactive-integration/                     # Reactive integration tests
│   │   ├── uniswapV3/
│   │   │   ├── differential/
│   │   │   │   └── FeeConcentrationIndexV4ReactiveV3.diff.t.sol
│   │   │   └── ...
│   │   ├── fork/
│   │   │   ├── FeeConcentrationIndexFull.fork.t.sol
│   │   │   ├── V3FeeGrowthReader.fork.t.sol
│   │   │   └── ...
│   │   ├── kontrol/
│   │   │   └── ... (formal verification specs)
│   │   ├── template/
│   │   │   └── ProtocolAdapterMod.t.sol
│   │   └── ...
│   ├── fci-token-vault/
│   │   ├── integration/
│   │   ├── unit/
│   │   ├── fuzz/
│   │   ├── helpers/
│   │   └── ...
│   ├── simulation/                               # Game theory / backtesting simulations
│   │   ├── CapponiJITSequentialGame.fork.t.sol
│   │   ├── JitGame.t.sol
│   │   └── ...
│   └── utils/
│       ├── Accounts.t.sol
│       ├── Pool.t.sol
│       └── ...
├── foundry-script/                               # Forge deployment scripts
│   ├── deploy/
│   │   ├── DeployFCI.s.sol
│   │   ├── DeployUniswapV3Adapter.s.sol
│   │   └── ...
│   ├── reactive-integration/
│   │   ├── DeployReactiveIntegration.s.sol
│   │   └── ...
│   ├── simulation/
│   ├── types/
│   │   ├── Accounts.sol
│   │   └── ...
│   └── utils/
│       ├── Deployments.sol
│       └── ...
├── research/                                     # Research & analysis (Python + LaTeX)
│   ├── backtest/                                 # Insurance backtest pipeline
│   │   ├── ... (8 modules)
│   ├── econometrics/                             # Duration, hazard, cross-pool analysis
│   │   ├── ... (13 modules)
│   ├── data/
│   │   ├── fixtures/                             # Test data (V3 events, pool snapshots)
│   │   ├── scripts/
│   │   │   ├── fci_oracle.py                    # Oracle for computing FCI metrics
│   │   │   └── hhi_oracle.py                    # HHI computation oracle
│   │   └── queries/
│   ├── model/
│   │   ├── main.tex                              # LaTeX spec
│   │   └── main.pdf
│   ├── notebooks/
│   │   ├── ... (4 Jupyter notebooks)
│   ├── tests/
│   │   ├── ... (114 Python tests)
│   └── scripts/
├── docs/
│   ├── plans/                                    # Branch-specific design docs (see rule below)
│   │   ├── 2026-03-16-uniswap-v3-reactive-edt-flow-3-1-design.md
│   │   └── ... (branch owns only its own plans)
│   ├── src/
│   ├── tester/
│   └── ...
├── specs/
│   ├── ... (feature specification directories)
├── foundry.toml                                  # Forge config (solc 0.8.26, FFI enabled, remappings)
├── Makefile                                      # Build/test commands
├── CLAUDE.md                                     # Development guidelines (enforced branch rules)
└── ...
```

## Directory Purposes

**src/fee-concentration-index-v2/:**
- Purpose: Protocol-agnostic FCI implementation; orchestrates position registration, fee growth tracking, and metrics accumulation
- Contains: Main orchestrator contract, protocol facets (V3, V4), storage definitions, types
- Key files: `FeeConcentrationIndexV2.sol` (orchestrator), `FeeConcentrationIndexStorageV2Mod.sol` (diamond storage)

**src/reactive-integration/:**
- Purpose: Bridges Uniswap V3 events from Reactive Network to FCI state updates on destination chain
- Contains: ReactVM consumer shell, event adapters, callback routing, event decoding
- Key files: `ThetaSwapReactive.sol` (shell), `ReactiveHookAdapter.sol` (destination adapter), `UniswapV3ReactiveMod.sol` (event handling)

**src/reactive-integration/adapters/uniswapV3/:**
- Purpose: V3-specific callback handling; translates V3 Swap/Mint/Burn events to FCI increments
- Contains: Authorization, event-to-state translation, callback routing
- Key files: `ReactiveHookAdapter.sol` (main), `ReactiveHookAdapterStorageMod.sol` (storage), `UniswapV3ReactiveMod.sol` (V3 event logic)

**src/fee-concentration-index-v2/protocols/:**
- Purpose: Protocol-specific facet implementations; pluggable per protocol
- Contains: UniswapV3Facet, NativeUniswapV4Facet, protocol callbacks, protocol libraries
- Key files: `UniswapV3Facet.sol` (V3 adapter), `UniswapV3Callback.sol` (fee growth reader)

**test/fee-concentration-index-v2/:**
- Purpose: Unit and integration tests for FCI V2 orchestrator and facets
- Contains: Protocol adapter tests, integration tests with live pools
- Key files: `test/fee-concentration-index-v2/protocols/uniswap-v3/integration/FeeConcentrationIndexV2Full.integration.t.sol` (end-to-end)

**test/reactive-integration/:**
- Purpose: Tests for reactive integration (event decoding, adapter callbacks, differential testing)
- Contains: Fork tests, differential tests (V4 hook vs. V3 reactive), formal verification specs
- Key files: `test/reactive-integration/fork/FeeConcentrationIndexFull.fork.t.sol`, `test/reactive-integration/uniswapV3/differential/FeeConcentrationIndexV4ReactiveV3.diff.t.sol`

**foundry-script/:**
- Purpose: Deployment and setup scripts
- Contains: Deploy scripts for FCI, adapters, reactive integration; utility scripts
- Key files: `foundry-script/deploy/DeployFCI.s.sol`, `foundry-script/reactive-integration/DeployReactiveIntegration.s.sol`

**research/:**
- Purpose: Econometric analysis, backtesting, oracle implementations
- Contains: Python pipelines (backtest, econometrics), LaTeX spec, Jupyter notebooks, test data
- Key files: `research/model/main.pdf` (spec), `research/data/scripts/fci_oracle.py` (metrics oracle)

**docs/plans/:**
- Purpose: Branch-specific design and planning documents (enforced rule: each branch owns only its plans)
- Contains: Design docs, technical specifications, planning artifacts
- Key files: Named `YYYY-MM-DD-<topic>.md` pattern; related to branch feature only

## Key File Locations

**Entry Points:**

- `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`: Main orchestrator—hook handlers and facet delegation
- `src/reactive-integration/ThetaSwapReactive.sol`: ReactVM consumer—processes reactive logs
- `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol`: Destination adapter—receives callbacks
- `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol`: Protocol adapter for V3

**Configuration:**

- `foundry.toml`: Forge configuration (Solidity version 0.8.26, FFI enabled, remappings)
- `CLAUDE.md`: Development guidelines and branch rules
- `research/model/main.tex`: LaTeX specification

**Core Logic:**

- `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol`: Diamond storage for FCI state
- `src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol`: Protocol facet registry
- `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapterStorageMod.sol`: Adapter storage (fee snapshots)
- `src/reactive-integration/uniswapV3/modules/UniswapV3ReactiveMod.sol`: V3 event decoding and state tracking

**Testing:**

- `test/fee-concentration-index-v2/protocols/uniswap-v3/integration/FeeConcentrationIndexV2Full.integration.t.sol`: End-to-end integration test
- `test/reactive-integration/fork/FeeConcentrationIndexFull.fork.t.sol`: Fork test with live Sepolia pool
- `test/reactive-integration/uniswapV3/differential/FeeConcentrationIndexV4ReactiveV3.diff.t.sol`: Differential test comparing V4 hook vs. V3 reactive

## Naming Conventions

**Files:**

- Contract files: PascalCase (e.g., `FeeConcentrationIndexV2.sol`, `UniswapV3Facet.sol`)
- Module files: PascalCase + `Mod` suffix (e.g., `FeeConcentrationIndexStorageV2Mod.sol`, `UniswapV3ReactiveMod.sol`)
- Type files: PascalCase + optional `Mod` (e.g., `TickRangeMod.sol`, `LiquidityPositionSnapshot.sol`)
- Library files: PascalCase + `Lib` suffix (e.g., `UniswapV3UniswapV4HookLib.sol`, `HookUtilsMod.sol`)
- Test files: PascalCase contract name + test category + `.t.sol` (e.g., `FeeConcentrationIndexV2Full.integration.t.sol`, `JitGame.t.sol`)
- Deployment scripts: PascalCase + `.s.sol` (e.g., `DeployFCI.s.sol`)

**Directories:**

- Protocol-specific: kebab-case (e.g., `uniswap-v3/`, `uniswap-v4/`, `reactive-integration/`)
- Functional: kebab-case (e.g., `fee-concentration-index/`, `fci-token-vault/`)
- Standard structure: lowercase (e.g., `modules/`, `interfaces/`, `libraries/`, `types/`, `storage/`)

**Constants:**

- Storage slot hashes: UPPERCASE + `_SLOT` (e.g., `FCI_V2_STORAGE_SLOT`, `REACTIVE_FCI_STORAGE_SLOT`)
- Event signatures: UPPERCASE (e.g., `V3_SWAP_SIG`, `V3_MINT_SIG`)
- Gas limits: UPPERCASE (e.g., `CALLBACK_GAS_LIMIT = 1_000_000`)
- Protocol flags: UPPERCASE (e.g., `UNISWAP_V3_REACTIVE`, `NATIVE_V4`)

## Where to Add New Code

**New Protocol Adapter:**
- Create `src/fee-concentration-index-v2/protocols/[new-protocol]/` with Facet contract implementing `IFCIProtocolFacet`
- Add storage module: `[NewProtocol]StorageMod.sol`
- Add type definitions: `types/` subdirectory
- Register facet flag in `FlagsRegistry.sol`
- Create integration test: `test/fee-concentration-index-v2/protocols/[new-protocol]/integration/`

**New Reactive Integration:**
- Create `src/reactive-integration/adapters/[protocol]/` (parallel to `uniswapV3/`)
- Create destination adapter inheriting reactive callback pattern (see `ReactiveHookAdapter.sol`)
- Create event decoding module: `modules/[Protocol]ReactiveMod.sol`
- Add event signatures and callbacks: `types/[Protocol]CallbackData.sol`
- Create tests: `test/reactive-integration/[protocol]/`

**New Metrics or Query Functions:**
- Implement as facet extending `IFCIProtocolFacet`—add new interface like `IFCIMetricsFacet.sol`
- Store aggregated data in protocol-specific storage (e.g., `protocolFciStorage`)
- Expose via delegatecall from main orchestrator

**New Type or Abstraction:**
- Define struct in `src/fee-concentration-index-v2/types/` (follow `LiquidityPositionSnapshot.sol` pattern)
- Add encoder/decoder functions if used in module interfaces
- Reference in main orchestrator if needed in data flow

**Test Utilities:**
- Add helpers to `test/utils/` (e.g., new test account type in `Accounts.sol`)
- Add deployment helpers to `foundry-script/utils/`
- Shared harness contracts in test category subdirectory (e.g., `test/fee-concentration-index-v2/harness/`)

**Python Research Code:**
- Add analysis scripts to `research/scripts/` (use Python 3.11+)
- Add test suites to `research/tests/`
- Use frozen dataclasses, free functions (no classes unless necessary), full type hints
- Run via `uhi8/bin/python` (project venv)

## Special Directories

**lib/:**
- Purpose: Git submodules for external dependencies
- Generated: No (committed git submodules)
- Committed: Yes (submodule references)
- Note: DO NOT modify lib/ contents; extend types in `src/types/` with Ext.sol naming convention

**broadcast/:**
- Purpose: Forge deployment artifacts (tx history, receipts)
- Generated: Yes (created by `forge script --broadcast`)
- Committed: No (.gitignore'd)

**out/:**
- Purpose: Forge build artifacts (JSON ABIs, bytecode)
- Generated: Yes (created by `forge build`)
- Committed: No (.gitignore'd)

**uhi8/:**
- Purpose: Python venv for research code
- Generated: Yes (created by `python -m venv uhi8`)
- Committed: No (.gitignore'd)
- Usage: `uhi8/bin/python`, `uhi8/bin/pytest`

**.solidity-language-server/:**
- Purpose: Language server cache
- Generated: Yes (created by editor/LSP)
- Committed: No (.gitignore'd)

**research/data/fixtures/:**
- Purpose: Test data (V3 event logs, pool snapshots, oracle responses)
- Generated: No (committed test fixtures)
- Committed: Yes
- Access: Forge FFI reads via `vm.readFile("research/data/fixtures/...")` (fs_permissions in foundry.toml)

---

*Structure analysis: 2026-03-17*
