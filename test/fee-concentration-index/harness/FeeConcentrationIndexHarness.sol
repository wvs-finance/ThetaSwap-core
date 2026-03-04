// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";

import {FeeConcentrationIndex} from "../../../src/fee-concentration-index/FeeConcentrationIndex.sol";
import {FeeConcentrationIndexStorage, fciStorage} from "../../../src/fee-concentration-index/types/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "../../../src/fee-concentration-index/types/TickRangeMod.sol";
import {SwapCount} from "../../../src/fee-concentration-index/types/SwapCountMod.sol";

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
}
