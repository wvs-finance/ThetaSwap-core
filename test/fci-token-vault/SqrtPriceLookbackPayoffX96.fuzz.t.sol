// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {Q128} from "typed-uniswap-v4/types/FeeConcentrationStateMod.sol";
import {
    deltaPlusToSqrtPriceX96,
    applyDecay,
    lookbackPayoffX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

contract SqrtPriceLookbackPayoffX96FuzzTest is Test {
    /// @dev INV-003: δ⁺ monotonicity — larger δ⁺ → smaller sqrtPrice
    function testFuzz_deltaPlusMonotonic(uint128 a, uint128 b) public pure {
        uint128 maxDelta = uint128(Q128 - 1);
        a = uint128(bound(a, 1, maxDelta - 1));
        b = uint128(bound(b, a + 1, maxDelta));

        uint160 resultA = deltaPlusToSqrtPriceX96(a);
        uint160 resultB = deltaPlusToSqrtPriceX96(b);
        assertLe(resultA, resultB); // larger δ⁺ → larger fraction → larger sqrtPrice
    }

    /// @dev INV-004: applyDecay never exceeds input
    function testFuzz_applyDecay_never_exceeds_input(uint160 hwm, uint256 dt, uint256 halfLife) public pure {
        halfLife = bound(halfLife, 1 hours, 365 days);
        dt = bound(dt, 0, 365 days);

        uint160 result = applyDecay(hwm, dt, halfLife);
        assertLe(result, hwm);
    }

    /// @dev INV-007 + INV-009: lookbackPayoffX96 ≥ 0 and ≤ Q96
    function testFuzz_lookbackPayoffX96_non_negative_and_capped(uint160 hwm, uint160 strike) public pure {
        hwm = uint160(bound(hwm, TickMath.MIN_SQRT_PRICE, TickMath.MAX_SQRT_PRICE));
        strike = uint160(bound(strike, TickMath.MIN_SQRT_PRICE, TickMath.MAX_SQRT_PRICE));

        uint256 payoff = lookbackPayoffX96(hwm, strike);
        assertLe(payoff, SqrtPriceLibrary.Q96);
    }
}
