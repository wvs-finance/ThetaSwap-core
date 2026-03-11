// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {Q128} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {deltaPlusToSqrtPriceX96} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

contract SqrtPriceLookbackPayoffX96Proof is Test {
    /// @dev INV-002 (formal): δ⁺=0 ⟹ result = Q96
    function prove_deltaPlusZero_returns_Q96() public pure {
        uint160 result = deltaPlusToSqrtPriceX96(0);
        assert(result == uint160(SqrtPriceLibrary.Q96));
    }
}
