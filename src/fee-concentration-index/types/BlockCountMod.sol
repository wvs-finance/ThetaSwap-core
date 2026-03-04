// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Block-based lifetime for HHI weighting.
// blockLifetime = block.number at removal - block.number at add.
// JIT in same block -> 0, floored to 1 for HHI divisor.
// uint256 to match block.number type.

type BlockCount is uint256;

function unwrap(BlockCount n) pure returns (uint256) {
    return BlockCount.unwrap(n);
}

function isZero(BlockCount n) pure returns (bool) {
    return BlockCount.unwrap(n) == 0;
}

function floorOne(BlockCount n) pure returns (uint256) {
    uint256 raw = BlockCount.unwrap(n);
    return raw == 0 ? 1 : raw;
}

using {unwrap, isZero, floorOne} for BlockCount global;
