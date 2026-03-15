// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {TickRange, fromTicks} from "typed-uniswap-v4/fee-concentration-index/types/TickRangeMod.sol";
import {derivePoolAndPosition, sortTicks} from "@libraries/HookUtilsMod.sol";
import {
    FeeConcentrationIndexStorage, fciStorage, reactiveFciStorage, _poolManager,
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    deregisterPosition, addStateTerm, incrementPosCount, decrementPosCount,
    incrementOverlappingRanges
} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {
    writeCacheTick, readCacheTick,
    writeCacheRemovalData, readCacheRemovalData
} from "@reactive-integration/libraries/FeeConcentrationIndexStorageExt.sol";
import {
    getCurrentTick,
    getPositionFeeGrowthInsideLast0,
    getFeeGrowthInside0
} from "@reactive-integration/libraries/FeeGrowthReaderExt.sol";
import {FeeShareRatio, fromFeeGrowthDelta} from "typed-uniswap-v4/fee-concentration-index/types/FeeShareRatioMod.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {SwapCount} from "typed-uniswap-v4/fee-concentration-index/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/fee-concentration-index/types/BlockCountMod.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IERC165} from "forge-std/interfaces/IERC165.sol";
import {
    FeeConcentrationEpochStorage, epochFciStorage,
    addEpochTerm, epochDeltaPlus, initializeEpoch
} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";
import {
    fciRegistryStorage, getProtocolFacet, setProtocolFacet
} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol";
import {IFCIProtocolFacet} from "@protocol-adapter/interfaces/IFCIProtocolFacet.sol";
import {
    protocolFciStorage, protocolEpochFciStorage
} from "@protocol-adapter/modules/FCIProtocolFacetStorageMod.sol";

// Fee Concentration Index V2 — Protocol-agnostic dispatcher.
// V4 fast path: empty hookData → inlined logic (identical to V1).
// Non-V4: hookData[0] flag byte → delegatecall to registered protocol facet.

contract FeeConcentrationIndexV2 {

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
        // ── Protocol dispatch ──
        if (hookData.length > 0) {
            bytes1 flags = hookData[0];
            address facet = address(getProtocolFacet(flags));
            require(facet != address(0), "FCI: unknown protocol");
            (bool ok, bytes memory ret) = facet.delegatecall(msg.data);
            require(ok, "FCI: facet delegatecall failed");
            return abi.decode(ret, (bytes4, BalanceDelta));
        }

        // ── V4 fast path (unchanged from V1) ──
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params, hookData);
        TickRange rk = fromTicks(params.tickLower, params.tickUpper);
        (uint128 posLiquidity,) = getPositionFeeGrowthInsideLast0(hookData, _poolManager(), poolId, positionKey);
        registerPosition(poolId, rk, positionKey, params.tickLower, params.tickUpper, posLiquidity);

        int24 currentTick = getCurrentTick(hookData, _poolManager(), poolId);
        uint256 feeGrowthInside0X128 = getFeeGrowthInside0(
            hookData, _poolManager(), poolId, currentTick, params.tickLower, params.tickUpper
        );
        setFeeGrowthBaseline(poolId, positionKey, feeGrowthInside0X128);
        incrementPosCount(poolId);

        return (IHooks.afterAddLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── beforeSwap ──

    function beforeSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        bytes calldata hookData
    ) external virtual returns (bytes4, BeforeSwapDelta, uint24) {
        // ── Protocol dispatch ──
        if (hookData.length > 0) {
            bytes1 flags = hookData[0];
            address facet = address(getProtocolFacet(flags));
            require(facet != address(0), "FCI: unknown protocol");
            (bool ok, bytes memory ret) = facet.delegatecall(msg.data);
            require(ok, "FCI: facet delegatecall failed");
            return abi.decode(ret, (bytes4, BeforeSwapDelta, uint24));
        }

        // ── V4 fast path ──
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
        // ── Protocol dispatch ──
        if (hookData.length > 0) {
            bytes1 flags = hookData[0];
            address facet = address(getProtocolFacet(flags));
            require(facet != address(0), "FCI: unknown protocol");
            (bool ok, bytes memory ret) = facet.delegatecall(msg.data);
            require(ok, "FCI: facet delegatecall failed");
            return abi.decode(ret, (bytes4, int128));
        }

        // ── V4 fast path ──
        PoolId poolId = PoolIdLibrary.toId(key);
        int24 tickBefore = readCacheTick(hookData);
        int24 tickAfter = getCurrentTick(hookData, _poolManager(), poolId);
        (int24 tickMin, int24 tickMax) = sortTicks(tickBefore, tickAfter);
        incrementOverlappingRanges(poolId, tickMin, tickMax);

        return (IHooks.afterSwap.selector, 0);
    }

    // ── beforeRemoveLiquidity ──

    function beforeRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4) {
        // ── Protocol dispatch ──
        if (hookData.length > 0) {
            bytes1 flags = hookData[0];
            address facet = address(getProtocolFacet(flags));
            require(facet != address(0), "FCI: unknown protocol");
            (bool ok, bytes memory ret) = facet.delegatecall(msg.data);
            require(ok, "FCI: facet delegatecall failed");
            return abi.decode(ret, (bytes4));
        }

        // ── V4 fast path (uses 3-arg overload — no hookData for position key) ──
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params);
        (uint128 posLiquidity, uint256 feeLast0) = getPositionFeeGrowthInsideLast0(hookData, _poolManager(), poolId, positionKey);

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
        // ── Protocol dispatch ──
        if (hookData.length > 0) {
            bytes1 flags = hookData[0];
            address facet = address(getProtocolFacet(flags));
            require(facet != address(0), "FCI: unknown protocol");
            (bool ok, bytes memory ret) = facet.delegatecall(msg.data);
            require(ok, "FCI: facet delegatecall failed");
            return abi.decode(ret, (bytes4, BalanceDelta));
        }

        // ── V4 fast path ──
        (PoolId poolId, bytes32 positionKey) = derivePoolAndPosition(sender, key, params, hookData);

        (uint256 positionFeeLast0X128, uint128 posLiq, uint256 rangeFeeGrowthNow0X128) = readCacheRemovalData(hookData);

        uint128 removedLiq = uint128(uint256(-params.liquidityDelta));
        if (posLiq != removedLiq) {
            return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
        }

        uint256 baseline0X128 = getFeeGrowthBaseline(poolId, positionKey);

        (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
            deregisterPosition(poolId, positionKey, posLiq);

        FeeShareRatio xk = fromFeeGrowthDelta(
            rangeFeeGrowthNow0X128, positionFeeLast0X128, baseline0X128,
            posLiq, totalRangeLiq
        );

        if (!swapLifetime.isZero()) {
            uint256 xSquaredQ128 = xk.square();
            addStateTerm(poolId, blockLifetime, xSquaredQ128);
            addEpochTerm(poolId, blockLifetime, xSquaredQ128);
        }
        decrementPosCount(poolId);
        deleteFeeGrowthBaseline(poolId, positionKey);

        return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── View (V4 — unchanged from V1) ──

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
        deltaPlus_ = epochDeltaPlus(PoolIdLibrary.toId(key));
    }

    // ── View (protocol-scoped — new V2 overloads) ──

    function getIndex(PoolKey calldata key, bytes1 flags) external view returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) {
        FeeConcentrationIndexStorage storage $ = flags == 0x00 ? fciStorage() : protocolFciStorage(flags);
        PoolId poolId = PoolIdLibrary.toId(key);
        indexA = $.fciState[poolId].toIndexA();
        thetaSum = $.fciState[poolId].thetaSum;
        removedPosCount = $.fciState[poolId].removedPosCount;
    }

    function getDeltaPlus(PoolKey calldata key, bytes1 flags) external view returns (uint128 deltaPlus_) {
        FeeConcentrationIndexStorage storage $ = flags == 0x00 ? fciStorage() : protocolFciStorage(flags);
        deltaPlus_ = $.fciState[PoolIdLibrary.toId(key)].deltaPlus();
    }

    function getAtNull(PoolKey calldata key, bytes1 flags) external view returns (uint128 atNull_) {
        FeeConcentrationIndexStorage storage $ = flags == 0x00 ? fciStorage() : protocolFciStorage(flags);
        atNull_ = $.fciState[PoolIdLibrary.toId(key)].atNull();
    }

    function getThetaSum(PoolKey calldata key, bytes1 flags) external view returns (uint256 thetaSum_) {
        FeeConcentrationIndexStorage storage $ = flags == 0x00 ? fciStorage() : protocolFciStorage(flags);
        thetaSum_ = $.fciState[PoolIdLibrary.toId(key)].thetaSum;
    }

    function getDeltaPlusEpoch(PoolKey calldata key, bytes1 flags) external view returns (uint128 deltaPlus_) {
        FeeConcentrationEpochStorage storage $ = flags == 0x00 ? epochFciStorage() : protocolEpochFciStorage(flags);
        deltaPlus_ = epochDeltaPlus($, PoolIdLibrary.toId(key));
    }

    // ── Registration ──

    function registerProtocolFacet(bytes1 flags, IFCIProtocolFacet facet) external {
        setProtocolFacet(flags, facet);
    }

    function getRegisteredProtocolFacet(bytes1 flags) external view returns (IFCIProtocolFacet) {
        return getProtocolFacet(flags);
    }

    // ── Epoch initialization ──

    function initializeEpochPool(PoolKey calldata key, uint256 epochLengthSeconds) external {
        initializeEpoch(PoolIdLibrary.toId(key), epochLengthSeconds);
    }

    // ── IERC165 ──

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IFeeConcentrationIndex).interfaceId
            || interfaceId == type(IERC165).interfaceId;
    }
}
