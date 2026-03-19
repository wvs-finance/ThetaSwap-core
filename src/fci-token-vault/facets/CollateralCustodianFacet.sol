// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    custodianDeposit,
    custodianRedeemPair
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {
    getERC6909Storage
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {
    reentrancyGuardEnter,
    reentrancyGuardExit
} from "@fci-token-vault/modules/dependencies/ReentrancyLib.sol";
import {
    getOraclePayoffStorage,
    VaultAlreadySettled
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";

/// @title CollateralCustodianFacet — permanent diamond facet
/// @dev Handles USDC custody with CEI ordering. Survives Model B→C transition.
contract CollateralCustodianFacet {
    event PairedMint(address indexed depositor, uint256 amount);
    event PairedBurn(address indexed redeemer, uint256 amount);

    /// @notice Deposit USDC, receive equal LONG + SHORT tokens.
    /// CEI: transfer USDC in → update state → mint tokens.
    function deposit(uint256 amount) external {
        reentrancyGuardEnter();
        if (getOraclePayoffStorage().settled) revert VaultAlreadySettled();

        CustodianStorage storage cs = getCustodianStorage();

        // C: checks happen inside custodianDeposit (zero, cap)
        // E+I: transfer collateral FIRST (Panoptic pattern: get money before promises)
        SafeTransferLib.safeTransferFrom(cs.collateralToken, msg.sender, address(this), amount);

        // E: update internal state + mint tokens
        custodianDeposit(msg.sender, amount);

        emit PairedMint(msg.sender, amount);
        reentrancyGuardExit();
    }

    /// @notice Burn equal LONG + SHORT, receive exact USDC back.
    /// CEI: burn tokens + update state → transfer USDC out.
    function redeemPair(uint256 amount) external {
        reentrancyGuardEnter();

        CustodianStorage storage cs = getCustodianStorage();

        // E: burn tokens + update state
        custodianRedeemPair(msg.sender, amount);

        // I: transfer collateral LAST
        SafeTransferLib.safeTransfer(cs.collateralToken, msg.sender, amount);

        emit PairedBurn(msg.sender, amount);
        reentrancyGuardExit();
    }

    /// @notice Preview deposit amounts (always 1:1).
    function previewDeposit(uint256 amount) external pure returns (uint256, uint256) {
        return (amount, amount);
    }

    /// @notice Total USDC backing all tokens.
    function totalDeposited() external view returns (uint128) {
        return getCustodianStorage().totalDeposits;
    }

    /// @notice ERC-6909 balance query.
    function balanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }
}
