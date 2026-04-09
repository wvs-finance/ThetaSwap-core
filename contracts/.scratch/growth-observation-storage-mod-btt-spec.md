# GrowthObservationStorageMod -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/modules/GrowthObservationStorageMod.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Depends on:** BlockNumberAwareGrowthObserverLib BTT Spec (`growth-observer-lib-btt-spec.md`), GrowthObservation V2 BTT Spec (`growth-observation-v2-btt-spec.md`)

---

## Overview

GrowthObservationStorageMod is a **diamond storage module** consisting of free functions
that wrap BlockNumberAwareGrowthObserverLib with per-pool storage routing. It is the
**Layer 1.5 storage bridge** between the stateless observer library (Layer 1) and the
adapter/transformation contracts (Layer 2) that consume it.

Each free function takes a `PoolId` as its first parameter, computes the diamond storage
pointer internally via keccak256 slot hashing, resolves the correct
`CircularBuffer.Bytes32CircularBuffer` for that pool, and delegates to the corresponding
BlockNumberAwareGrowthObserverLib free function.

### Responsibilities

This module is responsible for exactly three things:

1. **Storage location:** Computing and accessing the diamond storage slot for the
   per-pool observation mapping.
2. **Pool lifecycle:** Managing pool initialization (buffer setup) with a one-time guard.
3. **Pool-keyed dispatch:** Routing each call to the correct per-pool ring buffer before
   delegating to the stateless library functions.

This module is NOT responsible for:

- Access control (the adapter handles permissions)
- Modifying Angstrom state (Angstrom contracts are read-only)
- Transformation logic (EMA, TWAP, etc. -- that is Layer 2)
- Computing relativeTimeDelta or cumulativeGrowth (caller's responsibility)

### Relationship to BlockNumberAwareGrowthObserverLib

Every function in this module (except `initializePool`) is a thin wrapper that:

1. Loads the storage struct from the diamond slot
2. Indexes the mapping by `PoolId` to obtain the per-pool `CircularBuffer`
3. Calls the identically-named free function from BlockNumberAwareGrowthObserverLib

The behavioral contracts of the underlying library carry through unchanged. This spec
focuses on the **storage routing**, **pool isolation**, and **initialization guard**
behaviors that this module adds on top.

---

## Diamond Storage Design

### Storage Slot

The module uses a single keccak256-derived storage slot to anchor its state:

```
bytes32 constant GROWTH_OBSERVATION_STORAGE_SLOT =
    keccak256("thetaswap.storage.GrowthObservationStorage");
```

This string is unique across all modules in the diamond. No other module uses this
hash input, guaranteeing disjoint storage slots.

### Storage Struct Layout

```
struct GrowthObservationStorage {
    mapping(PoolId => CircularBuffer.Bytes32CircularBuffer) buffers;
    mapping(PoolId => bool) initialized;
}
```

| Field | Type | Purpose |
|---|---|---|
| `buffers` | `mapping(PoolId => CircularBuffer.Bytes32CircularBuffer)` | Per-pool observation ring buffers |
| `initialized` | `mapping(PoolId => bool)` | One-time initialization guard per pool |

The `initialized` mapping is necessary because `CircularBuffer.setup()` can be called
multiple times (it calls `clear()` then resizes). The guard prevents accidental
re-initialization that would destroy existing observations.

### Storage Pointer Computation

Each free function computes the storage pointer internally:

```
function _storage() private pure returns (GrowthObservationStorage storage s) {
    bytes32 slot = GROWTH_OBSERVATION_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}
```

Alternatively, the pattern may use inline assembly directly in each function. The key
requirement is that the slot is computed from the constant -- no external input influences
the base slot. The `PoolId` key only affects which mapping entry is accessed, not the
base slot itself.

### Slot Disjointness Guarantee

The diamond storage pattern guarantees disjointness because:

1. Each module uses a different human-readable string as the keccak256 preimage.
2. keccak256 is collision-resistant: distinct preimages produce distinct slots.
3. The `EMAGrowthTransformationStorageMod` (specified separately) uses a different
   string (e.g., `"thetaswap.storage.EMAGrowthTransformationStorage"`), so its
   `OraclePack` state never overlaps with observation buffers.
4. Solidity's mapping derivation (`keccak256(key . slot)`) further isolates per-pool
   entries within each module's mapping.

---

## Errors

```
error PoolAlreadyInitialized();
```

Raised by `initializePool` when the pool's `initialized` flag is already `true`.
This is the only error defined by this module. All other errors propagate from
dependencies:

| Error | Source | Trigger |
|---|---|---|
| `PoolAlreadyInitialized` | GrowthObservationStorageMod | `initializePool` called on an already-initialized pool |
| `CircularBuffer.InvalidBufferSize` | OpenZeppelin CircularBuffer | `size == 0` passed to `initializePool` |
| `EmptyBuffer` | BlockNumberAwareGrowthObserverLib | Buffer count == 0 for `observeAt` / `latestObservation` / `oldestObservation` |
| `ObservationExpired(uint32, uint32)` | BlockNumberAwareGrowthObserverLib | `targetBlock` older than oldest observation in `observeAt` |
| `Panic(0x32)` (array out of bounds) | OpenZeppelin CircularBuffer | `push()` on an uninitialized buffer (no `setup()` call) |
| `SafeCastLib.Overflow` | Solady SafeCastLib | Input exceeds uint32/uint16/uint208 range (via `newGrowthObservation`) |

---

## Section 1: BTT Behavior Trees

### 1.1 initializePool

**Signature:**

```
function initializePool(PoolId poolId, uint256 size)
```

**Mutability:** storage-mutating (calls `CircularBuffer.setup`, sets `initialized` flag)

**Preconditions:**
- `poolId` is a valid Uniswap V4 `PoolId` (bytes32). No validation is performed on the
  value itself -- any bytes32 is accepted.
- `size` determines the ring buffer capacity. Must be > 0.

```
GrowthObservationStorageMod::initializePool
|
+-- when the pool buffer is already initialized
|   +-- it should revert with PoolAlreadyInitialized.
|   +-- it should NOT modify the existing buffer.
|   +-- it should NOT reset the initialized flag.
|
+-- when the pool buffer is not yet initialized
    |
    +-- when size is zero
    |   +-- it should revert with CircularBuffer.InvalidBufferSize.
    |   +-- it should NOT set the initialized flag.
    |
    +-- when size is greater than zero
        +-- it should create a buffer with the given capacity for that poolId.
        +-- it should mark the pool as initialized (initialized[poolId] = true).
        +-- it should not affect buffers for other poolIds.
        +-- it should not affect initialized flags for other poolIds.
        +-- the buffer should have observationCount == 0 after initialization.
```

**Design notes:**

- The `initialized` guard exists because `CircularBuffer.setup()` is re-entrant by
  design (it calls `clear()` then resizes). Without the guard, a second `initializePool`
  call would destroy all existing observations by resetting `_count` to 0. This is
  catastrophic for an oracle that depends on historical data.

- The check-then-set pattern (check `initialized[poolId]`, revert if true, set to true)
  is safe against reentrancy because this module has no callbacks or external calls.
  The only external interaction is `CircularBuffer.setup()`, which is a pure storage
  operation with no callbacks.

- The `PoolAlreadyInitialized` check MUST come before the `CircularBuffer.setup()` call.
  If the order were reversed, a re-initialization with `size == 0` would revert with
  `InvalidBufferSize` instead of `PoolAlreadyInitialized`, leaking implementation details
  and making the error non-deterministic based on argument values.

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| First initialization with size = 1 | Succeeds, buffer capacity = 1, initialized = true |
| First initialization with size = 256 | Succeeds, buffer capacity = 256, initialized = true |
| First initialization with size = 0 | Revert CircularBuffer.InvalidBufferSize |
| Second initialization (same poolId, any size) | Revert PoolAlreadyInitialized |
| Second initialization (same poolId, size = 0) | Revert PoolAlreadyInitialized (NOT InvalidBufferSize) |
| Initialize pool A, then pool B | Both succeed independently |
| Initialize pool A, check pool B is not initialized | pool B's initialized flag is false |
| First initialization with size = type(uint256).max | Behavior depends on OZ (likely OOG); not this module's concern |

---

### 1.2 recordObservation

**Signature:**

```
function recordObservation(
    PoolId poolId,
    uint256 blockNumber,
    uint256 relativeTimeDelta,
    uint256 cumulativeGrowth
)
```

**Mutability:** storage-mutating (pushes to ring buffer via `record`)

**Preconditions:**
- The pool SHOULD be initialized. Calling on an uninitialized pool is undefined behavior
  (panics inside `CircularBuffer.push` due to zero-length `_data` array).
- Parameter validation (range checks) is handled by `newGrowthObservation` inside the
  library's `record` function.

```
GrowthObservationStorageMod::recordObservation
|
+-- given the pool buffer is not initialized
|   +-- it should panic with array out-of-bounds (Panic 0x32).
|   +-- this is caller's responsibility -- the module does NOT check initialization.
|
+-- given the pool buffer is initialized
    |
    +-- it should resolve the correct buffer for poolId from diamond storage.
    +-- it should delegate to BlockNumberAwareGrowthObserverLib.record for that buffer.
    +-- it should not read from or write to buffers for other poolIds.
    |
    +-- (all behavioral branches from BlockNumberAwareGrowthObserverLib::record apply)
        |
        +-- given the buffer is empty (count == 0)
        |   +-- when all inputs are within range
        |       +-- it should push a new observation.
        |       +-- observationCount(poolId) should become 1.
        |
        +-- given the buffer has at least one observation
            |
            +-- when blockNumber <= latest observation blockNumber
            |   +-- it should skip without pushing (idempotent / stale).
            |   +-- observationCount(poolId) should not change.
            |
            +-- when blockNumber is strictly greater than the latest observation blockNumber
                +-- it should push a new observation.
                +-- the new observation should be retrievable via latestObservation(poolId).
```

**Design notes:**

- This function does NOT check the `initialized` flag. The rationale is that the
  `CircularBuffer.push` on an uninitialized buffer panics immediately (array OOB on
  zero-length `_data`), which is a sufficient fail-safe. Adding a redundant check would
  cost gas on every record call for a condition that should never occur in correct usage.

- Access control is NOT this module's concern. The adapter that calls `recordObservation`
  is responsible for restricting callers (e.g., to a trusted keeper).

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Record into uninitialized pool | Panic 0x32 |
| Record into initialized empty buffer | Push succeeds, count = 1 |
| Record same blockNumber twice (same pool) | Second call skipped, count unchanged |
| Record into pool A, verify pool B unchanged | pool B observationCount unchanged |
| Record with all-zero parameters into empty buffer | Push succeeds (block 0 is valid) |
| Record after buffer wraps | Oldest evicted, count stays at capacity |

---

### 1.3 observeAt

**Signature:**

```
function observeAt(
    PoolId poolId,
    uint32 targetBlock
) view returns (GrowthObservation)
```

**Mutability:** view

```
GrowthObservationStorageMod::observeAt
|
+-- given the pool buffer is not initialized or empty (count == 0)
|   +-- it should revert with EmptyBuffer.
|
+-- given the pool buffer has observations
    |
    +-- it should resolve the correct buffer for poolId from diamond storage.
    +-- it should delegate to BlockNumberAwareGrowthObserverLib.observeAt for that buffer.
    +-- it should not read from buffers for other poolIds.
    |
    +-- (all behavioral branches from BlockNumberAwareGrowthObserverLib::observeAt apply)
        |
        +-- when targetBlock >= latest observation blockNumber
        |   +-- it should return the latest observation.
        |
        +-- when targetBlock < oldest observation blockNumber
        |   +-- it should revert with ObservationExpired(targetBlock, oldestBlockNumber).
        |
        +-- when targetBlock is between oldest and latest blockNumbers
            |
            +-- when an observation exists at exactly targetBlock
            |   +-- it should return that exact observation.
            |
            +-- when no observation exists at exactly targetBlock
                +-- it should return the most recent observation BEFORE targetBlock.
```

**Design notes:**

- An uninitialized pool has `_count == 0` and `_data.length == 0`, so
  `CircularBuffer.count()` returns `min(0, 0) == 0`, which triggers the `EmptyBuffer`
  revert in the library. This means uninitialized and empty-but-initialized pools
  produce the same error -- which is correct behavior, since both represent "no data."

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Uninitialized pool | Revert EmptyBuffer |
| Initialized but empty pool | Revert EmptyBuffer |
| Pool A has data, query pool B (empty) | Revert EmptyBuffer (pool isolation) |
| Pool A has data at block 100, observeAt(A, 100) | Return observation at block 100 |
| Pool A has data at block 100, observeAt(A, 200) | Return observation at block 100 (latest) |
| Pool A has data at block 100, observeAt(A, 50) | Revert ObservationExpired(50, 100) |
| Two pools with different data, same targetBlock | Each returns its own observation |

---

### 1.4 latestObservation

**Signature:**

```
function latestObservation(PoolId poolId) view returns (GrowthObservation)
```

**Mutability:** view

```
GrowthObservationStorageMod::latestObservation
|
+-- given the pool buffer is empty (count == 0)
|   +-- it should revert with EmptyBuffer.
|
+-- given the pool buffer has observations
    +-- it should return the latest observation for that poolId only.
    +-- it should not read from other poolId buffers.
```

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Uninitialized pool | Revert EmptyBuffer |
| Initialized, empty pool | Revert EmptyBuffer |
| Pool with 1 observation | Return that observation |
| Pool with N observations | Return the most recently recorded observation |
| Pool after buffer wrapping | Return the most recently recorded (not the evicted one) |
| Two pools, each with different latest | Each returns its own latest |

---

### 1.5 oldestObservation

**Signature:**

```
function oldestObservation(PoolId poolId) view returns (GrowthObservation)
```

**Mutability:** view

```
GrowthObservationStorageMod::oldestObservation
|
+-- given the pool buffer is empty (count == 0)
|   +-- it should revert with EmptyBuffer.
|
+-- given the pool buffer has observations
    +-- it should return the oldest observation for that poolId only.
    +-- it should not read from other poolId buffers.
```

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Uninitialized pool | Revert EmptyBuffer |
| Initialized, empty pool | Revert EmptyBuffer |
| Pool with 1 observation | Return that observation (same as latest) |
| Pool partially filled (3 of 256 slots) | Return the first-ever recorded observation |
| Pool after wrapping | Return the oldest surviving observation |
| Two pools, each with different oldest | Each returns its own oldest |

---

### 1.6 observationCount

**Signature:**

```
function observationCount(PoolId poolId) view returns (uint256)
```

**Mutability:** view

```
GrowthObservationStorageMod::observationCount
|
+-- given the pool is uninitialized
|   +-- it should return 0.
|
+-- given the pool is initialized but empty
|   +-- it should return 0.
|
+-- given the pool has observations
|   +-- it should return the number of observations for that specific poolId.
|
+-- given the pool buffer has wrapped
    +-- it should return the buffer capacity (saturated).
```

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Uninitialized pool | 0 |
| Initialized, no pushes | 0 |
| After 1 push | 1 |
| After N pushes (N < capacity) | N |
| After capacity pushes | capacity |
| After capacity + K pushes | capacity |
| Pool A has 5 observations, pool B has 0 | observationCount(A) == 5, observationCount(B) == 0 |

---

## Section 2: Algebraic Properties (Invariants for Fuzz Testing)

### Property 1: Pool Isolation

**Statement:** For any two distinct poolIds A and B, operations on A never affect the
observable state of B. Specifically:

- `recordObservation(A, ...)` does not change `observationCount(B)`.
- `initializePool(A, ...)` does not affect `latestObservation(B)` (if B has data) or
  `observationCount(B)`.
- `recordObservation(A, ...)` does not change the return value of `observeAt(B, block)`
  for any block value.

**Formal:**

```
Pre:  Pool B is initialized with some observations.
      countB = observationCount(B)
      latestB = latestObservation(B)
      oldestB = oldestObservation(B)
      A != B

Action: recordObservation(A, bn, rtd, cg)  OR  initializePool(A, size)

Post: observationCount(B) == countB
      latestObservation(B) == latestB
      oldestObservation(B) == oldestB
```

**Test approach:** Initialize two pools. Push observations to pool A (fuzzed sequence).
After each push, verify pool B's count, latest, and oldest are unchanged. Then repeat
with the roles reversed.

---

### Property 2: Storage Slot Determinism

**Statement:** The same poolId always resolves to the same underlying CircularBuffer.
Multiple calls with the same poolId access identical data. There is no path-dependent
behavior in storage resolution.

**Formal:**

```
For any poolId, any sequence of operations O1, O2, ..., On on poolId:
  The storage accessed by Oi is at the same Solidity storage slot as O1.

Equivalently:
  latestObservation(poolId) after recordObservation(poolId, bn, rtd, cg)
  returns the observation just recorded (assuming bn > previous latest).
```

**Test approach:** Record an observation to a pool, then read it back via
`latestObservation`. Verify the returned observation matches the input parameters.
This confirms the write and read paths resolve to the same underlying storage.

---

### Property 3: Delegation Transparency

**Statement:** For any initialized poolId with observations, the result of calling
any view function through this module is identical to calling the corresponding
BlockNumberAwareGrowthObserverLib function directly on the underlying buffer for that pool.

**Formal:**

```
Let buf = _storage().buffers[poolId]

For all targetBlock:
  observeAt(poolId, targetBlock)       == BlockNumberAwareGrowthObserverLib.observeAt(buf, targetBlock)
  latestObservation(poolId)            == BlockNumberAwareGrowthObserverLib.latestObservation(buf)
  oldestObservation(poolId)            == BlockNumberAwareGrowthObserverLib.oldestObservation(buf)
  observationCount(poolId)             == BlockNumberAwareGrowthObserverLib.observationCount(buf)
```

**Test approach:** In a test harness that exposes the internal storage pointer, call
both the module function and the library function directly, and assert equality. This
is a "transparent wrapper" property.

---

### Property 4: Initialization Guard (At-Most-Once)

**Statement:** `initializePool(poolId, size)` succeeds at most once per poolId. The
second call reverts with `PoolAlreadyInitialized` regardless of the `size` parameter.

**Formal:**

```
Pre:  initializePool(poolId, size1) succeeded
Action: initializePool(poolId, size2)  // for any size2, including size1
Post: reverts with PoolAlreadyInitialized
```

**Corollary:** The capacity of a pool's buffer is immutable after initialization.
There is no mechanism to resize or re-initialize.

**Test approach:** Fuzz `size1` and `size2` (both > 0). First call succeeds, second
call always reverts. Also test with `size2 == 0` to confirm the guard fires before
the size check.

---

### Property 5: Initialization Prerequisite for record

**Statement:** `recordObservation` on a poolId that has never been initialized results
in a panic (Solidity Panic 0x32 -- array out of bounds).

**Formal:**

```
Pre:  initialized[poolId] == false (initializePool never called for this poolId)
Action: recordObservation(poolId, bn, rtd, cg)
Post: Panic(0x32)
```

**Test approach:** Attempt to record into a fresh poolId without initialization.
Assert the transaction reverts with the expected panic code.

---

### Property 6: Initialization Prerequisite for views

**Statement:** For an uninitialized poolId, `observeAt`, `latestObservation`, and
`oldestObservation` all revert with `EmptyBuffer`. `observationCount` returns 0.

**Formal:**

```
Pre:  initialized[poolId] == false
Post: observeAt(poolId, anyBlock) reverts with EmptyBuffer
      latestObservation(poolId) reverts with EmptyBuffer
      oldestObservation(poolId) reverts with EmptyBuffer
      observationCount(poolId) == 0
```

**Rationale:** An uninitialized buffer has `_count == 0` and `_data.length == 0`.
`CircularBuffer.count()` returns `min(0, 0) == 0`, which is the trigger for the
`EmptyBuffer` revert in the library. `observationCount` returns 0 directly.

**Test approach:** Call all view functions on a never-initialized poolId and verify
the expected revert/return.

---

### Property 7: Observation Persistence Through Cross-Pool Operations

**Statement:** Recording observations to pool A, then recording observations to pool B,
does not corrupt the observations previously stored for pool A. The full observation
history for A remains intact and retrievable.

**Formal:**

```
Pre:  initializePool(A, capA); initializePool(B, capB)
      record N observations to A: obs_A_1, ..., obs_A_N  (N <= capA)
      Snapshot: for all i in [0, N-1]: expected_A_i = last(bufferA, i)

Action: record M observations to B: obs_B_1, ..., obs_B_M

Post: for all i in [0, N-1]:
        observeAt(A, obs_A_i.blockNumber()) == expected_A_i
      observationCount(A) == N
```

**Test approach:** Initialize two pools. Fill pool A with observations, snapshot
them. Fill pool B with a large number of observations (potentially wrapping).
Verify all of pool A's observations are unchanged.

---

## Section 3: Test Matrix -- Cross-Cutting Scenarios

These scenarios test combinations of states across multiple function calls,
focusing on behaviors unique to the storage module (not already covered by the
underlying library spec).

### 3.1 Multi-Pool Interleaved Operations

| Step | Action | Pool A State | Pool B State |
|---|---|---|---|
| 1 | `initializePool(A, 4)` | initialized, empty, cap=4 | uninitialized |
| 2 | `initializePool(B, 8)` | initialized, empty, cap=4 | initialized, empty, cap=8 |
| 3 | `recordObservation(A, 100, 0, 1000)` | count=1, latest=block100 | count=0 |
| 4 | `recordObservation(B, 100, 0, 2000)` | count=1, latest=block100 | count=1, latest=block100 |
| 5 | `recordObservation(A, 200, 12, 2000)` | count=2, latest=block200 | count=1, latest=block100 |
| 6 | `observeAt(A, 150)` | returns obs at block 100 | -- |
| 7 | `observeAt(B, 150)` | -- | returns obs at block 100 |
| 8 | `latestObservation(A)` | returns obs at block 200 | -- |
| 9 | `latestObservation(B)` | -- | returns obs at block 100 |

**Assertions per step:**
- After step 3: `observationCount(B) == 0` (isolation).
- After step 4: Pool A's observation is unchanged; Pool B has its own distinct observation
  at block 100 with `cumulativeGrowth == 2000` (not 1000).
- After step 5: `observationCount(B) == 1` (isolation).
- Steps 6-7: Same targetBlock, different pools, different results (different cumulativeGrowth).

### 3.2 Initialization Ordering

| Scenario | Action | Expected |
|---|---|---|
| Record before initialize | `recordObservation(X, 100, 0, 1000)` on fresh pool X | Panic 0x32 |
| Initialize then record | `initializePool(X, 4)` then `recordObservation(X, 100, 0, 1000)` | Success, count = 1 |
| Initialize pool A, record to pool B | `initializePool(A, 4)` then `recordObservation(B, 100, 0, 1000)` | Panic 0x32 (B not initialized) |
| Double initialize same pool | `initializePool(X, 4)` then `initializePool(X, 8)` | Second call reverts PoolAlreadyInitialized |

### 3.3 Buffer Capacity Independence

| Step | Action | Assertion |
|---|---|---|
| 1 | `initializePool(A, 2)`, `initializePool(B, 256)` | Both succeed |
| 2 | Record 3 observations to A (blocks 10, 20, 30) | count(A) = 2 (wrapped), oldest = block 20 |
| 3 | Record 3 observations to B (blocks 10, 20, 30) | count(B) = 3 (not wrapped), oldest = block 10 |
| 4 | `observeAt(A, 10)` | Revert ObservationExpired(10, 20) -- evicted |
| 5 | `observeAt(B, 10)` | Returns observation at block 10 -- still present |

This demonstrates that pool A's smaller capacity causes eviction while pool B retains
the same data, confirming that capacities are independent per-pool.

---

## Section 4: Relationship to Other Components

### Consumer: AngstromAccumulatorOracleAdapter

The adapter (`contracts/src/_adapters/AngstromAccumulatorOracleAdapter.sol`) is the
primary consumer of this module. Its workflow:

1. Read `globalGrowth` from Angstrom via `extsload` (read-only -- does not modify Angstrom).
2. Compute `relativeTimeDelta` from the previous observation's timestamp.
3. Call `recordObservation(poolId, block.number, relativeTimeDelta, globalGrowth)` on
   this module.

The adapter is responsible for:
- Access control (restricting who can call `recordObservation`)
- Calling `initializePool` during pool setup
- Computing the `relativeTimeDelta` parameter

This module does NOT validate that the adapter is the caller. That is the adapter's
concern (enforced at the adapter/diamond level).

### Consumer: EMAGrowthTransformationLib

The transformation library (`contracts/src/libraries/transformations/EMAGrowthTransformationLib.sol`)
reads from this module indirectly via the BlockNumberAwareGrowthObserverLib primitives:

```
Pipeline:
  EMAGrowthTransformationLib.updateGrowthEMA(buffer, ...)
    -> observationCount(buffer)           // Layer 1
    -> oldestObservation(buffer)          // Layer 1
    -> latestObservation(buffer)          // Layer 1
    -> growthToTick(...)                  // GrowthToTickLib
    -> OraclePack.insertObservation(...)  // Panoptic
```

In the diamond architecture, the adapter resolves the per-pool buffer from this module's
storage and passes it to `updateGrowthEMA`. The transformation library never accesses
diamond storage directly -- it receives the buffer as a storage parameter.

### Sibling: EMAGrowthTransformationStorageMod (to be specified separately)

The EMA transformation module owns independent diamond storage for `OraclePack` state
(4 EMAs + 8-slot median queue). Its storage slot uses a different keccak256 preimage,
guaranteeing disjointness from observation buffer storage. The two modules are composed
by the adapter but never interact directly.

---

## Section 5: Implementation Constraints

### C1: Free Function Pattern

All functions MUST be free functions (not inside a `library` or `abstract contract` block).
This is consistent with the existing codebase pattern for BlockNumberAwareGrowthObserverLib
and GrowthObservation. Free functions that access diamond storage internally are the
idiomatic pattern for this codebase's storage modules.

### C2: No Storage Parameter

Unlike BlockNumberAwareGrowthObserverLib (which takes `CircularBuffer storage` as a
parameter), the functions in this module take `PoolId` and compute the storage pointer
internally. The caller never sees or handles the raw CircularBuffer. This encapsulates
the storage layout.

### C3: PoolId as First Parameter

All functions take `PoolId` as their first parameter for consistency and to enable
potential `using ... for PoolId` syntax in consuming contracts.

### C4: No Access Control

This module MUST NOT implement access control (e.g., `onlyKeeper`, `onlyAdapter`).
Access control is the adapter's responsibility. This module is a pure storage primitive.

### C5: No Event Emission

Consistent with Angstrom's design decision ("No Events: Contracts avoid events to save
gas"), this module MUST NOT emit events. State changes are observable through view
function return values.

### C6: Error Ordering in initializePool

The `PoolAlreadyInitialized` check MUST precede the `CircularBuffer.setup()` call.
This ensures the error is deterministic: a re-initialization attempt always reverts
with `PoolAlreadyInitialized`, never with `InvalidBufferSize` (even if size == 0).

---

## Section 6: Gas Considerations

### Storage Access Pattern

Each function call incurs:
1. One SLOAD equivalent for the diamond storage pointer computation (the keccak256 is a
   compile-time constant, so the slot is known at compile time -- no runtime hashing).
2. One or more SLOADs for the mapping lookup (`keccak256(poolId . buffers_slot)`).
3. The SLOADs from the underlying CircularBuffer operations.

The diamond storage pointer computation does NOT add runtime gas beyond what a normal
storage variable access costs, because the slot constant is embedded in the bytecode.

### initializePool Gas

`initializePool` is a one-time operation per pool. Its gas cost is dominated by
`CircularBuffer.setup()`, which allocates `size` storage slots (one SSTORE per slot
for the array resize). For a 256-slot buffer, this is approximately 256 * 20,000 =
5,120,000 gas (cold SSTORE). This is acceptable as a one-time setup cost.

### recordObservation Gas

The hot path (recording a new observation) costs approximately:
- 1 cold/warm SLOAD for the mapping lookup
- The cost of `CircularBuffer.push()` (1 SLOAD for `_count`, 1 SSTORE for the new
  value, 1 SSTORE for incrementing `_count`)
- If the buffer is non-empty: 1 additional SLOAD for `CircularBuffer.last(buffer, 0)`
  to check the latest block number

The skip path (same-block or stale) is cheaper: only the mapping lookup and the latest
observation SLOAD, with no SSTOREs.
