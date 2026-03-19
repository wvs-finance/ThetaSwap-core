# ReactVmStorage
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/modules/ReactVmStorageMod.sol)


```solidity
struct ReactVmStorage {
// Pool whitelist synced from RN instance via self-subscription.
mapping(uint256 => mapping(address => bool)) poolWhitelist;
mapping(uint256 => mapping(address => TickShadow)) tickShadow;
}
```

