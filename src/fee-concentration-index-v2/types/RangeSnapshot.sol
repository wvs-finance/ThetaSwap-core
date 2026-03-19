// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

struct RangeSnapshot {
    int24 tickLower;
    int24 tickUpper;
    uint128 totalLiquidity;
    uint256 swapCount;
    uint256 positionCount;
    bytes32[] positionKeys;
}
