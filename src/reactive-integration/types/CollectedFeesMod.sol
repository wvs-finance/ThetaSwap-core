// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Accumulated V3 Collect event fees per position.
// Summed over position lifetime, consumed on Burn.
struct CollectedFees {
    uint256 amount0;
    uint256 amount1;
}
