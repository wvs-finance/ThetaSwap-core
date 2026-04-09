// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {OraclePack} from "panoptic-v2/src/types/OraclePack.sol";
import {CircularBuffer} from "openzeppelin-contracts/utils/structs/CircularBuffer.sol";
import {updateGrowthEMA} from "core/src/libraries/transformations/EMAGrowthTransformationLib.sol";
import {
    GrowthObservationStorage,
    _growthObservationStorage
} from "core/src/modules/GrowthObservationStorageMod.sol";

// ── Diamond Storage ──

struct EMAGrowthTransformationStorage {
    mapping(PoolId => OraclePack) oraclePacks;
    mapping(PoolId => bool) initialized;
    mapping(PoolId => uint96) emaPeriodsConfig;
    mapping(PoolId => int24) clampDeltaConfig;
}

/// @dev keccak256("thetaswap.storage.EMAGrowthTransformation")
bytes32 constant EMA_GROWTH_TRANSFORMATION_STORAGE_SLOT =
    0x343bdefdc18c4e700c86da83b816cde11ce64f06179e4a37d2d13986269d2913;

// ── Errors ──

error EMAAlreadyInitialized();
error EMANotInitialized();

// ── Internal Storage Access ──

function _emaStorage() pure returns (EMAGrowthTransformationStorage storage s) {
    bytes32 slot = EMA_GROWTH_TRANSFORMATION_STORAGE_SLOT;
    assembly ("memory-safe") {
        s.slot := slot
    }
}

// ── Free Functions ──

/// @notice Initialize EMA state and config for a pool.
/// @dev Must be called exactly once per poolId. Config (EMAperiods, clampDelta) is
///      write-once and immutable after initialization. OraclePack starts at zero state.
///      The EMAAlreadyInitialized check precedes all writes (C7).
/// @param poolId The Uniswap V4 pool identifier.
/// @param EMAperiods Packed uint96: four uint24 periods (spot, fast, slow, eons).
/// @param clampDelta Maximum tick change per update (manipulation resistance).
function initializeEMA(PoolId poolId, uint96 EMAperiods, int24 clampDelta) {
    EMAGrowthTransformationStorage storage $ = _emaStorage();
    if ($.initialized[poolId]) revert EMAAlreadyInitialized();
    $.emaPeriodsConfig[poolId] = EMAperiods;
    $.clampDeltaConfig[poolId] = clampDelta;
    $.oraclePacks[poolId] = OraclePack.wrap(0);
    $.initialized[poolId] = true;
}

/// @notice Update the EMA oracle for a pool by reading observations and feeding
///         the growth tick into OraclePack.
/// @dev Reads Layer 1 observation buffer (cross-module) and Layer 2 config/state (own).
///      Delegates to EMAGrowthTransformationLib.updateGrowthEMA (stateless).
///      Stores the returned OraclePack. Same-epoch calls are no-ops (OraclePack unchanged).
///      The EMANotInitialized check precedes all reads (C6).
/// @param poolId The pool to update.
function updateEMA(PoolId poolId) {
    EMAGrowthTransformationStorage storage $ = _emaStorage();
    if (!$.initialized[poolId]) revert EMANotInitialized();

    // Read Layer 1 observation buffer (cross-module access via C9)
    CircularBuffer.Bytes32CircularBuffer storage buffer =
        _growthObservationStorage().buffers[poolId];

    // Read Layer 2 state and config
    OraclePack currentOraclePack = $.oraclePacks[poolId];
    uint96 periods = $.emaPeriodsConfig[poolId];
    int24 clamp = $.clampDeltaConfig[poolId];

    // Delegate to stateless transformation library
    OraclePack updatedOraclePack = updateGrowthEMA(buffer, currentOraclePack, periods, clamp);

    // Persist
    $.oraclePacks[poolId] = updatedOraclePack;
}

/// @notice Returns the current OraclePack for a pool.
/// @dev Returns OraclePack.wrap(0) for uninitialized pools (Solidity mapping default).
/// @param poolId The pool to query.
function getOraclePack(PoolId poolId) view returns (OraclePack) {
    return _emaStorage().oraclePacks[poolId];
}

/// @notice Returns the EMA configuration for a pool.
/// @dev Returns (0, 0) for uninitialized pools (Solidity mapping default).
/// @param poolId The pool to query.
function getEMAConfig(PoolId poolId) view returns (uint96 EMAperiods, int24 clampDelta) {
    EMAGrowthTransformationStorage storage $ = _emaStorage();
    EMAperiods = $.emaPeriodsConfig[poolId];
    clampDelta = $.clampDeltaConfig[poolId];
}
