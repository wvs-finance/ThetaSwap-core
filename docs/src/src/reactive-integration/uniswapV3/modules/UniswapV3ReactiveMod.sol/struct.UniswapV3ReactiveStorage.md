# UniswapV3ReactiveStorage
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/uniswapV3/modules/UniswapV3ReactiveMod.sol)


```solidity
struct UniswapV3ReactiveStorage {
mapping(uint256 => mapping(address => bool)) poolWhitelist;
mapping(uint256 => mapping(address => TickShadow)) tickShadow;
}
```

