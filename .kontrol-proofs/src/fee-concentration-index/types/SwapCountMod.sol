// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// theta = (1 << 128) / lifetime, where lifetime = SwapCount at removal
// lifetime * theta = Q128, so SwapCount must fit in uint32
// (max ~4.3B swaps, theta precision floor = 2^96)

type SwapCount is uint32;

function unwrap(SwapCount n) pure returns (uint32) {
    return SwapCount.unwrap(n);
}

function increment(SwapCount n) pure returns (SwapCount) {
    return SwapCount.wrap(SwapCount.unwrap(n) + 1);
}

function isZero(SwapCount n) pure returns (bool) {
    return SwapCount.unwrap(n) == 0;
}

using {unwrap, increment, isZero} for SwapCount global;
