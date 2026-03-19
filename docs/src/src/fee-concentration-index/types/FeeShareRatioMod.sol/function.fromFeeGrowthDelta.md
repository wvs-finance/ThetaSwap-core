# fromFeeGrowthDelta
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/types/FeeShareRatioMod.sol)


```solidity
function fromFeeGrowthDelta(
uint256 rangeFeeGrowthNow0X128,
uint256 positionFeeLast0X128,
uint256 baseline0X128,
uint128 posLiquidity,
uint128 totalRangeLiquidity
) pure returns (FeeShareRatio);
```

