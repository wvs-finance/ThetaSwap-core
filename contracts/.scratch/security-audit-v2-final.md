# Security Audit: GrowthObservation V2 + BlockNumberAwareGrowthObserverLib

**Auditor:** Blockchain Security Auditor
**Date:** 2026-04-09
**Commit:** thetaswap-patches (working tree)
**Scope:** `src/types/GrowthObservation.sol`, `src/libraries/BlockNumberAwareGrowthObserverLib.sol`

---

## Executive Summary

2 files, ~148 SLOC. 0 Critical, 1 High, 1 Medium, 2 Low, 2 Informational.

| Severity      | Count |
|---------------|-------|
| Critical      | 0     |
| High          | 1     |
| Medium        | 1     |
| Low           | 2     |
| Informational | 2     |

---

## Findings

### [H-01] Silent truncation in `record()` monotonicity guard bypasses SafeCast

**Severity:** High
**File:** `BlockNumberAwareGrowthObserverLib.sol#L37`

**Description:**
The monotonicity guard compares `latest.blockNumber()` (uint32) against `uint32(_blockNumber)`.
If `_blockNumber` is a uint256 value exceeding `type(uint32).max`, the Solidity `uint32()` cast
silently truncates the upper bits. This means the guard can evaluate incorrectly, potentially
skipping a record that should have been pushed, or pushing when it should have skipped.

However, on the **push path** (line 41), the value flows into `newGrowthObservation()` which
calls `SafeCastLib.toUint32(_blockNumber)` and reverts on overflow. So the truncation on the
guard cannot lead to a corrupted observation being stored.

**The real exploit scenario:** If `_blockNumber` is, say, `2^32 + 5` and the latest observation
has blockNumber `10`, then `uint32(2^32 + 5) = 5`, and `10 >= 5` is true, so the guard skips.
The observation that should have been recorded (at a higher block) is silently dropped. The
SafeCast on the push path never fires because the skip prevents reaching it. **Valid observations
are silently lost.**

Conversely, if the latest blockNumber is `4` and `_blockNumber` is `2^32 + 5`, the truncated
comparison `4 >= 5` is false, so it proceeds to push, where SafeCast correctly reverts. This
path is safe.

The dangerous path is the skip: a caller passing `block.number` when `block.number > 2^32`
(~year 3659) would have every observation silently dropped once the truncated value wraps below
the latest stored blockNumber. This creates a permanent liveness failure with no revert or log.

**Impact:** After Ethereum block `2^32` (~year 3659), the observation system silently stops
recording. While distant, the fix is trivial and eliminates the class of bug entirely.

**Recommendation:**
Replace the truncating cast with `SafeCastLib.toUint32()`:

```solidity
if (latest.blockNumber() >= SafeCastLib.toUint32(_blockNumber)) return;
```

Or, more gas-efficient since the push path already SafeCasts:

```solidity
if (_blockNumber > type(uint32).max) {
    // blockNumber doesn't fit -- push path will SafeCast anyway, so let it through
    // (it will revert in newGrowthObservation). Or revert here explicitly.
}
if (latest.blockNumber() >= uint32(_blockNumber)) return;
```

The cleanest fix: just use SafeCast on the guard. The gas overhead of one extra SafeCast
on the skip path is negligible.

---

### [M-01] relativeTimeDelta uint16 overflow reverts halt observation recording

**Severity:** Medium
**File:** `GrowthObservation.sol#L47` (via `newGrowthObservation`)

**Description:**
If the keeper network experiences a gap exceeding 65,535 seconds (~18.2 hours), the
`SafeCastLib.toUint16(_relativeTimeDelta)` call reverts. This is by design per the spec
("surfaces keeper liveness failures"). However, the revert **blocks all future observations**
until the keeper is restarted with a corrected `_relativeTimeDelta` value or until a new
observation is recorded with a smaller delta.

This means a single keeper outage > 18.2 hours creates a situation where:
1. The next `record()` call reverts.
2. The caller must implement fallback logic (e.g., capping at `type(uint16).max`).
3. If the caller does not handle this, the observation system is bricked until manual intervention.

**Impact:** Temporary denial of service for observation recording after extended keeper downtime.
The adapter contract calling `record()` must handle this gracefully.

**Recommendation:** This is acknowledged as intentional per the spec. Ensure the adapter-level
caller either:
- Caps `_relativeTimeDelta` at `type(uint16).max` before calling `record()`, or
- Has explicit error handling for the revert, with alerting/fallback logic.

Document this requirement prominently in the adapter contract's NatSpec.

**Status:** PASS (intentional design) -- but the caller contract MUST handle the revert.

---

### [L-01] Unchecked arithmetic in `growthDelta` and `elapsedBlocks` wraps on misordering

**Severity:** Low
**File:** `GrowthObservation.sol#L79-L92`

**Description:**
Both functions use `unchecked` subtraction. If called with arguments in wrong order
(`earlier` has higher values than `later`), the result wraps modulo `2^208` or `2^32`
respectively, returning a silently incorrect value.

**Impact:** Low -- the spec explicitly documents this as a caller responsibility, and the
ring buffer's monotonicity invariant guarantees correct ordering for observations retrieved
via `observeAt()`. The risk exists only for direct callers who bypass `observeAt()`.

**Recommendation:** PASS. The NatSpec documentation is clear. No code change needed.

---

### [L-02] `StaleObservation` error declared but never used

**Severity:** Low
**File:** `GrowthObservation.sol#L26`

**Description:**
The `StaleObservation(uint32, uint32)` error is declared in `GrowthObservation.sol` but is
never emitted anywhere in either audited file. The lib uses `ObservationExpired` instead
(declared in `BlockNumberAwareGrowthObserverLib.sol`).

**Impact:** Dead code. No security impact but creates confusion about which error type is
canonical for stale/expired observations.

**Recommendation:** Remove the unused `StaleObservation` error from `GrowthObservation.sol`,
or consolidate error declarations in one location.

---

### [I-01] Binary search: no new vectors from uint32 narrowing

**Severity:** Informational

**Analysis:** The binary search in `observeAt()` operates over recency indices (uint256),
not block numbers directly. The block number comparisons on line 84, 87, and 99 all use
`blockNumber()` which returns uint32, and `targetBlock` is already uint32. The narrowing
from uint48 to uint32 does not change the search algorithm's correctness or introduce any
new overflow/underflow vectors. The midpoint calculation `(low + high) / 2` has max value
`(1 + 255) / 2 = 128`, no overflow risk.

**Status:** PASS.

---

### [I-02] Bit-packing layout verification

**Severity:** Informational

**Analysis of all seven audit focus areas:**

**1. Bit-packing safety (field leakage):** PASS.
- blockNumber: bits [0,31]. Mask = `(1<<32)-1` = 0xFFFFFFFF. No shift on pack, masked on extract.
- relativeTimeDelta: bits [32,47]. Shifted left 32 on pack, shifted right 32 then masked with `(1<<16)-1` on extract.
- cumulativeGrowth: bits [48,255]. Shifted left 48 on pack, shifted right 48 then masked with `(1<<208)-1` on extract.
- Total: 32 + 16 + 208 = 256 bits. No overlap, no gap. Fields cannot leak into each other.

**2. SafeCast coverage:** PASS.
- `toUint32(_blockNumber)`: guards bits 0-31.
- `toUint16(_relativeTimeDelta)`: guards bits 32-47.
- `toUint208(_cumulativeGrowth)`: guards bits 48-255.
- All three downcasts are SafeCast-protected in `newGrowthObservation()`.

**3. uint32 blockNumber safety:** PASS (with H-01 caveat).
- uint32 max = 4,294,967,295 blocks. At 12s/block = ~1,633 years from genesis. Current block
  ~22M is 0.5% of capacity. Sufficient headroom. The SafeCast in the constructor catches overflow.
- The guard in `record()` has the truncation issue (H-01) but the storage path is safe.

**4. relativeTimeDelta overflow:** PASS (with M-01 caveat).
- uint16 max = 65,535 seconds = ~18.2 hours. Revert on overflow is intentional per spec.
- See M-01 for operational implications.

**5. Binary search vectors:** PASS. See I-01 above.

**6. Unchecked arithmetic wrapping (uint32 vs uint48):** PASS.
- `elapsedBlocks` now wraps at 2^32 instead of 2^48. This is a smaller modulus, but since
  block numbers in the buffer are guaranteed monotonically increasing (by `record()`'s guard),
  the subtraction `later - earlier` is always non-negative for properly ordered observations.
  The wrapping only occurs on caller misuse, which is documented.

**7. Monotonicity guard truncation:** See H-01. The `uint32(_blockNumber)` cast in `record()`
   line 37 silently truncates. SafeCast is only on the push path (line 41), not the skip path.

---

## Summary

| ID   | Title                                              | Severity      | Status         |
|------|----------------------------------------------------|---------------|----------------|
| H-01 | Silent truncation in record() monotonicity guard   | High          | Open           |
| M-01 | relativeTimeDelta overflow halts recording          | Medium        | Acknowledged   |
| L-01 | Unchecked arithmetic wraps on misordering           | Low           | Pass (by design) |
| L-02 | StaleObservation error declared but unused          | Low           | Open           |
| I-01 | Binary search unaffected by uint32 narrowing        | Informational | Pass           |
| I-02 | Bit-packing layout fully verified                   | Informational | Pass           |

**Recommendation:** Fix H-01 before deployment. It is a one-line change. The remaining findings
are either by-design or cosmetic.
