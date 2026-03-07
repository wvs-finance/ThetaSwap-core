// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {FeeShareRatio, Q128, FEE_SHARE_ONE} from "../../fee-concentration-index/types/FeeShareRatioMod.sol";

// Synthetic feeGrowthDelta for V3 positions.
// V3 Burn event emits raw fee amounts (amount0, amount1).
// Dividing by position liquidity reverses V3's internal accumulation,
// producing a per-unit-of-liquidity delta compatible with V4's feeGrowthInsideX128.
// Stored as Q128 fixed-point (uint256).
// Zero when liquidity is zero (division avoided).

type SyntheticFeeGrowth is uint256;

// Compute synthetic feeGrowthDelta from V3 Burn event data (token0 only).
// amount0: fee amount from Burn event
// liquidity: position's liquidity at time of burn
// Returns Q128 fixed-point: amount0 * 2^128 / liquidity
function fromBurnAmount(
    uint256 amount0,
    uint128 liquidity
) pure returns (SyntheticFeeGrowth) {
    if (liquidity == 0) return SyntheticFeeGrowth.wrap(0);
    uint256 delta = FixedPointMathLib.mulDiv(amount0, Q128, uint256(liquidity));
    return SyntheticFeeGrowth.wrap(delta);
}

// Convert synthetic feeGrowthDelta to FeeShareRatio.
// positionDelta: this position's synthetic feeGrowth
// rangeDelta: total synthetic feeGrowth across all positions in the range
// Result in [0, Q128] — capped at FEE_SHARE_ONE.
function toFeeShareRatio(
    SyntheticFeeGrowth positionDelta,
    SyntheticFeeGrowth rangeDelta
) pure returns (FeeShareRatio) {
    uint256 rangeRaw = SyntheticFeeGrowth.unwrap(rangeDelta);
    if (rangeRaw == 0) return FeeShareRatio.wrap(0);
    uint256 posRaw = SyntheticFeeGrowth.unwrap(positionDelta);
    uint256 ratio = FixedPointMathLib.mulDiv(posRaw, Q128, rangeRaw);
    if (ratio > FEE_SHARE_ONE) ratio = FEE_SHARE_ONE;
    return FeeShareRatio.wrap(uint128(ratio));
}

function unwrap(SyntheticFeeGrowth x) pure returns (uint256) {
    return SyntheticFeeGrowth.unwrap(x);
}

function isZero(SyntheticFeeGrowth x) pure returns (bool) {
    return SyntheticFeeGrowth.unwrap(x) == 0;
}

using {unwrap, isZero} for SyntheticFeeGrowth global;
