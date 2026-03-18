# Architecture

**Analysis Date:** 2026-03-18

## Pattern Overview

**Overall:** Multi-layer Diamond (EIP-2535) with protocol-agnostic hook orchestration

**Key Characteristics:**
- No inheritance (`is`) in production contracts — composition via `delegatecall` and free functions
- Diamond storage pattern with `keccak256`-derived, disjoint slots per facet/namespace
- Protocol dispatch via `bytes2` flag encoded in `hookData` (first 2 bytes)
- All hook logic is `delegatecall`-invoked from an orchestrator; facets contain ONLY protocol behavior
- Free functions (not `library` keyword) used everywhere for reusable logic
- Solidity `^0.8.26`, EVM version `cancun`, compiled via IR (`via_ir = true`)

---

## Layers

**Orchestrator Layer — FCI V2:**
- Purpose: Implements the fee concentration index algorithm for all protocols. Owns hook function signatures. Routes behavioral calls via `delegatecall` to registered protocol facets.
- Location: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`
- Contains: `afterAddLiquidity`, `beforeSwap`, `afterSwap`, `beforeRemoveLiquidity`, `afterRemoveLiquidity`, view functions, facet registration
- Depends on: `IFCIProtocolFacet` (facet interface), diamond storage modules, `LibCall.delegateCallContract`
- Used by: Uniswap V4 PoolManager (hook calls), `UniswapV3Callback` (reactive path), off-chain readers

**Protocol Facet Layer:**
- Purpose: Protocol-specific behavioral implementations (position key derivation, fee growth reads, tick reads, transient storage). Called exclusively via `delegatecall` from the orchestrator.
- Location:
  - `src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol`
  - `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol`
- Contains: Implements `IFCIProtocolFacet` interface methods without `is` inheritance. `onlyDelegateCall` modifier validates context.
- Depends on: `FCIProtocolFacetStorageMod`, `FCIFacetAdminStorageMod`, `FeeConcentrationIndexV2Storage`
- Used by: `FeeConcentrationIndexV2` (via `delegatecall`)

**FCI V1 Layer (legacy, still active):**
- Purpose: Original V4-native-only FCI hook. Runs as a MasterHook diamond facet via `delegatecall`.
- Location: `src/fee-concentration-index/FeeConcentrationIndex.sol`
- Contains: Full hook lifecycle with direct `ProtocolAdapterMod` free-function calls
- Depends on: `FeeConcentrationIndexStorageMod`, `ProtocolAdapterMod`, `FeeGrowthReaderExt`, `FeeConcentrationIndexStorageExt`

**Reactive Integration Layer:**
- Purpose: Bridges Uniswap V3 on-chain events (Sepolia) to FCI V2 (running as a V4 hook) via the Reactive Network. Dual-instance design: one contract runs on Reactive Network (RN), one on ReactVM.
- Location:
  - `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol` — RN-side subscription manager
  - `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol` — Sepolia-side callback receiver
  - `src/fee-concentration-index-v2/modules/ReactiveDispatchMod.sol` — EDT-based dispatch (advanced V2 pattern)
- Contains: `react()` entry point, `registerPool`, `unlockCallbackReactive`, payload mutator calls
- Depends on: `reactive-lib`, `reactive-hooks`, `IUniswapV3Pool`, `V3HookDataLib`
- Used by: Reactive Network callback proxy

**Token Vault Layer:**
- Purpose: ERC-6909 vault issuing paired LONG/SHORT tokens backed 1:1 by USDC collateral. Oracle-based payoff (Model B, transitioning to CFMM Model C when CFMM ships).
- Location: `src/fci-token-vault/`
- Contains:
  - `facets/CollateralCustodianFacet.sol` — deposit/redeem pair
  - `facets/OraclePayoffFacet.sol` — settle/redeemLong/redeemShort (removable Model B facet)
  - `tokens/ERC20WrapperFacade.sol` — ERC-20 wrapper over ERC-6909 positions
- Depends on: `CustodianStorage`, `OraclePayoffStorage`, `ERC6909Lib`, `ReentrancyLib`, `solady/SafeTransferLib`

**Storage Modules:**
- Purpose: Diamond storage namespacing. Each feature owns disjoint slots via `keccak256`. Free functions expose typed storage pointers.
- Key slots:
  - `keccak256("thetaSwap.fci")` → `FeeConcentrationIndexV2Storage` (per-protocol via prefix: `keccak256("thetaSwap.fci.<flag>")`)
  - `keccak256("thetaSwap.fci.registry")` → `FeeConcentrationIndexRegistryStorage` (facet registry)
  - `keccak256("thetaSwap.fci.facetAdmin", flag)` → `FCIFacetAdminStorage` (per-protocol admin)
  - `keccak256("thetaswap.collateral-custodian")` → `CustodianStorage`
  - `keccak256("thetaSwap.protocolAdapter.uniswapV4")` / `...uniswapV3` → `ProtocolAdapterStorage`

**Protocol Adapter Layer:**
- Purpose: `hookData`-aware dispatch bridge for FCI V1 (pre-V2). Reads `bytes calldata hookData` flags to select `fciStorage` (native V4) or `reactiveFciStorage` (reactive path).
- Location: `src/protocol-adapter/`
- Contains: `ProtocolAdapterMod.sol` (9 wrapper free functions), `ProtocolAdapterStorage.sol`, `ProtocolAdapterLib.sol`

**Shared Libraries:**
- Location: `src/libraries/`
- `HookUtilsMod.sol` — `derivePoolAndPosition`, `sortTicks`
- `FeeConcentrationIndexStorageExt.sol` — transient storage read/write for tick cache and removal data
- `FeeGrowthReaderExt.sol` — `getCurrentTick`, `getPositionFeeGrowthInsideLast0`, `getFeeGrowthInside0`
- `PoolKeyExtMod.sol` — `v3PositionKey`

---

## Data Flow

**V4 Native Hook Path (add liquidity):**

1. Uniswap V4 `PoolManager` calls `FeeConcentrationIndexV2.afterAddLiquidity(sender, key, params, hookData)`
2. Orchestrator reads `protocolFlags` from first 2 bytes of `hookData` (empty → `NATIVE_V4 = 0xFFFF`)
3. Looks up registered facet: `fciRegistryStorage().protocolFacets[flags]`
4. For each behavioral step, calls `LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.<fn>, ...))`
5. Facet executes in V2's storage context, reads state from `protocolFciStorage(NATIVE_V4)` slot
6. V2 orchestrator computes `xk` (FCI term) using returned values and emits `FCITermAccumulated`

**V3 Reactive Path (swap event):**

1. Uniswap V3 pool on Sepolia emits `Swap` log
2. Reactive Network ReactVM receives log, `UniswapV3Reactive.react()` is called
3. `react()` emits `IReactive.Callback` event targeting `UniswapV3Callback` on Sepolia with 1M gas
4. Reactive Network callback proxy calls `UniswapV3Callback.unlockCallbackReactive(rvmId, data)`
5. Callback decodes log, constructs V4-shaped `PoolKey` + `hookData` (encoding `UNISWAP_V3_REACTIVE = 0x52FF` flag + pool address + tick data)
6. Callback calls `fci.beforeSwap(...)` then `fci.afterSwap(...)` — same FCI V2 orchestrator
7. Orchestrator dispatches to `UniswapV3Facet` via `delegatecall`, which reads state from `protocolFciStorage(UNISWAP_V3_REACTIVE)` slot

**Tick/Transient State within a Hook Pair:**

- `beforeSwap`: facet stores `tickBefore` via `tstore` (transient storage, keyed by protocol flag)
- `afterSwap`: facet loads `tickBefore` via `tload`, reads `tickAfter` from pool, computes overlap interval

**State Management:**
- Persistent FCI state: `mapping(PoolId => FeeConcentrationState)` inside `FeeConcentrationIndexV2Storage`
- Per-epoch state: `mapping(PoolId => mapping(uint256 epochId => FeeConcentrationState))` in `FeeConcentrationEpochStorage`
- Transient (within-tx): EVM `tstore`/`tload` keyed by `keccak256(abi.encode("thetaSwap.tstore.<flag>", slot))`
- Per-position baseline: `mapping(PoolId => mapping(bytes32 posKey => uint256))` in `FeeConcentrationIndexV2Storage`

---

## Key Abstractions

**`IFCIProtocolFacet` (interface contract):**
- Purpose: Defines the full behavioral API each protocol facet must implement. Acts as the delegatecall boundary between orchestrator and protocol.
- Examples: `src/fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol`
- Pattern: Interface extends `IHooks`. Facets implement without `is` inheritance. Calls always go through orchestrator.

**`bytes2 protocolFlags` (protocol dispatch key):**
- Purpose: Two-byte identifier that selects the correct facet and storage slot. First 2 bytes of `hookData`.
- Defined in: `src/fee-concentration-index-v2/types/FlagsRegistry.sol`
- Values: `NATIVE_V4 = 0xFFFF`, `UNISWAP_V3_REACTIVE = 0x52FF`, `UNISWAP_V3 = 0x5282`, `REACTIVE = 0x007F`
- Pattern: `getProtocolFlagFromHookData(hookData)` → flag → `getProtocolFacet(flag)` + `protocolFciStorage(flag)`

**Diamond Storage Slot Pattern:**
- Purpose: Ensures disjoint, non-colliding storage across facets deployed as separate contracts but sharing one address context via `delegatecall`.
- Pattern: `bytes32 slot = keccak256("<namespace>"); assembly { s.slot := slot }`
- Examples: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol`, `src/fci-token-vault/storage/CustodianStorage.sol`

**`FCIFacetAdminStorage` (per-protocol admin namespace):**
- Purpose: Stores the FCI entry point address, protocol state view, callback address, and registered pool IDs for each protocol. Slot derived per-flag.
- Defined in: `src/fee-concentration-index-v2/modules/FCIFacetAdminStorageMod.sol`
- Pattern: `fciFacetAdminStorage(bytes2 flag)` returns typed storage pointer at `keccak256(abi.encode("thetaSwap.fci.facetAdmin", flag))`

**`FeeConcentrationIndexV2Storage` (core FCI state):**
- Purpose: Holds per-pool `FeeConcentrationState` (accumulatedSum, thetaSum, posCount), `TickRangeRegistryV2` (active ranges + swap counts), and fee growth baselines.
- Defined in: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol`
- Pattern: Separate slot per protocol: `protocolFciStorage(bytes2 flag)` at `keccak256(abi.encode("thetaSwap.fci", flag))`

---

## Entry Points

**`FeeConcentrationIndexV2` (V4 hook + V3 reactive orchestrator):**
- Location: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`
- Triggers: Uniswap V4 PoolManager hook calls (add/remove liquidity, swap); `UniswapV3Callback` direct calls on reactive path
- Responsibilities: Algorithm orchestration, protocol dispatch, FCI term computation, event emission

**`UniswapV3Callback` (reactive bridge):**
- Location: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol`
- Triggers: Reactive Network callback proxy calls `unlockCallbackReactive(rvmSender, data)`
- Responsibilities: Auth check (`authorizedCallers` + `rvmId`), V3 log decode, V4-shaped call construction, FCI V2 invocation

**`UniswapV3Reactive` (reactive subscription manager):**
- Location: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol`
- Triggers: Deployed on Reactive Network. `react(LogRecord)` called by ReactVM per subscribed event.
- Responsibilities: Zero-burn skip guard, `IReactive.Callback` emission to trigger cross-chain callback

**`CollateralCustodianFacet` (vault deposit/redeem):**
- Location: `src/fci-token-vault/facets/CollateralCustodianFacet.sol`
- Triggers: Direct user calls
- Responsibilities: USDC receipt, ERC-6909 LONG/SHORT mint/burn, CEI ordering

**`FCIMetricsFacet` (read-only metrics):**
- Location: `src/fee-concentration-index-v2/FCIMetricsFacet.sol`
- Triggers: Off-chain reads or other contracts
- Responsibilities: Pool-level index values, epoch state, range snapshots (delegated to protocol facet)

---

## Error Handling

**Strategy:** Revert-based with custom errors. No try/catch in production logic (except `NativeUniswapV4Facet.listen` for pool already initialized).

**Patterns:**
- Custom errors defined alongside storage structs: `DepositCapExceeded`, `ZeroAmount` in `CustodianStorage.sol`
- Auth errors: `OnlyReactVM`, `OnlyRN`, `NotAuthorized`, `InvalidRvmId` in reactive contracts
- Guard modifiers use `require(condition, "message")` for `onlyDelegateCall` (not custom error — gas tradeoff)
- Reactive callback proxy failure is silent: proxy emits `CallbackFailure` but still calls `pay()`. `pay()` success does NOT imply callback success.
- Partial remove guard: `if (posLiq != removedLiq) return (selector, BalanceDelta.wrap(0))` — silent skip, not revert

---

## Cross-Cutting Concerns

**Logging:** No dedicated logging library. `emit Event(...)` at significant state transitions. `FCITermAccumulated` is the primary on-chain data event.

**Validation:** Access control is owner-gated (`requireOwner()` free function from `LibOwner`) at admin functions. Hook behavioral functions are gated by `onlyDelegateCall` (checks `address(this) != _self`).

**Authentication:** Reactive callback auth uses `authorizedCallers` mapping (proxy address) + `rvmId` (ReactVM deployer address). Both must match on every `unlockCallbackReactive` call.

**Protocol Flag Dispatch:** `hookData[0:2]` encodes protocol. Missing/empty `hookData` defaults to `NATIVE_V4`. Flags are composable bitmasks for the legacy V1 path (`src/types/HookDataFlagsMod.sol`); for V2, they are full `bytes2` registry keys.

**Transient Storage:** Used within a single transaction to pass `tickBefore` (between `beforeSwap` and `afterSwap`) and removal data (between `beforeRemoveLiquidity` and `afterRemoveLiquidity`). Keyed per protocol flag to avoid collisions between concurrent protocol paths.

---

*Architecture analysis: 2026-03-18*
