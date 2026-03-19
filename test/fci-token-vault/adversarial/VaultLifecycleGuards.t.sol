// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

import {FCIFixture} from "../fixtures/FCIFixture.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {VaultAlreadySettled} from "@fci-token-vault/storage/OraclePayoffStorage.sol";

/// @title VaultLifecycleGuards — Layer 3 adversarial tests
/// @dev Validates settled-state guards and full state-machine traversal
///      using real FCI hook + V4 pool (no stubs).
contract VaultLifecycleGuardsTest is FCIFixture {
    address depositorAddr;
    address lpAddr;
    address jitAddr;
    address swapperAddr;

    uint256 constant DEPOSIT_AMOUNT = 0.1e18;
    uint256 constant LP_CAPITAL = 1e18;
    uint256 constant ROUNDS = 3;

    function setUp() public {
        _deployFixture();

        Vm.Wallet memory w;
        w = vm.createWallet("depositor");
        depositorAddr = w.addr;
        w = vm.createWallet("lp");
        lpAddr = w.addr;
        w = vm.createWallet("jit");
        jitAddr = w.addr;
        w = vm.createWallet("swapper");
        swapperAddr = w.addr;

        _setupLP(lpAddr);
        _setupLP(jitAddr);
        _setupSwapper(swapperAddr);
        seedBalance(depositorAddr);
    }

    // ═══════════════════════════════════════════════════════════
    // Internal helpers
    // ═══════════════════════════════════════════════════════════

    /// @dev Run the common prefix: deposit + JIT rounds + poke + settle.
    function _depositAndSettle() internal {
        _depositToVault(depositorAddr, DEPOSIT_AMOUNT);

        for (uint256 i; i < ROUNDS; ++i) {
            _deadline = block.timestamp + 1;
            _runJitRound(
                lpAddr, LP_CAPITAL,
                jitAddr, JIT_CAPITAL,
                true,
                int256(TRADE_SIZE)
            );
        }

        _settleVault();
    }

    // ═══════════════════════════════════════════════════════════
    // Test 1: deposit after settle reverts
    // ═══════════════════════════════════════════════════════════

    /// @dev Design Decision 7: deposit() must revert once settled.
    function test_deposit_after_settle_reverts() public {
        _depositAndSettle();
        assertTrue(vault.isSettled(), "precondition: vault should be settled");

        // Attempt a second deposit — must revert
        vm.startPrank(depositorAddr);
        IERC20(Currency.unwrap(currency1)).approve(address(vault), DEPOSIT_AMOUNT);
        vm.expectRevert(VaultAlreadySettled.selector);
        vault.deposit(DEPOSIT_AMOUNT);
        vm.stopPrank();
    }

    // ═══════════════════════════════════════════════════════════
    // Test 2: settle twice reverts
    // ═══════════════════════════════════════════════════════════

    /// @dev Calling settle() a second time must revert with VaultAlreadySettled.
    function test_settle_twice_reverts() public {
        _depositAndSettle();
        assertTrue(vault.isSettled(), "precondition: vault should be settled");

        // Second settle — must revert
        vm.expectRevert(VaultAlreadySettled.selector);
        vault.settle();
    }

    // ═══════════════════════════════════════════════════════════
    // Test 3: full lifecycle state transitions
    // ═══════════════════════════════════════════════════════════

    /// @dev Complete state-machine traversal verifying isSettled() at every step.
    function test_full_lifecycle_state_transitions() public {
        // ─── deposit ─────────────────────────────────────────
        _depositToVault(depositorAddr, DEPOSIT_AMOUNT);
        assertFalse(vault.isSettled(), "isSettled should be false after deposit");

        // ─── JIT rounds + poke ───────────────────────────────
        for (uint256 i; i < ROUNDS; ++i) {
            _deadline = block.timestamp + 1;
            _runJitRound(
                lpAddr, LP_CAPITAL,
                jitAddr, JIT_CAPITAL,
                true,
                int256(TRADE_SIZE)
            );
            assertFalse(vault.isSettled(), "isSettled should be false during JIT rounds");
        }

        // ─── settle ──────────────────────────────────────────
        _settleVault();
        assertTrue(vault.isSettled(), "isSettled should be true after settle");

        // ─── redeemLong ──────────────────────────────────────
        vm.prank(depositorAddr);
        vault.redeemLong(DEPOSIT_AMOUNT);
        assertTrue(vault.isSettled(), "isSettled should remain true after redeemLong");

        // ─── redeemShort ─────────────────────────────────────
        vm.prank(depositorAddr);
        vault.redeemShort(DEPOSIT_AMOUNT);
        assertTrue(vault.isSettled(), "isSettled should remain true after redeemShort");

        // ─── final invariant ─────────────────────────────────
        assertEq(vault.totalDeposited(), 0, "totalDeposited should be 0 after full redemption");
    }
}
