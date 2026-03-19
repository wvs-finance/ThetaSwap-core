// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

struct EpochSnapshot {
    uint256 epochId;
    uint256 epochLength;
    uint256 accumulatedSum;
    uint256 thetaSum;
    uint256 posCount;
    uint256 removedPosCount;
    uint128 indexA;
    uint128 deltaPlus;
}
