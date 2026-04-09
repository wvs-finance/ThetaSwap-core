# Gap Analysis: Oracle Implementation vs. Research Specifications

**Date:** 2026-04-09
**Scope:** Comparing implemented code against `time-weighted-oracle-patterns-research.md` (oracle spec) and `mean-reversion-validation.md` (statistical requirements)
**Status:** 6 gaps identified, 2 critical, 2 moderate, 2 low

---

## Files Under Analysis

| File | Role |
|------|------|
| `src/libraries/BlockNumberAwareGrowthObserverLib.sol` | Transformation-agnostic raw primitives: record, observeAt, latestObservation, oldestObservation, observationCount. observeGrowthDelta REMOVED (moved to Layer 2 transformation contracts). |
| `src/types/GrowthObservation.sol` | Implemented: bytes32 UDT packing (uint48 blockNumber, uint208 cumulativeGrowth) |
| `.scratch/time-weighted-oracle-patterns-research.md` | Spec: two-layer architecture (ring buffer + optional EMA) |
| `.scratch/mean-reversion-validation.md` | Spec: statistical requirements for option pricing underlying |

---

## 1. observeGrowthDelta vs. G(t) - G(t-W) Requirement

**Question:** Does `observeGrowthDelta(startBlock, endBlock)` correctly enable the rolling-window growth delta G(t) - G(t-W) required by Section 4.2 of mean-reversion-validation.md?

**Verdict: YES -- structurally correct for globalGrowth, but see Gap 3 for the missing half.**

The implementation at `BlockNumberAwareGrowthObserverLib.sol:67-76` does exactly what is needed for a single accumulator:

1. It calls `observeAt(buffer, startBlock)` which binary-searches for the observation at or before `startBlock`.
2. It calls `observeAt(buffer, endBlock)` for the end.
3. It returns `earlier.growthDelta(later)`, which is `later.cumulativeGrowth() - earlier.cumulativeGrowth()`.

This correctly computes `G(endBlock) - G(startBlock)`. When called with `endBlock = block.number` and `startBlock = block.number - W`, this gives `G(t) - G(t-W)`.

**One subtlety:** `observeAt` returns the observation "at or before" the target block. If no observation was recorded at exactly block `t-W`, it returns the most recent observation before it. This is correct behavior -- the cumulative growth does not change between observations (growth only increments when rewards are distributed), so the observation before `t-W` carries the correct cumulative value for `t-W`.

**Assessment: No gap on this specific point.**

---

## 2. Ring Buffer Cardinality vs. Required Lookback Windows

**Question:** Can a ring buffer with cardinality 8-256 serve queries for 1 hour (~300 blocks), 1 day (~7200 blocks), and 1 week (~50400 blocks)?

**Verdict: CRITICAL GAP.**

The OZ `CircularBuffer` is fixed-size, set at `setup()` time. The cardinality determines how many observations the buffer holds. Since the `record()` function writes at most one observation per block, the buffer holds at most `cardinality` blocks of history.

| Cardinality | Max History (blocks) | Max History (time @ 12s/block) | Serves 1h (300 blocks)? | Serves 1d (7200)? | Serves 1w (50400)? |
|-------------|---------------------|-------------------------------|--------------------------|--------------------|--------------------|
| 8           | 8                   | 96 seconds                    | NO                       | NO                 | NO                 |
| 256         | 256                 | ~51 minutes                   | NO                       | NO                 | NO                 |
| 65,535      | 65,535              | ~9.1 days                     | YES                      | YES                | YES                |

**Even at maximum cardinality of 256, the buffer cannot serve a 1-hour lookback** (300 blocks). This is a fundamental mismatch.

**However**, there is a saving grace that the spec itself hints at: observations are only recorded when rewards are distributed (once per Angstrom bundle). If bundles execute less frequently than every block, the effective history extends. For example:

- If bundles execute once every 12 blocks (~2.4 minutes): 256 slots covers ~3072 blocks (~10.2 hours). Serves 1h, but not 1d.
- If bundles execute once every 100 blocks (~20 minutes): 256 slots covers ~25,600 blocks (~3.6 days). Serves 1h and 1d, but not 1w.

**But the code records every block where `record()` is called**, with no epoch-level aggregation. If the caller invokes `record()` every block (as the Active Observer Pattern suggests -- "called after each bundle execution"), then 256 slots covers 256 blocks.

**Recommendations:**
1. Either increase the buffer to 65,535 (matching V3 Oracle's maximum, at a storage cost of ~1.4M gas to pre-warm).
2. Or record observations at epoch boundaries rather than every block, so each slot covers an epoch instead of a block.
3. Or use the "observation interval" pattern from the spec where the buffer only records when a minimum block gap has elapsed since the last observation.

---

## 3. Missing growthInside Observations

**Question:** Does the implementation track BOTH growthInside and globalGrowth as required for rho(t;W) = [I(t)-I(t-W)] / [G(t)-G(t-W)]?

**Verdict: CRITICAL GAP.**

The implemented `GrowthObservation` type stores a single `uint208 cumulativeGrowth` field. The `record()` function accepts a single `_cumulativeGrowth` parameter. The `observeGrowthDelta()` function returns a single `uint208` delta.

Section 4.2 of mean-reversion-validation.md requires computing:

```
rho(t; W) = [I(t) - I(t-W)] / [G(t) - G(t-W)]
```

where I(t) = growthInside(tL, tU, t) and G(t) = globalGrowth(t). This requires historical observations of BOTH accumulators.

The current implementation can track G(t) - G(t-W) but has NO mechanism for I(t) - I(t-W).

**Why this matters:** The entire mean-reversion analysis concludes that the rolling-window ratio rho(t;W) is the correct underlying for option pricing. Without growthInside observations, the system can only serve globalGrowth queries -- which is the denominator only.

**Complication:** growthInside is position-specific (depends on tick range [tL, tU]). Storing per-position observation buffers is expensive. There are two approaches:

1. **Store growthOutside observations per tick** (the components from which growthInside is derived). Then growthInside can be reconstructed at query time: `I(t) = G(t) - outsideBelow(tL, t) - outsideAbove(tU, t)`. This requires ring buffers for growthOutside at each active tick boundary.

2. **Compute growthInside at record time for each active NoteId** and store per-NoteId observation buffers. Simpler but requires knowing which NoteIds are active.

3. **Accept the limitation** and rely on the per-NoteId entry snapshots (`entryGrowthInside` / `entryGlobalGrowth` from AccrualManagerMod) for position-specific ratios, using the ring buffer only for globalGrowth rate queries. This means rho(t;W) with arbitrary W is not available -- only R_delta(t; t_entry) is computable.

**The spec itself (Section 10, "Implementation Skeleton") only shows globalGrowth observation recording**, so the spec and implementation are aligned on this point -- but both are incomplete relative to the statistical requirement in mean-reversion-validation.md Section 4.2.

---

## 4. Layer 2: Growth Rate EMA

**Question:** Is the "Layer 2: Growth Rate EMA" from the oracle spec implemented?

**Verdict: NOT IMPLEMENTED. Moderate priority.**

The oracle spec (Section 10, "Layer 2: Growth Rate EMA") recommends adapting the Panoptic OraclePack EMA machinery to track smoothed growth rates at 4 timescales (~10, ~100, ~900, ~7200 blocks). This would be stored in a single uint256 slot per pool.

There is no EMA implementation in the codebase. No imports from OraclePack, no EMA update logic, no smoothed rate storage.

**How critical is this?**

The EMA layer is described as "optional" in the spec. Its use cases are:
- Detecting anomalous reward spikes
- Computing expected epoch yields for note pricing
- Providing a "fair rate" for the theta swap CFMM

For V1/prototype purposes, this is not blocking. The ring buffer delta queries can serve the same purpose (compute average rate over a window) at higher gas cost (two SLOADs + binary search vs. one SLOAD for EMA).

For production pricing, the EMA becomes more valuable because:
- It provides O(1) read cost for smoothed rates
- It handles the "rate of change" question directly rather than requiring the caller to do delta/elapsed arithmetic
- It provides multiple timescales simultaneously

**Assessment: Moderate gap. Not blocking for V1, important for production pricing.**

---

## 5. averageGrowthRate Function

**Question:** Does `averageGrowthRate(startBlock, endBlock)` exist as specified in the oracle spec skeleton?

**Verdict: NOT IMPLEMENTED. Low priority.**

The oracle spec skeleton (Section 10) includes:

```solidity
function averageGrowthRate(
    PoolId poolId,
    uint48 startBlock,
    uint48 endBlock
) external view returns (uint256 rateQ128) {
    uint256 delta = this.observeGrowthDelta(poolId, startBlock, endBlock);
    uint48 blockDelta = endBlock - startBlock;
    rateQ128 = delta / blockDelta;
}
```

This function does not exist in `BlockNumberAwareGrowthObserverLib.sol`. The library provides `observeGrowthDelta` but not the rate derivation.

**How critical:** Low. This is a trivial wrapper -- any caller can compute `delta / blockDelta` themselves. It is a convenience function, not a structural gap. However, implementing it would complete the spec's API surface.

---

## 6. recordObservation Pattern: Spec vs. Implementation

**Question:** Are there gaps between the spec's `recordObservation` pattern and the implemented `record()` function?

**Verdict: MODERATE GAP -- per-pool keying is missing.**

**Spec pattern (Section 10):**
```solidity
mapping(PoolId => GrowthObservation[256]) public observations;
mapping(PoolId => uint16) public poolObservationIndex;

function recordObservation(PoolId poolId) external {
    uint256 currentGrowth = this.globalGrowth(poolId);
    ...
}
```

**Implementation pattern:**
```solidity
function record(
    CircularBuffer.Bytes32CircularBuffer storage buffer,
    uint256 _blockNumber,
    uint256 _cumulativeGrowth
) { ... }
```

Key differences:

| Aspect | Spec | Implementation | Gap? |
|--------|------|---------------|------|
| Per-pool keying | `mapping(PoolId => ...)` | Bare `CircularBuffer storage buffer` parameter | YES -- the library is pool-agnostic; the caller must manage per-pool mappings |
| Growth source | Reads from adapter via `this.globalGrowth(poolId)` | Accepts raw `_cumulativeGrowth` parameter | NO -- this is a reasonable design choice (separation of concerns) |
| Index tracking | Explicit `poolObservationIndex` mapping | Handled internally by `CircularBuffer._count` | NO -- OZ CircularBuffer manages this |
| Same-block skip | `if (last.blockNumber == bn) return` | `if (latest.blockNumber() == uint48(_blockNumber)) return` | NO -- equivalent logic |
| Cardinality management | `cardinality` / `cardinalityNext` / growable | Fixed at `setup()` time | MODERATE -- no dynamic growth capability |
| Access control | `external` with implicit permissioning | Free function, no access control | YES -- the library is a building block; access control must be added by the integrating contract |

**The per-pool keying gap is structural.** The spec envisions a contract with `mapping(PoolId => CircularBuffer)` where `recordObservation(poolId)` is a self-contained entry point. The implementation provides library functions that operate on a bare buffer reference. This means:

1. The integrating contract (presumably the adapter) must declare `mapping(PoolId => CircularBuffer.Bytes32CircularBuffer)` in its storage.
2. The integrating contract must implement the `recordObservation(PoolId)` entry point that reads `globalGrowth` via extsload and calls `record()`.
3. Access control (permissioning who can call `recordObservation`) must be implemented at the contract level.

None of this is wrong -- it is a library vs. contract design decision. But the integration layer does not yet exist.

**The dynamic cardinality gap is moderate.** The spec mentions "configurable cardinality (start at 8, growable to 256)" with a `grow()` pattern similar to V3 Oracle. The OZ CircularBuffer is fixed-size at `setup()` time. To change cardinality, you would need to deploy a new buffer and migrate observations, or implement a custom growth mechanism. This means the system cannot adapt to changing lookback requirements without redeployment or migration.

---

## Summary Table

| # | Gap | Severity | Blocking for V1? | Location |
|---|-----|----------|-------------------|----------|
| 1 | ~~observeGrowthDelta correctly computes G(t)-G(t-W)~~ | REDESIGNED | NO | observeGrowthDelta removed from library (now transformation-agnostic). Windowed delta is a Layer 2 transformation, selected per-instrument via extensionFlag. |
| 2 | ~~Ring buffer cardinality cannot serve lookback windows~~ | RESOLVED | NO | 256 slots guarantees 30-min epoch at Ethereum max throughput. Single-period RAN = 30 min. Empirical: ~2h at typical activity. |
| 3 | No growthInside observation tracking; only globalGrowth is observed | CRITICAL | Depends on product scope -- blocks rolling-window rho(t;W) | GrowthObservation.sol stores single accumulator |
| 4 | Growth Rate EMA (Layer 2) not implemented | MODERATE | No | Not present in codebase |
| 5 | averageGrowthRate convenience function not implemented | LOW | No | Trivial to add |
| 6 | Per-pool keying and integration contract not yet built; no dynamic cardinality growth | MODERATE | Partially -- library exists but integration harness does not | BlockNumberAwareGrowthObserverLib.sol is pool-agnostic |

---

## Recommendations

### Immediate (before any testing)

1. **Resolve the cardinality problem (Gap 2).** Choose one of:
   - (a) Record observations at a minimum interval (e.g., every 300 blocks = 1 hour), so 256 slots covers 256 hours (~10.7 days). This serves all three lookback windows.
   - (b) Increase buffer size to 8192+ slots, accepting the storage pre-warming cost.
   - (c) Use a two-tier approach: a small fast buffer (256 slots, every-block) for short lookbacks, and a sparse buffer (256 slots, every-hour) for long lookbacks.

2. **Build the integration contract (Gap 6).** The library functions exist but the per-pool mapping, entry point, extsload read, and access control wrapper do not.

### Before production pricing

3. **Address growthInside observation (Gap 3).** Either:
   - (a) Track growthOutside per tick boundary in separate ring buffers (expensive but general).
   - (b) Accept that rho(t;W) with arbitrary W is not available and rely on per-NoteId entry snapshots for position-specific ratios.
   - (c) For a limited set of "canonical" tick ranges, maintain dedicated growthInside ring buffers.

4. **Implement the EMA layer (Gap 4)** for O(1) smoothed rate queries used in note pricing.

### Low priority

5. **Add averageGrowthRate (Gap 5)** as a convenience wrapper.
