// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {FeeRevenue} from "@types/FeeRevenueMod.sol";
import {
    PremiumFactor, Q128_ONE,
    fromRaw, applyTo, unwrap, isMax
} from "@theta-swap-insurance/types/PremiumFactorMod.sol";

contract PremiumFactorProof is Test, KontrolCheats {
    // Round-trip: fromRaw(x).unwrap() == x for all x > 0
    function prove_roundTrip(uint128 raw) public pure {
        vm.assume(raw > 0);
        PremiumFactor f = fromRaw(raw);
        assert(f.unwrap() == raw);
    }

    // Budget constraint: applyTo(f, r) <= r for all valid f, r
    function prove_budgetConstraint(uint128 raw, uint256 rev) public pure {
        vm.assume(raw > 0);
        PremiumFactor f = fromRaw(raw);
        FeeRevenue r = FeeRevenue.wrap(rev);
        FeeRevenue premium = f.applyTo(r);
        assert(FeeRevenue.unwrap(premium) <= rev);
    }

    // Zero revenue yields zero premium
    function prove_zeroRevenue(uint128 raw) public pure {
        vm.assume(raw > 0);
        PremiumFactor f = fromRaw(raw);
        FeeRevenue premium = f.applyTo(FeeRevenue.wrap(0));
        assert(FeeRevenue.unwrap(premium) == 0);
    }

    // isMax iff raw == Q128_ONE
    function prove_isMax(uint128 raw) public pure {
        vm.assume(raw > 0);
        PremiumFactor f = fromRaw(raw);
        assert(f.isMax() == (raw == Q128_ONE));
    }

    // Zero raw reverts (cannot test revert in Kontrol prove_, use fuzz)
}
