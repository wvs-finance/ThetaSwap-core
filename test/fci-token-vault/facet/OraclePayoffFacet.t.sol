// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {FacetDeployer} from "../fixtures/FacetDeployer.sol";
import {DeltaPlusStub} from "../fixtures/DeltaPlusStub.sol";
import {V4_ADAPTER_SLOT} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {ZeroAmount} from "@fci-token-vault/storage/CustodianStorage.sol";
import {
    VaultNotExpired,
    VaultAlreadySettled,
    VaultAlreadySettledPoke,
    VaultNotSettled
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

contract OraclePayoffFacetTest is Test {
    FacetDeployer vault;
    MockERC20 collateral;
    DeltaPlusStub stub;
    address alice = makeAddr("alice");
    uint256 constant DEPOSIT = 100e18;
    uint256 constant Q96 = SqrtPriceLibrary.Q96;

    // Mirror events from OraclePayoffFacet
    event HWMUpdated(uint160 newHwmSqrtPrice, uint160 currentSqrtPrice);
    event OracleSettlement(uint256 longPayoutPerToken, uint160 finalHWM);
    event RedeemLong(address indexed redeemer, uint256 amount, uint256 payout);
    event RedeemShort(address indexed redeemer, uint256 amount, uint256 payout);

    function setUp() public {
        vault = new FacetDeployer();
        collateral = new MockERC20("Collateral", "COL", 18);
        stub = new DeltaPlusStub();

        PoolKey memory dummyKey;
        vault.init(
            address(collateral),
            0, // no cap
            uint160(Q96), // strike = 1.0
            block.timestamp + 30 days,
            V4_ADAPTER_SLOT,
            address(stub),
            dummyKey,
            false
        );

        // Fund and approve alice
        collateral.mint(alice, 1000e18);
        vm.prank(alice);
        collateral.approve(address(vault), type(uint256).max);

        // Deposit so alice has LONG + SHORT tokens
        vm.prank(alice);
        vault.deposit(DEPOSIT);
    }

    // ── Helper ────────────────────────────────────────────────────────

    function _pokeAndSettle(uint128 deltaPlus) internal {
        stub.setDeltaPlus(deltaPlus);
        vault.poke();
        vm.warp(block.timestamp + 30 days);
        vault.settle();
    }

    // ── 1. poke emits HWMUpdated ──────────────────────────────────────

    function test_poke_emits_hwm_updated() public {
        stub.setDeltaPlus(1e36);
        vm.expectEmit(false, false, false, false);
        emit HWMUpdated(0, 0); // check topic only (event emitted)
        vault.poke();

        (, uint160 hwm,,,) = vault.getVaultStorage();
        assertGt(hwm, 0, "HWM should be non-zero after poke");
    }

    // ── 2. poke updates HWM monotonically ─────────────────────────────

    function test_poke_updates_hwm_monotonically() public {
        stub.setDeltaPlus(1e36);
        vault.poke();
        (, uint160 hwmHigh,,,) = vault.getVaultStorage();

        // Poke with a lower value
        stub.setDeltaPlus(1e30);
        vault.poke();
        (, uint160 hwmAfter,,,) = vault.getVaultStorage();

        assertEq(hwmAfter, hwmHigh, "HWM should stay at higher value");
    }

    // ── 3. poke zero delta-plus leaves HWM unchanged ──────────────────

    function test_poke_zero_delta_plus_hwm_unchanged() public {
        stub.setDeltaPlus(0);
        vault.poke();
        (, uint160 hwm,,,) = vault.getVaultStorage();
        assertEq(hwm, 0, "HWM should remain 0 when delta-plus is 0");
    }

    // ── 4. settle emits OracleSettlement ──────────────────────────────

    function test_settle_emits_settlement() public {
        stub.setDeltaPlus(1e36);
        vault.poke();
        vm.warp(block.timestamp + 30 days);

        vm.expectEmit(false, false, false, false);
        emit OracleSettlement(0, 0);
        vault.settle();

        assertTrue(vault.isSettled(), "Vault should be settled");
    }

    // ── 5. payoffRatio sums to Q96 ───────────────────────────────────

    function test_payoffRatio_sums_to_Q96() public {
        _pokeAndSettle(1e36);
        (uint256 longPer, uint256 shortPer) = vault.payoffRatio();
        assertEq(longPer + shortPer, Q96, "long + short should equal Q96");
    }

    // ── 6. redeemLong burns and pays ─────────────────────────────────

    function test_redeemLong_burns_and_pays() public {
        _pokeAndSettle(1e36);

        uint256 previewPayout = vault.previewLongPayout(DEPOSIT);
        uint256 balBefore = collateral.balanceOf(alice);
        uint128 totalBefore = vault.totalDeposited();

        vm.expectEmit(true, false, false, true);
        emit RedeemLong(alice, DEPOSIT, previewPayout);

        vm.prank(alice);
        vault.redeemLong(DEPOSIT);

        assertEq(vault.erc6909BalanceOf(alice, LONG), 0, "LONG balance should be 0");
        assertEq(vault.erc6909BalanceOf(alice, SHORT), DEPOSIT, "SHORT balance unchanged");
        assertEq(collateral.balanceOf(alice) - balBefore, previewPayout, "USDC payout mismatch");
        assertEq(vault.totalDeposited(), totalBefore - uint128(previewPayout), "totalDeposits decreased");
    }

    // ── 7. redeemShort burns and pays ────────────────────────────────

    function test_redeemShort_burns_and_pays() public {
        _pokeAndSettle(1e36);

        uint256 previewPayout = vault.previewShortPayout(DEPOSIT);
        uint256 balBefore = collateral.balanceOf(alice);

        vm.expectEmit(true, false, false, true);
        emit RedeemShort(alice, DEPOSIT, previewPayout);

        vm.prank(alice);
        vault.redeemShort(DEPOSIT);

        assertEq(vault.erc6909BalanceOf(alice, SHORT), 0, "SHORT balance should be 0");
        assertEq(vault.erc6909BalanceOf(alice, LONG), DEPOSIT, "LONG balance unchanged");
        assertEq(collateral.balanceOf(alice) - balBefore, previewPayout, "USDC payout mismatch");
    }

    // ── 8. previewLongPayout matches actual ──────────────────────────

    function test_previewLongPayout_matches_actual() public {
        _pokeAndSettle(1e36);

        uint256 expected = vault.previewLongPayout(DEPOSIT);
        uint256 balBefore = collateral.balanceOf(alice);

        vm.prank(alice);
        vault.redeemLong(DEPOSIT);

        uint256 actual = collateral.balanceOf(alice) - balBefore;
        assertEq(actual, expected, "preview should match actual LONG payout");
    }

    // ── 9. previewShortPayout matches actual ─────────────────────────

    function test_previewShortPayout_matches_actual() public {
        _pokeAndSettle(1e36);

        uint256 expected = vault.previewShortPayout(DEPOSIT);
        uint256 balBefore = collateral.balanceOf(alice);

        vm.prank(alice);
        vault.redeemShort(DEPOSIT);

        uint256 actual = collateral.balanceOf(alice) - balBefore;
        assertEq(actual, expected, "preview should match actual SHORT payout");
    }

    // ── 10. settle before expiry reverts ─────────────────────────────

    function test_settle_before_expiry_reverts() public {
        vm.expectRevert(VaultNotExpired.selector);
        vault.settle();
    }

    // ── 11. redeemLong before settle reverts ─────────────────────────

    function test_redeemLong_before_settle_reverts() public {
        vm.expectRevert(VaultNotSettled.selector);
        vm.prank(alice);
        vault.redeemLong(DEPOSIT);
    }

    // ── 12. redeemShort before settle reverts ────────────────────────

    function test_redeemShort_before_settle_reverts() public {
        vm.expectRevert(VaultNotSettled.selector);
        vm.prank(alice);
        vault.redeemShort(DEPOSIT);
    }

    // ── 13. poke after settle reverts ────────────────────────────────

    function test_poke_after_settle_reverts() public {
        _pokeAndSettle(1e36);
        vm.expectRevert(VaultAlreadySettledPoke.selector);
        vault.poke();
    }

    // ── 14. previewLongPayout before settle reverts ──────────────────

    function test_previewLongPayout_before_settle_reverts() public {
        vm.expectRevert(VaultNotSettled.selector);
        vault.previewLongPayout(DEPOSIT);
    }

    // ── 15. previewShortPayout before settle reverts ─────────────────

    function test_previewShortPayout_before_settle_reverts() public {
        vm.expectRevert(VaultNotSettled.selector);
        vault.previewShortPayout(DEPOSIT);
    }

    // ── 16. payoffRatio before settle reverts ────────────────────────

    function test_payoffRatio_before_settle_reverts() public {
        vm.expectRevert(VaultNotSettled.selector);
        vault.payoffRatio();
    }

    // ── 17. redeemLong zero reverts ──────────────────────────────────

    function test_redeemLong_zero_reverts() public {
        _pokeAndSettle(1e36);
        vm.expectRevert(ZeroAmount.selector);
        vm.prank(alice);
        vault.redeemLong(0);
    }

    // ── 18. redeemShort zero reverts ─────────────────────────────────

    function test_redeemShort_zero_reverts() public {
        _pokeAndSettle(1e36);
        vm.expectRevert(ZeroAmount.selector);
        vm.prank(alice);
        vault.redeemShort(0);
    }
}
