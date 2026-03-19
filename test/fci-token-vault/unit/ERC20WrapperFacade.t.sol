// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    ERC20WrapperFacade,
    getWrappedTokenId,
    WRAPPER_STORAGE_POSITION_SEED,
    InsufficientERC6909Balance
} from "@fci-token-vault/tokens/ERC20WrapperFacade.sol";
import {erc6909Mint, getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {getERC20Storage} from "@fci-token-vault/modules/dependencies/ERC20Lib.sol";

/// @dev Harness that contains both wrapper and helper logic in one contract
///      so diamond storage reads/writes happen in the same context.
contract WrapperHarness is ERC20WrapperFacade {
    function initTokenId(uint256 id) external {
        bytes32 slot = bytes32(WRAPPER_STORAGE_POSITION_SEED);
        assembly {
            sstore(slot, id)
        }
    }

    function mintERC6909(address to, uint256 id, uint256 amount) external {
        erc6909Mint(to, id, amount);
    }

    function erc6909BalanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }

    function erc20BalanceOf(address owner) external view returns (uint256) {
        return getERC20Storage().balanceOf[owner];
    }
}

contract ERC20WrapperFacadeTest is Test {
    WrapperHarness harness;
    uint256 constant TOKEN_ID = 0; // LONG

    function setUp() public {
        harness = new WrapperHarness();
        harness.initTokenId(TOKEN_ID);
    }

    /// @dev INV-W1: wrap converts ERC-6909 balance to ERC-20 balance 1:1
    function test_wrap_converts_6909_to_erc20() public {
        harness.mintERC6909(address(harness), TOKEN_ID, 100e6);

        vm.prank(address(harness));
        harness.wrap(100e6);

        assertEq(harness.erc20BalanceOf(address(harness)), 100e6);
        assertEq(harness.erc6909BalanceOf(address(harness), TOKEN_ID), 0);
    }

    /// @dev INV-W2: unwrap converts ERC-20 balance back to ERC-6909 1:1
    function test_unwrap_converts_erc20_to_6909() public {
        harness.mintERC6909(address(harness), TOKEN_ID, 100e6);
        vm.prank(address(harness));
        harness.wrap(100e6);

        vm.prank(address(harness));
        harness.unwrap(50e6);

        assertEq(harness.erc20BalanceOf(address(harness)), 50e6);
        assertEq(harness.erc6909BalanceOf(address(harness), TOKEN_ID), 50e6);
    }

    /// @dev INV-W3: wrap with insufficient ERC-6909 balance reverts
    function test_wrap_insufficient_6909_reverts() public {
        vm.prank(address(harness));
        vm.expectRevert();
        harness.wrap(100e6);
    }
}
