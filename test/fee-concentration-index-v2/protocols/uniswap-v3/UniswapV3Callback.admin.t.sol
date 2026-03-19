// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {UniswapV3Callback} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol";
import {OwnerUnauthorizedAccount} from
    "@fee-concentration-index-v2/modules/dependencies/LibOwner.sol";
import {NoFunds, MigrationTransferFailed, FundsMigrated} from
    "@fee-concentration-index-v2/modules/dependencies/AdminLib.sol";

/// @dev Helper contract that rejects ETH — used to test MigrationTransferFailed
contract RejectETH {}

contract UniswapV3CallbackAdminTest is Test {
    UniswapV3Callback callback;

    address owner = address(this);
    address fci = makeAddr("fci");
    address callbackProxy = makeAddr("callbackProxy");
    address rvmId = makeAddr("rvmId");
    address notOwner = makeAddr("notOwner");

    function setUp() public {
        callback = new UniswapV3Callback{value: 1 ether}(fci, callbackProxy, rvmId);
    }

    // ── setFci ──

    function test_setFci_updatesReference() public {
        address newFci = makeAddr("newFci");
        callback.setFci(newFci);
        assertEq(address(callback.fci()), newFci);
    }

    function test_setFci_emitsFciUpdated() public {
        address newFci = makeAddr("newFci");
        vm.expectEmit(true, true, false, false);
        emit UniswapV3Callback.FciUpdated(fci, newFci);
        callback.setFci(newFci);
    }

    function test_setFci_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.setFci(makeAddr("newFci"));
    }

    function test_setFci_revertsIfZeroAddress() public {
        vm.expectRevert(UniswapV3Callback.ZeroAddress.selector);
        callback.setFci(address(0));
    }

    // ── migrateFunds ──

    function test_migrateFunds_sendsAllETH() public {
        address payable recipient = payable(makeAddr("recipient"));
        uint256 balanceBefore = address(callback).balance;
        assertEq(balanceBefore, 1 ether);
        callback.migrateFunds(recipient);
        assertEq(address(callback).balance, 0);
        assertEq(recipient.balance, 1 ether);
    }

    function test_migrateFunds_emitsFundsMigrated() public {
        address payable recipient = payable(makeAddr("recipient"));
        vm.expectEmit(true, false, false, true);
        emit FundsMigrated(recipient, 1 ether);
        callback.migrateFunds(recipient);
    }

    function test_migrateFunds_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.migrateFunds(payable(makeAddr("recipient")));
    }

    function test_migrateFunds_revertsIfNoFunds() public {
        callback.migrateFunds(payable(makeAddr("drain")));
        vm.expectRevert(NoFunds.selector);
        callback.migrateFunds(payable(makeAddr("recipient")));
    }

    function test_migrateFunds_revertsIfRecipientRejectsETH() public {
        RejectETH rejector = new RejectETH();
        vm.expectRevert(MigrationTransferFailed.selector);
        callback.migrateFunds(payable(address(rejector)));
    }

    // ── transferOwnership ──

    function test_transferOwnership_updatesOwner() public {
        address newOwner = makeAddr("newOwner");
        callback.transferOwnership(newOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.setFci(makeAddr("x"));
        vm.prank(newOwner);
        callback.setFci(makeAddr("x"));
    }

    function test_transferOwnership_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.transferOwnership(notOwner);
    }

    function test_transferOwnership_toZeroRenouncesOwnership() public {
        callback.transferOwnership(address(0));
        vm.expectRevert(); // OwnerAlreadyRenounced
        callback.transferOwnership(makeAddr("x"));
    }

    // ── existing admin: setRvmId still works ──

    function test_setRvmId_stillWorksWithLibOwner() public {
        address newRvm = makeAddr("newRvm");
        callback.setRvmId(newRvm);
        assertEq(callback.rvmId(), newRvm);
    }

    function test_setRvmId_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.setRvmId(makeAddr("x"));
    }

    // ── existing admin: setAuthorized still works ──

    function test_setAuthorized_stillWorksWithLibOwner() public {
        address newCaller = makeAddr("newCaller");
        callback.setAuthorized(newCaller, true);
        assertTrue(callback.authorizedCallers(newCaller));
    }
}
