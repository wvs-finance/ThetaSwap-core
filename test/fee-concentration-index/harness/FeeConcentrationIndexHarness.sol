// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta} from "v4-core/src/types/BeforeSwapDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";

import {FeeConcentrationIndex} from "../../../src/fee-concentration-index/FeeConcentrationIndex.sol";
import {FeeConcentrationIndexStorage, fciStorage} from "../../../src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "../../../src/fee-concentration-index/types/TickRangeMod.sol";
import {SwapCount} from "../../../src/fee-concentration-index/types/SwapCountMod.sol";
import {AccumulatedHHI} from "../../../src/fee-concentration-index/types/AccumulatedHHIMod.sol";

// Test harness: exposes _afterAddLiquidity as external for direct fuzz testing.
// Also exposes storage views so properties can read harness state.
// Must be deployed at address with correct hook flag bits (via CREATE2 + HookMiner).

contract FeeConcentrationIndexHarness is FeeConcentrationIndex {
    constructor(IPositionManager _positionManager) FeeConcentrationIndex(_positionManager) {}

    function exposed_afterAddLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta delta,
        BalanceDelta feeDelta,
        bytes calldata hookData
    ) external returns (bytes4, BalanceDelta) {
        return _afterAddLiquidity(sender, key, params, delta, feeDelta, hookData);
    }

    // Storage views for property checking

    function containsPosition(PoolId poolId, int24 tickLower, int24 tickUpper, bytes32 positionKey)
        external
        view
        returns (bool)
    {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        TickRange rk = fromTicks(tickLower, tickUpper);
        return $.registries[poolId].contains(rk, positionKey);
    }

    function getRangeKeyOf(PoolId poolId, bytes32 positionKey) external view returns (bytes32) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return TickRange.unwrap($.registries[poolId].rangeKeyOf[positionKey]);
    }

    function getBaseline0(PoolId poolId, bytes32 positionKey) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.feeGrowthBaseline0[poolId][positionKey];
    }

    function getBaselineSwapCount(PoolId poolId, bytes32 positionKey) external view returns (uint32) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.registries[poolId].baselineSwapCount[positionKey].unwrap();
    }

    function getRangeLength(PoolId poolId, int24 tickLower, int24 tickUpper) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.registries[poolId].rangeLength(fromTicks(tickLower, tickUpper));
    }

    // ── Swap hook harness ──

    function exposed_beforeSwap(
        address sender,
        PoolKey calldata key,
        SwapParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4, BeforeSwapDelta, uint24) {
        return _beforeSwap(sender, key, params, hookData);
    }

    function exposed_afterSwap(
        address sender,
        PoolKey calldata key,
        SwapParams calldata params,
        BalanceDelta delta,
        bytes calldata hookData
    ) external returns (bytes4, int128) {
        return _afterSwap(sender, key, params, delta, hookData);
    }

    function getRangeSwapCount(PoolId poolId, int24 tickLower, int24 tickUpper) external view returns (uint32) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        bytes32 rkRaw = TickRange.unwrap(fromTicks(tickLower, tickUpper));
        return $.registries[poolId].rangeSwapCount[rkRaw].unwrap();
    }

    function getActiveRangeCount(PoolId poolId) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.registries[poolId].activeRangeCount();
    }

    // ── Remove liquidity harness ──

    function exposed_beforeRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4) {
        return _beforeRemoveLiquidity(sender, key, params, hookData);
    }

    function exposed_afterRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta delta,
        BalanceDelta feeDelta,
        bytes calldata hookData
    ) external returns (bytes4, BalanceDelta) {
        return _afterRemoveLiquidity(sender, key, params, delta, feeDelta, hookData);
    }

    function getAccumulatedHHI(PoolId poolId) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.accumulatedHHI[poolId].unwrap();
    }

    function getIndexA(PoolKey calldata key) external view returns (uint128) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        PoolId poolId_ = PoolIdLibrary.toId(key);
        return $.accumulatedHHI[poolId_].toIndexA();
    }

    function getIndexB(PoolKey calldata key) external view returns (uint128) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        PoolId poolId_ = PoolIdLibrary.toId(key);
        return $.accumulatedHHI[poolId_].toIndexB();
    }

    function getTotalRangeLiquidity(PoolId poolId, int24 tickLower, int24 tickUpper) external view returns (uint128) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        bytes32 rkRaw = TickRange.unwrap(fromTicks(tickLower, tickUpper));
        return $.registries[poolId].totalRangeLiquidity[rkRaw];
    }

    function getPositionAddBlock(PoolId poolId, bytes32 positionKey) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.registries[poolId].positionAddBlock[positionKey];
    }

}
