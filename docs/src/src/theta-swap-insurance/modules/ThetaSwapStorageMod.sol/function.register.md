# register
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/theta-swap-insurance/modules/ThetaSwapStorageMod.sol)

Called from afterAddLiquidity.
hookData is tightly packed: 16 bytes for uint128 factorRaw.
PremiumFactor type owns deserialization via fromCalldata.


```solidity
function register(PoolId poolId, bytes32 positionKey, bytes calldata hookData, address plp, address hook) ;
```

