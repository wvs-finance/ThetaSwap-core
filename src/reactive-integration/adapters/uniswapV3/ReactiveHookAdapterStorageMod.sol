// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeConcentrationIndexStorage} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";

// Reuses FeeConcentrationIndexStorage at a distinct slot for V3 pool FCI state.
bytes32 constant REACTIVE_FCI_STORAGE_SLOT = keccak256("ReactiveHookAdapter.fci.storage");

function reactiveFciStorage() pure returns (FeeConcentrationIndexStorage storage s) {
    bytes32 slot = REACTIVE_FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}
