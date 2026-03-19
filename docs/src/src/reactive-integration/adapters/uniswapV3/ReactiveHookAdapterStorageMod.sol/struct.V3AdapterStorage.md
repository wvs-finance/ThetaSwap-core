# V3AdapterStorage
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapterStorageMod.sol)


```solidity
struct V3AdapterStorage {
// poolId => positionKey => feeGrowthInside0X128 at mint time
mapping(PoolId => mapping(bytes32 => uint256)) feeGrowthSnapshot0;
}
```

