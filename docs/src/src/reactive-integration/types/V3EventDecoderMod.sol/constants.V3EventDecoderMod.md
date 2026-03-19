# Constants
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/types/V3EventDecoderMod.sol)

### V3_SWAP_SIG

```solidity
uint256 constant V3_SWAP_SIG = uint256(keccak256("Swap(address,address,int256,int256,uint160,uint128,int24)"))
```

### V3_MINT_SIG

```solidity
uint256 constant V3_MINT_SIG = uint256(keccak256("Mint(address,address,int24,int24,uint128,uint256,uint256)"))
```

### V3_BURN_SIG

```solidity
uint256 constant V3_BURN_SIG = uint256(keccak256("Burn(address,int24,int24,uint128,uint256,uint256)"))
```

### V3_COLLECT_SIG

```solidity
uint256 constant V3_COLLECT_SIG = uint256(keccak256("Collect(address,address,int24,int24,uint128,uint128)"))
```

