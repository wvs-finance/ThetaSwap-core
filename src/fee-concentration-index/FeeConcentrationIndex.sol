// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {TickRange, fromTicks} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {derivePoolAndPosition, sortTicks} from "../libraries/HookUtilsMod.sol";
import {
    FeeConcentrationIndexStorage, fciStorage, reactiveFciStorage, _poolManager
} from "./modules/FeeConcentrationIndexStorageMod.sol";
import {
    writeCacheTick, readCacheTick,
    writeCacheRemovalData, readCacheRemovalData
} from "@libraries/FeeConcentrationIndexStorageExt.sol";
import {
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    deregisterPosition, addStateTerm, incrementPosCount, decrementPosCount,
    incrementOverlappingRanges
} from "@protocol-adapter/modules/ProtocolAdapterMod.sol";
import {CalldataReader, CalldataReaderLib} from "@types/CalldataReader.sol";
import {TickRangeRegistryLib} from "typed-uniswap-v4/types/TickRangeRegistryMod.sol";
import {
    getCurrentTick,
    getPositionFeeGrowthInsideLast0,
    getFeeGrowthInside0
} from "@libraries/FeeGrowthReaderExt.sol";
import {FeeShareRatio, fromFeeGrowth, fromFeeGrowthDelta} from "typed-uniswap-v4/types/FeeShareRatioMod.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/types/FeeConcentrationStateMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {IFeeConcentrationIndex} from "./interfaces/IFeeConcentrationIndex.sol";
import {IERC165} from "forge-std/interfaces/IERC165.sol";
import {
    FeeConcentrationEpochStorage, epochFciStorage,
    addEpochTerm, epochDeltaPlus, initializeEpoch
} from "./modules/FeeConcentrationEpochStorageMod.sol";

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
    ) external virtual returns (bytes4, BalanceDelta) {
	// protocol(protocolFlag(hookData)).positionKey(hookData,sender,params)
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params, hookData);
        TickRange rk = fromTicks(params.tickLower, params.tickUpper);
	// protocol(protocolFlag(hookData)).latestPositionFeeGrowthInside(hookData,poolId)
       (uint128 posLiquidity,) = getPositionFeeGrowthInsideLast0(hookData, _poolManager(), poolId, positionKey);
       registerPosition(hookData, poolId, rk, positionKey, params.tickLower, params.tickUpper, posLiquidity);

       int24 currentTick = getCurrentTick(hookData, _poolManager(), poolId);
       uint256 feeGrowthInside0X128 = getFeeGrowthInside0(
                hookData, _poolManager(), poolId, currentTick, params.tickLower, params.tickUpper
            );
       setFeeGrowthBaseline(hookData, poolId, positionKey, feeGrowthInside0X128);
       incrementPosCount(hookData, poolId);
        

        return (IHooks.afterAddLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── beforeSwap ──

    function beforeSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        bytes calldata hookData
    ) external virtual returns (bytes4, BeforeSwapDelta, uint24) {
        PoolId poolId = PoolIdLibrary.toId(key);
        int24 tick = getCurrentTick(hookData, _poolManager(), poolId);
        writeCacheTick(hookData, tick);

        return (IHooks.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, 0);
    }

    // ── afterSwap ──

    function afterSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        BalanceDelta,
        bytes calldata hookData
    ) external virtual returns (bytes4, int128) {
        PoolId poolId = PoolIdLibrary.toId(key);
        int24 tickBefore = readCacheTick(hookData);
        int24 tickAfter = getCurrentTick(hookData, _poolManager(), poolId);
        (int24 tickMin, int24 tickMax) = sortTicks(tickBefore, tickAfter);
        incrementOverlappingRanges(hookData, poolId, tickMin, tickMax);

        return (IHooks.afterSwap.selector, 0);
    }

    // ── beforeRemoveLiquidity ──

    function beforeRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4) {
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params);
        (uint128 posLiquidity, uint256 feeLast0) = getPositionFeeGrowthInsideLast0(hookData, _poolManager(), poolId, positionKey);

        // Cache rangeFeeGrowthInside0 BEFORE V4 processes the removal.
        // When the last LP exits a range, V4 uninitializes the ticks, zeroing feeGrowthOutside.
        // Reading feeGrowthInside after that returns 0, losing the fee data.
        int24 currentTick = getCurrentTick(hookData, _poolManager(), poolId);
        uint256 rangeFeeGrowth0 = getFeeGrowthInside0(
            hookData, _poolManager(), poolId, currentTick, params.tickLower, params.tickUpper
        );

        writeCacheRemovalData(hookData, feeLast0, posLiquidity, rangeFeeGrowth0);
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
    ) external virtual returns (bytes4, BalanceDelta) {
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params, hookData);

        (uint256 positionFeeLast0X128, uint128 posLiq, uint256 rangeFeeGrowthNow0X128) = readCacheRemovalData(hookData);

        // Partial removes and fee-only collects (liquidityDelta == 0) leave the
        // position alive — skip FCI accumulation. Terms are recorded at full exit only.
        uint128 removedLiq = uint128(uint256(-params.liquidityDelta));
        if (posLiq != removedLiq) {
            return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
        }

        uint256 baseline0X128 = getFeeGrowthBaseline(hookData, poolId, positionKey);

        (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
            deregisterPosition(hookData, poolId, positionKey, posLiq);

        FeeShareRatio xk = fromFeeGrowthDelta(
            rangeFeeGrowthNow0X128, positionFeeLast0X128, baseline0X128,
            posLiq, totalRangeLiq
        );

        if (!swapLifetime.isZero()) {
            uint256 xSquaredQ128 = xk.square();
            addStateTerm(hookData, poolId, blockLifetime, xSquaredQ128);
            addEpochTerm(poolId, blockLifetime, xSquaredQ128);
        }
        decrementPosCount(hookData, poolId);
        deleteFeeGrowthBaseline(hookData, poolId, positionKey);

        return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── View ──

    function getIndex(PoolKey calldata key, bool reactive) external view returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) {
        FeeConcentrationIndexStorage storage $ = reactive ? reactiveFciStorage() : fciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        indexA = $.fciState[poolId].toIndexA();
        thetaSum = $.fciState[poolId].thetaSum;
        removedPosCount = $.fciState[poolId].removedPosCount;
    }

    function getDeltaPlus(PoolKey calldata key, bool reactive) external view returns (uint128 deltaPlus_) {
        FeeConcentrationIndexStorage storage $ = reactive ? reactiveFciStorage() : fciStorage();
        deltaPlus_ = $.fciState[PoolIdLibrary.toId(key)].deltaPlus();
    }

    function getAtNull(PoolKey calldata key, bool reactive) external view returns (uint128 atNull_) {
        FeeConcentrationIndexStorage storage $ = reactive ? reactiveFciStorage() : fciStorage();
        atNull_ = $.fciState[PoolIdLibrary.toId(key)].atNull();
    }

    function getThetaSum(PoolKey calldata key, bool reactive) external view returns (uint256 thetaSum_) {
        FeeConcentrationIndexStorage storage $ = reactive ? reactiveFciStorage() : fciStorage();
        thetaSum_ = $.fciState[PoolIdLibrary.toId(key)].thetaSum;
    }

    function getDeltaPlusEpoch(PoolKey calldata key, bool reactive) external view returns (uint128 deltaPlus_) {
        // TODO(chunk-3): reactive ? reactiveEpochFciStorage() : epochFciStorage()
        deltaPlus_ = epochDeltaPlus(PoolIdLibrary.toId(key));
    }

    /// @notice Initialize epoch metric for a pool. Must be called before epoch accumulation begins.
    /// @param key The pool key.
    /// @param epochLengthSeconds Epoch duration in seconds (e.g. 86400 for 1 day).
    function initializeEpochPool(PoolKey calldata key, uint256 epochLengthSeconds) external {
        initializeEpoch(PoolIdLibrary.toId(key), epochLengthSeconds);
    }

    // ── IERC165 ──

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IFeeConcentrationIndex).interfaceId
            || interfaceId == type(IERC165).interfaceId;
    }
}
