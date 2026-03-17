// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

import {FCIFixture} from "../fixtures/FCIFixture.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/CollateralCustodianMod.sol";

contract SingleUserLifecycleTest is FCIFixture {
    address aliceAddr;
    uint256 alicePk;
    address lpAddr;
    uint256 lpPk;
    address jitAddr;
    uint256 jitPk;
    address swapperAddr;
    uint256 swapperPk;

    uint256 constant DEPOSIT_AMOUNT = 0.1e18;
    uint256 constant LP_CAPITAL = 1e18;
    uint256 constant ROUNDS = 3;

    function setUp() public {
        _deployFixture();

        // Create wallets
        Vm.Wallet memory w;
        w = vm.createWallet("alice");
        aliceAddr = w.addr; alicePk = w.privateKey;
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
        seedBalance(aliceAddr); // for collateral
    }

    function test_single_user_full_lifecycle() public {
        // ─── 1. Alice deposits collateral ───────────────────────
        _depositToVault(aliceAddr, DEPOSIT_AMOUNT);

        assertEq(
            vault.totalDeposited(), DEPOSIT_AMOUNT,
            "totalDeposited should equal deposit"
        );
        assertEq(
            vault.balanceOf(aliceAddr, LONG), DEPOSIT_AMOUNT,
            "LONG balance should equal deposit"
        );
        assertEq(
            vault.balanceOf(aliceAddr, SHORT), DEPOSIT_AMOUNT,
            "SHORT balance should equal deposit"
        );

        // ─── 2. Run 3 JIT rounds ───────────────────────────────
        for (uint256 i; i < ROUNDS; ++i) {
            // Refresh POSM deadline after each epoch warp
            _deadline = block.timestamp + 1;
            _runJitRound(
                lpAddr, LP_CAPITAL,
                jitAddr, JIT_CAPITAL,
                true,               // zeroForOne
                int256(TRADE_SIZE)   // exactInput swap amount
            );
            assertFalse(vault.isSettled(), "vault should not be settled mid-lifecycle");
        }

        // ─── 3. Check HWM updated ──────────────────────────────
        (, uint160 hwm,,,) = vault.getVaultStorage();
        assertGt(uint256(hwm), 0, "HWM should be > 0 after JIT rounds");

        // ─── 4. Settle ─────────────────────────────────────────
        _settleVault();
        assertTrue(vault.isSettled(), "vault should be settled after _settleVault");

        // ─── 5. Verify view functions ───────────────────────────
        (uint256 longPerToken, uint256 shortPerToken) = vault.payoffRatio();
        uint256 Q96 = SqrtPriceLibrary.Q96;
        assertEq(longPerToken + shortPerToken, Q96, "payoff ratio should sum to Q96");
        assertGt(longPerToken, 0, "longPerToken should be > 0 (JIT generated positive payoff)");

        uint256 expectedLongPayout = vault.previewLongPayout(DEPOSIT_AMOUNT);
        uint256 expectedShortPayout = vault.previewShortPayout(DEPOSIT_AMOUNT);
        assertGt(expectedLongPayout, 0, "previewLongPayout should be > 0");

        // ─── 6. Redeem LONG ────────────────────────────────────
        address collateral = Currency.unwrap(currency1);
        uint256 balBefore = IERC20(collateral).balanceOf(aliceAddr);

        vm.prank(aliceAddr);
        vault.redeemLong(DEPOSIT_AMOUNT);

        uint256 balAfterLong = IERC20(collateral).balanceOf(aliceAddr);
        uint256 longPayout = balAfterLong - balBefore;
        assertEq(longPayout, expectedLongPayout, "LONG payout should match preview");
        assertEq(vault.balanceOf(aliceAddr, LONG), 0, "LONG tokens should be burned");

        // ─── 7. Redeem SHORT ───────────────────────────────────
        vm.prank(aliceAddr);
        vault.redeemShort(DEPOSIT_AMOUNT);

        uint256 balAfterShort = IERC20(collateral).balanceOf(aliceAddr);
        uint256 shortPayout = balAfterShort - balAfterLong;
        assertEq(shortPayout, expectedShortPayout, "SHORT payout should match preview");
        assertEq(vault.balanceOf(aliceAddr, SHORT), 0, "SHORT tokens should be burned");

        // ─── 8. Conservation ───────────────────────────────────
        uint256 totalPayout = longPayout + shortPayout;
        assertLe(totalPayout, DEPOSIT_AMOUNT, "total payout should not exceed deposit");
        assertGe(totalPayout, DEPOSIT_AMOUNT - 1, "total payout should be within 1 wei of deposit");

        // ─── 9. Final state ────────────────────────────────────
        assertEq(vault.totalDeposited(), 0, "totalDeposited should be 0 after full redemption");

        console.log("=== SINGLE USER LIFECYCLE ===");
        console.log("LONG payout:", longPayout);
        console.log("SHORT payout:", shortPayout);
        console.log("Total payout:", totalPayout);
        console.log("HWM:", uint256(hwm));
    }
}
