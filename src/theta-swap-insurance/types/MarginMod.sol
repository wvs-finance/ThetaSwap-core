// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BalanceDelta, toBalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {FullMath} from "@uniswap/v4-core/src/libraries/FullMath.sol";
import {FixedPoint128} from "@uniswap/v4-core/src/libraries/FixedPoint128.sol";
import {FeeRevenue} from "../../types/FeeRevenueMod.sol";
import {PremiumFactor, applyTo} from "./PremiumFactorMod.sol";

/// @dev Two int128 values packed into a single int256.
///      Upper 128 bits = credit (accumulated fees earned by PLP).
///      Lower 128 bits = debit  (accumulated premiums owed by PLP).
///      Bit layout is identical to V4's BalanceDelta:
///        credit ↔ amount0,  debit ↔ amount1.
///      Liquidation condition: credit(m) < debit(m).
type Margin is int256;

Margin constant ZERO_MARGIN = Margin.wrap(0);

// ── Factory ──────────────────────────────────────────────────────────

function fromCreditDebit(int128 _credit, int128 _debit) pure returns (Margin m) {
    assembly ("memory-safe") {
        m := or(shl(128, _credit), and(sub(shl(128, 1), 1), _debit))
    }
}

function fromBalanceDelta(BalanceDelta delta) pure returns (Margin) {
    return Margin.wrap(BalanceDelta.unwrap(delta));
}

/// @dev Derive Margin from CLAMM fee growth state and PremiumFactor.
///      unchecked subtraction on feeGrowth is expected (V4 convention: overflow wraps).
function deriveMargin(
    uint256 feeGrowthInside0X128,
    uint256 feeGrowthInside0LastX128,
    uint128 liquidity,
    PremiumFactor factor
) pure returns (Margin) {
    uint256 feesEarned;
    unchecked {
        feesEarned = FullMath.mulDiv(
            feeGrowthInside0X128 - feeGrowthInside0LastX128,
            liquidity,
            FixedPoint128.Q128
        );
    }
    FeeRevenue revenue = FeeRevenue.wrap(feesEarned);
    uint256 premium = FeeRevenue.unwrap(factor.applyTo(revenue));
    return fromCreditDebit(int128(uint128(feesEarned)), int128(uint128(premium)));
}

// ── Accessors ────────────────────────────────────────────────────────

function credit(Margin m) pure returns (int128 _credit) {
    assembly ("memory-safe") {
        _credit := sar(128, m)
    }
}

function debit(Margin m) pure returns (int128 _debit) {
    assembly ("memory-safe") {
        _debit := signextend(15, m)
    }
}

// ── Predicates ───────────────────────────────────────────────────────

function shouldLiquidate(Margin m) pure returns (bool) {
    return m.credit() < m.debit();
}

function isZero(Margin m) pure returns (bool) {
    return Margin.unwrap(m) == 0;
}

// ── V4 Interop ───────────────────────────────────────────────────────

/// @dev Zero-cost cast. Same bit layout: credit→amount0, debit→amount1.
///      Enables CurrencySettler.take/settle on the margin delta.
function intoBalanceDelta(Margin m) pure returns (BalanceDelta) {
    return BalanceDelta.wrap(Margin.unwrap(m));
}

using {credit, debit, shouldLiquidate, isZero, intoBalanceDelta} for Margin global;
