// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

// x_k = positionFeeDelta0 / rangeFeeDelta0 (token0 only)
// position's share of fees within its tick range, in [0, 1] as Q128
// token0 only: x_k0 == x_k1 in standard V4 (fees accrue proportional to liquidity share)
// uint128: max = 2^128 - 1, so 1.0 is capped at type(uint128).max (1 wei precision loss)
// compatible with V4StateReader.getFeeGrowthInside and getFeeGrowthInsideLast

type FeeShareRatio is uint128;

uint256 constant Q128 = 1 << 128;
uint128 constant FEE_SHARE_ONE = type(uint128).max;

function fromFeeGrowth(
    uint256 positionFeeGrowthInsideX128,
    uint256 rangeFeeGrowthInsideX128
) pure returns (FeeShareRatio) {
    if (rangeFeeGrowthInsideX128 == 0) return FeeShareRatio.wrap(0);
    uint256 ratio = FixedPointMathLib.mulDiv(positionFeeGrowthInsideX128, Q128, rangeFeeGrowthInsideX128);
    if (ratio > FEE_SHARE_ONE) ratio = FEE_SHARE_ONE;
    return FeeShareRatio.wrap(uint128(ratio));
}

// Compute x_k from feeGrowthInside deltas weighted by liquidity (token0 only)
// rangeFeeGrowthNow0 = V4StateReader.getFeeGrowthInside(...) token0 at removal
// positionFeeLast0   = V4StateReader.getFeeGrowthInsideLast(...) token0 (V4 tracks per position)
// baseline0          = feeGrowthInsideBaseline stored at add time
// posLiquidity       = position's liquidity amount
// totalRangeLiquidity = sum of all position liquidities in the range
//
// feeGrowthInside is per-unit-of-liquidity in V4. To get absolute fee share:
//   x_k = (posFeeDelta * posLiquidity) / (rangeFeeDelta * totalRangeLiquidity)
// When positions share the same baseline: x_k = posLiquidity / totalRangeLiquidity
function fromFeeGrowthDelta(
    uint256 rangeFeeGrowthNow0X128,
    uint256 positionFeeLast0X128,
    uint256 baseline0X128,
    uint128 posLiquidity,
    uint128 totalRangeLiquidity
) pure returns (FeeShareRatio) {
    if (totalRangeLiquidity == 0) return FeeShareRatio.wrap(0);
    uint256 posFeeDelta0;
    uint256 rangeFeeDelta0;
    unchecked {
        posFeeDelta0 = rangeFeeGrowthNow0X128 - positionFeeLast0X128;
        rangeFeeDelta0 = rangeFeeGrowthNow0X128 - baseline0X128;
    }
    // x_k = (posFeeDelta * posLiquidity) / (rangeFeeDelta * totalRangeLiquidity)
    // Split into two safe steps to avoid intermediate overflow:
    //   1. feeRatioQ128 = posFeeDelta / rangeFeeDelta (in Q128)
    //   2. x_k = feeRatioQ128 * posLiquidity / totalRangeLiquidity
    uint256 feeRatioQ128 = fromFeeGrowth(posFeeDelta0, rangeFeeDelta0).unwrap();
    // Combine fee ratio with liquidity share (safe: feeRatioQ128 <= 2^128-1, posLiquidity <= 2^128-1)
    uint256 ratio = FixedPointMathLib.mulDiv(feeRatioQ128, uint256(posLiquidity), uint256(totalRangeLiquidity));
    if (ratio > FEE_SHARE_ONE) ratio = FEE_SHARE_ONE;
    return FeeShareRatio.wrap(uint128(ratio));
}

function square(FeeShareRatio x) pure returns (uint256) {
    uint256 raw = FeeShareRatio.unwrap(x);
    return FixedPointMathLib.mulDiv(raw, raw, Q128);
}

function unwrap(FeeShareRatio x) pure returns (uint128) {
    return FeeShareRatio.unwrap(x);
}

function isZero(FeeShareRatio x) pure returns (bool) {
    return FeeShareRatio.unwrap(x) == 0;
}

using {square, unwrap, isZero} for FeeShareRatio global;
