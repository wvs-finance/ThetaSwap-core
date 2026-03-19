// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Action types for V3 reactive callback → FCI V2 hook dispatch.
// Semantically aligned with V4 IHooks hook names.
// Carried in hookData at byte offset 22 (after 2-byte flag + 20-byte pool address).

uint8 constant AFTER_ADD_LIQUIDITY = 0x01;
uint8 constant BEFORE_SWAP = 0x02;
uint8 constant AFTER_SWAP = 0x03;
uint8 constant BEFORE_REMOVE_LIQUIDITY = 0x04;
uint8 constant AFTER_REMOVE_LIQUIDITY = 0x05;
