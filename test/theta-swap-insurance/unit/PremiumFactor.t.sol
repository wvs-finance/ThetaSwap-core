// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {FeeRevenue} from "../../../src/types/FeeRevenueMod.sol";
import {
    PremiumFactor, Q128_ONE, PremiumFactor__Zero,
    fromRaw, applyTo, unwrap, isMax
} from "../../../src/theta-swap-insurance/types/PremiumFactorMod.sol";

contract PremiumFactorTest is Test {
    // Round-trip: fromRaw(x).unwrap() == x for all x > 0
    function testFuzz_roundTrip(uint128 raw) public pure {
        vm.assume(raw > 0);
        PremiumFactor f = fromRaw(raw);
        assertEq(f.unwrap(), raw);
    }

    // Budget constraint: applyTo(f, r) <= r for all valid f, r
    // FeeRevenue is bounded by uint128 in practice (V4 uses uint128 for amounts).
    function testFuzz_budgetConstraint(uint128 raw, uint128 revRaw) public pure {
        vm.assume(raw > 0);
        uint256 rev = uint256(revRaw);
        PremiumFactor f = fromRaw(raw);
        FeeRevenue r = FeeRevenue.wrap(rev);
        FeeRevenue premium = f.applyTo(r);
        assertLe(FeeRevenue.unwrap(premium), rev);
    }

    // Zero revenue yields zero premium
    function testFuzz_zeroRevenue(uint128 raw) public pure {
        vm.assume(raw > 0);
        PremiumFactor f = fromRaw(raw);
        FeeRevenue premium = f.applyTo(FeeRevenue.wrap(0));
        assertEq(FeeRevenue.unwrap(premium), 0);
    }

    // isMax iff raw == Q128_ONE
    function testFuzz_isMax(uint128 raw) public pure {
        vm.assume(raw > 0);
        PremiumFactor f = fromRaw(raw);
        assertEq(f.isMax(), raw == Q128_ONE);
    }

    // Zero raw reverts — external call needed for expectRevert on free functions
    function test_zeroReverts() public {
        vm.expectRevert(PremiumFactor__Zero.selector);
        this.externalFromRaw(0);
    }

    // Helper: wraps free function as external call for expectRevert
    function externalFromRaw(uint128 raw) external pure returns (PremiumFactor) {
        return fromRaw(raw);
    }

    // Max factor takes almost all revenue
    function test_maxFactor() public pure {
        PremiumFactor f = fromRaw(Q128_ONE);
        FeeRevenue r = FeeRevenue.wrap(1 ether);
        FeeRevenue premium = f.applyTo(r);
        // Q128_ONE / Q128_ONE = 1 (with rounding)
        assertEq(FeeRevenue.unwrap(premium), 1 ether);
    }

    // Half factor takes half revenue
    function test_halfFactor() public pure {
        uint128 half = Q128_ONE / 2;
        PremiumFactor f = fromRaw(half);
        FeeRevenue r = FeeRevenue.wrap(2 ether);
        FeeRevenue premium = f.applyTo(r);
        // half / Q128_ONE ≈ 0.5, so premium ≈ 1 ether
        // Allow 1 wei rounding
        assertApproxEqAbs(FeeRevenue.unwrap(premium), 1 ether, 1);
    }
}
