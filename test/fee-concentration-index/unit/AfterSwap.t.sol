// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Deployers} from "v4-core/test/utils/Deployers.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";

import {FeeConcentrationIndexHarness} from "../harness/FeeConcentrationIndexHarness.sol";
import {MockPositionManager} from "../harness/MockPositionManager.sol";

contract AfterSwapTest is Test, Deployers {
    FeeConcentrationIndexHarness harness;
    PoolKey poolKey;
    PoolId poolId;

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();

        MockPositionManager mockPosm = new MockPositionManager(manager);

        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );

        bytes memory constructorArgs = abi.encode(address(mockPosm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this),
            flags,
            type(FeeConcentrationIndexHarness).creationCode,
            constructorArgs
        );

        harness = new FeeConcentrationIndexHarness{salt: salt}(IPositionManager(address(mockPosm)));
        require(address(harness) == hookAddress, "hook address mismatch");

        (poolKey,) = initPool(
            currency0,
            currency1,
            IHooks(address(harness)),
            3000,
            SQRT_PRICE_1_1
        );
        poolId = PoolIdLibrary.toId(poolKey);
    }

    // ── helpers ──

    function _addLiquidity(int24 tickLower, int24 tickUpper, int256 liquidityDelta) internal {
        modifyLiquidityRouter.modifyLiquidity(
            poolKey,
            ModifyLiquidityParams({
                tickLower: tickLower,
                tickUpper: tickUpper,
                liquidityDelta: liquidityDelta,
                salt: bytes32(0)
            }),
            ""
        );
    }

    function _swap(bool zeroForOne, int256 amountSpecified) internal returns (BalanceDelta) {
        return swap(poolKey, zeroForOne, amountSpecified, "");
    }

    // ── INV-001: Swap Count Monotonicity ──

    function test_INV001_swapCountMonotonic() public {
        _addLiquidity(-60, 60, 1e18);

        _swap(true, -100);
        assertEq(harness.getRangeSwapCount(poolId, -60, 60), 1, "after 1st swap");

        _swap(true, -100);
        assertEq(harness.getRangeSwapCount(poolId, -60, 60), 2, "after 2nd swap");

        _swap(false, -100);
        assertEq(harness.getRangeSwapCount(poolId, -60, 60), 3, "after 3rd swap");
    }

    // ── INV-003: Only overlapping range incremented ──

    function test_INV003_onlyOverlappingRangeIncremented() public {
        _addLiquidity(-60, 60, 1e18);
        _addLiquidity(60000, 60060, 1e18);

        _swap(true, -100);

        assertEq(harness.getRangeSwapCount(poolId, -60, 60), 1, "near range incremented");
        assertEq(harness.getRangeSwapCount(poolId, 60000, 60060), 0, "far range untouched");
    }

    function test_INV003_rangeOutsideSwapPathUntouched() public {
        _addLiquidity(-60060, -60000, 1e18);
        _addLiquidity(-60, 60, 1e18);
        _addLiquidity(60000, 60060, 1e18);

        _swap(true, -100);

        assertEq(harness.getRangeSwapCount(poolId, -60, 60), 1, "active range incremented");
        assertEq(harness.getRangeSwapCount(poolId, -60060, -60000), 0, "below range untouched");
        assertEq(harness.getRangeSwapCount(poolId, 60000, 60060), 0, "above range untouched");
    }

    // ── Accumulation ──

    function test_swapCountAccumulatesAcrossSwaps() public {
        _addLiquidity(-60, 60, 1e18);

        uint256 N = 5;
        for (uint256 i; i < N; ++i) {
            _swap(true, -100);
        }

        assertEq(harness.getRangeSwapCount(poolId, -60, 60), N, "count == N");
    }

    // ── Active range count ──

    function test_activeRangeCountTracksRegistration() public {
        assertEq(harness.getActiveRangeCount(poolId), 0, "starts at 0");

        _addLiquidity(-60, 60, 1e18);
        assertEq(harness.getActiveRangeCount(poolId), 1, "after 1st range");

        _addLiquidity(-120, 120, 1e18);
        assertEq(harness.getActiveRangeCount(poolId), 2, "after 2nd range");

        // Second position in same range doesn't increase count
        _addLiquidity(-60, 60, 1e18);
        assertEq(harness.getActiveRangeCount(poolId), 2, "duplicate range same count");
    }

    // ── Edge case: no active ranges ──

    function test_noActiveRanges_swapIsNoOp() public {
        assertEq(harness.getActiveRangeCount(poolId), 0, "no active ranges initially");
    }

    // ── Fuzz: T019 — swap count monotonic ──

    function testFuzz_swapCount_monotonic(uint8 swapCount) public {
        vm.assume(swapCount > 0 && swapCount <= 20);
        _addLiquidity(-60, 60, 1e18);

        uint32 prev = 0;
        for (uint8 i; i < swapCount; ++i) {
            _swap(true, -100);
            uint32 current = harness.getRangeSwapCount(poolId, -60, 60);
            assertGe(current, prev, "T019: swap count must be monotonic");
            prev = current;
        }
    }

    // ── Fuzz: T021 — only active range incremented ──

    function testFuzz_only_active_range_incremented(int256 amount) public {
        vm.assume(amount >= 10 && amount <= 1e18);
        _addLiquidity(-60, 60, 1e18);
        _addLiquidity(60000, 60060, 1e18);

        _swap(true, -amount);

        assertGe(harness.getRangeSwapCount(poolId, -60, 60), 1, "T021: near range incremented");
        assertEq(harness.getRangeSwapCount(poolId, 60000, 60060), 0, "T021: far range untouched");
    }
}
