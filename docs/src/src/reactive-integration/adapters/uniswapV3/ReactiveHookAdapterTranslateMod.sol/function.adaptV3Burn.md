# adaptV3Burn
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapterTranslateMod.sol)


```solidity
function adaptV3Burn(V3BurnData calldata data, uint256 feeAmount0, uint256 feeAmount1, address adapter)
view
returns (
    address sender,
    PoolKey memory key,
    ModifyLiquidityParams memory params,
    BalanceDelta delta,
    BalanceDelta feesAccrued,
    bytes memory hookData
);
```

