// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {FeeShareRatio, fromFeeGrowth, Q128, FEE_SHARE_ONE} from "typed-uniswap-v4/types/FeeShareRatioMod.sol";

contract FeeShareRatioProof is Test, KontrolCheats {
    // INV-006: Fee share ratio always in [0, type(uint128).max]
    // Inputs constrained to uint128 — avoids solady mulDiv 512-bit assembly path
    // that Kontrol cannot symbolically verify. Full uint256 range tested via fuzz.
    function prove_feeShareRatio_bounds() public view {
        uint128 positionFee = freshUInt128();
        uint128 rangeFee = freshUInt128();
        vm.assume(rangeFee > 0);
        vm.assume(positionFee <= rangeFee);

        FeeShareRatio x = fromFeeGrowth(uint256(positionFee), uint256(rangeFee));
        assert(x.unwrap() <= FEE_SHARE_ONE);
    }

    // INV-007: Fee share is zero when no fees generated
    function prove_feeShareRatio_zero_when_no_fees() public view {
        uint256 positionFee = freshUInt256();

        FeeShareRatio x = fromFeeGrowth(positionFee, 0);
        assert(x.unwrap() == 0);
    }

    // SC-006: x_k^2 via mulDiv does not overflow (returns valid Q128)
    function prove_feeShareRatio_square_no_overflow() public view {
        uint128 raw = freshUInt128();

        FeeShareRatio x = FeeShareRatio.wrap(raw);
        uint256 xSquared = x.square();

        // x in [0, 2^128-1], so x^2/Q128 in [0, 2^128-2]
        assert(xSquared <= type(uint128).max);
    }
}
