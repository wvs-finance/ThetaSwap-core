// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IPayable} from "reactive-lib/interfaces/IPayable.sol";

address payable constant SYSTEM_CONTRACT = payable(0x0000000000000000000000000000000000fffFfF);

// Pay outstanding subscription debt from received ETH/REACT.
// Called from receive() fallback. Funding-source agnostic.
// Must pass address(this) since free functions cannot access `this`.
function coverDebt(address self) {
    uint256 debt = IPayable(SYSTEM_CONTRACT).debt(self);
    if (debt == 0) return;
    uint256 payment = debt <= self.balance ? debt : self.balance;
    if (payment == 0) return;
    (bool success,) = payable(SYSTEM_CONTRACT).call{value: payment}("");
    if (!success) revert DebtPaymentFailed();
}

// Deposit contract's entire native balance into the SystemContract as a pre-funded
// reserve. Subscription costs are drawn from this reserve instead of accumulating debt.
function depositToSystem(address self) {
    uint256 bal = self.balance;
    if (bal == 0) return;
    (bool success,) = payable(SYSTEM_CONTRACT).call{value: bal}("");
    if (!success) revert DebtPaymentFailed();
}

error DebtPaymentFailed();
