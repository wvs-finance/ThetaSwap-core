// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {Position} from "v4-core/src/libraries/Position.sol";
import {v3PositionKey} from "../reactive-integration/libraries/PoolKeyExtMod.sol";
import {isUniswapV3, isUniswapV4} from "../reactive-integration/uniswapV3/types/HookDataFlagsMod.sol";

// Shared hook utilities — free functions (SCOP: no library keyword).
// Used by FCI and other hook facets that need poolId + positionKey from hook params.

function fetchPositionKey(
    bytes calldata hookData,
    address sender,
    ModifyLiquidityParams calldata liquidityParams
) pure returns (bytes32) {
    if (isUniswapV4(hookData)) {
        return Position.calculatePositionKey(
            sender,
            liquidityParams.tickLower,
            liquidityParams.tickUpper,
            liquidityParams.salt
        );
    }
    if (isUniswapV3(hookData)) {
        return v3PositionKey(
            sender,
            liquidityParams.tickLower,
            liquidityParams.tickUpper
        );
    }
}

function derivePoolAndPosition(
    address sender,
    PoolKey calldata key,
    ModifyLiquidityParams calldata params,
    bytes calldata hookData
) pure returns (PoolId poolId, bytes32 positionKey) {
    poolId = PoolIdLibrary.toId(key);
    positionKey = fetchPositionKey(hookData, sender, params);
}

function derivePoolAndPosition(
    address sender,
    PoolKey calldata key,
    ModifyLiquidityParams calldata params
) pure returns (PoolId poolId, bytes32 positionKey) {
    poolId = PoolIdLibrary.toId(key);
    positionKey = Position.calculatePositionKey(
        sender, params.tickLower, params.tickUpper, params.salt
    );
}

// Sort two ticks so tickMin <= tickMax.
// Not provided by Uniswap v4-core (Pool.sol only validates tickLower < tickUpper).
function sortTicks(int24 a, int24 b) pure returns (int24 tickMin, int24 tickMax) {
    if (a < b) {
        tickMin = a;
        tickMax = b;
    } else {
        tickMin = b;
        tickMax = a;
    }
}
