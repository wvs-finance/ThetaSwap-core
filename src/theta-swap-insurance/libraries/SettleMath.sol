// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {LogPrice, Q128} from "../types/LogPriceMod.sol";
import {getPayoffDelta, getNextLogPriceFromPayoff} from "./LogPriceMath.sol";

/// @dev Computes the result of a settlement step within a single tick range.
///      Analogous to V4's SwapMath but for insurance CFMM settlement.
///
///      In V4 SwapMath:
///        computeSwapStep(sqrtPriceCurrent, sqrtPriceTarget, liquidity, amountRemaining, feePips)
///        → (sqrtPriceNext, amountIn, amountOut, feeAmount)
///
///      In insurance SettleMath:
///        computeSettleStep(logPriceCurrent, logPriceTarget, liquidity, payoffRemaining)
///        → (logPriceNext, payoffDelta, premiumDelta)
///
///      Key difference: settlement is oracle-driven (not user-specified amount),
///      so there's no exactIn/exactOut distinction. The oracle sets the target price
///      and we walk toward it, computing payoff and premium at each step.
///
///      Free functions (SCOP): no `library` keyword.

// ── Target Price Selection ──────────────────────────────────────────────

/// @dev Select the settlement target for a single step.
///      Analogous to SwapMath.getSqrtPriceTarget.
///      When increasing: target = min(logPriceNext, logPriceLimit)
///      When decreasing: target = max(logPriceNext, logPriceLimit)
function getLogPriceTarget(
    bool increasing,
    LogPrice logPriceNext,
    LogPrice logPriceLimit
) pure returns (LogPrice target) {
    int256 next = LogPrice.unwrap(logPriceNext);
    int256 limit = LogPrice.unwrap(logPriceLimit);
    if (increasing) {
        target = LogPrice.wrap(next < limit ? next : limit);
    } else {
        target = LogPrice.wrap(next > limit ? next : limit);
    }
}

// ── Per-Tick Settlement Step ────────────────────────────────────────────

/// @dev Compute the result of settling within a single tick range.
///      Walks the trading function y(s) = s - 1 + e^{-s} from logPriceCurrent
///      toward logPriceTarget, bounded by available liquidity.
///
///      Returns:
///        logPriceNext — the resulting log-price after this step
///        payoffDelta  — protection payoff accrued in this step (to PLPs)
///        premiumDelta — premium accrued in this step (to underwriters)
///
///      The premium in each step is proportional to the payoff delta,
///      scaled by the active liquidity (underwriters earn pro-rata).
function computeSettleStep(
    LogPrice logPriceCurrent,
    LogPrice logPriceTarget,
    uint128 liquidity
) pure returns (LogPrice logPriceNext, uint256 payoffDelta, uint256 premiumDelta) {
    // TODO: implement
    // Scaffold only — no business logic until invariants and proofs exist.
    //
    // Pseudocode:
    //   bool increasing = logPriceTarget > logPriceCurrent
    //   (lower, upper) = increasing ? (current, target) : (target, current)
    //   payoffDelta = getPayoffDelta(lower, upper, liquidity, roundUp=!increasing)
    //   logPriceNext = logPriceTarget  (always reaches target in oracle-driven settlement)
    //   premiumDelta = payoffDelta  (premium = payoff in single-asset CFMM)
}
