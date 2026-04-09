# AngstromAccumulatorConsumer -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/_adapters/AngstromAccumulatorConsumer.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Renamed from:** `AngstromAccumulatorOracleAdapter.sol`
**Depends on:** AngstromView (slot constants, extsload patterns), PoolConfigStore / ConfigEntry (pool config retrieval), StoreKey / StoreKeyLib (pair key derivation), IAngstromAuth (extsload interface), IUniV4 (Uniswap V4 slot0 access)

---

## Overview

AngstromAccumulatorConsumer is a **read-only Angstrom client**. It reads Angstrom's
on-chain storage via `extsload` to surface accumulator values, block metadata, and pool
configuration data. It does NOT write observations, manage oracle state, or mutate any
Angstrom storage -- that responsibility belongs to the observer layer.

This contract was previously named `AngstromAccumulatorOracleAdapter`. The rename reflects
its refined role: it is a **consumer** of Angstrom data, not an adapter that transforms it.
The transformation and observation-recording responsibilities live in
`AngstromPoolObserver` and its downstream storage modules.

### Responsibilities

This contract is responsible for exactly two things:

1. **Accumulator reads:** Reading Angstrom's per-pool reward growth accumulators
   (`globalGrowth`, `growthInside`) via `extsload` with slot arithmetic derived from
   Angstrom's storage layout.
2. **Metadata reads:** Reading Angstrom's block-level metadata (`lastBlockUpdated`,
   `configStore`) and pool configuration (`poolExists`, `getPoolConfig`) via `extsload`
   and SSTORE2 code reads.

This contract is NOT responsible for:

- Writing any state (it is entirely `view`/`pure`)
- Managing observation buffers or EMA state (that is the observer's job)
- Access control (all functions are public view)
- Validating Angstrom's internal consistency (it trusts Angstrom's storage)

---

## Immutable References

| Name       | Type            | Description                                        |
|------------|-----------------|----------------------------------------------------|
| `ANGSTROM` | `IAngstromAuth` | The Angstrom contract; target of all `extsload` calls |
| `UNI_V4`   | `IPoolManager`  | The Uniswap V4 PoolManager; used for `getSlot0` in `growthInside` |

Both are set in the constructor and cannot be changed after deployment.

---

## Angstrom Storage Layout Constants

These constants mirror Angstrom's internal storage layout and are used to compute
`extsload` target slots. They MUST remain in sync with Angstrom's layout.

| Constant                   | Value      | Description                                                   |
|----------------------------|------------|---------------------------------------------------------------|
| `POOL_REWARDS_SLOT`        | `7`        | Base mapping slot for per-pool reward accumulators             |
| `REWARD_GROWTH_SIZE`       | `16777216` | Offset within pool rewards for the globalGrowth field          |
| `POOLS_SLOT`               | `6`        | Base mapping slot for pool state (reserved, not yet used)      |
| `LAST_BLOCK_CONFIG_STORE_SLOT` | `3`    | Packed slot: lower 64 bits = lastBlockUpdated, upper bits = configStore address |
| `LAST_BLOCK_BIT_OFFSET`   | `0`        | Bit offset for lastBlockUpdated within slot 3                  |
| `STORE_BIT_OFFSET`         | `64`       | Bit offset for PoolConfigStore address within slot 3           |

The slot 3 layout is borrowed directly from `AngstromView.sol` (lines 16-18).

---

## Function Specifications

### 1. globalGrowth

```
function globalGrowth(PoolId poolId) external view returns (uint256 _globalGrowth)
```

**Purpose:** Returns the cumulative global reward growth for a given pool, read from
Angstrom's storage via `extsload`.

**Slot computation:**
1. Derive the mapping base slot: `keccak256(abi.encode(PoolId.unwrap(poolId), POOL_REWARDS_SLOT))`
2. Offset by `REWARD_GROWTH_SIZE` to reach the globalGrowth field.
3. Read via `ANGSTROM.extsload(slot)`.

**Existing implementation:** Lines 28-31 of `AngstromAccumulatorOracleAdapter.sol`.

#### BTT Tree

```
AngstromAccumulatorConsumer::globalGrowth
├── when poolId corresponds to a pool that has never received rewards
│   └── it should return 0.
└── when poolId corresponds to a pool that has received rewards
    └── it should return the cumulative globalGrowth value from Angstrom's storage.
```

No branching logic -- this is a direct slot read. The return value is whatever Angstrom
has stored. If the pool does not exist in Angstrom, the extsload returns the storage
default (0), which is a valid return.

---

### 2. growthInside

```
function growthInside(
    PoolId poolId,
    int24 tickLower,
    int24 tickUpper
) external view returns (uint256)
```

**Purpose:** Returns the cumulative reward growth accrued within a tick range
`[tickLower, tickUpper)` for a given pool, using the standard 3-branch Uniswap V4
"growth inside" formula.

**Slot computation for `outsideBelow` and `outsideAbove`:**
1. Derive the mapping base slot: `keccak256(abi.encode(PoolId.unwrap(poolId), POOL_REWARDS_SLOT))`
2. Offset by `uint256(uint24(tickLower))` for outsideBelow.
3. Offset by `uint256(uint24(tickUpper))` for outsideAbove.
4. Read both via `ANGSTROM.extsload(slot)`.

**3-branch tick logic** (depends on `currentTick` from `UNI_V4.getSlot0(poolId).tick()`):

| Condition                        | Formula                                           |
|----------------------------------|----------------------------------------------------|
| `currentTick < tickLower`        | `outsideBelow - outsideAbove`                      |
| `currentTick >= tickUpper`       | `outsideAbove - outsideBelow`                      |
| `tickLower <= currentTick < tickUpper` | `global - outsideBelow - outsideAbove`       |

All arithmetic is `unchecked` -- underflow wraps intentionally (matching Angstrom's
uint256 accumulator semantics).

**Existing implementation:** Lines 33-55 of `AngstromAccumulatorOracleAdapter.sol`.

#### BTT Tree

```
AngstromAccumulatorConsumer::growthInside
├── when currentTick < tickLower
│   └── it should return outsideBelow - outsideAbove (unchecked).
├── when currentTick >= tickUpper
│   └── it should return outsideAbove - outsideBelow (unchecked).
└── when tickLower <= currentTick < tickUpper
    └── it should return global - outsideBelow - outsideAbove (unchecked).
```

**Notes:**
- `currentTick` is read from Uniswap V4's `getSlot0`, not from Angstrom.
- The function does not validate that `tickLower < tickUpper`. This is the caller's
  responsibility (Uniswap V4 enforces this at pool creation).
- If the pool does not exist in Uniswap V4, `getSlot0` behavior depends on the
  PoolManager implementation (may return zero tick).

---

### 3. lastBlockUpdated (NEW)

```
function lastBlockUpdated() external view returns (uint64)
```

**Purpose:** Returns the block number of the most recent Angstrom bundle execution.
This is the primary freshness signal used by `AngstromPoolObserver` to determine
whether new data is available.

**Slot computation:**
1. Read slot 3 from Angstrom: `ANGSTROM.extsload(LAST_BLOCK_CONFIG_STORE_SLOT)`
2. Extract lower 64 bits: `uint64(value >> LAST_BLOCK_BIT_OFFSET)`

**Pattern source:** `AngstromView.lastBlockUpdated()` (lines 26-28).

#### BTT Tree

```
AngstromAccumulatorConsumer::lastBlockUpdated
└── it should return the lower 64 bits of Angstrom's slot 3.
```

No branching logic. This is a direct slot read with bit extraction. Returns 0 if no
bundle has ever been executed.

---

### 4. configStore (NEW)

```
function configStore() external view returns (PoolConfigStore)
```

**Purpose:** Returns the SSTORE2 address of Angstrom's current PoolConfigStore. This
address points to a code-deployed contract whose bytecode contains the list of all
configured pool entries.

**Slot computation:**
1. Read slot 3 from Angstrom: `ANGSTROM.extsload(LAST_BLOCK_CONFIG_STORE_SLOT)`
2. Extract upper bits as address: `PoolConfigStore.wrap(address(uint160(value >> STORE_BIT_OFFSET)))`

**Pattern source:** `AngstromView.configStore()` (lines 30-33).

#### BTT Tree

```
AngstromAccumulatorConsumer::configStore
└── it should return the PoolConfigStore address from Angstrom's slot 3.
```

No branching logic. Returns `PoolConfigStore.wrap(address(0))` (NULL_CONFIG_CACHE)
if no config store has been set.

---

### 5. poolExists (NEW)

```
function poolExists(address token0, address token1) external view returns (bool)
```

**Purpose:** Returns whether at least one Angstrom pool is configured for the given
token pair. This requires iterating the PoolConfigStore entries because multiple pools
can exist per pair (different tick spacings).

**Algorithm:**
1. Validate `token0 < token1` (tokens must be sorted). If not, return false.
2. Derive `StoreKey` from `(token0, token1)` via `StoreKeyLib.keyFromAssetsUnchecked`.
3. Read the current `configStore()` from Angstrom.
4. Compute `totalEntries()` on the config store.
5. Iterate indices `0..totalEntries()-1`, calling `getWithDefaultEmpty(key, index)`.
6. If any entry is non-empty (key matches), return `true`.
7. If no entry matches, return `false`.

**Design note:** `getWithDefaultEmpty` returns a zeroed ConfigEntry when the key at the
given index does not match our derived StoreKey. An entry is "non-empty" when
`!entry.isEmpty()`. This handles the case where different pairs occupy different indices.

**Gas consideration:** This function iterates all entries in the worst case. The
PoolConfigStore is expected to be small (tens of entries), so linear scan is acceptable.
For production deployments with many pairs, a mapping-based index could be added to the
observer layer, but that is out of scope for this consumer.

#### BTT Tree

```
AngstromAccumulatorConsumer::poolExists
├── when token0 >= token1
│   └── it should return false.
└── when token0 < token1
    ├── when configStore is the null address (no config store set)
    │   └── it should return false.
    ├── when no entry in the config store matches the derived StoreKey
    │   └── it should return false.
    └── when at least one entry in the config store matches the derived StoreKey
        └── it should return true.
```

---

### 6. getPoolConfig (NEW)

```
function getPoolConfig(
    address token0,
    address token1,
    uint256 index
) external view returns (int24 tickSpacing, uint24 bundleFee)
```

**Purpose:** Returns the tick spacing and bundle fee for a specific pool configuration
entry in Angstrom's PoolConfigStore. The `index` parameter selects which entry to read
(since multiple pools can exist per pair with different tick spacings).

**Algorithm:**
1. Derive `StoreKey` from `(token0, token1)` via `StoreKeyLib.keyFromAssetsUnchecked`.
2. Read the current `configStore()` from Angstrom.
3. Call `configStore.get(key, index)` which:
   a. Reads the entry at the given index via `extcodecopy`.
   b. Verifies the entry's key matches our derived StoreKey.
   c. Reverts with `NoEntry` if the keys do not match (entry is empty or belongs to a different pair).
   d. Returns `(tickSpacing, bundleFee)` if the keys match.

**Note on token ordering:** Unlike `poolExists`, this function does NOT validate
`token0 < token1`. The caller is responsible for providing correctly sorted tokens.
If unsorted tokens are provided, the derived StoreKey will not match any entry, and
the function will revert with `NoEntry`. This is the desired behavior -- silent
failure via revert rather than returning incorrect data.

#### BTT Tree

```
AngstromAccumulatorConsumer::getPoolConfig
├── when configStore is the null address
│   └── it should revert (extcodecopy on address(0) reads empty bytecode, NoEntry).
├── when index is out of bounds (>= totalEntries)
│   └── it should revert (extcodecopy reads zeros, NoEntry).
├── when index is in bounds but StoreKey does not match the entry at that index
│   └── it should revert (NoEntry from PoolConfigStoreLib.get).
└── when index is in bounds and StoreKey matches the entry
    ├── it should return the tickSpacing from the entry.
    └── it should return the bundleFee from the entry.
```

---

## Algebraic Properties

### P1: lastBlockUpdated monotonicity

```
forall block_a, block_b where block_b > block_a:
    lastBlockUpdated() at block_b >= lastBlockUpdated() at block_a
```

**Rationale:** Angstrom's bundle execution sets `lastBlockUpdated` to `block.number`,
which is monotonically increasing. The value can only stay the same (no bundle in
the interval) or increase.

### P2: configStore address stability within a block

```
forall tx_a, tx_b within the same block:
    configStore() at tx_a == configStore() at tx_b
```

**Rationale:** PoolConfigStore updates are admin-gated operations that rewrite slot 3.
Within a single block, the configStore address is stable because only one Angstrom
bundle executes per block (enforced by lastBlockUpdated check in Angstrom's execute).

**Caveat:** An admin transaction in the same block could theoretically change the config
store. This property holds under normal operation but is not cryptographically guaranteed.

### P3: globalGrowth monotonicity

```
forall block_a, block_b where block_b > block_a:
    globalGrowth(poolId) at block_b >= globalGrowth(poolId) at block_a
```

**Rationale:** Angstrom's reward accrual only adds to the cumulative globalGrowth
accumulator. It never subtracts. This is a core invariant of the reward system.

### P4: poolExists / getPoolConfig consistency

```
forall (token0, token1) where token0 < token1:
    poolExists(token0, token1) == true
    =>
    exists index such that getPoolConfig(token0, token1, index) does not revert
```

**Rationale:** If `poolExists` finds a matching entry, then at least one valid index
exists. `getPoolConfig` at that index must succeed.

**Converse does NOT hold unconditionally:** `getPoolConfig` succeeding at a specific
index does not guarantee `poolExists` returns true, because `poolExists` must also
successfully read the configStore. However, under normal operation (configStore is set),
the converse does hold.

### P5: growthInside decomposition

```
forall poolId, tickLower, tickUpper where tickLower <= currentTick < tickUpper:
    growthInside(poolId, tickLower, tickUpper)
        == globalGrowth(poolId)
           - outsideBelow(poolId, tickLower)
           - outsideAbove(poolId, tickUpper)
```

This is a direct consequence of the 3-branch formula. The other two branches
(`currentTick < tickLower` and `currentTick >= tickUpper`) decompose analogously.
All arithmetic is unchecked uint256.

---

## Error Taxonomy

| Error     | Source                            | Trigger                                           |
|-----------|-----------------------------------|----------------------------------------------------|
| `NoEntry` | `PoolConfigStoreLib.get`          | `getPoolConfig` called with index that has no matching entry |

Note: `poolExists` does NOT revert -- it returns `false` for all failure cases.
`globalGrowth`, `growthInside`, `lastBlockUpdated`, and `configStore` do not revert
under normal conditions (they read storage defaults when data is absent).

---

## Constructor Specification

```
constructor(IAngstromAuth _angstrom, IPoolManager _poolManager)
```

| Parameter      | Type            | Validation | Description                        |
|----------------|-----------------|------------|------------------------------------|
| `_angstrom`    | `IAngstromAuth` | None       | Angstrom contract address          |
| `_poolManager` | `IPoolManager`  | None       | Uniswap V4 PoolManager address     |

Both parameters are stored as immutables. No validation is performed -- deploying with
zero addresses produces a contract that reverts on all `extsload` calls, which is the
correct fail-safe behavior.

---

## Test Harness Requirements

Tests for this contract require:

1. **A deployed Angstrom contract** (or a mock that supports `extsload`) with known
   storage layout at slots 3, 6, and 7.
2. **A deployed Uniswap V4 PoolManager** (or a mock that supports `getSlot0`).
3. **A deployed PoolConfigStore** (SSTORE2 contract) with known entries for test pairs.
4. **Fork testing** is recommended for `globalGrowth` and `growthInside` to validate
   against real Angstrom state.

### Mock Strategy

For unit tests, a minimal mock approach:

- `MockAngstrom`: Implements `extsload(uint256 slot) returns (bytes32)` with a
  configurable slot-to-value mapping. Allows tests to set specific values at specific
  slots without deploying a full Angstrom contract.
- `MockPoolManager`: Implements `getSlot0(PoolId) returns (Slot0)` with a configurable
  tick value per pool.

For integration tests, use Angstrom's test deployment or mainnet fork.

---

## Relationship to AngstromPoolObserver

AngstromAccumulatorConsumer is consumed by AngstromPoolObserver as an immutable dependency.
The observer calls:

- `lastBlockUpdated()` to determine if a new Angstrom bundle has been processed
- `globalGrowth(poolId)` to read the current cumulative growth for observation recording
- `getPoolConfig(token0, token1, index)` during pool registration to verify pool existence
  and retrieve tick spacing

The consumer never calls the observer. Data flows in one direction:

```
Angstrom Storage → AngstromAccumulatorConsumer → AngstromPoolObserver
                   (reads via extsload)          (reads via function calls)
```
