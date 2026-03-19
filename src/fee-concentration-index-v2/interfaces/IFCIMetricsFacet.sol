// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {TickRange} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {RangeSnapshot} from "@fee-concentration-index-v2/types/RangeSnapshot.sol";
import {EpochSnapshot} from "@fee-concentration-index-v2/types/EpochSnapshot.sol";

interface IFCIMetricsFacet {
    // ── Pool-level ──
    function getAccumulatedSum(PoolKey calldata key, bytes2 flags) external view returns (uint256);
    function getActivePosCount(PoolKey calldata key, bytes2 flags) external view returns (uint256);
    function getDeltaPlusPrice(PoolKey calldata key, bytes2 flags) external view returns (uint256);

    // ── Range (non-view: delegatecall to protocol facet; staticcall enforced at diamond level) ──
    function getRangeSnapshot(PoolKey calldata key, bytes2 flags, TickRange rk) external returns (RangeSnapshot memory);
    function getActiveRanges(PoolKey calldata key, bytes2 flags) external returns (TickRange[] memory);
    function getAllRangeSnapshots(PoolKey calldata key, bytes2 flags) external returns (RangeSnapshot[] memory);

    // ── Epoch ──
    function getCurrentEpoch(PoolKey calldata key, bytes2 flags) external view returns (EpochSnapshot memory);
    function getEpochState(PoolKey calldata key, bytes2 flags, uint256 epochId) external view returns (EpochSnapshot memory);
    function getEpochMetadata(PoolKey calldata key, bytes2 flags) external view returns (uint256 currentEpochId, uint256 epochLength);

    // ── Position (non-view: delegatecall to protocol facet; staticcall enforced at diamond level) ──
    function getPositionBaseline(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256);
    function getPositionAddBlock(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256);
    function getPositionSwapLifetime(PoolKey calldata key, bytes2 flags, bytes32 posKey) external returns (uint256);
}
