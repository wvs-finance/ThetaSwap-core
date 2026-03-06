// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {FeeConcentrationIndexStorage} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {CollectedFees} from "../../types/CollectedFeesMod.sol";

// Extension storage — only fields that FeeConcentrationIndexStorage does not have.
struct ReactiveHookAdapterStorage {
    mapping(PoolId => mapping(bytes32 => CollectedFees)) collectedFees;
}

// Reuses FeeConcentrationIndexStorage at a distinct slot for V3 pool FCI state.
bytes32 constant REACTIVE_FCI_STORAGE_SLOT = keccak256("ReactiveHookAdapter.fci.storage");
bytes32 constant REACTIVE_ADAPTER_STORAGE_SLOT = keccak256("ReactiveHookAdapter.adapter.storage");

function reactiveFciStorage() pure returns (FeeConcentrationIndexStorage storage s) {
    bytes32 slot = REACTIVE_FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

function reactiveAdapterStorage() pure returns (ReactiveHookAdapterStorage storage s) {
    bytes32 slot = REACTIVE_ADAPTER_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

// ── CollectedFees accessors (adapter's own storage concern) ──

function getCollectedFees(PoolId poolId, bytes32 positionKey) view returns (CollectedFees memory) {
    return reactiveAdapterStorage().collectedFees[poolId][positionKey];
}

function addCollectedFees(PoolId poolId, bytes32 positionKey, uint256 amount0, uint256 amount1) {
    CollectedFees storage fees = reactiveAdapterStorage().collectedFees[poolId][positionKey];
    fees.amount0 += amount0;
    fees.amount1 += amount1;
}

function deleteCollectedFees(PoolId poolId, bytes32 positionKey) {
    delete reactiveAdapterStorage().collectedFees[poolId][positionKey];
}
