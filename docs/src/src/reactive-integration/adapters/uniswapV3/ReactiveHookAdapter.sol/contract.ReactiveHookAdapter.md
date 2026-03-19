# ReactiveHookAdapter
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol)


## State Variables
### rvmId

```solidity
address public rvmId
```


### owner

```solidity
address immutable owner
```


### authorizedCallers

```solidity
mapping(address => bool) public authorizedCallers
```


## Functions
### constructor


```solidity
constructor(address callbackProxy) payable;
```

### setRvmId


```solidity
function setRvmId(address rvmId_) external;
```

### setAuthorized


```solidity
function setAuthorized(address caller, bool authorized) external;
```

### onV3Swap


```solidity
function onV3Swap(address rvmSender, V3SwapData calldata data) external;
```

### onV3MintTranstionToHook


```solidity
function onV3MintTranstionToHook(address rvmSender, V3MintData calldata data) external;
```

### onV3Mint


```solidity
function onV3Mint(address rvmSender, V3MintData calldata data) external;
```

### onV3Burn


```solidity
function onV3Burn(address rvmSender, V3BurnData calldata data) external;
```

### getIndex


```solidity
function getIndex(
    PoolKey calldata key,
    bool /* reactive */
)
    external
    view
    returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount);
```

### getDeltaPlus


```solidity
function getDeltaPlus(
    PoolKey calldata key,
    bool /* reactive */
)
    external
    view
    returns (uint128 deltaPlus_);
```

### getAtNull


```solidity
function getAtNull(
    PoolKey calldata key,
    bool /* reactive */
)
    external
    view
    returns (uint128 atNull_);
```

### getThetaSum


```solidity
function getThetaSum(
    PoolKey calldata key,
    bool /* reactive */
)
    external
    view
    returns (uint256 thetaSum_);
```

### pay


```solidity
function pay(uint256 amount) external;
```

### receive


```solidity
receive() external payable;
```

### supportsInterface


```solidity
function supportsInterface(bytes4 interfaceId) external pure returns (bool);
```

## Events
### AuthorizedCallerUpdated

```solidity
event AuthorizedCallerUpdated(address indexed caller, bool authorized);
```

### RvmIdUpdated

```solidity
event RvmIdUpdated(address indexed oldRvmId, address indexed newRvmId);
```

## Errors
### OnlyOwner

```solidity
error OnlyOwner();
```

### InvalidRvmId

```solidity
error InvalidRvmId();
```

### InsufficientFunds

```solidity
error InsufficientFunds();
```

### TransferFailed

```solidity
error TransferFailed();
```

