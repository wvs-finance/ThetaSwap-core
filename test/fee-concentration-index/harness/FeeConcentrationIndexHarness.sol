// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";

import {FeeConcentrationIndex} from "@fee-concentration-index/FeeConcentrationIndex.sol";
import {FeeConcentrationIndexStorage, fciStorage} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "typed-uniswap-v4/fee-concentration-index/types/TickRangeMod.sol";
import {SwapCount} from "typed-uniswap-v4/fee-concentration-index/types/SwapCountMod.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";

// Test harness: inherits FeeConcentrationIndex to expose storage views.
// Hook functions are already external on FeeConcentrationIndex — no exposed_* wrappers needed.
// Must be deployed at address with correct hook flag bits (via CREATE2 + HookMiner).

contract FeeConcentrationIndexHarness is FeeConcentrationIndex {
    constructor(IPositionManager _positionManager)
        FeeConcentrationIndex(address(_positionManager.poolManager()))
    {}

    // ── Storage views for property checking ──

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

    function getRangeSwapCount(PoolId poolId, int24 tickLower, int24 tickUpper) external view returns (uint32) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        bytes32 rkRaw = TickRange.unwrap(fromTicks(tickLower, tickUpper));
        return $.registries[poolId].rangeSwapCount[rkRaw].unwrap();
    }

    function getActiveRangeCount(PoolId poolId) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.registries[poolId].activeRangeCount();
    }

    function getAccumulatedHHI(PoolId poolId) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.fciState[poolId].accumulatedSum;
    }

    function getIndexA(PoolKey calldata key) external view returns (uint128) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        PoolId poolId_ = PoolIdLibrary.toId(key);
        return $.fciState[poolId_].toIndexA();
    }

    function getThetaSum(PoolId poolId) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.fciState[poolId].thetaSum;
    }

    function getPosCount(PoolId poolId) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.fciState[poolId].posCount;
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

    function getRemovedPosCount(PoolId poolId) external view returns (uint256) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.fciState[poolId].removedPosCount;
    }

    function getAtNull(PoolId poolId) external view returns (uint128) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.fciState[poolId].atNull();
    }

    function getDeltaPlus(PoolId poolId) external view returns (uint128) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        return $.fciState[poolId].deltaPlus();
    }
}
