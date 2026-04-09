# EMAGrowthTransformationLib -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/libraries/transformations/EMAGrowthTransformationLib.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Depends on:**
- GrowthToTickLib BTT Spec (`growth-to-tick-lib-btt-spec.md`)
- GrowthObservation V2 BTT Spec (`growth-observation-v2-btt-spec.md`)
- BlockNumberAwareGrowthObserverLib BTT Spec (`growth-observer-lib-btt-spec.md`)

---

## Overview

EMAGrowthTransformationLib is the first Layer 2 transformation library in the observation
pipeline. It converts raw cumulative growth observations into EMA-smoothed tick values
by composing three primitives: the observation buffer (Layer 1), GrowthToTickLib (ratio
to tick conversion), and OraclePack (Panoptic's 256-bit packed oracle with 4 EMAs +
median).

This library maps to `extensionFlag = CALLABLE (4)` in the NoteId bit-packing scheme.
Selecting this transformation when constructing a NoteId creates a CALLABLE Range Accrual
Note whose coupon accrual is gated by EMA-smoothed growth ticks. Other extensionFlag
values (VANILLA, ACCRUAL_DECRUAL, TARN, BARRIERS, BASKET_UNDERLIER, FLOATING_COUPON)
use different transformation libraries, but all consume the same underlying observation
buffer.

### Pattern

Free functions (not inside a `library` block), consistent with all other ThetaSwap
libraries and types.

### Architecture Layer Diagram

```
                              Storage
                                |
                                v
Layer 1:  BlockNumberAwareGrowthObserverLib
          (CircularBuffer of GrowthObservation V2)
                |                          |
                v                          v
          latestObservation()      oldestObservation()
                |                          |
                +--- .cumulativeGrowth() --+
                           |
                           v
Bridge:   GrowthToTickLib.growthToTick(latestCG, oldestCG)
          (Q128.128 ratio -> sqrtPriceX96 -> int24 tick)
                           |
                           v
                     int24 growthTick
                           |
                     [clampTick]
                           |
                           v
Layer 2:  OraclePack.insertObservation(oraclePack, clampedTick, epoch, timeDelta, EMAperiods)
          (feeds tick into 8-slot median queue + 4 cascading EMAs)
                           |
                           v
                   OraclePack (updated)
                           |
              +----+----+----+----+----+
              |    |    |    |    |    |
              v    v    v    v    v    v
          spotEMA fastEMA slowEMA eonsEMA medianTick epoch
          (callers read these directly from the returned OraclePack)
```

### Dependencies

| Dependency | Source | Functions Used |
|---|---|---|
| `CircularBuffer` | `openzeppelin-contracts/utils/structs/CircularBuffer.sol` | `count()`, storage type |
| `GrowthObservation` | `../types/GrowthObservation.sol` | `cumulativeGrowth()`, `blockNumber()`, `relativeTimeDelta()` |
| `BlockNumberAwareGrowthObserverLib` | `./BlockNumberAwareGrowthObserverLib.sol` | `latestObservation()`, `oldestObservation()`, `observationCount()` |
| `GrowthToTickLib` | `./GrowthToTickLib.sol` | `growthToTick(uint208, uint208) -> int24` |
| `OraclePack` / `OraclePackLibrary` | Panoptic `contracts/types/OraclePack.sol` | `insertObservation()`, `clampTick()`, `epoch()`, `computeInternalMedian()` |

---

## Section 1: Design Decisions

### 1.1 Anchor Selection: Oldest Observation in Buffer

The anchor for GrowthToTickLib is always the **oldest observation currently in the buffer**
(`oldestObservation(buffer).cumulativeGrowth()`), NOT a fixed snapshot or a rolling
window endpoint.

**Rationale:**
- **Self-correcting:** As new observations push out old ones, the anchor naturally advances.
  No keeper or governance action is needed to update it.
- **Bounded tick values:** The maximum tick is bounded by the buffer depth (capacity)
  multiplied by the maximum per-observation growth rate. With 256 observations at ~12-second
  intervals, the window covers approximately 50 minutes, limiting the growth ratio to a
  practically bounded range.
- **No extra storage:** The anchor is implicitly defined by the buffer state -- no
  additional storage slot is needed for an anchor snapshot.

**Tradeoff:** The anchor drifts as the buffer wraps. This means the same absolute growth
level produces different ticks at different times, depending on what the oldest observation
happens to be. This is acceptable for EMA-smoothed coupon gating because the EMAs track
the relative trend, not the absolute level.

### 1.2 Read Responsibilities

This library does NOT re-export OraclePack read functions. Callers that need EMA values
read them directly from the returned OraclePack:

```
oraclePack.spotEMA()    -- int24, shortest timescale
oraclePack.fastEMA()    -- int24, second shortest
oraclePack.slowEMA()    -- int24, second longest
oraclePack.eonsEMA()    -- int24, longest timescale
getMedianTick(oraclePack) -- int24, median of 8 observations
```

### 1.3 Epoch Semantics

OraclePack uses 64-second epochs for timekeeping:

```
currentEpoch = (block.timestamp >> 6) & 0xFFFFFF
```

This means:
- Epoch 0 covers timestamps [0, 63]
- Epoch 1 covers timestamps [64, 127]
- Each epoch is exactly 64 seconds
- The 24-bit epoch counter wraps after 2^24 * 64 seconds ~= 34.1 years

Updates are skipped when the current epoch matches the OraclePack's recorded epoch.
This ensures at most one OraclePack update per 64-second window, regardless of how
many times `updateGrowthEMA` is called.

### 1.4 Clamp Delta for Manipulation Resistance

The `clampDelta` parameter limits the maximum tick change per update. This is passed
through to `OraclePackLibrary.clampTick()`, which bounds the new tick to be within
`+/- clampDelta` of the OraclePack's last recorded tick:

```
clampedTick = clampTick(growthTick, oraclePack, clampDelta)
```

This prevents a single large growth observation (whether from legitimate volatility or
manipulation) from drastically shifting the OraclePack's median or EMAs.

### 1.5 EMA Period Configuration

The `EMAperiods` parameter is a packed uint96 containing four uint24 period values:

```
Bits [0,23]:   spotEMA period  (shortest timescale)
Bits [24,47]:  fastEMA period  (second shortest)
Bits [48,71]:  slowEMA period  (second longest)
Bits [72,95]:  eonsEMA period  (longest timescale)
```

These are passed directly to `OraclePackLibrary.updateEMAs()`. The cascading time delta
cap inside `updateEMAs` ensures that after long periods of inactivity, EMAs converge at
most 75% toward the new tick value (linear approximation of exponential decay).

---

## Section 2: BTT Behavior Tree

### 2.1 updateGrowthEMA

**Signature:**

```
function updateGrowthEMA(
    CircularBuffer.Bytes32CircularBuffer storage buffer,
    OraclePack currentOraclePack,
    uint96 EMAperiods,
    int24 clampDelta
) returns (OraclePack)
```

**Mutability:** view (reads storage for buffer observations, reads block.timestamp for
epoch computation; does NOT write to storage -- the caller is responsible for persisting
the returned OraclePack)

```
EMAGrowthTransformationLib::updateGrowthEMA
|
+-- given the observation buffer is empty (observationCount == 0)
|   +-- it should revert with EmptyBuffer
|       (propagated from oldestObservation or latestObservation).
|
+-- given the observation buffer has exactly one observation
|   +-- it should revert.
|   +-- Rationale: GrowthToTickLib requires two distinct observations
|       to compute a ratio. With only one observation, the oldest and
|       latest are identical, producing ratio = 1 and tick = 0 perpetually.
|       However, this degenerate case is explicitly rejected because
|       a single observation provides no information about growth rate.
|       The revert may be a dedicated error (InsufficientObservations)
|       or propagated from a precondition check.
|
+-- given the observation buffer has at least two observations
    |
    +-- when the current epoch equals the OraclePack epoch
    |   +-- it should return currentOraclePack unchanged (no-op).
    |   +-- it should NOT call GrowthToTickLib (gas optimization).
    |   +-- it should NOT call OraclePack.insertObservation.
    |
    +-- when the current epoch is newer than the OraclePack epoch
        |
        +-- it should read the oldest observation from the buffer
        |   (via oldestObservation).
        |
        +-- it should read the latest observation from the buffer
        |   (via latestObservation).
        |
        +-- it should compute the growth tick:
        |   growthTick = growthToTick(
        |       latest.cumulativeGrowth(),
        |       oldest.cumulativeGrowth()
        |   )
        |
        +-- it should clamp the growth tick:
        |   clampedTick = clampTick(growthTick, currentOraclePack, clampDelta)
        |
        +-- it should compute the epoch and time delta:
        |   currentEpoch = (block.timestamp >> 6) & 0xFFFFFF
        |   timeDelta = (currentEpoch - oraclePack.epoch()) * 64
        |
        +-- it should call OraclePack.insertObservation:
        |   newOraclePack = insertObservation(
        |       currentOraclePack,
        |       clampedTick,
        |       currentEpoch,
        |       timeDelta,
        |       EMAperiods
        |   )
        |
        +-- it should return the updated OraclePack with:
            +-- refreshed spotEMA, fastEMA, slowEMA, eonsEMA.
            +-- updated median (new tick inserted into 8-slot queue).
            +-- updated epoch (set to currentEpoch).
```

---

## Section 3: Algebraic Properties (Invariants for Fuzz Testing)

### Property 1: Idempotence Within Epoch

For any buffer state and OraclePack where the current block.timestamp falls within
the same 64-second epoch as `currentOraclePack.epoch()`:

```
updateGrowthEMA(buffer, oraclePack, periods, clamp) == oraclePack
```

Calling updateGrowthEMA multiple times within the same epoch returns the identical
OraclePack. No bits change. This follows from the epoch check short-circuit.

**Test approach:** Call updateGrowthEMA twice in the same block (or within 63 seconds
of each other); assert that the returned OraclePack values are bitwise identical.

### Property 2: Monotonicity of Growth Tick

If the buffer accumulates more growth between consecutive updateGrowthEMA calls
(i.e., the latest observation's cumulativeGrowth increases while the oldest observation
remains the same or its cumulativeGrowth is less than the new oldest), then the growth
tick input to OraclePack is higher or equal:

```
growthTick_t2 >= growthTick_t1
```

provided that the oldest observation's cumulativeGrowth at time t2 is less than or equal
to the oldest at time t1 (which holds when the buffer has not wrapped and pushed out
the original anchor).

This is a consequence of GrowthToTickLib's monotonicity property.

### Property 3: Boundedness by Buffer Depth

The growth tick is bounded by the buffer's depth: the ratio is between the newest and
oldest observations, which span at most `capacity` observations. If each observation
adds at most `maxGrowthPerObservation` to the cumulative growth, then:

```
ratio <= (oldest.cumulativeGrowth() + capacity * maxGrowthPerObservation) / oldest.cumulativeGrowth()
```

In practice, with 256 slots and ~12-second observation cadence, the window is approximately
50 minutes. The growth rate of Uniswap V4 fee accumulators over 50 minutes is bounded,
producing ticks well within the TickMath range.

This property should be verified via bounded fuzz testing with realistic growth rates.

### Property 4: EMA Convergence

After N consecutive updates (each in a new epoch) with a stable growth rate (constant
growth tick), all four EMAs converge toward the growth tick value:

```
|oraclePack.spotEMA() - growthTick| < epsilon_spot   (smallest epsilon)
|oraclePack.fastEMA() - growthTick| < epsilon_fast
|oraclePack.slowEMA() - growthTick| < epsilon_slow
|oraclePack.eonsEMA() - growthTick| < epsilon_eons   (largest epsilon)
```

where `epsilon_X` decreases as N increases, and:

```
epsilon_spot < epsilon_fast < epsilon_slow < epsilon_eons
```

because shorter-period EMAs converge faster.

**Test approach:** Initialize an OraclePack with all EMAs at 0. Run 100+ updates with a
constant growth tick of, say, 6931 (ratio ~= 2). Assert that spotEMA converges first,
followed by fastEMA, slowEMA, and eonsEMA, with each within some tolerance of 6931.

### Property 5: Clamp Effectiveness

For any update where `|growthTick - oraclePack.lastTick()| > clampDelta`:

```
|clampedTick - oraclePack.lastTick()| == clampDelta
```

and:

```
sign(clampedTick - oraclePack.lastTick()) == sign(growthTick - oraclePack.lastTick())
```

The clamp limits the magnitude of the tick change without altering its direction.

### Property 6: Epoch Advancement

After a successful update (non-same-epoch case):

```
returnedOraclePack.epoch() == (block.timestamp >> 6) & 0xFFFFFF
```

The returned OraclePack's epoch always reflects the current block's epoch.

---

## Section 4: Integration with OraclePack

### 4.1 Functions Called

EMAGrowthTransformationLib calls exactly two OraclePackLibrary functions:

**`OraclePackLibrary.clampTick(int24 newTick, OraclePack oraclePack, int24 clampDelta) -> int24`**

Bounds `newTick` to be within `+/- clampDelta` of `oraclePack.lastTick()`. The last
tick is computed as `referenceTick + residualTick(0)`, representing the most recent
observation stored in the OraclePack's 8-slot queue.

**`OraclePackLibrary.insertObservation(OraclePack, int24, uint256, int256, uint96) -> OraclePack`**

Inserts a new tick observation into the OraclePack:
1. Computes residual = newTick - referenceTick
2. If residual exceeds the 12-bit threshold (+/- 2047), rebases the OraclePack
3. Inserts the new residual into slot 0, shifting existing residuals
4. Updates the 24-bit order map to maintain sorted order
5. Calls `updateEMAs` with the timeDelta and EMAperiods
6. Returns the new packed OraclePack

### 4.2 Functions NOT Called (Caller Responsibility)

The following OraclePack read functions are NOT called by this library but are available
to callers who hold the returned OraclePack:

| Function | Returns | Description |
|---|---|---|
| `spotEMA(OraclePack)` | int24 | Shortest-timescale EMA |
| `fastEMA(OraclePack)` | int24 | Second shortest EMA |
| `slowEMA(OraclePack)` | int24 | Second longest EMA |
| `eonsEMA(OraclePack)` | int24 | Longest-timescale EMA |
| `getEMAs(OraclePack)` | (int24, int24, int24, int24, int24) | All 4 EMAs + median |
| `getMedianTick(OraclePack)` | int24 | Median of 8 observations |
| `lastTick(OraclePack)` | int24 | Most recent observation tick |
| `epoch(OraclePack)` | uint24 | Last update epoch |
| `lockMode(OraclePack)` | uint8 | Safe mode override (0=off, 3=on) |

### 4.3 OraclePack Epoch Alignment

OraclePack's native timekeeping uses 64-second epochs:

```
epoch = (block.timestamp >> 6) & 0xFFFFFF
```

This library computes the epoch identically and compares it against `currentOraclePack.epoch()`
to determine whether an update should proceed. The time delta passed to `insertObservation`
is:

```
timeDelta = int256(uint256(uint24(currentEpoch - recordedEpoch))) * 64
```

This matches the pattern used in `OraclePackLibrary.computeInternalMedian()` (line 553
of OraclePack.sol), ensuring consistent timekeeping between Panoptic's native usage and
ThetaSwap's growth-based usage.

---

## Section 5: Integration with extensionFlag

### 5.1 NoteId Mapping

The NoteId type (defined in `contracts/src/types/NoteId.sol`) encodes an extensionFlag
in bits [64, 66] (3 bits). The defined constants are:

| Flag | Value | Transformation Library |
|---|---|---|
| VANILLA | 0 | None (raw accrual) |
| ACCRUAL_DECRUAL | 1 | TBD |
| TARN | 2 | TBD |
| BARRIERS | 3 | TBD |
| CALLABLE | 4 | **EMAGrowthTransformationLib** |
| BASKET_UNDERLIER | 5 | TBD |
| FLOATING_COUPON | 6 | TBD |

### 5.2 The Transformation IS the Instrument

Choosing `extensionFlag = CALLABLE` when constructing a NoteId means the note's coupon
accrual is gated by EMA-smoothed growth observations. The caller (AccrualManagerMod or
a higher-level module) dispatches to the appropriate transformation library based on the
extensionFlag:

```
if (noteId.extensionFlag() == CALLABLE) {
    oraclePack = updateGrowthEMA(buffer, oraclePack, periods, clampDelta);
    int24 currentEMA = oraclePack.spotEMA();  // or fastEMA, slowEMA, etc.
    // ... use currentEMA for coupon gating logic ...
}
```

The choice of which EMA timescale gates the coupon is a parameter of the note, not of
this library. This library's sole responsibility is producing the updated OraclePack.

---

## Section 6: Edge Cases

### 6.1 Buffer Has Exactly Two Observations (Minimum Valid Case)

```
buffer: [obs_0 (block 100, cg 1000), obs_1 (block 112, cg 1100)]
```

Expected: growthTick = growthToTick(1100, 1000). The ratio is 1.1, producing a small
positive tick. This is the minimum viable input for the transformation.

### 6.2 All Observations Have the Same cumulativeGrowth

```
buffer: [obs_0 (block 100, cg 5000), ..., obs_255 (block 3100, cg 5000)]
```

Expected: growthTick = growthToTick(5000, 5000) = 0. All EMAs converge toward 0.
This represents a pool with no fee activity -- the growth accumulator is flat.

### 6.3 Very Large Growth Over Short Window

```
buffer: [obs_0 (block 100, cg 1), obs_1 (block 112, cg 2^80)]
```

Expected: growthTick = growthToTick(2^80, 1). The ratio is 2^80, which is within the
TickMath range (max ratio ~= 2^128). The resulting tick is very large but valid.
The clampDelta mechanism limits how much of this tick change feeds into the OraclePack
per update, preventing a single spike from dominating the EMAs.

### 6.4 OraclePack at Epoch 0 (Fresh Initialization)

```
currentOraclePack = OraclePack.wrap(0)  // all fields zero
```

Expected: epoch() returns 0. If current block.timestamp >= 64, the current epoch is >= 1,
which differs from 0, so the update proceeds. The clampTick against lastTick() = 0 bounds
the first observation. If the growth tick exceeds clampDelta, the clamped tick is
clampDelta (positive direction).

### 6.5 Epoch Wraparound (24-bit Counter)

```
oraclePack.epoch() = 0xFFFFFE  (one before max)
block.timestamp such that currentEpoch = 0xFFFFFF
```

Expected: timeDelta = 1 * 64 = 64 seconds. Update proceeds normally.

```
oraclePack.epoch() = 0xFFFFFF  (max)
block.timestamp such that currentEpoch = 0x000000  (wrapped)
```

Expected: The uint24 subtraction `(0x000000 - 0xFFFFFF)` wraps to 1 in unchecked
arithmetic. timeDelta = 1 * 64 = 64. Update proceeds. This is consistent with
OraclePack's own wraparound handling.

### 6.6 clampDelta = 0 (Maximum Restriction)

```
clampDelta = 0
```

Expected: clampTick always returns `oraclePack.lastTick()`, regardless of the growth tick.
The OraclePack's EMAs never change. This effectively freezes the oracle. While not useful
in production, it is a valid edge case that should not revert.

### 6.7 clampDelta = type(int24).max (No Restriction)

```
clampDelta = 8388607
```

Expected: Since TickMath ticks are bounded to [-887272, 887272], and clampDelta at
8388607 far exceeds the tick range, the clamp is never binding. The growth tick passes
through to insertObservation unclamped.

---

## Section 7: Revert Taxonomy

| Condition | Source | Error |
|---|---|---|
| Buffer empty (count == 0) | `oldestObservation()` or `latestObservation()` | `EmptyBuffer()` |
| Buffer has < 2 observations | `updateGrowthEMA` precondition check | `InsufficientObservations()` (new error) or equivalent |
| anchorGrowth == 0 | `growthToTick` -> `FullMath.mulDiv` | EVM panic (0x12) division by zero |
| Growth ratio overflows | `growthToTick` -> `FullMath.mulDiv` | Overflow revert |
| sqrtPriceX96 out of TickMath range | `growthToTick` -> `TickMath.getTickAtSqrtPrice` | `InvalidSqrtPrice()` |

Note: The same-epoch short-circuit path has NO revert conditions (it returns
immediately without reading the buffer or calling any downstream functions).

---

## Section 8: Gas Considerations

### 8.1 Same-Epoch Fast Path

When the current epoch matches the OraclePack's epoch, the function performs:
- One epoch computation: `(block.timestamp >> 6) & 0xFFFFFF`
- One comparison against `currentOraclePack.epoch()`
- Immediate return

This costs approximately 50-80 gas (pure arithmetic, no storage reads).

### 8.2 New-Epoch Full Path

When the epoch differs, the function performs:
- 2 SLOAD operations (latestObservation + oldestObservation from CircularBuffer)
- 1 FullMath.mulDiv (512-bit multiplication)
- 1 Solady sqrt
- 1 TickMath.getTickAtSqrtPrice
- 1 OraclePack.clampTick
- 1 OraclePack.insertObservation (includes updateEMAs + sorted insertion)

All operations after the SLOAD are pure computation. The two SLOADs dominate gas cost
at 2100 gas each (cold) or 100 gas each (warm, if read in the same transaction).

### 8.3 No Storage Writes

This library does NOT write to storage. The caller is responsible for persisting the
returned OraclePack. This separation enables the caller to batch multiple updates or
conditionally skip persistence based on business logic.

---

## Section 9: Fuzz Input Ranges

### For the valid update path:

| Parameter | Type | Min | Max | Notes |
|---|---|---|---|---|
| buffer observations | count | 2 | 256 | Buffer capacity is 256 in production |
| oldest cumulativeGrowth | uint208 | 1 | 2^208 - 1 | Must be non-zero for valid ratio |
| latest cumulativeGrowth | uint208 | oldest | oldest * 2^128 | Ratio must fit in TickMath range |
| EMAperiods (spot) | uint24 | 64 | 16777215 | Minimum = 1 epoch = 64 seconds |
| EMAperiods (fast) | uint24 | 256 | 16777215 | > spot period |
| EMAperiods (slow) | uint24 | 1024 | 16777215 | > fast period |
| EMAperiods (eons) | uint24 | 4096 | 16777215 | > slow period |
| clampDelta | int24 | 0 | 887272 | 0 = max restriction, MAX_TICK = no restriction |

### For the same-epoch no-op path:

Set `block.timestamp` such that `(block.timestamp >> 6) & 0xFFFFFF == currentOraclePack.epoch()`.
The buffer contents are irrelevant (never read).

### For the revert paths:

| Scenario | Buffer State | Expected Error |
|---|---|---|
| Empty buffer | count = 0 | EmptyBuffer |
| Single observation | count = 1 | InsufficientObservations |
| Zero anchor growth | oldest.cumulativeGrowth = 0 | EVM panic 0x12 |
| Extreme ratio | latest/oldest > 2^128 | Overflow or InvalidSqrtPrice |
