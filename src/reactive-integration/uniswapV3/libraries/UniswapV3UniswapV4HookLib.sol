// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    V3SwapData, V3MintData, V3BurnData, V3CollectData
    // V3SwapDataV2, V3BurnDataV2, V3MintDataV2, V3CollectDataV2
} from "../types/UniswapV3CallbackData.sol";
import {
    AfterSwapData, AfterAddLiquidityData, AfterRemoveLiquidityData
} from "../../uniswapV4/types/HooksCallData.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {V3_FLAG, encodeSwapHookData, encodeMintHookData, encodeBurnHookData} from "../types/HookDataFlagsMod.sol";

function toAfterSwapData(V3SwapData memory data, PoolKey memory key) pure returns (AfterSwapData memory) {
    return AfterSwapData({
        sender: address(data.pool),
        key: key,
        params: SwapParams({zeroForOne: true, amountSpecified: 0, sqrtPriceLimitX96: 0}),
        delta: BalanceDelta.wrap(0),
        hookData: encodeSwapHookData(V3_FLAG, data.tickBefore, data.tick)
    });
}

function toAfterAddLiquidityData(V3MintData memory data, PoolKey memory key) pure returns (AfterAddLiquidityData memory) {
    return AfterAddLiquidityData({
        sender: data.owner,
        key: key,
        params: ModifyLiquidityParams({tickLower: data.tickLower, tickUpper: data.tickUpper, liquidityDelta: int256(uint256(data.liquidity)), salt: bytes32(0)}),
        delta: BalanceDelta.wrap(0),
        feesAccrued: BalanceDelta.wrap(0),
        hookData: encodeMintHookData(V3_FLAG, data.owner, data.tickLower, data.tickUpper, data.liquidity)
    });
}

function toAfterRemoveLiquidityData(V3BurnData memory data, PoolKey memory key) pure returns (AfterRemoveLiquidityData memory) {
    return AfterRemoveLiquidityData({
        sender: data.owner,
        key: key,
        params: ModifyLiquidityParams({tickLower: data.tickLower, tickUpper: data.tickUpper, liquidityDelta: -int256(uint256(data.liquidity)), salt: bytes32(0)}),
        delta: BalanceDelta.wrap(0),
        feesAccrued: BalanceDelta.wrap(0),
        hookData: encodeBurnHookData(V3_FLAG, data.owner, data.tickLower, data.tickUpper, data.liquidity)
    });
}
