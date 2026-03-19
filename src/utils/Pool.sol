// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {TokenPair} from "./TokenPair.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";

/// @notice Initialize a V4 pool. Optional — not part of seed/approve flow.
function createPoolV4(
    TokenPair memory pair,
    address hookAddress,
    uint24 fee,
    int24 tickSpacing,
    uint160 sqrtPriceX96,
    address poolManager
) returns (PoolKey memory key, PoolId poolId) {
    key = PoolKey({
        currency0: Currency.wrap(pair.token0),
        currency1: Currency.wrap(pair.token1),
        fee: fee,
        tickSpacing: tickSpacing,
        hooks: IHooks(hookAddress)
    });
    poolId = PoolIdLibrary.toId(key);
    IPoolManager(poolManager).initialize(key, sqrtPriceX96);
}

/// @notice Initialize a V3 pool. Optional — not part of seed/approve flow.
///         Calls factory.createPool(token0, token1, fee), then pool.initialize(sqrtPriceX96).
function createPoolV3(
    TokenPair memory pair,
    uint24 fee,
    uint160 sqrtPriceX96,
    address factory
) returns (address pool) {
    pool = IUniswapV3Factory(factory).createPool(pair.token0, pair.token1, fee);
    IUniswapV3Pool(pool).initialize(sqrtPriceX96);
}
