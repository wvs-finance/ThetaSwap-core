# function setFeeGrowthBaseline
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol)

### setFeeGrowthBaseline(FeeConcentrationIndexStorage, PoolId, bytes32, uint256)

```solidity
function setFeeGrowthBaseline(
FeeConcentrationIndexStorage storage $,
PoolId poolId,
bytes32 positionKey,
uint256 feeGrowth0X128
) ;
```

### setFeeGrowthBaseline(PoolId, bytes32, uint256)

```solidity
function setFeeGrowthBaseline(PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) ;
```

