// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    custodianDeposit,
    custodianRedeemPair
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

/// @dev Handler for invariant fuzzing. Tracks ghost variables for cross-check.
contract CustodianHandler is Test {
    // Ghost variables — shadow the real state for invariant checking
    uint256 public ghost_totalMinted;
    uint256 public ghost_totalRedeemed;
    address[] public actors;

    constructor() {
        // Bounded actor set for multi-user fuzzing
        actors.push(makeAddr("actor0"));
        actors.push(makeAddr("actor1"));
        actors.push(makeAddr("actor2"));

        // Init custodian storage (handler owns the storage)
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = address(1);
        cs.depositCap = 0; // no cap for fuzz
    }

    function deposit(uint256 actorSeed, uint256 amount) external {
        address actor = actors[actorSeed % actors.length];
        amount = bound(amount, 1, 1_000_000e6); // 1 wei to 1M USDC

        custodianDeposit(actor, amount);
        ghost_totalMinted += amount;
    }

    function redeemPair(uint256 actorSeed, uint256 amount) external {
        address actor = actors[actorSeed % actors.length];
        uint256 longBal = getERC6909Storage().balanceOf[actor][LONG];
        uint256 shortBal = getERC6909Storage().balanceOf[actor][SHORT];
        uint256 maxRedeem = longBal;
        if (shortBal < maxRedeem) maxRedeem = shortBal;

        if (maxRedeem == 0) return; // skip if nothing to redeem
        amount = bound(amount, 1, maxRedeem);

        custodianRedeemPair(actor, amount);
        ghost_totalRedeemed += amount;
    }

    function actorCount() external view returns (uint256) {
        return actors.length;
    }

    // Storage getters for invariant test (reads from handler's storage context)
    function getTotalDeposits() external view returns (uint128) {
        return getCustodianStorage().totalDeposits;
    }

    function getBalanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }
}
