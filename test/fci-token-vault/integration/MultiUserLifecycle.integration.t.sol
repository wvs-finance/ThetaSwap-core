// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

import {FCIFixture} from "../fixtures/FCIFixture.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/CollateralCustodianMod.sol";

contract MultiUserLifecycleTest is FCIFixture {
    address aliceAddr;
    uint256 alicePk;
    address bobAddr;
    uint256 bobPk;
    address lpAddr;
    uint256 lpPk;
    address jitAddr;
    uint256 jitPk;
    address swapperAddr;
    uint256 swapperPk;

    uint256 constant ALICE_DEPOSIT = 0.1e18;
    uint256 constant BOB_DEPOSIT = 0.2e18;
    uint256 constant TOTAL_DEPOSIT = ALICE_DEPOSIT + BOB_DEPOSIT;
    uint256 constant LP_CAPITAL = 1e18;
    uint256 constant ROUNDS = 3;

    function setUp() public {
        _deployFixture();

        // Create wallets
        Vm.Wallet memory w;
        w = vm.createWallet("alice");
        aliceAddr = w.addr; alicePk = w.privateKey;
        w = vm.createWallet("bob");
        bobAddr = w.addr; bobPk = w.privateKey;
        w = vm.createWallet("lp");
        lpAddr = w.addr; lpPk = w.privateKey;
        w = vm.createWallet("jit");
        jitAddr = w.addr; jitPk = w.privateKey;
        w = vm.createWallet("swapper");
        swapperAddr = w.addr; swapperPk = w.privateKey;

        // Setup actors
        _setupLP(lpAddr);
        _setupLP(jitAddr);
        _setupSwapper(swapperAddr);
        seedBalance(aliceAddr);
        seedBalance(bobAddr);
    }

    // ═══════════════════════════════════════════════════════════════
    // Helpers
    // ═══════════════════════════════════════════════════════════════

    function _runRounds() internal {
        for (uint256 i; i < ROUNDS; ++i) {
            _deadline = block.timestamp + 1;
            _runJitRound(
                lpAddr, LP_CAPITAL,
                jitAddr, JIT_CAPITAL,
                true,
                int256(TRADE_SIZE)
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // Test 1: Multi-user deposit totals
    // ═══════════════════════════════════════════════════════════════

    function test_multi_user_deposit_and_total() public {
        _depositToVault(aliceAddr, ALICE_DEPOSIT);
        _depositToVault(bobAddr, BOB_DEPOSIT);

        assertEq(
            vault.totalDeposited(), TOTAL_DEPOSIT,
            "totalDeposited should equal sum of deposits"
        );
        assertEq(
            vault.balanceOf(aliceAddr, LONG), ALICE_DEPOSIT,
            "Alice LONG balance should equal her deposit"
        );
        assertEq(
            vault.balanceOf(bobAddr, LONG), BOB_DEPOSIT,
            "Bob LONG balance should equal his deposit"
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // Test 2: Independent redemption (Alice LONG only, Bob SHORT only)
    // ═══════════════════════════════════════════════════════════════

    function test_multi_user_independent_redemption() public {
        _depositToVault(aliceAddr, ALICE_DEPOSIT);
        _depositToVault(bobAddr, BOB_DEPOSIT);

        _runRounds();
        _settleVault();

        // Alice redeems only LONG
        vm.prank(aliceAddr);
        vault.redeemLong(ALICE_DEPOSIT);

        assertEq(vault.balanceOf(aliceAddr, LONG), 0, "Alice LONG should be 0 after redeem");
        assertEq(
            vault.balanceOf(aliceAddr, SHORT), ALICE_DEPOSIT,
            "Alice SHORT should be unchanged"
        );

        // Bob redeems only SHORT
        vm.prank(bobAddr);
        vault.redeemShort(BOB_DEPOSIT);

        assertEq(vault.balanceOf(bobAddr, SHORT), 0, "Bob SHORT should be 0 after redeem");
        assertEq(
            vault.balanceOf(bobAddr, LONG), BOB_DEPOSIT,
            "Bob LONG should be unchanged"
        );

        // Vault still has backing for unredeemed tokens
        assertGt(
            vault.totalDeposited(), 0,
            "Vault should still have backing for unredeemed tokens"
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // Test 3: Cross-solvency (both redeem both sides)
    // ═══════════════════════════════════════════════════════════════

    function test_multi_user_cross_solvency() public {
        _depositToVault(aliceAddr, ALICE_DEPOSIT);
        _depositToVault(bobAddr, BOB_DEPOSIT);

        _runRounds();
        _settleVault();

        address collateral = Currency.unwrap(currency1);

        // Alice redeems both
        uint256 aliceBalBefore = IERC20(collateral).balanceOf(aliceAddr);
        vm.prank(aliceAddr);
        vault.redeemLong(ALICE_DEPOSIT);
        uint256 aliceBalMid = IERC20(collateral).balanceOf(aliceAddr);
        vm.prank(aliceAddr);
        vault.redeemShort(ALICE_DEPOSIT);
        uint256 aliceBalAfter = IERC20(collateral).balanceOf(aliceAddr);

        uint256 aliceLongPayout = aliceBalMid - aliceBalBefore;
        uint256 aliceShortPayout = aliceBalAfter - aliceBalMid;
        uint256 aliceTotal = aliceLongPayout + aliceShortPayout;

        // Bob redeems both
        uint256 bobBalBefore = IERC20(collateral).balanceOf(bobAddr);
        vm.prank(bobAddr);
        vault.redeemLong(BOB_DEPOSIT);
        uint256 bobBalMid = IERC20(collateral).balanceOf(bobAddr);
        vm.prank(bobAddr);
        vault.redeemShort(BOB_DEPOSIT);
        uint256 bobBalAfter = IERC20(collateral).balanceOf(bobAddr);

        uint256 bobLongPayout = bobBalMid - bobBalBefore;
        uint256 bobShortPayout = bobBalAfter - bobBalMid;
        uint256 bobTotal = bobLongPayout + bobShortPayout;

        // Per-user conservation (±1 wei)
        assertLe(aliceTotal, ALICE_DEPOSIT, "Alice total payout should not exceed deposit");
        assertGe(aliceTotal, ALICE_DEPOSIT - 1, "Alice total payout within 1 wei of deposit");

        assertLe(bobTotal, BOB_DEPOSIT, "Bob total payout should not exceed deposit");
        assertGe(bobTotal, BOB_DEPOSIT - 1, "Bob total payout within 1 wei of deposit");

        // Final state
        assertEq(vault.totalDeposited(), 0, "totalDeposited should be 0 after full redemption");

        console.log("=== MULTI USER CROSS SOLVENCY ===");
        console.log("Alice LONG payout:", aliceLongPayout);
        console.log("Alice SHORT payout:", aliceShortPayout);
        console.log("Alice total:", aliceTotal);
        console.log("Bob LONG payout:", bobLongPayout);
        console.log("Bob SHORT payout:", bobShortPayout);
        console.log("Bob total:", bobTotal);
    }

    // ═══════════════════════════════════════════════════════════════
    // Test 4: Partial redemption ordering
    // ═══════════════════════════════════════════════════════════════

    function test_partial_redemption_ordering() public {
        _depositToVault(aliceAddr, ALICE_DEPOSIT);

        _runRounds();
        _settleVault();

        address collateral = Currency.unwrap(currency1);

        // Preview what full LONG redemption would yield
        uint256 expectedFullPayout = vault.previewLongPayout(ALICE_DEPOSIT);

        uint256 half = ALICE_DEPOSIT / 2; // 0.05e18

        // First partial redeem
        uint256 balBefore = IERC20(collateral).balanceOf(aliceAddr);
        vm.prank(aliceAddr);
        vault.redeemLong(half);
        uint256 balMid = IERC20(collateral).balanceOf(aliceAddr);
        uint256 firstPayout = balMid - balBefore;

        // Second partial redeem
        vm.prank(aliceAddr);
        vault.redeemLong(half);
        uint256 balAfter = IERC20(collateral).balanceOf(aliceAddr);
        uint256 secondPayout = balAfter - balMid;

        uint256 totalPayout = firstPayout + secondPayout;

        // Total from two halves should equal full preview (±1 wei rounding)
        assertLe(
            totalPayout, expectedFullPayout,
            "Split payout should not exceed full preview"
        );
        assertGe(
            totalPayout, expectedFullPayout - 1,
            "Split payout within 1 wei of full preview"
        );

        assertEq(vault.balanceOf(aliceAddr, LONG), 0, "LONG balance should be 0 after two partial redeems");

        console.log("=== PARTIAL REDEMPTION ORDERING ===");
        console.log("Expected full payout:", expectedFullPayout);
        console.log("First half payout:", firstPayout);
        console.log("Second half payout:", secondPayout);
        console.log("Total split payout:", totalPayout);
    }
}
