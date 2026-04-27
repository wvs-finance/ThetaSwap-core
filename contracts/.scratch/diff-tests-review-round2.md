# Differential Test Review — Round 2

**Reviewer:** Blockchain Security Auditor
**Date:** 2026-04-12
**Files under review:**
1. `contracts/test/libraries/BlockNumberAwareGrowthObserverLib.diff.t.sol` (16 tests)
2. `contracts/test/libraries/GrowthToTickLib.diff.t.sol` (9 tests)
**Grounding:** `growth-observer-lib-btt-spec.md`, `growth-to-tick-lib-btt-spec.md`,
`security-edge-cases-growth-observer.md`, `security-edge-cases-growth-to-tick.md`,
`test-review-growth-observer.md` (round 1).

---

## Verdicts

| File | Verdict | One-line justification |
|------|---------|------------------------|
| `BlockNumberAwareGrowthObserverLib.diff.t.sol` | **NEEDS WORK** | S-1, S-2, S-3 from round 1 are unaddressed; 2 of the 6 observer P0s remain uncovered; several "security edge" tests only prove the field round-trips, not the library's guarantees. |
| `GrowthToTickLib.diff.t.sol` | **INSUFFICIENT** | 4 of 5 P0 findings (G.1, G.2, G.4, G.5) have either zero or weak coverage; the one covered (G.3) uses fuzz bounds that silently exclude the boundary case; the "inverted args" test has an incorrect mathematical assumption. |

Default was NEEDS WORK; GrowthToTick slips to INSUFFICIENT because the P0 surface
it actually stresses is essentially the happy path plus revert-on-zero, while the
real silent-miscomputation class (G.4 case 4, G.5 symmetry, G.1 cast) is untouched
or tested with an assertion that is too loose to differentiate bug from correctness.

---

## Systemic Issues (apply across both files)

### SS-1 `onlyForked` silently skips 15 of 16 observer tests without the env var

Same finding as round 1 Issue S-1. The observer suite still gates **every** test on
`onlyForked`, including tests that construct their own `MockBlockNumberAware` and
never touch a forked contract. Without `ALCHEMY_API_KEY`, `forked = false`, the
modifier logs `"skipping forked test"` and returns — Foundry shows green. CI
without the secret would report 16 passing tests while asserting nothing.

Round 1 flagged this. Round 2 still has it. This is a **Critical false-confidence
source** that will not be caught by anyone who doesn't explicitly grep the suite
for `onlyForked`. Mark each of the 15 non-FFI tests for un-gating.

### SS-2 20k gas ceiling is 5–13× looser than production observations

Four observer tests assert `assertLt(gasUsed, 20_000, ...)`. Per the BTT spec and
round 1's S-2, binary search over a 256-entry buffer uses ~1.5–4k gas on warm
cache. A 2× regression (say, a defensive rewrite that adds extra
invariant-checking SLOADs) would NOT trip this ceiling. A regression that
converts binary search into linear scan (256 SLOADs × 100 = ~25.6k) would fail
only marginally, and a subtler linearization (e.g., 16k gas) would pass cleanly.

Additionally — and this is new — a hypothetical **safer rewrite** (e.g., adding
`ObservationExpired` at multiple levels, or replacing unchecked modular arithmetic
in `CircularBuffer.last`) could push gas from 4k to 7k without introducing any
bug. The 20k ceiling would pass. But a gas snapshot with tight bounds
(e.g., `assertApproxEqAbs(gasUsed, 3500, 500)`) would correctly flag the change
for review without failing a benign defensive refactor. Current ceilings are the
worst of both worlds: too loose to catch real regressions, too arbitrary to
distinguish safe rewrites from unsafe ones.

### SS-3 Descending-block sequences never approach `type(uint32).max`

Every observer test that loops `for (uint256 i; i < N; ++i) m.recordObs(startBlock + i, ...)`
relies on `startBlock = block.number`. On a fork pinned to mainnet (~block 20M),
`startBlock + 256 * 5 ≈ 20_001_280`. The uint32 narrowing boundary at
`type(uint32).max ≈ 4.29e9` is **never approached**. P0 A.1 (BlockNumber uint32
boundary near `type(uint32).max`) is uncovered. Round 1 flagged this; round 2
has not added a boundary-primed test.

### SS-4 `vm.assume` filtering silently excludes adversarial inputs

In `GrowthToTickLibDifferentialTest`, four tests use
`vm.assume(currentGrowth / anchorGrowth < (1 << 128))`. This filter discards
**every input that would stress Stage 1 overflow** — the exact P0 revert-taxonomy
boundary (G.3). The `Stage1OverflowReverts` test does attempt the opposite
(bounds chosen to force overflow), but see SR-9 below — its bounds have a
shrink-resistance bug that often yields trivially empty fuzz runs.

A `vm.assume` that filters out the primary adversarial class is a clear
anti-pattern. Every fuzz test that needs normal inputs AND a separate test that
verifies revert behavior is the right pattern. The filtering in
`TickMathRoundTripConsistency`, `Monotonicity`, `NonNegativity`, and
`AnchorScalingInvariance` is legitimate (those tests assert properties that
require no-revert), but the test suite as a whole lacks a complement test that
exercises the filtered-out region deliberately. G.3 attempts this but poorly
(see below). G.1 (narrowing cast at exactly sqrtPriceX96 < 2^160 boundary) is
unattempted.

### SS-5 "Security Edge" tests mostly exercise the happy-path boundary, not the adversarial surface

Tests tagged `fuzzSecurityEdge__` are semantically the ones that should stress
the adversarial surface identified in the security reports. In practice many of
them are boundary round-trip tests that only verify the bit-packing works (see
per-test below). The label creates false confidence that the security report has
been addressed. This is especially sharp for:
- `RelativeTimeDeltaInRangeRoundTrips` — checks `latest()` only, not the whole
  read path (`observeAt`, `oldest`); does not prove that post-wrap the stored
  value is still readable correctly.
- `BlockNumberInRangeRoundTrips` — same, and `bn = 0` is inside the bound
  `[0, uint32.max]` but the library's monotonicity skip rejects `bn <= 0` as
  non-monotonic, so the fuzzer can hit a case the test silently accepts.
- `InvertedArgsProducesNegativeTick` — bounds `oldestGrowth ∈ [2, 1<<60]`
  excludes the most adversarial sub-region (`oldestGrowth` near 2^208), which
  is where ratio inversion combined with precision-floor can produce
  unexpectedly near-zero ticks instead of the negative tick the name promises.

---

## Per-Test Critique — `BlockNumberAwareGrowthObserverLib.diff.t.sol`

### 1. `test__fuzzDifferential__ObserveAtFullBufferBinarySearchWorstCase`

Loads 256 oracle rows, records all, queries for `rows[1].blockNumber` (second-
newest). Asserts match + gas < 20k + span > 30 min. "Worst case" is a misnomer —
index 1 is a **near-best case** for the binary search because `low=1, high=255,
mid=128` resolves the upper half in one comparison. True worst case is an
odd-indexed interior target where every midpoint test alternates. The span
assertion depends on DuckDB fixture data, not the library. Gas 20k ceiling per
SS-2. This test measures oracle health, not library health.

### 2. `test__fuzzDifferential__ObserveAtProductionCadence30MinCoverage`

`assertGt(productionSpanSeconds, 1800)` is a **tautology**: `productionSpanSeconds
= (256 - 1) * 12 = 3060` is fully determined by two constants defined in the
test file. It proves nothing about the library — it proves that 255 × 12 > 1800.
The correctness assertion at `observeAt(startBlock + 1)` is again a near-best
case. Test is essentially two console.logs wrapped in assertions that can never
fail for any library change.

### 3. `test__fuzzDifferential__ObserveAtPostWrapGasStability`

Bound `[257, 2560]` — one to ten wraps. "Stability" is a variance property, but
the test asserts only the upper bound on a single invocation per fuzz run. A
regression making gas spike at exactly one wrap depth would be caught only if
the spike > 20k, otherwise the spike passes as "stable." Also: modular arithmetic
inside `CircularBuffer.last` is identical mathematically across wrap depths, so
fuzzing across `[257, 2560]` samples a single equivalence class, not diverse
behaviors. P0 B.1 (multi-wrap determinism with exact oldest-block computation)
remains uncovered: this test does not pick a target that would have been evicted
after the specific wrap count, which is B.1's failure mode.

### 4. `test__fuzzSecurityEdge__RelativeTimeDeltaInRangeRoundTrips`

Only `latest()` is checked. The name says "round trips" — should also verify
`observeAt(1001).relativeTimeDelta() == relTimeDelta` and
`oldest().relativeTimeDelta()` paths match. If the packing logic silently lost
the upper bits under post-wrap index calculation, `latest()` would still be
correct (it reads the most recent push) while the interior accessors would be
wrong. Does not prove what its name claims.

### 5. `test__fuzzSecurityEdge__RelativeTimeDeltaOverflowReverts`

Legitimately tests the SafeCastLib revert. But: it fuzzes `relTimeDelta ∈
[65_536, uint256.max]` which means the fuzzer almost never hits the exact
boundary value 65_536. A safe-cast off-by-one (e.g., `>` vs `>=` in SafeCastLib)
would pass this test because the fuzz probability of picking exactly 65_536 from
that range is ~0. Needs a dedicated boundary assertion at `relTimeDelta = 65_536`
as a deterministic case.

### 6. `test__fuzzSecurityEdge__BlockNumberInRangeRoundTrips`

Bound `[0, uint32.max]` allows `bn = 0`. The library's `record` then stores
(0, 0, 1e18). `latest().blockNumber() == 0` passes. But the library's monotonicity
check uses `>= SafeCastLib.toUint32(_blockNumber)`, and on an empty buffer the
`total > 0` check is false, so the very first push always succeeds. No bug, but
no adversarial check either — the test would pass even if the library had a bug
that allowed `record(0, ...)` to silently skip on a non-empty buffer, because
the test starts from empty. Boundary value `type(uint32).max` as a deterministic
case is missing.

### 7. `test__fuzzSecurityEdge__BlockNumberOverflowReverts`

Same critique as #5 — bounds `[uint32.max + 1, uint256.max]` means the boundary
value `uint32.max + 1` is never explicitly hit. Solid in aggregate but lacks a
deterministic boundary case.

### 8. `test__fuzzSecurityEdge__ObserveAtExactOldestBoundaryPostWrap`

Good structure: exercises the `oldestBlock` exact boundary and
`oldestBlock - 1` miss. Two problems. First: the `vm.expectRevert` call
hard-codes the error signature as
`abi.encodeWithSignature("ObservationExpired(uint32,uint32)", oldestBlock - 1, oldestBlock)`
— but if the library is refactored to widen the error args or rename, this test
breaks silently while the bug slips. Second: only one post-wrap depth is
exercised. P0 B.1 explicitly asks for 10+ wraps (2560 pushes) — this test
maxes at 4 wraps and even at 4 wraps the modular arithmetic is equivalent to
1 wrap. It does not cover what B.1 asks for. Name suggests more than it tests.

### 9. `test__fuzzBTT__RecordMonotonicity_DescendingBlocksSilentlySkipped`

**Name mismatch.** Test name says "Silently Skipped" which should mean the
library accepts the call without effect. The test checks `count` is unchanged
(good), `latest.blockNumber() == firstBlock` (good), `latest.cumulativeGrowth
== 1e18` (good). But **it does not check** `latest.relativeTimeDelta()` is
unchanged — the second record tried to set it to `12`. If a future bug caused
`record` to overwrite the relativeTimeDelta in-place while skipping the block
update, this test would pass while the pre-existing latest is silently mutated.
Round 1 flagged this class of mismatch (assertion doesn't prove the full claim);
round 2 still has it.

Also: `bound(secondBlock, 0, firstBlock)` — the equality case (`secondBlock ==
firstBlock`) is already covered by the dedicated `RecordIdempotence_SameBlockDuplicateSkipped`
test. The inclusive bound here creates redundancy that dilutes the distinct-input
assertion power.

### 10. `test__fuzzBTT__CountSaturatesAtCapacity`

Pushes `[1, 5 * CAPACITY]` monotonic observations. Correct, but trivial: the
CircularBuffer primitive has been in OpenZeppelin for years and its saturation
is a library invariant. This test effectively verifies OZ, not the library
under test. The library's only contribution is the monotonicity skip — which is
not tested here (every input is strictly monotonic). No adversarial value.

### 11. `test__BTT__EmptyBufferBehavior`

Straightforward revert check. Solid but thin — only `latest()` and `oldest()`
are checked. `observeAt(anyBlock)` on an empty buffer should also revert with
`EmptyBuffer()` (per the library source line 87), but the test does not cover
this path. One-line addition.

### 12. `test__fuzzBTT__RecordThenReadRoundTrip`

Single observation: `latest == oldest == observeAt(bn)`. Good invariant. But:
the test does not cover **post-wrap read invariance** — the real bug class is
"write succeeds, latest() returns right value, observeAt() returns garbage
after wrap because the index arithmetic desyncs with `_count`." A single-obs
round-trip proves none of that. Needs a companion test that pushes N >
CAPACITY observations and then asserts `observeAt(stored_block) == the stored
observation` for each stored block.

### 13. `test__fuzzBTT__DescendingBlockOrderingInvariant`

Good test in principle. `for i; i < c; assertLt(currBlock, prevBlock)` verifies
strict descending order via `rawAt(i)` across all stored slots. But: it relies
on the inputs being strictly monotonic (`startBlock + i`), so the test is
essentially a tautology — of course descending order holds when the inputs are
strictly increasing and the buffer is a FIFO. The adversarial case that would
break this invariant is when a keeper submits a **mixed monotonic/stale**
sequence that tests the skip logic — and that sequence is not fuzzed here. The
`BinarySearchUnderKeeperSkipPattern` test fuzzes gaps but only with positive
gaps, not descending. Neither test exercises the case where the library's skip
decision itself could be wrong.

### 14. `test__fuzzBTT__ObserveAtMonotonicity`

`t1 <= t2 ⇒ observeAt(t1).blockNumber() <= observeAt(t2).blockNumber()`. Good
core invariant. Concern: `uint32(bound(targetSeedA, oldestBlock, newestBlock))`
inclusive on both ends — when `t1 == t2`, the assertion becomes `r1.blockNumber
<= r2.blockNumber` which, on a non-gapped buffer, is always an equality. Not a
bug; the test is valid but half its fuzz runs degenerate to a single identity
check. Stratifying the seeds to bias toward distinct targets would produce
stronger evidence.

### 15. `test__fuzzBTT__RecordIdempotence_SameBlockDuplicateSkipped`

`record(bn, 0, 1e18)` then `record(bn, 999, 5e18)`. Asserts `count` and full
`latest` bytes unchanged. **This is the right pattern** — compares the full
32-byte unwrap. The critique of test #9 does not apply here; this one is
correct. Good test.

### 16. `test__fuzzSecurityEdge__BinarySearchUnderKeeperSkipPattern`

Gap-sequence fuzz with `bn += 1 + (keccak(seed, i) % 20)`. Asserts
`result.blockNumber() <= target` and gas < 20k. The correctness assertion is
weak: `<= target` is satisfied by **any** observation in the buffer with a
smaller block number. The **binary search correctness property** is "returns
the observation with the *largest* blockNumber still `<= target`" — that
stronger property is not asserted. A regression that made the binary search
return the *oldest* observation on every call would still satisfy
`result.blockNumber() <= target`. Per P0 B.3 the test must verify the
*predecessor* property, not just bounded-below. Missing.

---

## Per-Test Critique — `GrowthToTickLib.diff.t.sol`

### 1. `test__fuzzBTT__GrowthToTick_TickMathRoundTripConsistency`

Correctness: asserts `sqrtAtTick <= computedSqrtPriceX96 < sqrtAtNextTick`. This
is the right TickMath floor invariant. Scope: filtered by
`vm.assume(currentGrowth / anchorGrowth < (1 << 128))`, so every Stage 1
overflow is skipped. The filter is correct for this property test, but means
the suite's only correctness check never stresses the cast boundary (G.1). The
`currentGrowth ≥ anchorGrowth` bound also excludes inverted calls, so the
silent-negative-tick regime (G.4 case 4) is never observed here.

### 2. `test__fuzzBTT__GrowthToTick_Identity`

`growthToTick(x, x) == 0`. Correct invariant, but trivial. `x / x = 1`, sqrt =
1, so tick = 0 mechanically. The test proves `FullMath.mulDiv(x, Q128, x) == Q128`
and `sqrt(Q128) == 2^64` and `2^64 << 32 == 2^96` and `TickMath(2^96) == 0` —
all of which are library-level invariants, not `growthToTick`-specific. No
adversarial value.

### 3. `test__fuzzBTT__GrowthToTick_Monotonicity`

Fuzz `a1 ≤ a2`, assert `t1 ≤ t2`. Good core property. But: both assumes filter
out overflow; `vm.assume(a2 / anchorGrowth < (1 << 128))` can filter heavily when
`anchorGrowth` is small, making this a low-coverage fuzz. Solidity fuzz assume
rejection typically does not warn, so silently degraded coverage is plausible.
Also: `a2 = bound(uint256(keccak256(abi.encode(deltaSeed))), a1, type(uint208).max)`
— deriving `a2` by keccak of `deltaSeed` makes it nearly uncorrelated with
`a1`, which is fine for distribution but removes the ability to hit the
adjacent case (`a2 == a1 + 1`) that G.8 (tick boundary transitions) requires.

### 4. `test__fuzzBTT__GrowthToTick_NonNegativity`

`currentGrowth >= anchorGrowth ⇒ tick >= 0`. Correct but this is BTT Property 4
and the filtering guarantees it. Under the conditions the test sets up, the
output MUST be non-negative by construction. The test does not probe the
condition Property 4 is silent about — the inverted case where `currentGrowth <
anchorGrowth` and the tick silently goes negative. That adversarial surface is
(partially) covered by test #8 but with a separate critique (see below).

### 5. `test__fuzzBTT__GrowthToTick_AnchorScalingInvariance`

`|growthToTick(c, a) - growthToTick(c*k, a*k)| <= 1`. Correct invariant.
Weakness: bounds `anchorGrowth ∈ [1, uint208.max / 2]`, `currentGrowth ∈
[anchorGrowth, uint208.max / 2]`, `k ∈ [2, uint208.max / currentGrowth]`. The
`currentGrowth * k < uint208.max` upper bound is enforced, but this never hits
the G.7 P1 case where `k*c = uint208.max - 1` exactly (no headroom) — the
most adversarial scaling case. `maxK > 1` filter means when `currentGrowth` is
near `uint208.max`, the test simply skips (no `k >= 2` exists). Silent coverage
loss. G.7's "tight integer-scaling bit-for-bit equality" sub-claim (where
`k * c / k * a` is exactly `c/a` with no floor-remainder loss) is not tested —
the `<= 1` bound permits the weaker claim even if the stronger one holds.

### 6. `test__fuzzBTT__GrowthToTick_ZeroAnchorReverts`

`externalGrowthToTick(current, 0)` reverts. `vm.expectRevert()` with no
signature — accepts **any** revert. If FullMath's division-by-zero panic were
replaced with a different revert (or even an OOG), this test would still pass.
A panic-code-specific assertion (`vm.expectRevert(stdError.divisionError)` for
Panic 0x12) would pin the revert taxonomy. Per G.4, this anonymous revert is
exactly the class the security report flagged for taxonomy regression.

### 7. `test__fuzzBTT__GrowthToTick_ZeroCurrentReverts`

**This test is likely wrong.** Per the library source and G.4 case 3: with
`currentGrowth = 0` and `anchorGrowth > 0`, Stage 1 returns 0 (not a revert),
Stage 2 returns 0, Stage 3 returns 0, Stage 4 is `TickMath.getTickAtSqrtPrice(0)`
which reverts with `InvalidSqrtPrice(0)` because `0 < MIN_SQRT_PRICE`. So the
function does revert, but from TickMath, not from FullMath.

The test's `vm.expectRevert()` (no signature) accepts either path, so it passes.
But the name says "ZeroCurrentReverts" which implies an expected revert — it
does revert, but the test does not distinguish *which* revert, which is the
entire point of G.4 (revert taxonomy). A future refactor that added an
explicit `require(currentGrowth > 0, ZeroCurrent())` check would pass this
test without the caller being able to distinguish the new named error from the
previous TickMath revert. Silent taxonomy regression.

### 8. `test__fuzzSecurityEdge__GrowthToTick_InvertedArgsProducesNegativeTick`

`oldestGrowth ∈ [2, 1<<60]`, `latestGrowth ∈ [1, oldestGrowth - 1]`, assert
`tickInverted < 0`. Claims to be a "silent bug canary" for G.5.

**Three significant problems:**

1. The bound `oldestGrowth <= 1<<60` excludes the interesting regime
   (`oldestGrowth` near uint208.max). G.5's concern is that inverted arguments
   with an extreme ratio can actually `revert` with `InvalidSqrtPrice` (when
   `sqrtPriceX96 < MIN_SQRT_PRICE`), not produce a negative tick. That regime
   is skipped. The test pretends to cover G.5 but covers only the mid-range
   inverted case.

2. `tickInverted < 0` is a weak property. G.5's proposed assertion is
   `|tick_forward + tick_inverted| <= 1` — the symmetry check. The current
   test does not compute `tick_forward` and does not verify the symmetry.
   A bug that made all inverted calls return a negative tick of the wrong
   magnitude (e.g., always `-1` regardless of ratio) would pass this test.

3. `latestGrowth = 0` case (G.4 case 3) is excluded by
   `latestGrowth >= 1`. That case is separately covered by test #7, but
   with the taxonomy issue flagged above.

"Silent bug canary" is aspirational naming; the actual assertion catches only
the "always-non-negative" regression, not the silent-wrong-magnitude regression.

### 9. `test__fuzzSecurityEdge__GrowthToTick_Stage1OverflowReverts`

Attempts to exercise G.3 Stage 1 overflow. **The bound computation is broken.**

Code:
```
anchorGrowth = bound(anchorGrowth, 1, (1 << 80) - 1);
uint256 minOverflowCurrent = anchorGrowth * (1 << 128);
vm.assume(minOverflowCurrent < type(uint208).max);
currentGrowth = bound(currentGrowth, minOverflowCurrent + 1, type(uint208).max);
```

Issue 1: `anchorGrowth * (1 << 128)` is computed in `uint256`. When
`anchorGrowth` is near `2^80`, `anchorGrowth * 2^128` approaches `2^208` —
which fits in uint256 (208 < 256), so no overflow. OK there.

Issue 2: `vm.assume(minOverflowCurrent < type(uint208).max)` is the critical
filter. `minOverflowCurrent = anchorGrowth * 2^128`. For this to be less than
`2^208 - 1`, we need `anchorGrowth < 2^80`. That's satisfied by the upper
bound `(1 << 80) - 1`. So the assume rarely fires. OK.

Issue 3: The revert condition in FullMath.mulDiv is `require(denominator >
prod1)` where `prod1 = (currentGrowth * Q128) >> 256`. For `prod1 >=
denominator` — i.e., for overflow — we need `currentGrowth * Q128 / 2^256 >=
anchorGrowth`, or equivalently `currentGrowth >= anchorGrowth * 2^128`.
Setting `currentGrowth > anchorGrowth * 2^128` does guarantee overflow. Good.

**But the final check:** `bound(currentGrowth, minOverflowCurrent + 1,
type(uint208).max)` requires `minOverflowCurrent + 1 <= type(uint208).max`,
which combined with `anchorGrowth < 2^80` means most fuzz runs have a narrow
`currentGrowth` window near the top of uint208. Whenever the fuzzer picks
`anchorGrowth` close to `2^80`, `minOverflowCurrent` is close to `2^208` and
the bound range collapses to a handful of values. When `anchorGrowth` is small
(e.g., 1), `minOverflowCurrent = 2^128` and the bound range is massive — but
`vm.assume(2^128 < 2^208)` passes. So the distribution is heavily skewed toward
small-anchor cases, which **duplicates** the simpler assertions already tested.
G.3's boundary case (`anchorGrowth = 2^80, currentGrowth = type(uint208).max`)
is near-impossible to hit from this fuzz distribution.

Also: `vm.expectRevert()` without a signature — same taxonomy concern as #6.
The *whole point* of G.3 is to pin the revert is from FullMath's bare `require`,
not from a narrowing cast or TickMath. This test does not enforce that.

---

## Uncovered P0s — Observer

| P0 | Title | Status | Gap |
|----|-------|--------|-----|
| A.1 | BlockNumberUint32BoundaryWrap | **Uncovered** | No test primes buffer at `uint32.max - 1` and tries the wrap sequence. Tests #6 and #7 fuzz in-range and overflow-range separately, but neither exercises the `uint32.max → uint32.max + 1 → 0` sequence that stresses the keeper liveness contract. |
| A.2 | RelativeTimeDeltaUint16Saturation | **Partial** | Tests #4 and #5 cover in-range and overflow-range but miss the exact boundary 65_535 as a deterministic case (fuzz hits it with ~1/65k probability). Also: test #4 does not verify the stored value is accessible from all read paths. |
| B.1 | ObserveAtAfterMultipleFullWraps | **Weak** | Test #3 stops at 10 wraps and only asserts correctness + gas bound on a single query. The "deterministic revert with `ObservationExpired` when querying the original first block after many wraps" claim (B.1's specific setup) is not asserted. |
| B.2 | ObserveAtExactlyAtOldestBoundary | **Partial** | Test #8 hits the boundary and `oldestBlock - 1` revert. Does NOT hit `oldestBlock + 1` sub-case (returns oldest or second-oldest depending on gaps), which B.2 specifies. Also hard-codes the error signature string — brittle. |
| C.1 | EMAUpdateRevertsOnZeroAnchorGrowth | **Out of scope here** | Requires EMA transformation layer; not in this observer test file. Flagged so it's not forgotten. |
| D.4 | GrowthDeltaUncheckedWrapOnMisorderedInputs | **Uncovered** | `growthDelta` is never exercised. The observer's monotonicity skip only checks block numbers — not cumulative growth. An adversarial sequence `record(B, t, 100), record(B+1, t, 50)` would succeed (block increasing) but leave `growthDelta` wrapping to `2^208 - 50`. Zero tests exercise this. |

Observer P0 coverage: **2 / 6 partial, 3 / 6 missing (A.1, B.1 strictly, D.4)**.
If C.1 is counted as out-of-scope, effective coverage is 2 partial / 4 P0s.

## Uncovered P0s — GrowthToTick

| P0 | Title | Status | Gap |
|----|-------|--------|-----|
| G.1 | SqrtPriceX96NarrowingSafety | **Uncovered** | Zero tests compute the uint256 intermediate and assert `< 2^160`. The narrowing cast is the single unchecked width change in the pipeline and is the most likely place for a silent refactor bug to land. |
| G.2 | RatioAtMaxSqrtPriceBoundary | **Uncovered** | No test constructs input pairs targeting `sqrtPriceX96 == MAX_SQRT_PRICE - 1`, `MAX_SQRT_PRICE`, `MAX_SQRT_PRICE + 1`. The MAX_TICK cliff is not pinned. |
| G.3 | Stage1OverflowRevertTaxonomy | **Weak** | Test #9 attempts this but has the fuzz-distribution and signatureless-revert problems documented above. The exact deterministic boundary at `anchorGrowth = 2^80, currentGrowth = uint208.max` is not exercised. |
| G.4 | ZeroAnchorAndZeroCurrent | **Weak** | Tests #6 and #7 accept any revert via `vm.expectRevert()`. Case 4 (`currentGrowth = anchorGrowth - 1`, ratio just below 1, returns negative tick, no revert) is not asserted here — partially in test #8 but with the wrong bound and assertion (see above). |
| G.5 | InvertedArgumentSilentMiscomputation | **Weak** | Test #8 covers inverted args but only asserts `tick < 0` — G.5's symmetry assertion `\|forward + inverted\| <= 1` is missing, the MIN_TICK regime is excluded by the `1<<60` bound, and the revert regime (when `b >> a` drives `sqrtPriceX96 < MIN_SQRT_PRICE`) is not asserted. |

GrowthToTick P0 coverage: **0 / 5 solidly covered, 3 / 5 weak, 2 / 5 missing.**

---

## False-Confidence Risks (Ranked)

1. **SS-1: onlyForked silent skip.** Critical. Entire observer suite becomes a
   no-op without the env var. CI without ALCHEMY_API_KEY reports 16 green tests
   while asserting nothing. Round 1 flagged; round 2 unaddressed.

2. **Test #2 Tautology.** `assertGt(BUFFER_CAPACITY * BLOCK_TIME_SECONDS - 12,
   1800)` proves nothing about the library. Any library change — including
   complete deletion of the function — would still pass this test's numerical
   assertion (the test data is constructed, not observed). Medium-High.

3. **GrowthToTick #8 "canary" under-asserts.** Asserts `tick < 0` only. A
   silent-magnitude bug would pass. The test's name ("silent bug canary")
   creates false confidence that G.5 is addressed when only a partial claim is
   tested. High.

4. **GrowthToTick #6 and #7 signatureless reverts.** `vm.expectRevert()`
   catches any revert. The whole G.4 P0 is about *taxonomy* — which revert
   fires. These tests would pass if the revert path silently changed from
   FullMath panic to TickMath error to a named library error, undetected. High.

5. **20k gas ceiling (SS-2).** Misses 2–5× regressions and false-alarms on
   safe defensive rewrites. Medium — wastes review time on either direction.

6. **Test #9 "SilentlySkipped" incomplete assertion.** Does not verify
   `relativeTimeDelta` is unchanged when a stale record is skipped. A bug that
   partially updates the latest observation would be masked. Medium.

7. **Test #16 binary search weak predicate.** Only asserts `<= target` when
   the correct invariant is "largest `<= target`." A bug always returning
   oldest would pass. Medium.

8. **Fuzz bounds excluding boundary values.** Tests #5, #6, #7, #8 of observer
   and #7, #8, #9 of GrowthToTick use ranges that make exact boundary hits
   probabilistically zero. Medium.

9. **Test #13 descending-ordering is tautological.** Verifies FIFO behavior of
   OpenZeppelin's CircularBuffer, not library logic. Low impact but dilutes
   coverage reporting.

10. **Test #12 single-observation round-trip does not cover post-wrap
    read invariance.** The worst failure mode (read returns garbage after wrap
    due to index-arithmetic desync with `_count`) is not tested. Low-Medium.

---

## Recommended Tightening (specific assertion changes)

Observer:

- **SS-1 fix:** Remove `onlyForked` from tests 4–16. Only test 1 legitimately
  needs a fork (FFI oracle pulls from DuckDB).
- **Test #2:** Delete `assertGt(productionSpanSeconds, 1800)`. Replace with a
  Solidity-level `static assert(BUFFER_CAPACITY * BLOCK_TIME_SECONDS >= 30 minutes)`
  outside the test body. Or delete outright.
- **Test #4:** Add `observeAtTarget(1001)` and `oldest()` assertions. Add a
  deterministic case at `relTimeDelta = type(uint16).max` outside the fuzz.
- **Test #5, #7:** Add a deterministic case at the exact boundary value
  (`type(uint16).max + 1`, `type(uint32).max + 1`) in addition to the fuzzed
  overrange.
- **Test #6:** Add a deterministic case at `bn = type(uint32).max` and
  `bn = type(uint32).max - 1`; prime the buffer at `uint32.max - 2` and
  verify the full monotonic sequence at the boundary (this covers P0 A.1).
- **Test #8:** Replace `abi.encodeWithSignature(...)` hard-coded string with
  `ObservationExpired.selector` abi-encoded. Extend to 10+ wraps for P0 B.1.
- **Test #9:** Compare `GrowthObservation.unwrap(latest) == oldLatestUnwrap`
  (full 32-byte) rather than field-by-field. Matches test #15's correct
  pattern.
- **Test #12:** Add a companion fuzz that pushes N > CAPACITY observations and
  asserts `observeAt(stored_block_i) == stored_observation_i` for multiple i.
- **Test #16:** Strengthen assertion to "result is the observation with the
  largest blockNumber still `<= target`" — computable off-chain or by
  iterating the buffer.
- **New test:** Cover P0 D.4. Fuzz `(B1, G1), (B2, G2)` with `B2 > B1` and
  `G2 < G1`. Record both. Assert either (a) the library rejects the
  non-monotonic-growth record, or (b) document the wrap behavior so
  downstream consumers can defend.
- **New test:** Cover P0 B.1 strictly. Push 10 × 256 = 2560 strictly monotonic
  observations. Query `observeAt(originalFirstBlock)`. Assert revert with
  `ObservationExpired(originalFirstBlock, oldestBlockAt2305thPush)`.

GrowthToTick:

- **Test #1:** Add a second assertion verifying `sqrtPriceX96 < (1 << 160)`
  (captured as uint256) before the cast. Covers P0 G.1.
- **Test #2:** Delete — trivial tautology. Or convert to a deterministic
  `assertEq(growthToTick(1, 1), 0)`.
- **Test #6, #7:** Replace `vm.expectRevert()` with specific expected reverts:
  `vm.expectRevert(stdError.divisionError)` for the Panic 0x12 case (anchor=0)
  and `vm.expectRevert(abi.encodeWithSelector(TickMath.InvalidSqrtPrice.selector, 0))`
  for the zero-current case. Pins the revert taxonomy.
- **Test #8:** Extend to `oldestGrowth ∈ [2, uint208.max]` (remove the `1<<60`
  cap). Add the symmetry assertion `|tick_forward + tick_inverted| <= 1` with
  a forward call on the same inputs. Add a sub-case that asserts the
  extreme-ratio inverted call reverts with `InvalidSqrtPrice`.
- **Test #9:** Restructure so the fuzz distribution covers the G.3 boundary.
  Specifically: deterministic cases at `anchorGrowth ∈ {1, 2^79, 2^80, 2^80+1}`
  and `currentGrowth = type(uint208).max`. Add specific revert signature
  assertion (FullMath's error).
- **New test:** Cover P0 G.2. Reverse-engineer `(currentGrowth, anchorGrowth)`
  such that `sqrtPriceX96 ∈ {MAX_SQRT_PRICE - 1, MAX_SQRT_PRICE}` exactly.
  Assert tick = MAX_TICK for the former, revert with `InvalidSqrtPrice` for
  the latter.
- **New test:** Cover P0 G.4 case 4. `currentGrowth = anchorGrowth - 1` fuzz
  with `anchorGrowth ∈ [Q64, 2^208-1]`. Assert tick is strictly negative (not
  just `< 0`, but asserts the precise predecessor property). Document that
  this is the "inverted-argument silent miscomputation" regime.

Both files:

- **Gas ceiling:** Replace `assertLt(gasUsed, 20_000, ...)` with
  `assertApproxEqAbs(gasUsed, BASELINE, TOLERANCE)` where BASELINE is the
  observed production gas and TOLERANCE is ~500–1000. This catches both
  regressions and benign refactors at the right time.
- **Consider disabling `onlyForked` globally for pure-unit tests.** The
  observer library is purely in-memory; the test does not actually need a
  mainnet fork except for test #1.

---

## Final Assessment

The diff tests have grown significantly but are propagating the exact patterns
round 1 flagged: assertions that prove less than the name claims, fuzz bounds
that skip the adversarial region, gas ceilings too loose to guard regressions,
and `onlyForked` silent skips.

For the observer library, 2 of 6 P0 findings remain effectively uncovered
(A.1, D.4), and 3 more are only partially covered (A.2, B.1, B.2). For the
growth-to-tick library, 0 of 5 P0 findings are solidly covered — the nearest
is G.5 (inverted args) but the assertion is too weak to distinguish the right
answer from a wrong magnitude, and the bound excludes the extreme-ratio revert
regime that G.5 specifically calls out.

The recommendation is to treat the current test suite as **coverage inventory,
not a correctness guarantee**. Before production use, the missing P0 tests
need to be added, the `onlyForked` gates removed from the 15 pure-unit tests,
and the signatureless reverts replaced with taxonomy-pinning assertions. Gas
ceilings should migrate to tight-bound snapshots rather than round-number
comfort levels.

