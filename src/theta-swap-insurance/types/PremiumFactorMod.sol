// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeRevenue} from "../../types/FeeRevenueMod.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {CalldataReader, CalldataReaderLib} from "@angstrom/types/CalldataReader.sol";

type PremiumFactor is uint128;

uint128 constant Q128_ONE = type(uint128).max;

error PremiumFactor__Zero();

function fromRaw(uint128 raw) pure returns (PremiumFactor) {
    if (raw == 0) revert PremiumFactor__Zero();
    return PremiumFactor.wrap(raw);
}

function fromCalldata(bytes calldata hookData) pure returns (PremiumFactor) {
    CalldataReader reader = CalldataReaderLib.from(hookData);
    uint128 raw;
    (reader, raw) = reader.readU128();
    return fromRaw(raw);
}

function applyTo(PremiumFactor f, FeeRevenue r) pure returns (FeeRevenue) {
    uint256 premium = FixedPointMathLib.mulDiv(
        FeeRevenue.unwrap(r),
        uint256(PremiumFactor.unwrap(f)),
        uint256(Q128_ONE)
    );
    return FeeRevenue.wrap(premium);
}

function unwrap(PremiumFactor f) pure returns (uint128) {
    return PremiumFactor.unwrap(f);
}

function isMax(PremiumFactor f) pure returns (bool) {
    return PremiumFactor.unwrap(f) == Q128_ONE;
}

using {applyTo, unwrap, isMax} for PremiumFactor global;
