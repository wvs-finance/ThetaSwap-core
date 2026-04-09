# Code Review: EMAGrowthTransformationLib vs BTT Spec

**File:** `contracts/src/libraries/transformations/EMAGrowthTransformationLib.sol`
**Spec:** `.scratch/ema-growth-transformation-lib-btt-spec.md`
**Date:** 2026-04-09

---

## Checkpoint Results

### 1. Function signature matches spec Section 2.1 -- PASS

Params: `(CircularBuffer.Bytes32CircularBuffer storage buffer, OraclePack currentOraclePack, uint96 EMAperiods, int24 clampDelta)`. Return: `OraclePack`. Mutability: `view`. All match. The spec code block omits `view` but the prose below it states "Mutability: view" explicitly.

### 2. Same-epoch fast path -- PASS

Line 45: `uint24 currentEpoch = uint24((block.timestamp >> 6) & 0xFFFFFF);`
Line 46: `if (currentEpoch == currentOraclePack.epoch()) return currentOraclePack;`
Matches spec epoch formula and short-circuit behavior exactly.

### 3. InsufficientObservations revert when count < 2 -- PASS

Line 49-50: `if (count < 2) revert InsufficientObservations();`
Matches spec Section 2.1 tree branch for single-observation case.

### 4. Correct observation reads -- PASS

Line 53: `GrowthObservation oldest = oldestObservation(buffer);`
Line 54: `GrowthObservation latest = latestObservation(buffer);`
Both match spec. Signatures verified against BlockNumberAwareGrowthObserverLib.sol.

### 5. growthToTick call order (latest first, oldest second) -- PASS

Line 57: `growthToTick(latest.cumulativeGrowth(), oldest.cumulativeGrowth())`
Matches spec: "growthToTick(latest.cumulativeGrowth(), oldest.cumulativeGrowth())".
Verified against GrowthToTickLib signature: `growthToTick(uint208 currentGrowth, uint208 anchorGrowth)`.

### 6. clampTick call signature -- PASS

Line 60: `OraclePackLibrary.clampTick(growthTick, currentOraclePack, clampDelta)`
Verified against OraclePack.sol line 511-514: `clampTick(int24 newTick, OraclePack _oraclePack, int24 clampDelta) -> int24`. Match.

### 7. timeDelta computation -- PASS

Line 63: `int256(uint256(uint24(currentEpoch - currentOraclePack.epoch()))) * 64`
Matches spec Section 4.3: `int256(uint256(uint24(currentEpoch - recordedEpoch))) * 64`.
The uint24 cast ensures wraparound safety (spec Section 6.5).

### 8. insertObservation call signature -- PASS

Line 66: `currentOraclePack.insertObservation(clampedTick, uint256(currentEpoch), timeDelta, EMAperiods)`
Verified against OraclePack.sol line 436-441: `insertObservation(OraclePack, int24, uint256, int256, uint96) -> OraclePack`. Match. Note: called as member function on `currentOraclePack` via `using ... global`, so the first `OraclePack` param is implicit.

### 9. No storage writes (view function) -- PASS

Function is declared `view`. No SSTORE operations. Returns updated OraclePack for caller to persist.

### 10. Free function pattern -- PASS

`updateGrowthEMA` is defined at file scope (lines 38-67), not inside a `library` or `contract` block.

---

## Spec-Internal Inconsistency (informational, not a code defect)

The BTT tree in Section 2.1 structures the branches as buffer-size checks first, then epoch check:

```
+-- given buffer empty -> revert
+-- given buffer has 1 obs -> revert
+-- given buffer has >= 2 obs
    +-- when same epoch -> return unchanged
```

But the **implementation** (and spec Sections 7 and 8.1) do epoch check **before** buffer check. Section 7 states: "The same-epoch short-circuit path has NO revert conditions (it returns immediately without reading the buffer)." Section 8.1 confirms: "no storage reads" on the fast path.

This means: if the epoch matches but the buffer has 0 or 1 observations, the implementation returns successfully (no revert), which contradicts the tree's implied ordering. The implementation behavior is correct and gas-optimal. The BTT tree should be restructured to nest the buffer-count branches under the "epoch differs" branch to match the actual execution order.

---

## Summary

**10/10 checkpoints pass.** One spec-internal inconsistency noted (tree ordering vs actual execution order) that does not affect the implementation's correctness.
