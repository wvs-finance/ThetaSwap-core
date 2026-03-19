// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @title ICollateralCustodian — permanent vault interface
/// @dev Survives Model B→C transition. Only paired operations (no oracle dependency).
interface ICollateralCustodian {
    /// @notice Deposit USDC, receive equal LONG + SHORT ERC-6909 tokens.
    /// @param amount USDC amount (must be > 0, within depositCap)
    function deposit(uint256 amount) external;

    /// @notice Burn equal LONG + SHORT tokens, receive exact USDC back.
    /// @dev Risk-free exit. No oracle dependency. Always returns exactly `amount` USDC.
    /// @param amount Token amount to redeem (must hold >= amount of both LONG and SHORT)
    function redeemPair(uint256 amount) external;

    /// @notice Preview deposit: returns (longAmount, shortAmount) — always equal to amount.
    function previewDeposit(uint256 amount) external view returns (uint256 longAmount, uint256 shortAmount);

    /// @notice Total USDC deposited and backing all tokens.
    function totalDeposited() external view returns (uint128);

    /// @notice ERC-6909 balance query.
    function balanceOf(address owner, uint256 id) external view returns (uint256);

    event PairedMint(address indexed depositor, uint256 amount);
    event PairedBurn(address indexed redeemer, uint256 amount);
}
