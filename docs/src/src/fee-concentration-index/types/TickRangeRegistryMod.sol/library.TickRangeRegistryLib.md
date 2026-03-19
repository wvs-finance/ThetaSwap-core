# TickRangeRegistryLib
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/types/TickRangeRegistryMod.sol)


## Functions
### register


```solidity
function register(
    TickRangeRegistry storage self,
    TickRange rk,
    bytes32 positionKey,
    int24 tickLower,
    int24 tickUpper,
    uint128 posLiquidity
) internal;
```

### deregister


```solidity
function deregister(
    TickRangeRegistry storage self,
    bytes32 positionKey,
    uint128 /* posLiquidity */
)
    internal
    returns (TickRange rk, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalLiquidityBefore);
```

### incrementRangeSwapCount


```solidity
function incrementRangeSwapCount(TickRangeRegistry storage self, TickRange rk) internal;
```

### positionsInRange


```solidity
function positionsInRange(TickRangeRegistry storage self, TickRange rk) internal view returns (bytes32[] memory);
```

### rangeLength


```solidity
function rangeLength(TickRangeRegistry storage self, TickRange rk) internal view returns (uint256);
```

### contains


```solidity
function contains(TickRangeRegistry storage self, TickRange rk, bytes32 positionKey) internal view returns (bool);
```

### getLifetime


```solidity
function getLifetime(TickRangeRegistry storage self, bytes32 positionKey) internal view returns (SwapCount);
```

### activeRangeCount


```solidity
function activeRangeCount(TickRangeRegistry storage self) internal view returns (uint256);
```

### activeRangeAt


```solidity
function activeRangeAt(TickRangeRegistry storage self, uint256 index) internal view returns (bytes32);
```

