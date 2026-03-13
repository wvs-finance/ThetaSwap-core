// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    custodianDeposit,
    custodianRedeemPair
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {
    oraclePoke,
    oracleSettle
} from "@fci-token-vault/modules/OraclePayoffMod.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {
    getOraclePayoffStorage,
    OraclePayoffStorage,
    VaultAlreadySettled,
    VaultAlreadySettledPoke,
    VaultNotSettled
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {
    getERC6909Storage,
    ERC6909Storage
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {
    applyDecay,
    updateHWM,
    deltaPlusToSqrtPriceX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

/// @dev Integration-test harness built on the new separated modules.
///      Preserves the full API of the old FciTokenVaultHarness so that
///      all integration tests compile without change.
contract FciTokenVaultHarness {
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

    function harness_poke() external {
        oraclePoke();
    }

    /// @dev Same as poke() but reads getDeltaPlusEpoch() instead of getDeltaPlus().
    function harness_pokeEpoch() external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (os.settled) revert VaultAlreadySettledPoke();

        uint128 deltaPlus = IFeeConcentrationIndex(address(os.poolKey.hooks))
            .getDeltaPlusEpoch(os.poolKey, os.reactive);

        uint256 dt = block.timestamp - os.lastHwmTimestamp;
        uint160 decayed = applyDecay(os.sqrtPriceHWM, dt, os.halfLifeSeconds);

        if (deltaPlus > 0) {
            uint160 currentSqrtPrice = deltaPlusToSqrtPriceX96(deltaPlus);
            os.sqrtPriceHWM = updateHWM(decayed, currentSqrtPrice);
        } else {
            os.sqrtPriceHWM = decayed;
        }
        os.lastHwmTimestamp = uint64(block.timestamp);
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
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        CustodianStorage storage cs = getCustodianStorage();
        return (
            os.sqrtPriceStrike,
            os.sqrtPriceHWM,
            os.halfLifeSeconds,
            os.expiry,
            uint256(cs.totalDeposits),
            uint256(os.lastHwmTimestamp),
            os.settled,
            os.longPayoutPerToken
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
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateralToken;

        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = sqrtPriceStrike;
        os.halfLifeSeconds = halfLifeSeconds;
        os.expiry = expiry;
        os.lastHwmTimestamp = uint64(block.timestamp);
        os.poolKey = poolKey;
        os.reactive = reactive;
    }

    function harness_setHWM(uint160 hwm, uint256 timestamp) external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceHWM = hwm;
        os.lastHwmTimestamp = uint64(timestamp);
    }

    function harness_getPoolKey() external view returns (PoolKey memory) {
        return getOraclePayoffStorage().poolKey;
    }

    function harness_getReactive() external view returns (bool) {
        return getOraclePayoffStorage().reactive;
    }
}
