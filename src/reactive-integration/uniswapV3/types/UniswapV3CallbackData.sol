// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";


// note
struct V3SwapDataV2{
    IUniswapV3Pool pool;
    address sender;
    address recipient;
    int256 amount0;
    int256 amount1;
    uint160 afterSwapSqrtPriceX96;
    uint128 afterSwapLiquidity;
    int24 afterSwapTick;
}
    
struct V3SwapData {
    IUniswapV3Pool pool;
    int24 tickBefore;
    int24 tick;
}

struct V3MintDataV2{
    IUniswapV3Pool pool;
    address liquidityProvider; // maps to event owner field
    int24 tickLower;
    int24 tickUpper;
    uint128 liquidity;
    uint256 liquidityAmount0;
    uint256 liquidityAmount1;
}

struct V3MintData {
    IUniswapV3Pool pool;
    address owner;
    int24 tickLower;
    int24 tickUpper;
    uint128 liquidity;
}


struct V3BurnDataV2{
    IUniswapV3Pool pool;
    address liquidityProvider; // maps to the owner field
    int24 tickLower;
    int24 tickUpper;
    uint128 liquidity;
    uint256 liquidityAmount0;
    uint256 liquidityAmount1;
}
struct V3BurnData {
    IUniswapV3Pool pool;
    address owner;
    int24 tickLower;
    int24 tickUpper;
    uint128 liquidity;
}

struct V3CollectDataV2{
    IUniswapV3Pool pool;
    address liquidityProvider; // maps to the owner field
    address recipiant; // who receives the fees
    int24 tickLower;
    int24 tickUpper;
    uint128 amount0; // note: This needs to be filtered for non-zeroa moutns as there
    // are events where the lp does not collect fees
    uint128 amount1;

}
struct V3CollectData {
    IUniswapV3Pool pool;
    address owner;
    int24 tickLower;
    int24 tickUpper;
    uint128 feeAmount0;
    uint128 feeAmount1;
}
