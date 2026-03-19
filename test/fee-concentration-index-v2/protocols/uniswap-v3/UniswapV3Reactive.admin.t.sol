// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {UniswapV3Reactive} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol";
import {OwnerUnauthorizedAccount} from
    "@fee-concentration-index-v2/modules/dependencies/LibOwner.sol";
import {NoFunds, MigrationTransferFailed, FundsMigrated} from
    "@fee-concentration-index-v2/modules/dependencies/AdminLib.sol";

/// @dev Helper contract that rejects ETH — used to test MigrationTransferFailed
contract RejectETH {}

contract UniswapV3ReactiveAdminTest is Test {
    UniswapV3Reactive reactive;

    address owner = address(this);
    address callbackAddr = makeAddr("callback");
    address notOwner = makeAddr("notOwner");

    function setUp() public {
        // Mock SystemContract so constructor doesn't revert
        address systemContract = 0x0000000000000000000000000000000000fffFfF;
        vm.etch(systemContract, hex"00");
        vm.mockCall(systemContract, bytes(""), abi.encode(true));

        reactive = new UniswapV3Reactive{value: 1 ether}(callbackAddr);
    }

    // ── setCallback ──

    function test_setCallback_updatesReference() public {
        address newCallback = makeAddr("newCallback");
        reactive.setCallback(newCallback);
        assertEq(reactive.callback(), newCallback);
    }

    function test_setCallback_emitsCallbackUpdated() public {
        address newCallback = makeAddr("newCallback");
        vm.expectEmit(true, true, false, false);
        emit UniswapV3Reactive.CallbackUpdated(callbackAddr, newCallback);
        reactive.setCallback(newCallback);
    }

    function test_setCallback_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        reactive.setCallback(makeAddr("newCallback"));
    }

    function test_setCallback_revertsIfZeroAddress() public {
        vm.expectRevert(UniswapV3Reactive.ZeroAddress.selector);
        reactive.setCallback(address(0));
    }

    // ── migrateFunds ──

    function test_migrateFunds_sendsAllETH() public {
        address payable recipient = payable(makeAddr("recipient"));
        vm.deal(address(reactive), 1 ether);
        reactive.migrateFunds(recipient);
        assertEq(address(reactive).balance, 0);
        assertEq(recipient.balance, 1 ether);
    }

    function test_migrateFunds_emitsFundsMigrated() public {
        vm.deal(address(reactive), 1 ether);
        address payable recipient = payable(makeAddr("recipient"));
        vm.expectEmit(true, false, false, true);
        emit FundsMigrated(recipient, 1 ether);
        reactive.migrateFunds(recipient);
    }

    function test_migrateFunds_revertsIfNotOwner() public {
        vm.deal(address(reactive), 1 ether);
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        reactive.migrateFunds(payable(makeAddr("recipient")));
    }

    function test_migrateFunds_revertsIfNoFunds() public {
        vm.deal(address(reactive), 0);
        vm.expectRevert(NoFunds.selector);
        reactive.migrateFunds(payable(makeAddr("recipient")));
    }

    function test_migrateFunds_revertsIfRecipientRejectsETH() public {
        vm.deal(address(reactive), 1 ether);
        RejectETH rejector = new RejectETH();
        vm.expectRevert(MigrationTransferFailed.selector);
        reactive.migrateFunds(payable(address(rejector)));
    }

    // ── transferOwnership ──

    function test_transferOwnership_updatesOwner() public {
        address newOwner = makeAddr("newOwner");
        reactive.transferOwnership(newOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        reactive.setCallback(makeAddr("x"));
        vm.prank(newOwner);
        reactive.setCallback(makeAddr("x"));
    }

    function test_transferOwnership_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        reactive.transferOwnership(notOwner);
    }

    function test_transferOwnership_toZeroRenouncesOwnership() public {
        reactive.transferOwnership(address(0));
        vm.expectRevert(); // OwnerAlreadyRenounced
        reactive.transferOwnership(makeAddr("x"));
    }
}
