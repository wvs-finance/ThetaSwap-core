// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @title IOraclePayoff — removable Model B interface
/// @dev Will be replaced when CFMM ships (Model C). See issue #41.
interface IOraclePayoff {
    /// @notice Permissionless HWM update. Reads FCI oracle, applies decay.
    function poke() external;

    /// @notice Settle vault after expiry. Computes final LONG/SHORT payout split.
    function settle() external;

    /// @notice Burn LONG tokens, receive oracle-determined USDC payout.
    /// @param amount LONG token amount to redeem
    function redeemLong(uint256 amount) external;

    /// @notice Burn SHORT tokens, receive oracle-determined USDC payout.
    /// @param amount SHORT token amount to redeem
    function redeemShort(uint256 amount) external;

    /// @notice Preview LONG payout at current oracle state.
    /// @return payout USDC amount per `amount` LONG tokens
    function previewLongPayout(uint256 amount) external view returns (uint256 payout);

    /// @notice Preview SHORT payout at current oracle state.
    /// @return payout USDC amount per `amount` SHORT tokens
    function previewShortPayout(uint256 amount) external view returns (uint256 payout);

    /// @notice Current payoff ratio: (longPerToken, shortPerToken) in Q96.
    /// @dev longPerToken + shortPerToken = Q96 (conservation).
    function payoffRatio() external view returns (uint256 longPerToken, uint256 shortPerToken);

    /// @notice Whether the vault has been settled.
    function isSettled() external view returns (bool);

    event OracleSettlement(uint256 longPayoutPerToken, uint160 finalHWM);
    event HWMUpdated(uint160 newHwmSqrtPrice, uint160 currentSqrtPrice);
    event RedeemLong(address indexed redeemer, uint256 amount, uint256 payout);
    event RedeemShort(address indexed redeemer, uint256 amount, uint256 payout);
}
