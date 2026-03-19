// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {TokenPair, mockPair, existingPair} from "@utils/TokenPair.sol";

contract TokenPairTest is Test {
    function test_existingPair_sortsTokens() public pure {
        address a = address(0xBBBB);
        address b = address(0xAAAA);
        TokenPair memory pair = existingPair(a, b);
        assertEq(pair.token0, b);
        assertEq(pair.token1, a);
    }

    function test_existingPair_alreadySorted() public pure {
        address a = address(0xAAAA);
        address b = address(0xBBBB);
        TokenPair memory pair = existingPair(a, b);
        assertEq(pair.token0, a);
        assertEq(pair.token1, b);
    }

    function test_existingPair_revertsOnIdentical() public {
        address a = address(0xAAAA);
        vm.expectRevert("TokenPair: identical addresses");
        this.callExistingPair(a, a);
    }

    /// @dev External wrapper so vm.expectRevert can catch the revert at a lower depth.
    function callExistingPair(address a, address b) external pure returns (TokenPair memory) {
        return existingPair(a, b);
    }

    function test_mockPair_deploysAndSorts() public {
        uint256 supply = 1_000_000e18;
        TokenPair memory pair = mockPair(supply, address(this));
        assertTrue(pair.token0 < pair.token1, "not sorted");
        assertTrue(pair.token0 != address(0), "token0 is zero");
        assertTrue(pair.token1 != address(0), "token1 is zero");
    }

    function test_mockPair_mintsSupplyToRecipient() public {
        uint256 supply = 500e18;
        address recipient = makeAddr("recipient");
        TokenPair memory pair = mockPair(supply, recipient);
        assertEq(MockERC20(pair.token0).balanceOf(recipient), supply);
        assertEq(MockERC20(pair.token1).balanceOf(recipient), supply);
    }
}
