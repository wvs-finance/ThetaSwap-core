# Interface Contract: Fee Concentration Index Hook

**Note**: This is a design document, NOT Solidity code. The actual contract follows SCOP (no `interface` keyword in production — tests only). This documents the external-facing surface.

## Hook Callbacks (called by PoolManager)

These are the Uniswap V4 hook callbacks the contract implements. They are NOT user-facing — they are called automatically by the PoolManager during pool operations.

### afterAddLiquidity

**Trigger**: PoolManager calls after a position is added to a monitored pool.

**Inputs** (from V4 callback signature):
- `PoolKey calldata key` — pool identifier
- `ModifyLiquidityParams calldata params` — contains tickLower, tickUpper, liquidityDelta, salt
- `BalanceDelta delta` — actual token amounts
- `BalanceDelta feesAccrued` — fees accrued
- `bytes calldata hookData` — arbitrary hook data

**Effects**:
1. Derive positionKey from (msg.sender, params.tickLower, params.tickUpper, params.salt)
2. Initialize swapCount[positionKey] = 0
3. Register positionKey in TickRangePositionSet under rangeKey(tickLower, tickUpper)

**Returns**: `bytes4` (hook selector) + `BalanceDelta` (no delta modification)

---

### afterSwap

**Trigger**: PoolManager calls after every swap in a monitored pool.

**Inputs** (from V4 callback signature):
- `PoolKey calldata key` — pool identifier
- `SwapParams calldata params` — swap parameters
- `BalanceDelta delta` — swap result
- `bytes calldata hookData` — arbitrary hook data

**Effects**:
1. Read tick before and after swap (from pool state)
2. Walk V4 tick bitmap over [tick_before, tick_after] range
3. For each initialized tick boundary found, look up rangeKey
4. For each position in matching ranges, increment swapCount by 1

**Gas budget**: < 50,000 gas for up to 10 active positions (SC-004)

**Returns**: `bytes4` (hook selector) + `int128` (no fee override)

---

### afterRemoveLiquidity

**Trigger**: PoolManager calls after a position is removed from a monitored pool.

**Inputs** (from V4 callback signature):
- `PoolKey calldata key` — pool identifier
- `ModifyLiquidityParams calldata params` — contains tickLower, tickUpper, liquidityDelta, salt
- `BalanceDelta delta` — actual token amounts
- `BalanceDelta feesAccrued` — fees accrued
- `bytes calldata hookData` — arbitrary hook data

**Effects**:
1. Derive positionKey
2. Read lifetime = swapCount[positionKey]
3. If lifetime == 0: skip index update (FR-010)
4. If lifetime > 0:
   a. Compute x_k = feeGrowthInside / feeGrowthGlobal (Q128)
   b. Compute theta_k = 1 / lifetime (Q128)
   c. accumulatedHHI[poolId] += theta_k * x_k^2
5. Deregister from TickRangePositionSet
6. Delete swapCount[positionKey]

**Gas budget**: < 100,000 gas (SC-005)

**Returns**: `bytes4` (hook selector) + `BalanceDelta` (no delta modification)

---

## View Functions (user-facing)

### getIndex

**Description**: Returns the current fee concentration and dispersion indices for a pool.

**Input**: `PoolId poolId`

**Output**: `(uint256 A_T, uint256 B_T)` — both Q128 fixed-point values in [0, 1]

**Computation**:
```
sum = accumulatedHHI[poolId]
A_T = sqrt(sum << 128)           // Q128
if A_T > 2^128: A_T = 2^128     // cap at 1
B_T = 2^128 - A_T               // complement
```

### getSwapCount

**Description**: Returns the current swap count for a specific position.

**Input**: `PoolId poolId`, `bytes32 positionKey`

**Output**: `SwapCount` (uint256)

### getPositionsInRange

**Description**: Returns position keys registered in a specific tick range.

**Input**: `PoolId poolId`, `int24 tickLower`, `int24 tickUpper`

**Output**: `bytes32[] memory positionKeys`
