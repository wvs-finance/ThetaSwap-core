// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PositionConfig} from "@uniswap/v4-periphery/src/libraries/PositionConfig.sol";

/// @title LiquidityPositionSnapshot
/// @dev Captures the state of a position at a point in time.
/// Combines PositionConfig (poolKey + tick range) with Position.State data
/// (liquidity + fee growth accumulators).
struct LiquidityPositionSnapshot {
    PositionConfig config;
    uint128 liquidity;
    uint256 feeGrowthInside0LastX128;
    uint256 feeGrowthInside1LastX128;
}
