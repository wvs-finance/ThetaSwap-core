// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

bytes32 constant CUSTODIAN_STORAGE_POSITION = keccak256("thetaswap.collateral-custodian");

struct CustodianStorage {
    uint128 totalDeposits;     // total USDC locked (uint128: cap at ~3.4e38)
    address collateralToken;   // USDC address (immutable after init)
    uint128 depositCap;        // max total deposits (0 = unlimited)
}

error DepositCapExceeded();
error ZeroAmount();

function getCustodianStorage() pure returns (CustodianStorage storage s) {
    bytes32 position = CUSTODIAN_STORAGE_POSITION;
    assembly {
        s.slot := position
    }
}
