// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";

contract SwapCountProof is Test, KontrolCheats {
    // INV-001: SwapCount only increases — increment produces a value strictly greater than input
    function prove_swapCount_increment_monotonic() public view {
        uint32 raw = freshUInt32();
        vm.assume(raw < type(uint32).max);

        SwapCount before = SwapCount.wrap(raw);
        SwapCount after_ = before.increment();

        assert(after_.unwrap() > before.unwrap());
    }

    // INV-002: SwapCount starts at zero
    function prove_swapCount_initial_zero() public pure {
        SwapCount initial = SwapCount.wrap(0);
        assert(initial.isZero());
        assert(initial.unwrap() == 0);
    }
}
