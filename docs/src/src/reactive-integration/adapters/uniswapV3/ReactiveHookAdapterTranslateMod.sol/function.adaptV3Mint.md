# adaptV3Mint
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapterTranslateMod.sol)


```solidity
function adaptV3Mint(V3MintData calldata data, address adapter)
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

