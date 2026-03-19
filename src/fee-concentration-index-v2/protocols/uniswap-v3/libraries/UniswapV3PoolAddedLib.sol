// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @dev Encode/decode the `bytes data` field of PoolAdded for Uniswap V3.
/// V3 data = (uint256 chainId, address pool, address protocolStateView).
/// For V3, protocolStateView == pool (the pool IS the state source).

function encodeV3PoolAddedData(
    uint256 chainId,
    address pool,
    address protocolStateView
) pure returns (bytes memory) {
    return abi.encode(chainId, pool, protocolStateView);
}

function decodeV3PoolAddedData(
    bytes memory data
) pure returns (uint256 chainId, address pool, address protocolStateView) {
    (chainId, pool, protocolStateView) = abi.decode(data, (uint256, address, address));
}
