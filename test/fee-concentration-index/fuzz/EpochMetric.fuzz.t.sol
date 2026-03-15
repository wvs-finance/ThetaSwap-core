// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/types/FeeConcentrationStateMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {
    FeeConcentrationEpochStorage,
    epochFciStorage,
    addEpochTerm,
    epochDeltaPlus,
    initializeEpoch
} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";

contract EpochMetricFuzzTest is Test {
    uint256 constant Q128 = 1 << 128;
    uint256 constant EPOCH_1D = 86400;
    PoolId constant POOL = PoolId.wrap(bytes32(uint256(1)));

    function setUp() public {
        vm.warp(1000);
        initializeEpoch(POOL, EPOCH_1D);
    }

    /// @dev INV-E1: epochDeltaPlus does not revert and reads are idempotent.
    function testFuzz_deltaPlusNoRevertIdempotent(
        uint256 xSqQ128,
        uint256 blockLifetime,
        uint8 count
    ) public {
        blockLifetime = bound(blockLifetime, 1, 1e9);
        xSqQ128 = bound(xSqQ128, 0, Q128 - 1);
        count = uint8(bound(count, 1, 20));

        vm.warp(1500);
        for (uint256 i; i < count; i++) {
            addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);
        }
        uint128 dp1 = epochDeltaPlus(POOL);
        uint128 dp2 = epochDeltaPlus(POOL);
        assertEq(dp1, dp2, "reads must be idempotent");
    }

    /// @dev INV-E2: Expired epoch with no new data returns 0.
    function testFuzz_expiredEpochReturnsZero(uint256 xSqQ128, uint256 blockLifetime) public {
        blockLifetime = bound(blockLifetime, 1, 1e9);
        xSqQ128 = bound(xSqQ128, 1, Q128 - 1);

        vm.warp(1500);
        addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);

        vm.warp(1000 + EPOCH_1D + 1);
        assertEq(epochDeltaPlus(POOL), 0);
    }

    /// @dev INV-E3: Equal shares with same blocklife → Δ⁺ = 0.
    function testFuzz_equalSharesZeroDelta(uint256 blockLifetime, uint8 n) public {
        blockLifetime = bound(blockLifetime, 1, 1e6);
        n = uint8(bound(n, 2, 20));

        uint256 xSqQ128 = Q128 / (uint256(n) * uint256(n));

        vm.warp(1500);
        for (uint256 i; i < n; i++) {
            addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);
        }
        assertEq(epochDeltaPlus(POOL), 0);
    }

    /// @dev INV-E4: New epoch starts with fresh state.
    function testFuzz_newEpochFreshState(uint256 xSqQ128, uint256 blockLifetime) public {
        blockLifetime = bound(blockLifetime, 1, 1e9);
        xSqQ128 = bound(xSqQ128, 1, Q128 - 1);

        // Add in first epoch
        vm.warp(1500);
        addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);

        // Advance to new epoch
        vm.warp(1000 + EPOCH_1D + 500);
        // Only add one term in new epoch
        addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);

        FeeConcentrationEpochStorage storage $ = epochFciStorage();
        uint256 newEpochId = $.currentEpochId[POOL];
        // New epoch should have exactly 1 position
        assertEq($.epochStates[POOL][newEpochId].removedPosCount, 1);
    }

    /// @dev INV-E5: Exact epoch boundary triggers expiry.
    function testFuzz_exactBoundaryTriggersExpiry(uint256 xSqQ128, uint256 blockLifetime) public {
        blockLifetime = bound(blockLifetime, 1, 1e9);
        xSqQ128 = bound(xSqQ128, 1, Q128 - 1);

        vm.warp(1500);
        // Need 2 terms with different shares for Δ⁺ > 0
        addEpochTerm(POOL, BlockCount.wrap(1), (Q128 * 81) / 100);
        addEpochTerm(POOL, BlockCount.wrap(10000), Q128 / 100);

        // Warp to EXACT boundary: epochStart(1000) + epochLen(86400) = 87400
        vm.warp(1000 + EPOCH_1D);
        // View should return 0 (>= triggers expiry check)
        assertEq(epochDeltaPlus(POOL), 0, "exact boundary should trigger expiry");
    }
}
