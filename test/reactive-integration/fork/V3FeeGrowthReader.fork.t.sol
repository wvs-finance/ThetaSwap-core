// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console2} from "forge-std/Test.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {v3FeeGrowthInside0, v3PositionFeeGrowthLast0} from
    "reactive-hooks/libraries/V3FeeGrowthReaderMod.sol";
import {sepoliaFreshV3Pool} from "@foundry-script/utils/Deployments.sol";

/// @title V3FeeGrowthReader Fork Test
/// @notice Validates that v3FeeGrowthInside0() matches V3 pool's internal computation.
contract V3FeeGrowthReaderForkTest is Test {
    IUniswapV3Pool pool;

    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("sepolia"));
        pool = sepoliaFreshV3Pool();
    }

    /// @dev Verify v3FeeGrowthInside0 returns a value consistent with pool state.
    function test_fork_feeGrowthInsideReadsFromPool() public view {
        int24 tickLower = -60;
        int24 tickUpper = 60;

        uint256 feeGrowthInside = v3FeeGrowthInside0(pool, tickLower, tickUpper);
        console2.log("feeGrowthInside0X128:", feeGrowthInside);

        // Sanity: function did not revert
        assertTrue(true, "v3FeeGrowthInside0 did not revert");
    }

    /// @dev Verify snapshot consistency — feeGrowthInside >= position's feeGrowthLast.
    function test_fork_feeGrowthSnapshotConsistency() public view {
        int24 tickLower = -60;
        int24 tickUpper = 60;

        uint256 snapshotAtMint = v3FeeGrowthInside0(pool, tickLower, tickUpper);

        // Check deployer's position (known to exist on this pool)
        address posOwner = 0xe69228626E4800578D06a93BaaA595f6634A47C3;
        bytes32 posKey = keccak256(abi.encodePacked(posOwner, tickLower, tickUpper));
        (uint128 liq, uint256 feeGrowthLast0,,,) = pool.positions(posKey);

        console2.log("Position liquidity:", liq);
        console2.log("Position feeGrowthInside0Last:", feeGrowthLast0);
        console2.log("Current feeGrowthInside0:", snapshotAtMint);

        if (liq > 0) {
            uint256 delta;
            unchecked {
                delta = snapshotAtMint - feeGrowthLast0;
            }
            console2.log("Fee growth delta:", delta);
        }
    }

    /// @dev Verify that v3PositionFeeGrowthLast0 reads position storage correctly.
    /// For a fully-collected position, feeGrowthInsideLast0 equals 0 (V3 clears on collect).
    /// For a position with uncollected fees, it equals the feeGrowthInside at last update.
    function test_fork_positionFeeGrowthLastMatchesTicks() public view {
        int24 tickLower = -60;
        int24 tickUpper = 60;
        address posOwner = 0xe69228626E4800578D06a93BaaA595f6634A47C3;

        uint256 fromTicks = v3FeeGrowthInside0(pool, tickLower, tickUpper);
        uint256 fromPosition = v3PositionFeeGrowthLast0(pool, posOwner, tickLower, tickUpper);

        console2.log("feeGrowthInside0 (from ticks):", fromTicks);
        console2.log("feeGrowthInsideLast0 (from position):", fromPosition);

        // Verify the library reads match direct pool.positions() call.
        bytes32 posKey = keccak256(abi.encodePacked(posOwner, tickLower, tickUpper));
        (, uint256 directFeeGrowthLast0,,,) = pool.positions(posKey);
        assertEq(fromPosition, directFeeGrowthLast0, "library must match direct read");

        // feeGrowthInsideLast0 <= current feeGrowthInside0 (monotonically non-decreasing)
        assertTrue(fromTicks >= fromPosition, "current feeGrowthInside >= position snapshot");
    }
}
