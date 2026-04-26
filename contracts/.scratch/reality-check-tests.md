# Reality Check — RAN Oracle Test Suite

**Reviewer**: TestingRealityChecker
**Date**: 2026-04-13
**Claim under review**: "This test suite covers BTT properties + P0 security findings across the entire RAN oracle pipeline (Consumer → GrowthObservation → BlockNumberAware → GrowthToTick → EMA). All tests pass in 27 seconds under `FOUNDRY_PROFILE=diff forge test`."

**Verdict (TL;DR)**: **NEEDS WORK — leaning FANTASY**. The 27-second "all-green" is the single most alarming signal. Most of the green in this suite comes from tests silently no-oping rather than from the library being correct.

---

## Global defects that poison the whole suite

These issues apply across multiple files and change how to read every individual result.

### G-1. `onlyForked` is a silent no-op skip, not a skip

`contracts/test/_helpers/BaseForkTest.t.sol` lines 25–32:

```solidity
modifier onlyForked() {
    if (forked) {
        console2.log("running forked test");
        _;
        return;
    }
    console2.log("skipping forked test");
}
```

If `ALCHEMY_API_KEY` is unset, `setUp()` catches the failure, leaves `forked = false`, and every `onlyForked` test **returns success without running a single assertion**. Foundry reports these as PASSED, not SKIPPED. Roughly **39 of 48 tests** use `onlyForked`:

- 6/6 in `AngstromAccumulatorConsumer.fork.diff.t.sol`
- 6/6 in `GrowthObservation.diff.t.sol`
- 17/17 in `BlockNumberAwareGrowthObserverLib.diff.t.sol`
- 5/5 in `AngstromRANPipeline.diff.t.sol`

Of the suite's 48 tests, **only ~14 (GrowthToTick + EMA) actually execute without an RPC key**. The "27 seconds all passing" statistic is consistent with those 34+ tests never running. **A 27-second runtime is, in fact, prima facie evidence the fork tests are silently skipping** — a real fork fuzz over rows[0..27678] with `vm.rollFork` + ffi-to-Python + DuckDB lookups cannot finish 5×6 fuzz iterations across six files in 27 s.

### G-2. `runs = 5` under `[profile.diff.fuzz]`

`contracts/foundry.toml`:

```
[profile.diff.fuzz]
runs = 5
```

Five seeds per `test__fuzz*` function is not fuzzing — it is "five-example testing." None of the claimed invariants (monotonicity, round-trip, scaling invariance, binary-search cost, wrap) can be reasonably stressed in 5 calls when the domain is `uint208` or `uint32`. A real regression that only hits on ~0.1% of the input space has a ~99.5% probability of being missed. This profile exists specifically to make the suite fast, which conflicts with the claim that it proves anything about the library.

### G-3. Tests are authored to check their own construction

Across multiple files, the expected value passed to `assertEq` is itself computed from the same Python harness / test-file constants / same primitives being tested. This means the test verifies self-consistency of the test, not a property of the library. Specific examples are flagged per file.

### G-4. `vm.expectRevert(bytes(""))` (catch-all) in critical canary tests

Two of the supposed "P0" canaries (`C.1`, `GrowthToTick_ZeroAnchorReverts`, `GrowthToTick_Stage1OverflowReverts`) use the bare-bytes wildcard. Any revert from anywhere in the pipeline — including a misconfigured mock, missing import, or OOG — satisfies the assertion. A correct mutation that also happens to revert differently still passes.

---

## Per-file reality check

### 1. `AngstromAccumulatorConsumer.fork.diff.t.sol` (6 tests) — NEEDS WORK

| Test | Issue |
|---|---|
| `First`, `Last`, `FirstNonZero`, `MaxSpike`, `Midpoint` | Each test does `row = ffi(idx)` then `assertEq(onchain, row.globalGrowth)`. The Python FFI reads the same `ran_accumulator.duckdb` that was *populated by reading the same chain slot via the same `extsload` path*. This is a tautology: the DuckDB is a snapshot of the chain; the consumer reads the chain; of course they match. A bug where `globalGrowth()` read the **wrong slot** would pass if the DuckDB was also populated by reading the wrong slot (highly likely — see `ran_growth_query.py`). This is a consistency check between two mirrors of the same source, not a differential test. |
| `MaxSpike` | `MAX_SPIKE_IDX = 27677` is a hardcoded magic number with no justification in-file. "MaxSpike" implies this index has the largest growth delta; the test never verifies that. If the Python pipeline ever re-sorts or re-filters, `27677` silently points at a different row and the test still passes. |
| `Fuzz__GlobalGrowthMatches` | Same tautology, now with 5 random indices. |

**What would fail if the library were wrong?** Only a bug in `extsload` slot arithmetic that doesn't also exist in the Python query. Since the Python query was written to match the Solidity's slot arithmetic, any slot bug in the spec is **baked into both sides** and invisible here.

**Evidence required to upgrade to "believed"**: compute `globalGrowth` from a source independent of `extsload` — e.g., sum `saveNodeFees`/swap events from the same range, or reconstruct from a subgraph. Until the oracle side of the diff is produced by a different computation, this is not differential testing.

---

### 2. `GrowthObservation.diff.t.sol` (6 tests) — NEEDS WORK

| Test | Issue |
|---|---|
| `PackRoundTripBitPackingSuccess` | Creates an observation from `(blockNumber, 0, globalGrowth)`, then asserts each field accessor returns those same inputs. This is a trivial round-trip with no FFI relevance — the `onlyForked` gating + ffi call contributes nothing. A mutation that swaps `blockNumber` and `cumulativeGrowth` shifts would fail, but so would a 2-line unit test with zero FFI. |
| `GrowthDeltaMatchesRawSubtraction` | Asserts `curr.cumulativeGrowth() - prev.cumulativeGrowth() == expectedDelta`, where `expectedDelta = currRow.globalGrowth - prevRow.globalGrowth`. Since the observations are constructed from those exact row values, this is `SafeCastLib.toUint208(x) - SafeCastLib.toUint208(y) == x - y` — true by construction unless values exceed uint208 (which `bound(idxSeed, 1, n-1)` doesn't enforce). It tests `SafeCastLib`, not `growthDelta`. |
| `ElapsedBlocksMatchesRawSubtraction` | Same pattern: `block.number - block.number == expected`. Asserts that `vm.rollFork` does what `vm.rollFork` claims — a test of Foundry, not the library. |
| `ConsecutiveRowsMonotonic` | Tests that `gte`/`lt` are consistent with each other on chronologically ordered rows. Would only fail if the `gte`/`lt` definitions were swapped — a 30-second visual review of `GrowthObservation.sol` catches that. Under 5 fuzz seeds over 27k+ indices, this samples 5 points out of a monotonic sequence — guaranteed to succeed. |
| `RealObservationsAreNonZero` | Asserts `obs.isZero() == false` for real data. But `isZero` returns true only when the entire 256-bit slot is zero. Since the test supplies a nonzero `blockNumber` (the current `vm.rollFork` target), this is always false **regardless of growth data**. The test would pass even if every row's `globalGrowth == 0`. |
| `BlockNumberGteBoundary` | Asserts `(x ≥ t) == !(x < t)` for three values. This is a tautology of integer ordering; it does not test anything specific to `GrowthObservation`. |

**What would fail if the library were wrong?** A bit-layout swap (blockNumber vs relativeTimeDelta fields) would fail `PackRoundTripBitPackingSuccess` — but that's the only useful signal, and it doesn't need FFI or forking.

**Evidence required to upgrade**: Replace "does X equal what I just wrote in X" with "does X equal a value computed from an independent source" (e.g., decode the packed bytes32 manually with bit ops and compare).

---

### 3. `BlockNumberAwareGrowthObserverLib.diff.t.sol` (17 tests) — MIXED

The file splits into (a) real BTT / security checks, (b) gas ceilings, (c) tautologies.

#### Tests I partially believe

- **`RelativeTimeDeltaOverflowReverts`** — asserts a specific error selector (`SafeCastLib.Overflow`), bounds inputs to genuinely out-of-range space. A mutation that removes `SafeCastLib.toUint16` would fail. Still only 5 runs.
- **`BlockNumberOverflowReverts`** — same structure, same qualified belief.
- **`ObserveAtExactOldestBoundaryPostWrap`** — checks the exact boundary revert with the **correct selector and arguments** (`ObservationExpired(oldestBlock - 1, oldestBlock)`). This is one of the few assertions with a real, precise expectation.
- **`EmptyBufferBehavior`** — verifies both `latest()` and `oldest()` revert with `EmptyBuffer()`. Small, specific, meaningful.
- **`DescendingBlockOrderingInvariant`** — iterates the buffer and asserts strict descending block order. A real invariant; a mutation that pushed to the wrong end would fail this. Still 5 runs.

#### Tests with fake rigor

- **`ObserveAtFullBufferBinarySearchWorstCase`**: hardcoded `assertLt(gasUsed, 18_000)` — that number is not derived from anything. For a binary search over 256 entries with each step loading a single storage slot (~2100 gas cold, ~100 warm), 8 * 2100 = 16,800 is plausible but the ceiling of 18,000 is just "enough room above whatever measured today." A regression from O(log n) to O(n) would blow past 18k, but so would a cold-warm flip between runs. It's a coarse smoke alarm, not a test. Also, the test targets `rows[1]` — the **second-to-newest** observation. This is the *best* case for this binary search (2 iterations), not the worst. The name is wrong: `WorstCase` suggests it exercises the deepest path, but `rows[1]` is shallow. The actual worst case is `rows[total/2]` or `rows[total-1]`.
- **`ObserveAtProductionCadence30MinCoverage`**: This test is the most egregious example of the "test its own inputs" pattern. It writes 256 synthetic observations at 12 s cadence, then asserts `storedTimeSpanSeconds >= 1800`. The span is `255 * 12 = 3060`. The value `1800` was clearly chosen to pass. Mutating `BUFFER_CAPACITY`, `BLOCK_TIME_SECONDS`, or the timestamp loop would have to drop either `capacity` or `block_time_seconds` by >40% before this fails. The test proves `255 * 12 >= 1800`, which is arithmetic, not a library property.
- **`ObserveAtPostWrapGasStability`**: Same `18_000` ceiling, same arbitrary choice. The name claims "stability" across wrap patterns, but it only tests one target — the `oldestSurvivingIdx + 1` — not a spread of targets post-wrap.
- **`RelativeTimeDeltaInRangeRoundTrips` / `BlockNumberInRangeRoundTrips`**: These are single-field round-trip tests of the constructor — the same round-trip already covered by `RecordThenReadRoundTrip`. They don't test `record()`'s monotonicity guard; any mutation there passes.
- **`RecordMonotonicity_DescendingBlocksSilentlySkipped`**: **Correctly named but tautological**. It asserts `count` and `latest` are unchanged after writing a descending block. But if `record()` erroneously accepted the stale write, the `count` would increase *and* the `latest` accessor would return the new slot. The test would fail. OK — this one is real. Caveats: (a) 5 runs; (b) does not test that `growth` fields in other slots are untouched; (c) the `bound(secondBlock, 0, firstBlock)` includes the equal case (same-block), which is semantically different from "stale" — the test conflates two branches.
- **`CountSaturatesAtCapacity`**: Real invariant, tests saturation. Good. But `bound(pushCountSeed, 1, BUFFER_CAPACITY * 5)` means only 4 of 5 fuzz seeds will land in `pushCount > 256`. Often all 5 will be under 256, making the saturation branch untested.
- **`RecordThenReadRoundTrip`**: This is OK as a unit test; `onlyForked` adds no value here — the test does not use fork state.
- **`ObserveAtMonotonicity`**: Real property; a swap of `low` / `high` in the binary search would fail this. Good. Still 5 runs.
- **`RecordIdempotence_SameBlockDuplicateSkipped`**: Real. The duplicate must not overwrite. Good.
- **`BinarySearchUnderKeeperSkipPattern`**: The post-condition loop (lines 412–418) is the first real search-correctness check in this file: "no observation exists strictly between `result` and `target`." This is a genuine algorithmic property. However, `assertLt(gasUsed, 18_000)` is still the coarse smoke alarm. And the target is `bound(gapSeed, oldestBlock, newestBlock)` using the same `gapSeed` that drove the gaps — so the target correlates with the gap layout, reducing adversarial coverage.
- **`GrowthDeltaWrapsOnDescendingGrowth`**: Correctly asserts the **specific wrap magnitude** `(2^208 - (firstGrowth - secondGrowth))`. This is a real test of unchecked behavior. Good — though the name and test exist because the library chose to wrap silently instead of reverting, which is itself a design smell the test documents rather than catches.

**What would silently regress?**
- A bug where `observeAt` returns the *wrong* observation in the middle of the buffer (e.g., off-by-one that happens to satisfy `result ≤ target`) — not caught by the binary-search tests because `assertLe(result.blockNumber(), target)` is too loose. Only `BinarySearchUnderKeeperSkipPattern`'s inner loop checks exactness, and only for 5 fuzz seeds.
- A bug in `elapsedBlocks` for 32-bit wrap — not tested.
- A bug where `record()` pushes when `count == 0` (edge case) — not explicitly covered; the round-trip test hits it but doesn't verify "pushed to position 0 specifically."

---

### 4. `GrowthToTickLib.diff.t.sol` (11 tests) — PARTIAL BELIEVE

This file is the strongest in the suite (no `onlyForked`, actual math properties).

#### Tests I believe

- **`GrowthToTick_Identity`**: `growthToTick(x, x) == 0`. A genuine property of the math. Small, correct.
- **`GrowthToTick_ZeroAnchorReverts`**: Real, but uses `vm.expectRevert(bytes(""))` — any revert counts. A mutation that reverted via a *different* path (e.g., a require-statement added above the mulDiv) would pass. **Should assert the specific panic selector** (FullMath division-by-zero is the 0x12 arithmetic panic, selector `0x4e487b71` with 0x12).
- **`GrowthToTick_ZeroCurrentReverts`**: Good — asserts the *specific* `TickMath.InvalidSqrtPrice` selector with the correct argument. This is how revert tests should be written.
- **`GrowthToTick_SqrtPriceX96FitsInUint160`**: Real bounds invariant. But its `vm.assume(currentGrowth / anchorGrowth < (1 << 128))` gates away the very regime where truncation would occur. Under 5 runs, you will almost never hit the cliff.

#### Tests with issues

- **`TickMathRoundTripConsistency`**: Asserts `sqrtAtTick <= computedSqrtPrice < sqrtAtNextTick`. This is a **restatement of TickMath's own invariant** — it's what `getTickAtSqrtPrice` is defined to do. If the library composes `sqrt`/`shift`/`getTickAtSqrtPrice` correctly, this is tautological. If the library is wrong, the failure mode it catches is narrow: only a bug where the `<<32` shift or the `sqrt` computation disagree with `getTickAtSqrtPrice`'s interpretation. A swap of `currentGrowth` and `anchorGrowth` (sign-flip bug) still satisfies both bounds because `getTickAtSqrtPrice` is defined for all valid sqrtPrice. Doesn't verify direction.
- **`GrowthToTick_Monotonicity`**: Uses `vm.assume(a1/anchor < 1<<128)` and `vm.assume(a2/anchor < 1<<128)`. Under 5 runs this will frequently fail to find two growth values with the same anchor that both pass the assume AND differ enough to distinguish ticks. Many of the 5 runs will land in the low-ratio regime where both ticks are near 0 and trivially satisfy `t1 ≤ t2`. Real monotonicity bugs at the extreme ratios are not exercised.
- **`GrowthToTick_AnchorScalingInvariance`**: Tolerance is `assertLe(diff, 1, "drift > 1 tick")`. For a function that composes `mulDiv`, `sqrt`, bit-shift, and tick lookup, drift of 1 tick on scaling `(c, a) → (ck, ak)` could mask genuine loss of precision on the order of ~0.01%. Why 1 tick and not 0? The spec should specify exact invariance for integer scaling, and any drift is a bug. The test tolerates drift without justifying it.
- **`InvertedArgsProducesNegativeTick`**: `bound(oldestGrowth, 2, 1 << 60)` — range caps ratios at ~2^59, far from the interesting regime (uint208 extremes). Again a 1-tick tolerance on the symmetry sum; why?
- **`Stage1OverflowReverts`**: Uses `vm.expectRevert(bytes(""))` — catch-all. Same caveat as `ZeroAnchorReverts`.
- **`NearMaxSqrtPriceCliff`**: The `try/catch` structure either accepts a revert or a valid tick — but both branches are satisfied by a mutant that always reverts (the `catch` branch asserts `sqrtPriceX96 >= MAX_SQRT_PRICE`, which is trivially true for the chosen range). The test is soft.

**What would silently regress?**
- A precision regression that costs 1 tick of accuracy — tolerated by AnchorScalingInvariance and InvertedArgs.
- A swap of `latest` / `oldest` in upstream callers — **not caught here**, because `growthToTick(a, b)` vs `growthToTick(b, a)` both return valid int24 and the tests don't care about sign relative to the "real" answer (they just check consistency between two calls).

---

### 5. `EMAGrowthTransformationLib.diff.t.sol` (3 tests) — PARTIAL

Only 3 tests. For a library with a 7-step pipeline (epoch check, future-pack guard, count check, observation read, growthToTick, clampTick, insertObservation) with multiple revert paths and a time-delta unchecked subtraction, **3 tests is insufficient coverage regardless of individual quality**.

- **`EMA_SameEpochNoOpIsBitwiseIdentical`**: Real, strong test. Asserts full bitwise equality of the returned pack to the original. A mutation that modifies *any* bit in the same-epoch path would fail. **This is the one fully-believable test in this file.**
- **`EMA_InsufficientObservationsRevertsBelow2`**: Good — asserts the specific selector `InsufficientObservations.selector` twice (empty buffer, 1-obs buffer). Covers the count-branch precisely.
- **`EMA_FuturePackReverts`**: Asserts the specific selector `FuturePack(futureEpoch, currentEpoch)` with both arguments. Good — but only 5 fuzz runs and the bound (`1 .. type(uint24).max - currentEpoch`) is enormous, so 5 seeds sample nothing structured.

**Not tested at all**:
- The happy-path `insertObservation` output (no assertion that EMAs actually update correctly).
- The `clampTick` boundary — does a tick above `clampDelta` get clamped, and is the clamped output fed into `insertObservation`?
- The unchecked `timeDelta` wrap at epoch rollover — the very property the `unchecked` block's comment justifies. No test of epoch-rollover behavior.
- Any cross-call continuity (run update, then update again — does the buffer state stay sane?).

**What would silently regress?** Any bug in steps 3–7 of the pipeline (observation read, tick conversion, clamp, insertion, timeDelta arithmetic). None of these are asserted.

---

### 6. `AngstromRANPipeline.diff.t.sol` (5 tests) — FANTASY-LEANING

"Integration" here means "calls multiple libraries in one test function." It doesn't integrate *behaviors*, just invocations.

- **`PipelineHappyPath`**: Feeds 5 real rows, checks the buffer's oldest/latest fields match the first/last rows, then checks that the pack after `runEMA` has `epoch == currentEpoch` and that the buffer wasn't mutated. The pack's *content* beyond epoch is never asserted. A bug where `insertObservation` writes garbage into the EMA slots passes silently. This is a smoke test dressed up as an integration.
- **`C1_ZeroAnchorRevertsEMA`**: `vm.expectRevert(bytes(""))` — catch-all. The assertion passes on any revert, including a bug in `MockRANPipeline`, a missing mock function, an out-of-gas, or a Solidity type error. For a canary supposedly proving "zero anchor in the EMA path reverts at the correct stage," the test tells us only "something reverted." To actually canary the phenomenon named, it must assert the FullMath div-by-zero panic (`0x11` / `0x12` arithmetic panic selector).
- **`C2_StagnantPoolDoesNotRevertAndTicksEpoch`**: Three assertions: (a) `afterFirst.epoch() == currentEpoch`; (b) `afterFirst != stalePack`; (c) `afterSecond == afterFirst`; (d) `growthToTick(lat, old) == 0`.
  - (a) is trivially true because the same-epoch branch only skips when epoch is already current; `stalePack` has `epoch - 1`, so `insertObservation` unconditionally sets epoch to `currentEpoch`. The assertion tests the epoch field of `insertObservation`, not stagnation handling.
  - (b) is trivially true for the same reason: advancing the epoch changes bits.
  - (c) is trivially true by the same-epoch short-circuit at line 47 of `EMAGrowthTransformationLib.sol` — any two consecutive `runEMA` calls in the same epoch return the first argument bit-for-bit. It has nothing to do with stagnation.
  - (d) `growthToTick(x, x) == 0` is already tested in `GrowthToTickLib_Identity`.
  - **None of (a)–(d) is specific to stagnation.** Rename this test `EpochAdvanceAndIdempotence` and it's exactly the same test with honest labeling. It does **not** canary stagnation.
- **`I2_EMAPassesLatestAsCurrentNotAnchor`**: Claims to canary the "arg-order" bug (passing `oldest` as `currentGrowth` and vice versa). Both mirrored pipelines are constructed; `packA != packB` is asserted. **But**: `packB`'s pipeline records `(1000, 0, 5e30)` then `(1001, 12, 1e30)` — descending growth, which triggers wrap-around in `growthDelta` and a negative tick that `clampTick` will *clamp to `-1000`*. `packA`'s pipeline records the same two obs in opposite order: `(1000, 0, 1e30)`, `(1001, 12, 5e30)` — ascending, producing a positive tick. Of course the two packs differ. **An arg-order bug in `updateGrowthEMA` (swapping `latest.cumulativeGrowth()` and `oldest.cumulativeGrowth()` in the `growthToTick` call) would flip packA and packB's ticks, but the test only asserts `packA != packB`, which is still true after the swap.** The canary does not canary the phenomenon named — it detects "these two runs differ," which is a different claim.
- **`D4_DescendingGrowthProducesGarbageTick`**: Asserts the wrap-delta magnitude precisely (good), and that the tick is negative (good). Unlike C2, D4 is actually specific to descending growth. Believable as a canary.

---

## Canary report card

| Canary | Claim | Reality |
|---|---|---|
| `C.1` zero-anchor reverts in EMA | Catches zero-anchor bug | Catch-all `bytes("")` — passes on *any* revert. **Does not canary the named phenomenon.** |
| `C.2` stagnant pool does not revert and ticks epoch | Catches stagnation handling | All four assertions are true for *any* non-zero observations, not just stagnant. **Does not canary the named phenomenon.** |
| `D.4` descending growth produces garbage tick | Catches silent wrap + negative tick | **Does canary the phenomenon**; precise wrap magnitude asserted. |
| `I.2` EMA passes latest-as-current | Catches arg-order bug | Arg-order swap in the EMA's `growthToTick` call would still yield `packA != packB`. **Does not canary the named phenomenon.** |
| `F.2` | (not present as F.2 in files) | The `FuturePack` revert test (`EMA_FuturePackReverts`) is precise and believable. If that was the intended "F.2", it's fine. |

---

## Tests I believe (full list)

1. `BlockNumberAware.ObserveAtExactOldestBoundaryPostWrap` — precise error + args
2. `BlockNumberAware.EmptyBufferBehavior`
3. `BlockNumberAware.RelativeTimeDeltaOverflowReverts` — specific selector
4. `BlockNumberAware.BlockNumberOverflowReverts` — specific selector
5. `BlockNumberAware.DescendingBlockOrderingInvariant` (5 runs caveat)
6. `BlockNumberAware.RecordIdempotence_SameBlockDuplicateSkipped`
7. `BlockNumberAware.GrowthDeltaWrapsOnDescendingGrowth` — precise wrap magnitude
8. `BlockNumberAware.BinarySearchUnderKeeperSkipPattern` — real post-condition loop
9. `GrowthToTick.Identity`
10. `GrowthToTick.ZeroCurrentReverts` — specific selector
11. `EMA.SameEpochNoOpIsBitwiseIdentical` — full bitwise equality
12. `EMA.InsufficientObservationsRevertsBelow2` — specific selector
13. `EMA.FuturePackReverts` — specific selector + args
14. `Integration.D4_DescendingGrowthProducesGarbageTick` — specific wrap magnitude

**13 believable out of 48. ~35 are silent no-ops under the default dev environment, tautologies, or have catch-all reverts / wrong canaries.**

---

## Required upgrades (per test, not code changes — assertion changes)

To upgrade the rest of the suite to "believed," the **test assertions** need these changes (this is a test-review, not a library-fix list):

1. **Fork tests must fail loud, not skip silent**: replace the `onlyForked` no-op with `vm.skip(true)` *or* require `ALCHEMY_API_KEY` and error out if missing. Silent skip + green status is fantasy.
2. **Bump `runs` to ≥ 256 for the fuzz tests** or stop calling them fuzz tests. 5 runs is example-based.
3. **`AngstromAccumulatorConsumer`**: produce the expected `globalGrowth` from an independent source (events, subgraph, alternate slot-computation) — not from the DuckDB mirror of the same chain read.
4. **`GrowthObservation`**: drop the FFI wrapper on trivial round-trip tests, or actually use the FFI data to cross-validate against a Python-computed packing.
5. **`GrowthToTick.AnchorScalingInvariance` / `InvertedArgsProducesNegativeTick`**: justify or remove the ±1 tick tolerance. Integer scaling should be exact; any drift is a bug.
6. **`GrowthToTick.ZeroAnchorReverts` / `Stage1OverflowReverts`**: replace `vm.expectRevert(bytes(""))` with the specific arithmetic-panic selector `0x4e487b7100..0012`.
7. **`Integration.C1`**: replace catch-all revert with the specific panic selector; verify the revert comes from `growthToTick`, not from `insertObservation` or the mock.
8. **`Integration.C2`**: rename to `EpochAdvanceAndIdempotence`, **or** add assertions that only stagnation satisfies (e.g., `lat.cumulativeGrowth() == old.cumulativeGrowth()`, which the current test doesn't check).
9. **`Integration.I2`**: **cannot work as written**. To canary arg-order in `growthToTick(latest, oldest)`, you need two pipelines where only the arg order of the library call differs, not where the *buffer contents* differ. Current construction guarantees different outputs regardless of arg-order. Either call a mocked version of `updateGrowthEMA` with deliberately swapped args, or assert a specific property of `packA` that a swap breaks.
10. **`BlockNumberAware.ObserveAtFullBufferBinarySearchWorstCase`**: target `rows[total - 1]` or `rows[total / 2]` — actual worst-case paths.
11. **Gas ceilings (`< 18_000`)**: justify each ceiling with a comment citing the expected operation count × per-op cost. If it's empirical, state so; don't dress it as a budget.
12. **`EMA`**: add at least three happy-path tests that assert specific EMA output values against a Python reference implementation (this is a differential-test suite; the absence of numeric EMA diffs is a glaring gap).
13. **`Integration.PipelineHappyPath`**: assert at least one field of the EMA output pack beyond `epoch`. Currently, any mutation to the EMA math in the happy path passes.

---

## Verdict

**NEEDS WORK (leaning FANTASY)**.

The claim "covers BTT properties + P0 security findings across the entire RAN oracle pipeline" is not supported by the evidence:

- ~34 of 48 tests likely silently no-op in any environment without `ALCHEMY_API_KEY` (the 27-second runtime corroborates this).
- 5 fuzz runs per test is not fuzzing.
- Three of four named P0 canaries (C.1, C.2, I.2) do **not** canary the phenomenon named. Only D.4 (and F.2 if that maps to `EMA_FuturePackReverts`) canaries correctly.
- Most "differential" tests are consistency checks between two mirrors of the same data source — they cannot detect a bug shared between source and oracle (which is the realistic failure mode).
- The EMA library has 3 tests for a 7-step pipeline. Happy-path EMA output values are never asserted against anything.
- Catch-all `vm.expectRevert(bytes(""))` is used in the most security-critical canaries, where precise selectors matter most.

**Recommended disposition**: Do **not** treat the "all green in 27 s" as a readiness signal. Require:
1. CI run with `ALCHEMY_API_KEY` set + fork runtime > 5 minutes to prove fork tests actually execute.
2. `[profile.diff.fuzz] runs = 256` minimum; re-run and report failures.
3. Rewrites of C.1, C.2, I.2 to canary their named phenomena, or renamed and descoped.
4. Independent reference for the `AngstromAccumulatorConsumer` differential (not a DuckDB mirror of the same slot read).
5. At least 5 additional EMA tests asserting numeric output against a Python reference.

Until those are delivered, this suite's "PASS" is not evidence of correctness.
