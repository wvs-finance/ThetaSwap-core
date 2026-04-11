// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {NoteId} from "core/src/types/NoteId.sol";
import {NoteSnapshot} from "core/src/types/NoteSnapshot.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {X128MathLib} from "../libraries/X128MathLib.sol";
import {FixedPointMathLib} from "solady/src/utils/FixedPointMathLib.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";

uint256 constant Q128 = 1 << 128;

struct AccrualManagerStorage {
    /// @notice Per-NoteId snapshot (set on first mint)
    mapping(NoteId => NoteSnapshot) snapshots;
    /// @notice Per-holder last-claimed growthInside (keyed on unwrapped NoteId)
    mapping(uint256 => mapping(address => uint256)) lastGrowthInside;
    /// @notice Per-holder last-claimed globalGrowth (keyed on unwrapped NoteId)
    mapping(uint256 => mapping(address => uint256)) lastGlobalGrowth;
    /// @notice LP revenue oracle adapter
    AngstromAccumulatorConsumer oracle;
}

/// @dev keccak256("accrualManager.angstrom")
bytes32 constant ACCRUAL_MANAGER_SLOT =
    0xe6f92ab924f4caafb6cbf13d069f296c17d7b6698effcf0636a7ee1eca05fa83;

function getAccrualManagerStorage() pure returns (AccrualManagerStorage storage $) {
    bytes32 pos = ACCRUAL_MANAGER_SLOT;
    assembly ("memory-safe") {
        $.slot := pos
    }
}

// ── Task 3.5: Birth concentration view ──

/// @notice Returns r₀ = entryGrowthInside / entryGlobalGrowth as Q128 fixed-point.
/// @dev Fee-weighted approximation of Pap (2022) Eq. 2.1 n/N at mint time.
///      Zero storage cost — computed on read via 512-bit intermediate (Solady fullMulDiv).
///      X128MathLib.flatDivX128 only takes uint128 numerator; accumulators are uint256,
///      so FixedPointMathLib.mulDiv is used for the full-range case.
function entryRatioQ128(NoteId id) view returns (uint256) {
    NoteSnapshot storage snap = getAccrualManagerStorage().snapshots[id];
    if (!snap.initialized || snap.entryGlobalGrowth == 0) return 0;
    return FixedPointMathLib.mulDiv(snap.entryGrowthInside, Q128, snap.entryGlobalGrowth);
}

// ── Free functions ──

error ZeroLiquidity();
error NoteNotInitialized();

/// @notice Snapshots accumulators on first mint for a NoteId, checkpoints per-holder state.
/// @dev Pure state update on AccrualManagerStorage. Does NOT mint ERC-1155 tokens —
///      the composing contract handles that via Compose ERC1155MintMod.
///      Oracle read from ran.sol keccak-slotted storage (not caller-supplied).
function updateSnapshotAndCheckpoint(
    NoteId id,
    PoolId poolId,
    uint128 liquidityUnits,
    address recipient
) {
    if (liquidityUnits == 0) revert ZeroLiquidity();
    id.validate();

    AngstromAccumulatorConsumer oracle = getAccrualManagerStorage().oracle;

    AccrualManagerStorage storage $ = getAccrualManagerStorage();
    NoteSnapshot storage snap = $.snapshots[id];

    if (!snap.initialized) {
        snap.entryGrowthInside = oracle.growthInside(poolId, id.tickLower(), id.tickUpper());
        snap.entryGlobalGrowth = oracle.globalGrowth(poolId);
        snap.initialized = true;
    }

    unchecked {
        snap.totalLiquidity += liquidityUnits;
    }

    uint256 tokenId = NoteId.unwrap(id);
    if ($.lastGrowthInside[tokenId][recipient] == 0 && snap.entryGrowthInside != 0) {
        $.lastGrowthInside[tokenId][recipient] = snap.entryGrowthInside;
        $.lastGlobalGrowth[tokenId][recipient] = snap.entryGlobalGrowth;
    }
}

/// @notice Settles accrued rewards for a holder and updates their checkpoint.
/// @dev Panoptic equivalent: _updateStoredPremia + _getPremiaDeltas.
///      Pure state update on AccrualManagerStorage. Does NOT transfer tokens —
///      the composing contract handles settlement.
///      holderBalance is injected by composing contract from ERC1155Storage.
///      V1a: single accumulator, no VEGOID spread. V1b adds premiumOwed/premiumGross split.
/// @return reward Accrued reward amount (Q128.128 → token units via fullMulX128)
function settleAndCheckpoint(NoteId id, PoolId poolId, address holder, uint256 holderBalance)
    returns (uint256 reward)
{
    AccrualManagerStorage storage $ = getAccrualManagerStorage();
    NoteSnapshot storage snap = $.snapshots[id];
    if (!snap.initialized) revert NoteNotInitialized();

    AngstromAccumulatorConsumer oracle = getAccrualManagerStorage().oracle;
    uint256 currentGI = oracle.growthInside(poolId, id.tickLower(), id.tickUpper());

    uint256 tokenId = NoteId.unwrap(id);
    uint256 lastGI = $.lastGrowthInside[tokenId][holder];

    uint256 giDelta;
    unchecked {
        giDelta = currentGI - lastGI;
    }

    if (giDelta == 0) return 0;

    // Update checkpoint
    $.lastGrowthInside[tokenId][holder] = currentGI;
    $.lastGlobalGrowth[tokenId][holder] = oracle.globalGrowth(poolId);

    // Angstrom pattern (PoolUpdates.sol:140): reward = (growthInsideDelta * liquidity) >> 128
    reward = X128MathLib.fullMulX128(giDelta, holderBalance);
}

/// @notice Returns the n/N ratio (Pap 2022 Eq. 2.1) for a NoteId as Q128.
/// @dev Panoptic equivalent: getAccountPremium (external view, ~line 1280).
///      Delta-over-delta: (currentGI - entryGI) / (currentGG - entryGG).
///      Read-only — no state changes.
function viewAccruedRatio(NoteId id, PoolId poolId) view returns (uint256 ratioQ128) {
    AccrualManagerStorage storage $ = getAccrualManagerStorage();
    NoteSnapshot storage snap = $.snapshots[id];
    if (!snap.initialized) return 0;

    AngstromAccumulatorConsumer oracle = getAccrualManagerStorage().oracle;
    uint256 currentGI = oracle.growthInside(poolId, id.tickLower(), id.tickUpper());
    uint256 currentGG = oracle.globalGrowth(poolId);

    uint256 giDelta;
    uint256 ggDelta;
    unchecked {
        giDelta = currentGI - snap.entryGrowthInside;
        ggDelta = currentGG - snap.entryGlobalGrowth;
    }

    if (ggDelta == 0) return 0;
    ratioQ128 = FixedPointMathLib.mulDiv(giDelta, Q128, ggDelta);
}
