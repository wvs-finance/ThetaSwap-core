# V3MintDataV2
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/uniswapV3/types/UniswapV3CallbackData.sol)


```solidity
struct V3MintDataV2 {
IUniswapV3Pool pool;
address liquidityProvider; // maps to event owner field
int24 tickLower;
int24 tickUpper;
uint128 liquidity;
uint256 liquidityAmount0;
uint256 liquidityAmount1;
}
```

