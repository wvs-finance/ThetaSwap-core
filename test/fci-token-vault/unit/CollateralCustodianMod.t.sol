// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    custodianDeposit,
    custodianRedeemPair,
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
// getERC6909Storage is used inside CustodianModCaller (same file) for the getter helpers

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

contract CustodianModCaller {
    function doDeposit(address depositor, uint256 amount) external {
        custodianDeposit(depositor, amount);
    }
    function doRedeemPair(address redeemer, uint256 amount) external {
        custodianRedeemPair(redeemer, amount);
    }
    function initStorage(address collateral, uint128 cap) external {
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateral;
        cs.depositCap = cap;
    }
    function erc6909BalanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }
    function totalDeposits() external view returns (uint128) {
        return getCustodianStorage().totalDeposits;
    }
}

contract CollateralCustodianModTest is Test {
    CustodianModCaller caller;
    address alice = makeAddr("alice");

    function setUp() public {
        caller = new CustodianModCaller();
        caller.initStorage(address(1), 0); // no cap
    }

    /// @dev INV-001: deposit mints equal LONG + SHORT
    function test_deposit_mints_equal_pair() public {
        caller.doDeposit(alice, 100e6);
        assertEq(caller.erc6909BalanceOf(alice, LONG), 100e6);
        assertEq(caller.erc6909BalanceOf(alice, SHORT), 100e6);
    }

    /// @dev INV-002: deposit increases totalDeposits
    function test_deposit_increases_totalDeposits() public {
        caller.doDeposit(alice, 100e6);
        assertEq(caller.totalDeposits(), 100e6);
    }

    /// @dev INV-003: redeemPair burns equal LONG + SHORT
    function test_redeemPair_burns_pair() public {
        caller.doDeposit(alice, 100e6);
        caller.doRedeemPair(alice, 100e6);
        assertEq(caller.erc6909BalanceOf(alice, LONG), 0);
        assertEq(caller.erc6909BalanceOf(alice, SHORT), 0);
    }

    /// @dev INV-004: redeemPair decreases totalDeposits by exact amount
    function test_redeemPair_decreases_totalDeposits() public {
        caller.doDeposit(alice, 100e6);
        caller.doRedeemPair(alice, 60e6);
        assertEq(caller.totalDeposits(), 40e6);
    }

    /// @dev INV-005: zero amount reverts
    function test_deposit_zero_reverts() public {
        vm.expectRevert();
        caller.doDeposit(alice, 0);
    }

    function test_redeemPair_zero_reverts() public {
        vm.expectRevert();
        caller.doRedeemPair(alice, 0);
    }

    /// @dev INV-006: deposit exceeding cap reverts
    function test_deposit_exceeds_cap_reverts() public {
        caller.initStorage(address(1), 50e6); // cap at 50
        vm.expectRevert();
        caller.doDeposit(alice, 100e6);
    }
}
