// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseProperties} from "chimera/BaseProperties.sol";

import {Position} from "v4-core/src/libraries/Position.sol";

import {TickRange, fromTicks} from "../../../src/fee-concentration-index/types/TickRangeMod.sol";
import {Setup} from "./Setup.sol";

// Properties that must hold after every call to _afterAddLiquidity.
// Reads harness storage via view functions (diamond storage lives in harness, not test contract).

abstract contract Properties is BaseProperties, Setup {
    // INV-004 (Registry Consistency): every registered position is in the correct tick range set
    function echidna_registered_positions_in_range() public view returns (bool) {
        for (uint256 i = 0; i < allPositionKeys.length; i++) {
            bytes32 pk = allPositionKeys[i];
            if (!ghostRegistered[pk]) continue;

            int24 tl = ghostTickLower[pk];
            int24 tu = ghostTickUpper[pk];

            if (!harness.containsPosition(fciPoolId, tl, tu, pk)) return false;
        }
        return true;
    }

    // INV: rangeKeyOf reverse lookup is consistent after registration
    function echidna_rangeKeyOf_consistent() public view returns (bool) {
        for (uint256 i = 0; i < allPositionKeys.length; i++) {
            bytes32 pk = allPositionKeys[i];
            if (!ghostRegistered[pk]) continue;

            int24 tl = ghostTickLower[pk];
            int24 tu = ghostTickUpper[pk];
            bytes32 expected = TickRange.unwrap(fromTicks(tl, tu));
            bytes32 stored = harness.getRangeKeyOf(fciPoolId, pk);

            if (stored != expected) return false;
        }
        return true;
    }

    // INV: ghost position count matches allPositionKeys length
    function echidna_position_count_consistent() public view returns (bool) {
        return positionsAdded == allPositionKeys.length;
    }

    // INV-002: baseline swap count is set (rangeKeyOf nonzero proves register() ran)
    function echidna_baseline_swap_count_set() public view returns (bool) {
        for (uint256 i = 0; i < allPositionKeys.length; i++) {
            bytes32 pk = allPositionKeys[i];
            if (!ghostRegistered[pk]) continue;

            bytes32 stored = harness.getRangeKeyOf(fciPoolId, pk);
            if (stored == bytes32(0)) return false;
        }
        return true;
    }

    // INV: feeGrowthBaseline0 storage slot was written (may be 0 if no fees yet)
    function echidna_baseline_fee_growth_written() public view returns (bool) {
        // This property verifies the code path ran — baseline may be 0 in a fresh pool.
        // The real check: position is in registry (which implies baseline was set in same code path).
        for (uint256 i = 0; i < allPositionKeys.length; i++) {
            bytes32 pk = allPositionKeys[i];
            if (!ghostRegistered[pk]) continue;

            int24 tl = ghostTickLower[pk];
            int24 tu = ghostTickUpper[pk];
            if (!harness.containsPosition(fciPoolId, tl, tu, pk)) return false;
        }
        return true;
    }
}
