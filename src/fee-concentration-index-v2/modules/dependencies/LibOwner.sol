// SPDX-License-Identifier: MIT
// Copied from compose/access/Owner/LibOwner.sol — pragma changed to ^0.8.26
pragma solidity ^0.8.26;

event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

error OwnerUnauthorizedAccount();
error OwnerAlreadyRenounced();

bytes32 constant STORAGE_POSITION = keccak256("compose.owner");

struct OwnerStorage {
    address owner;
}

function getStorage() pure returns (OwnerStorage storage s) {
    bytes32 position = STORAGE_POSITION;
    assembly {
        s.slot := position
    }
}

function setContractOwner(address _initialOwner) {
    OwnerStorage storage s = getStorage();
    s.owner = _initialOwner;
    emit OwnershipTransferred(address(0), _initialOwner);
}

function owner() view returns (address) {
    return getStorage().owner;
}

function requireOwner() view {
    if (getStorage().owner != msg.sender) {
        revert OwnerUnauthorizedAccount();
    }
}

error AlreadyInitialized();

function initOwner(address _owner) {
    OwnerStorage storage s = getStorage();
    if (s.owner != address(0)) revert AlreadyInitialized();
    s.owner = _owner;
    emit OwnershipTransferred(address(0), _owner);
}

function transferOwnership(address _newOwner) {
    OwnerStorage storage s = getStorage();
    address previousOwner = s.owner;
    if (previousOwner == address(0)) {
        revert OwnerAlreadyRenounced();
    }
    s.owner = _newOwner;
    emit OwnershipTransferred(previousOwner, _newOwner);
}
