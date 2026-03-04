// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    LogPrice, ZERO_LOG_PRICE, LN_1_0001_Q128, Q128,
    LogPrice__ZeroDenominator,
    fromIndex, fromTick,
    unwrap, toTick, isZero, gt, lt
} from "../../../src/theta-swap-insurance/types/LogPriceMod.sol";
import {fromSqrt, toSqrt} from "../../../src/theta-swap-insurance/libraries/LogPriceMath.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";

contract LogPriceTest is Test {
    // ── fromIndex ────────────────────────────────────────────────────

    // A_T = 0 → p = 0 → ln(1) = 0
    function test_fromIndexZeroAT() public pure {
        LogPrice s = fromIndex(0, Q128 / 2);
        assertTrue(s.isZero());
    }

    // A_T = B_T → p = 1 → ln(2) ≈ 0.693...
    function test_fromIndexEqual() public pure {
        uint256 half = Q128 / 2;
        LogPrice s = fromIndex(half, half);
        // ln(2) in Q128 ≈ 0.6931... * 2^128 ≈ 2.358e38
        int256 ln2Q128 = 235865763225513294137944142764154484399;
        // Allow 0.01% relative error from WAD precision
        assertApproxEqRel(s.unwrap(), ln2Q128, 1e14);
    }

    // B_T = 0 → revert
    function test_fromIndexZeroDenominatorReverts() public {
        vm.expectRevert(LogPrice__ZeroDenominator.selector);
        this.externalFromIndex(Q128 / 2, 0);
    }

    // Monotonicity: larger A_T/B_T → larger LogPrice
    function testFuzz_fromIndexMonotone(uint64 aT1, uint64 aT2, uint64 bT) public pure {
        vm.assume(bT > 0);
        vm.assume(aT1 < aT2);
        LogPrice s1 = fromIndex(uint256(aT1), uint256(bT));
        LogPrice s2 = fromIndex(uint256(aT2), uint256(bT));
        assertTrue(s2.gt(s1) || (s2.unwrap() == s1.unwrap()));
    }

    // ── fromTick / toTick round-trip ─────────────────────────────────

    // Round-trip: fromTick(t).toTick() == t
    function testFuzz_tickRoundTrip(int24 tick) public pure {
        vm.assume(tick >= -887272 && tick <= 887272); // V3 tick bounds
        LogPrice s = fromTick(tick);
        assertEq(s.toTick(), tick);
    }

    // Tick 0 → LogPrice 0
    function test_tickZero() public pure {
        LogPrice s = fromTick(0);
        assertTrue(s.isZero());
    }

    // Positive tick → positive LogPrice
    function test_tickPositive() public pure {
        LogPrice s = fromTick(100);
        assertTrue(s.unwrap() > 0);
    }

    // Negative tick → negative LogPrice
    function test_tickNegative() public pure {
        LogPrice s = fromTick(-100);
        assertTrue(s.unwrap() < 0);
    }

    // ── Comparisons ──────────────────────────────────────────────────

    function testFuzz_gtLt(int24 a, int24 b) public pure {
        vm.assume(a >= -887272 && a <= 887272);
        vm.assume(b >= -887272 && b <= 887272);
        vm.assume(a != b);
        LogPrice sa = fromTick(a);
        LogPrice sb = fromTick(b);
        assertEq(sa.gt(sb), a > b);
        assertEq(sa.lt(sb), a < b);
    }

    // ── fromSqrt / toSqrt ────────────────────────────────────────────

    // Round-trip through sqrt: fromSqrt(sqrtPrice).toSqrt() recovers
    // the sqrtPrice at the same tick (tick-granularity precision).
    function testFuzz_sqrtRoundTrip(int24 tick) public pure {
        vm.assume(tick >= TickMath.MIN_TICK && tick <= TickMath.MAX_TICK);
        uint160 sqrtPrice = TickMath.getSqrtPriceAtTick(tick);
        LogPrice s = fromSqrt(sqrtPrice);
        uint160 recovered = toSqrt(s);
        assertEq(recovered, sqrtPrice);
    }

    // fromSqrt at tick 0 → LogPrice 0
    function test_fromSqrtTickZero() public pure {
        uint160 sqrtAtZero = TickMath.getSqrtPriceAtTick(0);
        LogPrice s = fromSqrt(sqrtAtZero);
        assertTrue(s.isZero());
    }

    // Monotonicity: higher sqrtPrice → higher LogPrice
    function testFuzz_fromSqrtMonotone(int24 a, int24 b) public pure {
        vm.assume(a >= TickMath.MIN_TICK && a < TickMath.MAX_TICK);
        vm.assume(b >= TickMath.MIN_TICK && b < TickMath.MAX_TICK);
        vm.assume(a < b);
        uint160 sqrtA = TickMath.getSqrtPriceAtTick(a);
        uint160 sqrtB = TickMath.getSqrtPriceAtTick(b);
        LogPrice sA = fromSqrt(sqrtA);
        LogPrice sB = fromSqrt(sqrtB);
        assertTrue(sB.gt(sA) || sB.unwrap() == sA.unwrap());
    }

    // Tick consistency: fromSqrt(sqrtPrice).toTick() == TickMath.getTickAtSqrtPrice(sqrtPrice)
    function testFuzz_fromSqrtTickConsistency(int24 tick) public pure {
        vm.assume(tick >= TickMath.MIN_TICK && tick <= TickMath.MAX_TICK);
        uint160 sqrtPrice = TickMath.getSqrtPriceAtTick(tick);
        LogPrice s = fromSqrt(sqrtPrice);
        assertEq(s.toTick(), tick);
    }

    // ── Zero constant ────────────────────────────────────────────────

    function test_zeroConstant() public pure {
        assertTrue(ZERO_LOG_PRICE.isZero());
    }

    // ── Helper for expectRevert on free functions ────────────────────

    function externalFromIndex(uint256 aT, uint256 bT) external pure returns (LogPrice) {
        return fromIndex(aT, bT);
    }
}
