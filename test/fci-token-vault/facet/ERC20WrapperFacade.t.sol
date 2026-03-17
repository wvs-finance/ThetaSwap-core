// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {FacetDeployer} from "../fixtures/FacetDeployer.sol";
import {InsufficientERC6909Balance} from "@fci-token-vault/tokens/ERC20WrapperFacade.sol";
import {ERC20InsufficientBalance} from "@fci-token-vault/modules/dependencies/ERC20Lib.sol";

contract ERC20WrapperFacadeTest is Test {
    FacetDeployer vault;
    address alice = makeAddr("alice");
    uint256 constant TOKEN_ID = 0; // LONG
    uint256 constant AMOUNT = 100e18;

    function setUp() public {
        vault = new FacetDeployer();
        vault.initWrappedTokenId(TOKEN_ID);
        // Mint ERC-6909 tokens directly to alice (bypassing deposit)
        vault.mintERC6909(alice, TOKEN_ID, AMOUNT);
    }

    function test_wrap_converts_6909_to_erc20() public {
        vm.prank(alice);
        vault.wrap(AMOUNT);

        assertEq(vault.erc6909BalanceOf(alice, TOKEN_ID), 0);
        assertEq(vault.erc20BalanceOf(alice), AMOUNT);
    }

    function test_unwrap_converts_erc20_to_6909() public {
        vm.prank(alice);
        vault.wrap(AMOUNT);

        vm.prank(alice);
        vault.unwrap(AMOUNT / 2);

        assertEq(vault.erc6909BalanceOf(alice, TOKEN_ID), AMOUNT / 2);
        assertEq(vault.erc20BalanceOf(alice), AMOUNT / 2);
    }

    function test_wrap_insufficient_balance_reverts() public {
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(InsufficientERC6909Balance.selector, alice, AMOUNT, AMOUNT * 2, TOKEN_ID)
        );
        vault.wrap(AMOUNT * 2);
    }

    function test_unwrap_insufficient_erc20_reverts() public {
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(ERC20InsufficientBalance.selector, alice, 0, AMOUNT)
        );
        vault.unwrap(AMOUNT);
    }
}
