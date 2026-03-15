// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/types/FeeConcentrationStateMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";

// Diamond storage for the epoch-reset FCI metric.
// Runs via delegatecall in MasterHook's storage context.
// Namespace: keccak256("thetaSwap.fci.epoch") — disjoint from cumulative FCI and all other facets.
//
// Design: epoch-indexed mapping (Option C — destruction by abandonment).
// Each epoch gets a fresh FeeConcentrationState at a new mapping slot keyed by epochId.
// When the epoch expires, currentEpochId advances and the old state becomes unreachable.
// No explicit delete, no zeroing SSTOREs. Dead storage is negligible (~4 slots/pool/epoch).

struct FeeConcentrationEpochStorage {
    // Current epoch ID per pool (block.timestamp at epoch start)
    mapping(PoolId => uint256) currentEpochId;
    // Epoch duration in seconds per pool (e.g. 86400 for 1 day)
    mapping(PoolId => uint256) epochLength;
    // Epoch-indexed accumulator: epochStates[poolId][epochId] → FeeConcentrationState
    // Old epochs become unreachable when currentEpochId advances — destruction by abandonment.
    mapping(PoolId => mapping(uint256 => FeeConcentrationState)) epochStates;
}

bytes32 constant EPOCH_FCI_STORAGE_SLOT = keccak256("thetaSwap.fci.epoch");

// Reactive epoch FCI: same struct at a disjoint slot for V3 pool state.
// When epoch FCI runs on behalf of the reactive adapter, state is stored
// here so it never collides with native V4 epoch state.
bytes32 constant REACTIVE_EPOCH_FCI_STORAGE_SLOT = keccak256("thetaSwap.fci.epoch.reactive");

function epochFciStorage() pure returns (FeeConcentrationEpochStorage storage s) {
    bytes32 slot = EPOCH_FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

function reactiveEpochFciStorage() pure returns (FeeConcentrationEpochStorage storage s) {
    bytes32 slot = REACTIVE_EPOCH_FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

// ── Epoch term accumulation ──

function addEpochTerm(
    FeeConcentrationEpochStorage storage $,
    PoolId poolId,
    BlockCount blockLifetime,
    uint256 xSquaredQ128
) {
    uint256 epochLen = $.epochLength[poolId];
    if (epochLen == 0) return; // epoch not initialized for this pool

    uint256 epochId = $.currentEpochId[poolId];
    if (block.timestamp >= epochId + epochLen) {
        // Epoch expired — advance to new epoch. Old state abandoned.
        epochId = block.timestamp;
        $.currentEpochId[poolId] = epochId;
    }

    $.epochStates[poolId][epochId].addTerm(blockLifetime, xSquaredQ128);
}

function addEpochTerm(PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) {
    addEpochTerm(epochFciStorage(), poolId, blockLifetime, xSquaredQ128);
}

// ── Epoch delta plus (read) ──

function epochDeltaPlus(
    FeeConcentrationEpochStorage storage $,
    PoolId poolId
) view returns (uint128) {
    uint256 epochId = $.currentEpochId[poolId];
    if (epochId == 0) return 0; // not initialized

    // If epoch expired, current epoch has no data — return 0
    uint256 epochLen = $.epochLength[poolId];
    if (block.timestamp >= epochId + epochLen) return 0;

    return $.epochStates[poolId][epochId].deltaPlus();
}

function epochDeltaPlus(PoolId poolId) view returns (uint128) {
    return epochDeltaPlus(epochFciStorage(), poolId);
}

// ── Epoch initialization ──

function initializeEpoch(
    FeeConcentrationEpochStorage storage $,
    PoolId poolId,
    uint256 epochLengthSeconds
) {
    $.epochLength[poolId] = epochLengthSeconds;
    $.currentEpochId[poolId] = block.timestamp;
}

function initializeEpoch(PoolId poolId, uint256 epochLengthSeconds) {
    initializeEpoch(epochFciStorage(), poolId, epochLengthSeconds);
}
