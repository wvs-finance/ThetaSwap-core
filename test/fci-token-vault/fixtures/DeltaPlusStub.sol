// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @dev Minimal stub implementing IFeeConcentrationIndex.getDeltaPlusEpoch
/// for Layer 1 vault tests. Returns a configurable uint128.
contract DeltaPlusStub {
    uint128 public deltaPlusValue;

    function setDeltaPlus(uint128 v) external {
        deltaPlusValue = v;
    }

    function getDeltaPlusEpoch(PoolKey calldata, bool) external view returns (uint128) {
        return deltaPlusValue;
    }

    function getDeltaPlus(PoolKey calldata, bool) external view returns (uint128) {
        return deltaPlusValue;
    }
}
