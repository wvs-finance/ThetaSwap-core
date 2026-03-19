# function deregisterPosition
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol)

### deregisterPosition(FeeConcentrationIndexStorage, PoolId, bytes32, uint128)

```solidity
function deregisterPosition(
FeeConcentrationIndexStorage storage $,
PoolId poolId,
bytes32 positionKey,
uint128 posLiquidity
) returns (TickRange rk, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq);
```

### deregisterPosition(PoolId, bytes32, uint128)

```solidity
function deregisterPosition(PoolId poolId, bytes32 positionKey, uint128 posLiquidity)
returns (TickRange rk, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq);
```

