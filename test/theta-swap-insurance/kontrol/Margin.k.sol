// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {BalanceDelta, toBalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {
    Margin, ZERO_MARGIN,
    fromCreditDebit, fromBalanceDelta, credit, debit, shouldLiquidate, isZero, intoBalanceDelta
} from "../../../src/theta-swap-insurance/types/MarginMod.sol";

contract MarginProof is Test, KontrolCheats {
    // Round-trip: pack then unpack recovers both fields
    function prove_roundTrip(int128 c, int128 d) public pure {
        Margin m = fromCreditDebit(c, d);
        assert(m.credit() == c);
        assert(m.debit() == d);
    }

    // shouldLiquidate iff credit < debit
    function prove_shouldLiquidate(int128 c, int128 d) public pure {
        Margin m = fromCreditDebit(c, d);
        assert(m.shouldLiquidate() == (c < d));
    }

    // Zero margin is zero
    function prove_zeroIsZero() public pure {
        assert(ZERO_MARGIN.isZero());
    }

    // Equal credit and debit: no liquidation
    function prove_equalNoLiquidation(int128 v) public pure {
        Margin m = fromCreditDebit(v, v);
        assert(!m.shouldLiquidate());
    }

    // Margin ↔ BalanceDelta round-trip is identity
    function prove_balanceDeltaRoundTrip(int128 c, int128 d) public pure {
        Margin original = fromCreditDebit(c, d);
        Margin restored = fromBalanceDelta(original.intoBalanceDelta());
        assert(Margin.unwrap(restored) == Margin.unwrap(original));
    }

    // intoBalanceDelta preserves credit→amount0, debit→amount1
    function prove_intoBalanceDelta(int128 c, int128 d) public pure {
        Margin m = fromCreditDebit(c, d);
        BalanceDelta bd = m.intoBalanceDelta();
        assert(bd.amount0() == c);
        assert(bd.amount1() == d);
    }
}
