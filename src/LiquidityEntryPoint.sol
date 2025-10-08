//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {ILiquidityEntryPoint} from "./interfaces/ILiquidityEntryPoint.sol";

import {
    OnboardingData,
    Commitment,
    DEX
} from ".types/Shared.sol";


//=============================UNISWAP-V4========================
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";

// NOTE: This contract is upgradeable, as more liquidity Aggregators join
// New versions are added to the storage, same if they quit
abstract contract LiquidityEntryPoint is ILiquidityEntryPoint{
    
    struct DEX_CONFIG{
        address hook;
        address poolManager;
    }

    mapping(DEX => DEX_CONFIG) internal _dexEntryPoint;

    function onboard_liquidity(bytes memory _onboardingData) external{
        OnboardingData memory onboardingData = abi.decode(
            _onboardingData,
            (OnbordingData)
        );
        _onboard_liquidity(onboardingData);
    }

    function _onboard_liquidity(OnbardingData memory _onboardingData) internal{
        if (_onboardingData.dex == DEX.UNISWAP_V4){
            
            DEX_CONFIG memory uniswapDexConfig = DEX_CONFIG(
                // NOTE:
            );

            PoolKey memory poolKey = PoolKey(
                Currency.wrap(_onboardingData.token0),
                Currency.wrap(_onboardingData.token1),

            );

        }
    }




}