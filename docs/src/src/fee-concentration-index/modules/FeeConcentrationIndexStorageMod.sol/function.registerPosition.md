# function registerPosition
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol)

### registerPosition(FeeConcentrationIndexStorage, PoolId, TickRange, bytes32, int24, int24, uint128)

```solidity
function registerPosition(
FeeConcentrationIndexStorage storage $,
PoolId poolId,
TickRange rk,
bytes32 positionKey,
int24 tickLower,
int24 tickUpper,
uint128 posLiquidity
) ;
```

### registerPosition(PoolId, TickRange, bytes32, int24, int24, uint128)

```solidity
function registerPosition(
PoolId poolId,
TickRange rk,
bytes32 positionKey,
int24 tickLower,
int24 tickUpper,
uint128 posLiquidity
) ;
```

