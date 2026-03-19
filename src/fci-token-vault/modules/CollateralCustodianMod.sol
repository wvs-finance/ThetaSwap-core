// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    getCustodianStorage,
    CustodianStorage,
    DepositCapExceeded,
    ZeroAmount
} from "@fci-token-vault/storage/CustodianStorage.sol";

import {
    erc6909Mint,
    erc6909Burn
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

import {SafeCastLib} from "solady/utils/SafeCastLib.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

/// @dev Deposit collateral and receive equal LONG + SHORT tokens.
/// Collateral transfer must happen BEFORE calling this (CEI: facet handles transfer).
/// Panoptic pattern: internal tracking via totalDeposits, never balanceOf.
function custodianDeposit(address depositor, uint256 amount) {
    if (amount == 0) revert ZeroAmount();

    CustodianStorage storage cs = getCustodianStorage();

    // SafeCastLib.toUint128 reverts on overflow — prevents silent truncation
    uint128 amount128 = SafeCastLib.toUint128(amount);
    uint128 newTotal = cs.totalDeposits + amount128;
    if (cs.depositCap > 0 && newTotal > cs.depositCap) revert DepositCapExceeded();

    cs.totalDeposits = newTotal;

    // Atomic paired mint — supply parity enforced by construction
    erc6909Mint(depositor, LONG, amount);
    erc6909Mint(depositor, SHORT, amount);
}

/// @dev Burn equal LONG + SHORT tokens and mark collateral as available for return.
/// Collateral transfer must happen AFTER calling this (CEI: facet handles transfer).
/// Risk-free exit: always returns exactly `amount` USDC regardless of oracle state.
function custodianRedeemPair(address redeemer, uint256 amount) {
    if (amount == 0) revert ZeroAmount();

    CustodianStorage storage cs = getCustodianStorage();

    // Burn both sides — reverts if insufficient balance (ERC6909Lib checks)
    erc6909Burn(redeemer, LONG, amount);
    erc6909Burn(redeemer, SHORT, amount);

    cs.totalDeposits -= SafeCastLib.toUint128(amount);
}
