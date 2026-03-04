// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {AccumulatedHHI} from "../types/AccumulatedHHIMod.sol";
import {TickRangeRegistry} from "../types/TickRangeRegistryMod.sol";
import {TickRange, intersects} from "../types/TickRangeMod.sol";

// Diamond storage for Fee Concentration Index.
// All hook state lives here — the contract itself holds only logic.

struct FeeConcentrationIndexStorage {
    // Running HHI accumulator per pool: sum of (x_k^2 / lifetime)
    mapping(PoolId => AccumulatedHHI) accumulatedHHI;
    // Per-pool tick range registry (positions grouped by range, per-range swap counters)
    mapping(PoolId => TickRangeRegistry) registries;
    // Per-position snapshot of feeGrowthInside0X128 at add time.
    // Delta = (current feeGrowthInside0 - baseline) gives fees earned during position lifetime.
    // Used to compute x_k (fee share ratio) when the position is removed.
    mapping(PoolId => mapping(bytes32 => uint256)) feeGrowthBaseline0;
}

bytes32 constant FCI_STORAGE_SLOT = keccak256("FeeConcentrationIndex.storage");

// Transient storage slot for caching pre-swap tick (Cancun TSTORE/TLOAD)
bytes32 constant TICK_BEFORE_SLOT = keccak256("FeeConcentrationIndex.tickBefore");
// Transient storage slot for caching feeGrowthInsideLast0 before V4 updates it on removal
bytes32 constant FEE_GROWTH_LAST0_SLOT = keccak256("FeeConcentrationIndex.feeGrowthLast0");
// Transient storage slot for caching position liquidity before V4 updates it on removal
bytes32 constant POS_LIQUIDITY_SLOT = keccak256("FeeConcentrationIndex.posLiquidity");
// Transient storage slot for caching rangeFeeGrowthInside0 before V4 uninitializes ticks
bytes32 constant RANGE_FEE_GROWTH0_SLOT = keccak256("FeeConcentrationIndex.rangeFeeGrowth0");

function fciStorage() pure returns (FeeConcentrationIndexStorage storage s) {
    bytes32 slot = FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

// ── Storage accessors ──

function getAccumulatedHHI(PoolId poolId) view returns (AccumulatedHHI) {
    return fciStorage().accumulatedHHI[poolId];
}

function setAccumulatedHHI(PoolId poolId, AccumulatedHHI value) {
    fciStorage().accumulatedHHI[poolId] = value;
}

function setFeeGrowthBaseline0(PoolId poolId, bytes32 positionKey, uint256 value) {
    fciStorage().feeGrowthBaseline0[poolId][positionKey] = value;
}

function getFeeGrowthBaseline0(PoolId poolId, bytes32 positionKey) view returns (uint256) {
    return fciStorage().feeGrowthBaseline0[poolId][positionKey];
}

function deleteFeeGrowthBaseline0(PoolId poolId, bytes32 positionKey) {
    delete fciStorage().feeGrowthBaseline0[poolId][positionKey];
}

// ── Transient storage helpers ──

function t_storeTick(int24 tick) {
    bytes32 slot = TICK_BEFORE_SLOT;
    assembly {
        tstore(slot, tick)
    }
}

function t_readTick() returns (int24 tick) {
    bytes32 slot = TICK_BEFORE_SLOT;
    assembly {
        tick := tload(slot)
    }
}

function sortTicks(int24 a, int24 b) pure returns (int24 tickMin, int24 tickMax) {
    tickMin = a < b ? a : b;
    tickMax = a > b ? a : b;
}

function t_cacheRemovalData(uint256 feeLast0, uint128 posLiquidity, uint256 rangeFeeGrowth0) {
    bytes32 feeSlot = FEE_GROWTH_LAST0_SLOT;
    bytes32 liqSlot = POS_LIQUIDITY_SLOT;
    bytes32 rangeFeeSlot = RANGE_FEE_GROWTH0_SLOT;
    assembly {
        tstore(feeSlot, feeLast0)
        tstore(liqSlot, posLiquidity)
        tstore(rangeFeeSlot, rangeFeeGrowth0)
    }
}

function t_readRemovalData() returns (uint256 feeLast0, uint128 posLiquidity, uint256 rangeFeeGrowth0) {
    bytes32 feeSlot = FEE_GROWTH_LAST0_SLOT;
    bytes32 liqSlot = POS_LIQUIDITY_SLOT;
    bytes32 rangeFeeSlot = RANGE_FEE_GROWTH0_SLOT;
    assembly {
        feeLast0 := tload(feeSlot)
        posLiquidity := tload(liqSlot)
        rangeFeeGrowth0 := tload(rangeFeeSlot)
    }
}

// ── Loop extracted from _afterSwap ──

function incrementOverlappingRanges(PoolId poolId, int24 tickMin, int24 tickMax) {
    FeeConcentrationIndexStorage storage $ = fciStorage();
    uint256 count = $.registries[poolId].activeRangeCount();
    for (uint256 i; i < count; ++i) {
        bytes32 rkRaw = $.registries[poolId].activeRangeAt(i);
        int24 lower = $.registries[poolId].rangeLowerTick[rkRaw];
        int24 upper = $.registries[poolId].rangeUpperTick[rkRaw];

        if (intersects(lower, upper, tickMin, tickMax)) {
            $.registries[poolId].incrementRangeSwapCount(TickRange.wrap(rkRaw));
        }
    }
}
