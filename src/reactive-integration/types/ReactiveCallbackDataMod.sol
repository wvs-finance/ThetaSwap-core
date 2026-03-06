// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";

// Decoded V3 event data for reactive callbacks.
// Each struct mirrors a V3 event's indexed + data fields,
// pre-decoded by the reactive subscription contract.

// V3 Swap(address sender, address recipient, int256 amount0, int256 amount1,
//         uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
struct V3SwapData {
    IUniswapV3Pool pool;
    int24 tick;
}

// V3 Mint(address sender, address owner, int24 tickLower, int24 tickUpper,
//         uint128 amount, uint256 amount0, uint256 amount1)
struct V3MintData {
    IUniswapV3Pool pool;
    address owner;
    int24 tickLower;
    int24 tickUpper;
    uint128 liquidity;
}

// V3 Burn(address owner, int24 tickLower, int24 tickUpper,
//         uint128 amount, uint256 amount0, uint256 amount1)
// Signals position removal. Fee data comes from accumulated Collect events.
struct V3BurnData {
    IUniswapV3Pool pool;
    address owner;
    int24 tickLower;
    int24 tickUpper;
    uint128 liquidity;
}

// V3 Collect(address owner, address recipient, int24 tickLower, int24 tickUpper,
//            uint128 amount0, uint128 amount1)
// Fee amounts collected from the position. Accumulated over lifetime, consumed on Burn.
struct V3CollectData {
    IUniswapV3Pool pool;
    address owner;
    int24 tickLower;
    int24 tickUpper;
    uint128 feeAmount0;
    uint128 feeAmount1;
}
