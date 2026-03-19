# function derivePoolAndPosition
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/libraries/HookUtilsMod.sol)

### derivePoolAndPosition(address, PoolKey, ModifyLiquidityParams, bytes)

```solidity
function derivePoolAndPosition(
address sender,
PoolKey calldata key,
ModifyLiquidityParams calldata params,
bytes calldata hookData
) pure returns (PoolId poolId, bytes32 positionKey);
```

### derivePoolAndPosition(address, PoolKey, ModifyLiquidityParams)

```solidity
function derivePoolAndPosition(address sender, PoolKey calldata key, ModifyLiquidityParams calldata params)
pure
returns (PoolId poolId, bytes32 positionKey);
```

