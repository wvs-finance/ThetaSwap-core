# Security Edge-Case Test Proposals — GrowthToTickLib

**Document type:** Security audit — adversarial test proposals
**Target file:** `contracts/src/libraries/GrowthToTickLib.sol`
**Dependencies under test:** `v4-core/FullMath`, `solady/FixedPointMathLib`, `v4-core/TickMath`, `v4-core/FixedPoint128`
**Status:** Audit report — no code written
**Date:** 2026-04-12
**Auditor:** Blockchain Security Auditor
**Existing coverage:** 1 differential test (`test__fuzzBTT__GrowthToTick_TickMathRoundTripConsistency`) + BTT spec

---

## 1. Audit Framing

`growthToTick(currentGrowth, anchorGrowth)` is a four-stage pure pipeline:

```
Stage 1: ratioQ128   = FullMath.mulDiv(currentGrowth, 2^128, anchorGrowth)   // uint256
Stage 2: sqrtRatioX64 = FixedPointMathLib.sqrt(ratioQ128)                    // uint128 upper bound
Stage 3: sqrtPriceX96 = sqrtRatioX64 << 32                                   // uint256, stored
Stage 4: tick         = TickMath.getTickAtSqrtPrice(uint160(sqrtPriceX96))   // int24
```

Compromise modes for a *pure* library split into three families:

1. **Revert-taxonomy surprises** — inputs that revert with an unnamed panic (0x11/0x12) or a vague error, rather than a domain-specific error the caller can branch on. Matters because this is a read-path primitive: a revert in the oracle poisons downstream EMA updates and option pricing.
2. **Silent miscomputation** — inputs where the pipeline does *not* revert but returns a tick that does not correspond to the intended semantic ratio. This is the worst class of bug; static analysis will not find it.
3. **Downstream contract violation** — inputs that produce a tick outside the range `EMAGrowthTransformationLib` / `OraclePack` expects, or that interact badly with the Q64.64 → Q64.96 shift / `uint160` narrowing cast.

The existing differential test covers Property 3 (TickMath round-trip floor) — a good *structural* check, but the fuzz bounds (`anchorGrowth ∈ [1, 2^208-1]`, `currentGrowth ≥ anchorGrowth`, `ratio < 2^128`) *skip every revert path and never stress the cast boundary*. That is the gap.

### Critical sub-observation on the `uint160(sqrtPriceX96)` cast

From the bit-width table in the BTT:
- `sqrtRatioX64 = sqrt(ratioQ128) ≤ sqrt(2^256 - 1) < 2^128` — strict.
- `sqrtPriceX96 = sqrtRatioX64 << 32 < 2^160` — strict.
- So `uint160(sqrtPriceX96)` is **never actually truncated** (because `sqrtPriceX96 < 2^160` always).
- **However**: `MAX_SQRT_PRICE ≈ 1.461 × 10^48 ≈ 2^160 / 1.098`, so there is a window
  `[MAX_SQRT_PRICE, 2^160)` — roughly the top ~9% of the uint160 range — where
  `sqrtPriceX96` is representable in uint160 **but** TickMath rejects it with `InvalidSqrtPrice`.
  This window is reachable with `ratioQ128` values near `2^256 − 1`.
- The BTT spec labels this "Edge Case 4.5" but no concrete test currently exercises the exact
  `MAX_SQRT_PRICE - 1` / `MAX_SQRT_PRICE` / `MAX_SQRT_PRICE + 1` boundary. A one-off-by-one
  in a future refactor (e.g. someone replaces `<< 32` with `* Q96 / Q64`) could silently
  cross this boundary in the wrong direction.

This is the kind of boundary that hides a silent miscomputation or a surprise revert, and it
is the primary focus of proposals G.1, G.2, G.3 below.

---

## 2. Test Proposals

Notation:
- `Q128 = 2^128`
- `MIN_SQRT_PRICE = 4_295_128_739`
- `MAX_SQRT_PRICE = 1_461_446_703_485_210_103_287_273_052_203_988_822_378_723_970_342`
- `MAX_TICK = 887_272`, `MIN_TICK = -887_272`

---

### G.1 `test__SecurityEdge__GrowthToTick_SqrtPriceX96NarrowingSafety` — **P0**

**Attack / failure mode.** The pipeline performs a narrowing cast `uint160(sqrtPriceX96)` where
`sqrtPriceX96` is a `uint256`. The spec argues this is safe because the prior stages bound
`sqrtPriceX96 < 2^160`. A refactor that changes Stage 2 or Stage 3 (e.g. swaps Solady sqrt for
another library that returns a tighter Q-format, or replaces `<< 32` with `mulDiv(x, Q96, Q64)`)
could silently lift the bound without triggering a compile error. Then values in `[2^160, 2^256)`
would silently truncate to arbitrary uint160 values, and TickMath would happily return a wildly
wrong tick.

**Concrete setup.** A hybrid fuzz + boundary test:
1. Deterministic boundary cases where the *mathematical* result of Stage 3 equals exactly
   `2^160 - 1`, `2^160`, `2^160 + 1`. Construct `anchorGrowth, currentGrowth` whose ratio maps
   Stage 2 to `2^128 - 1` (max representable). Compute Stage 3 manually as `uint256`.
2. Fuzz over the full valid input space and assert `sqrtPriceX96` (captured as uint256 in a test
   helper that mirrors the pipeline) is always `< 2^160`.

**Assertion.**
- The uint256 intermediate `sqrtPriceX96` satisfies `sqrtPriceX96 < (1 << 160)` for every reachable input pair.
- `uint160(sqrtPriceX96) == sqrtPriceX96` (no bits lost).
- When `sqrtPriceX96 >= MAX_SQRT_PRICE`, the function reverts with `TickMath.InvalidSqrtPrice`,
  not with a silently-truncated tick.

**Why P0.** This is the canary test for the only *unchecked* type narrowing in the pipeline.
Even if currently safe, documenting the invariant in an executable test pins it for future
refactors. The cast is the single thing most likely to break silently.

---

### G.2 `test__SecurityEdge__GrowthToTick_RatioAtMaxSqrtPriceBoundary` — **P0**

**Attack / failure mode.** BTT Edge Case 4.5 names the boundary `ratio = (MAX_SQRT_PRICE - 1)^2 / 2^192`
as the largest valid ratio, but no test exercises:
(a) a ratio producing `sqrtPriceX96 == MAX_SQRT_PRICE - 1` (should return `MAX_TICK`),
(b) a ratio producing `sqrtPriceX96 == MAX_SQRT_PRICE` exactly (should revert),
(c) a ratio producing `sqrtPriceX96 == MAX_SQRT_PRICE + 1` (should revert),
(d) a ratio producing `sqrtPriceX96 == MAX_SQRT_PRICE - 1 + 1` after a round-up elsewhere.

Solady's `sqrt` is `floor`. There is no rounding mode that would cause Stage 2 + Stage 3 to
overshoot the mathematical value, but a *compiler upgrade* or a *library version bump* on
FixedPointMathLib could introduce a round-to-nearest mode. The test must pin the current
floor semantics.

**Concrete setup.** Reverse-engineer the input pair:
- Target `sqrtPriceX96_target`. Compute `sqrtRatioX64_target = sqrtPriceX96_target >> 32`.
- Compute `ratioQ128_target = sqrtRatioX64_target^2` (exact square — fits in uint256 since
  sqrtRatioX64_target < 2^128).
- Pick `anchorGrowth = 1` and `currentGrowth = ratioQ128_target / Q128` — but this only works
  when `ratioQ128_target` is divisible by Q128, otherwise the floor in Stage 1 perturbs the
  result. Instead: pick `anchorGrowth = 2^80` (smallest anchor that avoids Stage 1 overflow for
  the MAX boundary) and `currentGrowth = ratioQ128_target * anchorGrowth / Q128`, clamped to
  uint208.
- Execute and capture the tick.

Four sub-cases:
1. `sqrtPriceX96_target = MAX_SQRT_PRICE - 1` → expect `tick == MAX_TICK`, no revert.
2. `sqrtPriceX96_target = MAX_SQRT_PRICE` → expect revert `InvalidSqrtPrice`.
3. Target such that the floors cause Stage 3 to produce `MAX_SQRT_PRICE - 1` or higher →
   boundary verified at the discrete-price transition.
4. A fuzz sweep of ratios just below the boundary to ensure `tick` monotonically reaches
   `MAX_TICK` before the revert cliff (no dead band).

**Assertion.** Cases 1 and 3 return valid ticks `∈ [0, MAX_TICK]`. Case 2 reverts with
`TickMath.InvalidSqrtPrice`. Case 4 confirms monotonicity right up to the cliff.

**Why P0.** This test pins the `MAX_TICK` cliff. Without it, an attacker supplying a near-max
ratio could silently produce a tick one-off-by-one on either side, and the downstream EMA would
integrate a wrong top-of-range value.

---

### G.3 `test__SecurityEdge__GrowthToTick_Stage1OverflowRevertTaxonomy` — **P0**

**Attack / failure mode.** BTT Section 5 lists "ratio overflows uint256" as a revert but the
existing diff test skips this via `vm.assume(currentGrowth / anchorGrowth < (1 << 128))`. The
actual revert surface is:
- `FullMath.mulDiv(current, 2^128, anchor)` reverts when `(current * 2^128) / anchor >= 2^256`.
- This happens for `anchorGrowth < 2^80` paired with sufficiently large `currentGrowth`.
- The revert is `FullMath`'s internal `require(denominator > prod1)` — a *bare require with no
  reason string*. This is indistinguishable at the call site from a generic failure.

If the keeper ever records a pool with extremely small early anchor growth (a brand-new pool
with one microscopic fee accrual), the ratio computation could overflow on the very first
`updateGrowthEMA` call and the caller sees a bare revert. Hard to debug in production.

**Concrete setup.** Enumerate:
1. `anchorGrowth = 1, currentGrowth = type(uint208).max` — guaranteed Stage 1 overflow.
2. `anchorGrowth = 2^79, currentGrowth = type(uint208).max` — just below the safe threshold.
3. `anchorGrowth = 2^80, currentGrowth = type(uint208).max` — exactly at the safe threshold;
   ratio ≈ `2^128`, borderline representable.
4. `anchorGrowth = 2^80 + 1, currentGrowth = type(uint208).max` — just inside the safe region.
5. Fuzz: `anchorGrowth ∈ [1, 2^80]`, `currentGrowth ∈ [anchorGrowth, 2^208-1]`, expect revert.

**Assertion.** Cases 1, 2 revert. Case 3 either reverts or produces `tick == MAX_TICK` without
truncation (document whichever). Case 4 produces a valid tick. Case 5 fuzz universally reverts.
The revert is captured and asserted to be from FullMath — not from a narrowing cast, not from
TickMath, not a generic Panic 0x11 — so the caller can build a reliable revert-classifier.

**Why P0.** The current revert is anonymous. A named error (`RatioOverflow()`) is a
recommended design change but absent that, a test that pins the *exact* revert point protects
against a future FullMath version that changes the require to a panic, or vice versa.

---

### G.4 `test__SecurityEdge__GrowthToTick_ZeroAnchorAndZeroCurrent` — **P0**

**Attack / failure mode.** BTT Edge Cases 4.6 (current=0, anchor>0) and anchor=0 (previous
audit C.1) are named but the combinations are not:
1. `anchorGrowth = 0, currentGrowth = 0` → Panic 0x12 (div by zero), not the `InvalidSqrtPrice`
   that a caller might expect for the semantic "zero ratio" case.
2. `anchorGrowth = 0, currentGrowth > 0` → Panic 0x12.
3. `anchorGrowth > 0, currentGrowth = 0` → Stage 1 returns 0, Stage 2 returns 0, Stage 3 returns
   0 → `TickMath.InvalidSqrtPrice` because `0 < MIN_SQRT_PRICE`.
4. `anchorGrowth > 0, currentGrowth = anchorGrowth - 1` (ratio just below 1) → Stage 3 returns
   a value near `2^96` but below — still likely above `MIN_SQRT_PRICE`, so no revert, but the
   returned tick is *negative*. The BTT's Property 4 claims non-negativity *conditional on
   current ≥ anchor*; this test documents what happens when the implicit precondition is
   violated. Crucial because the caller (EMA) has no input validation.

**Concrete setup.** Four deterministic calls covering cases 1–4 above. For case 4, sweep
`currentGrowth ∈ [1, anchorGrowth - 1]` with `anchorGrowth = Q64` (a round value) and record
all returned ticks.

**Assertion.**
- Case 1, 2: revert with Panic 0x12 (div by zero). Explicitly `vm.expectRevert(stdError.divisionError)`.
- Case 3: revert with `TickMath.InvalidSqrtPrice(0)`.
- Case 4: returns a negative tick (possibly down to `MIN_TICK` at extreme ratios). Document
  the observation that `EMAGrowthTransformationLib` must never pass ratios < 1 — this test is
  the contract. Additionally: assert that `tick < 0` exactly when `currentGrowth < anchorGrowth`.

**Why P0.** Property 4 (non-negativity) in the BTT is a *conditional* property. Its guard
(ratio ≥ 1) is enforced nowhere in the library. If a caller ever inverts the argument order
(`growthToTick(oldest, latest)` instead of `growthToTick(latest, oldest)`), the function does
not revert — it returns a valid-looking but semantically inverted tick. That is a silent
miscomputation of the worst kind. Pin the behavior.

---

### G.5 `test__SecurityEdge__GrowthToTick_InvertedArgumentSilentMiscomputation` — **P0**

**Attack / failure mode.** Directly related to G.4 case 4 but deserves its own test. A caller
bug that swaps the arguments — `growthToTick(oldest, latest)` instead of
`growthToTick(latest, oldest)` — produces a ratio < 1 and a **negative tick** with no revert.
The downstream `EMAGrowthTransformationLib` expects non-negative ticks (per BTT Section 8), but
the transformation does not explicitly reject negative ticks. An inverted call silently feeds
`OraclePack` a negative residual tick that may encode to a valid 22-bit signed value, silently
corrupting the oracle for 256 blocks.

**Concrete setup.** Fuzz pairs `(a, b)` where `a < b`, both in `[1, 2^208-1]`. Compute
`tick_forward = growthToTick(b, a)` and `tick_inverted = growthToTick(a, b)`.

**Assertion.**
- `tick_forward >= 0` (Property 4 normal case).
- `tick_inverted <= 0` (inverted ratio).
- `|tick_forward + tick_inverted| <= 1` when `MIN_SQRT_PRICE` is not violated — the *ideal*
  mathematical symmetry is `tick_forward == -tick_inverted` but tick discretization allows ±1.
  Document and assert a bound.
- There exist small-ratio inverted pairs where `tick_inverted == MIN_TICK` (approached as
  `b / a → ∞`).
- There exist extreme-ratio pairs where the inverted call *reverts* with `InvalidSqrtPrice`
  (when `b >> a` causes `sqrtPriceX96 < MIN_SQRT_PRICE`).

**Why P0.** This surfaces the worst class of latent bug — caller-error silent miscomputation
with no revert. The test documents the symmetry and highlights that the library itself cannot
detect argument inversion. The recommendation (out of scope here) would be to add
`require(currentGrowth >= anchorGrowth, RatioBelowUnity())` inside `growthToTick`.

---

### G.6 `test__SecurityEdge__GrowthToTick_PrecisionFloorAtMinimumRatio` — **P1**

**Attack / failure mode.** BTT Edge Case 4.2: `anchorGrowth = 10^38, currentGrowth = anchorGrowth + 1`.
The ratio is essentially 1 + 10^-38 ≈ 1. The pipeline must return `tick == 0`. But the precision
path is:
- `ratioQ128 = (10^38 + 1) * 2^128 / 10^38 = 2^128 + floor(2^128 / 10^38) ≈ 2^128 + 3`.
- `sqrt(2^128 + 3) = 2^64 + 0` (since Solady's sqrt is floor and 3 is far below 2^65).
- `sqrtPriceX96 = 2^64 << 32 = 2^96` exactly.
- `tick = 0`. ✓

So the math works out. But: what if `anchorGrowth = 10^2, currentGrowth = 10^2 + 1`? Ratio =
1 + 10^-2 = 1.01. Expected tick ≈ `log_1.0001(1.01) ≈ 99.5`. Does the pipeline return
tick 99 (floor) consistently, or does a subtle rounding step occasionally push it to 100?

The concern: when the "+1" in currentGrowth is a large fraction of anchorGrowth, the Stage 1
result is `Q128 * (1 + 1/anchor)`, and Stage 2's floor sqrt interacts non-trivially with
Stage 4's floor tick. The Property 3 test only verifies the local floor consistency — it does
not verify that no combination of three floors ever "beats" the true tick by more than 1.

**Concrete setup.** Fuzz `anchorGrowth ∈ [1, 10^18]`, `currentGrowth = anchorGrowth + k` for
`k ∈ [1, 100]`. For each pair:
- Compute the *true* tick via a high-precision Python oracle: `tick_true = floor(log_1.0001(sqrt(current/anchor)))`.
  (Or via `TickMath.getTickAtSqrtPrice(true_sqrtPriceX96)` using an exact sqrt in Python.)
- Compute `tick_actual = growthToTick(currentGrowth, anchorGrowth)`.
- Assert `|tick_actual - tick_true| <= 1`.

This is a **differential test against a Python oracle**, following the repo's existing
`ffi_utils` pattern.

**Assertion.** For all fuzzed small-anchor / small-delta pairs, the actual tick is within ±1 of
the true tick. The BTT's implicit claim "the compounded floors never exceed ±1 error" is
executable-pinned.

**Why P1.** The precision-floor analysis is theoretical in the BTT. A differential Python oracle
gives it teeth. Failures here would indicate that the compounded-floor error grows beyond the
assumed 1-tick bound, breaking Property 5 (anchor-scaling invariance) more than claimed.

---

### G.7 `test__SecurityEdge__GrowthToTick_AnchorScalingInvarianceWithSmallAnchors` — **P1**

**Attack / failure mode.** BTT Property 5 promises `|growthToTick(k*c, k*a) - growthToTick(c, a)| ≤ 1`.
The spec's justification relies on the ratio being unchanged. But with small `anchorGrowth`,
the Stage 1 floor `(c * Q128) / a` and `(k*c * Q128) / (k*a)` are not mathematically identical
due to different dividend magnitudes hitting uint256 differently. Specifically:
- Small `a`: the remainder in `c * Q128 mod a` is bounded by `a - 1`, so relative precision is
  `~1/a` in the Q128.128 ratio.
- Scaling by `k`: the remainder becomes bounded by `k*a - 1`, relative precision `~1/(k*a)` —
  *better*. So scaling up should tighten the tick, not widen it.

But what about scaling *down*? The BTT implicitly assumes integer `k`, not fractional. An
off-chain analyst might worry about `k = 1/2`: this is not supported (integer division) but the
test should prove that the library is robust against *any* integer `k` including k=1 (no-op)
and k at the boundary where `k * currentGrowth` overflows uint208.

**Concrete setup.**
1. Fuzz `a ∈ [1, 2^100]`, `c ∈ [a, 2*a]` (small ratio near 1), `k ∈ [1, 2^108]` such that
   `k * c < 2^208`.
2. Compute `tick_base = growthToTick(c, a)` and `tick_scaled = growthToTick(k*c, k*a)`.
3. Repeat with **extreme small anchor**: `a = 1`, `c = 2`, `k ∈ [1, 2^207]`.
4. Also test the boundary: `k` is such that `k*c` is exactly `2^208 - 1` (no headroom).

**Assertion.**
- `|tick_base - tick_scaled| <= 1` for every sampled pair.
- For `a = 1, c = 2, k = any`: `tick_scaled == tick_base` *exactly* (no rounding, because
  `k*2 / k*1 = 2` exactly for any k — no remainder to lose). Document that small-anchor ratios
  with exact integer `k` scaling are *bit-for-bit* identical, not just within ±1.
- If any pair produces `|Δ| > 1`, flag as a **Critical** finding: Property 5 is tighter than
  the BTT claims, and any violation is a real bug.

**Why P1.** The BTT claim of "±1" is loose. Tightening it to "exactly equal when k divides
evenly" would give the EMA library a stronger invariant to rely on. The test pins the actual
behavior.

---

### G.8 `test__SecurityEdge__GrowthToTick_MonotonicityAtTickBoundaryTransitions` — **P1**

**Attack / failure mode.** BTT Property 2 (monotonicity) says `a1 < a2 ⇒ tick(a1) ≤ tick(a2)`.
But monotonicity is *non-strict*, and the gap between two consecutive representable
`currentGrowth` values (i.e., `c` and `c + 1`) could theoretically straddle a tick boundary.
Tick boundaries are at `sqrtPriceX96 = getSqrtPriceAtTick(t)` for each `t`. Between tick `t`
and `t+1`, the sqrt ratio increases by a factor of `sqrt(1.0001)` ≈ `1 + 5e-5`. For this
factor to be achievable by a single +1 increment on `currentGrowth`, we need
`1/anchorGrowth >= 2 * 5e-5` roughly — i.e., `anchorGrowth ≤ 10_000`. So for tiny anchors,
adjacent inputs *can* skip a tick. Is the skip always by exactly +1, or can it skip multiple?

**Concrete setup.**
- Fix `anchorGrowth ∈ {1, 2, 10, 100, 1000, 10_000}`.
- For each, sweep `currentGrowth ∈ [anchorGrowth, anchorGrowth + 10000]` in unit increments.
- Compute `tick(c+1) - tick(c)` for each step.

**Assertion.**
- Every step is `>= 0` (monotonic).
- Steps of `> 1` are rare (bounded by some constant determined by the sqrt + log scaling).
- Specifically, there is no input pair where `tick(c+1) < tick(c)` (strict monotonicity
  violation = bug).
- Produce a histogram of step sizes. If any step is > ~10 ticks (which would be implausibly
  large), flag as a precision cliff.

**Why P1.** This is a smoke test against the precision-cliff class of bug. A strict
monotonicity violation would be a catastrophic correctness failure that Property 3's floor
consistency wouldn't catch (the floor holds locally even when global monotonicity breaks).

---

### G.9 `test__SecurityEdge__GrowthToTick_FullMathRoundingConsistency` — **P2**

**Attack / failure mode.** `FullMath.mulDiv` in v4-core rounds down (floor). An alternative
variant `mulDivRoundingUp` exists. If a future refactor swaps one for the other — or if a
compiler-level optimization changes semantics — the Stage 1 result could shift by up to ±1
ulp in Q128.128. The downstream test must catch this.

**Concrete setup.** Differential against a Python-reference pipeline that models both round-down
and round-up mulDiv. For each fuzzed input pair, assert the Solidity result matches the
round-down oracle, not the round-up oracle, and both oracles disagree on some inputs (proving
the test has discriminating power).

**Assertion.** For at least one fuzzed input pair, `round_down_oracle != round_up_oracle`
(discriminating power). For all fuzzed pairs, `solidity_result == round_down_oracle`.

**Why P2.** Nice-to-have regression test. Protects against a refactor that silently changes
FullMath rounding direction.

---

### G.10 `test__SecurityEdge__GrowthToTick_DownstreamEMATickRangeContract` — **P1**

**Attack / failure mode.** `EMAGrowthTransformationLib` feeds the output tick into
`OraclePack.insertObservation`, which stores it as a 22-bit signed residual relative to a
reference tick. If `growthToTick` ever returns a tick outside the range that OraclePack can
encode — either below `MIN_TICK` or above `MAX_TICK`, or outside the 22-bit residual window
given the current reference tick — OraclePack would either revert or silently truncate the tick
(depending on its encoding implementation).

The BTT claims the output is always `>= 0` (Property 4) but does not bound the upper tick.
Theoretically the output can reach `MAX_TICK`. If OraclePack's reference tick is e.g. `100_000`
and the residual is 22-bit signed (range `[-2^21, 2^21-1] = [-2_097_152, 2_097_151]`), then
any `tick ∈ [-1_997_152, 2_197_151]` encodes correctly. Since `MAX_TICK = 887_272` is well
inside that window for a zero-reference, this is probably fine — **but**, if the reference
tick is far from zero (e.g. a pool whose price has moved to tick 800_000), and `growthToTick`
returns 0 (the stagnation case C.2 from the previous audit), the residual becomes -800_000
which is still inside the 22-bit signed range, fine. What about reference = 800_000 and
growth-derived tick = 887_272? Residual = 87_272, fine. The window is large enough.

But the test should *prove* the composition holds for all reachable inputs, because downstream
libraries evolve and the tick-range contract is easy to break silently.

**Concrete setup.** Fuzz input pairs across the full valid domain. For each pair:
1. Compute `tick = growthToTick(current, anchor)`.
2. Assert `tick >= 0 && tick <= MAX_TICK` (Property 4 upper bound).
3. Assert `tick` is encodable as a 22-bit signed residual against a reference of
   `{0, MAX_TICK, MIN_TICK, MAX_TICK / 2}` — i.e. in all four, `(tick - reference)` fits in
   `[-2^21, 2^21 - 1]`, OR `growthToTick` is called in a context where the reference is known
   to be clamped (in which case document the clamp contract).

**Assertion.** The output tick is always within the range downstream consumers can handle
without truncation or revert, for every reachable input pair.

**Why P1.** Compositional invariants between libraries are the most commonly broken invariants
during refactors. A test here pins the handshake between `GrowthToTickLib` and `OraclePack`.

---

### G.11 `test__SecurityEdge__GrowthToTick_SoladySqrtPerfectSquareBehavior` — **P2**

**Attack / failure mode.** Solady's `sqrt` returns `floor(sqrt(x))`. For perfect squares, it
returns the exact integer root. BTT Edge Case 4.7 notes `ratioQ128 = 2^128` is a perfect square
(sqrt = 2^64). But there is a family of perfect-square ratios: `ratioQ128 = (2^64 + k)^2`
for small `k`, produced when `currentGrowth / anchorGrowth = 1 + 2k/2^64 + k^2/2^128`. These
are extremely rare in the fuzz space but could, if hit exactly, produce a tick that crosses a
tick boundary in a way the non-perfect-square fuzz does not exercise.

**Concrete setup.** Deterministically construct input pairs whose ratio Q128 value is exactly
`(2^64 + k)^2` for `k ∈ {0, 1, 2, 2^32, 2^63}`. For each:
- Compute `currentGrowth * Q128` exactly and solve for `(current, anchor)` integer pairs.
- Execute and capture the tick.
- Assert the tick equals `TickMath.getTickAtSqrtPrice((2^64 + k) << 32)` exactly, with no ±1
  rounding.

**Assertion.** Perfect-square inputs produce ticks identical to the direct TickMath call on the
exact sqrtPriceX96, with no off-by-one from the sqrt step.

**Why P2.** Defensive. Perfect-square inputs are the only case where the sqrt floor introduces
zero error. Pinning this cleanly helps isolate where error enters the pipeline.

---

### G.12 `test__SecurityEdge__GrowthToTick_SymbolicReplayAgainstPythonOracle` — **P1**

**Attack / failure mode.** Generic differential meta-test: run the whole pipeline in Python
using `mpmath` with arbitrary precision, and compare against the Solidity output across a
curated corpus of 10_000+ input pairs sampled to cover:
- Ratios near 1 (identity case).
- Ratios near `2^128 - ε` (upper boundary).
- Small anchor (1, 2, 10, 100).
- Large anchor (`2^208 - 1`, `2^208 - 2`, `2^200`).
- Pairs constructed to hit each tick boundary `t ∈ {0, 1, 10, 100, 1000, 10000, 100000, MAX_TICK}`.
- Pairs constructed to hit every power-of-two `currentGrowth` value.
- Pairs that cause Stage 1 overflow (expected revert).
- Pairs that cause `sqrtPriceX96 >= MAX_SQRT_PRICE` (expected revert).

The Python oracle computes the mathematically-correct floor-tick for each input at 500-bit
precision.

**Concrete setup.** An FFI-driven differential test using the repo's existing `ffi_utils`
infrastructure. The Python script is pure-mpmath, no on-chain calls. The Solidity test reads
the CSV of `(current, anchor, expected_tick_or_revert_reason)` triples and asserts each one.

**Assertion.** For every input in the corpus:
- If Python says "revert with X", Solidity reverts with X.
- If Python says "return tick T", Solidity returns T (exact, no ±1 tolerance — the composition
  of floors is deterministic and should match mpmath's floor-composition exactly).

**Why P1.** This is the "hardest-kind-of-bug" catcher: silent miscomputation. A single input
where Python and Solidity disagree is a bug. The Python oracle is the source of truth for the
mathematical semantics; the Solidity code must match it byte-exactly (given matching rounding
modes).

---

## 3. Summary — Priority Matrix

| ID   | Test Name                                                    | Priority | Bug class targeted                |
|------|--------------------------------------------------------------|----------|-----------------------------------|
| G.1  | SqrtPriceX96NarrowingSafety                                  | P0       | Silent cast truncation            |
| G.2  | RatioAtMaxSqrtPriceBoundary                                  | P0       | MAX_TICK cliff / revert boundary  |
| G.3  | Stage1OverflowRevertTaxonomy                                 | P0       | Revert-taxonomy regression        |
| G.4  | ZeroAnchorAndZeroCurrent                                     | P0       | Revert-taxonomy + silent negative |
| G.5  | InvertedArgumentSilentMiscomputation                         | P0       | Silent miscomputation (worst)     |
| G.6  | PrecisionFloorAtMinimumRatio                                 | P1       | Compounded floor error bound      |
| G.7  | AnchorScalingInvarianceWithSmallAnchors                      | P1       | Property 5 strict-form check      |
| G.8  | MonotonicityAtTickBoundaryTransitions                        | P1       | Monotonicity stress               |
| G.9  | FullMathRoundingConsistency                                  | P2       | Library-version regression        |
| G.10 | DownstreamEMATickRangeContract                               | P1       | Cross-library composition         |
| G.11 | SoladySqrtPerfectSquareBehavior                              | P2       | Pipeline rounding isolation       |
| G.12 | SymbolicReplayAgainstPythonOracle                            | P1       | Silent miscomputation (catch-all) |

**P0 count: 5** — must be added before the library is considered production-ready for the RAN oracle.
**P1 count: 5** — should be added before audit closure.
**P2 count: 2** — nice-to-have hardening.

---

## 4. Cross-Cutting Observations (not tests — design notes)

While inside the test-proposal scope, these surfaced as design changes that would eliminate
entire test classes. Per the instructions, the user will not merge fix recommendations — these
are for context only.

1. **Named error for Stage 1 overflow.** Wrap the `FullMath.mulDiv` call in a try/catch or
   pre-check (`require(anchorGrowth > 0, ZeroAnchorGrowth())` + an explicit bound check on
   `currentGrowth / anchorGrowth < 2^128`). Would collapse G.3 into a trivial
   `vm.expectRevert(ZeroAnchorGrowth.selector)` assertion.

2. **Monotonicity precondition.** Add `require(currentGrowth >= anchorGrowth, RatioBelowUnity())`
   at the top of `growthToTick`. Would close G.4 case 4 and G.5 entirely by making inverted
   arguments a caller-visible revert rather than a silent negative tick.

3. **Explicit tick-range bound.** After Stage 4, add `require(tick >= 0, ...)` to enforce
   Property 4 at the library level. Belt-and-braces, but the absence of this bound is why
   G.5 is a real silent-miscomputation risk.

4. **Document the uint160 cast safety invariant in a comment.** The safety of `uint160(sqrtPriceX96)`
   relies on a non-obvious bit-width chain. A `/// @dev` comment pinning the proof would reduce
   G.1's value but not its necessity.

---

## 5. Methodology Notes

- **Differential test style.** Proposals G.1, G.6, G.7, G.9, G.11, G.12 are explicitly
  differential against a Python/mpmath oracle. This aligns with the repo's existing
  `ffi_utils` + `_adapters/` / `_ffi_utils/` test organization.

- **Boundary-first style.** Proposals G.2, G.3, G.4 are deterministic boundary tests using
  reverse-engineered inputs, not fuzz. These complement the existing fuzz coverage.

- **Composition tests.** Proposal G.10 tests the library in the context of its downstream
  consumer. This is not pure-library testing but is necessary because `GrowthToTickLib`'s
  output contract is implicitly defined by `EMAGrowthTransformationLib`.

- **No mocks.** Consistent with the "real data over mocks" project rule, all tests use real
  TickMath / FullMath / Solady code paths. Python oracles for differential comparisons use
  `mpmath` at 500-bit precision, not mocked Solidity behavior.

---

## 6. Gaps Intentionally Not Covered

- **Formal verification.** Proposals do not include Halmos / Certora / KEVM specs. Formal
  verification of `growthToTick` is a natural extension but a different audit scope.

- **Gas regressions.** No gas-cost tests. The function is pure and the gas cost is dominated
  by TickMath's binary log lookup; any pathological gas behavior would be found by fuzz
  anyway.

- **Reentrancy / access control.** The function is pure; no state, no external calls, no
  access control concerns.
