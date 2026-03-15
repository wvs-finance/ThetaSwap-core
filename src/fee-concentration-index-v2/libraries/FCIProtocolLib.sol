// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {TickRange} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {CalldataReader, CalldataReaderLib} from "angstrom/src/types/CalldataReader.sol";
import {NATIVE_V4} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";

/// @dev Reads the protocol flag from hookData. The flag occupies the first 2 bytes
/// at a deterministic position. Empty hookData returns NATIVE_V4 (0xFFFF).
function getProtocolFlagFromHookData(bytes calldata hookData) pure returns (bytes2 flag) {
    if (hookData.length == 0) return NATIVE_V4;
    CalldataReader reader = CalldataReaderLib.from(hookData);
    uint16 raw;
    (reader, raw) = reader.readU16();
    flag = bytes2(raw);
}

/// @dev Derives a position key from hookData, sender, and liquidity params.
/// Each protocol MUST implement this function with its own position key logic.
/// - V4: Position.calculatePositionKey(sender, tickLower, tickUpper, salt)
/// - V3: v3PositionKey(owner, tickLower, tickUpper)
function positionKey(bytes calldata hookData, address sender, ModifyLiquidityParams calldata params) pure returns (bytes32) {
    // TODO: implement per protocol semantics
    revert("FCIProtocolLib: positionKey not implemented");
}

/// @dev Reads the current tick from the protocol's pool state.
/// Requires IProtocolStateView to access protocol-specific state.
/// Each protocol MUST implement with its own tick read logic.
/// - V4: StateLibrary.getSlot0(poolManager, poolId)
/// - V3: IUniswapV3Pool(pool).slot0()
function currentTick(IProtocolStateView protocolStateView, bytes calldata hookData) view returns (int24) {
    // TODO: implement per protocol semantics — requires IProtocolStateView
    revert("FCIProtocolLib: currentTick not implemented");
}

/// @dev Reads fee growth inside a tick range from the protocol's pool state.
/// Requires IProtocolStateView to access protocol-specific state.
/// Each protocol MUST implement with its own fee growth read logic.
function poolRangeFeeGrowthInside(
    IProtocolStateView protocolStateView,
    bytes calldata hookData,
    PoolId poolId,
    int24 currentTick_,
    TickRange tickRange
) view returns (uint256) {
    // TODO: implement per protocol semantics — requires IProtocolStateView
    revert("FCIProtocolLib: poolRangeFeeGrowthInside not implemented");
}

/// @dev Reads the latest position fee growth and liquidity from the protocol's pool state.
/// Requires IProtocolStateView to access protocol-specific state.
/// Each protocol MUST implement with its own position info read logic.
function latestPositionFeeGrowthInside(
    IProtocolStateView protocolStateView,
    bytes calldata hookData,
    PoolId poolId,
    bytes32 posKey
) view returns (uint128 posLiquidity, uint256 feeGrowthLast) {
    // TODO: implement per protocol semantics — requires IProtocolStateView
    revert("FCIProtocolLib: latestPositionFeeGrowthInside not implemented");
}
