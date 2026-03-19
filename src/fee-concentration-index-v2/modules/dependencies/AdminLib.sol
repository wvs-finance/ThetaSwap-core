// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

event FundsMigrated(address indexed to, uint256 amount);

error NoFunds();
error MigrationTransferFailed();

function migrateFunds(address payable to, uint256 balance) {
    if (balance == 0) revert NoFunds();
    (bool success,) = to.call{value: balance}("");
    if (!success) revert MigrationTransferFailed();
    emit FundsMigrated(to, balance);
}
