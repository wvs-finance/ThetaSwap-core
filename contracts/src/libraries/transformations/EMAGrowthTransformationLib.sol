// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {CircularBuffer} from "openzeppelin-contracts/utils/structs/CircularBuffer.sol";
import {OraclePack, OraclePackLibrary} from "panoptic-v2/src/types/OraclePack.sol";
import {GrowthObservation} from "core/src/types/GrowthObservation.sol";
import {
    latestObservation,
    oldestObservation,
    observationCount
} from "core/src/libraries/BlockNumberAwareGrowthObserverLib.sol";
import {growthToTick} from "core/src/libraries/GrowthToTickLib.sol";

// ── Errors ──

error InsufficientObservations();

// ── Free functions ──

/// @notice Converts raw cumulative growth observations into an EMA-smoothed OraclePack.
/// @dev Layer 2 transformation: composes Layer 1 observation primitives, GrowthToTickLib,
///      and OraclePack into a single update step. Maps to extensionFlag = CALLABLE (4).
///
///      Pipeline:
///      1. Short-circuit if current epoch == OraclePack epoch (same-epoch no-op)
///      2. Read oldest + latest observations from the ring buffer
///      3. Convert cumulative growth ratio to tick via GrowthToTickLib
///      4. Clamp tick to prevent manipulation spikes
///      5. Feed clamped tick into OraclePack.insertObservation (updates EMAs + median)
///
///      Does NOT write to storage. The caller persists the returned OraclePack.
///
/// @param buffer The per-pool observation ring buffer (Layer 1 storage)
/// @param currentOraclePack The current packed oracle state (4 EMAs + 8-slot median queue)
/// @param EMAperiods Packed uint96: four uint24 periods (spot, fast, slow, eons)
/// @param clampDelta Maximum tick change per update (manipulation resistance)
/// @return The updated OraclePack (or unchanged if same-epoch)
function updateGrowthEMA(
    CircularBuffer.Bytes32CircularBuffer storage buffer,
    OraclePack currentOraclePack,
    uint96 EMAperiods,
    int24 clampDelta
) view returns (OraclePack) {
    // ── Step 1: Epoch check (same-epoch fast path) ──
    uint24 currentEpoch = uint24((block.timestamp >> 6) & 0xFFFFFF);
    if (currentEpoch == currentOraclePack.epoch()) return currentOraclePack;

    // ── Step 2: Buffer precondition ──
    uint256 count = observationCount(buffer);
    if (count < 2) revert InsufficientObservations();

    // ── Step 3: Read anchor and latest observations ──
    GrowthObservation oldest = oldestObservation(buffer);
    GrowthObservation latest = latestObservation(buffer);

    // ── Step 4: Growth ratio → tick ──
    int24 growthTick = growthToTick(latest.cumulativeGrowth(), oldest.cumulativeGrowth());

    // ── Step 5: Clamp ──
    int24 clampedTick = OraclePackLibrary.clampTick(growthTick, currentOraclePack, clampDelta);

    // ── Step 6: Time delta (epochs × 64 seconds) ──
    // unchecked: uint24 subtraction must wrap on 24-bit epoch counter rollover (~34 years)
    int256 timeDelta;
    unchecked {
        timeDelta = int256(uint256(uint24(currentEpoch - currentOraclePack.epoch()))) * 64;
    }

    // ── Step 7: Feed into OraclePack ──
    return
        currentOraclePack.insertObservation(
            clampedTick, uint256(currentEpoch), timeDelta, EMAperiods
        );
}
