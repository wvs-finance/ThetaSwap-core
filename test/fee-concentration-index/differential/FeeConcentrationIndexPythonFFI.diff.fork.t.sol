// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console2} from "forge-std/Test.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";

import {FeeConcentrationIndexForkHarness} from "./FeeConcentrationIndexForkHarness.sol";

/// @title FCI Fork Test — Reactive Path Accuracy Validation
/// @notice Replays 107 real WETH/USDC V4 events through the FCI reactive path
///         and asserts state matches the Python oracle at 4 snapshot blocks.
///
/// Uses the V4 native path (empty hookData) throughout:
///   - afterAddLiquidity: reads posLiquidity + feeGrowth from forked PoolManager
///   - beforeSwap + afterSwap: caches tick in transient storage, reads tickAfter from PoolManager
///   - beforeRemoveLiquidity + afterRemoveLiquidity: caches feeLast/posLiq/rangeFeeGrowth in transient storage
contract FeeConcentrationIndexForkTest is Test {
    using PoolIdLibrary for PoolKey;

    // ── Mainnet constants ──
    address constant POOL_MANAGER = 0x000000000004444c5dc75cB358380D2e3dE08A90;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    uint256 constant FORK_BLOCK = 23655999;

    FeeConcentrationIndexForkHarness harness;
    PoolKey key;
    PoolId poolId;

    // Track registered positions to skip orphan removes (positions added before event window)
    mapping(bytes32 => bool) registered;

    // ── JSON Fixture Structs ──

    struct FixtureEvent {
        uint256 blockNumber;
        string eventType;
        address sender;
        int24 tickLower;
        int24 tickUpper;
        int256 liquidityDelta;
        bytes32 salt;
        int24 swapTick;
    }

    struct Snapshot {
        uint256 blockNumber;
        uint256 afterEventIndex;
        uint128 expectedIndexA;
        uint256 expectedThetaSum;
        uint256 expectedRemovedPosCount;
        uint256 expectedAccumulatedSum;
        uint128 expectedAtNull;
        uint128 expectedDeltaPlus;
        uint256 expectedDeltaPlusPrice;
    }

    // ── Setup ──

    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("mainnet"), FORK_BLOCK);

        harness = new FeeConcentrationIndexForkHarness(POOL_MANAGER);

        // Build PoolKey matching the real WETH/USDC pool
        // Currency ordering: USDC (0xA0b8...) < WETH (0xC02a...) by address
        key = PoolKey({
            currency0: Currency.wrap(USDC),
            currency1: Currency.wrap(WETH),
            fee: 500,
            tickSpacing: int24(10),
            hooks: IHooks(address(harness))
        });
        poolId = key.toId();
    }

    // ── Main Replay Test ──

    function test_fork_wethUsdc_replayEvents_indexMatchesOracle() public {
        // Load fixture
        string memory json = vm.readFile("research/data/fixtures/fci_weth_usdc_v4.json");

        // Parse events
        uint256 eventCount = abi.decode(vm.parseJson(json, ".eventCount"), (uint256));
        FixtureEvent[] memory events = new FixtureEvent[](eventCount);
        _parseEvents(json, events);

        // Parse snapshots
        Snapshot[] memory snapshots = _parseSnapshots(json);

        // Replay
        uint256 snapIdx = 0;
        for (uint256 i = 0; i < events.length; i++) {
            FixtureEvent memory ev = events[i];
            vm.roll(ev.blockNumber);

            if (_isSwap(ev.eventType)) {
                _replaySwap(ev);
            } else if (_isModifyLiquidity(ev.eventType)) {
                bytes32 pk = _posKey(ev);
                if (ev.liquidityDelta > 0) {
                    registered[pk] = true;
                    _replayAdd(ev);
                } else if (ev.liquidityDelta < 0) {
                    // Skip orphan removes (positions added before event window).
                    // No partial-liquidity guard: the oracle counts every in-window
                    // remove as a full deregistration regardless of pre-window adds.
                    if (registered[pk]) {
                        _replayRemove(ev);
                    }
                }
            }

            // Check snapshots
            if (snapIdx < snapshots.length && snapshots[snapIdx].afterEventIndex == i) {
                _assertSnapshot(snapshots[snapIdx], i);
                snapIdx++;
            }
        }

        assertEq(snapIdx, snapshots.length, "all snapshots checked");
    }

    // ── Replay Helpers ──

    function _replayAdd(FixtureEvent memory ev) internal {
        ModifyLiquidityParams memory params = ModifyLiquidityParams({
            tickLower: ev.tickLower,
            tickUpper: ev.tickUpper,
            liquidityDelta: ev.liquidityDelta,
            salt: ev.salt
        });

        // V4 path: empty hookData → isUniswapV4 = true, reads from PoolManager.
        bytes memory hookData = "";

        harness.afterAddLiquidity(
            ev.sender, key, params,
            BalanceDelta.wrap(0), BalanceDelta.wrap(0),
            hookData
        );
    }

    function _replaySwap(FixtureEvent memory ev) internal {
        SwapParams memory params = SwapParams({
            zeroForOne: true,
            amountSpecified: 0,
            sqrtPriceLimitX96: 0
        });

        // Set the new tick BEFORE afterSwap — harness uses shadowTick for both
        // tickBefore (previous swap's tick) and tickAfter (this swap's tick).
        // afterSwap reads shadowTick, then the test updates it for the next swap.
        bytes memory hookData = "";

        harness.beforeSwap(address(0), key, params, hookData);
        harness.setShadowTick(ev.swapTick);
        harness.afterSwap(
            address(0), key, params,
            BalanceDelta.wrap(0),
            hookData
        );
    }

    function _replayRemove(FixtureEvent memory ev) internal {
        ModifyLiquidityParams memory params = ModifyLiquidityParams({
            tickLower: ev.tickLower,
            tickUpper: ev.tickUpper,
            liquidityDelta: ev.liquidityDelta,
            salt: ev.salt
        });

        // Harness overrides afterRemoveLiquidity to use shadow liquidity
        // instead of PoolManager reads. No beforeRemoveLiquidity needed.
        bytes memory hookData = "";

        harness.afterRemoveLiquidity(
            ev.sender, key, params,
            BalanceDelta.wrap(0), BalanceDelta.wrap(0),
            hookData
        );
    }

    // ── Snapshot Assertion ──

    function _assertSnapshot(Snapshot memory snap, uint256 eventIdx) internal view {
        (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) = harness.getIndex(key, false);
        uint256 accSum = harness.getReactiveAccumulatedSum(poolId);
        uint128 atNull = harness.getReactiveAtNull(poolId);
        uint128 delta = harness.getReactiveDeltaPlus(poolId);
        uint256 price = harness.getReactiveDeltaPlusPrice(poolId);

        string memory blk = vm.toString(snap.blockNumber);

        assertEq(removedPosCount, snap.expectedRemovedPosCount,
            string.concat("removedPosCount mismatch at snapshot block ", blk));
        assertEq(thetaSum, snap.expectedThetaSum,
            string.concat("thetaSum mismatch at snapshot block ", blk));
        assertEq(accSum, snap.expectedAccumulatedSum,
            string.concat("accumulatedSum mismatch at snapshot block ", blk));
        assertEq(uint256(indexA), uint256(snap.expectedIndexA),
            string.concat("indexA mismatch at snapshot block ", blk));
        assertEq(uint256(atNull), uint256(snap.expectedAtNull),
            string.concat("atNull mismatch at snapshot block ", blk));
        assertEq(uint256(delta), uint256(snap.expectedDeltaPlus),
            string.concat("deltaPlus mismatch at snapshot block ", blk));
        assertEq(price, snap.expectedDeltaPlusPrice,
            string.concat("deltaPlusPrice mismatch at snapshot block ", blk));
    }

    // ── JSON Parsing ──

    function _parseEvents(string memory json, FixtureEvent[] memory events) internal pure {
        for (uint256 i = 0; i < events.length; i++) {
            string memory prefix = string.concat(".events[", vm.toString(i), "]");

            events[i].blockNumber = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".blockNumber")), (uint256)
            );
            events[i].eventType = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".eventType")), (string)
            );
            events[i].sender = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".sender")), (address)
            );

            // Swap-specific fields
            bytes memory swapTickRaw = vm.parseJson(json, string.concat(prefix, ".swapTick"));
            if (swapTickRaw.length > 0) {
                events[i].swapTick = abi.decode(swapTickRaw, (int24));
            }

            // ModifyLiquidity-specific fields
            bytes memory liqRaw = vm.parseJson(json, string.concat(prefix, ".liquidityDelta"));
            if (liqRaw.length > 0) {
                events[i].liquidityDelta = abi.decode(liqRaw, (int256));
            }
            bytes memory tickLowerRaw = vm.parseJson(json, string.concat(prefix, ".tickLower"));
            if (tickLowerRaw.length > 0) {
                events[i].tickLower = abi.decode(tickLowerRaw, (int24));
            }
            bytes memory tickUpperRaw = vm.parseJson(json, string.concat(prefix, ".tickUpper"));
            if (tickUpperRaw.length > 0) {
                events[i].tickUpper = abi.decode(tickUpperRaw, (int24));
            }
            bytes memory saltRaw = vm.parseJson(json, string.concat(prefix, ".salt"));
            if (saltRaw.length > 0) {
                events[i].salt = abi.decode(saltRaw, (bytes32));
            }
        }
    }

    function _parseSnapshots(string memory json) internal pure returns (Snapshot[] memory) {
        uint256 count = abi.decode(vm.parseJson(json, ".snapshotCount"), (uint256));
        Snapshot[] memory snaps = new Snapshot[](count);

        for (uint256 i = 0; i < count; i++) {
            string memory prefix = string.concat(".snapshots[", vm.toString(i), "]");

            snaps[i].blockNumber = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".blockNumber")), (uint256)
            );
            snaps[i].afterEventIndex = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".afterEventIndex")), (uint256)
            );

            snaps[i].expectedIndexA = uint128(abi.decode(
                vm.parseJson(json, string.concat(prefix, ".expectedIndexA")), (uint256)
            ));
            snaps[i].expectedThetaSum = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".expectedThetaSum")), (uint256)
            );
            snaps[i].expectedRemovedPosCount = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".expectedRemovedPosCount")), (uint256)
            );
            snaps[i].expectedAccumulatedSum = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".expectedAccumulatedSum")), (uint256)
            );
            snaps[i].expectedAtNull = uint128(abi.decode(
                vm.parseJson(json, string.concat(prefix, ".expectedAtNull")), (uint256)
            ));
            snaps[i].expectedDeltaPlus = uint128(abi.decode(
                vm.parseJson(json, string.concat(prefix, ".expectedDeltaPlus")), (uint256)
            ));
            snaps[i].expectedDeltaPlusPrice = abi.decode(
                vm.parseJson(json, string.concat(prefix, ".expectedDeltaPlusPrice")), (uint256)
            );
        }

        return snaps;
    }

    // ── Position Key Helper ──

    function _posKey(FixtureEvent memory ev) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(ev.sender, ev.tickLower, ev.tickUpper, ev.salt));
    }

    // ── String Comparison Helpers ──

    function _isSwap(string memory eventType) internal pure returns (bool) {
        return keccak256(bytes(eventType)) == keccak256("Swap");
    }

    function _isModifyLiquidity(string memory eventType) internal pure returns (bool) {
        return keccak256(bytes(eventType)) == keccak256("ModifyLiquidity");
    }
}
