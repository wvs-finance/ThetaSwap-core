# GrowthToTickLib -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/libraries/GrowthToTickLib.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Depends on:** GrowthObservation V2 BTT Spec (`growth-observation-v2-btt-spec.md`)

---

## Overview

GrowthToTickLib provides a single free function that converts a Q128.128 cumulative growth
ratio into a Uniswap V4 tick. This is the bridge between the raw accumulator domain
(uint208 values from the observation buffer) and the tick domain consumed by OraclePack
and all downstream transformation libraries.

The function is pure, stateless, and deterministic. It composes three external primitives
into a four-stage conversion pipeline:

1. FullMath.mulDiv -- 512-bit-intermediate division for Q128.128 ratio
2. Solady FixedPointMathLib.sqrt -- integer square root
3. Bit-shift scaling to Q96 format
4. Uniswap V4 TickMath.getTickAtSqrtPrice -- sqrtPriceX96 to int24 tick

### Pattern

Free functions (not inside a `library` block), consistent with GrowthObservation.sol and
BlockNumberAwareGrowthObserverLib.sol.

### Dependencies

| Dependency | Source | Function Used |
|---|---|---|
| `FullMath` | `v4-core/src/libraries/FullMath.sol` | `mulDiv(uint256, uint256, uint256) -> uint256` |
| `FixedPointMathLib` | `solady/src/utils/FixedPointMathLib.sol` | `sqrt(uint256) -> uint256` |
| `TickMath` | `v4-core/src/libraries/TickMath.sol` | `getTickAtSqrtPrice(uint160) -> int24` |
| `FixedPoint96` | `v4-core/src/libraries/FixedPoint96.sol` | `Q96 = 2^96` |
| `FixedPoint128` | `v4-core/src/libraries/FixedPoint128.sol` | `Q128 = 2^128` |

---

## Section 1: Conversion Math Pipeline

### 1.1 Input Domain

Both `currentGrowth` and `anchorGrowth` are uint208 values extracted from `GrowthObservation`
via the `cumulativeGrowth()` accessor. They represent truncated Q128.128 cumulative growth
accumulators (actually Q80.128 due to uint208 truncation, but the fractional precision is
the full 128 bits).

The ratio `currentGrowth / anchorGrowth` represents the multiplicative growth factor
between two points in time. Because cumulative growth is monotonically non-decreasing,
the ratio is always >= 1 when the caller provides correctly ordered observations.

### 1.2 Stage 1: Q128.128 Ratio via FullMath.mulDiv

```
ratioQ128 = FullMath.mulDiv(currentGrowth, Q128, anchorGrowth)
```

Where `Q128 = 2^128 = 0x100000000000000000000000000000000`.

This computes `(currentGrowth * 2^128) / anchorGrowth` with a 512-bit intermediate
product, avoiding overflow. The result is a Q128.128 fixed-point number where:
- The upper 128 bits represent the integer part of the ratio
- The lower 128 bits represent the fractional part

**Bit-width analysis:**
- Input: currentGrowth is at most uint208 (2^208 - 1)
- Multiplication: uint208 * uint128 = at most 336 bits -- fits in the 512-bit intermediate
- Division: 336-bit numerator / uint208 denominator = at most 128 + (208 - 0) = 336 bits
  in the worst case, but since ratio >= 1, the result is bounded by
  `(2^208 - 1) * 2^128 / 1 = 2^336 - 2^128`, which is 336 bits
- However, for the downstream stages to work, we need the result to fit in uint256.
  FullMath.mulDiv returns uint256 and will revert on overflow.

**Revert conditions:**
- `anchorGrowth == 0`: Division by zero inside FullMath.mulDiv (EVM reverts)
- Result > type(uint256).max: When currentGrowth is extremely large relative to
  anchorGrowth (e.g., currentGrowth near uint208 max, anchorGrowth == 1), the
  numerator is ~2^336, which exceeds uint256. FullMath.mulDiv reverts.

**Practical bound:** For the result to fit in uint256, we need:
```
currentGrowth * 2^128 / anchorGrowth < 2^256
=> currentGrowth / anchorGrowth < 2^128
```
This means the growth ratio must be less than 2^128, which is an astronomically large
multiplier and will never be reached in practice.

### 1.3 Stage 2: Integer Square Root via Solady sqrt

```
sqrtRatioX64 = FixedPointMathLib.sqrt(ratioQ128)
```

Solady's `sqrt(x)` computes `floor(sqrt(x))` for any uint256 input, returning uint256.

**Interpretation:** If `ratioQ128` is a Q128.128 value, then:
```
sqrt(ratioQ128) = sqrt(ratio * 2^128) = sqrt(ratio) * 2^64
```

So the result is `sqrt(ratio)` scaled by 2^64 -- a Q64.64 fixed-point number (with the
integer part in the upper bits and 64 bits of fractional precision).

**Bit-width analysis:**
- Input: ratioQ128 is at most uint256 (2^256 - 1)
- Output: sqrt(2^256 - 1) < 2^128, so result fits in uint128
- More precisely, since ratio >= 1, ratioQ128 >= 2^128, so sqrt(ratioQ128) >= 2^64

### 1.4 Stage 3: Scale to sqrtPriceX96

Uniswap V4's TickMath operates on `sqrtPriceX96` values -- Q64.96 fixed-point numbers
stored as uint160. We have a Q64.64 value and need Q64.96, so we left-shift by 32:

```
sqrtPriceX96 = sqrtRatioX64 << 32
```

Equivalently, we can express this as:
```
sqrtPriceX96 = sqrtRatioX64 * 2^32
```

**Alternative derivation via Q96 / Q64:**
```
sqrtPriceX96 = sqrtRatioX64 * Q96 / Q64
             = sqrtRatioX64 * 2^96 / 2^64
             = sqrtRatioX64 * 2^32
```

**Bit-width analysis:**
- Input: sqrtRatioX64 < 2^128 (from Stage 2)
- After shift: sqrtRatioX64 << 32 < 2^160
- TickMath.getTickAtSqrtPrice accepts uint160, so we must verify the shifted value
  fits. Since sqrtRatioX64 < 2^128, the shifted result < 2^160, which fits in uint160.
- More tightly: for the practical bound (ratio < 2^128), sqrtRatioX64 < 2^128, and
  the shift gives < 2^160 which is exactly the uint160 range.

**Range validation for TickMath:**
- TickMath.getTickAtSqrtPrice requires: `MIN_SQRT_PRICE <= sqrtPriceX96 < MAX_SQRT_PRICE`
- MIN_SQRT_PRICE = 4295128739 (approximately 2^32)
- MAX_SQRT_PRICE = 1461446703485210103287273052203988822378723970342 (approximately 2^160)
- For ratio = 1: sqrtRatioX64 = 2^64, sqrtPriceX96 = 2^96 (well within range)
- For ratio approaching 0 (if allowed): sqrtPriceX96 approaches 0 (below MIN_SQRT_PRICE)
- For ratio at the maximum representable value: sqrtPriceX96 approaches 2^160

### 1.5 Stage 4: Tick via TickMath.getTickAtSqrtPrice

```
tick = TickMath.getTickAtSqrtPrice(uint160(sqrtPriceX96))
```

Returns the greatest tick such that `getSqrtPriceAtTick(tick) <= sqrtPriceX96`.

**Range:**
- MIN_TICK = -887272
- MAX_TICK = 887272
- Since our ratio >= 1, sqrtPriceX96 >= 2^96, and `getTickAtSqrtPrice(2^96) = 0`
- Therefore the result is always tick >= 0

**Revert conditions:**
- `sqrtPriceX96 < MIN_SQRT_PRICE`: Reverts with `TickMath.InvalidSqrtPrice()`
- `sqrtPriceX96 >= MAX_SQRT_PRICE`: Reverts with `TickMath.InvalidSqrtPrice()`

---

## Section 2: BTT Behavior Tree

### 2.1 growthToTick

**Signature:**

```
function growthToTick(uint208 currentGrowth, uint208 anchorGrowth) pure returns (int24 tick)
```

**Mutability:** pure

```
GrowthToTickLib::growthToTick
|
+-- when anchorGrowth is zero
|   +-- it should revert (division by zero in FullMath.mulDiv).
|
+-- when currentGrowth is less than anchorGrowth
|   +-- it should revert (ratio < 1, sqrtPriceX96 < 2^96, which may fall
|       below MIN_SQRT_PRICE for sufficiently small ratios; additionally,
|       the accumulator is monotonically non-decreasing, so ratio < 1
|       indicates a caller bug or misordered observations).
|
+-- when currentGrowth equals anchorGrowth
|   +-- it should return tick zero.
|   +-- the intermediate ratioQ128 should equal Q128 exactly (ratio = 1).
|   +-- the intermediate sqrtRatioX64 should equal 2^64 exactly.
|   +-- the intermediate sqrtPriceX96 should equal 2^96 exactly.
|
+-- when currentGrowth is greater than anchorGrowth
    |
    +-- when the ratio exceeds TickMath MAX_SQRT_PRICE squared
    |   +-- it should revert (sqrtPriceX96 >= MAX_SQRT_PRICE triggers
    |       TickMath.InvalidSqrtPrice, or FullMath.mulDiv overflows uint256).
    |
    +-- when the ratio is within tick range
        +-- it should return a non-negative tick (ratio >= 1 maps to tick >= 0).
        +-- it should return a higher tick for a higher ratio (monotonic).
        +-- it should be consistent with TickMath:
            getSqrtPriceAtTick(result) <= sqrtPriceX96(ratio)
            < getSqrtPriceAtTick(result + 1).
```

---

## Section 3: Algebraic Properties (Invariants for Fuzz Testing)

### Property 1: Identity

For any valid anchorGrowth > 0:

```
growthToTick(anchorGrowth, anchorGrowth) == 0
```

When currentGrowth equals anchorGrowth, the ratio is 1.0, the sqrt is 1.0, the
sqrtPriceX96 is 2^96, and TickMath maps 2^96 to tick 0.

### Property 2: Monotonicity

For any anchorGrowth > 0 and currentGrowth values a1, a2 where
anchorGrowth <= a1 < a2 (both within the valid ratio range):

```
growthToTick(a1, anchorGrowth) <= growthToTick(a2, anchorGrowth)
```

This follows from the monotonicity of each pipeline stage:
- FullMath.mulDiv is monotonic in the numerator (larger currentGrowth -> larger ratio)
- sqrt is monotonic (larger ratio -> larger sqrt)
- Left-shift preserves ordering
- TickMath.getTickAtSqrtPrice is monotonic (floor function of a monotonic mapping)

The inequality is non-strict because tick is a discrete (floored) value -- two different
ratios can map to the same tick if they fall within the same tick's price range.

### Property 3: Consistency with TickMath

For any valid (currentGrowth, anchorGrowth) pair producing tick `t`:

```
getSqrtPriceAtTick(t) <= computedSqrtPriceX96 < getSqrtPriceAtTick(t + 1)
```

where `computedSqrtPriceX96` is the intermediate value passed to `getTickAtSqrtPrice`.

This is a direct consequence of TickMath's specification: `getTickAtSqrtPrice` returns
the greatest tick whose sqrt price is <= the input.

### Property 4: Non-negativity

For all valid inputs where `currentGrowth >= anchorGrowth`:

```
growthToTick(currentGrowth, anchorGrowth) >= 0
```

Because ratio >= 1 implies sqrtPriceX96 >= 2^96, and TickMath maps 2^96 to tick 0.
All prices above 2^96 map to non-negative ticks.

### Property 5: Anchor-scaling Invariance

For any constant multiplier `k > 0` (where all values remain within uint208 range):

```
growthToTick(k * currentGrowth, k * anchorGrowth) == growthToTick(currentGrowth, anchorGrowth)
```

This follows from the ratio being `(k * cg) / (k * ag) = cg / ag`. Note: due to
fixed-point truncation in FullMath.mulDiv, this property holds exactly only when `k`
divides evenly, and approximately (within +/- 1 tick) in general due to rounding.

For fuzz testing, assert the weaker form:

```
abs(growthToTick(k * cg, k * ag) - growthToTick(cg, ag)) <= 1
```

---

## Section 4: Edge Cases

### 4.1 anchorGrowth = 1 (minimum non-zero anchor)

```
anchorGrowth = 1
currentGrowth = 1
```

Expected: tick = 0 (ratio = 1).

```
anchorGrowth = 1
currentGrowth = 2
```

Expected: ratio = 2.0, which maps to tick = 6931 (approx, since tick represents
log_1.0001(price) and log_1.0001(2) ~= 6931).

This is a valid edge case because anchorGrowth = 1 represents the earliest possible
non-zero accumulator value.

### 4.2 currentGrowth = anchorGrowth + 1 (minimum non-trivial ratio)

```
anchorGrowth = 10^38 (a large but realistic accumulator)
currentGrowth = anchorGrowth + 1
```

Expected: ratio = 1 + 1/10^38, which is essentially 1.0. The tick should be 0 because
the price difference is negligible relative to tick spacing.

This tests the precision floor of the pipeline -- whether a minimal growth increment
produces tick 0 (correct) or an erroneous non-zero tick.

### 4.3 currentGrowth = type(uint208).max, anchorGrowth = 1

```
currentGrowth = 2^208 - 1
anchorGrowth = 1
```

Expected: FullMath.mulDiv computes `(2^208 - 1) * 2^128 / 1 = 2^336 - 2^128`,
which exceeds uint256. This should revert.

This tests the overflow boundary of Stage 1.

### 4.4 Large absolute values, ratio near 1

```
currentGrowth = type(uint208).max
anchorGrowth = type(uint208).max - 1
```

Expected: ratio = (2^208 - 1) / (2^208 - 2) ~= 1 + 2^(-208). Tick should be 0.

This tests that the pipeline handles large absolute values gracefully when their
ratio is close to 1. The FullMath.mulDiv computation involves a 512-bit intermediate
of approximately `2^336`, but the final result is close to `2^128` (ratio ~= 1),
which fits in uint256.

### 4.5 Ratio at the tick boundary

```
ratio = getSqrtPriceAtTick(MAX_TICK)^2 / 2^192
```

The maximum valid sqrtPriceX96 is MAX_SQRT_PRICE - 1 (since getTickAtSqrtPrice requires
strict less-than for MAX_SQRT_PRICE). The corresponding ratio is:

```
ratio = (MAX_SQRT_PRICE - 1)^2 / 2^192
```

This is the largest ratio that produces a valid tick (MAX_TICK). Any ratio larger than
`MAX_SQRT_PRICE^2 / 2^192` would cause sqrtPriceX96 >= MAX_SQRT_PRICE and revert.

### 4.6 currentGrowth = 0, anchorGrowth > 0

```
currentGrowth = 0
anchorGrowth = 100
```

Expected: ratio = 0, sqrtRatio = 0, sqrtPriceX96 = 0, which is below MIN_SQRT_PRICE.
This should revert via TickMath.InvalidSqrtPrice(). This case represents a caller bug
since cumulative growth should be monotonically non-decreasing and cannot go to zero
after being non-zero.

### 4.7 Both values equal to 1

```
currentGrowth = 1
anchorGrowth = 1
```

Expected: tick = 0. Tests the pipeline with the smallest possible equal non-zero values.
ratioQ128 = FullMath.mulDiv(1, 2^128, 1) = 2^128. sqrt(2^128) = 2^64.
sqrtPriceX96 = 2^64 << 32 = 2^96. getTickAtSqrtPrice(2^96) = 0.

---

## Section 5: Revert Taxonomy

| Condition | Stage | Revert Source | Error Selector |
|---|---|---|---|
| anchorGrowth == 0 | Stage 1 | FullMath.mulDiv | EVM division-by-zero panic (0x12) |
| ratio overflows uint256 | Stage 1 | FullMath.mulDiv | EVM arithmetic overflow or FullMath internal revert |
| sqrtPriceX96 < MIN_SQRT_PRICE | Stage 4 | TickMath.getTickAtSqrtPrice | InvalidSqrtPrice() |
| sqrtPriceX96 >= MAX_SQRT_PRICE | Stage 4 | TickMath.getTickAtSqrtPrice | InvalidSqrtPrice() |

Note: Stage 2 (sqrt) and Stage 3 (shift) cannot revert on their own. Solady's sqrt
is defined for all uint256 inputs. The left-shift by 32 of a value < 2^128 produces
a value < 2^160, which fits in uint256.

---

## Section 6: Bit-Width Analysis Summary

| Stage | Input Width | Operation | Output Width | Overflow Risk |
|---|---|---|---|---|
| 1. mulDiv | uint208, uint128, uint208 | (a * b) / c with 512-bit intermediate | uint256 | Yes -- reverts if result > 2^256 |
| 2. sqrt | uint256 | floor(sqrt(x)) | uint128 (at most) | No -- sqrt of uint256 fits in uint128 |
| 3. shift | uint128 | x << 32 | uint160 (at most) | No -- 128 + 32 = 160 bits |
| 4. getTickAtSqrtPrice | uint160 | lookup + log computation | int24 | No -- returns valid tick or reverts |

The critical overflow boundary is Stage 1. For the result to fit in uint256:

```
currentGrowth * Q128 / anchorGrowth < 2^256
```

Since currentGrowth <= 2^208 - 1 and Q128 = 2^128:

```
(2^208 - 1) * 2^128 / anchorGrowth < 2^256
=> anchorGrowth > (2^208 - 1) * 2^128 / 2^256
=> anchorGrowth > (2^208 - 1) / 2^128
=> anchorGrowth > 2^80 - 2^(-128) (approx)
=> anchorGrowth >= 2^80
```

So for anchorGrowth < 2^80, there exist currentGrowth values that cause Stage 1 to
overflow. In practice, cumulative growth accumulators start near zero and grow over time,
so very small anchorGrowth with very large currentGrowth represents an extreme scenario.

---

## Section 7: Fuzz Input Ranges

### For valid-path fuzz tests (should NOT revert):

| Parameter | Min | Max | Notes |
|---|---|---|---|
| anchorGrowth | 1 | 2^208 - 1 | Must be non-zero |
| currentGrowth | anchorGrowth | anchorGrowth * MAX_RATIO | Must be >= anchorGrowth, ratio must not overflow |

Where MAX_RATIO is bounded by the TickMath range. The maximum sqrtPriceX96 is
MAX_SQRT_PRICE - 1, so the maximum ratio is approximately `(MAX_SQRT_PRICE / 2^96)^2`.

MAX_SQRT_PRICE ~= 2^160, so maximum ratio ~= 2^128. Therefore:

```
currentGrowth / anchorGrowth < 2^128
```

### For revert-path fuzz tests:

| Scenario | anchorGrowth | currentGrowth |
|---|---|---|
| Division by zero | 0 | any |
| Ratio < 1 | bounded(1, 2^208 - 1) | bounded(0, anchorGrowth - 1) |
| Overflow | bounded(1, 2^80 - 1) | bounded(anchorGrowth * 2^128, 2^208 - 1) |

---

## Section 8: Relationship to Downstream Consumers

GrowthToTickLib is consumed by Layer 2 transformation libraries. The primary consumer
is `EMAGrowthTransformationLib`, which:

1. Reads the oldest and latest observations from the CircularBuffer
2. Extracts their cumulativeGrowth values
3. Calls `growthToTick(latest.cumulativeGrowth(), oldest.cumulativeGrowth())`
4. Feeds the resulting tick into `OraclePack.insertObservation()`

The tick output is an int24 in the range [0, MAX_TICK] (non-negative due to monotonic
growth). This maps directly to the `newTick` parameter of OraclePack, which stores it
as a 22-bit signed residual relative to its reference tick.

Other transformation libraries (TWAP, windowed delta, barrier observations) may also
consume GrowthToTickLib, always with the same (currentGrowth, anchorGrowth) interface.
The anchor selection strategy (oldest-in-buffer, fixed snapshot, rolling window) is
the caller's responsibility and defines the instrument's economic semantics.
