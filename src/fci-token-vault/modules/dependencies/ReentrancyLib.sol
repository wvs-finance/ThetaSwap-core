// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @dev Transient-storage reentrancy guard (EIP-1153).
/// Cheaper than SSTORE-based guards (100 gas vs 5000 gas per enter).
/// Auto-clears at end of transaction.

bytes32 constant REENTRANCY_SLOT = keccak256("thetaswap.reentrancy-guard");

error ReentrancyGuardReentrant();

function reentrancyGuardEnter() {
    bytes32 slot = REENTRANCY_SLOT;
    uint256 locked;
    assembly {
        locked := tload(slot)
    }
    if (locked != 0) revert ReentrancyGuardReentrant();
    assembly {
        tstore(slot, 1)
    }
}

function reentrancyGuardExit() {
    bytes32 slot = REENTRANCY_SLOT;
    assembly {
        tstore(slot, 0)
    }
}
