// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";

// Force-compile artifacts so vm.getCode can find them (used by Deploy.sol in PosmTestSetup)
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndexHarness} from "../harness/FeeConcentrationIndexHarness.sol";
import {INDEX_ONE} from "../../../src/fee-concentration-index/types/AccumulatedHHIMod.sol";
import {FCITestHelper} from "../helpers/FCITestHelper.sol";

contract FeeConcentrationIndexFullFuzzTest is PosmTestSetup, FCITestHelper {
    FeeConcentrationIndexHarness harness;
    PoolId poolId;

    // ── Shared bounds (must match scripts/ffi/hhi_oracle.py) ──
    uint256 constant MIN_LPS = 2;
    uint256 constant MAX_LPS = 50;
    uint256 constant MIN_LIQUIDITY = 1e15;
    uint256 constant MAX_LIQUIDITY = 100e18;
    uint256 constant MAX_BLOCK_LIFETIME = 10_000;

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        fciLP = makeAddr("fuzzLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );
        bytes memory constructorArgs = abi.encode(address(lpm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this), flags,
            type(FeeConcentrationIndexHarness).creationCode, constructorArgs
        );
        harness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(harness) == hookAddress, "hook address mismatch");

        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(harness)), 3000, SQRT_PRICE_1_1
        );
    }

    // ── Helpers ──

    function _clamp(uint256 v, uint256 lo, uint256 hi) internal pure returns (uint256) {
        return lo + (v % (hi - lo + 1));
    }

    function _createLP(uint256 index) internal returns (address lp) {
        lp = makeAddr(string(abi.encodePacked("lp", index)));
        seedBalance(lp);
        approvePosmFor(lp);
    }

    function _callOracle(
        uint256[] memory liquidities,
        uint256[] memory blockLifetimes
    ) internal returns (uint256 expectedHHI, uint256 expectedIndexA) {
        bytes memory input = abi.encode(liquidities, blockLifetimes);
        string[] memory cmd = new string[](3);
        cmd[0] = "python3";
        cmd[1] = "scripts/ffi/hhi_oracle.py";
        cmd[2] = vm.toString(input);
        bytes memory result = vm.ffi(cmd);
        (expectedHHI, expectedIndexA) = abi.decode(result, (uint256, uint256));
    }

    // ═══════════════════════════════════════════════════════════════════
    // Tier 1: Fuzz N LPs, equal capital, equal time
    //
    // All LPs mint same liquidity at block 1.
    // 1 deterministic swap (all active).
    // All LPs exit at block 1 + blockLifetime.
    // x_k = 1/N for each. HHI = N * (1/N)^2 / max(1, blockLifetime).
    // ═══════════════════════════════════════════════════════════════════

    function testFuzz_tier1_equalCapitalEqualTime(
        uint256 nRaw,
        uint256 liqRaw,
        uint256 blRaw
    ) public {
        uint256 n = _clamp(nRaw, MIN_LPS, MAX_LPS);
        uint256 liq = _clamp(liqRaw, MIN_LIQUIDITY, MAX_LIQUIDITY);
        uint256 bl = _clamp(blRaw, 0, MAX_BLOCK_LIFETIME);

        // Phase 1: All LPs mint at block 1
        address[] memory lps = new address[](n);
        uint256[] memory tokenIds = new uint256[](n);
        for (uint256 i; i < n; ++i) {
            lps[i] = _createLP(i);
            tokenIds[i] = _mintPositionAs(lps[i], key, -60, 60, liq);
        }

        // Phase 2: 1 deterministic swap (all LPs active)
        _swap(key, true, -1e15);

        // Phase 3: Advance blocks, all LPs exit at same block
        if (bl > 0) vm.roll(block.number + bl);
        for (uint256 i; i < n; ++i) {
            _burnPositionAs(lps[i], key, tokenIds[i], -60, 60, liq);
        }

        // Phase 4: Compare with oracle
        uint256[] memory liquidities = new uint256[](n);
        uint256[] memory blockLifetimes = new uint256[](n);
        for (uint256 i; i < n; ++i) {
            liquidities[i] = liq;
            blockLifetimes[i] = bl;
        }
        (uint256 expectedHHI, uint256 expectedIndexA) = _callOracle(liquidities, blockLifetimes);

        // Phase 5: Assert
        uint256 hhi = harness.getAccumulatedHHI(poolId);
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);

        // Tolerance: rounding from Q128 integer division. Scale with N.
        uint256 hhiTolerance = n * 3;
        assertApproxEqAbs(hhi, expectedHHI, hhiTolerance, "Tier1: HHI mismatch");
        assertApproxEqAbs(uint256(indexA), expectedIndexA, n * 3, "Tier1: indexA mismatch");
        assertEq(indexB, INDEX_ONE - indexA, "Tier1: indexB complement");
        assertLe(indexA, INDEX_ONE, "Tier1: indexA capped");
    }

    // ═══════════════════════════════════════════════════════════════════
    // Tier 2: Fuzz N LPs, equal capital, fuzz different exit times
    //
    // All LPs mint same liquidity at block 1.
    // 1 deterministic swap at block 1 (all active).
    // Each LP exits at a different fuzzed block → different blockLifetimes.
    // x_k = 1/N for each (all present during swap).
    // ═══════════════════════════════════════════════════════════════════

    function testFuzz_tier2_equalCapitalDiffTime(
        uint256 nRaw,
        uint256 liqRaw,
        uint256[50] calldata blRaws
    ) public {
        uint256 n = _clamp(nRaw, MIN_LPS, MAX_LPS);
        uint256 liq = _clamp(liqRaw, MIN_LIQUIDITY, MAX_LIQUIDITY);

        // Phase 1: All LPs mint at block 1
        address[] memory lps = new address[](n);
        uint256[] memory tokenIds = new uint256[](n);
        for (uint256 i; i < n; ++i) {
            lps[i] = _createLP(i);
            tokenIds[i] = _mintPositionAs(lps[i], key, -60, 60, liq);
        }

        // Phase 2: 1 deterministic swap (all active)
        _swap(key, true, -1e15);

        // Phase 3: Each LP exits at a different block (sorted ascending to avoid roll-back)
        uint256[] memory blockLifetimes = new uint256[](n);
        uint256 startBlock = block.number;

        for (uint256 i; i < n; ++i) {
            blockLifetimes[i] = _clamp(blRaws[i], 0, MAX_BLOCK_LIFETIME);
        }

        // Sort blockLifetimes ascending so vm.roll only goes forward
        for (uint256 i; i < n; ++i) {
            for (uint256 j = i + 1; j < n; ++j) {
                if (blockLifetimes[j] < blockLifetimes[i]) {
                    (blockLifetimes[i], blockLifetimes[j]) = (blockLifetimes[j], blockLifetimes[i]);
                    (lps[i], lps[j]) = (lps[j], lps[i]);
                    (tokenIds[i], tokenIds[j]) = (tokenIds[j], tokenIds[i]);
                }
            }
        }

        uint256 currentBlock = startBlock;
        for (uint256 i; i < n; ++i) {
            uint256 exitBlock = startBlock + blockLifetimes[i];
            if (exitBlock > currentBlock) {
                vm.roll(exitBlock);
                currentBlock = exitBlock;
            }
            _burnPositionAs(lps[i], key, tokenIds[i], -60, 60, liq);
        }

        // Phase 4: Compare with oracle
        uint256[] memory liquidities = new uint256[](n);
        for (uint256 i; i < n; ++i) liquidities[i] = liq;
        (uint256 expectedHHI, uint256 expectedIndexA) = _callOracle(liquidities, blockLifetimes);

        // Phase 5: Assert
        uint256 hhi = harness.getAccumulatedHHI(poolId);
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);

        uint256 hhiTolerance = n * 3;
        assertApproxEqAbs(hhi, expectedHHI, hhiTolerance, "Tier2: HHI mismatch");
        assertApproxEqAbs(uint256(indexA), expectedIndexA, n * 3, "Tier2: indexA mismatch");
        assertEq(indexB, INDEX_ONE - indexA, "Tier2: indexB complement");
    }

    // ═══════════════════════════════════════════════════════════════════
    // Tier 3: Fuzz N LPs, fuzz different capital, equal exit time
    //
    // Each LP mints different fuzzed liquidity at block 1.
    // 1 deterministic swap (all active).
    // All LPs exit at block 1 + blockLifetime.
    // x_k = liq_k / totalLiq for each.
    // ═══════════════════════════════════════════════════════════════════

    function testFuzz_tier3_diffCapitalEqualTime(
        uint256 nRaw,
        uint256[50] calldata liqRaws,
        uint256 blRaw
    ) public {
        uint256 n = _clamp(nRaw, MIN_LPS, MAX_LPS);
        uint256 bl = _clamp(blRaw, 0, MAX_BLOCK_LIFETIME);

        address[] memory lps = new address[](n);
        uint256[] memory tokenIds = new uint256[](n);
        uint256[] memory liquidities = new uint256[](n);

        for (uint256 i; i < n; ++i) {
            liquidities[i] = _clamp(liqRaws[i], MIN_LIQUIDITY, MAX_LIQUIDITY);
            lps[i] = _createLP(i);
            tokenIds[i] = _mintPositionAs(lps[i], key, -60, 60, liquidities[i]);
        }

        _swap(key, true, -1e15);

        if (bl > 0) vm.roll(block.number + bl);
        for (uint256 i; i < n; ++i) {
            _burnPositionAs(lps[i], key, tokenIds[i], -60, 60, liquidities[i]);
        }

        uint256[] memory blockLifetimes = new uint256[](n);
        for (uint256 i; i < n; ++i) blockLifetimes[i] = bl;
        (uint256 expectedHHI, uint256 expectedIndexA) = _callOracle(liquidities, blockLifetimes);

        uint256 hhi = harness.getAccumulatedHHI(poolId);
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);

        uint256 hhiTolerance = n * 3;
        assertApproxEqAbs(hhi, expectedHHI, hhiTolerance, "Tier3: HHI mismatch");
        assertApproxEqAbs(uint256(indexA), expectedIndexA, n * 3, "Tier3: indexA mismatch");
        assertEq(indexB, INDEX_ONE - indexA, "Tier3: indexB complement");
    }

    // ═══════════════════════════════════════════════════════════════════
    // Tier 4: Fuzz N LPs, fuzz different capital, fuzz different times
    //
    // Full generality. Each LP has fuzzed liquidity and exit time.
    // 1 deterministic swap at block 1 (all active).
    // ═══════════════════════════════════════════════════════════════════

    function testFuzz_tier4_diffCapitalDiffTime(
        uint256 nRaw,
        uint256[50] calldata liqRaws,
        uint256[50] calldata blRaws
    ) public {
        uint256 n = _clamp(nRaw, MIN_LPS, MAX_LPS);

        address[] memory lps = new address[](n);
        uint256[] memory tokenIds = new uint256[](n);
        uint256[] memory liquidities = new uint256[](n);
        uint256[] memory blockLifetimes = new uint256[](n);

        for (uint256 i; i < n; ++i) {
            liquidities[i] = _clamp(liqRaws[i], MIN_LIQUIDITY, MAX_LIQUIDITY);
            blockLifetimes[i] = _clamp(blRaws[i], 0, MAX_BLOCK_LIFETIME);
            lps[i] = _createLP(i);
            tokenIds[i] = _mintPositionAs(lps[i], key, -60, 60, liquidities[i]);
        }

        _swap(key, true, -1e15);

        // Sort by blockLifetime ascending for vm.roll ordering
        for (uint256 i; i < n; ++i) {
            for (uint256 j = i + 1; j < n; ++j) {
                if (blockLifetimes[j] < blockLifetimes[i]) {
                    (blockLifetimes[i], blockLifetimes[j]) = (blockLifetimes[j], blockLifetimes[i]);
                    (liquidities[i], liquidities[j]) = (liquidities[j], liquidities[i]);
                    (lps[i], lps[j]) = (lps[j], lps[i]);
                    (tokenIds[i], tokenIds[j]) = (tokenIds[j], tokenIds[i]);
                }
            }
        }

        uint256 startBlock = block.number;
        uint256 currentBlock = startBlock;
        for (uint256 i; i < n; ++i) {
            uint256 exitBlock = startBlock + blockLifetimes[i];
            if (exitBlock > currentBlock) {
                vm.roll(exitBlock);
                currentBlock = exitBlock;
            }
            _burnPositionAs(lps[i], key, tokenIds[i], -60, 60, liquidities[i]);
        }

        (uint256 expectedHHI, uint256 expectedIndexA) = _callOracle(liquidities, blockLifetimes);

        uint256 hhi = harness.getAccumulatedHHI(poolId);
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);

        uint256 hhiTolerance = n * 3;
        assertApproxEqAbs(hhi, expectedHHI, hhiTolerance, "Tier4: HHI mismatch");
        assertApproxEqAbs(uint256(indexA), expectedIndexA, n * 3, "Tier4: indexA mismatch");
        assertEq(indexB, INDEX_ONE - indexA, "Tier4: indexB complement");
    }
}
