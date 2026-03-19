# getFeeGrowthInside0
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/types/FeeGrowthReaderMod.sol)


```solidity
function getFeeGrowthInside0(IPoolManager manager, PoolId poolId, int24 currentTick, int24 tickLower, int24 tickUpper)
view
returns (uint256 feeGrowthInside0X128);
```

