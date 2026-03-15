// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Protocol flag registry — deterministic bytes2 identifiers.
// Values are hardcoded for gas efficiency. Derivations shown in comments.

// bytes2(type(uint16).max)
bytes2 constant NATIVE_V4 = bytes2(0xFFFF);

// bytes2(uint16(type(uint8).max / 2))
bytes2 constant REACTIVE = bytes2(0x007F);

// bytes2(keccak256("uniswap-v4"))
bytes2 constant UNISWAP_V4 = bytes2(0xBD70);

// bytes2(keccak256("uniswap-v3"))
bytes2 constant UNISWAP_V3 = bytes2(0x5282);

// bytes2(keccak256("uniswap-v2"))
bytes2 constant UNISWAP_V2 = bytes2(0x5F4C);
