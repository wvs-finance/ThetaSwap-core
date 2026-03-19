// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    oraclePoke,
    oracleSettle,
    oracleRedeemLong,
    oracleRedeemShort
} from "@fci-token-vault/modules/OraclePayoffMod.sol";
import {
    getOraclePayoffStorage,
    OraclePayoffStorage,
    VaultNotSettled
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {
    reentrancyGuardEnter,
    reentrancyGuardExit
} from "@fci-token-vault/modules/dependencies/ReentrancyLib.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

uint256 constant Q96 = SqrtPriceLibrary.Q96;

/// @title OraclePayoffFacet — removable Model B diamond facet
/// @dev Handles oracle-dependent operations. Removed when CFMM ships (issue #41).
contract OraclePayoffFacet {
    event OracleSettlement(uint256 longPayoutPerToken, uint160 finalHWM);
    event HWMUpdated(uint160 newHwmSqrtPrice, uint160 currentSqrtPrice);
    event RedeemLong(address indexed redeemer, uint256 amount, uint256 payout);
    event RedeemShort(address indexed redeemer, uint256 amount, uint256 payout);

    function poke() external {
        uint160 currentSqrtPrice = oraclePoke();
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        emit HWMUpdated(os.sqrtPriceHWM, currentSqrtPrice);
    }

    function settle() external {
        oracleSettle();
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        emit OracleSettlement(os.longPayoutPerToken, os.sqrtPriceHWM);
    }

    /// @notice Burn LONG tokens, receive USDC payout.
    /// CEI: burn tokens + update totalDeposits → transfer USDC out.
    /// Module computes payout internally (mulDiv rounds DOWN, favors vault).
    function redeemLong(uint256 amount) external {
        reentrancyGuardEnter();

        // E: burn LONG, compute payout, update totalDeposits (all in module)
        uint256 payout = oracleRedeemLong(msg.sender, amount);

        // I: transfer payout
        if (payout > 0) {
            CustodianStorage storage cs = getCustodianStorage();
            SafeTransferLib.safeTransfer(cs.collateralToken, msg.sender, payout);
        }

        emit RedeemLong(msg.sender, amount, payout);
        reentrancyGuardExit();
    }

    /// @notice Burn SHORT tokens, receive USDC payout.
    /// CEI: burn tokens + update totalDeposits → transfer USDC out.
    /// Module computes payout internally (amount - longPortion).
    function redeemShort(uint256 amount) external {
        reentrancyGuardEnter();

        // E: burn SHORT, compute payout, update totalDeposits (all in module)
        uint256 payout = oracleRedeemShort(msg.sender, amount);

        // I: transfer payout
        if (payout > 0) {
            CustodianStorage storage cs = getCustodianStorage();
            SafeTransferLib.safeTransfer(cs.collateralToken, msg.sender, payout);
        }

        emit RedeemShort(msg.sender, amount, payout);
        reentrancyGuardExit();
    }

    /// @notice Preview LONG payout. Rounds DOWN.
    function previewLongPayout(uint256 amount) external view returns (uint256) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (!os.settled) revert VaultNotSettled();
        return FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, Q96);
    }

    /// @notice Preview SHORT payout. Rounds DOWN.
    function previewShortPayout(uint256 amount) external view returns (uint256) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (!os.settled) revert VaultNotSettled();
        uint256 longPortion = FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, Q96);
        return amount - longPortion;
    }

    /// @notice Current payoff ratio (Q96-scaled).
    function payoffRatio() external view returns (uint256 longPerToken, uint256 shortPerToken) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (!os.settled) revert VaultNotSettled();
        longPerToken = os.longPayoutPerToken;
        shortPerToken = Q96 - os.longPayoutPerToken;
    }

    function isSettled() external view returns (bool) {
        return getOraclePayoffStorage().settled;
    }
}
