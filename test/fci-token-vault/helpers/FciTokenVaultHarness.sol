// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    deposit,
    settle,
    redeem,
    poke,
    mintPair,
    burnPair,
    getFciVaultStorage,
    FciVaultStorage,
    LONG,
    SHORT
} from "@fci-token-vault/modules/FciTokenVaultMod.sol";

import {
    getERC6909Storage,
    ERC6909Storage
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

contract FciTokenVaultHarness {
    function harness_deposit(address depositor, uint256 amount) external {
        FciVaultStorage storage vs = getFciVaultStorage();
        SafeTransferLib.safeTransferFrom(vs.collateralToken, depositor, address(this), amount);
        deposit(depositor, amount);
    }

    function harness_settle() external {
        settle();
    }

    function harness_redeem(address redeemer, uint256 amount) external {
        FciVaultStorage storage vs = getFciVaultStorage();
        uint256 longPayoutVal = (amount * vs.longPayoutPerToken) / SqrtPriceLibrary.Q96;
        uint256 shortPayoutVal = amount - longPayoutVal;
        redeem(redeemer, amount);
        if (longPayoutVal > 0) {
            SafeTransferLib.safeTransfer(vs.collateralToken, redeemer, longPayoutVal);
        }
        if (shortPayoutVal > 0) {
            SafeTransferLib.safeTransfer(vs.collateralToken, redeemer, shortPayoutVal);
        }
    }

    function harness_poke() external {
        poke();
    }

    function harness_balanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }

    function harness_getVaultStorage() external view returns (
        uint160 sqrtPriceStrike,
        uint160 sqrtPriceHWM,
        uint256 halfLifeSeconds,
        uint256 expiry,
        uint256 totalDeposits,
        uint256 lastHwmTimestamp,
        bool settled,
        uint256 longPayoutPerToken
    ) {
        FciVaultStorage storage vs = getFciVaultStorage();
        return (
            vs.sqrtPriceStrike,
            vs.sqrtPriceHWM,
            vs.halfLifeSeconds,
            vs.expiry,
            vs.totalDeposits,
            vs.lastHwmTimestamp,
            vs.settled,
            vs.longPayoutPerToken
        );
    }

    function harness_initVault(
        uint160 sqrtPriceStrike,
        uint256 halfLifeSeconds,
        uint256 expiry,
        PoolKey calldata poolKey,
        bool reactive,
        address collateralToken
    ) external {
        FciVaultStorage storage vs = getFciVaultStorage();
        vs.sqrtPriceStrike = sqrtPriceStrike;
        vs.halfLifeSeconds = halfLifeSeconds;
        vs.expiry = expiry;
        vs.lastHwmTimestamp = block.timestamp;
        vs.poolKey = poolKey;
        vs.reactive = reactive;
        vs.collateralToken = collateralToken;
    }

    function harness_setHWM(uint160 hwm, uint256 timestamp) external {
        FciVaultStorage storage vs = getFciVaultStorage();
        vs.sqrtPriceHWM = hwm;
        vs.lastHwmTimestamp = timestamp;
    }

    function harness_getPoolKey() external view returns (PoolKey memory) {
        return getFciVaultStorage().poolKey;
    }

    function harness_getReactive() external view returns (bool) {
        return getFciVaultStorage().reactive;
    }
}
