// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Composable bitmask flags for hookData protocol dispatch.
// First byte of hookData encodes source + protocol.
uint8 constant REACTIVE_FLAG = 0x01; // callback from Reactive Network
uint8 constant V3_FLAG       = 0x02; // Uniswap V3 source
uint8 constant V4_FLAG       = 0x00; // Uniswap V4 source (default: no flags = V4)

// note: The hookData ius the one that has the flags prestent this fucntions are the ones that return
// wheter the bytes has the flags

function isUniswapV4(bytes calldata hookData) pure returns(bool){
    if (hookData.length == 0) return true;
    return (uint8(hookData[0]) & (REACTIVE_FLAG | V3_FLAG)) == 0;
}

function isUniswapV3(bytes calldata hookData) pure returns(bool){
    if (hookData.length == 0) return false;
    return (uint8(hookData[0]) & V3_FLAG) != 0;
}

function isReactive(bytes calldata hookData) pure returns(bool){
    if (hookData.length == 0) return false;
    return (uint8(hookData[0]) & REACTIVE_FLAG) != 0;
}

function isUniswapV3Reactive(bytes calldata hookData) pure returns(bool){
    return (isUniswapV3(hookData) && isReactive(hookData));
}

function isReactive(uint8 flags) pure returns (bool) {
    return (flags & REACTIVE_FLAG) != 0;
}

function isV3(uint8 flags) pure returns (bool) {
    return (flags & V3_FLAG) != 0;
}

function isV4(uint8 flags) pure returns (bool) {
    return (flags & (REACTIVE_FLAG | V3_FLAG)) == 0;
}

// ── Encode helpers (used by ReactLogicMod to build callback hookData) ──

function encodeSwapHookData(uint8 flags, int24 tickBefore, int24 tickAfter) pure returns (bytes memory) {
    return abi.encodePacked(flags, tickBefore, tickAfter);
}

function encodeMintHookData(uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) pure returns (bytes memory) {
    return abi.encodePacked(flags, owner, tickLower, tickUpper, liquidity);
}

function encodeBurnHookData(uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) pure returns (bytes memory) {
    return abi.encodePacked(flags, owner, tickLower, tickUpper, liquidity);
}

// ── Decode helpers (used by FCI hook to read hookData) ──
// Uses abi.encodePacked layout: tightly packed, no padding.

function decodeSwapHookData(bytes memory data) pure returns (uint8 flags, int24 tickBefore, int24 tickAfter) {
    // Layout: [uint8(1)] [int24(3)] [int24(3)] = 7 bytes
    assembly {
        let ptr := add(data, 32) // skip length prefix
        let word := mload(ptr)
        flags := shr(248, word)                        // first byte
        tickBefore := signextend(2, shr(224, word))    // bytes 1-3
        tickAfter := signextend(2, shr(200, word))     // bytes 4-6
    }
}

function decodeMintHookData(bytes memory data) pure returns (uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) {
    // Layout: [uint8(1)] [address(20)] [int24(3)] [int24(3)] [uint128(16)] = 43 bytes
    assembly {
        let ptr := add(data, 32)
        let word0 := mload(ptr)
        flags := shr(248, word0)
        owner := and(shr(88, word0), 0xffffffffffffffffffffffffffffffffffffffff)
        tickLower := signextend(2, shr(64, word0))
        // tickUpper spans word boundary at byte 24
        let word1 := mload(add(ptr, 24))
        tickUpper := signextend(2, shr(232, word1))
        liquidity := and(shr(104, word1), 0xffffffffffffffffffffffffffffffff)
    }
}

function decodeBurnHookData(bytes memory data) pure returns (uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) {
    return decodeMintHookData(data); // same layout
}
