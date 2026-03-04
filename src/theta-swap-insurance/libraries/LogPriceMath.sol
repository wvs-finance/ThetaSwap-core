// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {LogPrice, LN_1_0001_Q128, Q128, WAD, fromTick} from "../types/LogPriceMod.sol";

/// @dev Functions based on LogPrice (Q128 log-price) and liquidity.
///      Analogous to V4's SqrtPriceMath but for the log-shaped trading function
///      y(s) = s - 1 + e^{-s}, where s = ln(1 + p).
///
///      Free functions (SCOP): no `library` keyword.

// ── Errors ──────────────────────────────────────────────────────────────

error LogPriceMath__InvalidPrice();
error LogPriceMath__NotEnoughLiquidity();

// ── V4 Bridge ───────────────────────────────────────────────────────────

/// @dev Convert V4 sqrtPriceX96 to LogPrice via tick as shared coordinate.
///      sqrtPriceX96 → tick (TickMath) → LogPrice (tick * ln(1.0001))
function fromSqrt(uint160 sqrtPriceX96) pure returns (LogPrice) {
    int24 tick = TickMath.getTickAtSqrtPrice(sqrtPriceX96);
    return fromTick(tick);
}

/// @dev Convert LogPrice to V4 sqrtPriceX96 via tick as shared coordinate.
///      LogPrice → tick (floor(s / ln(1.0001))) → sqrtPriceX96 (TickMath)
function toSqrt(LogPrice s) pure returns (uint160) {
    int24 tick = int24(LogPrice.unwrap(s) / LN_1_0001_Q128);
    return TickMath.getSqrtPriceAtTick(tick);
}

// ── Trading Function ────────────────────────────────────────────────────

/// @dev Trading function value at log-price s.
///      y(s) = s - 1 + e^{-s}
///      Returns Q128 signed. For s >= 0: y(s) >= 0 and y(0) = 0.
function tradingFunction(LogPrice s) pure returns (int256 yQ128) {
    int256 sRaw = LogPrice.unwrap(s);
    int256 sWad;
    if (sRaw >= 0) {
        sWad = int256(FixedPointMathLib.mulDiv(uint256(sRaw), WAD, Q128));
    } else {
        sWad = -int256(FixedPointMathLib.mulDiv(uint256(-sRaw), WAD, Q128));
    }
    // y = s - 1 + e^{-s} in WAD
    int256 expNegS = FixedPointMathLib.expWad(-sWad);
    int256 yWad = sWad - int256(WAD) + expNegS;
    // WAD → Q128
    if (yWad >= 0) {
        yQ128 = int256(FixedPointMathLib.mulDiv(uint256(yWad), Q128, WAD));
    } else {
        yQ128 = -int256(FixedPointMathLib.mulDiv(uint256(-yWad), Q128, WAD));
    }
}

/// @dev Marginal rate at log-price s.
///      dy/ds = 1 - e^{-s}
///      Returns Q128 signed. For s > 0: rate in (0, 1).
function marginalRate(LogPrice s) pure returns (int256 rateQ128) {
    int256 sRaw = LogPrice.unwrap(s);
    int256 sWad;
    if (sRaw >= 0) {
        sWad = int256(FixedPointMathLib.mulDiv(uint256(sRaw), WAD, Q128));
    } else {
        sWad = -int256(FixedPointMathLib.mulDiv(uint256(-sRaw), WAD, Q128));
    }
    // dy/ds = 1 - e^{-s} in WAD
    int256 expNegS = FixedPointMathLib.expWad(-sWad);
    int256 rateWad = int256(WAD) - expNegS;
    // WAD → Q128
    if (rateWad >= 0) {
        rateQ128 = int256(FixedPointMathLib.mulDiv(uint256(rateWad), Q128, WAD));
    } else {
        rateQ128 = -int256(FixedPointMathLib.mulDiv(uint256(-rateWad), Q128, WAD));
    }
}

// ── Payoff Deltas (analogous to SqrtPriceMath.getAmount0Delta / getAmount1Delta) ──

/// @dev Payoff delta between two log-prices for given liquidity.
///      delta = L * [y(s_b) - y(s_a)]
///      where y(s) = s - 1 + e^{-s} is the trading function.
///      Always: logPriceA < logPriceB (caller ensures ordering).
function getPayoffDelta(
    LogPrice logPriceA,
    LogPrice logPriceB,
    uint128 liquidity,
    bool roundUp
) pure returns (uint256 payoff) {
    int256 yA = tradingFunction(logPriceA);
    int256 yB = tradingFunction(logPriceB);
    // y(s_b) - y(s_a) in Q128 (non-negative when s_b > s_a and both >= 0)
    int256 deltaY = yB - yA;
    if (deltaY <= 0) return 0;
    // payoff = L * deltaY / Q128
    if (roundUp) {
        payoff = FixedPointMathLib.mulDivUp(uint256(deltaY), uint256(liquidity), Q128);
    } else {
        payoff = FixedPointMathLib.mulDiv(uint256(deltaY), uint256(liquidity), Q128);
    }
}

/// @dev Collateral delta between two log-prices for given liquidity.
///      In the insurance CFMM, collateral is the single-asset reserve backing protection.
///      For add/remove liquidity: amount = L * [y(s_upper) - y(s_lower)] at current price.
///      Equivalent to getPayoffDelta but with explicit sign for liquidity changes.
function getCollateralDelta(
    LogPrice logPriceA,
    LogPrice logPriceB,
    int128 liquidity
) pure returns (int256) {
    uint256 absDelta;
    if (liquidity >= 0) {
        absDelta = getPayoffDelta(logPriceA, logPriceB, uint128(liquidity), true);
        return -int256(absDelta);
    } else {
        absDelta = getPayoffDelta(logPriceA, logPriceB, uint128(-liquidity), false);
        return int256(absDelta);
    }
}

// ── Next Price (analogous to SqrtPriceMath.getNextSqrtPriceFromInput/Output) ──

/// @dev Compute the next log-price after consuming a given payoff amount.
///      This is the inverse of getPayoffDelta: given (s_current, L, payoffAmount),
///      find s_next such that L * [y(s_next) - y(s_current)] = payoffAmount.
///      Scaffold — exact inverse requires Newton's method on y(s).
function getNextLogPriceFromPayoff(
    LogPrice logPriceCurrent,
    uint128 liquidity,
    uint256 payoffAmount,
    bool increasing
) pure returns (LogPrice) {
    // TODO: implement via Newton iteration on y(s) = s - 1 + e^{-s}
    // Scaffold only — no business logic until invariants and proofs exist.
    return logPriceCurrent;
}
