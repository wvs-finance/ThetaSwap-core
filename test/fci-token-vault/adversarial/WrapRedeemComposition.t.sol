// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

import {FacetDeployer} from "../fixtures/FacetDeployer.sol";
import {DeltaPlusStub} from "../fixtures/DeltaPlusStub.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {V4_ADAPTER_SLOT} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {ERC6909InsufficientBalance} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

// ═══════════════════════════════════════════════════════════════════════
// Layer 3 — Wrap/redeem composition adversarial tests
// ═══════════════════════════════════════════════════════════════════════

contract WrapRedeemCompositionTest is Test {
    FacetDeployer vault;
    DeltaPlusStub stub;
    MockERC20 collateral;
    address alice = makeAddr("alice");
    address bob = makeAddr("bob");

    uint256 constant Q96 = SqrtPriceLibrary.Q96;
    uint256 constant LONG = 0;
    uint256 constant SHORT = 1;
    uint256 constant DEPOSIT = 100e18;

    function setUp() public {
        collateral = new MockERC20("USDC", "USDC", 18);
        stub = new DeltaPlusStub();
        vault = new FacetDeployer();
        PoolKey memory dummyKey;
        vault.init(
            address(collateral),
            0,
            uint160(Q96),
            block.timestamp + 30 days,
            V4_ADAPTER_SLOT,
            address(stub),
            dummyKey,
            false
        );
        vault.initWrappedTokenId(LONG);

        collateral.mint(alice, 1000e18);
        vm.prank(alice);
        collateral.approve(address(vault), type(uint256).max);
    }

    function _pokeAndSettle() internal {
        stub.setDeltaPlus(type(uint128).max - 1);
        vault.poke();
        vm.warp(block.timestamp + 30 days + 1);
        vault.settle();
    }

    /// @dev Full flow: Alice deposits → wraps LONG → tokens transferred to Bob
    ///      (simulated via mintERC6909) → settle → Bob redeems LONG.
    function test_deposit_wrap_transfer_unwrap_redeem() public {
        // Alice deposits → gets LONG + SHORT ERC-6909
        vm.prank(alice);
        vault.deposit(DEPOSIT);
        assertEq(vault.erc6909BalanceOf(alice, LONG), DEPOSIT);
        assertEq(vault.erc6909BalanceOf(alice, SHORT), DEPOSIT);

        // Alice wraps LONG to ERC-20
        vm.prank(alice);
        vault.wrap(DEPOSIT);
        assertEq(vault.erc6909BalanceOf(alice, LONG), 0);
        assertEq(vault.erc20BalanceOf(alice), DEPOSIT);

        // Simulate transfer: give Bob LONG ERC-6909 directly
        // (represents Alice transferring wrapped ERC-20 to Bob who unwraps)
        vault.mintERC6909(bob, LONG, DEPOSIT);

        // Settle vault
        _pokeAndSettle();

        // Bob redeems LONG → gets USDC payout
        uint256 expectedPayout = vault.previewLongPayout(DEPOSIT);
        uint256 bobBalBefore = collateral.balanceOf(bob);

        vm.prank(bob);
        vault.redeemLong(DEPOSIT);

        uint256 bobBalAfter = collateral.balanceOf(bob);
        assertEq(bobBalAfter - bobBalBefore, expectedPayout, "Bob payout mismatch");
        assertGt(expectedPayout, 0, "Expected non-zero payout");
        assertEq(vault.erc6909BalanceOf(bob, LONG), 0, "Bob LONG should be 0 after redeem");
    }

    /// @dev Wrap then unwrap is a no-op on balances.
    function test_wrap_unwrap_roundtrip() public {
        vm.prank(alice);
        vault.deposit(DEPOSIT);

        uint256 longBefore = vault.erc6909BalanceOf(alice, LONG);
        assertEq(longBefore, DEPOSIT);

        // Wrap
        vm.prank(alice);
        vault.wrap(DEPOSIT);
        assertEq(vault.erc6909BalanceOf(alice, LONG), 0);
        assertEq(vault.erc20BalanceOf(alice), DEPOSIT);

        // Unwrap
        vm.prank(alice);
        vault.unwrap(DEPOSIT);
        assertEq(vault.erc6909BalanceOf(alice, LONG), DEPOSIT, "LONG ERC-6909 not restored");
        assertEq(vault.erc20BalanceOf(alice), 0, "ERC-20 balance not zero after unwrap");
    }

    /// @dev Redeem with wrapped tokens fails: ERC-6909 LONG balance is 0
    ///      because tokens are in ERC-20 form.
    function test_redeem_with_wrapped_tokens_fails() public {
        vm.prank(alice);
        vault.deposit(DEPOSIT);

        // Wrap all LONG → ERC-6909 LONG balance becomes 0
        vm.prank(alice);
        vault.wrap(DEPOSIT);
        assertEq(vault.erc6909BalanceOf(alice, LONG), 0);

        // Settle
        _pokeAndSettle();

        // Attempt to redeem LONG → reverts (no ERC-6909 balance)
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(
                ERC6909InsufficientBalance.selector,
                alice,  // sender
                0,      // balance
                DEPOSIT, // needed
                LONG    // id
            )
        );
        vault.redeemLong(DEPOSIT);
    }
}
