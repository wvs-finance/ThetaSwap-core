// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    custodianDeposit,
    custodianRedeemPair
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {
    oraclePoke,
    oracleSettle,
    oracleRedeemLong,
    oracleRedeemShort
} from "@fci-token-vault/modules/OraclePayoffMod.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {
    getOraclePayoffStorage,
    OraclePayoffStorage,
    VaultAlreadySettled,
    VaultNotSettled
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @dev Test harness composing both new modules. Epoch-only: no decay.
contract CustodianHarness {
    function harness_deposit(address depositor, uint256 amount) external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (os.settled) revert VaultAlreadySettled();
        CustodianStorage storage cs = getCustodianStorage();
        SafeTransferLib.safeTransferFrom(cs.collateralToken, depositor, address(this), amount);
        custodianDeposit(depositor, amount);
    }

    function harness_settle() external {
        oracleSettle();
    }

    function harness_redeem(address redeemer, uint256 amount) external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (!os.settled) revert VaultNotSettled();
        uint256 longPayout = FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, SqrtPriceLibrary.Q96);
        uint256 shortPayout = amount - longPayout;

        custodianRedeemPair(redeemer, amount);

        CustodianStorage storage cs = getCustodianStorage();
        if (longPayout > 0) {
            SafeTransferLib.safeTransfer(cs.collateralToken, redeemer, longPayout);
        }
        if (shortPayout > 0) {
            SafeTransferLib.safeTransfer(cs.collateralToken, redeemer, shortPayout);
        }
    }

    function harness_poke() external returns (uint160) {
        return oraclePoke();
    }

    function harness_balanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }

    function harness_getVaultStorage() external view returns (
        uint160 sqrtPriceStrike,
        uint160 sqrtPriceHWM,
        uint256 expiry,
        uint256 totalDeposits,
        bool settled,
        uint256 longPayoutPerToken
    ) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        CustodianStorage storage cs = getCustodianStorage();
        return (
            os.sqrtPriceStrike,
            os.sqrtPriceHWM,
            os.expiry,
            uint256(cs.totalDeposits),
            os.settled,
            os.longPayoutPerToken
        );
    }

    function harness_initVault(
        uint160 sqrtPriceStrike,
        uint256 expiry,
        PoolKey calldata poolKey,
        bool reactive,
        address collateralToken
    ) external {
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateralToken;

        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = sqrtPriceStrike;
        os.expiry = expiry;
        os.poolKey = poolKey;
        os.reactive = reactive;
    }

    function harness_setHWM(uint160 hwm) external {
        getOraclePayoffStorage().sqrtPriceHWM = hwm;
    }

    function harness_getPoolKey() external view returns (PoolKey memory) {
        return getOraclePayoffStorage().poolKey;
    }

    function harness_getReactive() external view returns (bool) {
        return getOraclePayoffStorage().reactive;
    }
}
