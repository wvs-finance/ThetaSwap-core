# FeeConcentrationIndexStorage
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol)


```solidity
struct FeeConcentrationIndexStorage {
// Co-primary state per pool: (accumulatedSum, thetaSum, posCount)
mapping(PoolId => FeeConcentrationState) fciState;
// Per-pool tick range registry (positions grouped by range, per-range swap counters)
mapping(PoolId => TickRangeRegistry) registries;
// Per-position snapshot of feeGrowthInside0X128 at add time.
mapping(PoolId => mapping(bytes32 => uint256)) feeGrowthBaseline0;
// PoolManager reference — stored in facet's own namespace, not read from MasterHook.
// MasterHook is protocol-agnostic and does not guarantee a poolManager field.
IPoolManager poolManager;
}
```

