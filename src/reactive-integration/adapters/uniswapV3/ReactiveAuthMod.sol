// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Auth checks for ReactiveHookAdapter callback functions.
// No modifier keyword — inline revert via free functions. SCOP compliant.

error UnauthorizedCaller(address caller);
error InvalidRvmId(address provided, address expected);

function requireAuthorized(address caller, mapping(address => bool) storage authorizedCallers) view {
    if (!authorizedCallers[caller]) revert UnauthorizedCaller(caller);
}

function requireRvmId(address provided, address expected) pure {
    if (provided != expected) revert InvalidRvmId(provided, expected);
}
