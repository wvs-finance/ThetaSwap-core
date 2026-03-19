# FCI Protocol Facet Dispatch — Design Spec

**Date:** 2026-03-14
**Branch:** 006-fci-reactive-integration
**Status:** Draft

## Problem

The FeeConcentrationIndex (FCI) currently supports two protocols via hardcoded dispatch:
- **Uniswap V4** — native hooks, reads from PoolManager, hookData is empty
- **Uniswap V3 Reactive** — callbacks via Reactive Network, hookData composite flags `REACTIVE_FLAG | V3_FLAG = 0x03`

Behavioral functions (`derivePoolAndPosition`, `getCurrentTick`, `getPositionFeeGrowthInsideLast0`, `getFeeGrowthInside0`, `writeCacheTick`, `readCacheTick`) are hardcoded with V4/V3 branching logic. Adding a new protocol (e.g., QuickSwap on Somnia, Uniswap V4 Reactive) requires modifying the FCI core and all behavioral dispatch files.

## Goal

Make the FCI a **protocol-agnostic dispatcher** that delegates entire hook callbacks to per-protocol facets via a single delegatecall. Each protocol deploys three components that plug into the FCI without modifying its core.

## Implementation Strategy

The new dispatch logic is implemented in `src/fee-concentration-index-v2/` as a **parallel implementation**. The existing `src/fee-concentration-index/` remains untouched. A **differential test suite** validates that FCI V2 produces identical FCI state as V1 for Uniswap V4 pools. Passing differential tests is the green flag for migration.

## Architecture

### Flag Dispatch Model

The existing codebase uses **bitmask composition** for flags: `REACTIVE_FLAG (0x01)`, `V3_FLAG (0x02)`, checked via bitwise AND. This design shifts to **exact-byte-key dispatch**: `protocolFacets[hookData[0]]` is a direct mapping lookup, not a bitmask check.

This is intentional. Each composite flag combination (e.g., `V3 | REACTIVE = 0x03`, `V4 | REACTIVE = 0x01`) represents a distinct protocol identity that requires its own facet. 


The bitmask helpers (`isReactive()`, `isV3()`) remain available within facet implementations for internal use, but the FCI dispatcher uses exact-key lookup.

Known protocol flag assignments:
- `0x00` — Uniswap V4 (inlined, no delegatecall)
- `0x01` — Uniswap V4 Reactive (future)
- `0x03` — Uniswap V3 Reactive

### The Three Protocol Components

Each protocol that wants an FCI oracle deploys three contracts:

#### 1. FCIProtocolFacet (origin chain)

Per-protocol singleton deployed once. Contains:

- **Own diamond storage slot**: Derived from protocol flag, isolating FCI state per protocol. 
Two protocols with the same PoolId cannot collide because their state lives in different slots.
- **Transient storage**: Per-field `tstore`/`tload` at computed slot offsets (not struct-based — Solidity does not support struct-at-slot for transient storage).
- **All behavioral functions** (renamed from V1 to be facet-scoped — some stay the same, some change):
  - `positionKey(hookData, sender, params)` → replaces `derivePoolAndPosition()`
  - `latestPositionFeeGrowthInside(hookData, poolId)` → replaces `getPositionFeeGrowthInsideLast0()`
  - `addPositionInRange(hookData, poolId, positionKey, tickRange, posLiquidity)` → replaces `registerPosition()`
  - `removePositionInRange(hookData, poolKey, positionKey, posLiquidity)` → replaces `deregisterPosition()`
  - `currentTick(hookData)` → replaces `getCurrentTick()`
  - `poolRangeFeeGrowthInside(hookData, poolId, currentTick, tickRange)` → replaces `getFeeGrowthInside0()`
  - `setFeeGrowthBaseline(hookData, poolId, positionKey, feeGrowth)` — unchanged
  - `deleteFeeGrowthBaseline(hookData, poolKey, positionKey)` — unchanged
  - `incrementPosCount(hookData, poolId)` — unchanged
  - `decrementPosCount(hookData, poolId)` — unchanged
  - `tstoreTick(hookData, tick)` → replaces `writeCacheTick()`
  - `tloadTick(hookData)` → replaces `readCacheTick()`
  - `tstoreRemovalData(hookData, feeLast, posLiquidity, rangeFeeGrowth)` → replaces `writeCacheRemovalData()`
  - `tloadRemovalData(hookData)` → replaces `readCacheRemovalData()`
  - `addStateTerm(hookData, poolKey, blockLifetime, xSquaredQ128)` — unchanged
  - `addEpochTerm(hookData, poolKey, blockLifetime, xSquaredQ128)` — unchanged
- **Full hook handler implementations**: `afterAddLiquidity`, `beforeSwap`, `afterSwap`, `beforeRemoveLiquidity`, `afterRemoveLiquidity` — each implementing the complete hook logic (behavioral reads + FCI state accumulation) for that protocol.
- **Pool registry**: Tracks which pools this facet handles.
- **Callback reference**: Stores its `IFCIUnlockCallback` address. 
Only accepts delegatecalls originating from this callback (security boundary).
- **Own protocol state reader**: Each facet stores its own `IProtocolStateView` reference (e.g., PoolManager for V4, V3Pool for V3). Facets must **never** call `_poolManager()` from `FeeConcentrationIndexStorageMod` — that reads from the V4 storage slot and would return incorrect state for non-V4 protocols.

**Important**: `listen()` is called **directly** on the facet (not delegatecalled from the FCI). It is separated into `IFCIProtocolAdmin` interface, distinct from `IFCIProtocolHooks` which contains the delegatecall targets.

##### FCIProtocolFacet Storage

```solidity
struct FCIProtocolFacetStorage {
    EnumerableSet.Bytes32Set poolIds;        // registered pools
    IFeeConcentrationIndex fci;              // the FCI dispatcher
    IProtocolStateView protocolStateView;    // protocol-specific state reader (NOT _poolManager())
    IFCIUnlockCallback protocolCallback;     // authorized callback
}
```

##### Storage Slot Derivation

```solidity
bytes1 constant PROTOCOL_FLAG = ...; // e.g., 0x03 for V3|REACTIVE

function protocolFciStorage() pure returns (FeeConcentrationIndexStorage storage $) {
    bytes32 position = keccak256(abi.encode("thetaSwap.fci", PROTOCOL_FLAG));
    assembly ("memory-safe") { $.slot := position }
}

function protocolEpochFciStorage() pure returns (FeeConcentrationEpochStorage storage $) {
    bytes32 position = keccak256(abi.encode("thetaSwap.fci.epoch", PROTOCOL_FLAG));
    assembly ("memory-safe") { $.slot := position }
}
```

##### Transient Storage

Transient storage uses per-field `tstore`/`tload` with computed slot offsets, matching the existing pattern in `FeeConcentrationIndexStorageMod.sol` which uses four separate slots (`TICK_BEFORE_SLOT`, `FEE_GROWTH_LAST0_SLOT`, `POS_LIQUIDITY_SLOT`, `RANGE_FEE_GROWTH0_SLOT`).

Each protocol facet derives its transient slots from a base:

```solidity
bytes32 constant TRANSIENT_BASE = keccak256(abi.encode("thetaSwap.fci.transient", PROTOCOL_FLAG));

// Per-field slots offset from base
bytes32 constant TICK_BEFORE_SLOT     = TRANSIENT_BASE;
bytes32 constant FEE_GROWTH_LAST_SLOT = bytes32(uint256(TRANSIENT_BASE) + 1);
bytes32 constant POS_LIQUIDITY_SLOT   = bytes32(uint256(TRANSIENT_BASE) + 2);
bytes32 constant RANGE_FEE_GROWTH_SLOT = bytes32(uint256(TRANSIENT_BASE) + 3);

function writeCacheTick(int24 tick) {
    bytes32 slot = TICK_BEFORE_SLOT;
    assembly { tstore(slot, tick) }
}

function readCacheTick() view returns (int24 tick) {
    bytes32 slot = TICK_BEFORE_SLOT;
    assembly { tick := tload(slot) }
}
```

##### V3 Reactive Facet: Storage Slot Compatibility

**Pre-existing slot split in the codebase:** Two different `reactiveFciStorage()` functions exist, pointing at different slots:

| File | Slot String | Used By |
|------|------------|---------|
| `FeeConcentrationIndexStorageMod.sol` | `keccak256("thetaSwap.fci.reactive")` | FCI view functions (`getIndex`, `getDeltaPlus` with `reactive=true`), `ProtocolAdapterLib.fciStorageFor()` |
| `ReactiveHookAdapterStorageMod.sol` | `keccak256("ReactiveHookAdapter.fci.storage")` | `ReactiveHookAdapter` — the contract that actually writes V3 FCI state on live Sepolia deployment |

The `ReactiveHookAdapter` writes to `"ReactiveHookAdapter.fci.storage"`, but the FCI view functions read from `"thetaSwap.fci.reactive"`. This means the FCI's `getDeltaPlus(key, reactive=true)` currently reads from a **different slot** than where the adapter writes — a pre-existing inconsistency that must be resolved as part of this migration.

The new V3 protocol facet must use the slot where **production state actually lives** — `keccak256("ReactiveHookAdapter.fci.storage")`:

```solidity
// In UniswapV3FCIProtocolFacet:
// Use the slot where ReactiveHookAdapter actually writes V3 FCI state
bytes32 constant V3_FCI_SLOT = keccak256("ReactiveHookAdapter.fci.storage");

function protocolFciStorage() pure returns (FeeConcentrationIndexStorage storage $) {
    assembly ("memory-safe") { $.slot := V3_FCI_SLOT }
}
```

The FCI V2's view function routing (`_protocolFciStorage(0x03)`) must also point to this slot:

```solidity
function _protocolFciStorage(bytes1 flags) internal pure returns (FeeConcentrationIndexStorage storage $) {
    bytes32 position = flags == bytes1(0x03)
        ? keccak256("ReactiveHookAdapter.fci.storage")  // V3: production slot
        : keccak256(abi.encode("thetaSwap.fci", flags));
    assembly ("memory-safe") { $.slot := position }
}
```

New protocols (QuickSwap, etc.) use the derived pattern `keccak256("thetaSwap.fci", PROTOCOL_FLAG)`.

#### 2. FCIProtocolCallback (origin chain)

Implements `IFCIUnlockCallback`. Receives reactive callbacks and routes them to the FCI's hook functions.

```solidity
interface IFCIUnlockCallback is IUnlockCallback {
    function unlockReactiveCallback(address rvmId, bytes calldata data) external;
}
```

- Receives event data from the Reactive Network callback proxy
- Decodes protocol-specific event data
- Encodes hookData with the protocol's flag byte in `hookData[0]`
- Calls the FCI's hook functions (e.g., `afterAddLiquidity`) with the encoded hookData
- The FCI reads `hookData[0]`, looks up the facet, delegatecalls — which lands back in the facet's hook handler

**Note:** The facet can also serve as the callback (single contract) if the protocol doesn't need separation.

#### 3. FCIProtocolSocket (Reactive Network)

Implements `IReactive`. Lives on the Reactive Network, subscribes to protocol events on origin chains.

```solidity
interface IFCIProtocolSocket is IReactive {
    function listenPool(uint256 chainId, PoolKey calldata key) external;
    function unListenPool(uint256 chainId, PoolKey calldata key) external;
}
```

- Picks up `PoolAdded` event from the facet's `listen()` call → auto-registers pool subscriptions
- Routes protocol events (Swap, Mint, Burn) back to the callback via Reactive's callback proxy
- Manages subscription lifecycle and debt/funding

### FCI Dispatcher Changes

The FCI V2 contract (`FeeConcentrationIndexV2.sol` in `src/fee-concentration-index-v2/`) gains:

#### New Storage: FeeConcentrationIndexRegistryStorage

The `protocolFacets` mapping lives in a **separate** struct and diamond slot — NOT in `FeeConcentrationIndexStorage`. This avoids protocol facets inheriting an unused mapping in their storage layout (since each facet reuses the `FeeConcentrationIndexStorage` struct for its own FCI state).

```solidity
struct FeeConcentrationIndexRegistryStorage {
    mapping(bytes1 => address) protocolFacets; // flags → delegatecall target
}

bytes32 constant FCI_REGISTRY_SLOT = keccak256("thetaSwap.fci.registry");

function fciRegistryStorage() pure returns (FeeConcentrationIndexRegistryStorage storage $) {
    bytes32 slot = FCI_REGISTRY_SLOT;
    assembly ("memory-safe") { $.slot := slot }
}
```

#### Registration Functions

```solidity
function setProtocolFacet(bytes1 flags, address facet) external;
function getProtocolFacet(bytes1 flags) external view returns (address);
```

Access control enforced at the diamond facet level (MasterHook `onlyOwner` or initialization guard).

#### Hook Dispatch Pattern

Each hook function gains a dispatch preamble:

```solidity
function afterAddLiquidity(
    address sender,
    PoolKey calldata key,
    ModifyLiquidityParams calldata params,
    BalanceDelta delta0,
    BalanceDelta delta1,
    bytes calldata hookData
) external virtual returns (bytes4, BalanceDelta) {
    // ── V4 fast path: empty hookData = native V4, no delegatecall ──
	
    if (hookData.length == 0) {
        // ... existing V4 inlined logic (unchanged) ...
        return (IHooks.afterAddLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── Protocol dispatch: delegatecall to registered facet ──
    bytes1 flags = hookData[0];
    address facet = fciRegistryStorage().protocolFacets[flags];
    require(facet != address(0), "FCI: unknown protocol");
    (bool ok, bytes memory ret) = facet.delegatecall(msg.data);
    require(ok, "FCI: facet delegatecall failed");
    return abi.decode(ret, (bytes4, BalanceDelta));
}
```

This pattern applies to all five hook functions: `afterAddLiquidity`, `beforeSwap`, `afterSwap`, `beforeRemoveLiquidity`, `afterRemoveLiquidity`.

**Note on `beforeRemoveLiquidity`:** The existing V4 implementation calls `derivePoolAndPosition(sender, key, params)` — a 3-argument overload that does NOT take hookData and hardcodes V4 position key derivation. This is V4-specific behavior. Protocol facets implement `beforeRemoveLiquidity` with their own position key derivation that reads from hookData. The V4 fast path retains the 3-argument call unchanged.

### Interfaces (Split: Admin vs Hooks)

Two separate interfaces prevent mixing direct-call and delegatecall functions:

```solidity
/// @dev Called directly on the facet contract (not via delegatecall)
interface IFCIProtocolAdmin {
    function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey);
}

/// @dev Called via delegatecall from FCI dispatcher
interface IFCIProtocolHooks {
    function afterAddLiquidity(address, PoolKey calldata, ModifyLiquidityParams calldata, BalanceDelta, BalanceDelta, bytes calldata) external returns (bytes4, BalanceDelta);
    function beforeSwap(address, PoolKey calldata, SwapParams calldata, bytes calldata) external returns (bytes4, BeforeSwapDelta, uint24);
    function afterSwap(address, PoolKey calldata, SwapParams calldata, BalanceDelta, bytes calldata) external returns (bytes4, int128);
    function beforeRemoveLiquidity(address, PoolKey calldata, ModifyLiquidityParams calldata, bytes calldata) external returns (bytes4);
    function afterRemoveLiquidity(address, PoolKey calldata, ModifyLiquidityParams calldata, BalanceDelta, BalanceDelta, bytes calldata) external returns (bytes4, BalanceDelta);
}
```

### PoolId Collision Resolution

Different protocols may produce the same PoolId (e.g., two DEXes with identical token pairs and fee tiers). This is resolved by **storage slot isolation**: each protocol's FCI state lives in its own diamond storage slot, so the same PoolId maps to different storage locations for different protocols.

### View Function Routing

The FCI's view functions (`getDeltaPlus`, `getIndex`, etc.) need updating. Since facet storage is only accessible via delegatecall (the facet's own contract storage is empty), view functions **cannot** use `staticcall` to read from the facet. Two options:

**Option 1 (recommended): FCI computes the protocol slot directly.**
The FCI knows the slot formula and can read directly without calling the facet:

```solidity
function getDeltaPlus(PoolKey calldata key, bytes1 flags) external view returns (uint128) {
    if (flags == 0x00) {
        return fciStorage().fciState[PoolIdLibrary.toId(key)].deltaPlus();
    }
    // Read directly from the protocol's storage slot
    FeeConcentrationIndexStorage storage $ = _protocolFciStorage(flags);
    return $.fciState[PoolIdLibrary.toId(key)].deltaPlus();
}

function _protocolFciStorage(bytes1 flags) internal pure returns (FeeConcentrationIndexStorage storage $) {
    // V3 reactive uses legacy slot for backward compat
    bytes32 position = flags == bytes1(0x03)
        ? keccak256("ReactiveHookAdapter.fci.storage")
        : keccak256(abi.encode("thetaSwap.fci", flags));
    assembly ("memory-safe") { $.slot := position }
}
```

**Option 2: Delegatecall in static context.** Use `delegatecall` from a view function. Solidity allows this but the facet must also be `view`-safe.

Option 1 is simpler and avoids the delegatecall overhead for reads.

**Backward compatibility:** The existing `getDeltaPlus(PoolKey, bool reactive)` signature is preserved. `reactive=true` maps to `flags=0x03`. A new overload `getDeltaPlus(PoolKey, bytes1 flags)` serves arbitrary protocols.

The same pattern applies to `getDeltaPlusEpoch`. The existing V1 has a TODO: `// TODO(chunk-3): reactive ? reactiveEpochFciStorage() : epochFciStorage()`. V2 resolves this by routing epoch reads through `_protocolEpochFciStorage(flags)`, with `getDeltaPlusEpoch(PoolKey, bool reactive)` preserved for backward compat and a new `getDeltaPlusEpoch(PoolKey, bytes1 flags)` overload for arbitrary protocols.

### Registration + Listen Flow

```
PRE-CONDITIONS:
  Protocol A deploys:
    1. FCIProtocolFacet (origin chain) — behavioral logic + hook handlers
    2. FCIProtocolCallback (origin chain) — receives reactive callbacks
    3. FCIProtocolSocket (Reactive Network) — subscribes to events

REGISTRATION (one-time, admin):
  1. FCI.setProtocolFacet(flags_A, address(facet_A))
  2. facet_A stores reference to callback_A

LISTEN (per pool):
  Origin chain:
    facet_A.listen(poolRpt_i, funding_i)
      → converts poolRpt to PoolKey (with FCI as IHooks)
      → addPool(poolId_i) in facet storage
      → emits PoolAdded(address(facet_A), address(callback_A), poolId_i, flags_A)

  Reactive Network:
    socket_A.react(PoolAdded event)
      → listenPool(chainId, pool_i) — subscribes to protocol A events for pool_i

ONGOING (per event):
  Protocol event on origin chain
    → Reactive socket picks it up
    → Callback proxy delivers to callback_A on origin chain
    → callback_A encodes hookData with flags_A in byte 0
    → callback_A calls FCI.afterAddLiquidity(..., hookData)
    → FCI reads hookData[0] = flags_A
    → FCI delegatecalls to facet_A
    → facet_A executes full hook logic, writes to protocol-scoped storage

POST-CONDITIONS:
  - FCI.getDeltaPlus(poolKey_i, flags_A) returns delta+ from protocol A's storage
  - Protocol A LPs can access vault services via OraclePayoffMod
```

### Impact on Existing Code

#### Existing FeeConcentrationIndex.sol — NOT Modified

The V1 implementation in `src/fee-concentration-index/` stays exactly as-is. It remains the production implementation until differential tests validate V2.

#### New Directory: src/fee-concentration-index-v2/

Contains the V2 FCI with dispatch preamble in all 5 hook functions, `protocolFacets` mapping, and registration functions. V4 inlined path is identical to V1.

#### New Files

| File | Description |
|------|-------------|
| `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol` | V2 FCI with protocol dispatch |
| `src/fee-concentration-index-v2/modules/FeeConcentrationIndexV2StorageMod.sol` | V2 storage (adds protocolFacets mapping) |
| `src/reactive-integration/template/interfaces/IFCIProtocolAdmin.sol` | Admin interface (listen, direct calls) |
| `src/reactive-integration/template/interfaces/IFCIProtocolHooks.sol` | Hook interface (delegatecall targets) |
| `src/reactive-integration/template/interfaces/IFCIUnlockCallback.sol` | Callback interface extending IUnlockCallback |
| `src/reactive-integration/template/interfaces/IFCIProtocolSocket.sol` | Reactive Network socket interface |
| `src/reactive-integration/template/modules/FCIProtocolFacetStorageMod.sol` | Storage primitives for protocol facets |
| `src/reactive-integration/uniswapV3/UniswapV3FCIProtocolFacet.sol` | V3 reactive implementation |
| `src/reactive-integration/uniswapV3/UniswapV3FCICallback.sol` | V3 reactive callback (may merge with facet) |
| `test/fee-concentration-index-v2/differential/` | Differential tests: V2 vs V1 |

#### Files NOT Modified

- `src/fee-concentration-index/` — entire V1 directory untouched
- `ProtocolAdapterMod.sol` — V4 path still uses it; non-V4 protocols bypass it via full-hook delegatecall
- `ProtocolAdapterStorage.sol` — vault adapter layer, orthogonal to dispatch
- `OraclePayoffMod.sol` — reads via `ProtocolAdapterLib.getDeltaPlusEpoch()`, adapter slot indirection still works
- All vault code — untouched

### Slot Collision Analysis

Existing diamond storage slots:

| Slot String | Owner |
|-------------|-------|
| `"thetaSwap.fci"` | FCI V4 state |
| `"thetaSwap.fci.reactive"` | FCI V3 view functions (reads only — see slot split note above) |
| `"ReactiveHookAdapter.fci.storage"` | ReactiveHookAdapter V3 FCI state (production writes) |
| `"ReactiveHookAdapter.v3.storage"` | V3 adapter fee growth snapshots |
| `"thetaSwap.fci.epoch"` | FCI epoch state |
| `"thetaSwap.protocolAdapter.uniswapV4"` | Protocol adapter V4 |
| `"thetaSwap.protocolAdapter.uniswapV3"` | Protocol adapter V3 |
| `"thetaswap.oracle-payoff"` | Oracle payoff |
| `"thetaswap.collateral-custodian"` | Collateral custodian |

New slots:
- `keccak256("thetaSwap.fci.registry")` — FCI V2 registry (protocolFacets mapping). Separate from `FeeConcentrationIndexStorage` so facets don't inherit unused fields.
- `keccak256(abi.encode("thetaSwap.fci", PROTOCOL_FLAG))` — per-protocol FCI state. Since `abi.encode` produces a 64-byte input (32 bytes string + 32 bytes flag), this cannot collide with `keccak256("thetaSwap.fci")` which hashes a 14-byte string.
- `keccak256(abi.encode("thetaSwap.fci.epoch", PROTOCOL_FLAG))` — per-protocol epoch state. Same non-collision argument.
- V3 reactive facet reuses existing `keccak256("ReactiveHookAdapter.fci.storage")` for backward compatibility with production state.

### Differential Testing Strategy

The V2 implementation is validated via differential tests before migration:

1. **V4 Differential Test**: Run identical sequences of `afterAddLiquidity`, `beforeSwap`, `afterSwap`, `beforeRemoveLiquidity`, `afterRemoveLiquidity` against both V1 and V2 FCI with empty hookData (V4 path). Assert identical FCI state (`deltaPlus`, `thetaSum`, `removedPosCount`, `indexA`) after each operation.

2. **V3 Differential Test**: Run the same V3 reactive event sequences through both the existing `ReactiveHookAdapter` (V1 path) and the new `UniswapV3FCIProtocolFacet` + V2 FCI dispatch path. Assert identical FCI state.

3. **Fuzz Differential Test**: Fuzz-test random sequences of hook callbacks against both V1 and V2, asserting state equivalence.

Passing all differential tests is the **green flag for migration** — swapping V1 for V2 in the MasterHook diamond.

### Epoch Storage

Each protocol facet has its own epoch storage slot: `keccak256(abi.encode("thetaSwap.fci.epoch", PROTOCOL_FLAG))`. The facet's hook handlers call `addEpochTerm()` writing to their protocol-scoped epoch slot. The FCI's `getDeltaPlusEpoch()` view function routes to the correct epoch slot based on the `flags` parameter, using the same direct-slot-read pattern as `getDeltaPlus()`.

### Migration Path

The existing V3 reactive path (`ReactiveHookAdapter` + `ThetaSwapReactive`) currently bypasses the FCI entirely — it has its own adapter contract with direct FCI storage writes. Under this design:

1. Deploy `UniswapV3FCIProtocolFacet` — contains V3 behavioral logic from `ReactiveHookAdapter`, `FeeGrowthReaderExt`, and `HookDataFlagsMod`. Uses existing `keccak256("ReactiveHookAdapter.fci.storage")` slot for backward compat with production state.
2. Register at `setProtocolFacet(0x03, address(v3Facet))`
3. The existing `ReactiveHookAdapter` becomes the `IFCIUnlockCallback` (or is replaced by a thinner callback)
4. The existing `ThetaSwapReactive` becomes the `IFCIProtocolSocket` (or is replaced)

The V4 path requires zero changes — empty hookData bypasses dispatch entirely.

### Resolved Design Decisions

1. **Facet ≠ Callback**: Separate contracts. The facet implements `IFCIProtocolHooks` (delegatecall targets). The callback implements `IFCIUnlockCallback` (receives reactive events, calls FCI). Separation of concerns.

2. **View function routing**: Option 1 — FCI computes protocol storage slot directly and reads without calling the facet. No delegatecall overhead for reads.

3. **Epoch storage**: Per-protocol isolated slots. Each facet's `addEpochTerm()` writes to its own epoch slot.

4. **Interface split**: `IFCIProtocolAdmin` for direct calls (`listen()`), `IFCIProtocolHooks` for delegatecall targets (hook handlers). Prevents accidentally direct-calling a delegatecall target or vice versa.

5. **V4 fast path**: Empty hookData = V4, inlined logic, no delegatecall. Saves ~2600 gas per hook callback on the hot path.

6. **Bitmask → exact-byte-key**: The dispatcher uses `protocolFacets[hookData[0]]` exact lookup, not bitmask checks. Each composite flag combination is a distinct protocol identity.
