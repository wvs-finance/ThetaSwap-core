// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {AccumulatedHHI} from "./AccumulatedHHIMod.sol";
import {TickRangeRegistry} from "./TickRangeRegistryMod.sol";

// Diamond storage for Fee Concentration Index.
// All hook state lives here — the contract itself holds only logic.

struct FeeConcentrationIndexStorage {
    // Running HHI accumulator per pool: sum of (x_k^2 / lifetime)
    mapping(PoolId => AccumulatedHHI) accumulatedHHI;
    // Per-pool tick range registry (positions grouped by range, per-range swap counters)
    mapping(PoolId => TickRangeRegistry) registries;
    // Per-position snapshot of feeGrowthInside0X128 at add time.
    // Delta = (current feeGrowthInside0 - baseline) gives fees earned during position lifetime.
    // Used to compute x_k (fee share ratio) when the position is removed.
    mapping(PoolId => mapping(bytes32 => uint256)) feeGrowthBaseline0;
}

bytes32 constant FCI_STORAGE_SLOT = keccak256("FeeConcentrationIndex.storage");

function fciStorage() pure returns (FeeConcentrationIndexStorage storage s) {
    bytes32 slot = FCI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}
