# FCI Metrics Facet Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose all FCI-computed data to external clients via a read-only diamond facet and event emissions.

**Architecture:** New `FCIMetricsFacet` diamond facet with view functions for persistent state + `FCITermAccumulated` event emitted from V2 orchestrator for transient per-removal data. Registry reads delegated to protocol facets via `bytes2 flags` parameter.

**Tech Stack:** Solidity ^0.8.26, Uniswap V4 core, forge-std, Solady (FixedPointMathLib, EnumerableSetLib), typed-uniswap-v4, diamond storage pattern.

**Spec:** `docs/superpowers/specs/2026-03-17-fci-metrics-facet-design.md`

---

### Task 1: Add `thetaWeight` Helper as BlockCount Extension

**Files:**
- Create: `src/types/BlockCountExt.sol`

This helper computes `Q128 / blockLifetime.floorOne()` — used by both the event emission and available for off-chain replication. We do NOT modify the `lib/typed-uniswap-v4` submodule. Instead, we create an extension file in `src/types/`.

- [ ] **Step 1: Create `BlockCountExt.sol`**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";

uint256 constant Q128 = 1 << 128;

/// @notice Theta weight for a position: θ_k = 1/ℓ_k in Q128.
/// @dev Matches the computation inside FeeConcentrationState.addTerm().
function thetaWeight(BlockCount n) pure returns (uint256) {
    return Q128 / n.floorOne();
}
```

- [ ] **Step 2: Run forge build to verify compilation**

Run: `forge build`
Expected: Compilation succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add src/types/BlockCountExt.sol
git commit -m "feat: add thetaWeight helper as BlockCount extension"
```

---

### Task 2: Create Type Definitions (RangeSnapshot, EpochSnapshot)

**Files:**
- Create: `src/fee-concentration-index-v2/types/RangeSnapshot.sol`
- Create: `src/fee-concentration-index-v2/types/EpochSnapshot.sol`

- [ ] **Step 1: Create RangeSnapshot.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

struct RangeSnapshot {
    int24 tickLower;
    int24 tickUpper;
    uint128 totalLiquidity;
    uint256 swapCount;
    uint256 positionCount;
    bytes32[] positionKeys;
}
```

- [ ] **Step 2: Create EpochSnapshot.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

struct EpochSnapshot {
    uint256 epochId;
    uint256 epochLength;
    uint256 accumulatedSum;
    uint256 thetaSum;
    uint256 posCount;
    uint256 removedPosCount;
    uint128 indexA;
    uint128 deltaPlus;
}
```

- [ ] **Step 3: Run forge build**

Run: `forge build`
Expected: Compiles (types are standalone, no imports needed beyond pragma).

- [ ] **Step 4: Commit**

```bash
git add src/fee-concentration-index-v2/types/RangeSnapshot.sol src/fee-concentration-index-v2/types/EpochSnapshot.sol
git commit -m "feat: add RangeSnapshot and EpochSnapshot type definitions"
```

---

### Task 3: Extend IFCIProtocolFacet with Registry Read Functions

**Files:**
- Modify: `src/fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol`

- [ ] **Step 1: Add 6 new registry read function signatures**

Add at the end of the `IFCIProtocolFacet` interface, before the closing `}`:

```solidity
import {RangeSnapshot} from "@fee-concentration-index-v2/types/RangeSnapshot.sol";
import {TickRange} from "typed-uniswap-v4/types/TickRangeMod.sol";

// ── Registry reads (metrics facet support) ──
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

Note: The `TickRange` import may already exist. The `RangeSnapshot` import is new. `PoolId` is already imported.

- [ ] **Step 2: Run forge build to verify interface compiles**

Run: `forge build`
Expected: Compiles. Protocol facet implementations will fail until Task 5 implements them.

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol
git commit -m "feat: extend IFCIProtocolFacet with registry read functions"
```

---

### Task 4: Add FCITermAccumulated Event to V2 Orchestrator

**Files:**
- Modify: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`

- [ ] **Step 1: Add event definition and import**

At the top of `FeeConcentrationIndexV2.sol`, add import:

```solidity
import {thetaWeight} from "@types/BlockCountExt.sol";
```

Note: The import path depends on the remapping. If `@types` is not mapped, use the relative path from the V2 orchestrator: `import {thetaWeight} from "../../types/BlockCountExt.sol";`. Check `foundry.toml` for existing remappings.

Inside the contract, add the event:

```solidity
event FCITermAccumulated(
    PoolId indexed poolId,
    bytes2 indexed protocolFlags,
    bytes32 indexed posKey,
    uint128 xk,
    uint256 xSquaredQ128,
    uint256 thetaK,
    uint256 blockLifetime,
    uint256 swapLifetime
);
```

- [ ] **Step 2: Emit event in afterRemoveLiquidity**

In `afterRemoveLiquidity`, inside the `if (!swapLifetime.isZero())` block, after `uint256 xSquaredQ128 = xk.square();` and before the `addStateTerm` delegatecall, add:

```solidity
emit FCITermAccumulated(
    poolId,
    protocolFlags,
    posKey,
    xk.unwrap(),
    xSquaredQ128,
    thetaWeight(blockLifetime),
    BlockCount.unwrap(blockLifetime),
    SwapCount.unwrap(swapLifetime)
);
```

Note: `protocolFlags` is already available as `bytes2 protocolFlags = getProtocolFlagFromHookData(hookData);` at the top of the function. `posKey` is already computed. `BlockCount.unwrap` and `SwapCount.unwrap` are already imported.

- [ ] **Step 3: Run forge build**

Run: `forge build`
Expected: Compiles successfully.

- [ ] **Step 4: Commit**

```bash
git add src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol
git commit -m "feat: emit FCITermAccumulated event on removal accumulation"
```

---

### Task 5: Implement Registry Read Functions on Protocol Facets

**Files:**
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol`
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol`

Both facets need the same 6 functions. Each reads from `protocolFciStorage(FLAG)` where FLAG is `UNISWAP_V3_REACTIVE` or `NATIVE_V4` respectively.

- [ ] **Step 1: Add imports to UniswapV3Facet**

```solidity
import {RangeSnapshot} from "@fee-concentration-index-v2/types/RangeSnapshot.sol";
```

- [ ] **Step 2: Implement 6 registry read functions on UniswapV3Facet**

Add at the end of the contract, before the closing `}`. These are `view` functions with **NO `onlyDelegateCall` guard** — they are pure reads with no state-mutation risk, and the `onlyDelegateCall` guard's second check (`address(this) == fci`) would create an unnecessary coupling between FCIMetricsFacet and protocol facet initialization. Only blocking direct calls matters, and that's already handled by the diamond routing:

```solidity
// ── Registry reads (metrics facet support) ──

function getRegistryRangeSnapshot(bytes2, PoolId poolId, TickRange rk) external view returns (RangeSnapshot memory snapshot) {
    FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
    bytes32 rkRaw = TickRange.unwrap(rk);
    snapshot.tickLower = rk.lowerTick();
    snapshot.tickUpper = rk.upperTick();
    snapshot.totalLiquidity = $.registries[poolId].totalRangeLiquidity[rkRaw];
    snapshot.swapCount = SwapCount.unwrap($.registries[poolId].rangeSwapCount[rkRaw]);
    snapshot.positionKeys = $.registries[poolId].positionsInRange(rk);
    snapshot.positionCount = snapshot.positionKeys.length;
}

function getRegistryActiveRanges(bytes2, PoolId poolId) external view returns (TickRange[] memory ranges) {
    FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
    uint256 count = $.registries[poolId].activeRangeCount();
    ranges = new TickRange[](count);
    for (uint256 i; i < count; ++i) {
        ranges[i] = TickRange.wrap($.registries[poolId].activeRangeAt(i));
    }
}

function getRegistryAllSnapshots(bytes2, PoolId poolId) external view returns (RangeSnapshot[] memory snapshots) {
    FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
    uint256 count = $.registries[poolId].activeRangeCount();
    snapshots = new RangeSnapshot[](count);
    for (uint256 i; i < count; ++i) {
        TickRange rk = TickRange.wrap($.registries[poolId].activeRangeAt(i));
        bytes32 rkRaw = TickRange.unwrap(rk);
        snapshots[i].tickLower = rk.lowerTick();
        snapshots[i].tickUpper = rk.upperTick();
        snapshots[i].totalLiquidity = $.registries[poolId].totalRangeLiquidity[rkRaw];
        snapshots[i].swapCount = SwapCount.unwrap($.registries[poolId].rangeSwapCount[rkRaw]);
        snapshots[i].positionKeys = $.registries[poolId].positionsInRange(rk);
        snapshots[i].positionCount = snapshots[i].positionKeys.length;
    }
}

function getRegistryPositionBaseline(bytes2, PoolId poolId, bytes32 posKey) external view returns (uint256) {
    return protocolFciStorage(UNISWAP_V3_REACTIVE).feeGrowthBaseline0[poolId][posKey];
}

function getRegistryPositionAddBlock(bytes2, PoolId poolId, bytes32 posKey) external view returns (uint256) {
    return protocolFciStorage(UNISWAP_V3_REACTIVE).registries[poolId].positionAddBlock[posKey];
}

function getRegistryPositionSwapLifetime(bytes2, PoolId poolId, bytes32 posKey) external view returns (uint256) {
    return SwapCount.unwrap(protocolFciStorage(UNISWAP_V3_REACTIVE).registries[poolId].getLifetime(posKey));
}
```

- [ ] **Step 3: Implement same 6 functions on NativeUniswapV4Facet**

Identical code but replace `UNISWAP_V3_REACTIVE` with `NATIVE_V4`. Add the same `RangeSnapshot` import.

- [ ] **Step 4: Run forge build**

Run: `forge build`
Expected: Both facets compile.

- [ ] **Step 5: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol
git commit -m "feat: implement registry read functions on V3 and V4 protocol facets"
```

---

### Task 6: Create IFCIMetricsFacet Interface

**Files:**
- Create: `src/fee-concentration-index-v2/interfaces/IFCIMetricsFacet.sol`

- [ ] **Step 1: Write the interface**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {TickRange} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {RangeSnapshot} from "@fee-concentration-index-v2/types/RangeSnapshot.sol";
import {EpochSnapshot} from "@fee-concentration-index-v2/types/EpochSnapshot.sol";

interface IFCIMetricsFacet {
    // ── Pool-level ──
    function getAccumulatedSum(PoolKey calldata key, bytes2 flags) external view returns (uint256);
    function getActivePosCount(PoolKey calldata key, bytes2 flags) external view returns (uint256);
    function getDeltaPlusPrice(PoolKey calldata key, bytes2 flags) external view returns (uint256);

    // ── Range (non-view: delegatecall to protocol facet; staticcall enforced at diamond level) ──
    function getRangeSnapshot(PoolKey calldata key, bytes2 flags, TickRange rk) external returns (RangeSnapshot memory);
    function getActiveRanges(PoolKey calldata key, bytes2 flags) external returns (TickRange[] memory);
    function getAllRangeSnapshots(PoolKey calldata key, bytes2 flags) external returns (RangeSnapshot[] memory);

    // ── Epoch ──
    function getCurrentEpoch(PoolKey calldata key, bytes2 flags) external view returns (EpochSnapshot memory);
    function getEpochState(PoolKey calldata key, bytes2 flags, uint256 epochId) external view returns (EpochSnapshot memory);
    function getEpochMetadata(PoolKey calldata key, bytes2 flags) external view returns (uint256 currentEpochId, uint256 epochLength);

    // ── Position (non-view: delegatecall to protocol facet; staticcall enforced at diamond level) ──
    function getPositionBaseline(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256);
    function getPositionAddBlock(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256);
    function getPositionSwapLifetime(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256);
}
```

- [ ] **Step 2: Run forge build**

Run: `forge build`
Expected: Compiles.

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/interfaces/IFCIMetricsFacet.sol
git commit -m "feat: add IFCIMetricsFacet interface"
```

---

### Task 7: Implement FCIMetricsFacet

**Files:**
- Create: `src/fee-concentration-index-v2/FCIMetricsFacet.sol`

This is the core deliverable. Pure view functions — reads from existing storage namespaces. Range/position reads are delegated to the protocol facet.

- [ ] **Step 1: Write the facet**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {TickRange} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/types/FeeConcentrationStateMod.sol";
import {FeeConcentrationEpochStorage} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";
import {RangeSnapshot} from "@fee-concentration-index-v2/types/RangeSnapshot.sol";
import {EpochSnapshot} from "@fee-concentration-index-v2/types/EpochSnapshot.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {
    FeeConcentrationIndexV2Storage
} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol";
import {
    protocolFciStorage, protocolEpochFciStorage
} from "@fee-concentration-index-v2/modules/FCIProtocolFacetStorageMod.sol";
import {getProtocolFacet} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol";
import {LibCall} from "solady/utils/LibCall.sol";

/// @title FCIMetricsFacet
/// @notice Read-only diamond facet exposing all FCI persistent state.
/// MUST be installed on the same diamond as FeeConcentrationIndexV2 and protocol facets.
contract FCIMetricsFacet {

    // ── Pool-level metrics ──

    function getAccumulatedSum(PoolKey calldata key, bytes2 flags) external view returns (uint256) {
        return protocolFciStorage(flags).fciState[PoolIdLibrary.toId(key)].accumulatedSum;
    }

    function getActivePosCount(PoolKey calldata key, bytes2 flags) external view returns (uint256) {
        return protocolFciStorage(flags).fciState[PoolIdLibrary.toId(key)].posCount;
    }

    function getDeltaPlusPrice(PoolKey calldata key, bytes2 flags) external view returns (uint256) {
        return protocolFciStorage(flags).fciState[PoolIdLibrary.toId(key)].toDeltaPlusPrice();
    }

    // ── Range snapshots (delegated to protocol facet) ──

    function getRangeSnapshot(PoolKey calldata key, bytes2 flags, TickRange rk) external returns (RangeSnapshot memory) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryRangeSnapshot, (flags, poolId, rk))),
            (RangeSnapshot)
        );
    }

    function getActiveRanges(PoolKey calldata key, bytes2 flags) external returns (TickRange[] memory) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryActiveRanges, (flags, poolId))),
            (TickRange[])
        );
    }

    function getAllRangeSnapshots(PoolKey calldata key, bytes2 flags) external returns (RangeSnapshot[] memory) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryAllSnapshots, (flags, poolId))),
            (RangeSnapshot[])
        );
    }

    // ── Epoch state ──

    function getCurrentEpoch(PoolKey calldata key, bytes2 flags) external view returns (EpochSnapshot memory snapshot) {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(flags);
        PoolId poolId = PoolIdLibrary.toId(key);
        uint256 epochId = $.currentEpochId[poolId];
        snapshot.epochId = epochId;
        snapshot.epochLength = $.epochLength[poolId];
        if (epochId == 0) return snapshot;
        // If epoch expired, return metadata only (state is stale)
        if (block.timestamp >= epochId + snapshot.epochLength) return snapshot;
        FeeConcentrationState storage state = $.epochStates[poolId][epochId];
        snapshot.accumulatedSum = state.accumulatedSum;
        snapshot.thetaSum = state.thetaSum;
        snapshot.posCount = state.posCount;
        snapshot.removedPosCount = state.removedPosCount;
        snapshot.indexA = state.toIndexA();
        snapshot.deltaPlus = state.deltaPlus();
    }

    function getEpochState(PoolKey calldata key, bytes2 flags, uint256 epochId) external view returns (EpochSnapshot memory snapshot) {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(flags);
        PoolId poolId = PoolIdLibrary.toId(key);
        snapshot.epochId = epochId;
        snapshot.epochLength = $.epochLength[poolId];
        FeeConcentrationState storage state = $.epochStates[poolId][epochId];
        snapshot.accumulatedSum = state.accumulatedSum;
        snapshot.thetaSum = state.thetaSum;
        snapshot.posCount = state.posCount;
        snapshot.removedPosCount = state.removedPosCount;
        snapshot.indexA = state.toIndexA();
        snapshot.deltaPlus = state.deltaPlus();
    }

    function getEpochMetadata(PoolKey calldata key, bytes2 flags) external view returns (uint256 currentEpochId, uint256 epochLength) {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(flags);
        PoolId poolId = PoolIdLibrary.toId(key);
        currentEpochId = $.currentEpochId[poolId];
        epochLength = $.epochLength[poolId];
    }

    // ── Position-level (delegated to protocol facet) ──

    function getPositionBaseline(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryPositionBaseline, (flags, poolId, posKey))),
            (uint256)
        );
    }

    function getPositionAddBlock(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryPositionAddBlock, (flags, poolId, posKey))),
            (uint256)
        );
    }

    function getPositionSwapLifetime(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryPositionSwapLifetime, (flags, poolId, posKey))),
            (uint256)
        );
    }
}
```

**`LibCall.delegateCallContract` is not `view`-safe:** Solady's `LibCall.delegateCallContract` is declared `internal returns (bytes memory)` — not `view`. The Solidity compiler will reject `view` functions that call non-`view` functions. The range, position, and epoch-delegation functions in FCIMetricsFacet that use `LibCall.delegateCallContract` must therefore be declared `external` (without `view`). This is safe because: (1) the target protocol facet functions are read-only, (2) external callers going through the diamond's `fallback` execute under `staticcall` context which enforces no state changes at the EVM level. The pool-level metrics and epoch views that read storage directly (not via delegatecall) remain `external view`.

- [ ] **Step 2: Run forge build**

Run: `forge build`
Expected: Compiles. If `delegateCallContract` in `view` functions fails, see note above and switch to direct storage reads.

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/FCIMetricsFacet.sol
git commit -m "feat: implement FCIMetricsFacet with all view functions"
```

---

### Task 8: Write Tests — Pool-Level Views

**Files:**
- Create: `test/fee-concentration-index-v2/FCIMetricsFacet.t.sol`

The test needs a harness that deploys FCI V2 + a protocol facet + the metrics facet, then drives state through add/swap/remove to produce known FCI values.

- [ ] **Step 1: Write test harness and pool-level tests**

The test should:
1. Deploy `FeeConcentrationIndexV2`, a protocol facet (use `NativeUniswapV4Facet` since it's simpler — no V3 pool needed), and `FCIMetricsFacet`
2. Register the protocol facet and metrics facet on the diamond
3. Add 2 positions in different ranges
4. Perform swaps that cross both ranges
5. Remove both positions (full exit)
6. Assert `getAccumulatedSum` > 0
7. Assert `getActivePosCount` == 0 (both removed)
8. Assert `getDeltaPlusPrice` matches manual computation from known Δ⁺

```solidity
// Test structure — implementer fills in harness setup based on existing
// test/fee-concentration-index-v2/protocols/uniswap-v3/integration/FeeConcentrationIndexV2Full.integration.t.sol
// for diamond deployment patterns.

function test_poolLevel_accumulatedSum() public { /* ... */ }
function test_poolLevel_activePosCount_afterAdd() public { /* ... */ }
function test_poolLevel_activePosCount_afterRemove() public { /* ... */ }
function test_poolLevel_deltaPlusPrice() public { /* ... */ }
```

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/FCIMetricsFacet.t.sol" -vv`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add test/fee-concentration-index-v2/FCIMetricsFacet.t.sol
git commit -m "test: add pool-level view tests for FCIMetricsFacet"
```

---

### Task 9: Write Tests — Range Snapshots

**Files:**
- Modify: `test/fee-concentration-index-v2/FCIMetricsFacet.t.sol`

- [ ] **Step 1: Add range snapshot tests**

```solidity
function test_rangeSnapshot_singleRange() public {
    // Add position, do swaps, check snapshot fields
    // Assert tickLower, tickUpper, totalLiquidity, swapCount, positionCount, positionKeys
}

function test_rangeSnapshot_multipleRanges() public {
    // Add positions in 2 different ranges, verify getActiveRanges returns both
    // getAllRangeSnapshots returns correct data for each
}

function test_rangeSnapshot_emptyPool() public {
    // No positions added — getActiveRanges returns empty array
    // getAllRangeSnapshots returns empty array
}

function test_rangeSnapshot_positionKeys() public {
    // Add 3 positions in same range, verify positionKeys contains all 3
}
```

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/FCIMetricsFacet.t.sol" -vv`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add test/fee-concentration-index-v2/FCIMetricsFacet.t.sol
git commit -m "test: add range snapshot tests for FCIMetricsFacet"
```

---

### Task 10: Write Tests — Epoch State

**Files:**
- Modify: `test/fee-concentration-index-v2/FCIMetricsFacet.t.sol`

- [ ] **Step 1: Add epoch tests**

```solidity
function test_epoch_currentEpoch() public {
    // Initialize epoch, add+remove positions within epoch, verify getCurrentEpoch
}

function test_epoch_historicalEpoch() public {
    // Initialize epoch, accumulate terms, warp past epoch boundary,
    // accumulate more terms (new epoch), query old epoch by ID
}

function test_epoch_nonExistentEpoch() public {
    // Query getEpochState with an epochId that was never active
    // Assert all fields are zero (removedPosCount == 0)
}

function test_epoch_uninitializedPool() public {
    // Pool with no epoch initialization — getEpochMetadata returns (0, 0)
    // getCurrentEpoch returns all zeros
}
```

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/FCIMetricsFacet.t.sol" -vv`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add test/fee-concentration-index-v2/FCIMetricsFacet.t.sol
git commit -m "test: add epoch state tests for FCIMetricsFacet"
```

---

### Task 11: Write Tests — Position-Level Views

**Files:**
- Modify: `test/fee-concentration-index-v2/FCIMetricsFacet.t.sol`

- [ ] **Step 1: Add position-level tests**

```solidity
function test_position_baseline() public {
    // Add position, verify getPositionBaseline matches stored feeGrowthBaseline
}

function test_position_addBlock() public {
    // Add position at known block, verify getPositionAddBlock returns that block
}

function test_position_swapLifetime() public {
    // Add position, perform N swaps that overlap its range,
    // verify getPositionSwapLifetime returns N
}
```

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/FCIMetricsFacet.t.sol" -vv`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add test/fee-concentration-index-v2/FCIMetricsFacet.t.sol
git commit -m "test: add position-level view tests for FCIMetricsFacet"
```

---

### Task 12: Write Tests — Event Emission

**Files:**
- Modify: `test/fee-concentration-index-v2/FCIMetricsFacet.t.sol`

- [ ] **Step 1: Add event emission test**

```solidity
function test_event_FCITermAccumulated() public {
    // Add position, swap, remove (full exit with swaps > 0)
    // Use vm.expectEmit to verify FCITermAccumulated fields
    // Manually compute expected xk, xSquaredQ128, thetaK, blockLifetime, swapLifetime
    // and compare with emitted values
}

function test_event_notEmitted_partialRemove() public {
    // Partial remove — no event emitted
    // Use vm.recordLogs, verify no FCITermAccumulated
}

function test_event_notEmitted_zeroSwaps() public {
    // Full remove but zero swaps — no event emitted
    // Use vm.recordLogs, verify no FCITermAccumulated
}
```

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/FCIMetricsFacet.t.sol" -vv`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add test/fee-concentration-index-v2/FCIMetricsFacet.t.sol
git commit -m "test: add FCITermAccumulated event emission tests"
```

---

### Task 13: Run Full Test Suite — Regression Check

**Files:** None (verification only)

- [ ] **Step 1: Run all FCI tests**

Run: `forge test --match-path "test/fee-concentration-index/**" -vv`
Expected: All existing tests pass. No regressions from thetaWeight refactor or event addition.

- [ ] **Step 2: Run V2 tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/**" -vv`
Expected: All pass including new FCIMetricsFacet tests.

- [ ] **Step 3: Run full test suite**

Run: `forge test -vv`
Expected: No regressions anywhere.

- [ ] **Step 4: Commit any fixes if needed**
