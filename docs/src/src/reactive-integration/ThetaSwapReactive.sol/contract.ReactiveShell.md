# ReactiveShell
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/ThetaSwapReactive.sol)


## State Variables
### service

```solidity
ISubscriptionService immutable service
```


## Functions
### constructor


```solidity
constructor(address adapter_, address payable service_) payable;
```

### onlyVM


```solidity
modifier onlyVM() ;
```

### debtFree


```solidity
modifier debtFree() ;
```

### react


```solidity
function react(IReactive.LogRecord calldata log) external onlyVM debtFree;
```

### receive


```solidity
receive() external payable;
```

