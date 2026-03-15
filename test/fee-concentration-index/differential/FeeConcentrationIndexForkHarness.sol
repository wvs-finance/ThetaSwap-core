// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {Position} from "v4-core/src/libraries/Position.sol";

import {FeeConcentrationIndex} from "@fee-concentration-index/FeeConcentrationIndex.sol";
import {FeeConcentrationIndexStorage, fciStorage} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {FeeShareRatio, fromFeeGrowth} from "typed-uniswap-v4/types/FeeShareRatioMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    deregisterPosition, addStateTerm, incrementPosCount, decrementPosCount,
    incrementOverlappingRanges
} from "@protocol-adapter/modules/ProtocolAdapterMod.sol";
import {sortTicks} from "@libraries/HookUtilsMod.sol";

/// @title FCI Differential Test Harness
/// @notice Replays V4 events without going through PoolManager.
/// Shadows position liquidity and tick state internally since positions
/// don't actually exist in the forked PoolManager.
/// hookData is always empty (V4 native path).
contract FeeConcentrationIndexForkHarness is FeeConcentrationIndex {
    using PoolIdLibrary for PoolKey;

    // Shadow state: position liquidity tracked from add events
    mapping(bytes32 posKey => uint128 liquidity) public shadowLiquidity;
    // Shadow state: current tick tracked from swap events
    int24 public shadowTick;

    constructor(address poolManager_) FeeConcentrationIndex(poolManager_) {}

    // ── Override afterAddLiquidity — use params.liquidityDelta instead of PoolManager ──

    function afterAddLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta,
        BalanceDelta,
        bytes calldata hookData
    ) external override returns (bytes4, BalanceDelta) {
        PoolId poolId = key.toId();
        bytes32 positionKey = Position.calculatePositionKey(
            sender, params.tickLower, params.tickUpper, params.salt
        );

        uint128 posLiquidity = uint128(uint256(params.liquidityDelta));
        shadowLiquidity[positionKey] += posLiquidity;

        TickRange rk = fromTicks(params.tickLower, params.tickUpper);
        registerPosition(hookData, poolId, rk, positionKey, params.tickLower, params.tickUpper, posLiquidity);
        setFeeGrowthBaseline(hookData, poolId, positionKey, 0);
        incrementPosCount(hookData, poolId);

        return (IHooks.afterAddLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── Override beforeSwap — cache shadowTick instead of reading PoolManager ──

    function beforeSwap(
        address,
        PoolKey calldata,
        SwapParams calldata,
        bytes calldata
    ) external override returns (bytes4, BeforeSwapDelta, uint24) {
        // shadowTick holds the tick from the previous swap (or 0 initially).
        // The test will call setShadowTick before afterSwap to set the new tick.
        return (IHooks.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, 0);
    }

    // ── Override afterSwap — use shadow ticks instead of PoolManager + transient cache ──

    /// @notice Replay a swap. Takes the new tick as argument, uses shadowTick as tickBefore,
    ///         then updates shadowTick to the new tick.
    function afterSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        BalanceDelta,
        bytes calldata hookData
    ) external override returns (bytes4, int128) {
        PoolId poolId = key.toId();
        int24 tickBefore = shadowTick;
        int24 tickAfter = pendingTick;
        shadowTick = pendingTick;
        (int24 tickMin, int24 tickMax) = sortTicks(tickBefore, tickAfter);
        incrementOverlappingRanges(hookData, poolId, tickMin, tickMax);

        return (IHooks.afterSwap.selector, 0);
    }

    /// @notice Stage the next swap tick. Called by the test before afterSwap.
    int24 public pendingTick;
    function setShadowTick(int24 tick) external {
        pendingTick = tick;
    }

    // ── Override afterRemoveLiquidity — use shadow liquidity, skip PoolManager reads ──

    function afterRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta,
        BalanceDelta,
        bytes calldata hookData
    ) external override returns (bytes4, BalanceDelta) {
        PoolId poolId = key.toId();
        bytes32 positionKey = Position.calculatePositionKey(
            sender, params.tickLower, params.tickUpper, params.salt
        );

        uint128 removedLiq = uint128(uint256(-params.liquidityDelta));

        // Differential test: no partial-remove guard. The Python oracle counts every
        // negative liquidityDelta event as a full deregistration. Use removedLiq for x_k.
        (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
            deregisterPosition(hookData, poolId, positionKey, removedLiq);

        if (!swapLifetime.isZero()) {
            FeeShareRatio xk = fromFeeGrowth(uint256(removedLiq), uint256(totalRangeLiq));
            uint256 xSquaredQ128 = xk.square();
            addStateTerm(hookData, poolId, blockLifetime, xSquaredQ128);
        }

        decrementPosCount(hookData, poolId);
        deleteFeeGrowthBaseline(hookData, poolId, positionKey);
        delete shadowLiquidity[positionKey];

        return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── View helpers ──

    function getReactiveAccumulatedSum(PoolId poolId) external view returns (uint256) {
        return fciStorage().fciState[poolId].accumulatedSum;
    }

    function getReactiveThetaSum(PoolId poolId) external view returns (uint256) {
        return fciStorage().fciState[poolId].thetaSum;
    }

    function getReactivePosCount(PoolId poolId) external view returns (uint256) {
        return fciStorage().fciState[poolId].posCount;
    }

    function getReactiveRemovedPosCount(PoolId poolId) external view returns (uint256) {
        return fciStorage().fciState[poolId].removedPosCount;
    }

    function getReactiveAtNull(PoolId poolId) external view returns (uint128) {
        return fciStorage().fciState[poolId].atNull();
    }

    function getReactiveDeltaPlus(PoolId poolId) external view returns (uint128) {
        return fciStorage().fciState[poolId].deltaPlus();
    }

    function getReactiveDeltaPlusPrice(PoolId poolId) external view returns (uint256) {
        return fciStorage().fciState[poolId].toDeltaPlusPrice();
    }
}
