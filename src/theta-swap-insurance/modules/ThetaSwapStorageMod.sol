// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {IERC6909Claims} from "@uniswap/v4-core/src/interfaces/external/IERC6909Claims.sol";
import {PremiumFactor, fromCalldata} from "../types/PremiumFactorMod.sol";

// Diamond storage for ThetaSwap Insurance.
// Disjoint from FCI storage (different keccak256 slot).
//
// Registration driven through V4's modifyLiquidity + hookData:
//   - addLiquidity(hookData = packed uint128 factorRaw)
//       → afterAddLiquidity: register
//   - removeLiquidity → afterRemoveLiquidity: deregister

struct ThetaSwapInsuranceStorage {
    // positionKey → PremiumFactor committed by PLP.
    // Zero means not registered.
    mapping(PoolId => mapping(bytes32 => PremiumFactor)) registrations;
    // ERC6909 claims token (the PoolManager implements this).
    // Used solely for operator checks — PLP must grant hook operator status.
    IERC6909Claims feeClaimsToken;
}

bytes32 constant TSI_STORAGE_SLOT = keccak256("ThetaSwapInsurance.storage");

function tsiStorage() pure returns (ThetaSwapInsuranceStorage storage s) {
    bytes32 slot = TSI_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

// ── Storage accessors ──

function getRegistration(PoolId poolId, bytes32 positionKey) view returns (PremiumFactor) {
    return tsiStorage().registrations[poolId][positionKey];
}

function isRegistered(PoolId poolId, bytes32 positionKey) view returns (bool) {
    return PremiumFactor.unwrap(tsiStorage().registrations[poolId][positionKey]) != 0;
}

function feeClaimsToken() view returns (IERC6909Claims) {
    return tsiStorage().feeClaimsToken;
}

// ── State transitions ──

error TSI__NotRegistered();
error TSI__NotOperator();

/// @dev Called from afterAddLiquidity.
///      hookData is tightly packed: 16 bytes for uint128 factorRaw.
///      PremiumFactor type owns deserialization via fromCalldata.
function register(
    PoolId poolId,
    bytes32 positionKey,
    bytes calldata hookData,
    address plp,
    address hook
) {
    require(feeClaimsToken().isOperator(plp, hook), TSI__NotOperator());
    ThetaSwapInsuranceStorage storage $ = tsiStorage();
    $.registrations[poolId][positionKey] = fromCalldata(hookData);
}

/// @dev Called from afterRemoveLiquidity. Clears registration.
function deregister(PoolId poolId, bytes32 positionKey) {
    require(isRegistered(poolId, positionKey), TSI__NotRegistered());
    ThetaSwapInsuranceStorage storage $ = tsiStorage();
    $.registrations[poolId][positionKey] = PremiumFactor.wrap(0);
}

// ── Initialization ──

function setFeeClaimsToken(IERC6909Claims token) {
    tsiStorage().feeClaimsToken = token;
}
