# TickRangeRegistry
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/types/TickRangeRegistryMod.sol)


```solidity
struct TickRangeRegistry {
// TickRange => set of position keys in that range
mapping(bytes32 => EnumerableSetLib.Bytes32Set) positionsByRange;
// positionKey => its TickRange (reverse lookup for deregister)
mapping(bytes32 => TickRange) rangeKeyOf;
// TickRange => cumulative swap count for this range
mapping(bytes32 => SwapCount) rangeSwapCount;
// positionKey => snapshot of rangeSwapCount at add time
mapping(bytes32 => SwapCount) baselineSwapCount;
// All range keys with >= 1 position (for afterSwap iteration)
EnumerableSetLib.Bytes32Set activeRanges;
// Recover tick bounds from one-way TickRange hash (for intersects check)
mapping(bytes32 => int24) rangeLowerTick;
mapping(bytes32 => int24) rangeUpperTick;
// TickRange => sum of liquidity across all positions in range (for x_k weighting)
mapping(bytes32 => uint128) totalRangeLiquidity;
// positionKey => block.number at registration (for block-based lifetime)
mapping(bytes32 => uint256) positionAddBlock;
}
```

