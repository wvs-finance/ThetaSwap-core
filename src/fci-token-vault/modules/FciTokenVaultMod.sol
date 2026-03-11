// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    erc6909Mint,
    erc6909Burn
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

import {
    lookbackPayoffX96,
    applyDecay,
    updateHWM,
    deltaPlusToSqrtPriceX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

bytes32 constant FCI_VAULT_STORAGE_POSITION = keccak256("thetaswap.fci-token-vault");

struct FciVaultStorage {
    uint160 sqrtPriceStrike;
    uint160 sqrtPriceHWM;
    uint256 halfLifeSeconds;
    uint256 expiry;
    uint256 totalDeposits;
    uint256 lastHwmTimestamp;
    bool settled;
    uint256 longPayoutPerToken;  // Q96-scaled
    address collateralToken;
    PoolKey poolKey;
    bool reactive;
}

error VaultAlreadySettled();
error VaultExpired();
error VaultNotExpired();
error VaultNotSettled();

function getFciVaultStorage() pure returns (FciVaultStorage storage s) {
    bytes32 position = FCI_VAULT_STORAGE_POSITION;
    assembly {
        s.slot := position
    }
}

/// @dev Mint equal LONG + SHORT tokens to `to`. Enforces INV-012 by construction.
function mintPair(address to, uint256 amount) {
    erc6909Mint(to, LONG, amount);
    erc6909Mint(to, SHORT, amount);
}

/// @dev Burn equal LONG + SHORT tokens from `from`. Enforces INV-012 by construction.
function burnPair(address from, uint256 amount) {
    erc6909Burn(from, LONG, amount);
    erc6909Burn(from, SHORT, amount);
}

/// @dev Deposit collateral and receive equal LONG + SHORT tokens.
function deposit(address depositor, uint256 amount) {
    FciVaultStorage storage vs = getFciVaultStorage();
    if (vs.settled) revert VaultAlreadySettled();
    if (block.timestamp >= vs.expiry) revert VaultExpired();

    vs.totalDeposits += amount;
    mintPair(depositor, amount);
}

/// @dev Settle the vault after expiry. Computes final LONG payout from HWM vs strike.
function settle() {
    FciVaultStorage storage vs = getFciVaultStorage();
    if (vs.settled) revert VaultAlreadySettled();
    if (block.timestamp < vs.expiry) revert VaultNotExpired();

    // Apply final decay to HWM
    uint256 dt = block.timestamp - vs.lastHwmTimestamp;
    uint160 decayedHWM = applyDecay(vs.sqrtPriceHWM, dt, vs.halfLifeSeconds);

    // Compute payoff and store for redemptions
    vs.longPayoutPerToken = lookbackPayoffX96(decayedHWM, vs.sqrtPriceStrike);
    vs.settled = true;
}

/// @dev Redeem equal LONG + SHORT tokens for collateral.
/// LONG holder gets: amount * longPayoutPerToken / Q96
/// SHORT holder gets: amount - longPayout
/// Actual collateral transfer happens in the Facet layer.
function redeem(address redeemer, uint256 amount) {
    FciVaultStorage storage vs = getFciVaultStorage();
    if (!vs.settled) revert VaultNotSettled();

    burnPair(redeemer, amount);
    vs.totalDeposits -= amount;
}

error VaultAlreadySettledPoke();

/// @dev Read Δ⁺ from FCI oracle, convert to sqrtPrice, apply decay, update HWM.
function poke() {
    FciVaultStorage storage vs = getFciVaultStorage();
    if (vs.settled) revert VaultAlreadySettledPoke();

    uint128 deltaPlus = IFeeConcentrationIndex(address(vs.poolKey.hooks))
        .getDeltaPlus(vs.poolKey, vs.reactive);

    uint160 currentSqrtPrice = deltaPlusToSqrtPriceX96(deltaPlus);

    uint256 dt = block.timestamp - vs.lastHwmTimestamp;
    uint160 decayed = applyDecay(vs.sqrtPriceHWM, dt, vs.halfLifeSeconds);

    vs.sqrtPriceHWM = updateHWM(decayed, currentSqrtPrice);
    vs.lastHwmTimestamp = block.timestamp;
}
