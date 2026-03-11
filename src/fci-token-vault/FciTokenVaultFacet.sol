// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    deposit as _deposit,
    settle as _settle,
    redeem as _redeem,
    poke as _poke,
    getFciVaultStorage,
    FciVaultStorage
} from "@fci-token-vault/modules/FciTokenVaultMod.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

contract FciTokenVaultFacet {
    function deposit(uint256 amount) external {
        FciVaultStorage storage vs = getFciVaultStorage();
        SafeTransferLib.safeTransferFrom(vs.collateralToken, msg.sender, address(this), amount);
        _deposit(msg.sender, amount);
    }

    function settle() external {
        _settle();
    }

    function redeem(uint256 amount) external {
        FciVaultStorage storage vs = getFciVaultStorage();

        uint256 longPayout = (amount * vs.longPayoutPerToken) / SqrtPriceLibrary.Q96;
        uint256 shortPayout = amount - longPayout;

        _redeem(msg.sender, amount);

        if (longPayout > 0) {
            SafeTransferLib.safeTransfer(vs.collateralToken, msg.sender, longPayout);
        }
        if (shortPayout > 0) {
            SafeTransferLib.safeTransfer(vs.collateralToken, msg.sender, shortPayout);
        }
    }

    function poke() external {
        _poke();
    }
}
