// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseHook} from "@uniswap/v4-hooks/BaseHook.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {Position} from "v4-core/src/libraries/Position.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";

import {TickRange, fromTicks} from "./types/TickRangeMod.sol";
import {FeeConcentrationIndexStorage, fciStorage} from "./types/FeeConcentrationIndexStorageMod.sol";
import {getCurrentTick, getFeeGrowthInside0} from "./types/FeeGrowthReaderMod.sol";

// Fee Concentration Index Hook
// Inherits BaseHook (sole SCOP exception) to avoid rewriting IHooks boilerplate.
// All business logic delegated to free functions and library calls.
// Storage follows diamond pattern — state lives in FeeConcentrationIndexStorage struct.

contract FeeConcentrationIndex is BaseHook {
    IPositionManager public immutable positionManager;

    constructor(IPositionManager _positionManager) BaseHook(_positionManager.poolManager()) {
        positionManager = _positionManager;
    }

    function getHookPermissions() public pure override returns (Hooks.Permissions memory) {
        return Hooks.Permissions({
            beforeInitialize: false,
            afterInitialize: false,
            beforeAddLiquidity: false,
            afterAddLiquidity: true,
            beforeRemoveLiquidity: false,
            afterRemoveLiquidity: true,
            beforeSwap: false,
            afterSwap: true,
            beforeDonate: false,
            afterDonate: false,
            beforeSwapReturnDelta: false,
            afterSwapReturnDelta: false,
            afterAddLiquidityReturnDelta: false,
            afterRemoveLiquidityReturnDelta: false
        });
    }

    function _afterAddLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta,
        BalanceDelta,
        bytes calldata
    ) internal override returns (bytes4, BalanceDelta) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);

        bytes32 positionKey = Position.calculatePositionKey(
            sender, params.tickLower, params.tickUpper, params.salt
        );
        TickRange rk = fromTicks(params.tickLower, params.tickUpper);

        $.registries[poolId].register(rk, positionKey);

        int24 currentTick = getCurrentTick(poolManager, poolId);
        uint256 feeGrowthInside0X128 = getFeeGrowthInside0(
            poolManager, poolId, currentTick, params.tickLower, params.tickUpper
        );
        $.feeGrowthBaseline0[poolId][positionKey] = feeGrowthInside0X128;

        return (BaseHook.afterAddLiquidity.selector, BalanceDelta.wrap(0));
    }
}
