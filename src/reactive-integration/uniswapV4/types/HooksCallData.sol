// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";

struct BeforeInitializeData {
    address sender;
    PoolKey key;
    uint160 sqrtPriceX96;
}

struct AfterInitializeData {
    address sender;
    PoolKey key;
    uint160 sqrtPriceX96;
    int24 tick;
}

struct BeforeAddLiquidityData {
    address sender;
    PoolKey key;
    ModifyLiquidityParams params;
    bytes hookData;
}

struct AfterAddLiquidityData {
    address sender;
    PoolKey key;
    ModifyLiquidityParams params;
    BalanceDelta delta;
    BalanceDelta feesAccrued;
    bytes hookData;
}

struct BeforeRemoveLiquidityData {
    address sender;
    PoolKey key;
    ModifyLiquidityParams params;
    bytes hookData;
}

struct AfterRemoveLiquidityData {
    address sender;
    PoolKey key;
    ModifyLiquidityParams params;
    BalanceDelta delta;
    BalanceDelta feesAccrued;
    bytes hookData;
}

struct BeforeSwapData {
    address sender;
    PoolKey key;
    SwapParams params;
    bytes hookData;
}

struct AfterSwapData {
    address sender;
    PoolKey key;
    SwapParams params;
    BalanceDelta delta;
    bytes hookData;
}

struct BeforeDonateData {
    address sender;
    PoolKey key;
    uint256 amount0;
    uint256 amount1;
    bytes hookData;
}

struct AfterDonateData {
    address sender;
    PoolKey key;
    uint256 amount0;
    uint256 amount1;
    bytes hookData;
}
