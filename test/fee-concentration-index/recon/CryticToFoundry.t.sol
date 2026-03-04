// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {TargetFunctions} from "./TargetFunctions.sol";

// Bridge: runs Chimera property tests via Foundry's fuzzer.
// Implements Asserts overrides using Test (already inherited via PosmTestSetup).
// `forge test --match-contract CryticToFoundry`

contract CryticToFoundry is TargetFunctions {
    function setUp() public {
        setup();
    }

    // Asserts overrides — Test is inherited via PosmTestSetup
    function gt(uint256 a, uint256 b, string memory reason) internal override {
        assertGt(a, b, reason);
    }

    function gte(uint256 a, uint256 b, string memory reason) internal override {
        assertGe(a, b, reason);
    }

    function lt(uint256 a, uint256 b, string memory reason) internal override {
        assertLt(a, b, reason);
    }

    function lte(uint256 a, uint256 b, string memory reason) internal override {
        assertLe(a, b, reason);
    }

    function eq(uint256 a, uint256 b, string memory reason) internal override {
        assertEq(a, b, reason);
    }

    function t(bool b, string memory reason) internal override {
        assertTrue(b, reason);
    }

    function between(uint256 value, uint256 low, uint256 high) internal pure override returns (uint256) {
        if (value < low || value > high) {
            return low + (value % (high - low + 1));
        }
        return value;
    }

    function between(int256 value, int256 low, int256 high) internal pure override returns (int256) {
        if (value < low || value > high) {
            int256 range = high - low + 1;
            int256 clamped;
            unchecked {
                clamped = (value - low) % range;
            }
            if (clamped < 0) clamped += range;
            return low + clamped;
        }
        return value;
    }

    function precondition(bool p) internal override {
        vm.assume(p);
    }

    // Fuzz test: single position registration
    function testFuzz_afterAddLiquidity_registersPosition(
        address sender,
        int24 tickLower,
        int24 tickUpper,
        int256 liquidityDelta,
        bytes32 salt
    ) public {
        fuzz_afterAddLiquidity(sender, tickLower, tickUpper, liquidityDelta, salt);
        assertTrue(echidna_registered_positions_in_range());
        assertTrue(echidna_rangeKeyOf_consistent());
        assertTrue(echidna_position_count_consistent());
        assertTrue(echidna_baseline_swap_count_set());
    }

    // Fuzz test: two positions in same range
    function testFuzz_afterAddLiquidity_multiplePositions(
        address sender1,
        address sender2,
        int24 tickLower,
        int24 tickUpper,
        bytes32 salt1,
        bytes32 salt2
    ) public {
        fuzz_afterAddLiquidity(sender1, tickLower, tickUpper, 1e18, salt1);
        fuzz_afterAddLiquidity(sender2, tickLower, tickUpper, 1e18, salt2);
        assertTrue(echidna_registered_positions_in_range());
        assertTrue(echidna_rangeKeyOf_consistent());
        assertTrue(echidna_position_count_consistent());
    }
}
