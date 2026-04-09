// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {CircularBuffer} from "openzeppelin-contracts/utils/structs/CircularBuffer.sol";
import {SafeCastLib} from "solady/src/utils/SafeCastLib.sol";
import {GrowthObservation, newGrowthObservation} from "../types/GrowthObservation.sol";

// ── Errors ──

error EmptyBuffer();
error ObservationExpired(uint32 targetBlock, uint32 oldestBlock);

// ── Free functions ──

/// @notice Records a new observation into the ring buffer.
/// @dev Skips if the latest observation has a block number >= `_blockNumber`.
///      This enforces strict monotonicity: only observations with a strictly higher
///      block number than the latest are accepted. Same-block duplicates and stale /
///      out-of-order block numbers are silently skipped (no revert) to remain
///      idempotent for keeper retries.
///
///      IMPORTANT: The caller MUST call `CircularBuffer.setup(buffer, N)` before
///      first use — an uninitialized buffer will panic on `push()`.
///
///      Design note (M-01): Same-block observations are skipped rather than
///      overwritten because `recordObservation()` on the adapter is access-controlled
///      to a trusted keeper, eliminating the frontrunning vector.
function record(
    CircularBuffer.Bytes32CircularBuffer storage buffer,
    uint256 _blockNumber,
    uint256 _relativeTimeDelta,
    uint256 _cumulativeGrowth
) {
    uint256 total = CircularBuffer.count(buffer);
    if (total > 0) {
        GrowthObservation latest = GrowthObservation.wrap(CircularBuffer.last(buffer, 0));
        // Skip if same block OR stale block — only strictly newer blocks are recorded.
        if (latest.blockNumber() >= SafeCastLib.toUint32(_blockNumber)) return;
    }
    CircularBuffer.push(
        buffer,
        GrowthObservation.unwrap(newGrowthObservation(_blockNumber, _relativeTimeDelta, _cumulativeGrowth))
    );
}

// ── Convenience wrappers ──

/// @notice Returns the most recent observation in the buffer.
/// @dev Reverts with `EmptyBuffer` if no observations have been recorded.
function latestObservation(
    CircularBuffer.Bytes32CircularBuffer storage buffer
) view returns (GrowthObservation) {
    if (CircularBuffer.count(buffer) == 0) revert EmptyBuffer();
    return GrowthObservation.wrap(CircularBuffer.last(buffer, 0));
}

/// @notice Returns the oldest observation still in the buffer.
/// @dev Reverts with `EmptyBuffer` if no observations have been recorded.
function oldestObservation(
    CircularBuffer.Bytes32CircularBuffer storage buffer
) view returns (GrowthObservation) {
    uint256 total = CircularBuffer.count(buffer);
    if (total == 0) revert EmptyBuffer();
    return GrowthObservation.wrap(CircularBuffer.last(buffer, total - 1));
}

/// @notice Returns the number of observations currently stored in the buffer.
function observationCount(
    CircularBuffer.Bytes32CircularBuffer storage buffer
) view returns (uint256) {
    return CircularBuffer.count(buffer);
}

/// @notice Returns the observation at or before `targetBlock`.
/// @dev Binary search over the descending-block-number ring buffer.
///      Reverts if the buffer is empty or if targetBlock is older than the oldest observation.
function observeAt(
    CircularBuffer.Bytes32CircularBuffer storage buffer,
    uint32 targetBlock
) view returns (GrowthObservation) {
    uint256 total = CircularBuffer.count(buffer);
    if (total == 0) revert EmptyBuffer();

    GrowthObservation newest = GrowthObservation.wrap(CircularBuffer.last(buffer, 0));
    if (newest.blockNumber() <= targetBlock) return newest;

    GrowthObservation oldest = GrowthObservation.wrap(CircularBuffer.last(buffer, total - 1));
    if (oldest.blockNumber() > targetBlock) {
        revert ObservationExpired(targetBlock, oldest.blockNumber());
    }

    // Binary search: find smallest i such that last(i).blockNumber() <= targetBlock.
    // last(0) is newest (highest block), last(total-1) is oldest (lowest block).
    uint256 low = 1;
    uint256 high = total - 1;

    while (low < high) {
        uint256 mid = (low + high) / 2;
        GrowthObservation obs = GrowthObservation.wrap(CircularBuffer.last(buffer, mid));
        if (obs.blockNumber() > targetBlock) {
            low = mid + 1;
        } else {
            high = mid;
        }
    }

    return GrowthObservation.wrap(CircularBuffer.last(buffer, low));
}
