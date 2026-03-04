// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {BalanceDelta, toBalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {
    Margin, ZERO_MARGIN,
    fromCreditDebit, fromBalanceDelta, deriveMargin,
    credit, debit, shouldLiquidate, isZero, intoBalanceDelta
} from "../../../src/theta-swap-insurance/types/MarginMod.sol";
import {PremiumFactor, fromRaw, Q128_ONE} from "../../../src/theta-swap-insurance/types/PremiumFactorMod.sol";
import {FixedPoint128} from "@uniswap/v4-core/src/libraries/FixedPoint128.sol";

contract MarginTest is Test {
    // Round-trip: pack then unpack recovers both fields
    function testFuzz_roundTrip(int128 c, int128 d) public pure {
        Margin m = fromCreditDebit(c, d);
        assertEq(m.credit(), c);
        assertEq(m.debit(), d);
    }

    // INS-002: shouldLiquidate iff credit < debit
    function testFuzz_shouldLiquidate(int128 c, int128 d) public pure {
        Margin m = fromCreditDebit(c, d);
        assertEq(m.shouldLiquidate(), c < d);
    }

    // Zero margin is zero
    function test_zeroMarginIsZero() public pure {
        assertTrue(ZERO_MARGIN.isZero());
    }

    // Non-zero margin is not zero
    function test_nonZeroNotZero() public pure {
        Margin m = fromCreditDebit(1, 0);
        assertFalse(m.isZero());
    }

    // Equal credit and debit: no liquidation
    function testFuzz_equalNoLiquidation(int128 v) public pure {
        Margin m = fromCreditDebit(v, v);
        assertFalse(m.shouldLiquidate());
    }

    // credit > debit: no liquidation
    function testFuzz_creditAboveDebit(int128 c, int128 d) public pure {
        vm.assume(c > d);
        Margin m = fromCreditDebit(c, d);
        assertFalse(m.shouldLiquidate());
    }

    // credit < debit: liquidation
    function testFuzz_creditBelowDebit(int128 c, int128 d) public pure {
        vm.assume(c < d);
        Margin m = fromCreditDebit(c, d);
        assertTrue(m.shouldLiquidate());
    }

    // Boundary: max positive values
    function test_maxValues() public pure {
        int128 maxInt = type(int128).max;
        Margin m = fromCreditDebit(maxInt, maxInt);
        assertEq(m.credit(), maxInt);
        assertEq(m.debit(), maxInt);
        assertFalse(m.shouldLiquidate());
    }

    // Boundary: min negative values
    function test_minValues() public pure {
        int128 minInt = type(int128).min;
        Margin m = fromCreditDebit(minInt, minInt);
        assertEq(m.credit(), minInt);
        assertEq(m.debit(), minInt);
        assertFalse(m.shouldLiquidate());
    }

    // ── V4 Interop ───────────────────────────────────────────────────

    // Margin → BalanceDelta preserves both fields as amount0/amount1
    function testFuzz_intoBalanceDelta(int128 c, int128 d) public pure {
        Margin m = fromCreditDebit(c, d);
        BalanceDelta bd = m.intoBalanceDelta();
        assertEq(bd.amount0(), c);
        assertEq(bd.amount1(), d);
    }

    // BalanceDelta → Margin preserves both fields as credit/debit
    function testFuzz_fromBalanceDelta(int128 a0, int128 a1) public pure {
        BalanceDelta bd = toBalanceDelta(a0, a1);
        Margin m = fromBalanceDelta(bd);
        assertEq(m.credit(), a0);
        assertEq(m.debit(), a1);
    }

    // Round-trip: Margin → BalanceDelta → Margin is identity
    function testFuzz_roundTripBalanceDelta(int128 c, int128 d) public pure {
        Margin original = fromCreditDebit(c, d);
        Margin restored = fromBalanceDelta(original.intoBalanceDelta());
        assertEq(Margin.unwrap(restored), Margin.unwrap(original));
    }

    // ── deriveMargin ─────────────────────────────────────────────────

    // Zero fee growth → zero margin
    function testFuzz_deriveZeroFees(uint128 factorRaw) public pure {
        vm.assume(factorRaw > 0);
        PremiumFactor f = fromRaw(factorRaw);
        Margin m = deriveMargin(100, 100, 1e18, f);
        assertTrue(m.isZero());
    }

    // Zero liquidity → zero margin
    function testFuzz_deriveZeroLiquidity(uint128 factorRaw, uint256 growth) public pure {
        vm.assume(factorRaw > 0);
        vm.assume(growth > 0);
        PremiumFactor f = fromRaw(factorRaw);
        Margin m = deriveMargin(growth, 0, 0, f);
        assertTrue(m.isZero());
    }

    // Budget constraint: debit ≤ credit (follows from PremiumFactor budget constraint)
    // Bounded so feesEarned fits int128 (mulDiv(delta, liq, Q128) < int128.max)
    function testFuzz_deriveBudgetConstraint(
        uint64 feeGrowthDelta,
        uint64 liquidity,
        uint128 factorRaw
    ) public pure {
        vm.assume(factorRaw > 0);
        vm.assume(liquidity > 0);
        PremiumFactor f = fromRaw(factorRaw);
        Margin m = deriveMargin(uint256(feeGrowthDelta), 0, liquidity, f);
        assertLe(m.debit(), m.credit());
    }

    // No liquidation when factor < Q128_ONE (debit < credit)
    // Bounded to uint64 so feesEarned fits int128 (same as deriveBudgetConstraint)
    function testFuzz_deriveNoLiquidation(
        uint64 feeGrowthDelta,
        uint64 liquidity,
        uint128 factorRaw
    ) public pure {
        vm.assume(factorRaw > 0);
        vm.assume(factorRaw < Q128_ONE); // factor < 1
        vm.assume(liquidity > 0);
        vm.assume(feeGrowthDelta > 0);
        PremiumFactor f = fromRaw(factorRaw);
        Margin m = deriveMargin(uint256(feeGrowthDelta), 0, liquidity, f);
        // When factor < 1, debit < credit, so no liquidation
        // (unless both are zero due to rounding)
        if (!m.isZero()) {
            assertFalse(m.shouldLiquidate());
        }
    }

    // Max factor (Q128_ONE) → credit == debit (all fees go to premium)
    function test_deriveMaxFactor() public pure {
        PremiumFactor f = fromRaw(Q128_ONE);
        uint256 growth = uint256(1e18) * FixedPoint128.Q128; // 1e18 fees worth of growth
        Margin m = deriveMargin(growth, 0, 1, f);
        assertEq(m.credit(), m.debit());
        assertFalse(m.shouldLiquidate());
    }

    // Half factor → debit ≈ credit / 2
    function test_deriveHalfFactor() public pure {
        uint128 half = Q128_ONE / 2;
        PremiumFactor f = fromRaw(half);
        uint256 growth = uint256(2e18) * FixedPoint128.Q128;
        Margin m = deriveMargin(growth, 0, 1, f);
        // credit = 2e18, debit ≈ 1e18 (allow 1 wei rounding)
        assertEq(m.credit(), int128(int256(2e18)));
        assertApproxEqAbs(uint128(int128(m.debit())), 1e18, 1);
    }
}
