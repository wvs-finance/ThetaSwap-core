// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {CollectedFees} from "../types/CollectedFeesMod.sol";

// ReactVM-side state. Isolated from destination chain.
// No diamond storage needed — ReactVM is a standard EVM instance.
// This state accumulates Collect fees until consumed by Burn.

struct ReactVmStorage {
    // Accumulated Collect fees per V3 position.
    // Key: v3PositionKey(owner, tickLower, tickUpper) scoped by pool.
    mapping(address => mapping(bytes32 => CollectedFees)) collectedFees;
    // Pool whitelist synced from RN instance via self-subscription.
    mapping(uint256 => mapping(address => bool)) poolWhitelist;
}

bytes32 constant REACT_VM_STORAGE_SLOT = keccak256("ThetaSwapReactive.vm.storage");

function reactVmStorage() pure returns (ReactVmStorage storage s) {
    bytes32 slot = REACT_VM_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

function isWhitelisted(uint256 chainId_, address pool) view returns (bool) {
    return reactVmStorage().poolWhitelist[chainId_][pool];
}

function setWhitelisted(uint256 chainId_, address pool, bool status) {
    reactVmStorage().poolWhitelist[chainId_][pool] = status;
}

function getCollectedFees(address pool, bytes32 posKey) view returns (CollectedFees storage) {
    return reactVmStorage().collectedFees[pool][posKey];
}

function clearCollectedFees(address pool, bytes32 posKey) {
    delete reactVmStorage().collectedFees[pool][posKey];
}
