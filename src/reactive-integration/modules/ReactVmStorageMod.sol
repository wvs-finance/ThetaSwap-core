// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// ReactVM-side state. Isolated from destination chain.
// Pool whitelist synced from RN instance via self-subscription.

struct TickShadow {
    int24 tick;
    bool isSet;
}

struct ReactVmStorage {
    // Pool whitelist synced from RN instance via self-subscription.
    mapping(uint256 => mapping(address => bool)) poolWhitelist;
    mapping(uint256 => mapping(address => TickShadow)) tickShadow;
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

function getLastTick(uint256 chainId_, address pool) view returns (int24 tick, bool isSet) {
    TickShadow storage ts = reactVmStorage().tickShadow[chainId_][pool];
    tick = ts.tick;
    isSet = ts.isSet;
}

function setLastTick(uint256 chainId_, address pool, int24 tick) {
    TickShadow storage ts = reactVmStorage().tickShadow[chainId_][pool];
    ts.tick = tick;
    ts.isSet = true;
}
