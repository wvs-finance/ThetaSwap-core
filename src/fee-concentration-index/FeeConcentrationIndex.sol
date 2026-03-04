// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseHook} from "@uniswap/v4-hooks/BaseHook.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {Position} from "v4-core/src/libraries/Position.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";

import {TickRange, fromTicks} from "./types/TickRangeMod.sol";
import {
    FeeConcentrationIndexStorage, fciStorage,
    t_storeTick, t_readTick, sortTicks,
    t_cacheRemovalData, t_readRemovalData,
    incrementOverlappingRanges
} from "./modules/FeeConcentrationIndexStorageMod.sol";
import {TickRangeRegistryLib} from "./types/TickRangeRegistryMod.sol";
import {getCurrentTick, getFeeGrowthInside0, getPositionFeeGrowthInsideLast0} from "./types/FeeGrowthReaderMod.sol";
import {FeeShareRatio, fromFeeGrowthDelta} from "./types/FeeShareRatioMod.sol";
import {AccumulatedHHI} from "./types/AccumulatedHHIMod.sol";
import {SwapCount} from "./types/SwapCountMod.sol";
import {BlockCount} from "./types/BlockCountMod.sol";

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
            beforeRemoveLiquidity: true,
            afterRemoveLiquidity: true,
            beforeSwap: true,
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

        // Read position liquidity from V4 to track totalRangeLiquidity
        (uint128 posLiquidity,) = getPositionFeeGrowthInsideLast0(poolManager, poolId, positionKey);

        $.registries[poolId].register(rk, positionKey, params.tickLower, params.tickUpper, posLiquidity);

        int24 currentTick = getCurrentTick(poolManager, poolId);
        uint256 feeGrowthInside0X128 = getFeeGrowthInside0(
            poolManager, poolId, currentTick, params.tickLower, params.tickUpper
        );
        $.feeGrowthBaseline0[poolId][positionKey] = feeGrowthInside0X128;

        return (BaseHook.afterAddLiquidity.selector, BalanceDelta.wrap(0));
    }

    function _beforeSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        bytes calldata
    ) internal override returns (bytes4, BeforeSwapDelta, uint24) {
        PoolId poolId = PoolIdLibrary.toId(key);
        int24 tick = getCurrentTick(poolManager, poolId);
        t_storeTick(tick);

        return (BaseHook.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, 0);
    }

    function _afterSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        BalanceDelta,
        bytes calldata
    ) internal override returns (bytes4, int128) {
        PoolId poolId = PoolIdLibrary.toId(key);

        int24 tickBefore = t_readTick();
        int24 tickAfter = getCurrentTick(poolManager, poolId);
        (int24 tickMin, int24 tickMax) = sortTicks(tickBefore, tickAfter);
        incrementOverlappingRanges(poolId, tickMin, tickMax);

        return (BaseHook.afterSwap.selector, 0);
    }

    function _beforeRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        bytes calldata
    ) internal override returns (bytes4) {
        PoolId poolId = PoolIdLibrary.toId(key);
        bytes32 positionKey = Position.calculatePositionKey(
            sender, params.tickLower, params.tickUpper, params.salt
        );
        (uint128 posLiquidity, uint256 feeLast0) = getPositionFeeGrowthInsideLast0(poolManager, poolId, positionKey);

        // Cache rangeFeeGrowthInside0 BEFORE V4 processes the removal.
        // When the last LP exits a range, V4 uninitializes the ticks, zeroing feeGrowthOutside.
        // Reading feeGrowthInside after that returns 0, losing the fee data.
        int24 currentTick = getCurrentTick(poolManager, poolId);
        uint256 rangeFeeGrowth0 = getFeeGrowthInside0(
            poolManager, poolId, currentTick, params.tickLower, params.tickUpper
        );

        t_cacheRemovalData(feeLast0, posLiquidity, rangeFeeGrowth0);
        return BaseHook.beforeRemoveLiquidity.selector;
    }

    function _afterRemoveLiquidity(
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

        // Read cached pre-update values from transient storage (set in _beforeRemoveLiquidity)
        (uint256 positionFeeLast0X128, uint128 posLiquidity, uint256 rangeFeeGrowthNow0X128) = t_readRemovalData();

        // Baseline stored at add time
        uint256 baseline0X128 = $.feeGrowthBaseline0[poolId][positionKey];

        // Deregister: get swap lifetime (zero-check) + block lifetime (HHI divisor)
        (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
            $.registries[poolId].deregister(positionKey, posLiquidity);

        // Compute fee share ratio x_k (liquidity-weighted)
        FeeShareRatio xk = fromFeeGrowthDelta(
            rangeFeeGrowthNow0X128, positionFeeLast0X128, baseline0X128,
            posLiquidity, totalRangeLiq
        );

        // Accumulate HHI term if swaps occurred (zero-guard uses swap count)
        if (!swapLifetime.isZero()) {
            uint256 xSquaredQ128 = xk.square();
            $.accumulatedHHI[poolId] = $.accumulatedHHI[poolId].addTerm(blockLifetime, xSquaredQ128);
        }

        // Clean up baseline
        delete $.feeGrowthBaseline0[poolId][positionKey];

        return (BaseHook.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
    }

    function getIndex(PoolKey calldata key) external view returns (uint128 indexA, uint128 indexB) {
        FeeConcentrationIndexStorage storage $ = fciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        indexA = $.accumulatedHHI[poolId].toIndexA();
        indexB = $.accumulatedHHI[poolId].toIndexB();
    }
}
