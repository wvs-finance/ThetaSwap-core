//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface ILiquidityEntryPoint{
    function onboard_liquidity(bytes memory onboardingData) external;

}