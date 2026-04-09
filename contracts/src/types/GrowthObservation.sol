// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {SafeCastLib} from "solady/src/utils/SafeCastLib.sol";

// GrowthObservation (bytes32) — bit-packed, single-slot accumulator snapshot (V2)
//
// From LSB to MSB:
// ===== Layout (256 bits = 1 slot) =============================
//   Property             Size      Offset    Comment
//   blockNumber          32 bits   0         Block number at observation
//   relativeTimeDelta    16 bits   32        Seconds since previous observation
//   cumulativeGrowth     208 bits  48        Truncated globalGrowth (Q128.128 → Q80.128)
// ==============================================================

type GrowthObservation is bytes32;

// ── Masks ──

uint256 constant BLOCK_NUMBER_MASK = (1 << 32) - 1;
uint256 constant RELATIVE_TIME_DELTA_MASK = (1 << 16) - 1;
uint256 constant CUMULATIVE_GROWTH_MASK = (1 << 208) - 1;

// ── Errors ──

error StaleObservation(uint32 observedBlock, uint32 currentBlock);

// ── Constructor ──

/// @notice Packs a block number, relative time delta, and cumulative growth into a single slot.
/// @dev Safe-casts all uint256 inputs — reverts on overflow.
///
/// @custom:safety uint32 blockNumber supports ~4.3 billion blocks (~1,633 years at 12s/block).
/// @custom:safety uint16 relativeTimeDelta supports up to 65,535 seconds (~18.2 hours).
///   Overflow reverts via SafeCastLib — this surfaces keeper liveness failures.
/// @custom:safety uint208 cumulativeGrowth: Q128.128 truncation leaves 80 integer bits,
///   supporting ~1.2 million tokens per unit of liquidity cumulatively. SafeCastLib.toUint208()
///   reverts on overflow — correct fail-safe since such overflow would indicate a bug.
function newGrowthObservation(
    uint256 _blockNumber,
    uint256 _relativeTimeDelta,
    uint256 _cumulativeGrowth
) pure returns (GrowthObservation) {
    return GrowthObservation.wrap(
        bytes32(
            uint256(SafeCastLib.toUint32(_blockNumber))
                | (uint256(SafeCastLib.toUint16(_relativeTimeDelta)) << 32)
                | (uint256(SafeCastLib.toUint208(_cumulativeGrowth)) << 48)
        )
    );
}

// ── Field accessors ──

function blockNumber(GrowthObservation self) pure returns (uint32) {
    unchecked {
        return uint32(uint256(GrowthObservation.unwrap(self)) & BLOCK_NUMBER_MASK);
    }
}

function relativeTimeDelta(GrowthObservation self) pure returns (uint16) {
    unchecked {
        return uint16((uint256(GrowthObservation.unwrap(self)) >> 32) & RELATIVE_TIME_DELTA_MASK);
    }
}

function cumulativeGrowth(GrowthObservation self) pure returns (uint208) {
    unchecked {
        return uint208((uint256(GrowthObservation.unwrap(self)) >> 48) & CUMULATIVE_GROWTH_MASK);
    }
}

// ── Derived views ──

/// @notice Returns the growth delta between two observations.
/// @custom:safety Callers MUST ensure `later.cumulativeGrowth() >= earlier.cumulativeGrowth()`.
///   Unchecked subtraction wraps modulo 2^208 on violation. The ring buffer's monotonicity
///   invariant guarantees correct ordering for observations retrieved via `observeAt()`.
function growthDelta(GrowthObservation earlier, GrowthObservation later) pure returns (uint208) {
    unchecked {
        return later.cumulativeGrowth() - earlier.cumulativeGrowth();
    }
}

/// @notice Returns the elapsed blocks between two observations.
/// @custom:safety Callers MUST ensure `later.blockNumber() >= earlier.blockNumber()`.
///   Unchecked subtraction wraps modulo 2^32 on violation.
function elapsedBlocks(GrowthObservation earlier, GrowthObservation later) pure returns (uint32) {
    unchecked {
        return later.blockNumber() - earlier.blockNumber();
    }
}

/// @notice Returns true if the observation is uninitialized (zero).
function isZero(GrowthObservation self) pure returns (bool) {
    return GrowthObservation.unwrap(self) == bytes32(0);
}

/// @notice Returns true if `a.blockNumber() >= b.blockNumber()`.
function gte(GrowthObservation a, GrowthObservation b) pure returns (bool) {
    unchecked {
        return a.blockNumber() >= b.blockNumber();
    }
}

/// @notice Returns true if `a.blockNumber() < b.blockNumber()`.
function lt(GrowthObservation a, GrowthObservation b) pure returns (bool) {
    unchecked {
        return a.blockNumber() < b.blockNumber();
    }
}

/// @notice Returns true if `self.blockNumber() >= targetBlock`.
function blockNumberGte(GrowthObservation self, uint32 targetBlock) pure returns (bool) {
    unchecked {
        return self.blockNumber() >= targetBlock;
    }
}

/// @notice Returns true if `self.blockNumber() < targetBlock`.
function blockNumberLt(GrowthObservation self, uint32 targetBlock) pure returns (bool) {
    unchecked {
        return self.blockNumber() < targetBlock;
    }
}

// ── Global using ──

using {
    blockNumber,
    relativeTimeDelta,
    cumulativeGrowth,
    growthDelta,
    elapsedBlocks,
    isZero,
    gte,
    lt,
    blockNumberGte,
    blockNumberLt
} for GrowthObservation global;
