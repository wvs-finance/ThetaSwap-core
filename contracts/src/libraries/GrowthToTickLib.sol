// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {FullMath} from "v4-core/src/libraries/FullMath.sol";
import {FixedPointMathLib} from "solady/src/utils/FixedPointMathLib.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {FixedPoint128} from "v4-core/src/libraries/FixedPoint128.sol";

/// @notice Converts a cumulative growth ratio into a Uniswap V4 tick.
/// @dev Four-stage pure pipeline:
///      1. Q128.128 ratio via FullMath.mulDiv (512-bit intermediate)
///      2. Integer square root via Solady (Q128.128 → Q64.64)
///      3. Left-shift by 32 to scale Q64.64 → Q64.96 (sqrtPriceX96)
///      4. TickMath.getTickAtSqrtPrice → int24 tick
///
///      Reverts propagate from dependencies:
///      - anchorGrowth == 0 → FullMath div-by-zero panic
///      - ratio overflows uint256 → FullMath revert
///      - sqrtPriceX96 out of TickMath range → InvalidSqrtPrice()
///
/// @param currentGrowth The later (larger) cumulative growth value
/// @param anchorGrowth The earlier (smaller) cumulative growth value
/// @return tick The Uniswap V4 tick corresponding to the growth ratio
function growthToTick(uint208 currentGrowth, uint208 anchorGrowth) pure returns (int24 tick) {
    // Stage 1: Q128.128 ratio
    uint256 ratioQ128 =
        FullMath.mulDiv(uint256(currentGrowth), FixedPoint128.Q128, uint256(anchorGrowth));

    // Stage 2: sqrt(ratio * 2^128) = sqrt(ratio) * 2^64
    uint256 sqrtRatioX64 = FixedPointMathLib.sqrt(ratioQ128);

    // Stage 3: Q64.64 → Q64.96
    uint256 sqrtPriceX96 = sqrtRatioX64 << 32;

    // Stage 4: sqrtPriceX96 → tick
    tick = TickMath.getTickAtSqrtPrice(uint160(sqrtPriceX96));
}
