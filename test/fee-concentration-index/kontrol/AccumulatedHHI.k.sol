// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {AccumulatedHHI, addTerm, toIndexA, toIndexB, Q128, INDEX_ONE} from "../../../src/fee-concentration-index/types/AccumulatedHHIMod.sol";
import {BlockCount} from "../../../src/fee-concentration-index/types/BlockCountMod.sol";

contract AccumulatedHHIProof is Test, KontrolCheats {
    // INV-008: Accumulated sum only increases — addTerm produces value >= input
    function prove_accumulatedHHI_monotonic() public view {
        uint128 sumRaw = freshUInt128();
        uint256 lifetime = freshUInt256();
        uint128 xSquared = freshUInt128();
        vm.assume(lifetime > 0);

        AccumulatedHHI before_ = AccumulatedHHI.wrap(uint256(sumRaw));
        AccumulatedHHI after_ = addTerm(before_, BlockCount.wrap(lifetime), uint256(xSquared));

        assert(after_.unwrap() >= before_.unwrap());
    }

    // INV-009a: Index A is capped at INDEX_ONE
    function prove_indexA_capped_at_one() public view {
        uint256 sumRaw = freshUInt256();

        AccumulatedHHI sum = AccumulatedHHI.wrap(sumRaw);
        uint128 a = toIndexA(sum);

        assert(a <= INDEX_ONE);
    }

    // INV-009b: B_T = INDEX_ONE - A_T, so B_T + A_T == INDEX_ONE
    function prove_indexB_complement() public view {
        uint256 sumRaw = freshUInt256();

        AccumulatedHHI sum = AccumulatedHHI.wrap(sumRaw);
        uint128 a = toIndexA(sum);
        uint128 b = toIndexB(sum);

        assert(uint256(a) + uint256(b) == uint256(INDEX_ONE));
    }

    // INV-009c: Index A is zero when accumulated sum is zero
    function prove_indexA_zero_when_sum_zero() public pure {
        AccumulatedHHI sum = AccumulatedHHI.wrap(0);
        assert(toIndexA(sum) == 0);
    }
}
