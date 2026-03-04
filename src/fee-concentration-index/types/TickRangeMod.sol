// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// TickRange identifies a unique (tickLower, tickUpper) pair via keccak256 hash.
// Used as storage key for per-range swap counters and position sets.
// tickSpacing is a pool-level property — not encoded in the range key.

type TickRange is bytes32;

function fromTicks(int24 tickLower, int24 tickUpper) pure returns (TickRange) {
    return TickRange.wrap(keccak256(abi.encode(tickLower, tickUpper)));
}

function unwrap(TickRange rk) pure returns (bytes32) {
    return TickRange.unwrap(rk);
}

function eq(TickRange a, TickRange b) pure returns (bool) {
    return TickRange.unwrap(a) == TickRange.unwrap(b);
}

function isZero(TickRange rk) pure returns (bool) {
    return TickRange.unwrap(rk) == bytes32(0);
}

// O(1) overlap test on two half-open tick ranges [lA, uA) and [lB, uB).
// Returns true iff the ranges share at least one tick.
function intersects(
    int24 lowerA, int24 upperA,
    int24 lowerB, int24 upperB
) pure returns (bool) {
    return lowerA < upperB && lowerB < upperA;
}

using {unwrap, eq, isZero} for TickRange global;
