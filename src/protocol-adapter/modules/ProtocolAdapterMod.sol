// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {TickRange} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {
    FeeConcentrationIndexStorage,
    registerPosition as _registerPosition,
    incrementPosCount as _incrementPosCount,
    decrementPosCount as _decrementPosCount,
    incrementOverlappingRanges as _incrementOverlappingRanges,
    deregisterPosition as _deregisterPosition,
    addStateTerm as _addStateTerm,
    setFeeGrowthBaseline as _setFeeGrowthBaseline,
    getFeeGrowthBaseline as _getFeeGrowthBaseline,
    deleteFeeGrowthBaseline as _deleteFeeGrowthBaseline
} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {fciStorageFor} from "@protocol-adapter/libraries/ProtocolAdapterLib.sol";
import {
    ProtocolAdapterStorage,
    protocolAdapterStorage
} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";

// ── 9 hookData-aware wrappers ──
// Same signatures as FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.
// Dispatch via fciStorageFor(hookData) instead of inline ternaries.

function registerPosition(
    bytes calldata hookData,
    PoolId poolId,
    TickRange rk,
    bytes32 positionKey,
    int24 tickLower,
    int24 tickUpper,
    uint128 liquidity
) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _registerPosition($, poolId, rk, positionKey, tickLower, tickUpper, liquidity);
}

function incrementPosCount(bytes calldata hookData, PoolId poolId) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _incrementPosCount($, poolId);
}

function decrementPosCount(bytes calldata hookData, PoolId poolId) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _decrementPosCount($, poolId);
}

function incrementOverlappingRanges(bytes calldata hookData, PoolId poolId, int24 tickMin, int24 tickMax) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _incrementOverlappingRanges($, poolId, tickMin, tickMax);
}

function deregisterPosition(
    bytes calldata hookData,
    PoolId poolId,
    bytes32 positionKey,
    uint128 posLiquidity
) returns (TickRange rk, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    return _deregisterPosition($, poolId, positionKey, posLiquidity);
}

function addStateTerm(bytes calldata hookData, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _addStateTerm($, poolId, blockLifetime, xSquaredQ128);
}

function setFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _setFeeGrowthBaseline($, poolId, positionKey, feeGrowth0X128);
}

function getFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey) view returns (uint256) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    return _getFeeGrowthBaseline($, poolId, positionKey);
}

function deleteFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _deleteFeeGrowthBaseline($, poolId, positionKey);
}

// ── Adapter initialization ──

/// @dev Initialize a ProtocolAdapterStorage instance at the given slot.
/// Access control is enforced at the facet level (diamond proxy onlyOwner or init guard),
/// not within this free function — matches existing patterns (getCustodianStorage, etc.).
function initializeAdapter(
    bytes32 slot,
    address protocolState,
    IHooks fciEntryPoint,
    PoolKey calldata poolKey,
    bool reactive
) {
    ProtocolAdapterStorage storage $ = protocolAdapterStorage(slot);
    $.protocolState = protocolState;
    $.fciEntryPoint = fciEntryPoint;
    $.poolKey = poolKey;
    $.reactive = reactive;
}
