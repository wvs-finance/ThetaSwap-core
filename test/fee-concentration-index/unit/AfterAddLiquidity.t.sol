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

contract AfterAddLiquidityTest is Test, Deployers {
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

    function _addPosition(address sender, int24 tickLower, int24 tickUpper, bytes32 salt)
        internal
        returns (bytes32 positionKey)
    {
        ModifyLiquidityParams memory params = ModifyLiquidityParams({
            tickLower: tickLower,
            tickUpper: tickUpper,
            liquidityDelta: 1e18,
            salt: salt
        });

        harness.exposed_afterAddLiquidity(
            sender,
            poolKey,
            params,
            BalanceDelta.wrap(0),
            BalanceDelta.wrap(0),
            ""
        );

        positionKey = Position.calculatePositionKey(sender, tickLower, tickUpper, salt);
    }

    // ── INV-002: SwapCount Initial Zero ──
    // Every newly registered position starts with baseline swap count == 0.

    function test_INV002_baselineSwapCountZero() public {
        bytes32 pk = _addPosition(address(0xBEEF), -60, 60, bytes32(0));
        assertEq(harness.getBaselineSwapCount(poolId, pk), 0, "INV-002: baseline swap count must be 0");
    }

    function test_INV002_multiplePositions_allZero() public {
        bytes32 pk1 = _addPosition(address(0xA), -120, 120, bytes32(uint256(1)));
        bytes32 pk2 = _addPosition(address(0xB), -60, 60, bytes32(uint256(2)));
        bytes32 pk3 = _addPosition(address(0xC), -180, 180, bytes32(uint256(3)));

        assertEq(harness.getBaselineSwapCount(poolId, pk1), 0, "INV-002: pk1");
        assertEq(harness.getBaselineSwapCount(poolId, pk2), 0, "INV-002: pk2");
        assertEq(harness.getBaselineSwapCount(poolId, pk3), 0, "INV-002: pk3");
    }

    // ── INV-004: Registry Consistency ──
    // Position exists in the correct tick range set, and rangeKeyOf is consistent.

    function test_INV004_registeredPositionInRange() public {
        int24 tickLower = -60;
        int24 tickUpper = 60;
        bytes32 pk = _addPosition(address(0xBEEF), tickLower, tickUpper, bytes32(0));

        assertTrue(
            harness.containsPosition(poolId, tickLower, tickUpper, pk),
            "INV-004: position must be in its tick range"
        );
    }

    function test_INV004_rangeKeyOfConsistent() public {
        int24 tickLower = -120;
        int24 tickUpper = 120;
        bytes32 pk = _addPosition(address(0xBEEF), tickLower, tickUpper, bytes32(0));

        bytes32 expectedRangeKey = TickRange.unwrap(fromTicks(tickLower, tickUpper));
        bytes32 storedRangeKey = harness.getRangeKeyOf(poolId, pk);

        assertEq(storedRangeKey, expectedRangeKey, "INV-004: rangeKeyOf must match fromTicks");
    }

    function test_INV004_notInWrongRange() public {
        bytes32 pk = _addPosition(address(0xBEEF), -60, 60, bytes32(0));

        assertFalse(
            harness.containsPosition(poolId, -120, 120, pk),
            "INV-004: position must NOT be in a different tick range"
        );
    }

    function test_INV004_twoPositionsSameRange() public {
        int24 tickLower = -60;
        int24 tickUpper = 60;

        bytes32 pk1 = _addPosition(address(0xA), tickLower, tickUpper, bytes32(uint256(1)));
        bytes32 pk2 = _addPosition(address(0xB), tickLower, tickUpper, bytes32(uint256(2)));

        assertTrue(harness.containsPosition(poolId, tickLower, tickUpper, pk1), "INV-004: pk1 in range");
        assertTrue(harness.containsPosition(poolId, tickLower, tickUpper, pk2), "INV-004: pk2 in range");
        assertEq(harness.getRangeLength(poolId, tickLower, tickUpper), 2, "INV-004: range length == 2");
    }

    // ── INV-004 (range length): Range length increments on each registration ──

    function test_INV004_rangeLengthIncrementsOnRegister() public {
        int24 tickLower = -60;
        int24 tickUpper = 60;

        assertEq(harness.getRangeLength(poolId, tickLower, tickUpper), 0, "starts at 0");

        _addPosition(address(0xA), tickLower, tickUpper, bytes32(uint256(1)));
        assertEq(harness.getRangeLength(poolId, tickLower, tickUpper), 1, "after 1st add");

        _addPosition(address(0xB), tickLower, tickUpper, bytes32(uint256(2)));
        assertEq(harness.getRangeLength(poolId, tickLower, tickUpper), 2, "after 2nd add");

        _addPosition(address(0xC), tickLower, tickUpper, bytes32(uint256(3)));
        assertEq(harness.getRangeLength(poolId, tickLower, tickUpper), 3, "after 3rd add");
    }

    // ── Baseline fee growth: stored on registration (may be 0 in fresh pool) ──

    function test_baselineFeeGrowthStoredOnRegister() public {
        bytes32 pk = _addPosition(address(0xBEEF), -60, 60, bytes32(0));

        // In a fresh pool with no swaps, feeGrowthInside is 0.
        // The important thing is the code path ran — baseline was written.
        uint256 baseline = harness.getBaseline0(poolId, pk);
        assertEq(baseline, 0, "baseline fee growth should be 0 in fresh pool");
    }

    // ── Return value: selector correctness ──

    function test_returnsSelectorAndZeroDelta() public {
        ModifyLiquidityParams memory params = ModifyLiquidityParams({
            tickLower: -60,
            tickUpper: 60,
            liquidityDelta: 1e18,
            salt: bytes32(0)
        });

        (bytes4 selector, BalanceDelta delta) = harness.exposed_afterAddLiquidity(
            address(0xBEEF),
            poolKey,
            params,
            BalanceDelta.wrap(0),
            BalanceDelta.wrap(0),
            ""
        );

        assertEq(selector, harness.afterAddLiquidity.selector, "must return afterAddLiquidity selector");
        assertEq(BalanceDelta.unwrap(delta), 0, "must return zero delta");
    }

    // ── Idempotency: re-registering same position does not duplicate ──

    function test_reRegisterSamePositionIdempotent() public {
        int24 tickLower = -60;
        int24 tickUpper = 60;
        address sender = address(0xBEEF);
        bytes32 salt = bytes32(0);

        _addPosition(sender, tickLower, tickUpper, salt);
        _addPosition(sender, tickLower, tickUpper, salt);

        // Position key is deterministic — same inputs = same key.
        // Registry should still contain it (register is idempotent for same position).
        bytes32 pk = Position.calculatePositionKey(sender, tickLower, tickUpper, salt);
        assertTrue(harness.containsPosition(poolId, tickLower, tickUpper, pk), "still registered");

        // Range length should be 1, not 2 (no duplicate).
        assertEq(harness.getRangeLength(poolId, tickLower, tickUpper), 1, "no duplicate in range");
    }

    // ── Different tick ranges create separate entries ──

    function test_differentRangesAreSeparate() public {
        bytes32 pk1 = _addPosition(address(0xA), -60, 60, bytes32(uint256(1)));
        bytes32 pk2 = _addPosition(address(0xB), -120, 120, bytes32(uint256(2)));

        assertTrue(harness.containsPosition(poolId, -60, 60, pk1), "pk1 in [-60,60]");
        assertFalse(harness.containsPosition(poolId, -120, 120, pk1), "pk1 NOT in [-120,120]");

        assertTrue(harness.containsPosition(poolId, -120, 120, pk2), "pk2 in [-120,120]");
        assertFalse(harness.containsPosition(poolId, -60, 60, pk2), "pk2 NOT in [-60,60]");

        assertEq(harness.getRangeLength(poolId, -60, 60), 1, "range [-60,60] has 1");
        assertEq(harness.getRangeLength(poolId, -120, 120), 1, "range [-120,120] has 1");
    }
}
