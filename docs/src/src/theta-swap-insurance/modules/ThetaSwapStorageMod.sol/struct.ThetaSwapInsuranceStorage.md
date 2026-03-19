# ThetaSwapInsuranceStorage
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/theta-swap-insurance/modules/ThetaSwapStorageMod.sol)


```solidity
struct ThetaSwapInsuranceStorage {
// positionKey → PremiumFactor committed by PLP.
// Zero means not registered.
mapping(PoolId => mapping(bytes32 => PremiumFactor)) registrations;
// ERC6909 claims token (the PoolManager implements this).
// Used solely for operator checks — PLP must grant hook operator status.
IERC6909Claims feeClaimsToken;
}
```

