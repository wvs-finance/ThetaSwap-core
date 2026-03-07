// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {V3SwapData, V3MintData, V3BurnData, V3CollectData} from "./ReactiveCallbackDataMod.sol";
import {decodeTopic1AsAddress, decodeTopic2AsInt24, decodeTopic3AsInt24} from "./LogRecordExtMod.sol";

// V3-specific event decoders. Extracts typed structs from raw LogRecord fields.
// Each V3 event has a known layout of indexed topics and ABI-encoded data.

// V3 event signatures (canonical form for keccak256)
uint256 constant V3_SWAP_SIG = uint256(keccak256("Swap(address,address,int256,int256,uint160,uint128,int24)"));
uint256 constant V3_MINT_SIG = uint256(keccak256("Mint(address,address,int24,int24,uint128,uint256,uint256)"));
uint256 constant V3_BURN_SIG = uint256(keccak256("Burn(address,int24,int24,uint128,uint256,uint256)"));
uint256 constant V3_COLLECT_SIG = uint256(keccak256("Collect(address,address,int24,int24,uint128,uint128)"));

function decodeV3Swap(IReactive.LogRecord calldata log) pure returns (V3SwapData memory) {
    // Swap: topic_1=sender(indexed), topic_2=recipient(indexed)
    // data: (int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
    (,,,, int24 tick) = abi.decode(log.data, (int256, int256, uint160, uint128, int24));
    return V3SwapData({pool: IUniswapV3Pool(log._contract), tick: tick});
}

function decodeV3Mint(IReactive.LogRecord calldata log) pure returns (V3MintData memory) {
    // Mint: topic_1=owner(indexed), topic_2=tickLower(indexed), topic_3=tickUpper(indexed)
    // data: (address sender, uint128 amount, uint256 amount0, uint256 amount1)
    address owner = decodeTopic1AsAddress(log);
    int24 tickLower = decodeTopic2AsInt24(log);
    int24 tickUpper = decodeTopic3AsInt24(log);
    (, uint128 liquidity,,) = abi.decode(log.data, (address, uint128, uint256, uint256));
    return V3MintData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        liquidity: liquidity
    });
}

function decodeV3Burn(IReactive.LogRecord calldata log) pure returns (V3BurnData memory) {
    // Burn: topic_1=owner(indexed), topic_2=tickLower(indexed), topic_3=tickUpper(indexed)
    // data: (uint128 amount, uint256 amount0, uint256 amount1)
    address owner = decodeTopic1AsAddress(log);
    int24 tickLower = decodeTopic2AsInt24(log);
    int24 tickUpper = decodeTopic3AsInt24(log);
    (uint128 liquidity,,) = abi.decode(log.data, (uint128, uint256, uint256));
    return V3BurnData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        liquidity: liquidity
    });
}

function decodeV3Collect(IReactive.LogRecord calldata log) pure returns (V3CollectData memory) {
    // Collect: topic_1=owner(indexed), topic_2=tickLower(indexed), topic_3=tickUpper(indexed)
    // data: (address recipient, uint128 amount0, uint128 amount1)
    address owner = decodeTopic1AsAddress(log);
    int24 tickLower = decodeTopic2AsInt24(log);
    int24 tickUpper = decodeTopic3AsInt24(log);
    (, uint128 feeAmount0, uint128 feeAmount1) = abi.decode(log.data, (address, uint128, uint128));
    return V3CollectData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        feeAmount0: feeAmount0,
        feeAmount1: feeAmount1
    });
}
