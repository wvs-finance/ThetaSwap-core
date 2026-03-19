// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {TickRange} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/types/FeeConcentrationStateMod.sol";
import {FeeConcentrationEpochStorage} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";
import {RangeSnapshot} from "@fee-concentration-index-v2/types/RangeSnapshot.sol";
import {EpochSnapshot} from "@fee-concentration-index-v2/types/EpochSnapshot.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {
    FeeConcentrationIndexV2Storage
} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexStorageV2Mod.sol";
import {
    protocolFciStorage, protocolEpochFciStorage
} from "@fee-concentration-index-v2/modules/FCIProtocolFacetStorageMod.sol";
import {getProtocolFacet} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol";
import {LibCall} from "solady/utils/LibCall.sol";

/// @title FCIMetricsFacet
/// @notice Read-only diamond facet exposing all FCI persistent state.
/// MUST be installed on the same diamond as FeeConcentrationIndexV2 and protocol facets.
contract FCIMetricsFacet {

    // ── Pool-level metrics ──

    function getAccumulatedSum(PoolKey calldata key, bytes2 flags) external view returns (uint256) {
        return protocolFciStorage(flags).fciState[PoolIdLibrary.toId(key)].accumulatedSum;
    }

    function getActivePosCount(PoolKey calldata key, bytes2 flags) external view returns (uint256) {
        return protocolFciStorage(flags).fciState[PoolIdLibrary.toId(key)].posCount;
    }

    function getDeltaPlusPrice(PoolKey calldata key, bytes2 flags) external view returns (uint256) {
        return protocolFciStorage(flags).fciState[PoolIdLibrary.toId(key)].toDeltaPlusPrice();
    }

    // ── Range snapshots (delegated to protocol facet) ──

    function getRangeSnapshot(PoolKey calldata key, bytes2 flags, TickRange rk) external returns (RangeSnapshot memory) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryRangeSnapshot, (flags, poolId, rk))),
            (RangeSnapshot)
        );
    }

    function getActiveRanges(PoolKey calldata key, bytes2 flags) external returns (TickRange[] memory) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryActiveRanges, (flags, poolId))),
            (TickRange[])
        );
    }

    function getAllRangeSnapshots(PoolKey calldata key, bytes2 flags) external returns (RangeSnapshot[] memory) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryAllSnapshots, (flags, poolId))),
            (RangeSnapshot[])
        );
    }

    // ── Epoch state ──

    function getCurrentEpoch(PoolKey calldata key, bytes2 flags) external view returns (EpochSnapshot memory snapshot) {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(flags);
        PoolId poolId = PoolIdLibrary.toId(key);
        uint256 epochId = $.currentEpochId[poolId];
        snapshot.epochId = epochId;
        snapshot.epochLength = $.epochLength[poolId];
        if (epochId == 0) return snapshot;
        if (block.timestamp >= epochId + snapshot.epochLength) return snapshot;
        FeeConcentrationState storage state = $.epochStates[poolId][epochId];
        snapshot.accumulatedSum = state.accumulatedSum;
        snapshot.thetaSum = state.thetaSum;
        snapshot.posCount = state.posCount;
        snapshot.removedPosCount = state.removedPosCount;
        snapshot.indexA = state.toIndexA();
        snapshot.deltaPlus = state.deltaPlus();
    }

    function getEpochState(PoolKey calldata key, bytes2 flags, uint256 epochId) external view returns (EpochSnapshot memory snapshot) {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(flags);
        PoolId poolId = PoolIdLibrary.toId(key);
        snapshot.epochId = epochId;
        snapshot.epochLength = $.epochLength[poolId];
        FeeConcentrationState storage state = $.epochStates[poolId][epochId];
        snapshot.accumulatedSum = state.accumulatedSum;
        snapshot.thetaSum = state.thetaSum;
        snapshot.posCount = state.posCount;
        snapshot.removedPosCount = state.removedPosCount;
        snapshot.indexA = state.toIndexA();
        snapshot.deltaPlus = state.deltaPlus();
    }

    function getEpochMetadata(PoolKey calldata key, bytes2 flags) external view returns (uint256 currentEpochId, uint256 epochLength) {
        FeeConcentrationEpochStorage storage $ = protocolEpochFciStorage(flags);
        PoolId poolId = PoolIdLibrary.toId(key);
        currentEpochId = $.currentEpochId[poolId];
        epochLength = $.epochLength[poolId];
    }

    // ── Position-level (delegated to protocol facet) ──

    function getPositionBaseline(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryPositionBaseline, (flags, poolId, posKey))),
            (uint256)
        );
    }

    function getPositionAddBlock(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryPositionAddBlock, (flags, poolId, posKey))),
            (uint256)
        );
    }

    function getPositionSwapLifetime(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256) {
        address facet = address(getProtocolFacet(flags));
        PoolId poolId = PoolIdLibrary.toId(key);
        return abi.decode(
            LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.getRegistryPositionSwapLifetime, (flags, poolId, posKey))),
            (uint256)
        );
    }
}
