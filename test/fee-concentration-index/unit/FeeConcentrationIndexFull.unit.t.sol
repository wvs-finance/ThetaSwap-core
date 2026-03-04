// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";

// Force-compile artifacts so vm.getCode can find them (used by Deploy.sol in PosmTestSetup)
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndexHarness} from "../harness/FeeConcentrationIndexHarness.sol";
import {INDEX_ONE} from "../../../src/fee-concentration-index/types/AccumulatedHHIMod.sol";
import {FCITestHelper} from "../helpers/FCITestHelper.sol";

// US3 integration tests: full add → swap → remove → index lifecycle.
// Inherits PosmTestSetup for real PositionManager, Permit2, and token infrastructure.
// Inherits FCITestHelper for _mintPosition, _burnPosition, _swap, _positionKey helpers.
// All operations go through lpm (PositionManager) → PoolManager → hooks.

contract FeeConcentrationIndexFullUnitTest is PosmTestSetup, FCITestHelper {
    FeeConcentrationIndexHarness harness;
    PoolId poolId;
    address lp2;

    // INDEX_ONE imported from AccumulatedHHIMod.sol (canonical source of truth)

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        // Wire up FCITestHelper actor references
        fciLP = makeAddr("lp");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        lp2 = makeAddr("lp2");
        seedBalance(lp2);
        approvePosmFor(lp2);

        seedBalance(fciLP);
        approvePosmFor(fciLP);

        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );

        bytes memory constructorArgs = abi.encode(address(lpm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this),
            flags,
            type(FeeConcentrationIndexHarness).creationCode,
            constructorArgs
        );

        harness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(harness) == hookAddress, "hook address mismatch");

        (key, poolId) = initPool(
            currency0,
            currency1,
            IHooks(address(harness)),
            3000,
            SQRT_PRICE_1_1
        );
    }

    // ═══════════════════════════════════════════════════════════════════════
    // US3-A: Single passive LP — sole provider, no swaps
    //
    // Setup:  One LP mints a position in [-60, 60]. No swaps happen.
    // Remove: LP burns the position (full removal).
    //
    // Expected:
    //   - lifetime = 0 (no swaps crossed the range → swap counter never incremented)
    //   - Because lifetime == 0, the HHI term is skipped entirely (division by zero guard)
    //   - accumulatedHHI remains 0
    //   - indexA = 0 (sqrt(0) = 0)
    //   - indexB = INDEX_ONE (1.0 in Q128)
    //
    // Interpretation:
    //   Theta (the swap-time clock) never started. Without swap activity there is
    //   no fee generation and therefore no concentration measurement. The index
    //   correctly reports "no data" — indexB stays at its ceiling, meaning the
    //   system has not observed any concentration signal.
    // ═══════════════════════════════════════════════════════════════════════

    function test_US3A_soleProvider_noSwaps_indexUnchanged() public {
        // 1. Mint: single LP is the only provider (via LiquidityOperations.mint)
        uint256 tokenId = _mintPosition(key, -60, 60, 1e18);

        // Sanity: position is registered in the hook
        bytes32 pk = _positionKey(tokenId, -60, 60);
        assertTrue(harness.containsPosition(poolId, -60, 60, pk), "position registered");
        assertEq(harness.getActiveRangeCount(poolId), 1, "one active range");

        // 2. No swaps — theta never starts

        // 3. Burn: LP withdraws everything
        _burnPosition(key, tokenId, -60, 60, 1e18);

        // Position deregistered
        assertFalse(harness.containsPosition(poolId, -60, 60, pk), "position deregistered");
        assertEq(harness.getActiveRangeCount(poolId), 0, "no active ranges");

        // HHI unchanged — lifetime was 0, term was skipped
        assertEq(harness.getAccumulatedHHI(poolId), 0, "accumulatedHHI must be 0 when no swaps");

        // Index: A=0, B=1.0 — no concentration data
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);
        assertEq(indexA, 0, "indexA must be 0: theta never started");
        assertEq(indexB, INDEX_ONE, "indexB must be 1.0: no concentration observed");
    }

    // Variant: storage is fully cleaned up after the position lifecycle.

    function test_US3A_soleProvider_noSwaps_storageFullyCleanedUp() public {
        uint256 tokenId = _mintPosition(key, -60, 60, 1e18);
        bytes32 pk = _positionKey(tokenId, -60, 60);

        _burnPosition(key, tokenId, -60, 60, 1e18);

        // Baseline cleared
        assertEq(harness.getBaseline0(poolId, pk), 0, "baseline cleaned up");
        // Range key cleared
        assertEq(harness.getRangeKeyOf(poolId, pk), bytes32(0), "rangeKeyOf cleared");
        // Baseline swap count cleared
        assertEq(harness.getBaselineSwapCount(poolId, pk), 0, "baselineSwapCount cleared");
        // Range length is 0
        assertEq(harness.getRangeLength(poolId, -60, 60), 0, "range empty after removal");
    }

    // Variant: multiple mint/burn cycles with no swaps — index stays at (0, 1.0) every time.

    function test_US3A_soleProvider_noSwaps_repeatedCycles_indexStaysDefault() public {
        // note: positions coming from the same lp need to add to concentration, this is to be
        // addressed later

        for (uint256 i; i < 3; ++i) {
            uint256 tokenId = _mintPosition(key, -60, 60, 1e18);
            _burnPosition(key, tokenId, -60, 60, 1e18);
        }

        assertEq(harness.getAccumulatedHHI(poolId), 0, "HHI still 0 after 3 idle cycles");

        (uint128 indexA, uint128 indexB) = harness.getIndex(key);
        assertEq(indexA, 0, "indexA still 0");
        assertEq(indexB, INDEX_ONE, "indexB still 1.0");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // US3-B: Single passive LP — sole provider, 1 swap, full burn
    //
    // Pre-conditions:
    //   - single passive liquidity provider on [-60, 60]
    //   - SQRT_PRICE_1_1 → tick 0 in the middle of the range
    // Test:
    //   - 1 swap through the range generates fees, increments swap count to 1
    //   - LP burns position (full removal)
    //   - sole provider → x_k = 1, lifetime = 1
    //   - HHI = x_k^2 / lifetime = Q128, indexA = INDEX_ONE (within 1 wei)
    // ═══════════════════════════════════════════════════════════════════════

    function test_unit_soleProvider_oneSwapOnRange_indexIsMax() public {
        uint256 tokenId = _mintPosition(key, -60, 60, 1e18);

        // 1 swap through the range → generates fees, increments swap count to 1
        _swap(key, true, -100);

        // Full burn: decrease all liquidity + burn NFT
        _burnPosition(key, tokenId, -60, 60, 1e18);

        // Sole provider: x_k = FEE_SHARE_ONE (2^128-1), lifetime = 1
        // square() = mulDiv(2^128-1, 2^128-1, 2^128) = 2^128 - 2 (1 wei below Q128)
        // toIndexA(2^128-2) → sqrt((2^128-2) << 128) → INDEX_ONE - 1 (rounding)
        // 1-wei precision loss from Q128 representation of 1.0 as (2^128-1)
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);
        assertGe(indexA, INDEX_ONE - 1, "indexA must be max (within 1 wei): sole provider");
        assertLe(indexB, 1, "indexB must be ~0: complement of max concentration");
    }

    // TODO: partial removal via decreaseLiquidity (without burn) currently triggers
    // full deregister in _afterRemoveLiquidity. Needs a liquidityDelta guard:
    //   - if remaining liquidity > 0 after decrease, do NOT deregister
    //   - only compute HHI + deregister on full exit (liquidity reaches 0)
    // Once that guard is implemented, add:
    //   test_unit_soleProvider_partialRemoval_positionStaysRegistered
    //   test_unit_soleProvider_partialThenFullRemoval_indexIsMax


    // ═══════════════════════════════════════════════════════════════════════
    // US3-C: Two equal passive LPs, same range, 1 swap, both withdraw.
    //
    // Setup:  LP1 and LP2 each mint 1e18 liquidity on [-60, 60].
    // Action: 1 swap through the range.
    // Remove: Both LPs burn their positions.
    //
    // Expected:
    //   Each LP provides 50% of range liquidity → x_k = 1/2 for each.
    //   lifetime = 1 for each (1 swap crossed the range).
    //   HHI = (1/2)^2 / 1 + (1/2)^2 / 1 = 1/4 + 1/4 = 1/2 (in Q128).
    //   indexA = sqrt(1/2) ≈ 0.707 * INDEX_ONE.
    //
    // Interpretation:
    //   Equal competition — no LP dominates in sophistication. The index
    //   reflects moderate concentration (not max, not zero).
    // ═══════════════════════════════════════════════════════════════════════

    function test_unit_twoDifferentHomogeneousLps_oneSwap_indexIsHalf() public {
        // Both LPs mint equal liquidity on same range
        uint256 tokenId1 = _mintPosition(key, -60, 60, 1e18);
        uint256 tokenId2 = _mintPositionAs(lp2, key, -60, 60, 1e18);

        // Sanity: totalRangeLiquidity = 2e18
        assertEq(harness.getTotalRangeLiquidity(poolId, -60, 60), 2e18, "total range liquidity");

        // 1 swap through the range
        _swap(key, true, -100);

        // Both LPs burn
        _burnPosition(key, tokenId1, -60, 60, 1e18);
        _burnPositionAs(lp2, key, tokenId2, -60, 60, 1e18);

        // HHI = 1/2 in Q128 = (1 << 128) / 2 = Q128 / 2
        // Each term: x_k = 1/2, x_k^2 = (1/2)^2 = 1/4 in Q128
        // But FEE_SHARE_ONE = 2^128-1, not 2^128, so minor precision loss.
        // x_k ≈ (2^128-1)/2, x_k^2 ≈ mulDiv((2^128-1)/2, (2^128-1)/2, 2^128)
        // Each HHI term ≈ Q128/4, total ≈ Q128/2 (within rounding)
        uint256 hhi = harness.getAccumulatedHHI(poolId);
        uint256 expectedHHI = (1 << 128) / 2;
        // Allow small rounding tolerance (a few wei from Q128 arithmetic)
        assertApproxEqAbs(hhi, expectedHHI, 3, "HHI should be ~Q128/2");

        // indexA = sqrt(Q128/2) ≈ 0.707 * INDEX_ONE
        // sqrt(0.5) ≈ 0.7071067811865475
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);
        uint256 expectedIndexA = uint256(INDEX_ONE) * 7071 / 10000;
        assertApproxEqRel(indexA, expectedIndexA, 0.001e18, "indexA should be ~0.707 * INDEX_ONE");
        assertGt(indexA, 0, "indexA > 0: concentration detected");
        assertLt(indexA, INDEX_ONE, "indexA < 1: not sole provider");
        // indexB = 1 - indexA ≈ 0.293 * INDEX_ONE
        assertEq(indexB, INDEX_ONE - indexA, "indexB must be 1 - indexA");
        uint256 expectedIndexB = uint256(INDEX_ONE) - expectedIndexA;
        assertApproxEqRel(indexB, expectedIndexB, 0.001e18, "indexB should be ~0.293 * INDEX_ONE");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // US3-D: Two passive LPs with unequal capital, same range, 1 swap.
    //
    // Setup:  LP1 mints 1e18, LP2 mints 2e18 on [-60, 60]. totalRangeLiq = 3e18.
    // Action: 1 swap through the range.
    // Remove: Both LPs burn their positions.
    //
    // Expected:
    //   x_1 = 1e18 / 3e18 = 1/3,  x_2 = 2e18 / 3e18 = 2/3
    //   HHI = (1/3)^2 + (2/3)^2 = 1/9 + 4/9 = 5/9
    //   indexA = sqrt(5/9) = sqrt(5)/3 ≈ 0.7454 * INDEX_ONE
    //
    // Interpretation:
    //   The index captures "scale economics" — LP2's capital advantage shows
    //   as higher concentration than the equal-capital case (0.7454 > 0.707).
    //   The bigger the capital disparity, the closer the index approaches 1.0.
    // ═══════════════════════════════════════════════════════════════════════

    function test_unit_twoDifferentOnlyCapitalHeterogenousLps_oneSwap_indexIsGtHalf() public {
        uint256 tokenId1 = _mintPosition(key, -60, 60, 1e18);
        uint256 tokenId2 = _mintPositionAs(lp2, key, -60, 60, 2e18);

        assertEq(harness.getTotalRangeLiquidity(poolId, -60, 60), 3e18, "total range liquidity");

        // 1 swap through the range
        _swap(key, true, -100);

        // Both LPs burn
        _burnPosition(key, tokenId1, -60, 60, 1e18);
        _burnPositionAs(lp2, key, tokenId2, -60, 60, 2e18);

        // HHI = 5/9 in Q128 = 5 * Q128 / 9
        uint256 hhi = harness.getAccumulatedHHI(poolId);
        uint256 expectedHHI = 5 * (uint256(1) << 128) / 9;
        assertApproxEqAbs(hhi, expectedHHI, 3, "HHI should be ~5*Q128/9");

        // indexA = sqrt(5/9) = sqrt(5)/3 ≈ 0.7454 * INDEX_ONE
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);
        uint256 expectedIndexA = uint256(INDEX_ONE) * 7454 / 10000;
        assertApproxEqRel(indexA, expectedIndexA, 0.001e18, "indexA should be ~0.7454 * INDEX_ONE");

        // Must be strictly greater than the equal-capital case (sqrt(1/2) ≈ 0.707)
        uint256 equalCaseIndexA = uint256(INDEX_ONE) * 7071 / 10000;
        assertGt(indexA, equalCaseIndexA, "capital disparity increases concentration");

        // indexB = 1 - indexA ≈ 0.2546 * INDEX_ONE
        assertEq(indexB, INDEX_ONE - indexA, "indexB must be 1 - indexA");
        uint256 expectedIndexB = uint256(INDEX_ONE) - expectedIndexA;
        assertApproxEqRel(indexB, expectedIndexB, 0.001e18, "indexB should be ~0.2546 * INDEX_ONE");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // US3-E: Two equal-capital LPs, same range, one exits early (block-based).
    //
    // Setup:  LP1 and LP2 each mint 1e18 on [-60, 60] at block 1.
    // Action:
    //   Block 2: Swap 1 (both active)
    //   Block 3: LP1 burns (blockLifetime = 3-1 = 2)
    //   Block 4: Swap 2 (only LP2 active)
    //   Block 5: LP2 burns (blockLifetime = 5-1 = 4)
    //
    // Expected:
    //   LP1: x_1 = 1/2, blockLifetime = 2, term = (1/2)^2 / 2 = Q128/8
    //   LP2: x_2 = 1/2, blockLifetime = 4, term = (1/2)^2 / 4 = Q128/16
    //   HHI = Q128/8 + Q128/16 = 3*Q128/16
    //   indexA = sqrt(3/16) = sqrt(3)/4 ≈ 0.433 * INDEX_ONE
    //
    // Interpretation:
    //   Block-based lifetime dilutes concentration more than swap-based.
    //   Both LPs stay multiple blocks, reducing per-block dominance.
    //   indexA < US3-C (0.707): block-duration dilution reduces concentration.
    // ═══════════════════════════════════════════════════════════════════════

    function test_unit_twoDifferentCapitalHomogeneousDurationHeterogeneousLps_twoSwaps_indexGtHalf() public {
        // Block 1 (default): both LPs mint equal liquidity
        uint256 tokenId1 = _mintPosition(key, -60, 60, 1e18);
        uint256 tokenId2 = _mintPositionAs(lp2, key, -60, 60, 1e18);

        // Block 2: Swap 1 (both active)
        vm.roll(block.number + 1);
        _swap(key, true, -100);

        // Block 3: LP1 exits (blockLifetime = 3-1 = 2)
        vm.roll(block.number + 1);
        _burnPosition(key, tokenId1, -60, 60, 1e18);

        // Block 4: Swap 2 (only LP2 active)
        vm.roll(block.number + 1);
        _swap(key, false, -100);

        // Block 5: LP2 exits (blockLifetime = 5-1 = 4)
        vm.roll(block.number + 1);
        _burnPositionAs(lp2, key, tokenId2, -60, 60, 1e18);

        // HHI = 3/16 in Q128 = 3 * Q128 / 16
        uint256 hhi = harness.getAccumulatedHHI(poolId);
        uint256 expectedHHI = 3 * (uint256(1) << 128) / 16;
        assertApproxEqAbs(hhi, expectedHHI, 3, "HHI should be ~3*Q128/16");

        // indexA = sqrt(3/16) = sqrt(3)/4 ≈ 0.433 * INDEX_ONE
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);
        uint256 expectedIndexA = uint256(INDEX_ONE) * 4330 / 10000;
        assertApproxEqRel(indexA, expectedIndexA, 0.002e18, "indexA should be ~0.433 * INDEX_ONE");

        // Less than equal-exit same-block case (block dilution reduces concentration)
        uint256 equalExitIndexA = uint256(INDEX_ONE) * 7071 / 10000;
        assertLt(indexA, equalExitIndexA, "indexA < equal-exit case: block-duration dilution");

        // indexB = 1 - indexA
        assertEq(indexB, INDEX_ONE - indexA, "indexB must be 1 - indexA");
        uint256 expectedIndexB = uint256(INDEX_ONE) - expectedIndexA;
        assertApproxEqRel(indexB, expectedIndexB, 0.002e18, "indexB should be ~0.567 * INDEX_ONE");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // US3-F: Sophisticated LP crowd-out — captures fees across a round-trip then exits.
    //
    // This is NOT pure JIT (single-block in/out). The sophisticated LP stays for
    // the reverse swap to neutralize impermanent loss, making it a 1-block round-trip
    // strategy. Block-based lifetime still = 1, so the HHI penalty is identical to
    // pure JIT — which is the correct behavior: mempool advantage is bounded by blocks,
    // not by how many swaps fit in one block.
    //
    // Setup:
    //   Block 1: LP_passive adds 1e18 on [-60, 60].
    //   Block 50: LP_sophisticated adds 9e18 on [-60, 60] (9:1 capital ratio).
    //   totalRangeLiq = 10e18.
    //
    // Action:
    //   Block 50: Swap 1 (large zeroForOne, both active — sophisticated captures 90%).
    //   Block 51: Swap 2 (reverse oneForZero, both active — nullifies IL for sophisticated).
    //   Block 51: LP_sophisticated exits (blockLifetime = 51-50 = 1).
    //   Block 100: Swap 3 (small, only passive active).
    //   Block 101: LP_passive exits (blockLifetime = 101-1 = 100).
    //
    // x_k computation:
    //   Both LPs share the same range and both are active during swaps 1 and 2.
    //   feeGrowthInside accrues per-unit-of-liquidity, so the liquidity ratio
    //   determines fee share: x_sophisticated = 9e18/10e18 = 9/10.
    //   The reverse swap adds fees (fees always accrue regardless of direction),
    //   but the liquidity ratio stays 9:1, so x_k is unchanged.
    //
    // Expected:
    //   x_sophisticated = 9/10, blockLifetime = 1, term = (9/10)^2 / 1 = 81*Q128/100
    //   x_passive = 1/10, blockLifetime = 100, term = (1/10)^2 / 100 = Q128/10000
    //   HHI = 81*Q128/100 + Q128/10000 = 8101*Q128/10000
    //   indexA = sqrt(8101/10000) ≈ 0.900 * INDEX_ONE
    //
    // Interpretation:
    //   The sophisticated LP enters 1 block before the swap, captures 90% of fees
    //   across a forward+reverse round-trip (neutralizing IL), then exits.
    //   blockLifetime = 1 → no dilution of its HHI term.
    //   Passive LP's 100-block lifetime dilutes its negligible contribution further.
    //   Index ≈ 0.900, close to maximum — crowd-out dominates.
    // ═══════════════════════════════════════════════════════════════════════

    function test_unit_twoDifferentHeterogenousLps_threeSwaps_indexCapturesCrowdOutIsCloseToMax() public {
        // Block 1: LP_passive mints
        uint256 tokenId_passive = _mintPosition(key, -60, 60, 1e18);

        // Block 50: LP_sophisticated enters just before the swap
        vm.roll(block.number + 49);
        address lpSophisticated = makeAddr("lpSophisticated");
        seedBalance(lpSophisticated);
        approvePosmFor(lpSophisticated);
        uint256 tokenId_sophisticated = _mintPositionAs(lpSophisticated, key, -60, 60, 9e18);

        assertEq(harness.getTotalRangeLiquidity(poolId, -60, 60), 10e18, "total range liquidity = 10e18");

        // Block 50: Swap 1 (large zeroForOne, both active — sophisticated captures 90% of fees)
        _swap(key, true, -1e15);

        // Block 51: Swap 2 (reverse oneForZero, both still active — nullifies IL for sophisticated LP)
        // The sophisticated LP does NOT exit before the reverse swap. It stays for the round-trip
        // to neutralize impermanent loss. This is not pure JIT (same-block exit) but a sophisticated
        // strategy that spans the forward+reverse swap pair within a 1-block window.
        vm.roll(block.number + 1);
        _swap(key, false, -1e15);

        // Block 51: LP_sophisticated exits after the round-trip (blockLifetime = 51-50 = 1)
        _burnPositionAs(lpSophisticated, key, tokenId_sophisticated, -60, 60, 9e18);

        // Block 100: Swap 3 (small, only passive active)
        vm.roll(block.number + 49);
        _swap(key, true, -100);

        // Block 101: LP_passive exits (blockLifetime = 101-1 = 100)
        vm.roll(block.number + 1);
        _burnPosition(key, tokenId_passive, -60, 60, 1e18);

        // HHI = 81/100 + 1/10000 = 8101/10000
        uint256 hhi = harness.getAccumulatedHHI(poolId);
        uint256 expectedHHI = 8101 * (uint256(1) << 128) / 10000;
        assertApproxEqAbs(hhi, expectedHHI, 5, "HHI should be ~8101/10000 * Q128");

        // indexA = sqrt(8101/10000) ≈ 0.9006 * INDEX_ONE
        (uint128 indexA, uint128 indexB) = harness.getIndex(key);
        uint256 expectedIndexA = uint256(INDEX_ONE) * 9006 / 10000;
        assertApproxEqRel(indexA, expectedIndexA, 0.002e18, "indexA should be ~0.900 * INDEX_ONE");

        // Must dominate US3-D (capital-heterogeneous: 0.745)
        uint256 capitalHeteroIndexA = uint256(INDEX_ONE) * 7454 / 10000;
        assertGt(indexA, capitalHeteroIndexA, "crowd-out dominates capital-heterogeneous case");

        // Close to max (sole provider = 1.0)
        assertGt(indexA, uint128(uint256(INDEX_ONE) * 9 / 10), "indexA > 0.9: close to maximum concentration");

        // indexB = 1 - indexA ≈ 0.100 * INDEX_ONE
        assertEq(indexB, INDEX_ONE - indexA, "indexB must be 1 - indexA");
        uint256 expectedIndexB = uint256(INDEX_ONE) - expectedIndexA;
        assertApproxEqRel(indexB, expectedIndexB, 0.02e18, "indexB should be ~0.100 * INDEX_ONE");
    }
}
