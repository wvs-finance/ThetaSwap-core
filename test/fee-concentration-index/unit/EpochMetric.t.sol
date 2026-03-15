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

contract EpochMetricTest is Test {
    uint256 constant Q128 = 1 << 128;
    uint256 constant EPOCH_1D = 86400;

    PoolId constant POOL = PoolId.wrap(bytes32(uint256(1)));

    function setUp() public {
        vm.warp(1000);
        initializeEpoch(POOL, EPOCH_1D);
    }

    function test_initializeEpoch() public view {
        FeeConcentrationEpochStorage storage $ = epochFciStorage();
        assertEq($.epochLength[POOL], EPOCH_1D);
        assertEq($.currentEpochId[POOL], 1000);
    }

    function test_addTerm_incrementsState() public {
        uint256 xSqQ128 = Q128 / 4; // x_k² = 0.25
        BlockCount bl = BlockCount.wrap(100);

        vm.warp(1500);
        addEpochTerm(POOL, bl, xSqQ128);

        FeeConcentrationEpochStorage storage $ = epochFciStorage();
        FeeConcentrationState storage state = $.epochStates[POOL][1000];
        assertEq(state.removedPosCount, 1);
        assertGt(state.accumulatedSum, 0);
        assertGt(state.thetaSum, 0);
    }

    function test_deltaPlus_zeroWhenEmpty() public view {
        assertEq(epochDeltaPlus(POOL), 0);
    }

    function test_epochExpiry_returnsZero() public {
        // Need 2+ terms with different fee shares to get Δ⁺ > 0
        uint256 xSqJit = (Q128 * 81) / 100;   // JIT: x²=0.81
        uint256 xSqPassive = Q128 / 100;        // Passive: x²=0.01

        vm.warp(1500);
        addEpochTerm(POOL, BlockCount.wrap(1), xSqJit);
        addEpochTerm(POOL, BlockCount.wrap(10000), xSqPassive);
        assertGt(epochDeltaPlus(POOL), 0);

        // Advance past epoch boundary — no new data in new epoch
        vm.warp(1000 + EPOCH_1D + 1);
        assertEq(epochDeltaPlus(POOL), 0, "Expired epoch with no new data should return 0");
    }

    function test_epochAdvance_abandonsOldState() public {
        uint256 xSqQ128 = Q128 / 4;
        BlockCount bl = BlockCount.wrap(100);

        // Add term in first epoch
        vm.warp(1500);
        addEpochTerm(POOL, bl, xSqQ128);

        // Advance past epoch and add term — new epoch starts
        vm.warp(1000 + EPOCH_1D + 500);
        addEpochTerm(POOL, bl, xSqQ128);

        FeeConcentrationEpochStorage storage $ = epochFciStorage();
        // Old epoch state still has data (abandoned, not deleted)
        assertEq($.epochStates[POOL][1000].removedPosCount, 1);
        // New epoch ID is the new timestamp
        uint256 newEpochId = $.currentEpochId[POOL];
        assertEq(newEpochId, 1000 + EPOCH_1D + 500);
        // New epoch state has only the new term
        assertEq($.epochStates[POOL][newEpochId].removedPosCount, 1);
    }

    function test_uninitializedPool_silentlySkips() public {
        PoolId otherPool = PoolId.wrap(bytes32(uint256(999)));
        // epochLength == 0 for uninitialized pool
        vm.warp(1500);
        addEpochTerm(otherPool, BlockCount.wrap(100), Q128 / 4);
        // Should not revert, deltaPlus returns 0
        assertEq(epochDeltaPlus(otherPool), 0);
    }

    function test_deltaPlus_concentrated() public {
        // JIT: x_k²=0.81, bl=1
        uint256 xSq1 = (Q128 * 81) / 100;
        BlockCount bl1 = BlockCount.wrap(1);
        // Passive: x_k²=0.01, bl=10000
        uint256 xSq2 = Q128 / 100;
        BlockCount bl2 = BlockCount.wrap(10000);

        vm.warp(1500);
        addEpochTerm(POOL, bl1, xSq1);
        addEpochTerm(POOL, bl2, xSq2);

        assertGt(epochDeltaPlus(POOL), 0, "Concentrated positions should produce positive delta-plus");
    }
}
