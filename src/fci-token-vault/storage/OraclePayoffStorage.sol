// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

bytes32 constant ORACLE_PAYOFF_STORAGE_POSITION = keccak256("thetaswap.oracle-payoff");

struct OraclePayoffStorage {
    uint160 sqrtPriceStrike;
    uint160 sqrtPriceHWM;
    uint256 expiry;
    bool    settled;
    uint256 longPayoutPerToken; // Q96-scaled
    bytes32 adapterSlot;        // references ProtocolAdapterStorage instance
}

error VaultAlreadySettled();
error VaultExpired();
error VaultNotExpired();
error VaultNotSettled();
error VaultAlreadySettledPoke();

function getOraclePayoffStorage() pure returns (OraclePayoffStorage storage s) {
    bytes32 position = ORACLE_PAYOFF_STORAGE_POSITION;
    assembly {
        s.slot := position
    }
}
