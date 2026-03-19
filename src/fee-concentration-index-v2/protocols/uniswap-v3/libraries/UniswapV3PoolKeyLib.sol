// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
// reference: @fee-concentration-index-v2/libraries/PoolKeyExtLib.sol

/// @dev Builds a V4-shaped PoolKey from a V3 pool address.
/// Reads token0, token1, fee, tickSpacing from the V3 pool contract.
/// Sets hooks to the FCI hook address.
function fromUniswapV3PoolToPoolKey(IUniswapV3Pool pool, IHooks fciHook) view returns (PoolKey memory) {
    return PoolKey({
        currency0: Currency.wrap(pool.token0()),
        currency1: Currency.wrap(pool.token1()),
        fee: pool.fee(),
        tickSpacing: pool.tickSpacing(),
        hooks: fciHook
    });
}
