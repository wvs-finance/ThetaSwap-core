# Security Re-Audit: GrowthObservation + BlockNumberAwareGrowthObserverLib (v2)

**Auditor**: Blockchain Security Auditor
**Date**: 2026-04-09
**Scope**: Post-fix verification of H-01, H-02, H-03 + new code review
**Files**:
- `src/libraries/BlockNumberAwareGrowthObserverLib.sol`
- `src/types/GrowthObservation.sol`

---

## Prior Finding Verification

### H-02: No block monotonicity enforcement

**Status: RESOLVED**

The guard on line 39 of `BlockNumberAwareGrowthObserverLib.sol` now reads:

```solidity
if (latest.blockNumber() >= uint48(_blockNumber)) return;
```

This correctly rejects same-block and stale-block observations. Only strictly increasing block numbers are recorded. The NatSpec on lines 16-28 documents the design rationale including the M-01 same-block skip-vs-overwrite decision. No remaining issue.

### H-03: Unchecked subtraction in growthDelta / elapsedBlocks

**Status: RESOLVED (documented, accepted risk)**

Both `growthDelta()` (line 74-78) and `elapsedBlocks()` (line 85-89) remain `unchecked`. The `@custom:safety` NatSpec on each function clearly documents:

1. The precondition callers must satisfy (`later >= earlier`)
2. The consequence of violation (wraparound, not revert)
3. Why the invariant holds in practice (ring buffer monotonicity + `startBlock < endBlock` guard in `observeGrowthDelta`)

The public entry point `observeGrowthDelta()` (line 110-119) enforces `startBlock < endBlock` and retrieves observations via `observeAt()`, which respects the ring buffer's descending order. This chain of guarantees is sound. No remaining issue.

### H-01: uint208 SafeCast overflow concern

**Status: RESOLVED (documented, accepted risk)**

The `@custom:safety` NatSpec on `newGrowthObservation()` (lines 31-40) provides a quantitative analysis: 80 integer bits supports ~1.2M tokens per unit of liquidity before overflow, and SafeCastLib.toUint208() will hard-revert on overflow rather than silently wrapping. The analysis is mathematically correct (208 - 128 fractional bits = 80 integer bits, 2^80 / 1e18 ~ 1.2e6). No remaining issue.

---

## New Code Review

### Convenience Functions (latestObservation, oldestObservation, observationCount)

**latestObservation** (lines 48-53): SAFE. Checks `count == 0` and reverts with `EmptyBuffer()`. Then calls `CircularBuffer.last(buffer, 0)` which is valid when count > 0. No issue.

**oldestObservation** (lines 57-63): SAFE. Checks `count == 0` and reverts. Uses `CircularBuffer.last(buffer, total - 1)` where `total >= 1`, so `total - 1` is a valid index (the OZ `last()` function accepts indices 0..count-1). No underflow, no OOB. No issue.

**observationCount** (lines 66-69): SAFE. Pure delegation to `CircularBuffer.count()`. No issue.

### Comparison Operators (gte, lt, blockNumberGte, blockNumberLt)

All four functions (lines 97-122 of GrowthObservation.sol) are pure comparisons on uint48 values extracted via `blockNumber()`. The `unchecked` blocks contain no arithmetic -- only comparisons (`>=`, `<`), which cannot overflow or underflow. SAFE. No issue.

### isZero (line 92-94)

Pure equality check against `bytes32(0)`. SAFE. No issue.

---

## New Attack Vector Assessment

**Checked for**:

1. **Ring buffer wraparound corruption**: When the circular buffer is full and overwrites old entries, `oldestObservation()` returns `last(buffer, total-1)`. Since OZ `count()` returns `min(_count, _data.length)`, this correctly tracks the actual oldest surviving entry. No issue.

2. **observeAt binary search correctness**: The binary search (lines 90-105) finds the smallest index `i` where `blockNumber <= targetBlock`. The pre-checks handle the newest and oldest boundary cases. The search range `[1, total-1]` is correct because index 0 (newest) is already handled. When `low == high`, the result is valid. No off-by-one. No issue.

3. **observeGrowthDelta ordering assumption**: `startBlock < endBlock` (line 115) combined with the ring buffer's monotonic block numbers guarantees that `observeAt(startBlock)` returns an observation with `cumulativeGrowth <= observeAt(endBlock).cumulativeGrowth`, assuming the Angstrom accumulator is monotonically non-decreasing. This assumption is documented and reasonable for a reward accumulator. No issue.

4. **Frontrunning / access control**: The `record()` function is a free function with no access control -- it relies on the caller (adapter contract) to gate access. This is noted in the NatSpec (line 24-28: "access-controlled to a trusted keeper"). Not a vulnerability in these files, but the calling contract must enforce this. Informational only.

---

## Summary

| Finding | Status | Verdict |
|---------|--------|---------|
| H-02: Block monotonicity | Fixed (`>=` guard) | PASS |
| H-03: Unchecked subtraction | Documented via @custom:safety | PASS |
| H-01: uint208 overflow | Documented via @custom:safety | PASS |
| NEW: Convenience functions | Reviewed | PASS - no issues |
| NEW: Comparison operators | Reviewed | PASS - no issues |
| NEW: Attack vectors | Assessed | PASS - no new vectors |

**Overall verdict**: All prior findings are resolved. No new vulnerabilities introduced by the fixes or new code. The codebase is clean for these two files.
