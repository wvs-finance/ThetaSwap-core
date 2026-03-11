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
import {INDEX_ONE} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {FCITestHelper} from "../helpers/FCITestHelper.sol";

contract FeeConcentrationIndexFullFuzzTest is PosmTestSetup, FCITestHelper {
    FeeConcentrationIndexHarness harness;
    PoolId poolId;

    // ── Shared bounds (must match research/scripts/hhi_oracle.py) ──
    uint256 constant MIN_LPS = 2;
    uint256 constant MAX_LPS = 50;
    uint256 constant MIN_LIQUIDITY = 1e15;
    uint256 constant MAX_LIQUIDITY = 100e18;
    uint256 constant MAX_BLOCK_LIFETIME = 10_000;

    struct OracleResult {
        uint256 expectedHHI;
        uint256 expectedIndexA;
        uint256 expectedThetaSum;
        uint256 expectedRemovedPosCount;
        uint256 expectedAtNull;
        uint256 expectedDeltaPlus;
    }

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

    // indexA tolerance: N division rounding errors amplified by sqrt.
    // Error ≈ n * sqrt(n * max(bl, 1)) / 2. Use n * sqrt(n * max(bl,1)) for safety margin.
    function _indexATolerance(uint256 n, uint256 bl) internal pure returns (uint256) {
        uint256 product = n * (bl > 0 ? bl : 1);
        return 1 + n * FixedPointMathLib.sqrt(product);
    }

    function _createLP(uint256 index) internal returns (address lp) {
        lp = makeAddr(string(abi.encodePacked("lp", index)));
        seedBalance(lp);
        approvePosmFor(lp);
    }

    function _callOracle(
        uint256[] memory liquidities,
        uint256[] memory blockLifetimes
    ) internal returns (OracleResult memory result) {
        bytes memory input = abi.encode(liquidities, blockLifetimes);
        string[] memory cmd = new string[](3);
        cmd[0] = "python3";
        cmd[1] = "research/scripts/hhi_oracle.py";
        cmd[2] = vm.toString(input);
        bytes memory raw = vm.ffi(cmd);
        (
            result.expectedHHI,
            result.expectedIndexA,
            result.expectedThetaSum,
            result.expectedRemovedPosCount,
            result.expectedAtNull,
            result.expectedDeltaPlus
        ) = abi.decode(raw, (uint256, uint256, uint256, uint256, uint256, uint256));
    }

    function _assertFCI(
        string memory tier,
        OracleResult memory oracle,
        uint256 n,
        uint256 maxBl
    ) internal view {
        uint256 hhi = harness.getAccumulatedHHI(poolId);
        (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) = harness.getIndex(key, false);
        uint128 atNull = harness.getAtNull(poolId);
        uint128 deltaPlus = harness.getDeltaPlus(poolId);

        uint256 hhiTolerance = n * 3;
        uint256 idxTolerance = _indexATolerance(n, maxBl);

        assertApproxEqAbs(hhi, oracle.expectedHHI, hhiTolerance,
            string.concat(tier, ": HHI mismatch"));
        assertApproxEqAbs(uint256(indexA), oracle.expectedIndexA, idxTolerance,
            string.concat(tier, ": indexA mismatch"));
        assertLe(indexA, INDEX_ONE,
            string.concat(tier, ": indexA capped"));
        assertEq(removedPosCount, oracle.expectedRemovedPosCount,
            string.concat(tier, ": removedPosCount mismatch"));
        assertApproxEqAbs(thetaSum, oracle.expectedThetaSum, hhiTolerance,
            string.concat(tier, ": thetaSum mismatch"));
        assertApproxEqAbs(uint256(atNull), oracle.expectedAtNull, idxTolerance,
            string.concat(tier, ": atNull mismatch"));
        assertApproxEqAbs(uint256(deltaPlus), oracle.expectedDeltaPlus, 2 * idxTolerance,
            string.concat(tier, ": deltaPlus mismatch"));
    }

    // ═══════════════════════════════════════════════════════════════════
    // Tier 1: Fuzz N LPs, equal capital, equal time
    //
    // All LPs mint same liquidity at block 1.
    // 1 deterministic swap (all active).
    // All LPs exit at block 1 + blockLifetime.
    // x_k = 1/N for each → Δ⁺ = 0 (competitive equilibrium).
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
        OracleResult memory oracle = _callOracle(liquidities, blockLifetimes);

        // Phase 5: Assert all FCI quantities
        _assertFCI("Tier1", oracle, n, bl);

        // Tier 1 invariant: equal capital → Δ⁺ = 0 (competitive equilibrium)
        uint128 deltaPlus = harness.getDeltaPlus(poolId);
        assertEq(deltaPlus, 0, "Tier1: deltaPlus must be 0 - equal capital = competitive null");
    }

    // ═══════════════════════════════════════════════════════════════════
    // Tier 2: Fuzz N LPs, equal capital, fuzz different exit times
    //
    // All LPs mint same liquidity at block 1.
    // 1 deterministic swap at block 1 (all active).
    // Each LP exits at a different fuzzed block → different blockLifetimes.
    // x_k = 1/N for each (all present during swap) → Δ⁺ = 0.
    // Duration heterogeneity alone does NOT create excess concentration.
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
        OracleResult memory oracle = _callOracle(liquidities, blockLifetimes);

        // Phase 5: Assert all FCI quantities
        _assertFCI("Tier2", oracle, n, blockLifetimes[n - 1]);

        // Tier 2 invariant: equal capital → Δ⁺ = 0 regardless of duration heterogeneity
        uint128 deltaPlus = harness.getDeltaPlus(poolId);
        assertEq(deltaPlus, 0, "Tier2: deltaPlus must be 0 - equal fee shares = competitive null");
    }

    // ═══════════════════════════════════════════════════════════════════
    // Tier 3: Fuzz N LPs, fuzz different capital, equal exit time
    //
    // Each LP mints different fuzzed liquidity at block 1.
    // 1 deterministic swap (all active).
    // All LPs exit at block 1 + blockLifetime.
    // x_k = liq_k / totalLiq → Δ⁺ ≥ 0, verify against oracle.
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
        OracleResult memory oracle = _callOracle(liquidities, blockLifetimes);

        _assertFCI("Tier3", oracle, n, bl);
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

        OracleResult memory oracle = _callOracle(liquidities, blockLifetimes);

        _assertFCI("Tier4", oracle, n, blockLifetimes[n - 1]);
    }
}
