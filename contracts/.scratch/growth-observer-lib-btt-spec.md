# BlockNumberAwareGrowthObserverLib -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/libraries/BlockNumberAwareGrowthObserverLib.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Depends on:** GrowthObservation V2 BTT Spec (`growth-observation-v2-btt-spec.md`)

---

## Overview

BlockNumberAwareGrowthObserverLib provides raw observation primitives over an OpenZeppelin
`CircularBuffer.Bytes32CircularBuffer` of `GrowthObservation` values. It is
**transformation-agnostic** -- it stores and retrieves observations, period. Transformations
(windowed delta, EMA, TWAP, median, etc.) are the sole responsibility of Layer 2 caller
contracts that consume these primitives.

All public surface area consists of **free functions** (not inside a `library` block), each
taking `CircularBuffer.Bytes32CircularBuffer storage` as the first parameter.

### Underlying Buffer Semantics (OZ CircularBuffer)

The library delegates all storage management to OpenZeppelin's `CircularBuffer` (v5.1.0):

| OZ API | Semantics |
|---|---|
| `setup(buffer, N)` | Allocates N-slot ring buffer. Caller's responsibility before first use. |
| `push(buffer, value)` | O(1) append; when full, overwrites oldest slot. |
| `count(buffer)` | `min(_count, _data.length)` -- saturates at capacity. |
| `length(buffer)` | Fixed capacity (`_data.length`), set at `setup()` time. |
| `last(buffer, i)` | Returns the i-th most recent element (0 = newest). Panics if `i >= count`. |

Key implication: `count` returns the number of *valid* observations, which equals
`min(total_pushes, capacity)`. After the buffer wraps, `count` equals `capacity` permanently.

### GrowthObservation V2 Type Layout

```
Bit 255                                    Bit 48  Bit 47  Bit 32  Bit 31       Bit 0
 |                                           |       |       |       |             |
 [  cumulativeGrowth (208 bits)              ][ rtd  ][ blockNumber (32 bits)      ]
 |<------------ 208 bits ------------------>||<16b>| |<---------- 32 bits -------->|
```

- `blockNumber`: uint32 (bits 0-31)
- `relativeTimeDelta`: uint16 (bits 32-47) -- seconds since previous observation
- `cumulativeGrowth`: uint208 (bits 48-255) -- truncated globalGrowth accumulator

---

## Changelog from Current Implementation (V1 to V2)

| Location | Current (V1) | Required (V2) |
|---|---|---|
| `record()` signature | `(buffer, _blockNumber, _cumulativeGrowth)` | `(buffer, _blockNumber, _relativeTimeDelta, _cumulativeGrowth)` |
| `record()` block comparison | `uint48(_blockNumber)` | `uint32(_blockNumber)` |
| `record()` constructor call | `newGrowthObservation(_blockNumber, _cumulativeGrowth)` | `newGrowthObservation(_blockNumber, _relativeTimeDelta, _cumulativeGrowth)` |
| `observeAt()` parameter | `uint48 targetBlock` | `uint32 targetBlock` |
| `ObservationExpired` error | `(uint48, uint48)` | `(uint32, uint32)` |
| `observeGrowthDelta()` | Present | **REMOVED** (moved to transformation layer) |

---

## Errors

```
error EmptyBuffer();
error ObservationExpired(uint32 targetBlock, uint32 oldestBlock);
```

`EmptyBuffer` is raised by any view function when `CircularBuffer.count(buffer) == 0`.

`ObservationExpired` is raised by `observeAt` when the requested `targetBlock` is older
than the oldest observation remaining in the ring buffer (it has been overwritten).

---

## Section 1: BTT Behavior Trees

### 1.1 record

**Signature (V2):**

```
function record(
    CircularBuffer.Bytes32CircularBuffer storage buffer,
    uint256 _blockNumber,
    uint256 _relativeTimeDelta,
    uint256 _cumulativeGrowth
)
```

**Mutability:** storage-mutating (pushes to ring buffer)

**Preconditions:**
- Caller MUST have called `CircularBuffer.setup(buffer, N)` before first use. An
  uninitialized buffer will panic on `push()` (OZ behavior, not our revert).
- All three value parameters are uint256; safe-casting to their respective widths
  (uint32, uint16, uint208) is handled by `newGrowthObservation` and will revert
  via `SafeCastLib.Overflow()` if out of range.

```
BlockNumberAwareGrowthObserverLib::record
|
+-- given the buffer is empty (count == 0)
|   +-- when all inputs are within range
|       +-- it should push a new observation.
|       +-- it should be retrievable as the latest observation.
|       +-- it should set observationCount to 1.
|
+-- given the buffer has at least one observation (count > 0)
    |
    +-- when blockNumber equals the latest observation blockNumber
    |   +-- it should skip without pushing (idempotent).
    |   +-- it should NOT change observationCount.
    |   +-- it should leave the latest observation unchanged.
    |
    +-- when blockNumber is less than the latest observation blockNumber
    |   +-- it should skip without pushing (stale).
    |   +-- it should NOT change observationCount.
    |   +-- it should leave the latest observation unchanged.
    |
    +-- when blockNumber is strictly greater than the latest observation blockNumber
        +-- it should push a new observation with the given blockNumber.
        +-- it should push a new observation with the given relativeTimeDelta.
        +-- it should push a new observation with the given cumulativeGrowth.
        +-- it should increment the observation count by one (or wrap if buffer is full).
        +-- the new observation should be retrievable via latestObservation.
```

**Design notes:**

- Same-block and stale observations are **silently skipped** (no revert). This is
  intentional for keeper idempotency: if a keeper retries a transaction in the same block,
  the first value wins and the retry is a no-op.

- The comparison uses the `blockNumber()` accessor on the latest observation (returns uint32)
  and casts `_blockNumber` to uint32 for comparison. The safe-cast happens inside
  `newGrowthObservation` only when actually constructing the observation (i.e., only on
  the push path, not on the skip path).

- `_relativeTimeDelta` is caller-computed. This library does NOT read timestamps or compute
  deltas internally -- it is a passive store.

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| First ever record (empty buffer) | Push succeeds, count becomes 1 |
| Record with blockNumber == latest.blockNumber() | Skip, count unchanged |
| Record with blockNumber < latest.blockNumber() | Skip, count unchanged |
| Record with blockNumber == latest.blockNumber() + 1 | Push succeeds |
| Record with blockNumber == 0 into empty buffer | Push succeeds (0 is valid) |
| Record with blockNumber == 0 after a record with blockNumber == 0 | Skip (same block) |
| Record after buffer is full (wrapping) | Push succeeds, oldest is evicted, count stays at capacity |
| Record with _blockNumber > uint32 max | Reverts with SafeCastLib Overflow |
| Record with _relativeTimeDelta > uint16 max | Reverts with SafeCastLib Overflow |
| Record with _cumulativeGrowth > uint208 max | Reverts with SafeCastLib Overflow |

---

### 1.2 observeAt

**Signature (V2):**

```
function observeAt(
    CircularBuffer.Bytes32CircularBuffer storage buffer,
    uint32 targetBlock
) view returns (GrowthObservation)
```

**Mutability:** view (read-only)

```
BlockNumberAwareGrowthObserverLib::observeAt
|
+-- given the buffer is empty (count == 0)
|   +-- it should revert with EmptyBuffer.
|
+-- given the buffer has at least one observation
    |
    +-- when targetBlock >= latest observation blockNumber
    |   +-- it should return the latest observation.
    |
    +-- when targetBlock < oldest observation blockNumber
    |   +-- it should revert with ObservationExpired(targetBlock, oldestBlockNumber).
    |
    +-- when targetBlock is between oldest and latest blockNumbers (inclusive of oldest)
        |
        +-- when an observation exists at exactly targetBlock
        |   +-- it should return that exact observation.
        |
        +-- when no observation exists at exactly targetBlock
            +-- it should return the most recent observation BEFORE targetBlock.
            +-- the returned observation's blockNumber should be strictly less than targetBlock.
            +-- the next newer observation's blockNumber should be strictly greater than targetBlock.
```

**Algorithm: Binary search over descending recency indices**

The buffer stores observations in push order. `last(buffer, 0)` is the newest (highest
block number), `last(buffer, count-1)` is the oldest (lowest block number). The search
finds the smallest recency index `i` such that `last(buffer, i).blockNumber() <= targetBlock`.

```
Recency index:  0       1       2       ...     count-1
Block number:   900     850     800     ...     100
                newest  <---  descending  --->  oldest
```

Search bounds: `low = 1`, `high = count - 1` (index 0 is already handled by the
"targetBlock >= latest" early return).

Loop invariant: `last(buffer, low-1).blockNumber() > targetBlock` and
`last(buffer, high).blockNumber() <= targetBlock`.

Convergence: standard binary search; terminates when `low == high`.

**Complexity:** O(log2(capacity)). For the default 256-slot buffer, this is at most
8 SLOADs (binary search iterations) plus 3 SLOADs for the initial checks (count, newest,
oldest), totaling at most 11 SLOADs in the worst case.

**Semantic note -- "most recent observation before targetBlock":**

This is correct because cumulative growth is a step function: the accumulator value only
changes when rewards are distributed (at observation recording time). Between observations,
the accumulator is constant. Therefore, the observation immediately preceding `targetBlock`
holds the correct accumulator value for `targetBlock`.

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Empty buffer | Revert EmptyBuffer |
| Single observation, targetBlock == its blockNumber | Return that observation |
| Single observation, targetBlock > its blockNumber | Return that observation (latest) |
| Single observation, targetBlock < its blockNumber | Revert ObservationExpired |
| targetBlock == oldest blockNumber exactly | Return oldest observation |
| targetBlock == oldest blockNumber - 1 | Revert ObservationExpired |
| targetBlock == latest blockNumber exactly | Return latest observation |
| targetBlock == latest blockNumber + 100 | Return latest observation |
| Full buffer, targetBlock in middle, exact match | Return exact match |
| Full buffer, targetBlock in middle, no exact match | Return floor observation |
| Buffer with only two observations, targetBlock between them | Return older observation |
| Buffer after wrapping, targetBlock hits evicted range | Revert ObservationExpired |

---

### 1.3 latestObservation

**Signature:**

```
function latestObservation(
    CircularBuffer.Bytes32CircularBuffer storage buffer
) view returns (GrowthObservation)
```

**Mutability:** view

```
BlockNumberAwareGrowthObserverLib::latestObservation
|
+-- given the buffer is empty (count == 0)
|   +-- it should revert with EmptyBuffer.
|
+-- given the buffer has at least one observation
    +-- it should return the most recently pushed observation.
    +-- the returned observation should equal GrowthObservation.wrap(last(buffer, 0)).
```

**Implementation:** Reads `CircularBuffer.count(buffer)`, reverts if zero, otherwise
returns `GrowthObservation.wrap(CircularBuffer.last(buffer, 0))`.

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Empty buffer | Revert EmptyBuffer |
| Buffer with 1 observation | Return that observation |
| Buffer with N observations | Return the N-th pushed observation |
| Buffer after wrapping | Return the most recently pushed observation (not the evicted one) |

---

### 1.4 oldestObservation

**Signature:**

```
function oldestObservation(
    CircularBuffer.Bytes32CircularBuffer storage buffer
) view returns (GrowthObservation)
```

**Mutability:** view

```
BlockNumberAwareGrowthObserverLib::oldestObservation
|
+-- given the buffer is empty (count == 0)
|   +-- it should revert with EmptyBuffer.
|
+-- given the buffer has at least one observation
    +-- it should return the oldest observation still in the buffer.
    +-- the returned observation should equal GrowthObservation.wrap(last(buffer, count - 1)).
```

**Implementation:** Reads `CircularBuffer.count(buffer)`, reverts if zero, otherwise
returns `GrowthObservation.wrap(CircularBuffer.last(buffer, count - 1))`.

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Empty buffer | Revert EmptyBuffer |
| Buffer with 1 observation | Return that observation (same as latest) |
| Buffer partially filled (3 of 256 slots) | Return the first-ever pushed observation |
| Buffer full but not yet wrapped | Return the first-ever pushed observation |
| Buffer after wrapping (e.g., 260 pushes into 256-slot buffer) | Return the 5th pushed observation (first 4 evicted) |

---

### 1.5 observationCount

**Signature:**

```
function observationCount(
    CircularBuffer.Bytes32CircularBuffer storage buffer
) view returns (uint256)
```

**Mutability:** view

```
BlockNumberAwareGrowthObserverLib::observationCount
|
+-- given the buffer is empty (count == 0)
|   +-- it should return zero.
|
+-- given the buffer is partially filled
|   +-- it should return the number of observations pushed.
|
+-- given the buffer is full and has wrapped
    +-- it should return the buffer capacity.
    +-- it should NOT exceed the buffer capacity regardless of total pushes.
```

**Implementation:** Directly delegates to `CircularBuffer.count(buffer)`, which returns
`min(_count, _data.length)`.

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Uninitialized buffer (setup never called) | Returns 0 (min(0, 0)) |
| Empty buffer (setup called, no pushes) | Returns 0 |
| After 1 push | Returns 1 |
| After N pushes (N < capacity) | Returns N |
| After exactly capacity pushes | Returns capacity |
| After capacity + K pushes (K > 0) | Returns capacity (saturated) |

---

## Section 2: Removed Function

### observeGrowthDelta -- REMOVED

**Previous signature (V1):**

```
function observeGrowthDelta(
    CircularBuffer.Bytes32CircularBuffer storage buffer,
    uint48 startBlock,
    uint48 endBlock
) view returns (uint208)
```

**Removal rationale:** `observeGrowthDelta` computes a windowed delta (`growthDelta`
between two observations looked up by block number). This is a **transformation** --
it derives a new value from raw observations. Under the layered architecture:

- **Layer 1 (this library):** Raw observation infrastructure -- store, retrieve, search.
- **Layer 2 (transformation contracts):** Domain-specific computations consuming Layer 1
  primitives (windowed delta, EMA, TWAP, median, etc.).

The `extensionFlag` in `NoteId` determines which transformation is applied. Each extension
contract defines its own function that calls `observeAt` (Layer 1) and then applies its
specific transformation logic. Embedding one specific transformation (windowed delta) in the
infrastructure library would create an asymmetry where one transformation is privileged over
others.

Layer 2 consumers that need windowed delta functionality should implement it as:

```
GrowthObservation earlier = observeAt(buffer, startBlock);
GrowthObservation later   = observeAt(buffer, endBlock);
uint208 delta = earlier.growthDelta(later);
```

This is a two-line composition of existing primitives and does not warrant inclusion in the
infrastructure library.

---

## Section 3: Algebraic Properties (Invariants for Fuzz Testing)

### Property 1: Monotonicity of record

**Statement:** After a successful (non-skipped) `record(buffer, bn, rtd, cg)`,
`latestObservation(buffer).blockNumber()` equals `bn` (cast to uint32). The latest
observation always has the highest block number in the buffer.

**Formal:**

```
Pre:  count == 0 || bn > latestObservation(buffer).blockNumber()
      bn <= uint32 max, rtd <= uint16 max, cg <= uint208 max
Action: record(buffer, bn, rtd, cg)
Post: latestObservation(buffer).blockNumber() == uint32(bn)
      For all i in [0, observationCount-2]:
        last(buffer, i).blockNumber() > last(buffer, i+1).blockNumber()
```

**Test approach:** Fuzz a sequence of strictly increasing block numbers, verify after each
record that the latest observation matches and the full buffer is in descending order.

---

### Property 2: Idempotence of record

**Statement:** Calling `record` twice with the same `blockNumber` (where the second call
has `blockNumber == latestObservation.blockNumber()`) produces the same buffer state as
calling it once. `observationCount` does not change on the second call.

**Formal:**

```
Pre:  record(buffer, bn, rtd1, cg1) executed successfully
Action: record(buffer, bn, rtd2, cg2)   // same bn, potentially different rtd/cg
Post: observationCount(buffer) == countBefore
      latestObservation(buffer) == observationBefore  // first record's values win
```

**Test approach:** Record an observation, snapshot the buffer state, record again with
the same block number but different relativeTimeDelta and cumulativeGrowth values, verify
the buffer is identical to the snapshot.

---

### Property 3: Ordering invariant (descending block numbers)

**Statement:** For any recency indices `i < j` where both are less than `observationCount(buffer)`,
the observation at recency index `i` has a strictly higher `blockNumber` than the observation
at recency index `j`. The buffer is always in strictly descending order by block number.

**Formal:**

```
For all i, j where 0 <= i < j < observationCount(buffer):
  last(buffer, i).blockNumber() > last(buffer, j).blockNumber()
```

**Test approach:** Push a fuzzed sequence of block numbers (some strictly increasing, some
same-block, some stale). After each push, iterate the entire buffer and verify strict
descending order.

**Strengthened form:** Because `record` only accepts strictly greater block numbers and
silently skips same-or-stale, and because the buffer is append-only (no mutation of existing
entries), the ordering invariant is maintained inductively.

---

### Property 4: observeAt consistency (point query exactness)

**Statement:** For any observation `obs` currently in the buffer,
`observeAt(buffer, obs.blockNumber())` returns `obs` exactly. Point queries at recorded
block numbers are exact.

**Formal:**

```
For all i in [0, observationCount(buffer) - 1]:
  obs = GrowthObservation.wrap(last(buffer, i))
  observeAt(buffer, obs.blockNumber()) == obs
```

**Test approach:** Push N observations with known block numbers. For each observation
in the buffer, call `observeAt` with its exact block number and assert equality of
the returned bytes32.

---

### Property 5: observeAt monotonicity

**Statement:** For `targetA <= targetB` where both are within the buffer's valid range
(i.e., both >= oldest block number), `observeAt(buffer, targetA).blockNumber() <=
observeAt(buffer, targetB).blockNumber()`. Higher target blocks return same-or-later
observations.

**Formal:**

```
Pre:  targetA <= targetB
      targetA >= oldestObservation(buffer).blockNumber()
      targetB <= latestObservation(buffer).blockNumber()
Post: observeAt(buffer, targetA).blockNumber() <= observeAt(buffer, targetB).blockNumber()
```

**Test approach:** Fuzz two target blocks within the buffer's valid range, call `observeAt`
on both, verify the block number ordering of the results.

---

### Property 6: Count boundedness

**Statement:** `observationCount(buffer)` is always less than or equal to the buffer
capacity (set at `setup` time). It never exceeds the capacity.

**Formal:**

```
For all buffer states:
  observationCount(buffer) <= CircularBuffer.length(buffer)
```

**Test approach:** Fuzz a sequence of N pushes (where N >> capacity), verify after each
push that `observationCount <= capacity`.

---

### Property 7: Record-then-read round-trip

**Statement:** After `record(buffer, bn, rtd, cg)` where `bn > latestObservation.blockNumber()`
(or the buffer is empty), `latestObservation(buffer)` returns an observation where
`blockNumber() == uint32(bn)`, `relativeTimeDelta() == uint16(rtd)`, and
`cumulativeGrowth() == uint208(cg)`.

**Formal:**

```
Pre:  count == 0 || bn > latestObservation(buffer).blockNumber()
      bn <= uint32 max, rtd <= uint16 max, cg <= uint208 max
Action: record(buffer, bn, rtd, cg)
Post: obs = latestObservation(buffer)
      obs.blockNumber()       == uint32(bn)
      obs.relativeTimeDelta() == uint16(rtd)
      obs.cumulativeGrowth()  == uint208(cg)
```

**Test approach:** Fuzz valid (bn, rtd, cg) triples, record each into the buffer, read
back via `latestObservation`, verify all three fields match.

**Relationship to GrowthObservation Property 1 (round-trip packing):** This property
composes the type-level round-trip guarantee with the storage round-trip through the
CircularBuffer. It verifies that the `push` -> `last(0)` -> `wrap` pipeline preserves
all bits.

---

## Section 4: Interaction Between Functions

### 4.1 record + latestObservation

After a successful (non-skipped) `record`, `latestObservation` MUST return the observation
that was just recorded. This is the fundamental write-then-read contract.

### 4.2 record + oldestObservation

After the buffer wraps (total pushes > capacity), `oldestObservation` returns the observation
at recency index `count - 1`, which is the oldest surviving observation. The observation that
was previously oldest has been evicted.

### 4.3 record + observeAt

After a successful `record(buffer, bn, rtd, cg)`:
- `observeAt(buffer, uint32(bn))` MUST return the new observation.
- `observeAt(buffer, uint32(bn) + K)` for K > 0 MUST also return the new observation
  (it is the latest, so any target >= its block number returns it).
- `observeAt(buffer, uint32(bn) - 1)` MUST return the previous latest observation
  (the one that was latest before this record), provided it is still in the buffer.

### 4.4 observeAt + latestObservation/oldestObservation

The following identities hold:
- `observeAt(buffer, latestObservation(buffer).blockNumber())` returns `latestObservation(buffer)`.
- `observeAt(buffer, oldestObservation(buffer).blockNumber())` returns `oldestObservation(buffer)`.
- `observeAt(buffer, type(uint32).max)` returns `latestObservation(buffer)` (because max >= any block number).
- `observeAt(buffer, 0)` either returns `oldestObservation(buffer)` (if oldest block is 0) or reverts with `ObservationExpired`.

---

## Section 5: Buffer Lifecycle Scenarios

### 5.1 Fresh buffer (0 observations)

| Function | Result |
|---|---|
| `observationCount` | 0 |
| `latestObservation` | Revert EmptyBuffer |
| `oldestObservation` | Revert EmptyBuffer |
| `observeAt(_, anyBlock)` | Revert EmptyBuffer |

### 5.2 Single observation

After one successful `record(buffer, 100, 0, 5000)`:

| Function | Result |
|---|---|
| `observationCount` | 1 |
| `latestObservation` | Observation(bn=100, rtd=0, cg=5000) |
| `oldestObservation` | Observation(bn=100, rtd=0, cg=5000) (same as latest) |
| `observeAt(_, 100)` | Observation(bn=100, rtd=0, cg=5000) |
| `observeAt(_, 200)` | Observation(bn=100, rtd=0, cg=5000) (latest, since 200 >= 100) |
| `observeAt(_, 99)` | Revert ObservationExpired(99, 100) |

### 5.3 Partially filled buffer (capacity = 256, 3 observations)

After recording at blocks 100, 200, 300:

| Function | Result |
|---|---|
| `observationCount` | 3 |
| `latestObservation.blockNumber()` | 300 |
| `oldestObservation.blockNumber()` | 100 |
| `observeAt(_, 250)` | Observation at block 200 (floor) |
| `observeAt(_, 200)` | Observation at block 200 (exact) |
| `observeAt(_, 99)` | Revert ObservationExpired(99, 100) |

### 5.4 Full buffer after wrapping (capacity = 4, 6 pushes)

Pushed blocks: 10, 20, 30, 40, 50, 60. Buffer contains: 30, 40, 50, 60 (10 and 20 evicted).

| Function | Result |
|---|---|
| `observationCount` | 4 (capacity) |
| `latestObservation.blockNumber()` | 60 |
| `oldestObservation.blockNumber()` | 30 |
| `observeAt(_, 45)` | Observation at block 40 (floor) |
| `observeAt(_, 29)` | Revert ObservationExpired(29, 30) |
| `observeAt(_, 20)` | Revert ObservationExpired(20, 30) -- was evicted |

---

## Section 6: Binary Search Correctness Analysis

### 6.1 Search space

The binary search in `observeAt` operates over recency indices `[1, count-1]`. Index 0
(the latest observation) is handled by the early return before the search begins.

### 6.2 Loop invariant

At each iteration: `last(buffer, low-1).blockNumber() > targetBlock >= last(buffer, high).blockNumber()`.

This is established before the loop:
- `low = 1`: we know `last(buffer, 0).blockNumber() > targetBlock` (from the early return guard).
- `high = count - 1`: we know `last(buffer, count-1).blockNumber() <= targetBlock` (from the
  ObservationExpired guard, which checks `oldest.blockNumber() > targetBlock`).

### 6.3 Midpoint calculation

`mid = (low + high) / 2`. Since `low >= 1` and `high <= count-1 <= 255`, the sum
`low + high <= 510`, which cannot overflow.

### 6.4 Convergence

At each step, either `low` increases or `high` decreases (or both). The loop terminates
when `low == high`. The final index `low` points to the observation at or just before
`targetBlock`.

### 6.5 Worst-case SLOADs

For a 256-slot buffer: `ceil(log2(255))` = 8 iterations, each performing one SLOAD
(`CircularBuffer.last`). Plus 3 initial SLOADs (count, newest, oldest). Total: 11 SLOADs.

### 6.6 Edge case: count == 1

When count is 1, the early return handles all cases:
- `targetBlock >= newest.blockNumber()`: return newest.
- `targetBlock < newest.blockNumber()`: oldest == newest, so `oldest.blockNumber() > targetBlock`,
  which triggers ObservationExpired.

The binary search loop is never entered (low = 1, high = 0 would be invalid, but this
code path is unreachable because one of the two guards above fires first).

### 6.7 Edge case: count == 2

`low = 1`, `high = 1`. The while loop condition `low < high` is false, so the loop body
never executes. The result is `last(buffer, 1)` = the oldest observation. This is correct
because the early return already handled the case where `targetBlock >= newest.blockNumber()`,
so the only remaining valid target is one where the oldest observation is the floor.

---

## Section 7: Gas Analysis

| Function | Cold SLOADs | Hot SLOADs | Notes |
|---|---|---|---|
| `record` (push path) | 1-2 | 1 | Read count + read latest (if count > 0), then push (1 SSTORE) |
| `record` (skip path) | 1-2 | 0 | Read count + read latest, no write |
| `latestObservation` | 1-2 | 0 | Read count + read last(0) |
| `oldestObservation` | 1-2 | 0 | Read count + read last(count-1) |
| `observationCount` | 1 | 0 | Read count only |
| `observeAt` (exact latest) | 2 | 0 | Read count + read last(0), early return |
| `observeAt` (binary search) | 3 + ceil(log2(count)) | 0 | count + newest + oldest + search iterations |

The dominant cost is `observeAt` in the binary search case, which is bounded at 11 cold
SLOADs (~23,100 gas at 2,100 gas per cold SLOAD). For hot access patterns (e.g., multiple
`observeAt` calls in the same transaction), the cost drops to ~1,100 gas per SLOAD (100 gas
per hot SLOAD).

---

## Section 8: Design Decisions

### 8.1 Buffer initialization is the caller's responsibility

The library does NOT call `CircularBuffer.setup()` internally. An uninitialized buffer
(`_data.length == 0`) will cause OZ's `push()` to panic with a division-by-zero error
when computing `index % modulus`. This is acceptable: the adapter contract's constructor
or initializer MUST call `setup()`.

Rationale: The library is stateless infrastructure. It should not make assumptions about
when or how the buffer is initialized. Initialization is a one-time lifecycle event
controlled by the owning contract.

### 8.2 Silent skip for same-block and stale observations

`record` does not revert on same-block or stale block numbers. It silently returns without
modifying state. This design supports keeper idempotency: if a keeper's transaction is
retried (e.g., due to gas price bumping), the retry is a harmless no-op.

Alternative considered: Reverting with a `StaleObservation` error. Rejected because it
would cause keeper retries to fail, complicating keeper infrastructure for no safety benefit
(the access-controlled `recordObservation` on the adapter prevents frontrunning).

### 8.3 Transformation-agnostic architecture

This library provides ONLY storage and retrieval primitives. It does NOT compute:
- Windowed deltas (`observeGrowthDelta` is removed)
- Exponential moving averages
- Time-weighted average growth rates
- Medians or percentiles

Each transformation is implemented in a separate Layer 2 contract/library that consumes
`observeAt`, `latestObservation`, `oldestObservation`, and `observationCount` as primitives.
The `extensionFlag` in `NoteId` routes to the appropriate transformation contract.

### 8.4 relativeTimeDelta is caller-provided

The `record` function accepts `_relativeTimeDelta` as a parameter rather than computing it
internally. This is because:
- The library has no access to `block.timestamp` (it is a library of free functions).
- Even if it did, computing the delta requires knowing the previous observation's timestamp,
  which would require an additional SLOAD.
- The caller (adapter contract) already has the information needed to compute the delta.
- Keeping the library as a passive store simplifies testing and reasoning.

### 8.5 uint32 targetBlock for observeAt

Changed from uint48 in V1 to uint32 in V2 to match the GrowthObservation V2 type's
`blockNumber` width. A uint32 block number supports ~1,633 years of Ethereum blocks at
12-second intervals, which exceeds any reasonable deployment horizon.

---

## Section 9: Test Harness Requirements

### 9.1 Storage setup

Tests MUST call `CircularBuffer.setup(buffer, capacity)` before any other function.
The default test capacity should be 256 (matching production), with smaller capacities
(e.g., 4, 8) used for wrapping tests.

### 9.2 Helper functions for test contracts

The test harness should expose:

```
// Wrappers that forward to the free functions with the test contract's storage buffer
function record(uint256 bn, uint256 rtd, uint256 cg) external
function observeAt(uint32 targetBlock) external view returns (GrowthObservation)
function latestObservation() external view returns (GrowthObservation)
function oldestObservation() external view returns (GrowthObservation)
function observationCount() external view returns (uint256)

// Direct buffer inspection for invariant tests
function observationAtRecencyIndex(uint256 i) external view returns (GrowthObservation)
function bufferCapacity() external view returns (uint256)
```

### 9.3 Fuzz input ranges

| Parameter | Fuzz Type | Min | Max | Notes |
|---|---|---|---|---|
| blockNumber | uint256 (bounded) | 0 | `2^32 - 1` | For valid-input tests |
| blockNumber (overflow) | uint256 (bounded) | `2^32` | `type(uint256).max` | For revert tests |
| relativeTimeDelta | uint256 (bounded) | 0 | `2^16 - 1` | For valid-input tests |
| relativeTimeDelta (overflow) | uint256 (bounded) | `2^16` | `type(uint256).max` | For revert tests |
| cumulativeGrowth | uint256 (bounded) | 0 | `2^208 - 1` | For valid-input tests |
| cumulativeGrowth (overflow) | uint256 (bounded) | `2^208` | `type(uint256).max` | For revert tests |
| targetBlock | uint32 | 0 | `2^32 - 1` | For observeAt |
| bufferCapacity | uint256 (bounded) | 1 | 256 | For setup |
| sequenceLength | uint256 (bounded) | 1 | 512 | For wrapping tests |

### 9.4 Sequence generation for ordering tests

To test the ordering invariant and binary search correctness, generate sequences of block
numbers with the following properties:

- **Strictly increasing subsequence:** The block numbers that are actually recorded form a
  strictly increasing sequence (after filtering out same-block and stale attempts).
- **Gaps:** Include gaps of varying sizes (1, 2, 10, 100, 1000) between consecutive recorded
  block numbers to exercise binary search at different gap widths.
- **Noise:** Intersperse same-block and stale block numbers in the fuzzed sequence to verify
  that `record` correctly skips them without corrupting the buffer.

---

## Section 10: Complete Function Signature Summary (V2)

| Function | Mutability | Parameters | Returns | Reverts |
|---|---|---|---|---|
| `record` | mutating | `(buffer, uint256 _blockNumber, uint256 _relativeTimeDelta, uint256 _cumulativeGrowth)` | -- | SafeCastLib.Overflow (via newGrowthObservation) |
| `observeAt` | view | `(buffer, uint32 targetBlock)` | `GrowthObservation` | EmptyBuffer, ObservationExpired |
| `latestObservation` | view | `(buffer)` | `GrowthObservation` | EmptyBuffer |
| `oldestObservation` | view | `(buffer)` | `GrowthObservation` | EmptyBuffer |
| `observationCount` | view | `(buffer)` | `uint256` | -- (never reverts) |

All functions are **free functions** (file-level, not inside a `library` block).

All functions take `CircularBuffer.Bytes32CircularBuffer storage` as the first parameter.

The `observeGrowthDelta` function present in V1 is **removed** in V2.

---

## Appendix A: Relationship to Layer 2 Transformation Contracts

```
                    +---------------------------+
                    | Layer 2: Transformations  |
                    |                           |
                    |  WindowedDeltaExtension   |  <-- replaces observeGrowthDelta
                    |  EMAExtension             |
                    |  TWAPExtension            |
                    |  MedianExtension          |
                    |  (future extensions...)   |
                    +---------------------------+
                              |
                    calls observeAt, latestObservation,
                    oldestObservation, observationCount
                              |
                              v
                    +---------------------------+
                    | Layer 1: Infrastructure   |
                    |                           |
                    | BlockNumberAwareGrowth-    |
                    | ObserverLib (this spec)    |
                    +---------------------------+
                              |
                    push, last, count
                              |
                              v
                    +---------------------------+
                    | Storage: OZ Circular-     |
                    | Buffer (256 slots)        |
                    +---------------------------+
```

Each Layer 2 extension:
1. Reads raw observations via Layer 1 primitives.
2. Applies its specific transformation logic.
3. Returns a derived value to the caller (e.g., adapter contract).

The `extensionFlag` in `NoteId` routes to the appropriate Layer 2 extension at runtime.

---

## Appendix B: OZ CircularBuffer Behavioral Summary

For reference, here is the behavioral model of the OZ CircularBuffer that this specification
depends on:

| Operation | State Change | Return Value |
|---|---|---|
| `setup(N)` | `_count = 0`, `_data.length = N` | -- |
| `push(v)` | `_data[_count % N] = v`, `_count++` | -- |
| `count()` | -- | `min(_count, N)` |
| `length()` | -- | `N` (fixed at setup) |
| `last(i)` | -- | `_data[(_count - i - 1) % N]` if `i < count()`, else PANIC |

Critical invariant: `last(0)` always returns the most recently pushed value. `last(count()-1)`
always returns the oldest surviving value.

Wrapping behavior: When `_count >= N`, pushing overwrites the slot at `_count % N`, which
is the oldest slot. After the push, `count()` remains `N` and `last(N-1)` now points to
what was previously `last(N-2)` (the oldest surviving has advanced by one).
