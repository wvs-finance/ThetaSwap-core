// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {
    SyntheticFeeGrowth,
    fromBurnAmount,
    toFeeShareRatio
} from "../../../src/reactive-integration/types/SyntheticFeeGrowthMod.sol";
import {FeeShareRatio, FEE_SHARE_ONE} from "../../../src/fee-concentration-index/types/FeeShareRatioMod.sol";

contract SyntheticFeeGrowthProof is Test, KontrolCheats {
    // RX-008: fromBurnAmount returns zero when liquidity is zero (division avoided)
    function prove_syntheticFeeGrowth_zeroLiquidity() public view {
        uint256 amount0 = freshUInt256();

        SyntheticFeeGrowth delta = fromBurnAmount(amount0, 0);
        assert(delta.unwrap() == 0);
    }

    // RX-008: toFeeShareRatio result is bounded in [0, FEE_SHARE_ONE]
    // Inputs constrained to uint128 to avoid solady mulDiv 512-bit path.
    function prove_syntheticFeeGrowth_feeShareBounds() public view {
        uint128 posRaw = freshUInt128();
        uint128 rangeRaw = freshUInt128();
        vm.assume(rangeRaw > 0);
        vm.assume(posRaw <= rangeRaw);

        SyntheticFeeGrowth posDelta = SyntheticFeeGrowth.wrap(uint256(posRaw));
        SyntheticFeeGrowth rangeDelta = SyntheticFeeGrowth.wrap(uint256(rangeRaw));

        FeeShareRatio ratio = toFeeShareRatio(posDelta, rangeDelta);
        assert(ratio.unwrap() <= FEE_SHARE_ONE);
    }

    // RX-008: toFeeShareRatio returns zero when rangeDelta is zero
    function prove_syntheticFeeGrowth_zeroRange() public view {
        uint256 posRaw = freshUInt256();

        SyntheticFeeGrowth posDelta = SyntheticFeeGrowth.wrap(posRaw);
        SyntheticFeeGrowth rangeDelta = SyntheticFeeGrowth.wrap(0);

        FeeShareRatio ratio = toFeeShareRatio(posDelta, rangeDelta);
        assert(ratio.unwrap() == 0);
    }
}
