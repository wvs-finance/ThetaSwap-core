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

// Compute x_k from feeGrowthInside deltas (token0 only)
// rangeFeeGrowthNow0 = V4StateReader.getFeeGrowthInside(...) token0 at removal
// positionFeeLast0   = V4StateReader.getFeeGrowthInsideLast(...) token0 (V4 tracks per position)
// baseline0          = feeGrowthInsideBaseline stored at add time
function fromFeeGrowthDelta(
    uint256 rangeFeeGrowthNow0X128,
    uint256 positionFeeLast0X128,
    uint256 baseline0X128
) pure returns (FeeShareRatio) {
    uint256 posFeeDelta0;
    uint256 rangeFeeDelta0;
    unchecked {
        posFeeDelta0 = rangeFeeGrowthNow0X128 - positionFeeLast0X128;
        rangeFeeDelta0 = rangeFeeGrowthNow0X128 - baseline0X128;
    }
    return fromFeeGrowth(posFeeDelta0, rangeFeeDelta0);
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
