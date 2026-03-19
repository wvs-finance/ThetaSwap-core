# ThetaSwapReactive
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/ThetaSwapReactive.sol)


## State Variables
### owner

```solidity
address immutable owner
```


### adapter

```solidity
address immutable adapter
```


### service

```solidity
ISubscriptionService immutable service
```


### vm

```solidity
bool immutable vm
```


## Functions
### constructor


```solidity
constructor(address adapter_, address payable service_) payable;
```

### react


```solidity
function react(IReactive.LogRecord calldata log) external;
```

### registerPool


```solidity
function registerPool(uint256 chainId_, address pool) external;
```

### unregisterPool


```solidity
function unregisterPool(uint256 chainId_, address pool) external;
```

### fund


```solidity
function fund() external payable;
```

### receive


```solidity
receive() external payable;
```

## Errors
### OnlyOwner

```solidity
error OnlyOwner();
```

### OnlyReactVM

```solidity
error OnlyReactVM();
```

### OnlyRN

```solidity
error OnlyRN();
```

