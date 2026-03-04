// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {StateLibrary} from "v4-core/src/libraries/StateLibrary.sol";

// V4StateReader-compatible free functions for fee growth reads.
// Accepts currentTick to avoid redundant extsload when caller already has it
// (e.g., afterSwap provides tick via swap result).
// Adapted from Panoptic V4StateReader (MIT).

function getCurrentTick(
    IPoolManager manager,
    PoolId poolId
) view returns (int24 tick) {
    (, tick,,) = StateLibrary.getSlot0(manager, poolId);
}

function getPositionFeeGrowthInsideLast0(
    IPoolManager manager,
    PoolId poolId,
    bytes32 positionKey
) view returns (uint128 liquidity, uint256 feeGrowthInside0LastX128) {
    (liquidity, feeGrowthInside0LastX128,) = StateLibrary.getPositionInfo(manager, poolId, positionKey);
}

function getFeeGrowthInside0(
    IPoolManager manager,
    PoolId poolId,
    int24 currentTick,
    int24 tickLower,
    int24 tickUpper
) view returns (uint256 feeGrowthInside0X128) {
    (uint256 lowerOut0,) = StateLibrary.getTickFeeGrowthOutside(manager, poolId, tickLower);
    (uint256 upperOut0,) = StateLibrary.getTickFeeGrowthOutside(manager, poolId, tickUpper);

    unchecked {
        if (currentTick < tickLower) {
            feeGrowthInside0X128 = lowerOut0 - upperOut0;
        } else if (currentTick >= tickUpper) {
            feeGrowthInside0X128 = upperOut0 - lowerOut0;
        } else {
            (uint256 feeGrowthGlobal0X128,) = StateLibrary.getFeeGrowthGlobals(manager, poolId);
            feeGrowthInside0X128 = feeGrowthGlobal0X128 - lowerOut0 - upperOut0;
        }
    }
}
