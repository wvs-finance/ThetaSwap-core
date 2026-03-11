// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {
    deltaPlusToSqrtPriceX96,
    applyDecay,
    updateHWM,
    lookbackPayoffX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

contract SqrtPriceLookbackPayoffX96Test is Test {
    /// @dev INV-002: δ⁺=0 maps to SQRT_PRICE_1_1 (2⁹⁶)
    function test_deltaPlusZero_returns_Q96() public pure {
        uint160 result = deltaPlusToSqrtPriceX96(0);
        assertEq(result, uint160(SqrtPriceLibrary.Q96));
    }

    /// @dev INV-001: δ⁺ ∈ (0, Q128) → result ∈ [MIN_SQRT_PRICE, MAX_SQRT_PRICE]
    function test_deltaPlusInRange_returns_valid_sqrtPrice() public pure {
        uint128 deltaPlus = 1e18; // small non-zero value
        uint160 result = deltaPlusToSqrtPriceX96(deltaPlus);
        assertGe(result, TickMath.MIN_SQRT_PRICE);
        assertLe(result, TickMath.MAX_SQRT_PRICE);
    }

    /// @dev INV-005: applyDecay(hwm, 0) = hwm
    function test_applyDecay_zerodt_returns_hwm() public pure {
        uint160 hwm = uint160(SqrtPriceLibrary.Q96) * 2; // some HWM
        uint160 result = applyDecay(hwm, 0, 14 days);
        assertEq(result, hwm);
    }

    /// @dev INV-004: applyDecay never exceeds input
    function test_applyDecay_never_exceeds_input() public pure {
        uint160 hwm = uint160(SqrtPriceLibrary.Q96) * 3;
        uint160 result = applyDecay(hwm, 7 days, 14 days);
        assertLe(result, hwm);
        assertGt(result, 0);
    }

    /// @dev INV-006: updateHWM only increases
    function test_updateHWM_only_increases() public pure {
        uint160 hwm = uint160(SqrtPriceLibrary.Q96);
        uint160 higher = hwm + 1000;
        uint160 lower = hwm - 1000;

        assertEq(updateHWM(hwm, higher), higher);
        assertEq(updateHWM(hwm, lower), hwm);
    }

    /// @dev INV-008: lookbackPayoffX96 = 0 when hwm ≤ strike
    function test_lookbackPayoffX96_zero_when_hwm_le_strike() public pure {
        uint160 strike = uint160(SqrtPriceLibrary.Q96) * 2;
        uint160 hwmEqual = strike;
        uint160 hwmBelow = strike - 1;

        assertEq(lookbackPayoffX96(hwmEqual, strike), 0);
        assertEq(lookbackPayoffX96(hwmBelow, strike), 0);
    }

    /// @dev INV-007: lookbackPayoffX96 ≥ 0 (and positive when hwm > strike)
    function test_lookbackPayoffX96_positive_when_hwm_gt_strike() public pure {
        uint160 strike = uint160(SqrtPriceLibrary.Q96);
        uint160 hwm = strike * 2; // 2x price → large payoff

        uint256 payoff = lookbackPayoffX96(hwm, strike);
        assertGt(payoff, 0);
    }

    /// @dev INV-009: lookbackPayoffX96 capped at Q96
    function test_lookbackPayoffX96_capped_at_Q96() public pure {
        uint160 strike = uint160(SqrtPriceLibrary.Q96);
        uint160 hwm = strike * 10; // extreme ratio → should cap

        uint256 payoff = lookbackPayoffX96(hwm, strike);
        assertLe(payoff, SqrtPriceLibrary.Q96);
    }
}
