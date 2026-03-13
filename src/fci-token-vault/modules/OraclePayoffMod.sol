// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    getOraclePayoffStorage,
    OraclePayoffStorage,
    VaultAlreadySettled,
    VaultExpired,
    VaultNotExpired,
    VaultNotSettled,
    VaultAlreadySettledPoke
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";

import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";

import {
    erc6909Burn
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

import {
    lookbackPayoffX96,
    applyDecay,
    updateHWM,
    deltaPlusToSqrtPriceX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {SafeCastLib} from "solady/utils/SafeCastLib.sol";

import {ZeroAmount} from "@fci-token-vault/storage/CustodianStorage.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

/// @dev Read FCI oracle, apply decay, update HWM. Permissionless.
/// Returns currentSqrtPrice so the facet can emit it alongside the new HWM.
function oraclePoke() returns (uint160 currentSqrtPrice) {
    OraclePayoffStorage storage os = getOraclePayoffStorage();
    if (os.settled) revert VaultAlreadySettledPoke();

    uint128 deltaPlus = IFeeConcentrationIndex(address(os.poolKey.hooks))
        .getDeltaPlus(os.poolKey, os.reactive);

    uint256 dt = block.timestamp - os.lastHwmTimestamp;
    uint160 decayed = applyDecay(os.sqrtPriceHWM, dt, os.halfLifeSeconds);

    if (deltaPlus > 0) {
        currentSqrtPrice = deltaPlusToSqrtPriceX96(deltaPlus);
        os.sqrtPriceHWM = updateHWM(decayed, currentSqrtPrice);
    } else {
        currentSqrtPrice = 0;
        os.sqrtPriceHWM = decayed;
    }
    os.lastHwmTimestamp = uint64(block.timestamp);
}

/// @dev Settle after expiry. Computes final LONG payout from HWM vs strike.
function oracleSettle() {
    OraclePayoffStorage storage os = getOraclePayoffStorage();
    if (os.settled) revert VaultAlreadySettled();
    if (block.timestamp < os.expiry) revert VaultNotExpired();

    uint256 dt = block.timestamp - os.lastHwmTimestamp;
    uint160 decayedHWM = applyDecay(os.sqrtPriceHWM, dt, os.halfLifeSeconds);

    os.longPayoutPerToken = lookbackPayoffX96(decayedHWM, os.sqrtPriceStrike);
    os.settled = true;
}

/// @dev Burn LONG tokens. Returns computed payout for facet to transfer.
/// Rounds DOWN (mulDiv truncates — favors vault).
/// totalDeposits decremented by payout, not token amount — preserves collateral
/// backing for outstanding SHORT tokens.
function oracleRedeemLong(address redeemer, uint256 amount) returns (uint256 payout) {
    OraclePayoffStorage storage os = getOraclePayoffStorage();
    if (!os.settled) revert VaultNotSettled();
    if (amount == 0) revert ZeroAmount();

    payout = FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, SqrtPriceLibrary.Q96);

    erc6909Burn(redeemer, LONG, amount);

    CustodianStorage storage cs = getCustodianStorage();
    cs.totalDeposits -= SafeCastLib.toUint128(payout);
}

/// @dev Burn SHORT tokens. Returns computed payout for facet to transfer.
/// Payout = amount - longPortion. Rounds DOWN on longPortion, so SHORT gets ceiling.
/// totalDeposits decremented by payout, not token amount.
function oracleRedeemShort(address redeemer, uint256 amount) returns (uint256 payout) {
    OraclePayoffStorage storage os = getOraclePayoffStorage();
    if (!os.settled) revert VaultNotSettled();
    if (amount == 0) revert ZeroAmount();

    uint256 longPortion = FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, SqrtPriceLibrary.Q96);
    payout = amount - longPortion;

    erc6909Burn(redeemer, SHORT, amount);

    CustodianStorage storage cs = getCustodianStorage();
    cs.totalDeposits -= SafeCastLib.toUint128(payout);
}
