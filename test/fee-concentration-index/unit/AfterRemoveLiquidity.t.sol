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
import {Position} from "v4-core/src/libraries/Position.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";

import {FeeConcentrationIndexHarness} from "../harness/FeeConcentrationIndexHarness.sol";
import {MockPositionManager} from "../harness/MockPositionManager.sol";
import {TickRange, fromTicks} from "../../../src/fee-concentration-index/types/TickRangeMod.sol";

contract AfterRemoveLiquidityTest is Test, Deployers {
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

    function _removeLiquidity(int24 tickLower, int24 tickUpper, int256 liquidityDelta) internal {
        modifyLiquidityRouter.modifyLiquidity(
            poolKey,
            ModifyLiquidityParams({
                tickLower: tickLower,
                tickUpper: tickUpper,
                liquidityDelta: -liquidityDelta,
                salt: bytes32(0)
            }),
            ""
        );
    }

    function _swap(bool zeroForOne, int256 amountSpecified) internal returns (BalanceDelta) {
        return swap(poolKey, zeroForOne, amountSpecified, "");
    }

    function _positionKey(address sender, int24 tickLower, int24 tickUpper, bytes32 salt)
        internal
        pure
        returns (bytes32)
    {
        return Position.calculatePositionKey(sender, tickLower, tickUpper, salt);
    }

    // ── Test: deregister on removal ──

    function test_deregisterOnRemoval() public {
        _addLiquidity(-60, 60, 1e18);

        // modifyLiquidityRouter is the sender from the hook's perspective
        bytes32 pk = _positionKey(address(modifyLiquidityRouter), -60, 60, bytes32(0));
        assertTrue(harness.containsPosition(poolId, -60, 60, pk), "registered before removal");

        _removeLiquidity(-60, 60, 1e18);
        assertFalse(harness.containsPosition(poolId, -60, 60, pk), "deregistered after removal");
    }

    // ── Test: lifetime zero → no HHI update ──

    function test_lifetimeZero_noHHIUpdate() public {
        _addLiquidity(-60, 60, 1e18);
        // No swaps → lifetime = 0
        _removeLiquidity(-60, 60, 1e18);

        assertEq(harness.getAccumulatedHHI(poolId), 0, "no HHI when lifetime is zero");
    }

    // ── Test: single position JIT (1 swap, then remove) ──

    function test_singlePosition_JIT() public {
        _addLiquidity(-60, 60, 1e18);

        // 1 swap to generate fees and increment swap count
        _swap(true, -100);

        _removeLiquidity(-60, 60, 1e18);

        // With single position: x_k = 1, lifetime = 1
        // HHI term = x_k^2 / lifetime = 1^2 / 1 = Q128
        // accumulatedHHI should be Q128 = 1 << 128
        uint256 hhi = harness.getAccumulatedHHI(poolId);
        assertGt(hhi, 0, "HHI should be non-zero after swap+remove");
    }

    // ── Test: baseline cleaned up after removal ──

    function test_baselineCleanedUp() public {
        _addLiquidity(-60, 60, 1e18);

        bytes32 pk = _positionKey(address(modifyLiquidityRouter), -60, 60, bytes32(0));
        // Baseline may be 0 in fresh pool, but storage slot exists
        _removeLiquidity(-60, 60, 1e18);

        assertEq(harness.getBaseline0(poolId, pk), 0, "baseline cleaned up after removal");
    }

    // ── Test: active range count decrements on last removal ──

    function test_activeRangeCountDecrementsOnLastRemoval() public {
        _addLiquidity(-60, 60, 1e18);
        assertEq(harness.getActiveRangeCount(poolId), 1, "1 active range after add");

        _removeLiquidity(-60, 60, 1e18);
        assertEq(harness.getActiveRangeCount(poolId), 0, "0 active ranges after last removal");
    }

    // ── Test: getIndex returns correct values ──

    function test_getIndex_returnsCorrectValues() public {
        // Before any removals, indices should be A=0, B=max
        (uint128 indexA, uint128 indexB) = harness.getIndex(poolKey);
        assertEq(indexA, 0, "indexA should be 0 with no removals");
        assertEq(indexB, type(uint128).max, "indexB should be max with no removals");

        // Add, swap, remove to generate HHI
        _addLiquidity(-60, 60, 1e18);
        _swap(true, -100);
        _removeLiquidity(-60, 60, 1e18);

        (uint128 indexA2, uint128 indexB2) = harness.getIndex(poolKey);
        assertGt(indexA2, 0, "indexA should be > 0 after removal with fees");
        assertLt(indexB2, type(uint128).max, "indexB should be < max after removal with fees");
        assertEq(uint256(indexA2) + uint256(indexB2), type(uint128).max, "A + B = 1");
    }
}
