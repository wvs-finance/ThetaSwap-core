//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {SwapParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";


interface IJITLiquidityEntryPoint {
    // NOTE: This is the entry point for JIT Routers
    // to be part of the system

    function subscribe(address liquidityManager,bytes memory poolData) external;

    function onSwap(
        bytes memory swapData
    ) external returns(bytes memory jitLiquidityData);



}