// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {BlockCount} from "./BlockCountMod.sol";

// accumulatedSum = sum of (x_k^2 / lifetime) across all removed positions
// x_k = positionFeeDelta / rangeFeeDelta (Option B: delta-based, lifetime-scoped)
// stored as Q128. A_T = sqrt(accumulatedSum), B_T = 1 - A_T computed lazily.
// uint256 because the sum can exceed uint128 after many position removals.

type AccumulatedHHI is uint256;

uint256 constant Q128 = 1 << 128;
uint128 constant INDEX_ONE = type(uint128).max;

function addTerm(
    AccumulatedHHI sum,
    BlockCount blockLifetime,
    uint256 xSquaredQ128
) pure returns (AccumulatedHHI) {
    // term = x_k^2 / max(1, blockLifetime) (Q128 / uint256 = Q128)
    uint256 term = xSquaredQ128 / blockLifetime.floorOne();
    return AccumulatedHHI.wrap(AccumulatedHHI.unwrap(sum) + term);
}

function toIndexA(AccumulatedHHI sum) pure returns (uint128) {
    uint256 raw = AccumulatedHHI.unwrap(sum);
    // if sum >= Q128, A_T >= 1.0, cap at INDEX_ONE
    if (raw >= Q128) return INDEX_ONE;
    // sqrt(sum << 128) gives Q128 result. Safe because raw < Q128 so (raw << 128) < 2^256
    uint256 a = FixedPointMathLib.sqrt(raw << 128);
    if (a > INDEX_ONE) return INDEX_ONE;
    return uint128(a);
}

function toIndexB(AccumulatedHHI sum) pure returns (uint128) {
    return INDEX_ONE - toIndexA(sum);
}

function unwrap(AccumulatedHHI sum) pure returns (uint256) {
    return AccumulatedHHI.unwrap(sum);
}

using {addTerm, toIndexA, toIndexB, unwrap} for AccumulatedHHI global;
