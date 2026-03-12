# Protocol Adapter Storage — Design Spec

**Date**: 2026-03-12
**Branch**: 004-fci-token-vault
**Status**: Approved

## Problem

Three areas of the codebase carry redundant or scattered protocol-awareness:

1. **FeeConcentrationIndexStorageMultiProtocolReactiveExtMod** — every wrapper function has an inline ternary (`isUniswapV3Reactive(hookData) ? reactiveFciStorage() : fciStorage()`) that must be duplicated per function and extended per protocol.
2. **OraclePayoffStorage** — stores a full `PoolKey` (~5 storage slots) plus a `reactive` boolean, duplicating information that logically belongs to the adapter layer.
3. **ReactiveHookAdapterStorageMod** — V3-specific adapter storage is a one-off pattern. Each future protocol (V2, Balancer) would need its own bespoke storage module.

## Solution

A per-protocol adapter storage pattern with centralized dispatch.

### Core Struct

```solidity
struct ProtocolAdapterStorage {
    address protocolState;   // V4: IPoolManager, V3: IUniswapV3Factory — cast at call site
    IHooks  fciEntryPoint;   // typed IHooks for assignment compat with PoolKey.hooks; cast to IFeeConcentrationIndex at call sites
    PoolKey poolKey;          // V4-shaped PoolKey (V3 adapters construct via fromV3Pool). For V4 native, consumed only by vault oracle path — hook callbacks receive PoolKey as parameter
    bool    reactive;         // per-pool flag — true for V3, also true for V4 pools that missed initial hook registration
}
```

One instance per protocol, each at a distinct diamond slot:

```solidity
bytes32 constant V4_ADAPTER_SLOT = keccak256("thetaSwap.protocolAdapter.uniswapV4");
bytes32 constant V3_ADAPTER_SLOT = keccak256("thetaSwap.protocolAdapter.uniswapV3");
```

Generic accessor parameterized by slot, plus convenience aliases (all free functions, following project SCOP convention — no `library` keyword):

```solidity
function protocolAdapterStorage(bytes32 slot) pure returns (ProtocolAdapterStorage storage $) {
    assembly { $.slot := slot }
}

function v4AdapterStorage() pure returns (ProtocolAdapterStorage storage $) {
    return protocolAdapterStorage(V4_ADAPTER_SLOT);
}

function v3AdapterStorage() pure returns (ProtocolAdapterStorage storage $) {
    return protocolAdapterStorage(V3_ADAPTER_SLOT);
}
```

### File Layout

```
src/reactive-integration/template/
├── storage/ProtocolAdapterStorage.sol    # struct, slot constants, accessors
├── libraries/ProtocolAdapterLib.sol      # fciStorageFor(), getDeltaPlusEpoch(), getDeltaPlus()
└── modules/ProtocolAdapterMod.sol        # 9 hookData-aware wrappers + initializeAdapter()
```

**Slot collision analysis**: New slot strings (`thetaSwap.protocolAdapter.uniswapV4`, `thetaSwap.protocolAdapter.uniswapV3`) are disjoint from all existing diamond storage slots:

- FCI: `thetaSwap.fci`, `thetaSwap.fci.reactive`, `thetaSwap.fci.epoch`, `thetaSwap.fci.epoch.reactive`
- Vault: `thetaswap.oracle-payoff`, `thetaswap.collateral-custodian`, `thetaswap.reentrancy-guard`
- Tokens: `compose.erc20`, `compose.erc6909`, `thetaswap.erc20-wrapper`
- Reactive: `ReactiveHookAdapter.fci.storage`

New slots follow the `thetaSwap.*` camelCase convention established by the FCI module. The lowercase `thetaswap.*` variants are a legacy pattern in the vault module. Verified by distinct keccak256 preimages — no collision possible. Transient storage slots (`thetaSwap.fci.tickBefore`, etc.) are not at risk since they occupy a separate namespace.

The `template/` directory holds protocol-agnostic primitives. Protocol-specific fill-outs live in their own directories (e.g., `uniswapV3/`, `uniswapV2/`, `balancer/`).

## Components

### ProtocolAdapterLib

`src/reactive-integration/template/libraries/ProtocolAdapterLib.sol`

All functions below are free functions (not Solidity `library` members), consistent with the project's SCOP convention.

**FCI storage dispatch** — replaces ext mod inline ternaries:

```solidity
function fciStorageFor(bytes calldata hookData) pure returns (FeeConcentrationIndexStorage storage $) {
    if (isUniswapV3Reactive(hookData)) {
        return reactiveFciStorage();
    }
    return fciStorage();
}
```

Extensible: new protocols add branches here. Single place to update.

**Oracle reads** — encapsulates IFeeConcentrationIndex calls:

```solidity
function getDeltaPlusEpoch(ProtocolAdapterStorage storage $) view returns (uint128) {
    return IFeeConcentrationIndex(address($.fciEntryPoint))
        .getDeltaPlusEpoch($.poolKey, $.reactive);
}

function getDeltaPlus(ProtocolAdapterStorage storage $) view returns (uint128) {
    return IFeeConcentrationIndex(address($.fciEntryPoint))
        .getDeltaPlus($.poolKey, $.reactive);
}
```

> `getDeltaPlusEpoch` is consumed by `oraclePoke()`. `getDeltaPlus` is provided for script/test callers (`CompareDeltaPlus.s.sol`, `FeeConcentrationIndexBuilder.s.sol`) — migration of those callers is future work.

### ProtocolAdapterMod

`src/reactive-integration/template/modules/ProtocolAdapterMod.sol`

Replaces `FeeConcentrationIndexStorageMultiProtocolReactiveExtMod`. Same function signatures — takes `bytes calldata hookData`, dispatches through `ProtocolAdapterLib.fciStorageFor(hookData)` instead of inline ternaries.

9 wrapper functions migrated:
- `registerPosition`
- `incrementPosCount`, `decrementPosCount`
- `incrementOverlappingRanges`
- `deregisterPosition`
- `addStateTerm`
- `setFeeGrowthBaseline`, `getFeeGrowthBaseline`, `deleteFeeGrowthBaseline`

Additionally exposes a generic initialization function:

```solidity
function initializeAdapter(
    bytes32 slot,
    address protocolState,
    IHooks fciEntryPoint,
    PoolKey calldata poolKey,
    bool reactive
) {
    ProtocolAdapterStorage storage $ = protocolAdapterStorage(slot);
    $.protocolState = protocolState;
    $.fciEntryPoint = fciEntryPoint;
    $.poolKey = poolKey;
    $.reactive = reactive;
}
```

**Access control**: `initializeAdapter` is a free function callable by any facet in the diamond. Access control is enforced at the facet level (diamond proxy `onlyOwner` or initialization guard), not within the free function itself. This matches the existing pattern where `getCustodianStorage()` and `getOraclePayoffStorage()` are also unguarded free functions.

## OraclePayoffStorage Simplification

**Before** (actual `src/fci-token-vault/storage/OraclePayoffStorage.sol`):

```solidity
struct OraclePayoffStorage {
    uint160 sqrtPriceStrike;
    uint160 sqrtPriceHWM;
    uint256 expiry;
    bool    settled;
    uint256 longPayoutPerToken; // Q96-scaled
    PoolKey poolKey;            // ~5 storage slots
    bool    reactive;
}
```

**After:**

```solidity
struct OraclePayoffStorage {
    uint160 sqrtPriceStrike;
    uint160 sqrtPriceHWM;
    uint256 expiry;
    bool    settled;
    uint256 longPayoutPerToken; // Q96-scaled
    bytes32 adapterSlot;        // references ProtocolAdapterStorage instance
}
```

**OraclePayoffMod.oraclePoke()** changes from:

```solidity
uint128 deltaPlus = IFeeConcentrationIndex(address(os.poolKey.hooks))
    .getDeltaPlusEpoch(os.poolKey, os.reactive);
```

To:

```solidity
ProtocolAdapterStorage storage adapter = protocolAdapterStorage(os.adapterSlot);
uint128 deltaPlus = getDeltaPlusEpoch(adapter);
```

Vault deployers pass `bytes32 adapterSlot` (e.g., `V3_ADAPTER_SLOT`) at initialization instead of `PoolKey + reactive`.

## Migration Strategy

### Option C → toward A

Current approach (Option C): hookData flags stay for backward compatibility. `ProtocolAdapterLib.fciStorageFor(bytes calldata hookData)` centralizes dispatch but still reads flags. Future migration (Option A): callers pass `ProtocolAdapterStorage storage $` directly, hookData flags deprecated.

### Deprecated Files

**FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol** — converted to a re-export shim with deprecation header:

```solidity
// DEPRECATED: This module is superseded by ProtocolAdapterMod.
// Import path: @protocol-adapter/modules/ProtocolAdapterMod.sol
// This file re-exports for backward compatibility. Remove once all callers migrate.
```

Re-exports all 9 functions from `ProtocolAdapterMod` so external importers (`ReactiveHookAdapter.sol`, reactive-integration tests) continue working without changes.

**Primary callers migrate immediately**: `FeeConcentrationIndex.sol` and `FeeConcentrationIndexForkHarness.sol` update their import paths to `@protocol-adapter/modules/ProtocolAdapterMod.sol`. The shim exists only for callers that are out of scope (see Untouched Files).

### Untouched Files

These are out of scope — migrated in a follow-up V3 fill-out work package:

- `ReactiveHookAdapter.sol` — keeps its own `onV3Swap`, `onV3Mint`, `onV3Burn` callbacks
- `ReactiveHookAdapterStorageMod.sol` — keeps its own storage pattern
- `HookDataFlagsMod.sol` — flags stay for Option C compatibility
- `FeeConcentrationIndexStorageExt.sol` — transient cache wrappers stay as-is
- `FeeGrowthReaderExt.sol` — fee growth dispatch stays as-is
- All reactive-integration tests — no adapter changes, no regressions

### Modified Files

| File | Change |
|------|--------|
| `OraclePayoffStorage.sol` | Drop `PoolKey + reactive`, add `bytes32 adapterSlot` |
| `OraclePayoffMod.sol` | `oraclePoke()` reads adapter via `ProtocolAdapterLib.getDeltaPlusEpoch` |
| `FeeConcentrationIndex.sol` | Import from `ProtocolAdapterMod` instead of ext mod |
| `FeeConcentrationIndexForkHarness.sol` | Same import path update |
| `foundry.toml` | Add `@protocol-adapter/=src/reactive-integration/template/` remapping |

## Initialization Flow

Each `ProtocolAdapterStorage` instance is initialized once via `initializeAdapter()`.

**V4 native:**

```solidity
initializeAdapter(V4_ADAPTER_SLOT, address(poolManager), poolKey.hooks, poolKey, false);
```

**V4 reactive** (missed initial hook registration):

```solidity
initializeAdapter(V4_ADAPTER_SLOT, address(poolManager), fciEntryPoint, poolKey, true);
```

**V3:**

```solidity
PoolKey memory syntheticKey = fromV3Pool(v3PoolAddr, address(reactiveAdapter));
initializeAdapter(V3_ADAPTER_SLOT, address(v3Factory), IHooks(address(reactiveAdapter)), syntheticKey, true);
```

**Vault:**

```solidity
os.adapterSlot = V3_ADAPTER_SLOT; // or V4_ADAPTER_SLOT
```

## Data Flow

```
Path 1: FCI hook callbacks (hookData-aware dispatch, Option C)
─────────────────────────────────────────────────────────────
FeeConcentrationIndex.sol (V4 hook)
  │
  ├─ afterAddLiquidity(hookData)
  │    → ProtocolAdapterMod.registerPosition(hookData, ...)
  │        → fciStorageFor(hookData) → correct FeeConcentrationIndexStorage slot
  │        → registerPosition($, ...)  [FeeConcentrationIndexStorageMod]
  │
  └─ (same pattern for all 9 wrapper functions)

Path 2: Vault oracle reads (adapter-aware, no hookData)
───────────────────────────────────────────────────────
OraclePayoffMod.oraclePoke()
  │
  └─ adapter = protocolAdapterStorage(os.adapterSlot)
       → getDeltaPlusEpoch(adapter)  [ProtocolAdapterLib]
           → IFeeConcentrationIndex(adapter.fciEntryPoint)
               .getDeltaPlusEpoch(adapter.poolKey, adapter.reactive)
```

## Future Work (Out of Scope)

- **V3 fill-out**: Migrate `ReactiveHookAdapter` callbacks to use `ProtocolAdapterStorage` via template pattern
- **Adapter registry**: Higher-level component for registering/discovering protocol adapters
- **Option A migration**: Callers pass `ProtocolAdapterStorage storage $` directly, deprecate hookData flag dispatch
- **Delete deprecated shim**: Once all callers migrate, remove `FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol`
