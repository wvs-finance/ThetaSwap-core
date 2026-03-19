// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Compose-compatible ERC-20 diamond storage (keccak256("compose.erc20")).
// Inlined from Compose LibERC20.sol to avoid pragma >=0.8.30 requirement.
// Storage layout matches Compose exactly for future ERC20Facet compatibility.

bytes32 constant ERC20_STORAGE_POSITION = keccak256("compose.erc20");

struct ERC20Storage {
    mapping(address owner => uint256 balance) balanceOf;
    uint256 totalSupply;
    mapping(address owner => mapping(address spender => uint256 allowance)) allowance;
    uint8 decimals;
    string name;
    string symbol;
}

function getERC20Storage() pure returns (ERC20Storage storage s) {
    bytes32 position = ERC20_STORAGE_POSITION;
    assembly {
        s.slot := position
    }
}

function erc20Mint(address account, uint256 value) {
    if (account == address(0)) revert ERC20InvalidReceiver(address(0));
    ERC20Storage storage s = getERC20Storage();
    s.totalSupply += value;
    s.balanceOf[account] += value;
}

function erc20Burn(address account, uint256 value) {
    if (account == address(0)) revert ERC20InvalidSender(address(0));
    ERC20Storage storage s = getERC20Storage();
    uint256 bal = s.balanceOf[account];
    if (bal < value) revert ERC20InsufficientBalance(account, bal, value);
    unchecked {
        s.balanceOf[account] = bal - value;
        s.totalSupply -= value;
    }
}

error ERC20InvalidReceiver(address receiver);
error ERC20InvalidSender(address sender);
error ERC20InsufficientBalance(address sender, uint256 balance, uint256 needed);
