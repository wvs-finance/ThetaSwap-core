// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {Q128} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";

/// @dev Convert FCI delta-plus (Q128-scaled) to sqrtPriceX96.
/// Maps δ⁺ ∈ [0, Q128) → sqrtPriceX96 ∈ [MIN_SQRT_PRICE, MAX_SQRT_PRICE].
/// δ⁺ = 0 → fraction = 0/1 → sqrtPrice = 1.0 → SQRT_PRICE_1_1 (2⁹⁶).
/// Uses SqrtPriceLibrary.fractionToSqrtPriceX96(num, den) for precision.
function deltaPlusToSqrtPriceX96(uint128 deltaPlus) pure returns (uint160) {
    if (deltaPlus == 0) return uint160(SqrtPriceLibrary.Q96); // 1.0
    return SqrtPriceLibrary.fractionToSqrtPriceX96(
        uint256(deltaPlus),
        Q128 - uint256(deltaPlus)
    );
}

/// @dev Exponential HWM decay on sqrtPrice domain.
/// halfLifeSeconds is the price half-life; sqrtPrice half-life is 2x.
/// decay = hwm * exp(-ln(2) * dt / (2 * halfLifeSeconds))
/// Uses Solady expWad (18-decimal WAD domain) for the exponential.
function applyDecay(uint160 hwm, uint256 dt, uint256 halfLifeSeconds) pure returns (uint160) {
    if (dt == 0) return hwm;
    // exponent = -ln(2) * dt / (2 * halfLifeSeconds), scaled to WAD (1e18)
    // LN2_WAD = 693147180559945309 (ln(2) * 1e18)
    int256 exponent = -int256(
        FixedPointMathLib.mulDiv(693147180559945309, dt, 2 * halfLifeSeconds)
    );
    // exp(exponent) in WAD
    int256 decayFactor = FixedPointMathLib.expWad(exponent);
    // Apply: hwm * decayFactor / 1e18
    // Note: Solady sqrt() is integer sqrt, truncating ~1e-9 relative error
    return uint160(
        FixedPointMathLib.mulDiv(uint256(hwm), uint256(decayFactor), 1e18)
    );
}

/// @dev Update high-water mark: take the max of current HWM and new price.
function updateHWM(uint160 hwm, uint160 currentPrice) pure returns (uint160) {
    if (currentPrice > hwm) return currentPrice;
    return hwm;
}

/// @dev Power-squared payoff: ((sqrtPriceHWM / sqrtPriceStrike)⁴ − 1)⁺ capped at Q96.
/// The ⁴ exponent comes from squaring the sqrtPrice ratio twice:
///   (HWM/strike)² in price space = (sqrtHWM/sqrtStrike)⁴ in sqrtPrice space.
/// Returns a Q96-scaled uint256.
function lookbackPayoffX96(uint160 sqrtPriceHWM, uint160 sqrtPriceStrike) pure returns (uint256) {
    if (sqrtPriceHWM <= sqrtPriceStrike) return 0;

    // Guard: if hwm/strike ratio is extreme, divX96 will overflow.
    // When hwm > strike * 2^64, ratio⁴ certainly exceeds cap.
    if (uint256(sqrtPriceHWM) > uint256(sqrtPriceStrike) << 64) return SqrtPriceLibrary.Q96;

    // ratio = sqrtPriceHWM / sqrtPriceStrike, Q96-scaled
    uint256 ratioX96 = SqrtPriceLibrary.divX96(sqrtPriceHWM, sqrtPriceStrike);

    // Guard: if ratio² would overflow mulDiv (no 512-bit intermediate in Solady),
    // ratioX96 must fit uint128 so ratioX96² fits uint256.
    if (ratioX96 > type(uint128).max) return SqrtPriceLibrary.Q96;

    // ratio² (Q96-scaled): ratioX96 * ratioX96 / Q96
    uint256 ratioSqX96 = FixedPointMathLib.mulDiv(ratioX96, ratioX96, SqrtPriceLibrary.Q96);

    // Guard: ratioSqX96² must fit uint256 for the next mulDiv.
    if (ratioSqX96 > type(uint128).max) return SqrtPriceLibrary.Q96;

    // ratio⁴ (Q96-scaled): ratioSqX96 * ratioSqX96 / Q96
    uint256 ratioQuadX96 = FixedPointMathLib.mulDiv(ratioSqX96, ratioSqX96, SqrtPriceLibrary.Q96);

    // payoff = (ratio⁴ − 1)⁺, capped at Q96
    if (ratioQuadX96 <= SqrtPriceLibrary.Q96) return 0;
    uint256 payoff = ratioQuadX96 - SqrtPriceLibrary.Q96;

    if (payoff > SqrtPriceLibrary.Q96) return SqrtPriceLibrary.Q96;
    return payoff;
}
