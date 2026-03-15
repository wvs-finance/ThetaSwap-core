// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "v4-core/src/types/BeforeSwapDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {TickRange, fromTicksPacked} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {FeeShareRatio, fromFeeGrowthDelta} from "typed-uniswap-v4/types/FeeShareRatioMod.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IERC165} from "forge-std/interfaces/IERC165.sol";
import {FeeConcentrationEpochStorage} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";
import {
    fciRegistryStorage, getProtocolFacet, setProtocolFacet, getProtocolFlagFromHookData
} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol";
import {
    setFci as _setFci, setProtocolStateView as _setProtocolStateView
} from "@fee-concentration-index-v2/modules/FCIFacetAdminStorageMod.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {
    FeeConcentrationIndexV2Storage, fciV2Storage
} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol";
import {
    protocolFciStorage, protocolEpochFciStorage
} from "@fee-concentration-index-v2/modules/FCIProtocolFacetStorageMod.sol";
import {sortTicks} from "@libraries/HookUtilsMod.sol";
import {LibCall} from "solady/utils/LibCall.sol";
import {requireOwner, initOwner} from "@fee-concentration-index-v2/modules/dependencies/LibOwner.sol";
import {LiquidityPositionSnapshot} from "@fee-concentration-index-v2/types/LiquidityPositionSnapshot.sol";
import {PositionConfig} from "@uniswap/v4-periphery/src/libraries/PositionConfig.sol";

// Fee Concentration Index V2 — Protocol-agnostic orchestrator.
// Hook flow (algorithm) lives here. Protocol-specific behavior is delegatecalled
// per function to the registered facet via IFCIProtocolFacet.
// NATIVE_V4 (0xFFFF) is a registered facet like any other protocol.

contract FeeConcentrationIndexV2 {

    // ── afterAddLiquidity ──

    function afterAddLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        BalanceDelta,
        BalanceDelta,
        bytes calldata hookData
    ) external virtual returns (bytes4, BalanceDelta) {
        bytes2 protocolFlags = getProtocolFlagFromHookData(hookData);
        address facet = address(getProtocolFacet(protocolFlags));
        PoolId poolId = PoolIdLibrary.toId(key);

        // 1. positionKey
        bytes32 posKey = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.positionKey, (hookData, sender, params))),
            (bytes32)
        );

        // 2. latestPositionFeeGrowthInside
        (uint128 posLiquidity,) = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.latestPositionFeeGrowthInside, (hookData, poolId, posKey))),
            (uint128, uint256)
        );

        // 3. addPositionInRange
        TickRange rk = fromTicksPacked(params.tickLower, params.tickUpper);
        LiquidityPositionSnapshot memory snapshot = LiquidityPositionSnapshot({
            config: PositionConfig({poolKey: key, tickLower: params.tickLower, tickUpper: params.tickUpper}),
            liquidity: posLiquidity,
            feeGrowthInside0LastX128: 0,
            feeGrowthInside1LastX128: 0
        });
        LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.addPositionInRange, (hookData, posKey, snapshot)));

        // 4. currentTick
        int24 tick = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.currentTick, (hookData, poolId))),
            (int24)
        );

        // 5. poolRangeFeeGrowthInside
        uint256 feeGrowthInside0X128 = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.poolRangeFeeGrowthInside, (hookData, poolId, tick, rk))),
            (uint256)
        );

        // 6. setFeeGrowthBaseline
        LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.setFeeGrowthBaseline, (hookData, poolId, posKey, feeGrowthInside0X128)));

        // 7. incrementPosCount
        LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.incrementPosCount, (hookData, poolId)));

        return (IHooks.afterAddLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── beforeSwap ──

    function beforeSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        bytes calldata hookData
    ) external virtual returns (bytes4, BeforeSwapDelta, uint24) {
        bytes2 protocolFlags = getProtocolFlagFromHookData(hookData);
        address facet = address(getProtocolFacet(protocolFlags));
        PoolId poolId = PoolIdLibrary.toId(key);

        // 1. currentTick
        int24 tick = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.currentTick, (hookData, poolId))),
            (int24)
        );

        // 2. tstoreTick
        LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.tstoreTick, (hookData, tick)));

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
        bytes2 protocolFlags = getProtocolFlagFromHookData(hookData);
        address facet = address(getProtocolFacet(protocolFlags));
        PoolId poolId = PoolIdLibrary.toId(key);

        // 1. tloadTick (tickBefore)
        int24 tickBefore = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.tloadTick, (hookData))),
            (int24)
        );

        // 2. currentTick (tickAfter)
        int24 tickAfter = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.currentTick, (hookData, poolId))),
            (int24)
        );

        // 3. incrementOverlappingRanges
        (int24 tickMin, int24 tickMax) = sortTicks(tickBefore, tickAfter);
        LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.incrementOverlappingRanges, (hookData, poolId, tickMin, tickMax)));

        return (IHooks.afterSwap.selector, 0);
    }

    // ── beforeRemoveLiquidity ──

    function beforeRemoveLiquidity(
        address sender,
        PoolKey calldata key,
        ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4) {
        bytes2 protocolFlags = getProtocolFlagFromHookData(hookData);
        address facet = address(getProtocolFacet(protocolFlags));
        PoolId poolId = PoolIdLibrary.toId(key);

        // 1. positionKey
        bytes32 posKey = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.positionKey, (hookData, sender, params))),
            (bytes32)
        );

        // 2. latestPositionFeeGrowthInside
        (uint128 posLiquidity, uint256 feeLast0) = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.latestPositionFeeGrowthInside, (hookData, poolId, posKey))),
            (uint128, uint256)
        );

        // 3. currentTick
        int24 tick = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.currentTick, (hookData, poolId))),
            (int24)
        );

        // 4. poolRangeFeeGrowthInside
        TickRange rk = fromTicksPacked(params.tickLower, params.tickUpper);
        uint256 rangeFeeGrowth0 = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.poolRangeFeeGrowthInside, (hookData, poolId, tick, rk))),
            (uint256)
        );

        // 5. tstoreRemovalData
        LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.tstoreRemovalData, (hookData, feeLast0, posLiquidity, rangeFeeGrowth0)));

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
        bytes2 protocolFlags = getProtocolFlagFromHookData(hookData);
        address facet = address(getProtocolFacet(protocolFlags));
        PoolId poolId = PoolIdLibrary.toId(key);

        // 1. positionKey
        bytes32 posKey = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.positionKey, (hookData, sender, params))),
            (bytes32)
        );

        // 2. tloadRemovalData
        (uint256 positionFeeLast0X128, uint128 posLiq, uint256 rangeFeeGrowthNow0X128) = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.tloadRemovalData, (hookData))),
            (uint256, uint128, uint256)
        );

        // Partial remove guard — skip FCI accumulation if not full exit
        uint128 removedLiq = uint128(uint256(-params.liquidityDelta));
        if (posLiq != removedLiq) {
            return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
        }

        // 3. getFeeGrowthBaseline
        uint256 baseline0X128 = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getFeeGrowthBaseline, (hookData, poolId, posKey))),
            (uint256)
        );

        // 4. removePositionInRange
        LiquidityPositionSnapshot memory snapshot = LiquidityPositionSnapshot({
            config: PositionConfig({poolKey: key, tickLower: params.tickLower, tickUpper: params.tickUpper}),
            liquidity: posLiq,
            feeGrowthInside0LastX128: positionFeeLast0X128,
            feeGrowthInside1LastX128: 0
        });
        (SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) = abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.removePositionInRange, (hookData, posKey, snapshot))),
            (SwapCount, BlockCount, uint128)
        );

        // 5. FCI accumulation (xk computation is algorithm, lives in V2)
        if (!swapLifetime.isZero()) {
            FeeShareRatio xk = fromFeeGrowthDelta(
                rangeFeeGrowthNow0X128, positionFeeLast0X128, baseline0X128,
                posLiq, totalRangeLiq
            );
            uint256 xSquaredQ128 = xk.square();

            // 6. addStateTerm
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.addStateTerm, (hookData, poolId, blockLifetime, xSquaredQ128)));

            // 7. addEpochTerm
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.addEpochTerm, (hookData, poolId, blockLifetime, xSquaredQ128)));
        }

        // 8. decrementPosCount
        LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.decrementPosCount, (hookData, poolId)));

        // 9. deleteFeeGrowthBaseline
        LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.deleteFeeGrowthBaseline, (hookData, poolId, posKey)));

        return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
    }

    // ── View (protocol-scoped via bytes2 flags) ──

    function getIndex(PoolKey calldata key, bytes2 flags) external view returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(flags);
        PoolId poolId = PoolIdLibrary.toId(key);
        indexA = $.fciState[poolId].toIndexA();
        thetaSum = $.fciState[poolId].thetaSum;
        removedPosCount = $.fciState[poolId].removedPosCount;
    }

    function getDeltaPlus(PoolKey calldata key, bytes2 flags) external view returns (uint128 deltaPlus_) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(flags);
        deltaPlus_ = $.fciState[PoolIdLibrary.toId(key)].deltaPlus();
    }

    function getAtNull(PoolKey calldata key, bytes2 flags) external view returns (uint128 atNull_) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(flags);
        atNull_ = $.fciState[PoolIdLibrary.toId(key)].atNull();
    }

    function getThetaSum(PoolKey calldata key, bytes2 flags) external view returns (uint256 thetaSum_) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(flags);
        thetaSum_ = $.fciState[PoolIdLibrary.toId(key)].thetaSum;
    }

    function getDeltaPlusEpoch(PoolKey calldata key, bytes2 flags) external view returns (uint128 deltaPlus_) {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(flags);
        deltaPlus_ = $.epochStates[PoolIdLibrary.toId(key)][$.currentEpochId[PoolIdLibrary.toId(key)]].deltaPlus();
    }

    // ── Initialization ──

    function initialize(address _owner) external {
        initOwner(_owner);
    }

    // ── Facet admin storage (writes to V2's storage context for delegatecall reads) ──

    function setFacetFci(bytes2 flags, IFeeConcentrationIndex fci) external {
        requireOwner();
        _setFci(flags, fci);
    }

    function setFacetProtocolStateView(bytes2 flags, IProtocolStateView stateView) external {
        requireOwner();
        _setProtocolStateView(flags, stateView);
    }

    // ── Registration ──

    function registerProtocolFacet(bytes2 flags, IFCIProtocolFacet facet) external {
        requireOwner();
        setProtocolFacet(flags, facet);
    }

    function getRegisteredProtocolFacet(bytes2 flags) external view returns (IFCIProtocolFacet) {
        return getProtocolFacet(flags);
    }

    // ── IERC165 ──

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IFeeConcentrationIndex).interfaceId
            || interfaceId == type(IERC165).interfaceId;
    }
}
