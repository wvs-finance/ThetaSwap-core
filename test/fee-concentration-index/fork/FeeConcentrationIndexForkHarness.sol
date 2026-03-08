// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";

import {FeeConcentrationIndex} from "../../../src/fee-concentration-index/FeeConcentrationIndex.sol";
import {FeeConcentrationIndexStorage, reactiveFciStorage} from "../../../src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";

/// Fork test harness — takes IPoolManager directly and exposes reactive storage views.
/// No HookMiner needed: fork test calls hook functions directly (not via PoolManager).
contract FeeConcentrationIndexForkHarness is FeeConcentrationIndex {
    constructor(address poolManager_) FeeConcentrationIndex(poolManager_) {}

    function getReactiveAccumulatedSum(PoolId poolId) external view returns (uint256) {
        return reactiveFciStorage().fciState[poolId].accumulatedSum;
    }

    function getReactiveThetaSum(PoolId poolId) external view returns (uint256) {
        return reactiveFciStorage().fciState[poolId].thetaSum;
    }

    function getReactivePosCount(PoolId poolId) external view returns (uint256) {
        return reactiveFciStorage().fciState[poolId].posCount;
    }

    function getReactiveRemovedPosCount(PoolId poolId) external view returns (uint256) {
        return reactiveFciStorage().fciState[poolId].removedPosCount;
    }

    function getReactiveAtNull(PoolId poolId) external view returns (uint128) {
        return reactiveFciStorage().fciState[poolId].atNull();
    }

    function getReactiveDeltaPlus(PoolId poolId) external view returns (uint128) {
        return reactiveFciStorage().fciState[poolId].deltaPlus();
    }

    function getReactiveDeltaPlusPrice(PoolId poolId) external view returns (uint256) {
        return reactiveFciStorage().fciState[poolId].toDeltaPlusPrice();
    }
}
