// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {TickRange, fromTicks} from "./types/TickRangeMod.sol";
import {derivePoolAndPosition, sortTicks} from "../libraries/HookUtilsMod.sol";
import {
    FeeConcentrationIndexStorage, fciStorage, reactiveFciStorage, _poolManager,
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    deregisterPosition, addStateTerm, incrementPosCount, decrementPosCount,
    t_storeTick, t_readTick,
    t_cacheRemovalData, t_readRemovalData,
    incrementOverlappingRanges
} from "./modules/FeeConcentrationIndexStorageMod.sol";
import {CalldataReader, CalldataReaderLib} from "angstrom/src/types/CalldataReader.sol";
import {TickRangeRegistryLib} from "./types/TickRangeRegistryMod.sol";
import {getCurrentTick, getFeeGrowthInside0, getPositionFeeGrowthInsideLast0} from "./types/FeeGrowthReaderMod.sol";
import {FeeShareRatio, fromFeeGrowth, fromFeeGrowthDelta} from "./types/FeeShareRatioMod.sol";
import {FeeConcentrationState} from "./types/FeeConcentrationStateMod.sol";
import {SwapCount} from "./types/SwapCountMod.sol";
import {BlockCount} from "./types/BlockCountMod.sol";
import {IFeeConcentrationIndex} from "./interfaces/IFeeConcentrationIndex.sol";
import {IERC165} from "forge-std/interfaces/IERC165.sol";

// Fee Concentration Index — HookFacet (no BaseHook, no inheritance beyond interfaces).
// Deployed as a facet in MasterHook diamond — runs via delegatecall.
// poolManager stored in FCI's own diamond storage namespace (thetaSwap.fci).


contract FeeConcentrationIndex {

    constructor(address poolManager_) {
        fciStorage().poolManager = IPoolManager(poolManager_);
    }

    // ── afterAddLiquidity ──

    function afterAddLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta,
        BalanceDelta,
        bytes calldata hookData
    ) external returns (bytes4, BalanceDelta) {
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params);
        TickRange rk = fromTicks(params.tickLower, params.tickUpper);

        if (hookData.length > 0) {
            // Reactive path: posLiquidity from params, feeGrowthInside from hookData
            FeeConcentrationIndexStorage storage r$ = reactiveFciStorage();
            CalldataReader reader = CalldataReaderLib.from(hookData);
            uint256 feeGrowthInside0X128;
            (reader, feeGrowthInside0X128) = reader.readU256();
            reader.requireAtEndOf(hookData);
            uint128 posLiquidity = uint128(uint256(params.liquidityDelta));
            registerPosition(
			     r$,
			     poolId,
			     rk,
			     positionKey,
			     params.tickLower,
			     params.tickUpper,
			     posLiquidity
	    );
            setFeeGrowthBaseline(r$, poolId, positionKey, feeGrowthInside0X128);
            incrementPosCount(r$, poolId);
        } else {
            // V4 path: read from PoolManager
            (uint128 posLiquidity,) = getPositionFeeGrowthInsideLast0(_poolManager(), poolId, positionKey);
            registerPosition(poolId, rk, positionKey, params.tickLower, params.tickUpper, posLiquidity);

            int24 currentTick = getCurrentTick(_poolManager(), poolId);
            uint256 feeGrowthInside0X128 = getFeeGrowthInside0(
                _poolManager(), poolId, currentTick, params.tickLower, params.tickUpper
            );
            setFeeGrowthBaseline(poolId, positionKey, feeGrowthInside0X128);
            incrementPosCount(poolId);
        }

        return (IHooks.afterAddLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── beforeSwap ──

    function beforeSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        bytes calldata
    ) external returns (bytes4, BeforeSwapDelta, uint24) {
        PoolId poolId = PoolIdLibrary.toId(key);
        int24 tick = getCurrentTick(_poolManager(), poolId);
        t_storeTick(tick);

        return (IHooks.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, 0);
    }

    // ── afterSwap ──

    function afterSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        BalanceDelta,
        bytes calldata hookData
    ) external returns (bytes4, int128) {
        PoolId poolId = PoolIdLibrary.toId(key);

        int24 tickMin;
        int24 tickMax;
        if (hookData.length > 0) {
            // Reactive path: packed I24 tick via CalldataReader
            CalldataReader reader = CalldataReaderLib.from(hookData);
            int24 tick;
            (reader, tick) = reader.readI24();
            reader.requireAtEndOf(hookData);
            tickMin = tick;
            tickMax = tick + 1;
            incrementOverlappingRanges(reactiveFciStorage(), poolId, tickMin, tickMax);
        } else {
            // V4 path: tickBefore from transient storage, tickAfter from PoolManager
            int24 tickBefore = t_readTick();
            int24 tickAfter = getCurrentTick(_poolManager(), poolId);
            (tickMin, tickMax) = sortTicks(tickBefore, tickAfter);
            incrementOverlappingRanges(poolId, tickMin, tickMax);
        }

        return (IHooks.afterSwap.selector, 0);
    }

    // ── beforeRemoveLiquidity ──

    function beforeRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        bytes calldata
    ) external returns (bytes4) {
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params);
        (uint128 posLiquidity, uint256 feeLast0) = getPositionFeeGrowthInsideLast0(_poolManager(), poolId, positionKey);

        // Cache rangeFeeGrowthInside0 BEFORE V4 processes the removal.
        // When the last LP exits a range, V4 uninitializes the ticks, zeroing feeGrowthOutside.
        // Reading feeGrowthInside after that returns 0, losing the fee data.
        int24 currentTick = getCurrentTick(_poolManager(), poolId);
        uint256 rangeFeeGrowth0 = getFeeGrowthInside0(
            _poolManager(), poolId, currentTick, params.tickLower, params.tickUpper
        );

        t_cacheRemovalData(feeLast0, posLiquidity, rangeFeeGrowth0);
        return IHooks.beforeRemoveLiquidity.selector;
    }

    // ── afterRemoveLiquidity ──

    function afterRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta,
        BalanceDelta,
        bytes calldata hookData
    ) external returns (bytes4, BalanceDelta) {
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params);

        FeeShareRatio xk;
        uint128 posLiquidity;
        SwapCount swapLifetime;
        BlockCount blockLifetime;
        uint128 totalRangeLiq;

        if (hookData.length > 0) {
            // Reactive path: fees from hookData, liquidity share from reactive registry
            FeeConcentrationIndexStorage storage r$ = reactiveFciStorage();
            posLiquidity = uint128(uint256(-params.liquidityDelta));

            (, swapLifetime, blockLifetime, totalRangeLiq) =
                deregisterPosition(r$, poolId, positionKey, posLiquidity);

            xk = fromFeeGrowth(uint256(posLiquidity), uint256(totalRangeLiq));

            if (!swapLifetime.isZero()) {
                uint256 xSquaredQ128 = xk.square();
                addStateTerm(r$, poolId, blockLifetime, xSquaredQ128);
            }
            decrementPosCount(r$, poolId);
            deleteFeeGrowthBaseline(r$, poolId, positionKey);
        } else {
            // V4 path: read cached pre-update values from transient storage
            (uint256 positionFeeLast0X128, uint128 posLiq, uint256 rangeFeeGrowthNow0X128) = t_readRemovalData();
            posLiquidity = posLiq;

            uint256 baseline0X128 = getFeeGrowthBaseline(poolId, positionKey);

            (, swapLifetime, blockLifetime, totalRangeLiq) =
                deregisterPosition(poolId, positionKey, posLiquidity);

            xk = fromFeeGrowthDelta(
                rangeFeeGrowthNow0X128, positionFeeLast0X128, baseline0X128,
                posLiquidity, totalRangeLiq
            );

            if (!swapLifetime.isZero()) {
                uint256 xSquaredQ128 = xk.square();
                addStateTerm(poolId, blockLifetime, xSquaredQ128);
            }
            decrementPosCount(poolId);
            deleteFeeGrowthBaseline(poolId, positionKey);
        }

        return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── View ──

    function getIndex(PoolKey calldata key, bool reactive) external view returns (uint128 indexA, uint256 thetaSum, uint256 posCount) {
        FeeConcentrationIndexStorage storage $ = reactive ? reactiveFciStorage() : fciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        indexA = $.fciState[poolId].toIndexA();
        thetaSum = $.fciState[poolId].thetaSum;
        posCount = $.fciState[poolId].posCount;
    }

    // ── IERC165 ──

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IFeeConcentrationIndex).interfaceId
            || interfaceId == type(IERC165).interfaceId;
    }
}
