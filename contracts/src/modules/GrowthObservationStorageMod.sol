// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {CircularBuffer} from "openzeppelin-contracts/utils/structs/CircularBuffer.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {GrowthObservation} from "core/src/types/GrowthObservation.sol";
import {
    record as _record,
    observeAt as _observeAt,
    latestObservation as _latestObservation,
    oldestObservation as _oldestObservation,
    observationCount as _observationCount
} from "core/src/libraries/BlockNumberAwareGrowthObserverLib.sol";

// ── Diamond Storage ──

struct GrowthObservationStorage {
    mapping(PoolId => CircularBuffer.Bytes32CircularBuffer) buffers;
    mapping(PoolId => bool) initialized;
}

/// @dev keccak256("thetaswap.storage.GrowthObservationStorage")
bytes32 constant GROWTH_OBSERVATION_STORAGE_SLOT =
    0x4f58f0dc14989f533ec6a83b406d0cdb0185a40591c7e197eed7f8f68cda4a40;

// ── Errors ──

error PoolAlreadyInitialized();

// ── Internal Storage Access ──

function _growthObservationStorage() pure returns (GrowthObservationStorage storage s) {
    bytes32 slot = GROWTH_OBSERVATION_STORAGE_SLOT;
    assembly ("memory-safe") {
        s.slot := slot
    }
}

// ── Free Functions ──

/// @notice Initialize the observation ring buffer for a pool.
/// @dev Must be called exactly once per poolId before any recordObservation call.
///      Reverts with PoolAlreadyInitialized if called again (guard before setup — C6).
/// @param poolId The Uniswap V4 pool identifier.
/// @param size The ring buffer capacity (number of observation slots).
function initializePool(PoolId poolId, uint256 size) {
    GrowthObservationStorage storage $ = _growthObservationStorage();
    if ($.initialized[poolId]) revert PoolAlreadyInitialized();
    CircularBuffer.setup($.buffers[poolId], size);
    $.initialized[poolId] = true;
}

/// @notice Record an observation for a pool.
/// @dev Delegates to BlockNumberAwareGrowthObserverLib.record on the pool's buffer.
///      Does NOT check initialization — an uninitialized buffer panics naturally (0x32).
/// @param poolId The pool to record into.
/// @param blockNumber The block number of this observation.
/// @param relativeTimeDelta Seconds since the previous observation.
/// @param cumulativeGrowth The cumulative globalGrowth value.
function recordObservation(
    PoolId poolId,
    uint256 blockNumber,
    uint256 relativeTimeDelta,
    uint256 cumulativeGrowth
) {
    _record(
        _growthObservationStorage().buffers[poolId],
        blockNumber,
        relativeTimeDelta,
        cumulativeGrowth
    );
}

/// @notice Returns the observation at or before targetBlock for a pool.
/// @param poolId The pool to query.
/// @param targetBlock The block number to look up.
function observeAt(PoolId poolId, uint32 targetBlock) view returns (GrowthObservation) {
    return _observeAt(_growthObservationStorage().buffers[poolId], targetBlock);
}

/// @notice Returns the most recent observation for a pool.
/// @param poolId The pool to query.
function latestObservation(PoolId poolId) view returns (GrowthObservation) {
    return _latestObservation(_growthObservationStorage().buffers[poolId]);
}

/// @notice Returns the oldest observation still in the buffer for a pool.
/// @param poolId The pool to query.
function oldestObservation(PoolId poolId) view returns (GrowthObservation) {
    return _oldestObservation(_growthObservationStorage().buffers[poolId]);
}

/// @notice Returns the number of observations stored for a pool.
/// @param poolId The pool to query.
function observationCount(PoolId poolId) view returns (uint256) {
    return _observationCount(_growthObservationStorage().buffers[poolId]);
}
