// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {isUniswapV3Reactive} from "../../fee-concentration-index/types/HookDataFlagsMod.sol";
import {
    getCurrentTick,
    getPositionFeeGrowthInsideLast0,
    getFeeGrowthInside0
} from "../../fee-concentration-index/types/FeeGrowthReaderMod.sol";

function getCurrentTick(
    bytes calldata hookData,
    IPoolManager manager,
    PoolId poolId
) view returns (int24 tick) {
    if (isUniswapV3Reactive(hookData)) {
        return 0;
    }
    return getCurrentTick(manager, poolId);
}

function getPositionFeeGrowthInsideLast0(
    bytes calldata hookData,
    IPoolManager manager,
    PoolId poolId,
    bytes32 positionKey
) view returns (uint128 liquidity, uint256 feeGrowthInside0LastX128) {
    if (isUniswapV3Reactive(hookData)) {
        // V3 reactive: no feeGrowthLast tracking. posLiquidity comes from params.
        return (0, 0);
    }
    return getPositionFeeGrowthInsideLast0(manager, poolId, positionKey);
}

function getFeeGrowthInside0(
    bytes calldata hookData,
    IPoolManager manager,
    PoolId poolId,
    int24 currentTick,
    int24 tickLower,
    int24 tickUpper
) view returns (uint256 feeGrowthInside0X128) {
    if (isUniswapV3Reactive(hookData)) {
        // V3 reactive: feeGrowthInside arrives in hookData, not from PoolManager.
        return 0;
    }
    return getFeeGrowthInside0(manager, poolId, currentTick, tickLower, tickUpper);
}
