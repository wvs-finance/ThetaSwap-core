// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";

/// @title AngstromRANOracleAdapter Fork Test
/// @notice Validates adapter reads against pre-frozen on-chain accumulator snapshots.
/// @dev Requires ETH_RPC_URL pointing to an archive node.
///      Fixture: test/_fixtures/ran_accumulator_snapshots.json
///      Run: ETH_RPC_URL=<archive_rpc> forge test --match-contract AngstromRANOracleAdapterForkTest -vv
contract AngstromRANOracleAdapterForkTest is Test {
    string constant FIXTURE_PATH = "test/_fixtures/ran_accumulator_snapshots.json";

    AngstromAccumulatorConsumer adapter;
    PoolId poolId;
    int24 tickLower;
    int24 tickUpper;

    /// @dev Fields MUST be alphabetical by JSON key name — Forge's vm.parseJson
    ///      encodes object fields in alphabetical order for abi.decode.
    struct Snapshot {
        uint256 blockNumber;
        uint256 blockTimestamp;
        int256 currentTick;
        uint256 expectedGrowthInside;
        uint256 globalGrowth;
        uint256 outsideAbove;
        uint256 outsideBelow;
    }

    function test_accumulatorSnapshotsMatchFixture() public {
        // ── Read fixture ──
        string memory json = vm.readFile(FIXTURE_PATH);

        address angstromHook = vm.parseJsonAddress(json, ".pool.angstromHook");
        address poolManager = vm.parseJsonAddress(json, ".pool.poolManager");
        tickLower = int24(vm.parseJsonInt(json, ".pool.tickLower"));
        tickUpper = int24(vm.parseJsonInt(json, ".pool.tickUpper"));
        poolId = PoolId.wrap(vm.parseJsonBytes32(json, ".pool.poolId"));

        // ── Decode snapshots ──
        bytes memory snapshotsRaw = vm.parseJson(json, ".snapshots");
        Snapshot[] memory snapshots = abi.decode(snapshotsRaw, (Snapshot[]));
        uint256 n = snapshots.length;
        require(n >= 3, "Fixture must have at least 3 snapshots");

        // ── Fork at first block ──
        uint256 forkId = vm.createFork(vm.envString("ETH_RPC_URL"), snapshots[0].blockNumber);
        vm.selectFork(forkId);

        // ── Deploy adapter on fork ──
        adapter =
            new AngstromAccumulatorConsumer(IAngstromAuth(angstromHook), IPoolManager(poolManager));

        uint256 prevGlobalGrowth = 0;

        for (uint256 i; i < n; i++) {
            Snapshot memory snap = snapshots[i];

            // Roll to snapshot block
            vm.rollFork(snap.blockNumber);

            // ── Assert globalGrowth (exact) ──
            uint256 adapterGG = adapter.globalGrowth(poolId);
            assertEq(
                adapterGG,
                snap.globalGrowth,
                string.concat("globalGrowth mismatch at block ", vm.toString(snap.blockNumber))
            );

            // ── Assert growthInside (exact) ──
            uint256 adapterGI = adapter.growthInside(poolId, tickLower, tickUpper);
            assertEq(
                adapterGI,
                snap.expectedGrowthInside,
                string.concat("growthInside mismatch at block ", vm.toString(snap.blockNumber))
            );

            // ── Conservation cross-check (in-range snapshots) ──
            int24 snapTick = int24(snap.currentTick);
            if (snapTick >= tickLower && snapTick < tickUpper) {
                uint256 conservationGI;
                unchecked {
                    conservationGI = snap.globalGrowth - snap.outsideBelow - snap.outsideAbove;
                }
                assertEq(
                    snap.expectedGrowthInside,
                    conservationGI,
                    string.concat("Conservation violated at block ", vm.toString(snap.blockNumber))
                );
            }

            // ── Monotonicity ──
            if (i > 0) {
                assertGe(
                    adapterGG,
                    prevGlobalGrowth,
                    string.concat("globalGrowth decreased at block ", vm.toString(snap.blockNumber))
                );
            }
            prevGlobalGrowth = adapterGG;

            // ── Story-tell ──
            console2.log("Block", snap.blockNumber);
            console2.log("  globalGrowth:", adapterGG);
            console2.log("  growthInside:", adapterGI);
            console2.log("  currentTick:", snapTick);
            console2.log("  ---");
        }
    }
}
