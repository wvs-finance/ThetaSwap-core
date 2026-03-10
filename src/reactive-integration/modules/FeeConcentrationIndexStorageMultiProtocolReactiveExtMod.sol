// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {TickRange} from "../../fee-concentration-index/types/TickRangeMod.sol";
import {
    FeeConcentrationIndexStorage,
    fciStorage, reactiveFciStorage,
    registerPosition,
    incrementPosCount, decrementPosCount,
    incrementOverlappingRanges,
    deregisterPosition, addStateTerm,
    setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline
} from "../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {isUniswapV3Reactive} from "../../fee-concentration-index/types/HookDataFlagsMod.sol";
import {SwapCount} from "../../fee-concentration-index/types/SwapCountMod.sol";
import {BlockCount} from "../../fee-concentration-index/types/BlockCountMod.sol";

function registerPosition(
    bytes calldata hookData,
    PoolId poolId,
    TickRange rk,
    bytes32 positionKey,
    int24 tickLower,
    int24 tickUpper,
    uint128 liquidity
) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    registerPosition($, poolId, rk, positionKey, tickLower, tickUpper, liquidity);
}

function incrementPosCount(bytes calldata hookData, PoolId poolId) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    incrementPosCount($, poolId);
}

function decrementPosCount(bytes calldata hookData, PoolId poolId) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    decrementPosCount($, poolId);
}

function incrementOverlappingRanges(bytes calldata hookData, PoolId poolId, int24 tickMin, int24 tickMax) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    incrementOverlappingRanges($, poolId, tickMin, tickMax);
}

function deregisterPosition(
    bytes calldata hookData,
    PoolId poolId,
    bytes32 positionKey,
    uint128 posLiquidity
) returns (TickRange rk, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    return deregisterPosition($, poolId, positionKey, posLiquidity);
}

function addStateTerm(bytes calldata hookData, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    addStateTerm($, poolId, blockLifetime, xSquaredQ128);
}

function setFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    setFeeGrowthBaseline($, poolId, positionKey, feeGrowth0X128);
}

function getFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey) view returns (uint256) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    return getFeeGrowthBaseline($, poolId, positionKey);
}

function deleteFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey) {
    FeeConcentrationIndexStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveFciStorage()
        : fciStorage();
    deleteFeeGrowthBaseline($, poolId, positionKey);
}
