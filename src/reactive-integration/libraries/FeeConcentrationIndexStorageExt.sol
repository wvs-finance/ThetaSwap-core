// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {isUniswapV3Reactive} from "../uniswapV3/types/HookDataFlagsMod.sol";
import {
    t_storeTick, t_readTick,
    t_cacheRemovalData, t_readRemovalData
} from "../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";

function writeCacheTick(bytes calldata hookData, int24 tick) {
    if (isUniswapV3Reactive(hookData)) return;
    t_storeTick(tick);
}

function readCacheTick(bytes calldata hookData) returns (int24 tick) {
    if (isUniswapV3Reactive(hookData)) return 0;
    return t_readTick();
}

function writeCacheRemovalData(bytes calldata hookData, uint256 feeLast0, uint128 posLiquidity, uint256 rangeFeeGrowth0) {
    if (isUniswapV3Reactive(hookData)) return;
    t_cacheRemovalData(feeLast0, posLiquidity, rangeFeeGrowth0);
}

function readCacheRemovalData(bytes calldata hookData) returns (uint256 feeLast0, uint128 posLiquidity, uint256 rangeFeeGrowth0) {
    if (isUniswapV3Reactive(hookData)) return (0, 0, 0);
    return t_readRemovalData();
}
