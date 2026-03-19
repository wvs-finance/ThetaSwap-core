# V3CollectDataV2
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/uniswapV3/types/UniswapV3CallbackData.sol)


```solidity
struct V3CollectDataV2 {
IUniswapV3Pool pool;
address liquidityProvider; // maps to the owner field
address recipiant; // who receives the fees
int24 tickLower;
int24 tickUpper;
uint128 amount0; // note: This needs to be filtered for non-zeroa moutns as there
// are events where the lp does not collect fees
uint128 amount1;
}
```

