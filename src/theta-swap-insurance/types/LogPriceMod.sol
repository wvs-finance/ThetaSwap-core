// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

/// @dev ln(1 + p) in Q128 signed fixed-point, where p = A_T / B_T.
///      The natural price representation for a log-shaped trading function.
///      Tick-linear: tick = floor(s / LN_1_0001_Q128).
///      Trading-function-linear: y(s) = s - 1 + e^{-s} is the per-tick target.
///      Oracle-direct: s = ln((A_T + B_T) / B_T) from FCI state.
type LogPrice is int256;

LogPrice constant ZERO_LOG_PRICE = LogPrice.wrap(0);

uint256 constant Q128 = 1 << 128;
uint256 constant WAD = 1e18;

/// @dev ln(1.0001) in Q128 ≈ 0.000099995000333 * 2^128
///      Precomputed: lnWad(1000100000000000000) * 2^128 / 1e18
int256 constant LN_1_0001_Q128 = 34025203799886974196299315890735;

error LogPrice__ZeroDenominator();

// ── Factory ──────────────────────────────────────────────────────────

/// @dev From FCI oracle values. A_T, B_T are Q128 fractions in (0, 1).
///      s = ln((A_T + B_T) / B_T) = ln(1 + A_T/B_T)
function fromIndex(uint256 aT, uint256 bT) pure returns (LogPrice) {
    if (bT == 0) revert LogPrice__ZeroDenominator();
    // ratio = (aT + bT) / bT in WAD for lnWad input
    uint256 ratioWad = FixedPointMathLib.mulDiv(aT + bT, WAD, bT);
    // lnWad returns ln(ratio) in WAD. ratio ≥ 1 so result ≥ 0.
    int256 lnResult = FixedPointMathLib.lnWad(int256(ratioWad));
    // WAD → Q128
    int256 lnQ128 = int256(FixedPointMathLib.mulDiv(uint256(lnResult), Q128, WAD));
    return LogPrice.wrap(lnQ128);
}

/// @dev From a tick index. s = tick * ln(1.0001) in Q128.
function fromTick(int24 tick) pure returns (LogPrice) {
    return LogPrice.wrap(int256(tick) * LN_1_0001_Q128);
}

// ── Accessors ────────────────────────────────────────────────────────

function unwrap(LogPrice s) pure returns (int256) {
    return LogPrice.unwrap(s);
}

/// @dev Convert LogPrice to tick: tick = floor(s / ln(1.0001))
function toTick(LogPrice s) pure returns (int24) {
    return int24(LogPrice.unwrap(s) / LN_1_0001_Q128);
}

// ── Predicates ───────────────────────────────────────────────────────

function isZero(LogPrice s) pure returns (bool) {
    return LogPrice.unwrap(s) == 0;
}

function gt(LogPrice a, LogPrice b) pure returns (bool) {
    return LogPrice.unwrap(a) > LogPrice.unwrap(b);
}

function lt(LogPrice a, LogPrice b) pure returns (bool) {
    return LogPrice.unwrap(a) < LogPrice.unwrap(b);
}

using {unwrap, toTick, isZero, gt, lt} for LogPrice global;
