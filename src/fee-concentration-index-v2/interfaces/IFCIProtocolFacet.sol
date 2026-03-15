// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {TickRange} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {LiquidityPositionSnapshot} from "@fee-concentration-index-v2/types/LiquidityPositionSnapshot.sol";

/// @title IFCIProtocolFacet
/// @dev Extends IHooks with protocol-specific behavioral functions.
/// Hook handlers are called via delegatecall from FCI V2 dispatcher.
/// Behavioral functions are called internally by hook handler implementations.
interface IFCIProtocolFacet is IHooks {
    // ── Position key derivation ──
    function positionKey(bytes calldata hookData, address sender, ModifyLiquidityParams calldata params) external view returns (bytes32);

    // ── Fee growth reads ──
    function latestPositionFeeGrowthInside(bytes calldata hookData, PoolId poolId, bytes32 posKey) external view returns (uint128 posLiquidity, uint256 feeGrowthLast);
    function poolRangeFeeGrowthInside(bytes calldata hookData, PoolId poolId, int24 currentTick, TickRange tickRange) external view returns (uint256);

    // ── Position registration ──
    function addPositionInRange(bytes calldata hookData, bytes32 posKey, LiquidityPositionSnapshot calldata snapshot) external;
    function removePositionInRange(bytes calldata hookData, bytes32 posKey, LiquidityPositionSnapshot calldata snapshot) external returns (SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq);

    // ── Tick ──
    function currentTick(bytes calldata hookData, PoolId poolId) external view returns (int24);

    // ── Fee growth baseline ──
    function setFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 posKey, uint256 feeGrowth) external;
    function getFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 posKey) external view returns (uint256);
    function deleteFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 posKey) external;

    // ── Position count ──
    function incrementPosCount(bytes calldata hookData, PoolId poolId) external;
    function decrementPosCount(bytes calldata hookData, PoolId poolId) external;

    // ── Transient storage ──
    function tstoreTick(bytes calldata hookData, int24 tick) external;
    function tloadTick(bytes calldata hookData) external returns (int24 tick);
    function tstoreRemovalData(bytes calldata hookData, uint256 feeLast, uint128 posLiquidity, uint256 rangeFeeGrowth) external;
    function tloadRemovalData(bytes calldata hookData) external returns (uint256 feeLast, uint128 posLiquidity, uint256 rangeFeeGrowth);

    // ── Overlapping ranges ──
    function incrementOverlappingRanges(bytes calldata hookData, PoolId poolId, int24 tickMin, int24 tickMax) external;

    // ── FCI state accumulation ──
    function addStateTerm(bytes calldata hookData, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) external;
    function addEpochTerm(bytes calldata hookData, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) external;
}
