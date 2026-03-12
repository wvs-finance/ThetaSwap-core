// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    reentrancyGuardEnter,
    reentrancyGuardExit,
    ReentrancyGuardReentrant
} from "@fci-token-vault/modules/dependencies/ReentrancyLib.sol";

contract ReentrancyTarget {
    function enter() external { reentrancyGuardEnter(); }
    function exit() external { reentrancyGuardExit(); }
    function enterTwice() external {
        reentrancyGuardEnter();
        reentrancyGuardEnter(); // should revert
    }
}

contract ReentrancyLibTest is Test {
    ReentrancyTarget target;

    function setUp() public { target = new ReentrancyTarget(); }

    function test_enter_exit_succeeds() public {
        target.enter();
        target.exit();
    }

    function test_double_enter_reverts() public {
        vm.expectRevert(ReentrancyGuardReentrant.selector);
        target.enterTwice();
    }

    function test_reentry_after_exit_succeeds() public {
        target.enter();
        target.exit();
        target.enter();
        target.exit();
    }
}
