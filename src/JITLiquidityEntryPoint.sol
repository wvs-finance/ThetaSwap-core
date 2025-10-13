//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {
    PoolKey,
    IJITLiquidityEntryPoint
} from "./interfaces/IJITLiquidityEntryPoint.sol";


import {
    PoolId,
    PoolIdLibrary
} from "@uniswap/v4-core/src/types/PoolId.sol";

import {IParityTaxHook} from "./interfaces/IParityTaxHook.sol";


import {EnumerableMap} from "@openzeppelin/contracts/utils/struct/EnumerableMap.sol";

contract JITLiquidityEntryPoint is  IJITLiquidityEntryPoint{
    using PoolIdLibrary for PoolKey;
    using EnumerableMap for EnumerableMap.Bytes32ToAddressMap;

    IParityTaxHook public immutable parityTaxHook;

    EnumerableMap.Bytes32ToAddressMap jitLiquidityManagersOnPool;



    constructor(IParityTaxHook _parityTaxHook){
        parityTaxHook = _parityTaxHook;
    }

    function subscribe(
        address liquidityManager,
        PoolKey calldata poolKey
    ) external{
        if (address(poolKey.hooks) != address(parityTaxHook)) revert("Invalid PoolKey Hook Address");
        PoolId poolId = poolKey.toId();
        
        jitLiquidityManagersOnPool.set(
            PoolId.unwrap(poolId),
            liquidityManager
        );
    }

    function onboard_liquidity(bytes memory onboardingData) external{

    }



}