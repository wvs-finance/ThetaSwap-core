// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/types/FeeConcentrationStateMod.sol";
import {TickRangeRegistryV2} from "typed-uniswap-v4/types/TickRangeRegistryModV2.sol";
import {TickRange, fromTicksPacked, intersects} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {LiquidityPositionSnapshot} from "@fee-concentration-index-v2/types/LiquidityPositionSnapshot.sol";

// V2 storage — same layout as V1 minus IPoolManager poolManager.
// Uses TickRangeRegistryV2 (clean register signature, packed TickRange).

struct FeeConcentrationIndexV2Storage {
    mapping(PoolId => FeeConcentrationState) fciState;
    mapping(PoolId => TickRangeRegistryV2) registries;
    mapping(PoolId => mapping(bytes32 => uint256)) feeGrowthBaseline0;
}

bytes32 constant FCI_V2_STORAGE_SLOT = keccak256("thetaSwap.fci");

function fciV2Storage() pure returns (FeeConcentrationIndexV2Storage storage s) {
    bytes32 slot = FCI_V2_STORAGE_SLOT;
    assembly ("memory-safe") { s.slot := slot }
}

// ── addPositionInRange (was: registerPosition) ──

function addPositionInRange(
    FeeConcentrationIndexV2Storage storage $,
    bytes32 positionKey,
    LiquidityPositionSnapshot memory snapshot
) {
    PoolId poolId = PoolIdLibrary.toId(snapshot.config.poolKey);
    TickRange rk = fromTicksPacked(snapshot.config.tickLower, snapshot.config.tickUpper);
    $.registries[poolId].register(rk, positionKey, snapshot.liquidity);
}

// ── removePositionInRange (was: deregisterPosition) ──

function removePositionInRange(
    FeeConcentrationIndexV2Storage storage $,
    bytes32 positionKey,
    LiquidityPositionSnapshot memory snapshot
) returns (TickRange rk, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) {
    PoolId poolId = PoolIdLibrary.toId(snapshot.config.poolKey);
    return $.registries[poolId].deregister(positionKey, snapshot.liquidity);
}

// ── setFeeGrowthBaseline (unchanged) ──

function setFeeGrowthBaseline(FeeConcentrationIndexV2Storage storage $, PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) {
    $.feeGrowthBaseline0[poolId][positionKey] = feeGrowth0X128;
}

// ── getFeeGrowthBaseline (unchanged) ──

function getFeeGrowthBaseline(FeeConcentrationIndexV2Storage storage $, PoolId poolId, bytes32 positionKey) view returns (uint256) {
    return $.feeGrowthBaseline0[poolId][positionKey];
}

// ── deleteFeeGrowthBaseline (unchanged) ──

function deleteFeeGrowthBaseline(FeeConcentrationIndexV2Storage storage $, PoolId poolId, bytes32 positionKey) {
    delete $.feeGrowthBaseline0[poolId][positionKey];
}

// ── addStateTerm (unchanged) ──

function addStateTerm(FeeConcentrationIndexV2Storage storage $, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) {
    $.fciState[poolId].addTerm(blockLifetime, xSquaredQ128);
}

// ── incrementPosCount (unchanged) ──

function incrementPosCount(FeeConcentrationIndexV2Storage storage $, PoolId poolId) {
    $.fciState[poolId].incrementPos();
}

// ── decrementPosCount (unchanged) ──

function decrementPosCount(FeeConcentrationIndexV2Storage storage $, PoolId poolId) {
    $.fciState[poolId].decrementPos();
}

// ── incrementOverlappingRanges (unchanged name, uses V2 registry + packed TickRange) ──

function incrementOverlappingRanges(FeeConcentrationIndexV2Storage storage $, PoolId poolId, int24 tickMin, int24 tickMax) {
    uint256 count = $.registries[poolId].activeRangeCount();
    for (uint256 i; i < count; ++i) {
        bytes32 rkRaw = $.registries[poolId].activeRangeAt(i);
        TickRange rk = TickRange.wrap(rkRaw);
        if (intersects(rk.lowerTick(), rk.upperTick(), tickMin, tickMax)) {
            $.registries[poolId].incrementRangeSwapCount(rk);
        }
    }
}
