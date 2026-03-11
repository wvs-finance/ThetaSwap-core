// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeConcentrationIndexStorage} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";

// Reuses FeeConcentrationIndexStorage at a distinct slot for V3 pool FCI state.
bytes32 constant REACTIVE_FCI_STORAGE_SLOT = keccak256("ReactiveHookAdapter.fci.storage");

function reactiveFciStorage() pure returns (FeeConcentrationIndexStorage storage s) {
    bytes32 slot = REACTIVE_FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

// V3-specific adapter state: feeGrowthInside snapshots taken at mint time.
// Separate diamond slot from FCI to keep struct layouts independent.
struct V3AdapterStorage {
    // poolId => positionKey => feeGrowthInside0X128 at mint time
    mapping(PoolId => mapping(bytes32 => uint256)) feeGrowthSnapshot0;
}

bytes32 constant V3_ADAPTER_STORAGE_SLOT = keccak256("ReactiveHookAdapter.v3.storage");

function v3AdapterStorage() pure returns (V3AdapterStorage storage s) {
    bytes32 slot = V3_ADAPTER_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}
