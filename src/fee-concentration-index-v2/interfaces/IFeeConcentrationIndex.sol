// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IERC165} from "forge-std/interfaces/IERC165.sol";

interface IHookFacet {
    error HookFacet__NotValidHook();
}

interface IFeeConcentrationIndex is IERC165, IHookFacet {
    /// @notice Returns the co-primary state triple for the pool's FCI.
    /// @param key The pool key.
    /// @param reactive If true, reads from reactive storage; false for local.
    /// @return indexA A_T = sqrt(accumulatedSum), Q128-scaled, capped at INDEX_ONE.
    /// @return thetaSum Θ = Σ(1/ℓ_k), Q128-scaled, cumulative over removals.
    /// @return removedPosCount N = number of positions that contributed terms.
    function getIndex(PoolKey calldata key, bool reactive)
        external
        view
        returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount);

    /// @notice Returns Δ⁺ = max(0, A_T - atNull) for the pool, Q128-scaled.
    /// @dev Derived on the fly from stored co-primary state.
    function getDeltaPlus(PoolKey calldata key, bool reactive)
        external
        view
        returns (uint128 deltaPlus_);

    /// @notice Returns the competitive null atNull = sqrt(Θ/N²), Q128-scaled.
    function getAtNull(PoolKey calldata key, bool reactive)
        external
        view
        returns (uint128 atNull_);

    /// @notice Returns Θ = Σ(1/ℓ_k), Q128-scaled, cumulative over removals.
    function getThetaSum(PoolKey calldata key, bool reactive)
        external
        view
        returns (uint256 thetaSum_);

    /// @notice Returns epoch-reset Δ⁺ for the pool, Q128-scaled.
    /// @dev Accumulators reset each epoch (destruction by abandonment).
    /// Returns current epoch's Δ⁺, or 0 if epoch expired with no new data.
    function getDeltaPlusEpoch(PoolKey calldata key, bool reactive)
        external
        view
        returns (uint128 deltaPlus_);

    /// @notice Initialize epoch metric for a pool.
    function initializeEpochPool(PoolKey calldata key, uint256 epochLengthSeconds) external;
}
