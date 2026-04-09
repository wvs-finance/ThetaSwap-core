# Code Review: GrowthObservation V2 + BlockNumberAwareGrowthObserverLib

**Date:** 2026-04-09
**Reviewer:** Claude (Code Review Agent)
**Status:** ALL CHECKS PASS

---

## GrowthObservation.sol

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | V2 bit layout: uint32 (0-31), uint16 (32-47), uint208 (48-255) | PASS | Masks: `(1<<32)-1`, `(1<<16)-1`, `(1<<208)-1`. Packing: `uint32(bn) \| (uint16(rtd)<<32) \| (uint208(cg)<<48)`. Matches spec Section 3. |
| 2 | Constructor: 3 uint256 args, SafeCastLib.toUint32/toUint16/toUint208 | PASS | Lines 39-51. All three safe-casts present. Matches spec Section 1.1 + Section 4.4. |
| 3 | Accessors isolate fields without cross-contamination | PASS | `blockNumber`: mask low 32. `relativeTimeDelta`: shift 32, mask 16. `cumulativeGrowth`: shift 48, mask 208. No overlap possible. |

## BlockNumberAwareGrowthObserverLib.sol

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 4 | `record()` takes 3 value params + uint32 monotonicity comparison | PASS | Signature: `(buffer, uint256, uint256, uint256)`. Comparison: `latest.blockNumber() >= uint32(_blockNumber)`. |
| 5 | `observeAt()` uses `uint32 targetBlock` | PASS | Line 78. |
| 6 | `ObservationExpired` error uses `uint32, uint32` | PASS | Line 10. |
| 7 | `observeGrowthDelta` is REMOVED | PASS | Function absent from file. Matches spec Section 2. |
| 8a | Binary search: count==1 | PASS | Handled entirely by early returns (newest check + oldest==newest triggers ObservationExpired). Search unreachable. |
| 8b | Binary search: count==2 | PASS | low=1, high=1. Loop `while(low<high)` is false. Returns `last(buffer,1)` = oldest. Correct. |
| 8c | Binary search: exact match | PASS | Condition `obs.blockNumber() > targetBlock` steers to `high=mid` on match, converging to exact index. |
| 8d | Binary search: floor match | PASS | Finds smallest recency index where blockNumber <= targetBlock. Correct floor semantics. |
| 9 | All signatures match spec Section 10 | PASS | `record`, `observeAt`, `latestObservation`, `oldestObservation`, `observationCount` -- all free functions, correct mutability, params, and return types. |

---

## Summary

Both files are correct against their BTT specifications. No deviations found.
