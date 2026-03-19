# getPositionFeeGrowthInsideLast0
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/libraries/FeeGrowthReaderExt.sol)


```solidity
function getPositionFeeGrowthInsideLast0(
bytes calldata hookData,
IPoolManager manager,
PoolId poolId,
bytes32 positionKey
) view returns (uint128 liquidity, uint256 feeGrowthInside0LastX128);
```

