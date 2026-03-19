# V3SwapDataV2
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/uniswapV3/types/UniswapV3CallbackData.sol)


```solidity
struct V3SwapDataV2 {
IUniswapV3Pool pool;
address sender;
address recipient;
int256 amount0;
int256 amount1;
uint160 afterSwapSqrtPriceX96;
uint128 afterSwapLiquidity;
int24 afterSwapTick;
}
```

