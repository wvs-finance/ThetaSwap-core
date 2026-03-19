# FeeConcentrationIndex
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/FeeConcentrationIndex.sol)


## Functions
### constructor


```solidity
constructor(address poolManager_) ;
```

### afterAddLiquidity


```solidity
function afterAddLiquidity(
    address sender,
    PoolKey calldata key,
    ModifyLiquidityParams calldata params,
    BalanceDelta,
    BalanceDelta,
    bytes calldata hookData
) external virtual returns (bytes4, BalanceDelta);
```

### beforeSwap


```solidity
function beforeSwap(address, PoolKey calldata key, SwapParams calldata, bytes calldata hookData)
    external
    virtual
    returns (bytes4, BeforeSwapDelta, uint24);
```

### afterSwap


```solidity
function afterSwap(address, PoolKey calldata key, SwapParams calldata, BalanceDelta, bytes calldata hookData)
    external
    virtual
    returns (bytes4, int128);
```

### beforeRemoveLiquidity


```solidity
function beforeRemoveLiquidity(
    address sender,
    PoolKey calldata key,
    ModifyLiquidityParams calldata params,
    bytes calldata hookData
) external returns (bytes4);
```

### afterRemoveLiquidity


```solidity
function afterRemoveLiquidity(
    address sender,
    PoolKey calldata key,
    ModifyLiquidityParams calldata params,
    BalanceDelta,
    BalanceDelta,
    bytes calldata hookData
) external virtual returns (bytes4, BalanceDelta);
```

### getIndex


```solidity
function getIndex(PoolKey calldata key, bool reactive)
    external
    view
    returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount);
```

### getDeltaPlus


```solidity
function getDeltaPlus(PoolKey calldata key, bool reactive) external view returns (uint128 deltaPlus_);
```

### getAtNull


```solidity
function getAtNull(PoolKey calldata key, bool reactive) external view returns (uint128 atNull_);
```

### getThetaSum


```solidity
function getThetaSum(PoolKey calldata key, bool reactive) external view returns (uint256 thetaSum_);
```

### supportsInterface


```solidity
function supportsInterface(bytes4 interfaceId) external pure returns (bool);
```

