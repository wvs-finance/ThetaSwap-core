// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    ProtocolAdapterStorage
} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {
    FeeConcentrationIndexStorage,
    fciStorage, reactiveFciStorage
} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {isUniswapV3Reactive} from "@types/HookDataFlagsMod.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index-v2/interfaces/IFeeConcentrationIndex.sol";

// ── FCI storage dispatch (Option C: hookData flags) ──

/// @dev Centralizes the inline ternary that was duplicated in every ext mod wrapper.
/// Single place to update when new protocols are added.
function fciStorageFor(bytes calldata hookData) pure returns (FeeConcentrationIndexStorage storage $) {
    if (isUniswapV3Reactive(hookData)) {
        return reactiveFciStorage();
    }
    return fciStorage();
}

// ── Oracle read helpers ──

/// @dev Read epoch-reset Δ⁺ from the FCI oracle via the adapter's entry point.
/// Consumed by OraclePayoffMod.oraclePoke().
function getDeltaPlusEpoch(ProtocolAdapterStorage storage $) view returns (uint128) {
    return IFeeConcentrationIndex(address($.fciEntryPoint))
        .getDeltaPlusEpoch($.poolKey, $.reactive);
}

/// @dev Read raw Δ⁺ from the FCI oracle via the adapter's entry point.
/// Provided for script/test callers (CompareDeltaPlus.s.sol, FeeConcentrationIndexBuilder.s.sol).
function getDeltaPlus(ProtocolAdapterStorage storage $) view returns (uint128) {
    return IFeeConcentrationIndex(address($.fciEntryPoint))
        .getDeltaPlus($.poolKey, $.reactive);
}
