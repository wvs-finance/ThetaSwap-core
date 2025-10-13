//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {ILiquidityEntryPoint} from "./interfaces/ILiquidityEntryPoint.sol";
import {IHooks} from "@uniswap/v4-core/src/libraries/IHooks.sol";

import {
    OnboardingData,
    Commitment,
    DEX
} from ".types/Shared.sol";


//=============================UNISWAP-V4========================
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
// NOTE: This contract is upgradeable, as more liquidity Aggregators join
// New versions are added to the storage, same if they quit
abstract contract LiquidityEntryPoint is ILiquidityEntryPoint, AccessControl{
    
    
    constructor(){
        // NOTE: Deployer is the admin
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

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
            
            DEX_CONFIG memory uniswapDexConfig = _dexEntryPoint[DEX.UNISWAP_V4];
            PoolKey memory poolKey = PoolKey({
                currency0: Currency.wrap(token0),
                currency1: Currency.wrap(token1),
                fee: uint24(_onboardingData.currentFee),
                tickSpacing: uint24(_onboardingData.tickSpacing),
                hooks: IHooks(_dexEntryPoint.hook)
            });


        }
    }

    function setDexConfig(
        DEX _dex,
        DEX_CONFIG calldata _dexConfig
    ) external onlyRole(DEFAULT_ADMIN_ROLE){
        _dexEntryPoint[_dex] = _dexConfig;
    }


}