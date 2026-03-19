# V3CallbackRouter
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol)

**Inherits:**
IUniswapV3MintCallback, IUniswapV3SwapCallback

Minimal router enabling EOAs to mint/swap on V3 pools via broadcast.
Callbacks pull tokens from msg.sender (stored in calldata). Not for production.


## Functions
### mint


```solidity
function mint(IUniswapV3Pool pool, address recipient, int24 tickLower, int24 tickUpper, uint128 amount)
    external
    returns (uint256 amount0, uint256 amount1);
```

### swap


```solidity
function swap(
    IUniswapV3Pool pool,
    address recipient,
    bool zeroForOne,
    int256 amountSpecified,
    uint160 sqrtPriceLimitX96
) external returns (int256 amount0, int256 amount1);
```

### uniswapV3MintCallback


```solidity
function uniswapV3MintCallback(uint256 amount0Owed, uint256 amount1Owed, bytes calldata data) external override;
```

### uniswapV3SwapCallback


```solidity
function uniswapV3SwapCallback(int256 amount0Delta, int256 amount1Delta, bytes calldata data) external override;
```

## Structs
### CallbackData

```solidity
struct CallbackData {
    address token0;
    address token1;
    address payer;
}
```

