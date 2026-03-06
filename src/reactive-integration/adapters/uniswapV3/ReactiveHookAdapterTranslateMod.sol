// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";

import {V3SwapData, V3MintData, V3BurnData, V3CollectData} from "../../types/ReactiveCallbackDataMod.sol";
import {fromV3Pool} from "../../libraries/PoolKeyExtMod.sol";

// Translates V3 event data into V4 hook calldata.
// The reactive subscription contract calls these to build arguments
// for FeeConcentrationIndex's standard hook functions.

// V3 Swap → afterSwap calldata
// hookData carries the swap tick for FCI to consume.
function adaptV3Swap(
    V3SwapData calldata data,
    address adapter
) view returns (
    PoolKey memory key,
    SwapParams memory params,
    BalanceDelta delta,
    bytes memory hookData
) {
    key = fromV3Pool(data.pool, adapter);
    // SwapParams fields unused by FCI — zero is fine.
    params = SwapParams({zeroForOne: true, amountSpecified: 0, sqrtPriceLimitX96: 0});
    delta = BalanceDelta.wrap(0);
    hookData = abi.encode(data.tick);
}

// V3 Mint → afterAddLiquidity calldata
function adaptV3Mint(
    V3MintData calldata data,
    address adapter
) view returns (
    address sender,
    PoolKey memory key,
    ModifyLiquidityParams memory params,
    BalanceDelta delta,
    BalanceDelta feesAccrued,
    bytes memory hookData
) {
    sender = data.owner;
    key = fromV3Pool(data.pool, adapter);
    params = ModifyLiquidityParams({
        tickLower: data.tickLower,
        tickUpper: data.tickUpper,
        liquidityDelta: int256(uint256(data.liquidity)),
        salt: bytes32(0)
    });
    delta = BalanceDelta.wrap(0);
    feesAccrued = BalanceDelta.wrap(0);
    hookData = "";
}

// V3 Burn → afterRemoveLiquidity calldata
// feeAmount0/feeAmount1: accumulated Collect fees for this position.
function adaptV3Burn(
    V3BurnData calldata data,
    uint256 feeAmount0,
    uint256 feeAmount1,
    address adapter
) view returns (
    address sender,
    PoolKey memory key,
    ModifyLiquidityParams memory params,
    BalanceDelta delta,
    BalanceDelta feesAccrued,
    bytes memory hookData
) {
    sender = data.owner;
    key = fromV3Pool(data.pool, adapter);
    params = ModifyLiquidityParams({
        tickLower: data.tickLower,
        tickUpper: data.tickUpper,
        liquidityDelta: -int256(uint256(data.liquidity)),
        salt: bytes32(0)
    });
    delta = BalanceDelta.wrap(0);
    feesAccrued = BalanceDelta.wrap(0);
    hookData = abi.encode(feeAmount0, feeAmount1);
}
