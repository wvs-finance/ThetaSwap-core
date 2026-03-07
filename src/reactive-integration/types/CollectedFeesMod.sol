// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Accumulated V3 Collect event fees per position.
// Stored in ReactVM state. Consumed on Burn callback.

struct CollectedFees {
    uint256 fee0;
    uint256 fee1;
}

function accumulate(CollectedFees storage self, uint128 amount0, uint128 amount1) {
    self.fee0 += uint256(amount0);
    self.fee1 += uint256(amount1);
}

function clear(CollectedFees storage self) {
    self.fee0 = 0;
    self.fee1 = 0;
}

function isEmpty(CollectedFees memory self) pure returns (bool) {
    return self.fee0 == 0 && self.fee1 == 0;
}

// Derive position key from V3 event fields.
// Matches V3's internal position key: keccak256(owner, tickLower, tickUpper).
function v3PositionKey(address owner, int24 tickLower, int24 tickUpper) pure returns (bytes32) {
    return keccak256(abi.encodePacked(owner, tickLower, tickUpper));
}

using {accumulate, clear} for CollectedFees global;
