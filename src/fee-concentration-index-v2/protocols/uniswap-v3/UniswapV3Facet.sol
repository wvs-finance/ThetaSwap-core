// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {TickRange, fromTicksPacked, intersects} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {LiquidityPositionSnapshot} from "@fee-concentration-index-v2/types/LiquidityPositionSnapshot.sol";
import {RangeSnapshot} from "@fee-concentration-index-v2/types/RangeSnapshot.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {
    fciFacetAdminStorage, addPool,
    setProtocolStateView as _setProtocolStateView,
    setFci as _setFci,
    setProtocolCallback as _setProtocolCallback
} from "@fee-concentration-index-v2/modules/FCIFacetAdminStorageMod.sol";
import {
    FeeConcentrationIndexV2Storage
} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol";
import {
    protocolFciStorage, protocolEpochFciStorage,
    tstoreTick as _tstoreTick,
    tloadTick as _tloadTick,
    tstoreRemovalData as _tstoreRemovalData,
    tloadRemovalData as _tloadRemovalData
} from "@fee-concentration-index-v2/modules/FCIProtocolFacetStorageMod.sol";
import {FeeConcentrationEpochStorage} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";
import {requireOwner, initOwner} from "@fee-concentration-index-v2/modules/dependencies/LibOwner.sol";
import {fromUniswapV3PoolToPoolKey} from "./libraries/UniswapV3PoolKeyLib.sol";
import {encodeV3PoolAddedData} from "./libraries/UniswapV3PoolAddedLib.sol";
import {decodePoolAddress, decodeActionType, decodeSwapTick, decodePosLiqBefore} from "./libraries/V3HookDataLib.sol";
import {BEFORE_SWAP} from "./libraries/V3ActionTypes.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";

/// @title UniswapV3Facet
/// @dev Protocol facet for Uniswap V3 reactive integration.
/// Called via delegatecall from FeeConcentrationIndexV2 for each behavioral function.
/// Contains ONLY behavioral functions — hook orchestration lives in V2.
/// Does NOT inherit IFCIProtocolFacet explicitly (SCOP: no is inheritance).
contract UniswapV3Facet {

    address immutable _self;

    constructor() {
        _self = address(this);
    }

    modifier onlyDelegateCall() {
        require(address(this) != _self, "UniswapV3Facet: direct call");
        require(address(this) == address(fciFacetAdminStorage(UNISWAP_V3_REACTIVE).fci), "UniswapV3Facet: unauthorized caller");
        _;
    }

    // ── Admin (direct call, NOT delegatecall) ──

    event PoolAdded(address indexed facet, address indexed callback, PoolId indexed poolId, bytes2 protocolFlag, bytes data);
    error PoolAlreadyRegistered(PoolId poolId);

    function initialize(address _owner, IProtocolStateView _protocolStateView, IFeeConcentrationIndex _fci, IUnlockCallback _callback) external {
        initOwner(_owner);
        _setProtocolStateView(UNISWAP_V3_REACTIVE, _protocolStateView);
        _setFci(UNISWAP_V3_REACTIVE, _fci);
        _setProtocolCallback(UNISWAP_V3_REACTIVE, _callback);
    }

    /// @notice Register a V3 pool for FCI tracking.
    /// @dev poolRpt = abi.encode(IUniswapV3Pool).
    function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey) {
        IUniswapV3Pool v3Pool = abi.decode(poolRpt, (IUniswapV3Pool));
        IHooks fciHook = IHooks(address(fciFacetAdminStorage(UNISWAP_V3_REACTIVE).fci));
        poolKey = fromUniswapV3PoolToPoolKey(v3Pool, fciHook);
        PoolId poolId = PoolIdLibrary.toId(poolKey);
        addPool(UNISWAP_V3_REACTIVE, poolId);

        // NOTE: Epoch init must be called on FCI V2 (not facet) via
        // fci.initializeEpochPool(key, UNISWAP_V3_REACTIVE, 86400)

        emit PoolAdded(
            address(this),
            address(fciFacetAdminStorage(UNISWAP_V3_REACTIVE).protocolCallback),
            poolId,
            UNISWAP_V3_REACTIVE,
            encodeV3PoolAddedData(block.chainid, address(v3Pool), address(v3Pool))
        );
    }

    function setProtocolStateView(IProtocolStateView stateView) external {
        requireOwner();
        _setProtocolStateView(UNISWAP_V3_REACTIVE, stateView);
    }

    // ── Position key derivation ──

    function positionKey(bytes calldata, address sender, ModifyLiquidityParams calldata params) external view onlyDelegateCall returns (bytes32) {
        return keccak256(abi.encodePacked(sender, params.tickLower, params.tickUpper));
    }

    // ── Fee growth reads ──

    function latestPositionFeeGrowthInside(bytes calldata hookData, PoolId poolId, bytes32 posKey) external view onlyDelegateCall returns (uint128 posLiquidity, uint256 feeGrowthLast) {
        address pool = decodePoolAddress(hookData);
        (posLiquidity, feeGrowthLast,,,) = IUniswapV3Pool(pool).positions(posKey);

        // V3 reactive burn path: hookData carries posLiqBefore from ReactVM shadow.
        // V1 approach: x_k = posLiq / totalRangeLiq (exact for V3 — fees are per-unit-of-liq).
        // Set feeGrowthLast = 0; combined with getFeeGrowthBaseline returning 0,
        // fromFeeGrowthDelta reduces to feeRatio=1 × posLiq/totalRangeLiq.
        if (hookData.length >= 39) {
            uint128 posLiqOverride = decodePosLiqBefore(hookData);
            if (posLiqOverride > 0) {
                posLiquidity = posLiqOverride;
                feeGrowthLast = 0;
            }
        }
    }

    function poolRangeFeeGrowthInside(bytes calldata hookData, PoolId, int24 currentTick_, TickRange tickRange) external view onlyDelegateCall returns (uint256 feeGrowthInside0X128) {
        address pool = decodePoolAddress(hookData);
        int24 tickLower = tickRange.lowerTick();
        int24 tickUpper = tickRange.upperTick();

        (,,uint256 lowerFeeGrowthOutside0,,,,,) = IUniswapV3Pool(pool).ticks(tickLower);
        (,,uint256 upperFeeGrowthOutside0,,,,,) = IUniswapV3Pool(pool).ticks(tickUpper);

        unchecked {
            if (currentTick_ < tickLower) {
                feeGrowthInside0X128 = lowerFeeGrowthOutside0 - upperFeeGrowthOutside0;
            } else if (currentTick_ >= tickUpper) {
                feeGrowthInside0X128 = upperFeeGrowthOutside0 - lowerFeeGrowthOutside0;
            } else {
                uint256 feeGrowthGlobal0X128 = IUniswapV3Pool(pool).feeGrowthGlobal0X128();
                feeGrowthInside0X128 = feeGrowthGlobal0X128 - lowerFeeGrowthOutside0 - upperFeeGrowthOutside0;
            }
        }
    }

    // ── Position registration ──

    function addPositionInRange(bytes calldata, bytes32 posKey, LiquidityPositionSnapshot calldata snapshot) external onlyDelegateCall {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
        PoolId poolId = PoolIdLibrary.toId(snapshot.config.poolKey);
        TickRange rk = fromTicksPacked(snapshot.config.tickLower, snapshot.config.tickUpper);
        $.registries[poolId].register(rk, posKey, snapshot.liquidity);
    }

    function removePositionInRange(bytes calldata, bytes32 posKey, LiquidityPositionSnapshot calldata snapshot) external onlyDelegateCall returns (SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
        PoolId poolId = PoolIdLibrary.toId(snapshot.config.poolKey);
        (, swapLifetime, blockLifetime, totalRangeLiq) = $.registries[poolId].deregister(posKey, snapshot.liquidity);
    }

    // ── Tick ──

    function currentTick(bytes calldata hookData, PoolId) external view onlyDelegateCall returns (int24) {
        uint8 action = decodeActionType(hookData);
        if (action == BEFORE_SWAP) {
            return decodeSwapTick(hookData);
        }
        // AFTER_SWAP, AFTER_ADD_LIQUIDITY, BEFORE_REMOVE_LIQUIDITY — read from V3 pool
        address pool = decodePoolAddress(hookData);
        (, int24 tick,,,,,) = IUniswapV3Pool(pool).slot0();
        return tick;
    }

    // ── Fee growth baseline ──

    function setFeeGrowthBaseline(bytes calldata, PoolId poolId, bytes32 posKey, uint256 feeGrowth) external onlyDelegateCall {
        protocolFciStorage(UNISWAP_V3_REACTIVE).feeGrowthBaseline0[poolId][posKey] = feeGrowth;
    }

    function getFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 posKey) external view onlyDelegateCall returns (uint256) {
        // V3 reactive burn path: return 0 so fromFeeGrowthDelta reduces to posLiq/totalRangeLiq.
        if (hookData.length >= 39) {
            uint128 posLiqOverride = decodePosLiqBefore(hookData);
            if (posLiqOverride > 0) return 0;
        }
        return protocolFciStorage(UNISWAP_V3_REACTIVE).feeGrowthBaseline0[poolId][posKey];
    }

    function deleteFeeGrowthBaseline(bytes calldata, PoolId poolId, bytes32 posKey) external onlyDelegateCall {
        delete protocolFciStorage(UNISWAP_V3_REACTIVE).feeGrowthBaseline0[poolId][posKey];
    }

    // ── Position count ──

    function incrementPosCount(bytes calldata, PoolId poolId) external onlyDelegateCall {
        protocolFciStorage(UNISWAP_V3_REACTIVE).fciState[poolId].incrementPos();
    }

    function decrementPosCount(bytes calldata, PoolId poolId) external onlyDelegateCall {
        protocolFciStorage(UNISWAP_V3_REACTIVE).fciState[poolId].decrementPos();
    }

    // ── Transient storage ──

    function tstoreTick(bytes calldata, int24) external onlyDelegateCall {
        // No-op for V3 reactive — tick comes from hookData, not transient storage
    }

    function tloadTick(bytes calldata hookData) external onlyDelegateCall returns (int24 tick) {
        // V3 reactive: read tickBefore from hookData (injected by payload mutator)
        tick = decodeSwapTick(hookData);
    }

    function tstoreRemovalData(bytes calldata, uint256 feeLast, uint128 posLiquidity, uint256 rangeFeeGrowth) external onlyDelegateCall {
        // Uses transient storage — beforeRemoveLiquidity and afterRemoveLiquidity
        // are called sequentially in the same transaction by the callback.
        _tstoreRemovalData(UNISWAP_V3_REACTIVE, feeLast, posLiquidity, rangeFeeGrowth);
    }

    function tloadRemovalData(bytes calldata) external onlyDelegateCall returns (uint256 feeLast, uint128 posLiquidity, uint256 rangeFeeGrowth) {
        (feeLast, posLiquidity, rangeFeeGrowth) = _tloadRemovalData(UNISWAP_V3_REACTIVE);
    }

    // ── Overlapping ranges ──

    function incrementOverlappingRanges(bytes calldata, PoolId poolId, int24 tickMin, int24 tickMax) external onlyDelegateCall {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
        uint256 count = $.registries[poolId].activeRangeCount();
        for (uint256 i; i < count; ++i) {
            bytes32 rkRaw = $.registries[poolId].activeRangeAt(i);
            TickRange rk = TickRange.wrap(rkRaw);
            if (intersects(rk.lowerTick(), rk.upperTick(), tickMin, tickMax)) {
                $.registries[poolId].incrementRangeSwapCount(rk);
            }
        }
    }

    // ── FCI state accumulation ──

    function addStateTerm(bytes calldata, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) external onlyDelegateCall {
        protocolFciStorage(UNISWAP_V3_REACTIVE).fciState[poolId].addTerm(blockLifetime, xSquaredQ128);
    }

    function addEpochTerm(bytes calldata, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) external onlyDelegateCall {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(UNISWAP_V3_REACTIVE);
        uint256 epochLen = $.epochLength[poolId];
        if (epochLen == 0) return;

        uint256 epochId = $.currentEpochId[poolId];
        if (block.timestamp >= epochId + epochLen) {
            epochId = block.timestamp;
            $.currentEpochId[poolId] = epochId;
        }

        $.epochStates[poolId][epochId].addTerm(blockLifetime, xSquaredQ128);
    }

    // ── Registry reads (metrics facet support) ──

    function getRegistryRangeSnapshot(bytes2, PoolId poolId, TickRange rk) external view returns (RangeSnapshot memory snapshot) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
        bytes32 rkRaw = TickRange.unwrap(rk);
        snapshot.tickLower = rk.lowerTick();
        snapshot.tickUpper = rk.upperTick();
        snapshot.totalLiquidity = $.registries[poolId].totalRangeLiquidity[rkRaw];
        snapshot.swapCount = SwapCount.unwrap($.registries[poolId].rangeSwapCount[rkRaw]);
        snapshot.positionKeys = $.registries[poolId].positionsInRange(rk);
        snapshot.positionCount = snapshot.positionKeys.length;
    }

    function getRegistryActiveRanges(bytes2, PoolId poolId) external view returns (TickRange[] memory ranges) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
        uint256 count = $.registries[poolId].activeRangeCount();
        ranges = new TickRange[](count);
        for (uint256 i; i < count; ++i) {
            ranges[i] = TickRange.wrap($.registries[poolId].activeRangeAt(i));
        }
    }

    function getRegistryAllSnapshots(bytes2, PoolId poolId) external view returns (RangeSnapshot[] memory snapshots) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(UNISWAP_V3_REACTIVE);
        uint256 count = $.registries[poolId].activeRangeCount();
        snapshots = new RangeSnapshot[](count);
        for (uint256 i; i < count; ++i) {
            TickRange rk = TickRange.wrap($.registries[poolId].activeRangeAt(i));
            bytes32 rkRaw = TickRange.unwrap(rk);
            snapshots[i].tickLower = rk.lowerTick();
            snapshots[i].tickUpper = rk.upperTick();
            snapshots[i].totalLiquidity = $.registries[poolId].totalRangeLiquidity[rkRaw];
            snapshots[i].swapCount = SwapCount.unwrap($.registries[poolId].rangeSwapCount[rkRaw]);
            snapshots[i].positionKeys = $.registries[poolId].positionsInRange(rk);
            snapshots[i].positionCount = snapshots[i].positionKeys.length;
        }
    }

    function getRegistryPositionBaseline(bytes2, PoolId poolId, bytes32 posKey) external view returns (uint256) {
        return protocolFciStorage(UNISWAP_V3_REACTIVE).feeGrowthBaseline0[poolId][posKey];
    }

    function getRegistryPositionAddBlock(bytes2, PoolId poolId, bytes32 posKey) external view returns (uint256) {
        return protocolFciStorage(UNISWAP_V3_REACTIVE).registries[poolId].positionAddBlock[posKey];
    }

    function getRegistryPositionSwapLifetime(bytes2, PoolId poolId, bytes32 posKey) external view returns (uint256) {
        return SwapCount.unwrap(protocolFciStorage(UNISWAP_V3_REACTIVE).registries[poolId].getLifetime(posKey));
    }
}
