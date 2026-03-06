// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {FeeConcentrationState} from "../types/FeeConcentrationStateMod.sol";
import {TickRangeRegistry} from "../types/TickRangeRegistryMod.sol";
import {TickRange, intersects} from "../types/TickRangeMod.sol";

// Diamond storage for Fee Concentration Index HookFacet.
// Runs via delegatecall in MasterHook's storage context.
// Namespace: keccak256("thetaSwap.fci") — disjoint from MasterHook and DiamondCut slots.

struct FeeConcentrationIndexStorage {
    // Co-primary state per pool: (accumulatedSum, thetaSum, posCount)
    mapping(PoolId => FeeConcentrationState) fciState;
    // Per-pool tick range registry (positions grouped by range, per-range swap counters)
    mapping(PoolId => TickRangeRegistry) registries;
    // Per-position snapshot of feeGrowthInside0X128 at add time.
    mapping(PoolId => mapping(bytes32 => uint256)) feeGrowthBaseline0;
    // PoolManager reference — stored in facet's own namespace, not read from MasterHook.
    // MasterHook is protocol-agnostic and does not guarantee a poolManager field.
    IPoolManager poolManager;
}

bytes32 constant FCI_STORAGE_SLOT = keccak256("thetaSwap.fci");

// Transient storage slots (transaction-scoped, unaffected by delegatecall)
bytes32 constant TICK_BEFORE_SLOT = keccak256("thetaSwap.fci.tickBefore");
bytes32 constant FEE_GROWTH_LAST0_SLOT = keccak256("thetaSwap.fci.feeGrowthLast0");
bytes32 constant POS_LIQUIDITY_SLOT = keccak256("thetaSwap.fci.posLiquidity");
bytes32 constant RANGE_FEE_GROWTH0_SLOT = keccak256("thetaSwap.fci.rangeFeeGrowth0");

function fciStorage() pure returns (FeeConcentrationIndexStorage storage s) {
    bytes32 slot = FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

// ── PoolManager access ──
// Reads from FCI's own diamond storage namespace.
// Set once during facet initialization.

function _poolManager() view returns (IPoolManager) {
    return fciStorage().poolManager;
}

// ── Registry wrappers ──

function registerPosition(
    PoolId poolId,
    TickRange rk,
    bytes32 positionKey,
    int24 tickLower,
    int24 tickUpper,
    uint128 posLiquidity
) {
    FeeConcentrationIndexStorage storage $ = fciStorage();
    $.registries[poolId].register(rk, positionKey, tickLower, tickUpper, posLiquidity);
}

// ── Fee growth baseline wrappers ──

function setFeeGrowthBaseline(PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) {
    fciStorage().feeGrowthBaseline0[poolId][positionKey] = feeGrowth0X128;
}

function getFeeGrowthBaseline(PoolId poolId, bytes32 positionKey) view returns (uint256) {
    return fciStorage().feeGrowthBaseline0[poolId][positionKey];
}

function deleteFeeGrowthBaseline(PoolId poolId, bytes32 positionKey) {
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

// ── Loop extracted from afterSwap ──

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
