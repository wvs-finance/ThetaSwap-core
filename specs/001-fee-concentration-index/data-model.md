# Data Model: Fee Concentration Index

**Feature**: [spec.md](./spec.md) | **Research**: [research.md](./research.md)

## Entities

### 1. SwapCount

**Description**: Per-position counter tracking how many swaps used a position's liquidity. Incremented on afterSwap only when the swap touches ticks within the position's [tickLower, tickUpper] range.

| Field | Type | Description |
|-------|------|-------------|
| value | uint32 | Accumulated swap count for this position |

**UDVT**: `type SwapCount is uint32;`

**Validation rules**:
- SwapCount is monotonically non-decreasing (never decremented)
- Initialized to 0 on afterAddLiquidity
- Read on afterRemoveLiquidity as the position's lifetime
- Max ~4.3B swaps; theta precision floor = 2^96

**State transitions**:
```
Created(0) --[afterSwap if tick in range]--> Incremented(n+1)
Incremented(n) --[afterSwap if tick in range]--> Incremented(n+1)
Incremented(n) --[afterSwap if tick NOT in range]--> Incremented(n) (no change)
Created(0) or Incremented(n) --[afterRemoveLiquidity]--> Consumed (read as lifetime, then deleted)
```

---

### 2. FeeShareRatio

**Description**: The ratio x_k = positionFeeDelta / rangeFeeDelta measuring what fraction of fees generated during this position's lifetime were captured by the position. Delta-based (Option B): scoped to position's actual lifetime using feeGrowthInside baseline snapshot. Always in [0, 1]. Stored as Q128 fixed-point (uint128).

| Field | Type | Description |
|-------|------|-------------|
| value | uint128 | Q128 fixed-point value in [0, type(uint128).max] representing [0, 1] |

**UDVT**: `type FeeShareRatio is uint128;`

**Validation rules**:
- Must be in [0, 1] (i.e., raw value in [0, type(uint128).max])
- If rangeFeeDelta == 0, then x_k = 0
- Computed once at removal time from feeGrowth deltas, not stored persistently
- 1.0 capped at type(uint128).max (1 wei precision loss)
- Compatible with V4StateReader.getFeeGrowthInsideLast and getFeeGrowthInside

**Computation** (at afterRemoveLiquidity):
```
rangeFeeGrowthNow = V4StateReader.getFeeGrowthInside(manager, poolId, currentTick, tickLower, tickUpper)
positionFeeDelta  = rangeFeeGrowthNow - position.feeGrowthInsideLast  // V4 tracks this
rangeFeeDelta     = rangeFeeGrowthNow - feeGrowthInsideBaseline[positionKey]  // our baseline
x_k = fromFeeGrowth(positionFeeDelta, rangeFeeDelta)
```

---

### 3. AccumulatedHHI

**Description**: Running sum of (x_k^2 / lifetime) terms across all removed positions. x_k is delta-based fee share ratio computed at removal. A_T = sqrt(accumulatedSum), B_T = 1 - A_T computed lazily on read.

| Field | Type | Description |
|-------|------|-------------|
| value | uint256 | Q128 fixed-point accumulated sum of (x_k^2 / lifetime) per removed position |

**UDVT**: `type AccumulatedHHI is uint256;`

**Validation rules**:
- Monotonically non-decreasing (additive accumulation only)
- Each term x_k^2 / lifetime is non-negative and bounded by 1/lifetime
- A_T = sqrt(accumulatedSum) capped at 1 (uint128: type(uint128).max) per FR-009
- B_T = 1 - A_T capped at 0 per FR-009

**State transitions**:
```
Zero(0) --[first afterRemoveLiquidity]--> Accumulated(term_1)
Accumulated(sum) --[afterRemoveLiquidity]--> Accumulated(sum + x_k^2 / lifetime)
```

**Arithmetic** (on afterRemoveLiquidity):
```
xSquared = x_k.square()                         // Q128
term = xSquared / lifetime                       // Q128 / uint32 = Q128
accumulatedSum += term                           // Q128 additive
```

**Read**:
```
A_T = sqrt(accumulatedSum << 128)                // sqrt(Q256) = Q128
if A_T > type(uint128).max: A_T = type(uint128).max
B_T = type(uint128).max - A_T
```

---

### 4. TickRangePositionSet

**Description**: Data structure that groups position keys by their (tickLower, tickUpper) pair. Enables O(1) lookup per unique tick range on afterSwap and sequential iteration of all positions within a range.

| Field | Type | Description |
|-------|------|-------------|
| positionKeys | mapping(bytes32 rangeKey => bytes32[]) | Array of position keys per tick range |
| indexInArray | mapping(bytes32 positionKey => uint256) | Index of position key in array for O(1) removal |
| rangeKeyOf | mapping(bytes32 positionKey => bytes32) | Reverse mapping: position -> its range key |

**Key derivation**:
```
rangeKey = keccak256(abi.encode(tickLower, tickUpper))
positionKey = keccak256(abi.encode(owner, tickLower, tickUpper, salt))
```

**Validation rules**:
- A position key appears in exactly one range (enforced by rangeKeyOf mapping)
- When positionKeys[rangeKey].length == 0, the range entry is deleted (FR-002b)
- No duplicate position keys within a range array

**Operations**:

| Operation | Trigger | Gas (est.) | Description |
|-----------|---------|------------|-------------|
| register | afterAddLiquidity | ~60k | Push positionKey to array, set index, set reverse mapping |
| deregister | afterRemoveLiquidity | ~15k | Swap-and-pop from array, update moved element's index, clear mappings |
| lookup | afterSwap | ~2.1k/position | Read positionKeys[rangeKey] for a given tick range |

**State transitions**:
```
Empty --[register(first position)]--> Active(1 position)
Active(n) --[register]--> Active(n+1)
Active(n>1) --[deregister]--> Active(n-1)
Active(1) --[deregister last]--> Deleted (range key removed entirely)
```

---

### 5. PositionLifetime

**Description**: Composite record tracking a position's lifecycle from add to remove. Not a stored struct — logically composed of SwapCount + feeGrowthInsideBaseline + registration in TickRangePositionSet.

| Field | Type | Source |
|-------|------|--------|
| positionKey | bytes32 | Derived from (owner, tickLower, tickUpper, salt) |
| swapCount | SwapCount | Stored in mapping(PoolId => mapping(bytes32 => SwapCount)) |
| feeGrowthInsideBaseline | uint256 | Snapshot of feeGrowthInside(range) at add time |
| tickLower | int24 | From ModifyLiquidityParams in callback |
| tickUpper | int24 | From ModifyLiquidityParams in callback |

**Lifecycle** (maps to FR-001 through FR-003):
```
afterAddLiquidity:
  1. Derive positionKey
  2. Initialize swapCount[positionKey] = 0
  3. Snapshot feeGrowthInsideBaseline[positionKey] = feeGrowthInside(range, now)
  4. Register in TickRangePositionSet

afterSwap (for each position in overlapping ranges):
  5. swapCount[positionKey] += 1

afterRemoveLiquidity:
  6. lifetime = swapCount[positionKey]
  7. Skip if lifetime == 0 (FR-010)
  8. Compute x_k from feeGrowth deltas (positionFeeDelta / rangeFeeDelta)
  9. term = x_k^2 / lifetime
  10. accumulatedHHI += term
  11. Deregister from TickRangePositionSet
  12. Delete swapCount[positionKey]
  13. Delete feeGrowthInsideBaseline[positionKey]
```

---

## Relationships

```
PoolId (1) -------- (1) AccumulatedHHI
PoolId (1) -------- (*) TickRangePositionSet ranges
TickRange (1) ----- (*) PositionKeys (via TickRangePositionSet)
PositionKey (1) --- (1) SwapCount
PositionKey (1) --- (1) feeGrowthInsideBaseline
PositionKey (1) --- (1) TickRange (via rangeKeyOf reverse mapping)
```

## Storage Layout (Hook Contract)

```solidity
// Per-pool accumulated index
mapping(PoolId => AccumulatedHHI) internal accumulatedHHI;

// Per-position swap count
mapping(PoolId => mapping(bytes32 positionKey => SwapCount)) internal swapCounts;

// Per-position feeGrowthInside baseline (snapshot at add time for delta computation)
mapping(PoolId => mapping(bytes32 positionKey => uint256)) internal feeGrowthInsideBaseline;

// Tick range registry (per pool)
mapping(PoolId => mapping(bytes32 rangeKey => bytes32[])) internal positionsByRange;
mapping(PoolId => mapping(bytes32 positionKey => uint256)) internal positionIndex;
mapping(PoolId => mapping(bytes32 positionKey => bytes32)) internal positionRangeKey;
```

## Edge Cases (from spec)

| Case | Condition | Behavior |
|------|-----------|----------|
| Zero lifetime | lifetime == 0 | Skip index update (no swaps used this position) |
| Zero rangeFeeDelta | rangeFeeDelta == 0 | x_k = 0 (no fees generated during position's lifetime) |
| A_T overflow | sqrt(accumulatedSum) > 1 | Cap A_T = 1, B_T = 0 |
| JIT position | lifetime == 1 | term = x_k^2 / 1 = x_k^2 directly |
| Same-block batch | Multiple removals in one block | Sequential updates, each sees previous state |
| Empty range cleanup | Last position removed from range | Delete range entry entirely |
| Single position in range | Only LP in range for entire lifetime | x_k = 1, term = 1/lifetime |
