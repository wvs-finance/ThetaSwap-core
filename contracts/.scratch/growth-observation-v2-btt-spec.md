# GrowthObservation V2 -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/types/GrowthObservation.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Supersedes:** GrowthObservation V1 (uint48 blockNumber + uint208 cumulativeGrowth)

---

## Changelog from V1

| Property | V1 | V2 |
|---|---|---|
| blockNumber width | uint48 (bits 0-47) | uint32 (bits 0-31) |
| relativeTimeDelta | -- (not present) | uint16 (bits 32-47) |
| cumulativeGrowth width | uint208 (bits 48-255) | uint208 (bits 48-255) |
| cumulativeGrowth shift | 48 | 48 (unchanged: 32 + 16 = 48) |
| `blockNumber()` return type | uint48 | uint32 |
| `elapsedBlocks()` return type | uint48 | uint32 |
| `blockNumberGte` parameter | uint48 targetBlock | uint32 targetBlock |
| `blockNumberLt` parameter | uint48 targetBlock | uint32 targetBlock |
| Constructor SafeCast for blockNumber | `toUint48` | `toUint32` |
| Constructor SafeCast for relativeTimeDelta | -- | `toUint16` |
| `StaleObservation` error fields | uint48, uint48 | uint32, uint32 |

---

## Section 1: BTT Behavior Trees

### 1.1 Constructor -- `newGrowthObservation`

**Signature (V2):**
`newGrowthObservation(uint256 _blockNumber, uint256 _relativeTimeDelta, uint256 _cumulativeGrowth) pure returns (GrowthObservation)`

```
GrowthObservation::newGrowthObservation
├── when _blockNumber exceeds uint32 max (> 0xFFFFFFFF)
│   └── it should revert with SafeCastLib Overflow().
├── when _relativeTimeDelta exceeds uint16 max (> 0xFFFF)
│   └── it should revert with SafeCastLib Overflow().
├── when _cumulativeGrowth exceeds uint208 max (> 2^208 - 1)
│   └── it should revert with SafeCastLib Overflow().
└── when all inputs are within range
    ├── it should pack _blockNumber into bits [0, 31].
    ├── it should pack _relativeTimeDelta into bits [32, 47].
    ├── it should pack _cumulativeGrowth into bits [48, 255].
    └── it should round-trip all three fields through their respective accessors.
```

**Test boundary values for each overflow branch:**

| Field | Boundary | Passes | Reverts |
|---|---|---|---|
| blockNumber | `2^32 - 1` = 4,294,967,295 | yes | -- |
| blockNumber | `2^32` = 4,294,967,296 | -- | Overflow |
| relativeTimeDelta | `2^16 - 1` = 65,535 | yes | -- |
| relativeTimeDelta | `2^16` = 65,536 | -- | Overflow |
| cumulativeGrowth | `2^208 - 1` | yes | -- |
| cumulativeGrowth | `2^208` | -- | Overflow |

---

### 1.2 Accessor -- `blockNumber`

**Signature (V2):**
`blockNumber(GrowthObservation self) pure returns (uint32)`

```
GrowthObservation::blockNumber
├── when observation is zero (bytes32(0))
│   └── it should return 0.
├── when only blockNumber bits are set (relativeTimeDelta = 0, cumulativeGrowth = 0)
│   └── it should return the exact blockNumber value.
├── when only relativeTimeDelta bits are set (blockNumber = 0, cumulativeGrowth = 0)
│   └── it should return 0 (not contaminated by adjacent field).
├── when only cumulativeGrowth bits are set (blockNumber = 0, relativeTimeDelta = 0)
│   └── it should return 0 (not contaminated by upper field).
└── when all three fields are at their max values
    └── it should return uint32 max (0xFFFFFFFF) exactly.
```

---

### 1.3 Accessor -- `relativeTimeDelta`

**Signature (V2):**
`relativeTimeDelta(GrowthObservation self) pure returns (uint16)`

```
GrowthObservation::relativeTimeDelta
├── when observation is zero (bytes32(0))
│   └── it should return 0.
├── when only relativeTimeDelta bits are set (blockNumber = 0, cumulativeGrowth = 0)
│   └── it should return the exact relativeTimeDelta value.
├── when only blockNumber bits are set (relativeTimeDelta = 0, cumulativeGrowth = 0)
│   └── it should return 0 (not contaminated by adjacent field).
├── when only cumulativeGrowth bits are set (blockNumber = 0, relativeTimeDelta = 0)
│   └── it should return 0 (not contaminated by upper field).
└── when all three fields are at their max values
    └── it should return uint16 max (0xFFFF) exactly.
```

---

### 1.4 Accessor -- `cumulativeGrowth`

**Signature (V2):**
`cumulativeGrowth(GrowthObservation self) pure returns (uint208)`

```
GrowthObservation::cumulativeGrowth
├── when observation is zero (bytes32(0))
│   └── it should return 0.
├── when only cumulativeGrowth bits are set (blockNumber = 0, relativeTimeDelta = 0)
│   └── it should return the exact cumulativeGrowth value.
├── when only blockNumber bits are set (cumulativeGrowth = 0, relativeTimeDelta = 0)
│   └── it should return 0 (not contaminated by lower field).
├── when only relativeTimeDelta bits are set (blockNumber = 0, cumulativeGrowth = 0)
│   └── it should return 0 (not contaminated by adjacent field).
└── when all three fields are at their max values
    └── it should return uint208 max exactly.
```

---

### 1.5 Derived View -- `growthDelta`

**Signature (unchanged):**
`growthDelta(GrowthObservation earlier, GrowthObservation later) pure returns (uint208)`

```
GrowthObservation::growthDelta
├── when both observations have cumulativeGrowth = 0
│   └── it should return 0.
├── when earlier.cumulativeGrowth() == later.cumulativeGrowth()
│   └── it should return 0.
├── when later.cumulativeGrowth() > earlier.cumulativeGrowth()
│   └── it should return later.cumulativeGrowth() - earlier.cumulativeGrowth().
└── when later.cumulativeGrowth() < earlier.cumulativeGrowth() (caller violation)
    └── it should return a wrapped value (unchecked subtraction wraps modulo 2^208).
```

**Note:** The unchecked subtraction is intentional. Callers MUST ensure temporal ordering.
The `observeGrowthDelta()` function in `BlockNumberAwareGrowthObserverLib` enforces
`startBlock < endBlock` before calling this function.

---

### 1.6 Derived View -- `elapsedBlocks`

**Signature (V2):**
`elapsedBlocks(GrowthObservation earlier, GrowthObservation later) pure returns (uint32)`

```
GrowthObservation::elapsedBlocks
├── when both observations have blockNumber = 0
│   └── it should return 0.
├── when earlier.blockNumber() == later.blockNumber()
│   └── it should return 0.
├── when later.blockNumber() > earlier.blockNumber()
│   └── it should return later.blockNumber() - earlier.blockNumber().
└── when later.blockNumber() < earlier.blockNumber() (caller violation)
    └── it should return a wrapped value (unchecked subtraction wraps modulo 2^32).
```

**V1 to V2 change:** Return type narrowed from uint48 to uint32.

---

### 1.7 Derived View -- `isZero`

**Signature (unchanged):**
`isZero(GrowthObservation self) pure returns (bool)`

```
GrowthObservation::isZero
├── when observation is bytes32(0)
│   └── it should return true.
├── when only blockNumber is non-zero
│   └── it should return false.
├── when only relativeTimeDelta is non-zero
│   └── it should return false.
├── when only cumulativeGrowth is non-zero
│   └── it should return false.
└── when all three fields are non-zero
    └── it should return false.
```

---

### 1.8 Comparator -- `gte`

**Signature (unchanged in interface, but blockNumber() now returns uint32):**
`gte(GrowthObservation a, GrowthObservation b) pure returns (bool)`

```
GrowthObservation::gte
├── when a.blockNumber() > b.blockNumber()
│   └── it should return true.
├── when a.blockNumber() == b.blockNumber()
│   └── it should return true.
├── when a.blockNumber() < b.blockNumber()
│   └── it should return false.
├── when both observations are zero
│   └── it should return true (0 >= 0).
└── when relativeTimeDelta or cumulativeGrowth differ but blockNumbers are equal
    └── it should return true (comparison is solely on blockNumber).
```

---

### 1.9 Comparator -- `lt`

**Signature (unchanged in interface):**
`lt(GrowthObservation a, GrowthObservation b) pure returns (bool)`

```
GrowthObservation::lt
├── when a.blockNumber() < b.blockNumber()
│   └── it should return true.
├── when a.blockNumber() == b.blockNumber()
│   └── it should return false.
├── when a.blockNumber() > b.blockNumber()
│   └── it should return false.
├── when both observations are zero
│   └── it should return false (0 < 0 is false).
└── when relativeTimeDelta or cumulativeGrowth differ but blockNumbers are equal
    └── it should return false (comparison is solely on blockNumber).
```

---

### 1.10 Comparator -- `blockNumberGte`

**Signature (V2):**
`blockNumberGte(GrowthObservation self, uint32 targetBlock) pure returns (bool)`

```
GrowthObservation::blockNumberGte
├── when self.blockNumber() > targetBlock
│   └── it should return true.
├── when self.blockNumber() == targetBlock
│   └── it should return true.
├── when self.blockNumber() < targetBlock
│   └── it should return false.
├── when both are zero
│   └── it should return true.
└── when self.blockNumber() == uint32 max and targetBlock == uint32 max
    └── it should return true.
```

**V1 to V2 change:** `targetBlock` parameter type narrowed from uint48 to uint32.

---

### 1.11 Comparator -- `blockNumberLt`

**Signature (V2):**
`blockNumberLt(GrowthObservation self, uint32 targetBlock) pure returns (bool)`

```
GrowthObservation::blockNumberLt
├── when self.blockNumber() < targetBlock
│   └── it should return true.
├── when self.blockNumber() == targetBlock
│   └── it should return false.
├── when self.blockNumber() > targetBlock
│   └── it should return false.
├── when both are zero
│   └── it should return false.
└── when self.blockNumber() == uint32 max and targetBlock == uint32 max
    └── it should return false.
```

**V1 to V2 change:** `targetBlock` parameter type narrowed from uint48 to uint32.

---

## Section 2: Algebraic Properties (Invariants for Fuzz Testing)

### Property 1: Round-trip Packing

For any `(bn, rtd, cg)` where `bn <= 2^32 - 1`, `rtd <= 2^16 - 1`, `cg <= 2^208 - 1`:

```
obs = newGrowthObservation(bn, rtd, cg)
assert obs.blockNumber()        == bn
assert obs.relativeTimeDelta()  == rtd
assert obs.cumulativeGrowth()   == cg
```

This is the fundamental correctness property of the bit-packing scheme. Every valid input triple must survive a pack-unpack round trip without any data loss or cross-field contamination.

### Property 2: Monotonicity of cumulativeGrowth Delta

For any two observations `a` and `b` where `a.cumulativeGrowth() <= b.cumulativeGrowth()`:

```
growthDelta(a, b) == b.cumulativeGrowth() - a.cumulativeGrowth()
```

The delta equals the arithmetic difference when the ordering precondition holds. Since the return type is uint208 and the subtraction is unchecked, the result is non-negative by definition when `b >= a` in the unsigned sense.

### Property 3: Ordering Consistency (gte/lt are complements)

For all observation pairs `(a, b)`:

```
a.gte(b) == !a.lt(b)
a.lt(b)  == !a.gte(b)
```

Equivalently, for the scalar comparators and all valid uint32 `t`:

```
self.blockNumberGte(t) == !self.blockNumberLt(t)
self.blockNumberLt(t)  == !self.blockNumberGte(t)
```

### Property 4: Zero Identity

```
isZero(newGrowthObservation(0, 0, 0)) == true
```

For any `(bn, rtd, cg)` where at least one component is non-zero:

```
isZero(newGrowthObservation(bn, rtd, cg)) == false
```

### Property 5: Bit Isolation

Setting any single field to its maximum value must not affect the other two fields.

```
// blockNumber at max, others zero
obs_bn = newGrowthObservation(2^32 - 1, 0, 0)
assert obs_bn.relativeTimeDelta() == 0
assert obs_bn.cumulativeGrowth()  == 0

// relativeTimeDelta at max, others zero
obs_rtd = newGrowthObservation(0, 2^16 - 1, 0)
assert obs_rtd.blockNumber()       == 0
assert obs_rtd.cumulativeGrowth()  == 0

// cumulativeGrowth at max, others zero
obs_cg = newGrowthObservation(0, 0, 2^208 - 1)
assert obs_cg.blockNumber()        == 0
assert obs_cg.relativeTimeDelta()  == 0
```

### Property 6: Elapsed Blocks Consistency

For observations `a` and `b` where `a.blockNumber() <= b.blockNumber()`:

```
elapsedBlocks(a, b) == b.blockNumber() - a.blockNumber()
```

### Property 7: gte/lt Agree with blockNumberGte/blockNumberLt

For any two observations `a` and `b`:

```
a.gte(b) == a.blockNumberGte(b.blockNumber())
a.lt(b)  == a.blockNumberLt(b.blockNumber())
```

This property ensures the observation-vs-observation comparators and the observation-vs-scalar comparators are semantically identical when the scalar is extracted from an observation.

---

## Section 3: Mask and Shift Constants

### Bit Layout Diagram

```
Bit 255                                    Bit 48  Bit 47  Bit 32  Bit 31       Bit 0
 |                                           |       |       |       |             |
 [  cumulativeGrowth (208 bits)              ][ rtd  ][ blockNumber (32 bits)      ]
 |<------------ 208 bits ------------------>||<16b>| |<---------- 32 bits -------->|
```

### Constants

| Constant | Value | Purpose |
|---|---|---|
| `BLOCK_NUMBER_MASK` | `(1 << 32) - 1` = `0xFFFFFFFF` | Isolates bits [0, 31] |
| `RELATIVE_TIME_DELTA_MASK` | `(1 << 16) - 1` = `0xFFFF` | Isolates 16 bits after shift |
| `CUMULATIVE_GROWTH_MASK` | `(1 << 208) - 1` | Isolates 208 bits after shift |

### Shift Offsets

| Field | Shift (right-shift for extraction) | Width |
|---|---|---|
| blockNumber | 0 (no shift, mask only) | 32 bits |
| relativeTimeDelta | 32 (shift right by 32, then mask 16 bits) | 16 bits |
| cumulativeGrowth | 48 (shift right by 48, then mask 208 bits) | 208 bits |

### Packing Formula

```
packed = uint256(uint32(blockNumber))
       | (uint256(uint16(relativeTimeDelta)) << 32)
       | (uint256(uint208(cumulativeGrowth)) << 48)
```

### Extraction Formulas

```
blockNumber       = uint32(packed & BLOCK_NUMBER_MASK)
relativeTimeDelta = uint16((packed >> 32) & RELATIVE_TIME_DELTA_MASK)
cumulativeGrowth  = uint208((packed >> 48) & CUMULATIVE_GROWTH_MASK)
```

---

## Section 4: Migration Notes (V1 to V2)

### 4.1 blockNumber: uint48 to uint32

**Rationale:** A uint32 block number supports values up to 4,294,967,295. At Ethereum's
~12-second block time, this covers approximately 1,600 years of blocks from genesis.
The 16 bits freed by this reduction are reallocated to the new `relativeTimeDelta` field.

**Impact:** Any code that stores or compares block numbers as uint48 must be narrowed
to uint32. This includes the `StaleObservation` error type and all function signatures
that accept or return block numbers.

### 4.2 relativeTimeDelta: NEW field

**Purpose:** Records the number of seconds elapsed since the previous observation was
written. This enables time-weighted average growth rate calculations without requiring
an external timestamp oracle. A uint16 supports up to 65,535 seconds (approximately
18.2 hours), which is more than sufficient for the expected observation cadence.

**Overflow semantics:** If the actual time delta exceeds uint16 max, the `SafeCastLib.toUint16()`
call in the constructor will revert. This is the correct behavior: an observation gap
exceeding 18 hours indicates a liveness failure in the keeper network that should be
surfaced rather than silently truncated.

### 4.3 cumulativeGrowth: Unchanged

The cumulativeGrowth field retains its uint208 width and its bit offset of 48.
The offset is preserved because 32 (blockNumber) + 16 (relativeTimeDelta) = 48,
which equals the V1 offset of 48 (from the former 48-bit blockNumber). This means
the `CUMULATIVE_GROWTH_MASK` and the shift constant (48) are identical between V1 and V2.

### 4.4 SafeCast Changes

| V1 | V2 |
|---|---|
| `SafeCastLib.toUint48(_blockNumber)` | `SafeCastLib.toUint32(_blockNumber)` |
| -- | `SafeCastLib.toUint16(_relativeTimeDelta)` |
| `SafeCastLib.toUint208(_cumulativeGrowth)` | `SafeCastLib.toUint208(_cumulativeGrowth)` (unchanged) |

### 4.5 Error Type Update

The `StaleObservation` error must be updated:

```
// V1
error StaleObservation(uint48 observedBlock, uint48 currentBlock);

// V2
error StaleObservation(uint32 observedBlock, uint32 currentBlock);
```

---

## Section 5: Breaking Changes and Downstream Impact

### 5.1 BlockNumberAwareGrowthObserverLib.sol

**File:** `contracts/src/libraries/BlockNumberAwareGrowthObserverLib.sol`

This is the primary consumer of `GrowthObservation`. The following changes are required:

| Location | Current (V1) | Required (V2) | Lines affected |
|---|---|---|---|
| `record()` | casts `_blockNumber` to `uint48` for comparison | Must cast to `uint32` | Line 39 |
| `record()` | calls `newGrowthObservation(_blockNumber, _cumulativeGrowth)` | Must call `newGrowthObservation(_blockNumber, _relativeTimeDelta, _cumulativeGrowth)` -- requires a new `_relativeTimeDelta` parameter or computation | Line 41 |
| `observeAt()` | accepts `uint48 targetBlock` | Must accept `uint32 targetBlock` | Line 78 |
| `observeGrowthDelta()` | accepts `uint48 startBlock, uint48 endBlock` | Must accept `uint32 startBlock, uint32 endBlock` | Lines 113-114 |
| `ObservationExpired` error | uses `uint48, uint48` | Must use `uint32, uint32` | Line 10 |
| `latestObservation()` | returns `GrowthObservation` (unchanged) | No change needed | -- |
| `oldestObservation()` | returns `GrowthObservation` (unchanged) | No change needed | -- |

**Design decision for `record()`:** The `record()` function must either:
- (a) Accept `_relativeTimeDelta` as an additional parameter (caller-computed), or
- (b) Compute it internally by reading the latest observation's blockNumber and using a block-to-time conversion.

This design choice is outside the scope of this type-level specification and will be
resolved in the `BlockNumberAwareGrowthObserverLib` specification.

### 5.2 AngstromAdapter / Periphery Contracts

Any periphery contract that calls `BlockNumberAwareGrowthObserverLib.observeAt()` or
`observeGrowthDelta()` with uint48 block parameters must be updated to uint32.
A search of the current codebase shows that `GrowthObservation` is not directly
imported or referenced outside of `GrowthObservation.sol` and
`BlockNumberAwareGrowthObserverLib.sol` in the `src/` tree.

### 5.3 Test Files

No existing test files currently reference `GrowthObservation` directly (confirmed via
codebase search). New tests will be written as part of EVM-TDD Phase 2 (BUILD) based
on the BTT trees in Section 1 and the algebraic properties in Section 2.

### 5.4 AccrualManagerMod.sol

A search of `contracts/src/modules/AccrualManagerMod.sol` confirms it does NOT directly
reference `GrowthObservation` or `uint48` block numbers. No changes required in this file
for the V2 migration.

### 5.5 Summary of All Required File Changes

| File | Change Type | Severity |
|---|---|---|
| `src/types/GrowthObservation.sol` | Major rewrite (new field, new masks, new types) | High |
| `src/libraries/BlockNumberAwareGrowthObserverLib.sol` | Signature changes + new param for `record()` | High |
| `test/` (new files) | New BTT test suite | Medium |

---

## Appendix A: Design Rationale for uint32 blockNumber

Ethereum mainnet is currently at block ~22 million (as of April 2026). A uint32 supports
up to ~4.3 billion blocks. At 12 seconds per block, this provides coverage for approximately:

```
4,294,967,295 blocks * 12 seconds / (365.25 * 24 * 3600) = ~1,633 years
```

This exceeds any reasonable contract deployment horizon. The freed 16 bits are better
utilized for the `relativeTimeDelta` field, which enables time-weighted computations
that were previously impossible without an external timestamp oracle.

## Appendix B: Design Rationale for uint16 relativeTimeDelta

The `relativeTimeDelta` field stores the number of seconds between consecutive observations.
A uint16 supports up to 65,535 seconds, which equals approximately 18 hours and 12 minutes.

For the Angstrom keeper network, observations are expected to be recorded at least once
per epoch (typically every few minutes to every hour). An 18-hour maximum gap provides
substantial headroom while still catching keeper liveness failures via a revert on overflow.

If a future protocol upgrade requires longer observation gaps, the field could be
reinterpreted as a larger unit (e.g., minutes instead of seconds), but this is not
anticipated for the current design.

## Appendix C: Fuzz Input Ranges for Property Tests

When implementing the algebraic properties from Section 2 as fuzz tests, use the
following bounded input ranges:

| Field | Fuzz Type | Min | Max |
|---|---|---|---|
| blockNumber | uint256 (bounded) | 0 | `2^32 - 1` |
| relativeTimeDelta | uint256 (bounded) | 0 | `2^16 - 1` |
| cumulativeGrowth | uint256 (bounded) | 0 | `2^208 - 1` |

For the overflow tests (constructor revert branches), use:

| Field | Fuzz Type | Min | Max |
|---|---|---|---|
| blockNumber (overflow) | uint256 (bounded) | `2^32` | `type(uint256).max` |
| relativeTimeDelta (overflow) | uint256 (bounded) | `2^16` | `type(uint256).max` |
| cumulativeGrowth (overflow) | uint256 (bounded) | `2^208` | `type(uint256).max` |
