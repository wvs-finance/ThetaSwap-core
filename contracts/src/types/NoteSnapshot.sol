// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

/// @notice Per-NoteId storage for range accrual note lifecycle.
/// @dev Accumulators are uint256 in Q128.128 (Angstrom native format via X128MathLib).
///      epochId is NOT stored here — it lives in NoteId bits 130–169 (bit-packed design).
///      The birth concentration ratio r₀ = entryGrowthInside / entryGlobalGrowth is exposed
///      as a pure view (Approach C) rather than a stored field (zero storage cost).
struct NoteSnapshot {
    /// @notice growthInside at mint time, single-asset (asset0), Q128.128
    uint256 entryGrowthInside;
    /// @notice globalGrowth at mint time, Q128.128 — needed for n/N delta computation
    uint256 entryGlobalGrowth;
    /// @notice Sum of all liquidityUnits minted under this NoteId
    uint128 totalLiquidity;
    /// @notice False until first mint for this NoteId
    bool initialized;
}
    
