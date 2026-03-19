// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {CustodianHandler, LONG, SHORT} from "./CustodianHandler.sol";

contract CustodianInvariantTest is Test {
    CustodianHandler handler;

    function setUp() public {
        handler = new CustodianHandler();
        targetContract(address(handler));
    }

    /// INV-1: totalDeposits == ghost_totalMinted - ghost_totalRedeemed
    function invariant_totalDeposits_matches_ghost() public view {
        uint128 totalDep = handler.getTotalDeposits();
        uint256 expected = handler.ghost_totalMinted() - handler.ghost_totalRedeemed();
        assertEq(uint256(totalDep), expected);
    }

    /// INV-2: For each actor, LONG balance == SHORT balance
    function invariant_supply_parity_per_actor() public view {
        for (uint256 i = 0; i < handler.actorCount(); i++) {
            address actor = handler.actors(i);
            uint256 longBal = handler.getBalanceOf(actor, LONG);
            uint256 shortBal = handler.getBalanceOf(actor, SHORT);
            assertEq(longBal, shortBal, "LONG != SHORT for actor");
        }
    }

    /// INV-3: Sum of all actor LONG balances == totalDeposits
    function invariant_total_supply_eq_deposits() public view {
        uint256 totalLong;
        for (uint256 i = 0; i < handler.actorCount(); i++) {
            totalLong += handler.getBalanceOf(handler.actors(i), LONG);
        }
        assertEq(totalLong, uint256(handler.getTotalDeposits()));
    }

    /// INV-4: totalDeposits never goes negative
    function invariant_totalDeposits_non_negative() public view {
        assertGe(handler.ghost_totalMinted(), handler.ghost_totalRedeemed());
    }
}
