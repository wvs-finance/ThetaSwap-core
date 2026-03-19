// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// ReactVM-side shadow state for V3 reactive integration (V2).
// Shadows pool state that native V4 "before" hooks would read synchronously.
// Slot: keccak256("thetaSwap.fci.v3.reactvm") — V2-scoped, no V1 collision.

struct TickShadow {
    int24 tick;
    bool isSet;
}

struct PositionShadow {
    uint128 liquidity;
    bool isSet;
}

struct UniswapV3ReactVMStorage {
    mapping(uint256 => mapping(address => bool)) poolWhitelist;
    mapping(uint256 => mapping(address => TickShadow)) tickShadow;
    mapping(uint256 => mapping(address => mapping(bytes32 => PositionShadow))) positionShadow;
}

bytes32 constant UNISWAP_V3_REACTVM_SLOT = keccak256("thetaSwap.fci.v3.reactvm");

function uniswapV3ReactVMStorage() pure returns (UniswapV3ReactVMStorage storage $) {
    bytes32 slot = UNISWAP_V3_REACTVM_SLOT;
    assembly ("memory-safe") { $.slot := slot }
}

// ── Tick shadow ──

function getLastTick(uint256 chainId, address pool) view returns (int24 tick, bool isSet) {
    TickShadow storage ts = uniswapV3ReactVMStorage().tickShadow[chainId][pool];
    tick = ts.tick;
    isSet = ts.isSet;
}

function setLastTick(uint256 chainId, address pool, int24 tick) {
    TickShadow storage ts = uniswapV3ReactVMStorage().tickShadow[chainId][pool];
    ts.tick = tick;
    ts.isSet = true;
}

// ── Position shadow ──

function getPositionShadow(uint256 chainId, address pool, bytes32 posKey)
    view
    returns (uint128 liquidity, bool isSet)
{
    PositionShadow storage ps = uniswapV3ReactVMStorage().positionShadow[chainId][pool][posKey];
    liquidity = ps.liquidity;
    isSet = ps.isSet;
}

function setPositionShadow(uint256 chainId, address pool, bytes32 posKey, uint128 liquidity) {
    PositionShadow storage ps = uniswapV3ReactVMStorage().positionShadow[chainId][pool][posKey];
    ps.liquidity = liquidity;
    ps.isSet = true;
}

// ── Pool whitelist ──

function isWhitelisted(uint256 chainId, address pool) view returns (bool) {
    return uniswapV3ReactVMStorage().poolWhitelist[chainId][pool];
}

function setWhitelisted(uint256 chainId, address pool, bool whitelisted) {
    uniswapV3ReactVMStorage().poolWhitelist[chainId][pool] = whitelisted;
}
