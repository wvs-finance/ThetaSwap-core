// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Compose-compatible ERC6909 diamond storage (keccak256("compose.erc6909")).
// Inlined from Compose LibERC6909.sol to avoid pragma >=0.8.30 requirement.
// Storage layout matches Compose exactly for future ERC6909Facet compatibility.

bytes32 constant ERC6909_STORAGE_POSITION = keccak256("compose.erc6909");

struct ERC6909Storage {
    mapping(address owner => mapping(uint256 id => uint256 amount)) balanceOf;
    mapping(address owner => mapping(address spender => mapping(uint256 id => uint256 amount))) allowance;
    mapping(address owner => mapping(address spender => bool)) isOperator;
}

function getERC6909Storage() pure returns (ERC6909Storage storage s) {
    bytes32 position = ERC6909_STORAGE_POSITION;
    assembly {
        s.slot := position
    }
}

function erc6909Mint(address to, uint256 id, uint256 amount) {
    if (to == address(0)) revert ERC6909InvalidReceiver(address(0));
    getERC6909Storage().balanceOf[to][id] += amount;
}

function erc6909Burn(address from, uint256 id, uint256 amount) {
    if (from == address(0)) revert ERC6909InvalidSender(address(0));
    ERC6909Storage storage s = getERC6909Storage();
    uint256 balance = s.balanceOf[from][id];
    if (balance < amount) revert ERC6909InsufficientBalance(from, balance, amount, id);
    unchecked {
        s.balanceOf[from][id] = balance - amount;
    }
}

error ERC6909InvalidReceiver(address receiver);
error ERC6909InvalidSender(address sender);
error ERC6909InsufficientBalance(address sender, uint256 balance, uint256 needed, uint256 id);
