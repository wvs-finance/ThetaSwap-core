# FCI Metrics Facet — Full Data Exposure Design

**Date**: 2026-03-17
**Branch**: 008-uniswap-v3-reactive-integration
**Status**: Draft

## Problem

The FCI engine (V1 and V2) computes rich intermediate data — per-position fee share ratios, per-range swap counts, concentration prices, epoch decompositions — but only exposes a narrow set of derived metrics through its view functions. Clients building CLIs, dashboards, or indexing pipelines cannot access the full algorithmic output.

## Solution

Two-pronged approach:

1. **Event emission** from the V2 orchestrator for transient per-removal data (x_k, theta_k) that is computed and discarded during `afterRemoveLiquidity`.
2. **FCIMetricsFacet** — a new read-only diamond facet exposing all persistent derived state via view functions.

## Design Decisions

- **V2 interface only** — all new views take `(PoolKey, bytes2 flags)` for protocol-scoping. V1 views remain unchanged.
- **Event emission from V2 orchestrator** — single emission point in `afterRemoveLiquidity`, only on actual FCI term accumulation (full exit + swaps > 0).
- **Metrics facet as separate diamond facet** (Approach A) — clean separation from algorithm orchestration, independently deployable, pure reads.
- **Struct returns** for range and epoch data — one RPC round-trip per query.
- **Registry reads via delegatecall to protocol facet** — FCIMetricsFacet stays protocol-agnostic.
- **Historical epoch access** — abandoned epoch slots are still readable on-chain.
- **Same-diamond constraint** — FCIMetricsFacet MUST be installed on the same diamond as FeeConcentrationIndexV2 and the protocol facets. Delegatecall to protocol facets requires shared storage context and matching `address(this)` for `onlyDelegateCall` guards.
- **Registry read functions take `bytes2 flags` not `bytes calldata hookData`** — read-only registry views only need the protocol flag to locate the storage slot. No hookData synthesis needed.

## 1. Event Emission (V2 Orchestrator Touch)

### Event Definition

```solidity
event FCITermAccumulated(
    PoolId indexed poolId,
    bytes2 indexed protocolFlags,
    bytes32 indexed posKey,
    uint128 xk,              // FeeShareRatio Q128
    uint256 xSquaredQ128,    // x_k^2 Q128
    uint256 thetaK,          // 1/l_k in Q128
    uint256 blockLifetime,   // l_k raw
    uint256 swapLifetime     // swaps seen
);
```

### Emission Point

In `FeeConcentrationIndexV2.afterRemoveLiquidity`, inside the `if (!swapLifetime.isZero())` block, after `xSquaredQ128` is computed:

```solidity
// existing
FeeShareRatio xk = fromFeeGrowthDelta(...);
uint256 xSquaredQ128 = xk.square();

// new: compute thetaK via shared helper and emit
uint256 thetaK = thetaWeight(blockLifetime); // Q128 / blockLifetime.floorOne()
emit FCITermAccumulated(
    poolId, protocolFlags, posKey,
    xk.unwrap(), xSquaredQ128, thetaK,
    BlockCount.unwrap(blockLifetime),
    SwapCount.unwrap(swapLifetime)
);

// existing
LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.addStateTerm, ...));
LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.addEpochTerm, ...));
```

### Shared thetaK Helper

The `thetaWeight(BlockCount)` free function is created in `src/types/BlockCountExt.sol` as an extension of the `BlockCount` type from `typed-uniswap-v4`. We do not modify library submodules. The function computes `Q128 / blockLifetime.floorOne()` — matching the inline computation in `FeeConcentrationState.addTerm()` — and is used by the event emission in the V2 orchestrator.

### Files Modified

- `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol` — add event + ~5 lines emission

## 2. FCIMetricsFacet — View Functions

### Types

```solidity
// src/fee-concentration-index-v2/types/RangeSnapshot.sol
struct RangeSnapshot {
    int24 tickLower;
    int24 tickUpper;
    uint128 totalLiquidity;    // sum of all position liquidities in range
    uint256 swapCount;         // cumulative range swap counter (resets only when range empties)
    uint256 positionCount;     // current number of positions in this range
    bytes32[] positionKeys;    // enumerable position keys within the range
}

// src/fee-concentration-index-v2/types/EpochSnapshot.sol
struct EpochSnapshot {
    uint256 epochId;
    uint256 epochLength;
    uint256 accumulatedSum;     // raw stored value
    uint256 thetaSum;           // raw stored value
    uint256 posCount;           // active positions within epoch (stored)
    uint256 removedPosCount;    // positions that contributed terms (stored)
    uint128 indexA;             // computed: toIndexA() on accumulatedSum
    uint128 deltaPlus;          // computed: deltaPlus() from indexA and atNull
}
```

### Pool-Level Metrics

```solidity
/// Raw accumulated sum S(theta_k * x_k^2), Q128 — pre-sqrt HHI numerator
function getAccumulatedSum(PoolKey calldata key, bytes2 flags) external view returns (uint256);

/// Active position count (live, not removed)
function getActivePosCount(PoolKey calldata key, bytes2 flags) external view returns (uint256);

/// Concentration price p = Delta+/(1 - Delta+), Q128
function getDeltaPlusPrice(PoolKey calldata key, bytes2 flags) external view returns (uint256);
```

### Range Snapshots

```solidity
/// All data for a specific tick range
function getRangeSnapshot(PoolKey calldata key, bytes2 flags, TickRange rk)
    external view returns (RangeSnapshot memory);

/// Enumerate all active ranges for a pool
function getActiveRanges(PoolKey calldata key, bytes2 flags)
    external view returns (TickRange[] memory);

/// Batch: snapshots for all active ranges in one call
function getAllRangeSnapshots(PoolKey calldata key, bytes2 flags)
    external view returns (RangeSnapshot[] memory);
```

### Epoch State

```solidity
/// Current epoch full state
function getCurrentEpoch(PoolKey calldata key, bytes2 flags)
    external view returns (EpochSnapshot memory);

/// Historical epoch by ID (abandoned slots still readable).
/// Returns zero-initialized snapshot for epoch IDs that were never active.
/// Callers should check removedPosCount > 0 to distinguish "no removals" from "never existed".
function getEpochState(PoolKey calldata key, bytes2 flags, uint256 epochId)
    external view returns (EpochSnapshot memory);

/// Current epoch ID and length (lightweight metadata query).
/// Returns (0, 0) if epochs not initialized for this pool.
function getEpochMetadata(PoolKey calldata key, bytes2 flags)
    external view returns (uint256 currentEpochId, uint256 epochLength);
```

### Position-Level

```solidity
/// Fee growth baseline stored at add time
function getPositionBaseline(PoolKey calldata key, bytes2 flags, bytes32 posKey)
    external view returns (uint256 feeGrowthBaseline0X128);

/// Block number when position was registered
function getPositionAddBlock(PoolKey calldata key, bytes2 flags, bytes32 posKey)
    external view returns (uint256);

/// Swap lifetime for a live position (current range swap count minus baseline)
function getPositionSwapLifetime(PoolKey calldata key, bytes2 flags, bytes32 posKey)
    external view returns (uint256);
```

## 3. Storage Access Pattern

FCIMetricsFacet runs via delegatecall in the diamond (shared storage context). It reads from three existing namespaces:

1. **`protocolFciStorage(flags)`** — `fciState[poolId]` for accumulatedSum, thetaSum, posCount, removedPosCount
2. **`protocolEpochFciStorage(flags)`** — epoch states, currentEpochId, epochLength
3. **Protocol facet's TickRangeRegistry** — via delegatecall to the registered protocol facet

For registry reads, the protocol facet interface is extended with:

```solidity
// New additions to IFCIProtocolFacet
// NOTE: these take bytes2 flags (not hookData) since read-only registry views
// only need the protocol flag to locate the correct storage slot.
function getRegistryRangeSnapshot(bytes2 flags, PoolId poolId, TickRange rk)
    external view returns (RangeSnapshot memory);

function getRegistryActiveRanges(bytes2 flags, PoolId poolId)
    external view returns (TickRange[] memory);

function getRegistryAllSnapshots(bytes2 flags, PoolId poolId)
    external view returns (RangeSnapshot[] memory);

function getRegistryPositionBaseline(bytes2 flags, PoolId poolId, bytes32 posKey)
    external view returns (uint256);

function getRegistryPositionAddBlock(bytes2 flags, PoolId poolId, bytes32 posKey)
    external view returns (uint256);

function getRegistryPositionSwapLifetime(bytes2 flags, PoolId poolId, bytes32 posKey)
    external view returns (uint256);
```

This keeps FCIMetricsFacet protocol-agnostic — it delegates "give me your range/position data" to whichever protocol facet is registered for those flags. The `bytes2 flags` parameter is sufficient because registry storage is keyed by `(flags, poolId)` — no hookData synthesis is needed for read-only access.

## 4. File Manifest

### Modified (2)
- `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol` — event + emission
- `src/fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol` — 6 new registry read functions (bytes2 flags, not hookData)

### Created (5)
- `src/types/BlockCountExt.sol` — `thetaWeight(BlockCount)` free function (extension, not modifying lib)
- `src/fee-concentration-index-v2/types/RangeSnapshot.sol`
- `src/fee-concentration-index-v2/types/EpochSnapshot.sol`
- `src/fee-concentration-index-v2/FCIMetricsFacet.sol`
- `src/fee-concentration-index-v2/interfaces/IFCIMetricsFacet.sol`

### Protocol Facet Implementations Modified (2)
- `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol` — implement registry reads
- `src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol` — implement registry reads

### Tests Created (1)
- `test/fee-concentration-index-v2/FCIMetricsFacet.t.sol` — test matrix:
  - Pool-level views (accumulatedSum, activePosCount, deltaPlusPrice) with known state
  - Range enumeration: single range, multiple ranges, empty pool
  - Range snapshot struct correctness (swapCount is cumulative, positionCount, positionKeys)
  - Position-level: baseline, addBlock, swapLifetime for live positions
  - Epoch: current epoch, historical epoch, zero-initialized non-existent epoch, uninitialized pool returns zeros
  - Event emission: FCITermAccumulated fields match manual computation
  - Cross-protocol: V3 and V4 registry reads via protocol facet delegatecall

### No Changes To
- Storage layouts (zero new slots)
- Algorithm flow (event emission only addition)
- V1 contracts
- Existing view function signatures
