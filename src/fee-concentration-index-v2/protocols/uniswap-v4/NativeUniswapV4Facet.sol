// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {Position} from "v4-core/src/libraries/Position.sol";
import {StateLibrary} from "v4-core/src/libraries/StateLibrary.sol";
import {TickRange, fromTicksPacked, intersects} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {LiquidityPositionSnapshot} from "@fee-concentration-index-v2/types/LiquidityPositionSnapshot.sol";
import {RangeSnapshot} from "@fee-concentration-index-v2/types/RangeSnapshot.sol";
import {NATIVE_V4} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {
    fciFacetAdminStorage, addPool, setProtocolStateView as _setProtocolStateView, setFci as _setFci
} from "@fee-concentration-index-v2/modules/FCIFacetAdminStorageMod.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {fromUniswapV4PoolKeyToPoolKey} from "./libraries/UniswapV4PoolKeyLib.sol";
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

/// @title NativeUniswapV4Facet
/// @dev Protocol facet for Uniswap V4 native hooks.
/// Called via delegatecall from FeeConcentrationIndexV2 for each behavioral function.
/// Contains ONLY behavioral functions — hook orchestration lives in V2.
/// Does NOT inherit IFCIProtocolFacet explicitly (SCOP: no is inheritance).
contract NativeUniswapV4Facet {

    address immutable _self;

    constructor() {
        _self = address(this);
    }

    modifier onlyDelegateCall() {
        require(address(this) != _self, "NativeUniswapV4Facet: direct call");
        require(address(this) == address(fciFacetAdminStorage(NATIVE_V4).fci), "NativeUniswapV4Facet: unauthorized caller");
        _;
    }

    // ── Admin (direct call, NOT delegatecall) ──

    event PoolAdded(address indexed facet, address indexed callback, PoolId indexed poolId, bytes2 protocolFlag, bytes data);

    /// @notice Initialize the facet — sets owner, PoolManager, and FCI reference.
    function initialize(address _owner, IProtocolStateView _protocolStateView, IFeeConcentrationIndex _fci, IUnlockCallback _callback) external {
        initOwner(_owner);
        _setProtocolStateView(NATIVE_V4, _protocolStateView);
        _setFci(NATIVE_V4, _fci);
        // V4 native has no callback — _callback is ignored (address(0))
    }
    error PoolAlreadyInitialized(PoolId poolId);

    /// @notice Register and initialize a V4 pool for FCI tracking.
    /// @dev poolRpt = abi.encode(PoolKey, uint160 sqrtPriceX96).
    function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey) {
        // 1. Decode poolRpt
        (PoolKey memory rawKey, uint160 sqrtPriceX96) = abi.decode(poolRpt, (PoolKey, uint160));

        // 2. Set FCI hook
        IHooks fciHook = IHooks(address(fciFacetAdminStorage(NATIVE_V4).fci));
        poolKey = fromUniswapV4PoolKeyToPoolKey(abi.encode(rawKey), fciHook);

        // 3. Initialize pool on PoolManager
        PoolId poolId = PoolIdLibrary.toId(poolKey);
        try IPoolManager(address(fciFacetAdminStorage(NATIVE_V4).protocolStateView)).initialize(poolKey, sqrtPriceX96) {
        } catch {
            revert PoolAlreadyInitialized(poolId);
        }

        // 4. Register
        addPool(NATIVE_V4, poolId);

        // NOTE: Epoch init must be called on FCI V2 (not facet) via
        // fci.initializeEpochPool(key, NATIVE_V4, 86400) so storage
        // lives in the same context as addEpochTerm (delegatecall).

        emit PoolAdded(address(this), address(fciFacetAdminStorage(NATIVE_V4).protocolStateView), poolId, NATIVE_V4, "");
    }

    /// @notice Set the protocol state view (PoolManager for V4).
    function setProtocolStateView(IProtocolStateView stateView) external {
        requireOwner();
        _setProtocolStateView(NATIVE_V4, stateView);
    }

    // ── Position key derivation ──

    function positionKey(bytes calldata, address sender, ModifyLiquidityParams calldata params) external view onlyDelegateCall returns (bytes32) {
        return Position.calculatePositionKey(sender, params.tickLower, params.tickUpper, params.salt);
    }

    // ── Fee growth reads ──

    function latestPositionFeeGrowthInside(bytes calldata, PoolId poolId, bytes32 posKey) external view onlyDelegateCall returns (uint128 posLiquidity, uint256 feeGrowthLast) {
        (posLiquidity, feeGrowthLast,) = StateLibrary.getPositionInfo(
            IPoolManager(address(fciFacetAdminStorage(NATIVE_V4).protocolStateView)),
            poolId,
            posKey
        );
    }

    function poolRangeFeeGrowthInside(bytes calldata, PoolId poolId, int24 currentTick_, TickRange tickRange) external view onlyDelegateCall returns (uint256 feeGrowthInside0X128) {
        IPoolManager manager = IPoolManager(address(fciFacetAdminStorage(NATIVE_V4).protocolStateView));
        int24 tickLower = tickRange.lowerTick();
        int24 tickUpper = tickRange.upperTick();

        (uint256 lowerOut0,) = StateLibrary.getTickFeeGrowthOutside(manager, poolId, tickLower);
        (uint256 upperOut0,) = StateLibrary.getTickFeeGrowthOutside(manager, poolId, tickUpper);

        unchecked {
            if (currentTick_ < tickLower) {
                feeGrowthInside0X128 = lowerOut0 - upperOut0;
            } else if (currentTick_ >= tickUpper) {
                feeGrowthInside0X128 = upperOut0 - lowerOut0;
            } else {
                (uint256 feeGrowthGlobal0X128,) = StateLibrary.getFeeGrowthGlobals(manager, poolId);
                feeGrowthInside0X128 = feeGrowthGlobal0X128 - lowerOut0 - upperOut0;
            }
        }
    }

    // ── Position registration ──

    function addPositionInRange(bytes calldata, bytes32 posKey, LiquidityPositionSnapshot calldata snapshot) external onlyDelegateCall {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(NATIVE_V4);
        PoolId poolId = PoolIdLibrary.toId(snapshot.config.poolKey);
        TickRange rk = fromTicksPacked(snapshot.config.tickLower, snapshot.config.tickUpper);
        $.registries[poolId].register(rk, posKey, snapshot.liquidity);
    }

    function removePositionInRange(bytes calldata, bytes32 posKey, LiquidityPositionSnapshot calldata snapshot) external onlyDelegateCall returns (SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(NATIVE_V4);
        PoolId poolId = PoolIdLibrary.toId(snapshot.config.poolKey);
        (, swapLifetime, blockLifetime, totalRangeLiq) = $.registries[poolId].deregister(posKey, snapshot.liquidity);
    }

    // ── Tick ──

    function currentTick(bytes calldata, PoolId poolId) external view onlyDelegateCall returns (int24) {
        (, int24 tick,,) = StateLibrary.getSlot0(
            IPoolManager(address(fciFacetAdminStorage(NATIVE_V4).protocolStateView)),
            poolId
        );
        return tick;
    }

    // ── Fee growth baseline ──

    function setFeeGrowthBaseline(bytes calldata, PoolId poolId, bytes32 posKey, uint256 feeGrowth) external onlyDelegateCall {
        protocolFciStorage(NATIVE_V4).feeGrowthBaseline0[poolId][posKey] = feeGrowth;
    }

    function getFeeGrowthBaseline(bytes calldata, PoolId poolId, bytes32 posKey) external view onlyDelegateCall returns (uint256) {
        return protocolFciStorage(NATIVE_V4).feeGrowthBaseline0[poolId][posKey];
    }

    function deleteFeeGrowthBaseline(bytes calldata, PoolId poolId, bytes32 posKey) external onlyDelegateCall {
        delete protocolFciStorage(NATIVE_V4).feeGrowthBaseline0[poolId][posKey];
    }

    // ── Position count ──

    function incrementPosCount(bytes calldata, PoolId poolId) external onlyDelegateCall {
        protocolFciStorage(NATIVE_V4).fciState[poolId].incrementPos();
    }

    function decrementPosCount(bytes calldata, PoolId poolId) external onlyDelegateCall {
        protocolFciStorage(NATIVE_V4).fciState[poolId].decrementPos();
    }

    // ── Transient storage ──

    function tstoreTick(bytes calldata, int24 tick) external onlyDelegateCall {
        _tstoreTick(NATIVE_V4, tick);
    }

    function tloadTick(bytes calldata) external onlyDelegateCall returns (int24 tick) {
        tick = _tloadTick(NATIVE_V4);
    }

    function tstoreRemovalData(bytes calldata, uint256 feeLast, uint128 posLiquidity, uint256 rangeFeeGrowth) external onlyDelegateCall {
        _tstoreRemovalData(NATIVE_V4, feeLast, posLiquidity, rangeFeeGrowth);
    }

    function tloadRemovalData(bytes calldata) external onlyDelegateCall returns (uint256 feeLast, uint128 posLiquidity, uint256 rangeFeeGrowth) {
        (feeLast, posLiquidity, rangeFeeGrowth) = _tloadRemovalData(NATIVE_V4);
    }

    // ── Overlapping ranges ──

    function incrementOverlappingRanges(bytes calldata, PoolId poolId, int24 tickMin, int24 tickMax) external onlyDelegateCall {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(NATIVE_V4);
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
        protocolFciStorage(NATIVE_V4).fciState[poolId].addTerm(blockLifetime, xSquaredQ128);
    }

    function addEpochTerm(bytes calldata, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) external onlyDelegateCall {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(NATIVE_V4);
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
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(NATIVE_V4);
        bytes32 rkRaw = TickRange.unwrap(rk);
        snapshot.tickLower = rk.lowerTick();
        snapshot.tickUpper = rk.upperTick();
        snapshot.totalLiquidity = $.registries[poolId].totalRangeLiquidity[rkRaw];
        snapshot.swapCount = SwapCount.unwrap($.registries[poolId].rangeSwapCount[rkRaw]);
        snapshot.positionKeys = $.registries[poolId].positionsInRange(rk);
        snapshot.positionCount = snapshot.positionKeys.length;
    }

    function getRegistryActiveRanges(bytes2, PoolId poolId) external view returns (TickRange[] memory ranges) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(NATIVE_V4);
        uint256 count = $.registries[poolId].activeRangeCount();
        ranges = new TickRange[](count);
        for (uint256 i; i < count; ++i) {
            ranges[i] = TickRange.wrap($.registries[poolId].activeRangeAt(i));
        }
    }

    function getRegistryAllSnapshots(bytes2, PoolId poolId) external view returns (RangeSnapshot[] memory snapshots) {
        FeeConcentrationIndexV2Storage storage $ = protocolFciStorage(NATIVE_V4);
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
        return protocolFciStorage(NATIVE_V4).feeGrowthBaseline0[poolId][posKey];
    }

    function getRegistryPositionAddBlock(bytes2, PoolId poolId, bytes32 posKey) external view returns (uint256) {
        return protocolFciStorage(NATIVE_V4).registries[poolId].positionAddBlock[posKey];
    }

    function getRegistryPositionSwapLifetime(bytes2, PoolId poolId, bytes32 posKey) external view returns (uint256) {
        return SwapCount.unwrap(protocolFciStorage(NATIVE_V4).registries[poolId].getLifetime(posKey));
    }
}
