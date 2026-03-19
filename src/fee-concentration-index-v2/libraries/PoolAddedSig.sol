// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// keccak256("PoolAdded(address,address,bytes32,bytes2,bytes)")
// Shared across all protocol facets — unified topic0.
uint256 constant POOL_ADDED_SIG = 0x87b7fc1d2e292c55531c58e21885855f07db3a03b215cab62c4469c5bfd22803;
